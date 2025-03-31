import os
import json
from datetime import datetime, timedelta
from twelvedata import TDClient
import firebase_admin
from firebase_admin import credentials, db

# 1. Aktuelles Datum und Uhrzeit ermitteln (UTC)
now = datetime.utcnow()
date_str = now.strftime("%Y%m%d_%H%M")
hour = now.hour
minute = now.minute

# 2. Zeitfenster: 15:45 bis 21:45 UTC und nur werktags (Mo–Fr)
total_minutes = hour * 60 + minute

if now.weekday() >= 5:
    print("Heute ist Wochenende. Abbruch.")
    exit(0)

if total_minutes < (15 * 60 + 45) or total_minutes > (21 * 60 + 45):
    print("Außerhalb des Zeitfensters (15:45 - 21:45 UTC). Abbruch.")
    exit(0)

# 3. Zeitspanne der letzten 15 Minuten berechnen
end_time = now
start_time = now - timedelta(minutes=15)

start_date = start_time.strftime("%Y-%m-%d %H:%M:%S")
end_date = end_time.strftime("%Y-%m-%d %H:%M:%S")

# 4. Twelve Data API aufrufen
api_key = os.environ["TWELVE_API_KEY"]
td = TDClient(apikey=api_key)

try:
    response = td.time_series(
        symbol="NVDA",
        interval="1min",
        start_date=start_date,
        end_date=end_date
    ).as_json()

    if not response or isinstance(response, dict) and "status" in response:
        print("Keine Daten verfügbar oder API-Fehlermeldung:", response.get("message", "Unbekannter Fehler"))
        exit(0)

    # 5. JSON-Datei lokal speichern
    filename = f"{date_str}.json"
    with open(filename, "w") as f:
        json.dump(response, f, indent=4)
    print(f"Datei gespeichert: {filename}")

    # 6. Firebase vorbereiten und hochladen
    firebase_key = json.loads(os.environ["FIREBASE_KEY"])
    firebase_url = os.environ["FIREBASE_DB_URL"]

    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred, {
        'databaseURL': firebase_url
    })

    ref = db.reference(f"/marketdata/NVDA/{date_str}")
    ref.set(response)
    print("Daten wurden in Firebase gespeichert.")

except Exception as e:
    print("Fehler beim Abruf oder Firebase-Zugriff:", e)
    exit(1)
