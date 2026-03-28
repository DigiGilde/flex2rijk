#!/usr/bin/env python3
"""
flex2rijk.py — Automatische login voor flex2rijk.nl Citrix werkplek

Slaat credentials veilig op, vraagt de OneSpan 2FA code interactief op,
en download + opent het ICA bestand.
"""

import argparse
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

try:
    import keyring
except ImportError:
    keyring = None  # type: ignore

KEYCHAIN_SERVICE = "flex2rijk"
LOGIN_URL = "https://www.flex2rijk.nl/logon/LogonPoint/tmindex.html"


# ── Credential helpers (Multi-platform) ───────────────────────────────────────


def keychain_get(account: str) -> str:
    """Lees een waarde uit het systeem-credential-beheer."""
    if platform.system() == "Darwin":
        return _macos_keychain_get(account)
    return _keyring_get(account)


def keychain_set(account: str, password: str) -> None:
    """Sla een waarde op in het systeem-credential-beheer."""
    if platform.system() == "Darwin":
        _macos_keychain_set(account, password)
    else:
        _keyring_set(account, password)


def _macos_keychain_get(account: str) -> str:
    """Lees een waarde direct uit de macOS Keychain via de 'security' CLI."""
    cmd = ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", account, "-w"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"[!] Kan '{account}' niet vinden in macOS Keychain.")
        print("    Voer eerst uit: flex2rijk --setup")
        sys.exit(1)
    return result.stdout.strip()


def _macos_keychain_set(account: str, password: str) -> None:
    """Sla een waarde op in de macOS Keychain via de 'security' CLI."""
    # Verwijder eerst om 'already exists' fouten te voorkomen
    del_cmd = ["security", "delete-generic-password", "-s", KEYCHAIN_SERVICE, "-a", account]
    subprocess.run(del_cmd, capture_output=True, check=False)

    add_cmd = [
        "security",
        "add-generic-password",
        "-s",
        KEYCHAIN_SERVICE,
        "-a",
        account,
        "-w",
        password,
    ]
    result = subprocess.run(add_cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"[!] Fout bij opslaan in macOS Keychain: {result.stderr}")
        sys.exit(1)
    print(f"[✓] '{account}' opgeslagen in macOS Keychain.")


def _keyring_get(account: str) -> str:
    """Lees een waarde via de 'keyring' bibliotheek (Windows/Linux)."""
    if not keyring:
        print("[!] Keyring-bibliotheek niet gevonden.")
        sys.exit(1)

    password = keyring.get_password(KEYCHAIN_SERVICE, account)
    if not password:
        print(f"[!] Kan '{account}' niet vinden in credential-beheer.")
        print("    Voer eerst uit: flex2rijk --setup")
        sys.exit(1)
    return str(password)


def _keyring_set(account: str, password: str) -> None:
    """Sla een waarde op via de 'keyring' bibliotheek (Windows/Linux)."""
    if not keyring:
        print("[!] Keyring-bibliotheek niet gevonden.")
        sys.exit(1)

    try:
        keyring.set_password(KEYCHAIN_SERVICE, account, password)
    except (OSError, RuntimeError) as e:
        print(f"[!] Fout bij opslaan in credential-beheer: {e}")
        print("\nTip voor Linux: Installeer 'keyrings.alt' voor headless omgevingen:")
        print("    uv add keyrings.alt")
        sys.exit(1)
    print(f"[✓] '{account}' opgeslagen in credential-beheer.")


def setup() -> None:
    """Interactieve setup: sla credentials op in het systeem-credential-beheer."""
    import getpass

    print("=== flex2rijk Setup ===")
    backend = "macOS Keychain" if platform.system() == "Darwin" else "System Keyring"
    print(f"Gebruikt backend: {backend}")
    print(f"Credentials worden opgeslagen onder service: '{KEYCHAIN_SERVICE}'\n")

    username = input("Gebruikersnaam (bijv. RWS\\tijn.example of email): ").strip()
    password = getpass.getpass("Wachtwoord: ")

    keychain_set("username", username)
    keychain_set("password", password)
    print("\n[✓] Setup klaar. Start de login met: flex2rijk")


