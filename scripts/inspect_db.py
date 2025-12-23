#!/usr/bin/env python3
"""inspect_db.py - list recent downloads from the backend DB

Run from repository root with the repo venv active:

  python scripts/inspect_db.py

This prints recent rows and the configured DOWNLOAD_DIR.
"""
import os
import sqlite3
import json
import sys

DB = os.path.join('backend', 'universal_media_downloader.db')
if not os.path.exists(DB):
    print('Database not found:', DB, file=sys.stderr)
    sys.exit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute(
    '''SELECT id,title,status,file_path,file_name,file_size,created_at FROM downloads ORDER BY created_at DESC LIMIT 50'''
)
rows = []
for r in cur.fetchall():
    rows.append(
        {
            'id': r[0],
            'title': r[1],
            'status': r[2],
            'file_path': r[3],
            'file_name': r[4],
            'file_size': r[5],
            'created_at': str(r[6]) if r[6] is not None else None,
        }
    )

download_dir = None
try:
    # Load backend/app/config.py by file path to avoid package import issues in scripts
    import importlib.machinery
    import types
    config_path = os.path.join(os.getcwd(), 'backend', 'app', 'config.py')
    if os.path.exists(config_path):
        loader = importlib.machinery.SourceFileLoader("backend_app_config", config_path)
        cfg = types.ModuleType("backend_app_config")
        loader.exec_module(cfg)
        settings = getattr(cfg, "settings", None)
        if settings is not None:
            download_dir = str(settings.DOWNLOAD_DIR)
except Exception:
    download_dir = None

print(json.dumps({'db': DB, 'download_dir': download_dir,
      'rows': rows}, default=str, indent=2))
