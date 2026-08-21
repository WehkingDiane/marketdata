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

Lokal wurden alle drei Pakete aus `requirements.txt` importiert und `main.py`
mit `python -m compileall -q main.py` geprüft. Live-Aufrufe gegen Twelve Data
und Firebase gehören nicht zu diesem Kompatibilitätstest, damit keine API-
Credits oder produktiven Daten verändert werden.

## Aktualisierung

Nach einem erfolgreichen Lauf mit neu installierten Abhängigkeiten:

1. Versionen mit `python -m pip show twelvedata firebase-admin pytz` erfassen.
2. Tests und Syntaxprüfung ausführen.
3. Datum, Versionen und Prüfumfang in dieser Datei aktualisieren.

Ein fehlgeschlagener Lauf nach einem Paketupdate sollte zuerst gegen diese
zuletzt getesteten Versionen verglichen werden.
