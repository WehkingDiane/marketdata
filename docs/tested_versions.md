# Getestete Versionen

Die Abhängigkeiten bleiben absichtlich ohne feste Versionsnummern, damit der
GitHub-Workflow aktuelle kompatible Releases verwendet. Diese Datei hält den
zuletzt erfolgreich geprüften Stand fest und ist keine Sperrdatei.

## Zuletzt geprüft

Stand: 21. August 2026

| Komponente | Workflow | Lokal (WSL) |
| --- | --- | --- |
| Python | 3.11 | 3.12.3 |
| `twelvedata` | nicht separat geprüft | 1.4.0 |
| `firebase-admin` | nicht separat geprüft | 7.5.0 |
| `pytz` | nicht separat geprüft | 2026.3.post1 |
| `requests` | nicht separat geprüft | 2.34.2 |

### Ausführungsumgebung

| Komponente | Workflow | Lokal (WSL) |
| --- | --- | --- |
| Betriebssystem | `ubuntu-latest`, konkretes Image ausstehend | Ubuntu 24.04.4 LTS |
| `pip` | wird vor der Installation aktualisiert | 24.0 |

Die konkrete Version des veränderlichen `ubuntu-latest`-Runner-Images und die
dort verwendete `pip`-Version können erst aus dem nächsten Workflow-Lauf
übernommen werden. Die Twelve-Data-API und Firebase Realtime Database besitzen
in dieser Integration keine separat wählbare API-Version.

### GitHub-Actions-Konfiguration

| Action | Konfigurierte Version | Laufzeit | Prüfstatus |
| --- | --- | --- | --- |
| `actions/checkout` | v7 | Node.js 24 | lokal geprüft, Workflow-Lauf ausstehend |
| `actions/setup-python` | v7 | Node.js 24 | lokal geprüft, Workflow-Lauf ausstehend |
| `actions/upload-artifact` | v7 | Node.js 24 | lokal geprüft, Workflow-Lauf ausstehend |

Die Action-Majors wurden am 21. August 2026 wegen der Abschaltung der
Node.js-20-Laufzeit aktualisiert. Die drei `uses:`-Einträge und der Workflow-
Diff wurden lokal strukturell geprüft. Nach dem nächsten erfolgreichen Lauf
sollte der Prüfstatus in dieser Tabelle auf `Workflow erfolgreich` gesetzt
werden.

Lokal wurden alle Pakete aus `requirements.txt` installiert und ihre relevanten
Importpfade geprüft. Zusätzlich wurden die Unit-Tests mit
`python -m unittest discover -s tests -v` ausgeführt und `main.py` mit
`python -m compileall -q main.py` geprüft. Live-Aufrufe gegen Twelve Data und
Firebase gehören nicht zu diesem Kompatibilitätstest, damit keine API-Credits
oder produktiven Daten verändert werden.

## Aktualisierung

Nach einem erfolgreichen Lauf mit neu installierten Abhängigkeiten:

1. Direkte Versionen mit `python -m pip list` erfassen.
2. Tests und Syntaxprüfung ausführen.
3. Verwendete Action-Majors in `.github/workflows/main.yml` kontrollieren.
4. Datum, Versionen und Prüfumfang in dieser Datei aktualisieren.

Ein fehlgeschlagener Lauf nach einem Paketupdate sollte zuerst gegen diese
zuletzt getesteten Versionen verglichen werden.
