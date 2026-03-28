# flex2rijk

Automatiseert de login op flex2rijk.nl:

- Haalt gebruikersnaam + wachtwoord op uit **macOS Keychain**
- Vult credentials automatisch in via Playwright
- Vraagt interactief om je **OneSpan code**
- Download het ICA bestand en opent **Citrix Workspace**

---

## Installatie

### 1. Installeer als uv tool (aanbevolen)

```bash
uv tool install /pad/naar/flex2rijk-tool
```

Of rechtstreeks vanuit de map:

```bash
cd flex2rijk-tool
uv tool install .
```

Daarna is `flex2rijk` beschikbaar als commando in je PATH.

### 2. Installeer de Chromium browser (eenmalig)

```bash
# uv tool run zorgt dat playwright in de juiste omgeving zit:
uvx --from flex2rijk playwright install chromium

# Of als je de tool al hebt geïnstalleerd:
uv run --with playwright playwright install chromium
```

Makkelijkste manier na `uv tool install`:
```bash
python -c "import playwright" 2>/dev/null || uv tool run playwright install chromium
# Of gewoon:
playwright install chromium
```

> **Tip:** Als `playwright install chromium` niet werkt, run dan:
> ```bash
> $(uv tool dir)/flex2rijk/bin/playwright install chromium
> ```

### 3. Sla credentials op in Keychain (eenmalig)

```bash
flex2rijk --setup
```

---

## Gebruik

```bash
# Normaal (browser op achtergrond)
flex2rijk

# Met zichtbare browser — handig bij eerste keer of problemen
flex2rijk --no-headless

# Credentials opnieuw instellen
flex2rijk --setup
```

**Wat er gebeurt:**
1. Playwright-browser opent flex2rijk.nl op de achtergrond
2. Gebruikersnaam + wachtwoord worden automatisch ingevuld vanuit Keychain
3. Terminal toont: `🔐 Voer je OneSpan code in:`
4. Jij typt de 6-cijferige code over uit de OneSpan app
5. Script vult de code in en klikt submit
6. ICA bestand wordt gedownload en geopend → Citrix Workspace start

---

## Troubleshooting

**Loginformulier niet herkend**

Citrix NetScaler-pagina's zijn stuk voor stuk anders geconfigureerd.
Run met `--no-headless` om de browser live te zien. Open DevTools (F12),
klik op het gebruikersnaamveld en check het `name` attribuut. Voeg het toe
aan de `selectors` lijst in `_fill_username` in `cli.py`.

```bash
flex2rijk --no-headless
```

**"Kan 'username' niet vinden in Keychain"**
```bash
flex2rijk --setup
```

**Credentials bekijken/verwijderen**
Open **Sleutelhangertoegang.app** en zoek op `flex2rijk`.

**Citrix Workspace opent niet**
Zorg dat Citrix Workspace geïnstalleerd is en `.ica` bestanden eraan
gekoppeld zijn. Test door handmatig een `.ica` bestand te openen.
