# flex2rijk

[![PyPI version](https://badge.fury.io/py/flex2rijk.svg)](https://badge.fury.io/py/flex2rijk)
[![CI & Publish](https://github.com/tijnschouten/flex2rijk/actions/workflows/pypi-publish.yml/badge.svg)](https://github.com/tijnschouten/flex2rijk/actions/workflows/pypi-publish.yml)

Automatiseert de login op flex2rijk.nl:

- **Cross-platform:** Werkt op macOS, Windows en Linux.
- **Veilig:** Slaat credentials op in je systeem-keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service) via `keyring`.
- **Modern:** Volledig herschreven in moderne Python (Pathlib, Type Hinting).
- **Robuust:** Bevat unit tests en strikte linting (Ruff, MyPy, Pylint).

## Disclaimer

**Let op:** Deze tool is **geen** officieel product van flex2rijk of de betrokken overheidsinstanties. De auteur is op geen enkele wijze geassocieerd met flex2rijk.nl.

- **Geen Support:** Deze tool wordt geleverd "as-is" zonder enige vorm van garantie of support.
- **Eigen Risico:** Het gebruik van deze tool is volledig voor eigen risico. De auteur is niet verantwoordelijk voor eventuele schade, verlies van gegevens, of beveiligingsincidenten (zoals het verlies van wachtwoorden).
- **Doel:** Deze tool is uitsluitend bedoeld om de login-flow te automatiseren voor gebruikers die reeds rechtmatige toegang hebben tot de flex2rijk omgeving.

---

## Installatie

### 1. Installeer de tool (via uv)

De makkelijkste manier is via `uv`. Dit installeert de tool in een geïsoleerde omgeving:

```bash
uv tool install flex2rijk
```

### 2. Setup credentials (eenmalig)

Sla je gebruikersnaam en wachtwoord veilig op in je systeem-keychain:

```bash
flex2rijk --setup
```

---

## Gebruik

```bash
# Start login (browser op achtergrond)
# Bij de eerste keer wordt Chromium automatisch geïnstalleerd
flex2rijk

# Debug modus (browser zichtbaar)
flex2rijk --no-headless

# OneSpan token direct meegeven
flex2rijk 123456
```

---

## Ontwikkeling

### Installeren vanaf source
Als je de tool wilt aanpassen of testen vanaf de broncode:

```bash
git clone https://github.com/tijnschouten/flex2rijk.git
cd flex2rijk
uv tool install .
```

### Development omgeving setup
```bash
uv sync --all-groups
uv run pre-commit install
```

### Tests & Checks draaien
```bash
# Draai alle unit tests
uv run pytest

# Draai alle linters en formatters
uv run pre-commit run --all-files
```

---

## CI/CD & Publicatie

Dit project gebruikt GitHub Actions voor automatische tests en publicatie naar PyPI.

### Automatische Publicatie (Trusted Publishing)
Om automatisch te publiceren naar PyPI wanneer je een nieuwe tag aanmaakt (bijv. `v0.1.0`):

1. Ga naar je [PyPI account settings](https://pypi.org/manage/account/publishing/).
2. Voeg een **GitHub Publisher** toe voor dit repository:
   - **GitHub Repository Owner**: Je username.
   - **Repository Name**: `flex2rijk`.
   - **Workflow Name**: `pypi-publish.yml`.
   - **Environment Name**: `release`.
3. Wanneer je een tag pusht, zal de GitHub Action de tool automatisch builden en uploaden naar PyPI.

---

## Troubleshooting

- **"os.startfile niet beschikbaar":** Gebeurt alleen als je op een niet-Windows systeem probeert de Windows flow te forceren.
- **Loginformulier niet herkend:** Run met `--no-headless` om te zien waar Playwright blijft hangen.
- **ICA opent niet op Linux:** Zorg dat `xdg-open` correct geconfigureerd is voor `.ica` bestanden.
