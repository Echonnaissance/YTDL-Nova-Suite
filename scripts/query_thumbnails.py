#!/usr/bin/env python3
"""Query downloads DB for specific IDs and report thumbnail paths and file sizes."""
import sqlite3
import json
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / \
    'backend' / 'universal_media_downloader.db'
DOWNLOADS = Path(__file__).resolve().parents[1] / 'Downloads' / 'Thumbnails'

ids = [17, 21, 22, 23, 24, 42]


def main():
    if not DB.exists():
        print(json.dumps({"error": f"DB not found: {DB}"}))
        return

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    out = []
    for i in ids:
        cur.execute(
            "SELECT id, thumbnail_url, file_path FROM downloads WHERE id=?", (i,))
        row = cur.fetchone()
        rec = {"id": i, "db_row": row}
        if row:
            thumb_url = row[1]
            rec["thumbnail_url"] = thumb_url
            if thumb_url and thumb_url.startswith('/media/Thumbnails/'):
                fname = thumb_url.split('/media/Thumbnails/', 1)[1]
                fpath = DOWNLOADS / fname
                rec["thumb_path"] = str(fpath)
                if fpath.exists():
                    rec["thumb_exists"] = True
                    rec["thumb_size"] = fpath.stat().st_size
                else:
                    rec["thumb_exists"] = False
            else:
                rec["thumb_path"] = None
        out.append(rec)

    conn.close()
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
