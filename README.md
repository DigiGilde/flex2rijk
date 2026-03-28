# flex2rijk

Automatiseert de login op flex2rijk.nl:

- **Cross-platform:** Werkt op macOS, Windows en Linux.
- **Veilig:** Slaat credentials op in je systeem-keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service) via `keyring`.
- **Modern:** Volledig herschreven in moderne Python (Pathlib, Type Hinting).
- **Robuust:** Bevat unit tests en strikte linting (Ruff, MyPy, Pylint).

---

## Installatie

### 1. Installeer de tool (via uv)

```bash
uv tool install .
```

### 2. Installeer de Chromium browser

```bash
uvx --from flex2rijk playwright install chromium
```

### 3. Setup credentials (eenmalig)

```bash
flex2rijk --setup
```

---

## Gebruik

```bash
# Start login (browser op achtergrond)
flex2rijk

# Debug modus (browser zichtbaar)
flex2rijk --no-headless

# OneSpan token direct meegeven
flex2rijk 123456
```

---

## Ontwikkeling

Deze tool hanteert strikte kwaliteitseisen:
- **McCabe Complexity:** Maximaal 4.
- **Typing:** Strict MyPy.
- **Linting:** Ruff & Pylint.

### Setup development omgeving
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

## Troubleshooting

- **"os.startfile niet beschikbaar":** Gebeurt alleen als je op een niet-Windows systeem probeert de Windows flow te forceren.
- **Loginformulier niet herkend:** Run met `--no-headless` om te zien waar Playwright blijft hangen.
- **ICA opent niet op Linux:** Zorg dat `xdg-open` correct geconfigureerd is voor `.ica` bestanden.
