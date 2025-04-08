import os
import json
from datetime import datetime, timedelta
import pytz
from twelvedata import TDClient
import firebase_admin
from firebase_admin import credentials, db
from strategy_ema_rsi import analyze

# 1. Aktuelle Uhrzeit in New Yorker Börsenzeit (EDT/EST)
ny_tz = pytz.timezone("America/New_York")
now_ny = datetime.now(ny_tz).replace(second=0, microsecond=0)
date_str = now_ny.strftime("%Y%m%d_%H%M")
hour = now_ny.hour
minute = now_ny.minute

# 2. Zeitfenster prüfen: 09:45 – 15:45 (New Yorker Zeit), nur werktags (Mo–Fr)
total_minutes = hour * 60 + minute

if now_ny.weekday() >= 5:
    print("Heute ist Wochenende. Abbruch.")
    exit(0)

if total_minutes < (9 * 60 + 45) or total_minutes > (15 * 60 + 45):
    print("Außerhalb des Börsen-Zeitfensters (09:45 - 15:45 NY-Zeit). Abbruch.")
    exit(0)

# 3. Zeitraum der letzten 17 Minuten berechnen
end_time = now_ny
start_time = now_ny - timedelta(minutes=17)
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

    # 6. Firebase vorbereiten
    firebase_key = json.loads(os.environ["FIREBASE_KEY"])
    firebase_url = os.environ["FIREBASE_DB_URL"]

    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred, {
        'databaseURL': firebase_url
    })

    # 7. Kursdaten in Firebase speichern
    ref = db.reference(f"/marketdata/NVDA/{date_str}")
    ref.set(response)
    print("Kursdaten wurden in Firebase gespeichert.")

    # 8. Analyse durchführen und bei Signal auch speichern
    signal = analyze(response)
    if signal:
        print(f"Signal erkannt: {signal}")
        signal_ref = db.reference(f"/signals/NVDA/{signal['timestamp']}")
        signal_ref.set(signal)
        print("Signal wurde in Firebase gespeichert.")
    else:
        print("Kein Signal erkannt.")

except Exception as e:
    print("Fehler beim Abruf oder Firebase-Zugriff:", e)
    exit(1)