# ── Citrix ICA download ───────────────────────────────────────────────────────


def _open_ica_macos(path: Path) -> None:
    """Open het ICA bestand op macOS met subprocess.Popen."""
    with subprocess.Popen(["open", str(path.absolute())]) as _:
        pass


def _open_ica_windows(path: Path) -> None:
    """Open het ICA bestand op Windows."""
    if hasattr(os, "startfile"):
        os.startfile(str(path.absolute()))
    else:
        print("[!] os.startfile niet beschikbaar op dit systeem.")


def _open_ica_linux(path: Path) -> None:
    """Open het ICA bestand op Linux met subprocess.Popen."""
    with subprocess.Popen(["xdg-open", str(path.absolute())]) as _:
        pass


def _dispatch_open(current_os: str, path: Path) -> None:
    """Stuur het openen van het bestand naar de juiste OS-functie."""
    if current_os == "darwin":
        _open_ica_macos(path)
    elif current_os == "windows":
        _open_ica_windows(path)
    else:
        _open_ica_linux(path)


def open_ica(path: Path) -> None:
    """Open het ICA bestand met Citrix Workspace op een cross-platform manier."""
    if not path.exists():
        print(f"[!] Fout: ICA bestand niet gevonden op {path}")
        return

    print(f"[→] ICA bestand openen: {path}")
    current_os = platform.system().lower()
    try:
        _dispatch_open(current_os, path)
    except (OSError, subprocess.SubprocessError) as e:
        print(f"[!] Kon ICA bestand niet automatisch openen: {e}")
        print(f"    Open het bestand handmatig: {path}")


# ── Login flow ────────────────────────────────────────────────────────────────


def login(headless: bool = True, otp: Optional[str] = None) -> None:
    """Voer de volledige login-flow uit."""
    username = keychain_get("username")
    password = keychain_get("password")

    print(f"[✓] Credentials geladen voor: {username}")

    with tempfile.TemporaryDirectory(prefix="flex2rijk_") as download_dir:
        ica_path = _run_browser(headless, username, password, otp, Path(download_dir))

        if ica_path:
            open_ica(ica_path)
            print("[✓] Klaar! Citrix Workspace wordt geopend.")
            # Geef de applicatie de tijd om het bestand te laden voordat de map verdwijnt
            time.sleep(15)
        else:
            print("[!] Geen ICA bestand gevonden.")


