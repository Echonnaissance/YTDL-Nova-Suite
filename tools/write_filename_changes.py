#!/usr/bin/env python3
import sqlite3
import json
from pathlib import Path

DB = Path('backend/universal_media_downloader.db')
BAK = Path('backend/universal_media_downloader.db.bak')
OUT = Path('tools') / 'filename_changes.json'


def rows_map(conn):
    c = conn.cursor()
    c.execute('SELECT id, file_path, file_name FROM downloads')
    return {r[0]: {'file_path': r[1], 'file_name': r[2]} for r in c.fetchall()}


def main():
    if not DB.exists():
        print('DB not found:', DB)
        return
    if not BAK.exists():
        print('Backup DB not found:', BAK)
        return
    conn = sqlite3.connect(str(DB))
    conn2 = sqlite3.connect(str(BAK))
    cur = rows_map(conn)
    old = rows_map(conn2)
    changes = []
    all_ids = sorted(set(list(cur.keys()) + list(old.keys())))
    for id_ in all_ids:
        a = old.get(id_)
        b = cur.get(id_)
        if a != b:
            changes.append({'id': id_, 'old': a, 'new': b})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(changes, indent=2))
    print('Wrote', len(changes), 'entries to', OUT)
    conn.close()
    conn2.close()


if __name__ == '__main__':
    main()
