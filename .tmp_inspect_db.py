import sqlite3
import json
import os
import sys

DB = os.path.join('backend', 'universal_media_downloader.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute(
    '''SELECT id,title,status,file_path,file_name,file_size,created_at FROM downloads ORDER BY created_at DESC LIMIT 20'''
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

sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
try:
    from app.config import settings

    download_dir = str(settings.DOWNLOAD_DIR)
except Exception:
    download_dir = None

print(json.dumps(
    {'db': DB, 'download_dir': download_dir, 'rows': rows}, default=str))
