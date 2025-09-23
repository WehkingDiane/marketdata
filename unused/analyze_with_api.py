import os
import json
import pytz
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db, messaging

# === Konfiguration ===
SYMBOL = "NVDA"
INTERVAL = "15min"
EMA_SHORT = 9
EMA_LONG = 21
RSI_PERIOD = 14
NOTIFY_ON_SIGNAL = True  # <<<<< Hier Benachrichtigung aktivieren/deaktivieren
FCM_TOKEN = os.getenv("FCM_TOKEN")  # Sollte per Secret gesetzt werden

# === Zeit definieren ===
ny_tz = pytz.timezone("America/New_York")
now = datetime.now(ny_tz)
timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
signal_timestamp = now.strftime("%Y%m%d_%H%M")

# === Twelve Data abrufen ===
api_key = os.getenv("TWELVE_API_KEY")

def get_indicator(indicator):
    url = f"https://api.twelvedata.com/{indicator}"
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "apikey": api_key,
    }
    if indicator == "ema":
        params["time_period"] = EMA_SHORT
    elif indicator == "ema_long":
        url = url.replace("ema_long", "ema")
        params["time_period"] = EMA_LONG
    elif indicator == "rsi":
        params["time_period"] = RSI_PERIOD

    response = requests.get(url, params=params)
    return response.json()

def get_latest_close():
    url = f"https://api.twelvedata.com/time_series"
    params = {
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "outputsize": 1,
        "apikey": api_key,
    }
    response = requests.get(url, params=params)
    data = response.json()
    return float(data["values"][0]["close"]) if "values" in data else None

# === Indikatoren abrufen ===
ema9 = get_indicator("ema")
ema21 = get_indicator("ema_long")
rsi = get_indicator("rsi")
close_price = get_latest_close()

try:
    ema9_val = float(ema9["values"][0]["ema"])
    ema21_val = float(ema21["values"][0]["ema"])
    rsi_val = float(rsi["values"][0]["rsi"])
except Exception as e:
    print("Fehler bei der Verarbeitung der Indikatorwerte:", e)
    exit(1)

# === Analyse durchführen ===
signal = None
if ema9_val > ema21_val and 40 <= rsi_val <= 70:
    signal = {
        "type": "buy",
        "confidence": round((rsi_val - 40) / 30, 2),
        "price": close_price,
        "timestamp": timestamp,
    }
elif ema9_val < ema21_val and 30 <= rsi_val <= 60:
    signal = {
        "type": "sell",
        "confidence": round((60 - rsi_val) / 30, 2),
        "price": close_price,
        "timestamp": timestamp,
    }

if signal:
    print("Signal erkannt:", signal)

    # === Firebase initialisieren ===
    firebase_key = json.loads(os.environ["FIREBASE_KEY"])
    firebase_url = os.environ["FIREBASE_DB_URL"]

    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred, {
        'databaseURL': firebase_url
    })

    # === Signal in Firebase schreiben ===
    ref = db.reference(f"/signals/{SYMBOL}/{signal_timestamp}")
    ref.set(signal)
    print("Signal wurde in Firebase gespeichert.")

    # === Push Notification senden ===
    if NOTIFY_ON_SIGNAL and FCM_TOKEN:
        message = messaging.Message(
            notification=messaging.Notification(
                title=f"Trade-Signal: {signal['type'].upper()} {SYMBOL}",
                body=f"Kurs: {signal['price']} | RSI: {rsi_val:.1f} | {timestamp}",
            ),
            token=FCM_TOKEN,
        )
        response = messaging.send(message)
        print("Benachrichtigung gesendet:", response)

else:
    print("Kein Signal erkannt.")
