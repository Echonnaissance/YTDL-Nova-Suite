#!/usr/bin/env python3
"""auto_fix_missing_paths.py

Search for download DB rows with missing or non-existent `file_path` and attempt
to fix them by locating the file under the project's `Downloads` directory.

Run from the repository root with the venv active:
  python scripts/auto_fix_missing_paths.py
"""
import os
import sqlite3
import datetime
import sys


DB = os.path.join('backend', 'universal_media_downloader.db')
if not os.path.exists(DB):
    print('Database not found:', DB)
    sys.exit(1)


def find_file_in_downloads(download_dir, filename):
    # search recursively for a file with matching basename
    for root, dirs, files in os.walk(download_dir):
        for f in files:
            if f == filename:
                return os.path.abspath(os.path.join(root, f))
    return None


def main():
    # try to import settings.DOWNLOAD_DIR from backend config
    download_dir = None
    try:
        # load the backend/app/config.py module directly to avoid import resolution issues
        config_path = os.path.join(os.getcwd(), 'backend', 'app', 'config.py')
        if os.path.exists(config_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "backend_app_config", config_path)
            if spec is None or spec.loader is None:
                raise RuntimeError(
                    'Could not create module spec for backend app config')
            cfg = importlib.util.module_from_spec(spec)
            # type: ignore[attr-defined]
            spec.loader.exec_module(cfg)
            settings = getattr(cfg, 'settings', None)
            if settings is not None and hasattr(settings, 'DOWNLOAD_DIR'):
                download_dir = str(settings.DOWNLOAD_DIR)
            else:
                raise RuntimeError(
                    "settings or DOWNLOAD_DIR not found in config")
        else:
            raise FileNotFoundError(config_path)
    except Exception:
        download_dir = os.path.abspath(os.path.join(os.getcwd(), 'Downloads'))

    print('Using download_dir =', download_dir)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        'SELECT id, file_name, file_path, status FROM downloads ORDER BY id')
    rows = cur.fetchall()
    updated = 0
    for r in rows:
        id_, file_name, file_path, status = r
        needs_fix = False
        if not file_path:
            needs_fix = True
        else:
            # some DBs store forward slashes; normalize
            p = os.path.abspath(file_path)
            if not os.path.exists(p):
                needs_fix = True

        if not needs_fix:
            continue

        if not file_name:
            print(f'id={id_} missing file_name; skipping')
            continue

        found = find_file_in_downloads(download_dir, file_name)
        if not found:
            print(f'id={id_} file {file_name} not found under {download_dir}')
            continue

        size = os.path.getsize(found)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute(
            'UPDATE downloads SET file_path=?, file_size=?, status=?, completed_at=?, updated_at=? WHERE id=?',
            (found, size, 'COMPLETED', now, now, id_),
        )
        conn.commit()
        updated += 1
        print(f'Updated id={id_} -> {found}')

    print('Done. Updated', updated, 'rows')
    conn.close()


if __name__ == '__main__':
    main()
