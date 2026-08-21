# Repository Guidelines

## Project Structure & Module Organization

This repository is a small Python 3.11 market-data ingestion service. `main.py` contains the application flow, Twelve Data API calls, trading-window checks, local JSON export, and Firebase writes. Runtime dependencies are listed in the shared root `requirements.txt`; known-good versions are recorded in `docs/tested_versions.md`. Automation lives in `.github/workflows/main.yml`. Root-level `firebase.json` and `.firebaserc` hold Firebase project configuration. Generated files such as `NVDA_20260821_1545.json` are runtime artifacts and should not be committed.

## Setup, Run, and Validation Commands

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv-wsl
source .venv-wsl/bin/activate
python -m pip install -r requirements.txt
```

On Windows, use the separate `.venv` environment and activate it with `.venv\Scripts\Activate.ps1`.

Run the downloader with `python main.py`. It requires `TWELVE_API_KEY`, `FIREBASE_KEY`, and `FIREBASE_DB_URL`; never hard-code these values. The script exits normally outside its 09:45–15:45 New York weekday window. Use `python -m compileall main.py` for a quick syntax check. There is currently no separate build step.

## Coding Style & Naming Conventions

Follow standard PEP 8 conventions: four-space indentation, `snake_case` functions and variables, `UPPER_CASE` constants, and type annotations for function boundaries. Keep API, persistence, and validation work in small focused helpers. Preserve the existing module docstring style and UTF-8 file handling. Prefer `pathlib` for new path logic and avoid accessing library-private state unless necessary.

## Testing Guidelines

Tests use the standard-library `unittest` framework under `tests/`, with files named `test_<feature>.py` and methods named `test_<behavior>()`. Mock Twelve Data, Firebase, time, and environment variables; tests must not call live services or require real credentials. Run the suite with `python -m unittest discover -s tests -v`. No coverage threshold is currently configured.

## Commit & Pull Request Guidelines

Recent history favors short, imperative summaries such as `Remove unused code and document main script`. Keep each commit focused and explain configuration or dependency changes in the body. Pull requests should describe the behavior change, validation performed, required secret or workflow changes, and related issue. Include logs for ingestion changes and screenshots only when UI-based Firebase or Actions configuration is relevant.

## Security & Configuration

Treat API keys, Firebase service-account JSON, database URLs, and downloaded market data as sensitive. Store secrets in environment variables or GitHub Actions secrets, review generated artifacts before sharing, and avoid logging credential payloads.
