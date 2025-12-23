#!/usr/bin/env python3
"""Normalize thumbnail filenames to Thumbnail_##.jpg and update DB entries.

Backups: creates backend/universal_media_downloader.db.normalize.bak
"""
import shutil
import sqlite3
from pathlib import Path
import re
import sys


REPO = Path(__file__).resolve().parents[1]
DB = REPO / 'backend' / 'universal_media_downloader.db'
THUMBS = REPO / 'Downloads' / 'Thumbnails'


def main():
    if not DB.exists():
        print('DB not found:', DB)
        return 1
    if not THUMBS.exists():
        print('Thumbnails dir not found:', THUMBS)
        return 1

    # backup DB
    bak = DB.with_suffix('.normalize.bak')
    shutil.copy(DB, bak)
    print('DB backup:', bak)

    thumb_re = re.compile(r'^Thumbnail_(\d+)\.jpg$', re.IGNORECASE)

    # Collect used indices from already-correct files
    used = set()
    for p in THUMBS.iterdir():
        if not p.is_file():
            continue
        m = thumb_re.match(p.name)
        if m:
            try:
                used.add(int(m.group(1)))
            except Exception:
                pass

    def next_index():
        i = 1
        while i in used:
            i += 1
        used.add(i)
        return i

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    moved = []
    for p in sorted(THUMBS.iterdir()):
        if not p.is_file():
            continue
        if thumb_re.match(p.name):
            continue
        i = next_index()
        new_name = f"Thumbnail_{i:02d}.jpg"
        dest = THUMBS / new_name
        # ensure destination doesn't already exist (shouldn't because of next_index)
        if dest.exists():
            print('Unexpected collision, skipping', p.name)
            continue
        try:
            shutil.move(str(p), str(dest))
            print(f"Renamed thumbnail: {p.name} -> {new_name}")
            # update DB rows that reference the old name
            cur.execute("UPDATE downloads SET thumbnail_url=? WHERE thumbnail_url LIKE ?", (
                f"/media/Thumbnails/{new_name}", f"%/{p.name}"))
            moved.append((p.name, new_name))
        except Exception as e:
            print('Failed to rename', p.name, e)

    conn.commit()
    conn.close()

    print('Done. Renamed', len(moved), 'files.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
