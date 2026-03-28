#!/usr/bin/env python3
"""
flex2rijk.py — Automatische login voor flex2rijk.nl Citrix werkplek

Haalt gebruikersnaam en wachtwoord op uit macOS Keychain,
vraagt de OneSpan 2FA code interactief op, en download + opent het ICA bestand.

Setup (eenmalig):
    python flex2rijk.py --setup
"""

import argparse
import subprocess
import sys
import time
import tempfile
import os
from pathlib import Path

KEYCHAIN_SERVICE = "flex2rijk"
LOGIN_URL = "https://www.flex2rijk.nl/logon/LogonPoint/tmindex.html"


# ── Keychain helpers ──────────────────────────────────────────────────────────

def keychain_get(account: str) -> str:
    """Lees een waarde uit macOS Keychain."""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", account, "-w"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[!] Kan '{account}' niet vinden in Keychain voor service '{KEYCHAIN_SERVICE}'.")
        print(f"    Voer eerst uit: python flex2rijk.py --setup")
        sys.exit(1)
    return result.stdout.strip()


def keychain_set(account: str, password: str):
    """Sla een waarde op in macOS Keychain (of update als die al bestaat)."""
    # Verwijder eerst als die al bestaat (anders fout)
    subprocess.run(
        ["security", "delete-generic-password", "-s", KEYCHAIN_SERVICE, "-a", account],
        capture_output=True
    )
    result = subprocess.run(
        ["security", "add-generic-password", "-s", KEYCHAIN_SERVICE, "-a", account, "-w", password],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[!] Fout bij opslaan in Keychain: {result.stderr}")
        sys.exit(1)
    print(f"[✓] '{account}' opgeslagen in Keychain onder service '{KEYCHAIN_SERVICE}'")


def setup():
    """Interactieve setup: sla credentials op in Keychain."""
    import getpass
    print("=== flex2rijk Keychain Setup ===")
    print(f"Credentials worden opgeslagen onder Keychain service: '{KEYCHAIN_SERVICE}'\n")

    username = input("Gebruikersnaam (bijv. RWS\\tijn.example of gewoon je emailadres): ").strip()
    password = getpass.getpass("Wachtwoord: ")

    keychain_set("username", username)
    keychain_set("password", password)
    print("\n[✓] Setup klaar. Start de login met: python flex2rijk.py")


# ── Citrix ICA download ───────────────────────────────────────────────────────

def open_ica(path: str):
    """Open het ICA bestand met Citrix Workspace (of de standaard handler)."""
    print(f"[→] ICA bestand openen: {path}")
    subprocess.Popen(["open", path])


# ── Login flow ────────────────────────────────────────────────────────────────

def login(headless: bool = True, otp: str = None):
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("[!] Playwright niet gevonden. Installeer met: uv pip install playwright && playwright install chromium")
        sys.exit(1)

    username = keychain_get("username")
    password = keychain_get("password")

    print(f"[✓] Credentials geladen voor: {username}")
    print("[→] Browser starten...")

    # Tijdelijke download map
    download_dir = tempfile.mkdtemp(prefix="flex2rijk_")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print(f"[→] Navigeren naar {LOGIN_URL}")
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

        # ── Inloggen ──
        print("[→] Wachten op loginformulier...")
        page.get_by_role("textbox", name="User name:").wait_for(state="visible", timeout=15000)

        print("[→] Gebruikersnaam invullen...")
        page.get_by_role("textbox", name="User name:").fill(username)

        print("[→] Wachtwoord invullen...")
        page.get_by_role("textbox", name="Password:").fill(password)

        if not otp:
            print("\n" + "="*50)
            otp = input("🔐 Voer je OneSpan token in: ").strip()
            print("="*50 + "\n")

        print("[→] Token invullen...")
        page.get_by_role("textbox", name="Token:").fill(otp)

        print("[→] Log On klikken...")
        page.get_by_role("link", name="Log On").click()

        # ── Wacht op ICA download of desktop launcher ──
        print("[→] Wachten op Citrix sessie / ICA download...")
        ica_path = _wait_for_ica(page, context, download_dir)

        browser.close()

    if ica_path:
        open_ica(ica_path)
        print("[✓] Klaar! Citrix Workspace wordt geopend.")
    else:
        print("[!] Geen ICA bestand gevonden. Mogelijk is de sessie al direct geopend via de browser.")


# ── Page interaction helpers ──────────────────────────────────────────────────

def _wait_for_login_form(page):
    """Wacht tot er een username of password input zichtbaar is."""
    from playwright.sync_api import TimeoutError as PWTimeout

    selectors = [
        "input[name='login']",
        "input[name='passwd']",
        "input[id='login']",
        "input[id='passwd']",
        "input[type='text']",
        "input[placeholder*='gebruiker' i]",
        "input[placeholder*='user' i]",
        "input[autocomplete='username']",
        "#loginForm",
        ".login-form",
    ]

    combined = ", ".join(selectors)
    try:
        page.wait_for_selector(combined, timeout=15000, state="visible")
        print("[✓] Loginformulier gevonden")
        return
    except PWTimeout:
        pass

    # Als niets werkt: screenshot voor debug
    page.screenshot(path="/tmp/flex2rijk_debug.png")
    print("[!] Loginformulier niet herkend. Screenshot opgeslagen in /tmp/flex2rijk_debug.png")
    print("    Probeer opnieuw met: python flex2rijk.py --no-headless")
    sys.exit(1)


def _fill_username(page, username: str):
    """Vul gebruikersnaam in — probeert meerdere bekende Citrix selectors."""
    selectors = [
        "input[name='login']",
        "input[id='login']",
        "input[autocomplete='username']",
        "input[type='text']:visible",
        "input[placeholder*='user' i]",
        "input[placeholder*='naam' i]",
    ]
    _fill_first_match(page, selectors, username, "gebruikersnaam")


def _fill_password(page, password: str):
    """Vul wachtwoord in."""
    selectors = [
        "input[name='passwd']",
        "input[id='passwd']",
        "input[type='password']",
        "input[autocomplete='current-password']",
    ]
    _fill_first_match(page, selectors, password, "wachtwoord")


def _fill_2fa(page, otp: str):
    """Vul de 2FA code in."""
    selectors = [
        "input[name='passwd1']",      # Citrix tweede factor veld
        "input[name='passwd2']",
        "input[id='passwd1']",
        "input[id='passwd2']",
        "input[name='otp']",
        "input[name='passcode']",
        "input[placeholder*='code' i]",
        "input[placeholder*='token' i]",
        "input[type='password']",     # Fallback: enige password veld zichtbaar
        "input[type='text']:visible", # Of text veld
    ]
    _fill_first_match(page, selectors, otp, "2FA code")


def _fill_first_match(page, selectors: list, value: str, label: str):
    """Probeer selectors op volgorde en vul de eerste werkende in."""
    from playwright.sync_api import TimeoutError as PWTimeout

    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=3000, state="visible")
            if el:
                el.fill(value)
                print(f"[✓] {label} ingevuld via: {sel}")
                return
        except PWTimeout:
            continue

    page.screenshot(path="/tmp/flex2rijk_debug.png")
    print(f"[!] Kon {label} veld niet vinden. Screenshot: /tmp/flex2rijk_debug.png")
    sys.exit(1)


