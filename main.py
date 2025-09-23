import os
import json
from datetime import datetime, timedelta
import pytz
from twelvedata import TDClient
import firebase_admin
from firebase_admin import credentials, db
#from old.strategy_ema_rsi import analyze

#ENABLE_ANALYZE = False

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

symbols = ["NVDA","TSM"]

try:
    # 5. Firebase vorbereiten
    firebase_key = json.loads(os.environ["FIREBASE_KEY"])
    firebase_url = os.environ["FIREBASE_DB_URL"]

    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred, {
        'databaseURL': firebase_url
    })
    for symbol in symbols:
        print(f"Abruf der Kursdaten für {symbol} von {start_date} bis {end_date}...")
        response = td.time_series(
            symbol=symbol,
            interval="1min",
            start_date=start_date,
            end_date=end_date
        ).as_json()
        # Twelve Data kann bei fehlenden Kursdaten ein leeres Tuple zurückgeben.
        if isinstance(response, (list, tuple)) and len(response) == 0:
            print("Keine Kursdaten vom API erhalten (leere Antwort).")
            exit(0)

        if isinstance(response, dict) and "status" in response:
            print("API-Fehlermeldung:", response.get("message", "Unbekannter Fehler"))
            exit(0)

        if not response:
            print("Unerwartete leere Antwort vom API.")
            exit(0)

        if not response or isinstance(response, dict) and "status" in response:
            print(f"Keine Daten verfügbar oder API-Fehlermeldung für {symbol}:", response.get("message", "Unbekannter Fehler"))
            continue

        # 6. JSON-Datei lokal speichern
        filename = f"{symbol}_{date_str}.json"
        with open(filename, "w") as f:
            json.dump(response, f, indent=4)
        print(f"Datei gespeichert: {filename}")

        # 7. Kursdaten in Firebase speichern
        ref = db.reference(f"/marketdata/{symbol}/{date_str}")
        ref.set(response)
        print(f"Kursdaten für {symbol} wurden in Firebase gespeichert.")

        #8. Analyse durchführen und bei Signal auch speichern
        # if ENABLE_ANALYZE:
        #    signal = analyze(response)
        #    if signal:
        #        print(f"Signal erkannt für {symbol}: {signal}")
        #        signal_ref = db.reference(f"/signals/{symbol}/{signal['timestamp']}")
        #        signal_ref.set(signal)
        #        print("Signal wurde in Firebase gespeichert.")
        #    else:
        #        print(f"Kein Signal erkannt für {symbol}.")

except Exception as e:
    print("Fehler beim Abruf oder Firebase-Zugriff:", e)
    exit(1)
