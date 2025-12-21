# Scripts

This folder contains small helper scripts used during development and maintenance of the
Universal Media Downloader project. Most scripts expect to be run from the repository root
and rely on the project's virtual environment (`.venv`). They operate on the repository
layout and the SQLite DB at `backend/universal_media_downloader.db`.

Quick start (Windows PowerShell)

1. Activate the repo venv:

```powershell
& .\.venv\Scripts\Activate.ps1
```

2. Run a script (examples):

```powershell
# consolidated CLI
python .\scripts\cli_tools.py inspect
python .\scripts\cli_tools.py scan-fix-paths
python .\scripts\cli_tools.py populate-meta
python .\scripts\cli_tools.py register --path "C:/path/to/file.mp4"
```

Common scripts

- `api_check.py`: Fetch recent downloads from the API and test `HEAD`/range support for the first media URL.
- `auto_register.py`: Move/copy a local file into `Downloads/Video` and register it (runs related manage tasks).
- `scan_and_fix_paths.py`: Scan `Downloads/Video` and update or insert `downloads` DB rows for completed files.
- `populate_metadata.py`: Extract thumbnails and metadata from local media files and update the DB.
- `fill_durations.py`: Probe local files with `ffprobe` to fill missing `duration` values.
- `inspect_recent.py`: Print recent DB rows with Unicode-escaped fields (Windows-console safe).
- `manage_media.py`: Utility entrypoint used by many scripts to run subcommands like `populate-meta`, `fill-durations`, `scan-fix-paths`, etc.

New consolidated CLI

- `cli_tools.py`: A new consolidated admin CLI that provides subcommands for many previously small scripts: `inspect`, `scan-fix-paths`, `populate-meta`, `fill-durations`, `register`, `dedup`, `find-thumb`, `delete-thumb`, and `remove-ids`.

Notes & best practices

- Run scripts from the repository root so relative path handling works as expected.
- Prefer using the repo venv `python` (`.venv\Scripts\Activate.ps1`) to ensure dependencies are present.
- `ffmpeg.exe` / `ffprobe.exe`: place them in the repository root or ensure they're on your PATH when running `populate_metadata.py` / `fill_durations.py`.
- Windows console Unicode: scripts that call `ffmpeg` already use UTF-8 decoding with `errors='replace'` where possible to avoid noisy UnicodeDecodeErrors.

Removed / consolidated files

- Several very niche one-off scripts were consolidated into `cli_tools.py`. If you relied on any of these exact filenames, update your workflows to call `cli_tools.py` instead. Removed files include:
  - `find_thumb52.py`
  - `delete_thumb52.py`
  - `dedup_file.py`
  - `register_local_file.py`
  - `remove_db_ids.py`
  - `db_recent.py`

If you want these scripts moved into a different folder or packaged as commands, tell me where and I can update paths and imports accordingly.
