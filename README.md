# Market Data Downloader

Dieses Repository enthält ein Python-Skript, das 1-Minuten-Kursdaten ausgewählter Aktien von Twelve Data abruft, als JSON-Dateien speichert und in eine Firebase Realtime Database schreibt.

## Voraussetzungen

- Python 3.11 oder neuer
- Abhängigkeiten aus [`requirements.txt`](./requirements.txt)
- Umgebungsvariablen `TWELVE_API_KEY`, `FIREBASE_KEY` und `FIREBASE_DB_URL`

`FIREBASE_KEY` enthält das vollständige JSON des Firebase-Service-Accounts. Zugangsdaten dürfen nicht in Dateien oder Logs eingecheckt werden.

## Einrichtung

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

WSL/Linux:

```bash
python3 -m venv .venv-wsl
source .venv-wsl/bin/activate
python -m pip install -r requirements.txt
```

Die Abhängigkeiten bleiben absichtlich ohne feste Versionsnummern. Der zuletzt lokal geprüfte Stand ist unter [`docs/tested_versions.md`](./docs/tested_versions.md) dokumentiert.

## Ausführung

```bash
python main.py
```

Das Skript arbeitet montags bis freitags zwischen 09:45 und 15:45 Uhr New Yorker Zeit. Twelve-Data-Anfragen verwenden ausdrücklich `America/New_York`. Temporäre Abruffehler werden maximal zweimal mit 2 beziehungsweise 4 Sekunden Wartezeit wiederholt; ungültige Parameter oder API-Schlüssel werden nicht erneut versucht. Erfolgreiche Antworten werden als `<SYMBOL>_<YYYYMMDD_HHMM>.json` gespeichert und nach `/marketdata/<SYMBOL>/<ZEITSTEMPEL>` in Firebase geschrieben.

Der GitHub-Workflow in [`.github/workflows/main.yml`](./.github/workflows/main.yml) startet den Abruf werktags alle 15 Minuten und stellt erzeugte JSON-Dateien als Workflow-Artefakt bereit.

## Tests

Die Tests verwenden keine echten Zugangsdaten oder Netzwerkverbindungen:

```bash
python -m unittest discover -s tests -v
python -m compileall -q main.py tests
```

## Projektstruktur

- [`main.py`](./main.py) – Abruf-, Validierungs- und Speicherlogik
- [`tests/test_main.py`](./tests/test_main.py) – isolierte Unit-Tests
- [`requirements.txt`](./requirements.txt) – unverankerte Laufzeitabhängigkeiten
- [`docs/tested_versions.md`](./docs/tested_versions.md) – zuletzt geprüfte Versionen
- [`.github/workflows/`](./.github/workflows/) – zeitgesteuerte Automatisierung
