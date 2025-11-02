# Market Data Downloader

Dieses Repository enthält ein einzelnes Skript [`main.py`](./main.py), das Kursdaten für ausgewählte Aktien von der Twelve-Data-API abruft und sie sowohl lokal als auch in einer Firebase-Realtime-Datenbank speichert.

## Voraussetzungen
- Python 3.11 oder neuer
- Abhängigkeiten aus [`requirements.txt`](./requirements.txt)
- Gesetzte Umgebungsvariablen:
  - `TWELVE_API_KEY` – API-Schlüssel für Twelve Data
  - `FIREBASE_KEY` – JSON-Inhalt des Firebase-Service-Accounts
  - `FIREBASE_DB_URL` – URL der Firebase-Realtime-Datenbank

## Verwendung
1. Installiere die Abhängigkeiten:
   ```bash
   pip install -r requirements.txt
   ```
2. Setze die oben genannten Umgebungsvariablen.
3. Starte das Skript:
   ```bash
   python main.py
   ```

Während der Ausführung prüft das Skript, ob sich der aktuelle Zeitpunkt innerhalb des Handelsfensters (09:45–15:45 Uhr New Yorker Zeit) befindet und ruft anschließend 1-Minuten-Kerzen für die konfigurierten Symbole ab.

## Projektstruktur
Nach dem Aufräumen bleibt nur der für das Skript notwendige Kern bestehen:
- [`main.py`](./main.py) – Enthält sämtliche Logik für den Datenabruf und die Speicherung.
- [`requirements.txt`](./requirements.txt) – Listet die Python-Abhängigkeiten.
- [`README.md`](./README.md) – Diese Dokumentation.

Alle nicht benötigten Zusatzskripte und Firebase-Cloud-Function-Dateien wurden entfernt, sodass sich das Repository vollständig auf die Python-Anwendung konzentriert.
