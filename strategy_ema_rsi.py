import pandas as pd
import pandas_ta as ta
from typing import List, Dict, Optional
from datetime import datetime
def analyze(candles: List[Dict]) -> Optional[Dict]:
    df = pd.DataFrame(candles)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    # Technische Indikatoren berechnen
    df['EMA9'] = ta.ema(df['close'], length=9)
    df['EMA21'] = ta.ema(df['close'], length=21)
    df['RSI14'] = ta.rsi(df['close'], length=14)
    if len(df) < 21:
        return None  # Nicht genug Daten
    last = df.iloc[-1]
    prev = df.iloc[-2]
    # Trendfilter
    if last['EMA9'] > last['EMA21']:
        trend = 'long'
    elif last['EMA9'] < last['EMA21']:
        trend = 'short'
    else:
        return None
    # Candle-Muster prüfen
    bullish = last['close'] > last['open'] and (last['close'] - last['open']) > ((last['high'] - last['low']) * 0.6)
    bearish = last['close'] < last['open'] and (last['open'] - last['close']) > ((last['high'] - last['low']) * 0.6)
    if trend == 'long' and not bullish:
        return None
    if trend == 'short' and not bearish:
        return None
    # RSI prüfen
    if trend == 'long' and not (40 <= last['RSI14'] <= 70):
        return None
    if trend == 'short' and not (30 <= last['RSI14'] <= 60):
        return None
    # Signal generieren
    signal = {
        "type": "buy" if trend == "long" else "sell",
        "confidence": round(abs(last['RSI14'] - 50) / 50, 2),  # einfache Einschätzung
        "price": round(last['close'], 2),
        "timestamp": last.name.isoformat()
    }
    return signal