def _click_login(page):
    """Klik op de login/submit knop."""
    from playwright.sync_api import TimeoutError as PWTimeout

    combined = "input[type='submit'], button[type='submit'], input[value='Log On' i], input[value='Inloggen' i], #loginBtn"

    try:
        btn = page.wait_for_selector(combined, timeout=5000, state="visible")
        if btn:
            btn.click()
            print("[✓] Login knop geklikt")
            time.sleep(1)
            return
    except PWTimeout:
        pass

    # Fallback 1: JS click op eerste submit element
    clicked = page.evaluate("""() => {
        const btn = document.querySelector("input[type='submit'], button[type='submit']");
        if (btn) { btn.click(); return true; }
        return false;
    }""")
    if clicked:
        print("[✓] Login knop geklikt via JavaScript")
        time.sleep(1)
        return

    # Fallback 2: Submit het formulier direct
    submitted = page.evaluate("""() => {
        const form = document.querySelector("form");
        if (form) { form.submit(); return true; }
        return false;
    }""")
    if submitted:
        print("[✓] Formulier gesubmit via JavaScript")
        time.sleep(1)
        return

    print("[!] Kon login knop niet vinden of klikken")


def _wait_for_2fa(page):
    """Wacht tot het 2FA scherm verschijnt."""
    from playwright.sync_api import TimeoutError as PWTimeout

    # Citrix NetScaler gebruikt passwd1 of een tweede wachtwoordveld voor 2FA
    selectors = [
        "input[name='passwd1']",
        "input[name='passwd2']",
        "input[name='otp']",
        "input[name='passcode']",
        "input[placeholder*='code' i]",
        "input[placeholder*='token' i]",
    ]

    combined = ", ".join(selectors)
    print("[→] Wachten op 2FA veld (max 20s)...")
    try:
        page.wait_for_selector(combined, timeout=20000, state="visible")
        print("[✓] 2FA veld gevonden")
        return
    except PWTimeout:
        pass

    # 2FA veld niet gevonden: screenshot en stoppen
    page.screenshot(path="/tmp/flex2rijk_2fa_debug.png")
    print("[!] 2FA veld niet gevonden. Screenshot: /tmp/flex2rijk_2fa_debug.png")
    print("    Probeer opnieuw met: flex2rijk --no-headless")
    sys.exit(1)


STORE_URL = "https://www.flex2rijk.nl/Citrix/DWR-StoreWeb/"


def _wait_for_ica(page, context, download_dir: str) -> str | None:
    """Wacht tot de login redirect naar de store leidt en vang de ICA download op."""
    from playwright.sync_api import TimeoutError as PWTimeout

    print("[→] Wachten op detectiepagina...")
    try:
        detect = page.get_by_role("link", name="Detect Citrix Workspace app")
        detect.wait_for(state="visible", timeout=15000)
        print("[→] 'Detect Citrix Workspace app' klikken...")
        detect.click()

        print("[→] 'Already installed' klikken...")
        with page.expect_download(timeout=20000) as dl_info:
            page.get_by_role("link", name="Already installed").click()
        download = dl_info.value
        ica_path = os.path.join(download_dir, download.suggested_filename or "session.ica")
        download.save_as(ica_path)
        print(f"[✓] ICA gedownload: {ica_path}")
        return ica_path
    except PWTimeout:
        page.screenshot(path="/tmp/flex2rijk_ica_debug.png")
        print(f"[!] Mislukt. URL: {page.url}")
        print(f"    Screenshot: /tmp/flex2rijk_ica_debug.png")
        return None


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="flex2rijk.nl automatische login")
    parser.add_argument("token", nargs="?", help="OneSpan token (optioneel, anders interactief gevraagd)")
    parser.add_argument("--setup", action="store_true", help="Sla credentials op in macOS Keychain")
    parser.add_argument("--no-headless", action="store_true", help="Toon de browser (handig voor debuggen)")
    args = parser.parse_args()

    if args.setup:
        setup()
    else:
        login(headless=not args.no_headless, otp=args.token)


if __name__ == "__main__":
    main()
