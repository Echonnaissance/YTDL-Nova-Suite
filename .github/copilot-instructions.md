<!-- GitHub Copilot / AI Agent instructions for the Universal Media Downloader repo -->
# Quick AI onboarding

This file exists to help AI coding agents be productive immediately. Focus on the concrete patterns, commands, and files that are important to make changes safely.

## Big picture
- Backend: FastAPI application in `backend/app` — entrypoint: `backend/app/main.py`.
- Frontend: React + Vite in `frontend/` — entrypoint: `frontend/src/main.jsx` and `frontend/package.json`.
- Standalone CLI + packaging: `UniversalMediaDownloader.py` (CLI) and `build-exe.ps1` / `UniversalMediaDownloader.spec` for PyInstaller builds.
- External binaries expected in repository root: `yt-dlp.exe` and `ffmpeg.exe` (also looked for under `dist/` or `backend/`).

## How to run locally (developer workflow)
- Start both dev servers: run `start-dev.bat` (Windows) which launches the backend and frontend in separate windows.
- Backend quick start (Windows):
  - `cd backend` → `python -m venv venv` → `venv\Scripts\activate` → `pip install -r requirements.txt` → `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`.
- Frontend quick start:
  - `cd frontend` → `npm install` → `npm run dev` (Vite default port 5173).
- CLI testing: `python UniversalMediaDownloader.py <URL>` (auto-detects `yt-dlp` and `ffmpeg`).
- Packaging: use `build-exe.ps1` (PowerShell) which runs PyInstaller — see `--Test` and `--Clean` switches in the script.

## Key patterns & conventions (do not invent alternatives)
- Configuration is centralized in `backend/app/config.py` using Pydantic settings. Use environment variables or the `.env` file (Config.Config.env_file = `.env`).
- Binary discovery: code searches for `yt-dlp.exe` and `ffmpeg.exe` in project root, `backend/`, `dist/`, and script directory. Keep that behavior when moving binaries.
- Services and business logic live under `backend/app/services/` (download_service.py, ytdlp_service.py, download_queue.py). Prefer modifying or extending these files for download behavior.
- API routes live under `backend/app/api/routes/`. Add endpoints there and wire them into `main.py`.
- Exception types: custom exceptions are defined in `backend/app/core/exceptions.py` and handled centrally in `main.py` — return structured JSON for clients.

## Security & production notes for agents
- `config.py` enforces production checks (validate_secret_key and validate_cors_origins) — avoid committing insecure defaults. Ensure `SECRET_KEY` is set for non-debug environments.
- Production HTTPS behavior is toggleable via `FORCE_HTTPS` and middleware in `main.py`. Follow existing patterns for redirection and header settings.
- The app logs to `app.log` (RotatingFileHandler). Avoid unbounded logging changes that could fill disk.

## Tests, linting, and quick checks
- There is a `backend/tests` folder; run tests with `pytest` from the `backend` directory if present.
- Use the `start-dev.bat` for a fast local smoke test (backend + frontend). Use `build-exe.ps1 -Test` to validate packaged binary.

## Common edits examples
- To add a new API endpoint: add route file in `backend/app/api/routes/`, then import and include it in `backend/app/main.py` (follow existing router imports).
- To modify download behavior: update `backend/app/services/ytdlp_service.py` (yt-dlp invocation patterns) or `download_service.py` (orchestration & validation).
- To change settings: prefer environment variables or `.env`; update defaults in `backend/app/config.py` only when changing global defaults.

## Files to inspect when debugging
- `backend/app/main.py` — app startup, middleware, exception handling.
- `backend/app/config.py` — all runtime settings and path expectations.
- `backend/app/services/ytdlp_service.py` — wrapper around yt-dlp usage.
- `UniversalMediaDownloader.py` — CLI download logic and binary discovery.
- `build-exe.ps1` and `UniversalMediaDownloader.spec` — packaging rules.

## When to ask the human
- If a change requires adding or committing `yt-dlp.exe` or `ffmpeg.exe`, ask for explicit permission — those are large third-party binaries.
- If modifying security-sensitive defaults (CORS, SECRET_KEY, FORCE_HTTPS), request an explicit decision and/or deployment target.

---
If anything here is unclear or you want more detail on a particular area (routes, packaging, or the download queue), tell me which piece to expand or update.