def _run_browser(
    headless: bool, username: str, password: str, otp: Optional[str], download_dir: Path
) -> Optional[Path]:
    """Start de browser en voer de login uit."""
    _ensure_playwright_browsers()

    from playwright.sync_api import sync_playwright

    print("[→] Browser starten...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        _perform_page_login(page, username, password, otp)

        print("[→] Wachten op Citrix sessie / ICA download...")
        ica_path = _wait_for_ica(page, download_dir)

        browser.close()
        return ica_path


def _ensure_playwright_browsers() -> None:
    """Controleer of Playwright browsers zijn geïnstalleerd, installeer ze zo niet."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # Probeer browser te starten om te checken of deze er is
            browser = p.chromium.launch()
            browser.close()
    except (ImportError, Exception):  # pylint: disable=broad-exception-caught
        print("[→] Playwright browser (Chromium) niet gevonden. Installeren...")
        # Installeer alleen chromium (is sneller en kleiner dan alles)
        cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
        subprocess.run(cmd, check=True)
        print("[✓] Chromium succesvol geïnstalleerd.")


def _perform_page_login(page: Any, username: str, password: str, otp: Optional[str]) -> None:
    """Navigeer naar de loginpagina en vul de gegevens in."""
    print(f"[→] Navigeren naar {LOGIN_URL}")
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)

    print("[→] Wachten op loginformulier...")
    page.get_by_role("textbox", name="User name:").wait_for(state="visible", timeout=15000)

    print("[→] Gebruikersnaam invullen...")
    page.get_by_role("textbox", name="User name:").fill(username)

    print("[→] Wachtwoord invullen...")
    page.get_by_role("textbox", name="Password:").fill(password)

    if not otp:
        print("\n" + "=" * 50)
        otp = input("🔐 Voer je OneSpan token in: ").strip()
        print("=" * 50 + "\n")

    print("[→] Token invullen...")
    page.get_by_role("textbox", name="Token:").fill(otp)

    print("[→] Log On klikken...")
    page.get_by_role("link", name="Log On").click()


# ── Page interaction helpers ──────────────────────────────────────────────────


def _click_login(page: Any) -> None:
    """Klik op de login/submit knop (fallback voor complexe pagina's)."""
    from playwright.sync_api import Error as PWError

    selectors = [
        "input[type='submit']",
        "button[type='submit']",
        "input[value='Log On' i]",
        "#loginBtn",
    ]
    combined = ", ".join(selectors)

    try:
        btn = page.wait_for_selector(combined, timeout=5000, state="visible")
        if btn:
            btn.click()
            print("[✓] Login knop geklikt")
            return
    except PWError:
        # Fallback bij fouten (bijv. timeout of navigatie tijdens selector wacht)
        pass

    _click_login_fallback(page)


def _click_login_fallback(page: Any) -> None:
    """JS-gebaseerde fallbacks voor het klikken op de login-knop."""
    clicked = page.evaluate(
        """() => {
        const btn = document.querySelector("input[type='submit'], button[type='submit']");
        if (btn) { btn.click(); return true; }
        return false;
    }"""
    )
    if clicked:
        print("[✓] Login knop geklikt via JavaScript")
        return

    _submit_form_fallback(page)


def _submit_form_fallback(page: Any) -> None:
    """JS-gebaseerde fallback voor het submiten van het formulier."""
    submitted = page.evaluate(
        """() => {
        const form = document.querySelector("form");
        if (form) { form.submit(); return true; }
        return false;
    }"""
    )
    if submitted:
        print("[✓] Formulier gesubmit via JavaScript")
        return

    print("[!] Kon login knop niet vinden of klikken")


def _wait_for_ica(page: Any, download_dir: Path) -> Optional[Path]:
    """Wacht tot de login redirect naar de store leidt en vang de ICA download op."""
    from playwright.sync_api import TimeoutError as PWTimeout

    print("[→] Wachten op detectiepagina...")
    try:
        # 1. Klik op detectie
        _handle_detect_button(page)

        # 2. Klik op 'Already installed' en vang download op
        with page.expect_download(timeout=20000) as dl_info:
            _handle_install_button(page)

        download = dl_info.value
        filename = download.suggested_filename or "session.ica"
        ica_path = download_dir / filename
        download.save_as(str(ica_path))

        print(f"[✓] ICA succesvol gedownload naar: {ica_path}")
        return ica_path
    except PWTimeout:
        print("[!] Timeout tijdens wachten op ICA download.")
        page.screenshot(path="/tmp/flex2rijk_ica_timeout.png")
        return None


def _handle_detect_button(page: Any) -> None:
    """Klik op de 'Detect Citrix Workspace app' knop."""
    try:
        detect = page.get_by_role("link", name="Detect Citrix Workspace app")
        detect.wait_for(state="visible", timeout=15000)
        print("[→] 'Detect Citrix Workspace app' gevonden, klikken...")
        detect.click()
    except Exception:  # pylint: disable=broad-exception-caught
        # Knop wellicht niet aanwezig, negeer en ga door naar volgende stap
        pass


def _handle_install_button(page: Any) -> None:
    """Klik op de 'Already installed' knop."""
    installed = page.get_by_role("link", name="Already installed")
    installed.wait_for(state="visible", timeout=10000)
    print("[→] 'Already installed' gevonden, klikken...")
    installed.click()


# ── Entrypoint ────────────────────────────────────────────────────────────────


def main() -> None:
    """Main entrypoint voor de CLI."""
    parser = argparse.ArgumentParser(description="flex2rijk.nl automatische login")
    parser.add_argument("token", nargs="?", help="OneSpan token")
    parser.add_argument("--setup", action="store_true", help="Sla credentials op")
    parser.add_argument("--no-headless", action="store_true", help="Toon de browser")
    args = parser.parse_args()

    if args.setup:
        setup()
    else:
        login(headless=not args.no_headless, otp=args.token)


if __name__ == "__main__":
    main()
