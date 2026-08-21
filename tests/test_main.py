"""Unit-Tests für den Market-Data-Downloader."""

import json
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, call, patch
from zoneinfo import ZoneInfo

from firebase_admin import exceptions as firebase_exceptions
from requests.exceptions import Timeout
from twelvedata.exceptions import InternalServerError, InvalidApiKeyError, TwelveDataError

import main


class MarketDataTests(unittest.TestCase):
    def setUp(self) -> None:
        print_patcher = patch("builtins.print")
        print_patcher.start()
        self.addCleanup(print_patcher.stop)

    def test_trading_window_accepts_boundaries(self) -> None:
        timezone = ZoneInfo("America/New_York")

        for hour, minute in ((9, 45), (15, 45)):
            with self.subTest(hour=hour, minute=minute):
                now = datetime(2026, 8, 21, hour, minute, tzinfo=timezone)
                self.assertTrue(main._within_trading_window(now))

    def test_trading_window_rejects_weekend_and_outside_hours(self) -> None:
        timezone = ZoneInfo("America/New_York")
        examples = (
            datetime(2026, 8, 22, 12, 0, tzinfo=timezone),
            datetime(2026, 8, 21, 9, 44, tzinfo=timezone),
            datetime(2026, 8, 21, 15, 46, tzinfo=timezone),
        )

        for now in examples:
            with self.subTest(now=now):
                self.assertFalse(main._within_trading_window(now))

    def test_trading_window_rejects_nyse_holiday(self) -> None:
        good_friday = datetime(2026, 4, 3, 12, 0, tzinfo=main.NY_TZ)

        self.assertFalse(main._within_trading_window(good_friday))
        self.assertIn("Good Friday", main.NYSE_HOLIDAYS[good_friday.date()])

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

    @patch("main._require_env_var")
    @patch("main.firebase_admin.get_app")
    def test_initialize_firebase_reuses_existing_app(
        self, get_app: MagicMock, require_env_var: MagicMock
    ) -> None:
        main._initialize_firebase()

        get_app.assert_called_once_with()
        require_env_var.assert_not_called()

    @patch("main.firebase_admin.initialize_app")
    @patch("main.credentials.Certificate")
    @patch("main.firebase_admin.get_app", side_effect=ValueError)
    def test_initialize_firebase_creates_missing_app(
        self,
        get_app: MagicMock,
        certificate: MagicMock,
        initialize_app: MagicMock,
    ) -> None:
        firebase_key = {"type": "service_account", "project_id": "test"}

        with patch.dict(
            os.environ,
            {
                "FIREBASE_KEY": json.dumps(firebase_key),
                "FIREBASE_DB_URL": "https://example.firebaseio.com",
            },
            clear=True,
        ):
            main._initialize_firebase()

        get_app.assert_called_once_with()
        certificate.assert_called_once_with(firebase_key)
        initialize_app.assert_called_once_with(
            certificate.return_value,
            {"databaseURL": "https://example.firebaseio.com"},
        )

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

    @patch("main.time.sleep")
    @patch("main.db.reference")
    def test_store_in_firebase_retries_temporary_errors(
        self, reference: MagicMock, sleep: MagicMock
    ) -> None:
        payload = {"status": "ok", "values": [{"close": "100.00"}]}
        reference.return_value.set.side_effect = (
            firebase_exceptions.UnavailableError("temporary"),
            firebase_exceptions.InternalError("temporary"),
            None,
        )

        main._store_in_firebase("NVDA", "20260821_1545", payload)

        self.assertEqual(reference.return_value.set.call_count, 3)
        self.assertEqual(sleep.call_args_list, [call(2), call(4)])

    @patch("main.time.sleep")
    @patch("main.db.reference")
    def test_store_in_firebase_retries_transport_errors(
        self, reference: MagicMock, sleep: MagicMock
    ) -> None:
        payload = {"status": "ok", "values": [{"close": "100.00"}]}
        reference.return_value.set.side_effect = (Timeout("temporary"), None)

        main._store_in_firebase("NVDA", "20260821_1545", payload)

        self.assertEqual(reference.return_value.set.call_count, 2)
        sleep.assert_called_once_with(2)

    @patch("main.time.sleep")
    @patch("main.db.reference")
    def test_store_in_firebase_does_not_retry_permission_error(
        self, reference: MagicMock, sleep: MagicMock
    ) -> None:
        reference.return_value.set.side_effect = (
            firebase_exceptions.PermissionDeniedError("denied")
        )

        with self.assertRaises(firebase_exceptions.PermissionDeniedError):
            main._store_in_firebase("NVDA", "20260821_1545", {"status": "ok"})

        reference.return_value.set.assert_called_once_with({"status": "ok"})
        sleep.assert_not_called()

    @patch("main.time.sleep")
    def test_fetch_time_series_retries_temporary_errors(self, sleep: MagicMock) -> None:
        td_client = MagicMock()
        payload = [{"close": "100.00"}]
        td_client.time_series.return_value.as_json.side_effect = (
            InternalServerError("temporary"),
            Timeout("temporary"),
            payload,
        )

        response = main._fetch_time_series(
            td_client, "NVDA", "2026-08-21 11:43:00", "2026-08-21 12:00:00"
        )

        self.assertEqual(response, payload)
        self.assertEqual(td_client.time_series.call_count, 3)
        self.assertEqual(sleep.call_args_list, [call(2), call(4)])

    @patch("main.time.sleep")
    def test_fetch_time_series_does_not_retry_invalid_key(self, sleep: MagicMock) -> None:
        td_client = MagicMock()
        td_client.time_series.return_value.as_json.side_effect = InvalidApiKeyError(
            "invalid key"
        )

        with self.assertRaises(InvalidApiKeyError):
            main._fetch_time_series(
                td_client, "NVDA", "2026-08-21 11:43:00", "2026-08-21 12:00:00"
            )

        td_client.time_series.assert_called_once_with(
            symbol="NVDA",
            interval="1min",
            start_date="2026-08-21 11:43:00",
            end_date="2026-08-21 12:00:00",
            timezone="America/New_York",
        )
        sleep.assert_not_called()

    @patch("main.time.sleep")
    def test_fetch_time_series_retries_rate_limit(self, sleep: MagicMock) -> None:
        td_client = MagicMock()
        payload = [{"close": "100.00"}]
        td_client.time_series.return_value.as_json.side_effect = (
            TwelveDataError("429 Too Many Requests"),
            payload,
        )

        response = main._fetch_time_series(
            td_client, "NVDA", "2026-08-21 11:43:00", "2026-08-21 12:00:00"
        )

        self.assertEqual(response, payload)
        sleep.assert_called_once_with(2)

    @patch("main.time.sleep")
    def test_fetch_time_series_does_not_retry_unexpected_error(
        self, sleep: MagicMock
    ) -> None:
        td_client = MagicMock()
        td_client.time_series.return_value.as_json.side_effect = RuntimeError(
            "programming error"
        )

        with self.assertRaises(RuntimeError):
            main._fetch_time_series(
                td_client, "NVDA", "2026-08-21 11:43:00", "2026-08-21 12:00:00"
            )

        td_client.time_series.assert_called_once()
        sleep.assert_not_called()

    @patch("main._store_in_firebase")
    @patch("main._store_locally")
    @patch("main._initialize_firebase")
    @patch("main.TDClient")
    def test_main_continues_after_firebase_failure_and_exits_nonzero(
        self,
        td_client: MagicMock,
        initialize_firebase: MagicMock,
        store_locally: MagicMock,
        store_in_firebase: MagicMock,
    ) -> None:
        payload = {"status": "ok", "values": [{"close": "100.00"}]}
        td_client.return_value.time_series.return_value.as_json.return_value = payload
        store_in_firebase.side_effect = (RuntimeError("write failed"), None, None, None)
        fixed_now = datetime(2026, 8, 21, 12, 0, tzinfo=main.NY_TZ)

        with patch.dict(os.environ, {"TWELVE_API_KEY": "test-key"}, clear=True):
            with patch("main.datetime") as mocked_datetime:
                mocked_datetime.now.return_value = fixed_now
                with self.assertRaises(SystemExit) as context:
                    main.main()

        self.assertEqual(context.exception.code, 1)
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
                    timezone="America/New_York",
                )
                for symbol in main.SYMBOLS
            ],
        )
        self.assertEqual(store_locally.call_count, len(main.SYMBOLS))
        self.assertEqual(store_in_firebase.call_count, len(main.SYMBOLS))


if __name__ == "__main__":
    unittest.main()
