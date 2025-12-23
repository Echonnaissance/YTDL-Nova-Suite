import sqlite3
import sys
from pathlib import Path
p = Path(__file__).resolve().parents[1] / \
    'backend' / 'universal_media_downloader.db'
if not p.exists():
    print('DB not found:', p)
    sys.exit(1)
con = sqlite3.connect(str(p))
cur = con.cursor()
try:
    cur.execute(
        "SELECT id, title, file_name, file_path, file_size FROM downloads ORDER BY id LIMIT 500")
    rows = cur.fetchall()
    for r in rows:
        print('|'.join([str(x) if x is not None else '' for x in r]))
except Exception as e:
    print('ERR', e)
finally:
    con.close()
