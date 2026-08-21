"""Unit-Tests für den Market-Data-Downloader."""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, call, patch

import pytz

import main


class MarketDataTests(unittest.TestCase):
    def test_trading_window_accepts_boundaries(self) -> None:
        timezone = pytz.timezone("America/New_York")

        for hour, minute in ((9, 45), (15, 45)):
            with self.subTest(hour=hour, minute=minute):
                now = timezone.localize(datetime(2026, 8, 21, hour, minute))
                self.assertTrue(main._within_trading_window(now))

    def test_trading_window_rejects_weekend_and_outside_hours(self) -> None:
        timezone = pytz.timezone("America/New_York")
        examples = (
            timezone.localize(datetime(2026, 8, 22, 12, 0)),
            timezone.localize(datetime(2026, 8, 21, 9, 44)),
            timezone.localize(datetime(2026, 8, 21, 15, 46)),
        )

        for now in examples:
            with self.subTest(now=now):
                self.assertFalse(main._within_trading_window(now))

    def test_normalize_response_extracts_values(self) -> None:
        values = [{"close": "100.00"}]

        self.assertEqual(list(main._normalize_response({"values": values})), values)
        self.assertEqual(list(main._normalize_response(values)), values)
        self.assertEqual(list(main._normalize_response({"status": "ok"})), [])

    def test_error_response_recognizes_api_error(self) -> None:
        self.assertTrue(main._is_error_response({"status": "error", "message": "limit"}))
        self.assertFalse(main._is_error_response({"status": "ok", "values": []}))

    def test_require_env_var_rejects_missing_value(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as context:
                main._require_env_var("TWELVE_API_KEY")

        self.assertEqual(context.exception.code, 1)

    def test_store_locally_writes_json(self) -> None:
        payload = {"status": "ok", "values": [{"close": "100.00"}]}

        with tempfile.TemporaryDirectory() as directory:
            with patch("main.open", unittest.mock.mock_open()) as mocked_open:
                main._store_locally("NVDA", "20260821_1545", payload)

            mocked_open.assert_called_once_with(
                "NVDA_20260821_1545.json", "w", encoding="utf-8"
            )
            handle = mocked_open()
            written = "".join(
                item.args[0]
                for item in handle.write.call_args_list
                if item.args
            )
            self.assertEqual(json.loads(written), payload)

    @patch("main.db.reference")
    def test_store_in_firebase_sets_payload(self, reference: MagicMock) -> None:
        payload = {"status": "ok", "values": [{"close": "100.00"}]}

        main._store_in_firebase("NVDA", "20260821_1545", payload)

        reference.assert_called_once_with("/marketdata/NVDA/20260821_1545")
        reference.return_value.set.assert_called_once_with(payload)

    @patch("main._store_in_firebase")
    @patch("main._store_locally")
    @patch("main._initialize_firebase")
    @patch("main.TDClient")
    def test_main_fetches_and_stores_every_symbol(
        self,
        td_client: MagicMock,
        initialize_firebase: MagicMock,
        store_locally: MagicMock,
        store_in_firebase: MagicMock,
    ) -> None:
        payload = {"status": "ok", "values": [{"close": "100.00"}]}
        td_client.return_value.time_series.return_value.as_json.return_value = payload
        fixed_now = main.NY_TZ.localize(datetime(2026, 8, 21, 12, 0))

        with patch.dict(os.environ, {"TWELVE_API_KEY": "test-key"}, clear=True):
            with patch("main.datetime") as mocked_datetime:
                mocked_datetime.now.return_value = fixed_now
                main.main()

        td_client.assert_called_once_with(apikey="test-key")
        initialize_firebase.assert_called_once_with()
        self.assertEqual(td_client.return_value.time_series.call_count, len(main.SYMBOLS))
        self.assertEqual(
            td_client.return_value.time_series.call_args_list,
            [
                call(
                    symbol=symbol,
                    interval="1min",
                    start_date="2026-08-21 11:43:00",
                    end_date="2026-08-21 12:00:00",
                )
                for symbol in main.SYMBOLS
            ],
        )
        self.assertEqual(store_locally.call_count, len(main.SYMBOLS))
        self.assertEqual(store_in_firebase.call_count, len(main.SYMBOLS))


if __name__ == "__main__":
    unittest.main()
