"""Script zum Abrufen und Speichern von Kursdaten bei Twelve Data und Firebase."""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Sequence

import firebase_admin
import pytz
from firebase_admin import credentials, db
from twelvedata import TDClient


SYMBOLS: Sequence[str] = ("NVDA", "TSM", "WMT", "AMZN")
NY_TZ = pytz.timezone("America/New_York")
MARKET_OPEN_MINUTE = 9 * 60 + 45
MARKET_CLOSE_MINUTE = 15 * 60 + 45


def _require_env_var(name: str) -> str:
    """Gibt den Inhalt einer Umgebungsvariable zurück oder beendet das Programm."""

    value = os.environ.get(name)
    if not value:
        print(f"Erwartete Umgebungsvariable '{name}' ist nicht gesetzt.")
        sys.exit(1)
    return value


def _within_trading_window(now: datetime) -> bool:
    """Prüft, ob wir uns innerhalb des Handelsfensters befinden."""

    if now.weekday() >= 5:
        print("Heute ist Wochenende. Abbruch.")
        return False

    total_minutes = now.hour * 60 + now.minute
    if not (MARKET_OPEN_MINUTE <= total_minutes <= MARKET_CLOSE_MINUTE):
        print("Außerhalb des Börsen-Zeitfensters (09:45 - 15:45 NY-Zeit). Abbruch.")
        return False
    return True


def _is_error_response(response: Any) -> bool:
    """Bewertet, ob die Antwort der Twelve-Data-API einen Fehler enthält."""

    if isinstance(response, dict) and "status" in response:
        status = response.get("status")
        # Die API liefert "error" bei Fehlschlägen, andere Stati bleiben aber erhalten.
        if status and status.lower() != "ok":
            print("API-Fehlermeldung:", response.get("message", "Unbekannter Fehler"))
            return True
    return False


def _normalize_response(response: Any) -> Iterable[Dict[str, Any]]:
    """Stellt sicher, dass eine iterierbare Antwort zurückgegeben wird."""

    if isinstance(response, (list, tuple)):
        return response
    if isinstance(response, dict) and "values" in response:
        return response["values"]
    return []


def _initialize_firebase() -> None:
    """Initialisiert den Firebase-Client genau einmal."""

    firebase_key = json.loads(_require_env_var("FIREBASE_KEY"))
    firebase_url = _require_env_var("FIREBASE_DB_URL")

    if not firebase_admin._apps:  # type: ignore[attr-defined]
        cred = credentials.Certificate(firebase_key)
        firebase_admin.initialize_app(cred, {"databaseURL": firebase_url})


def _store_locally(symbol: str, date_str: str, payload: Any) -> None:
    filename = f"{symbol}_{date_str}.json"
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)
    print(f"Datei gespeichert: {filename}")


def _store_in_firebase(symbol: str, date_str: str, payload: Any) -> None:
    ref = db.reference(f"/marketdata/{symbol}/{date_str}")
    ref.set(payload)
    print(f"Kursdaten für {symbol} wurden in Firebase gespeichert.")


def main() -> None:
    now_ny = datetime.now(NY_TZ).replace(second=0, microsecond=0)
    date_str = now_ny.strftime("%Y%m%d_%H%M")

    if not _within_trading_window(now_ny):
        sys.exit(0)

    start_time = now_ny - timedelta(minutes=17)
    start_date = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_date = now_ny.strftime("%Y-%m-%d %H:%M:%S")

    td = TDClient(apikey=_require_env_var("TWELVE_API_KEY"))

    try:
        _initialize_firebase()
    except Exception as exc:  # pragma: no cover - defensive logging
        print("Firebase konnte nicht initialisiert werden:", exc)
        sys.exit(1)

    for symbol in SYMBOLS:
        print(f"Abruf der Kursdaten für {symbol} von {start_date} bis {end_date}...")
        try:
            response = td.time_series(
                symbol=symbol,
                interval="1min",
                start_date=start_date,
                end_date=end_date,
            ).as_json()
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"Fehler beim Abruf der Kursdaten für {symbol}:", exc)
            continue

        if not response:
            print("Unerwartete leere Antwort vom API.")
            continue

        if _is_error_response(response):
            continue

        normalized = list(_normalize_response(response))
        if not normalized:
            print("Keine Kursdaten vom API erhalten (leere Antwort).")
            continue

        _store_locally(symbol, date_str, response)
        _store_in_firebase(symbol, date_str, response)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Abbruch durch Benutzer.")
        sys.exit(1)
