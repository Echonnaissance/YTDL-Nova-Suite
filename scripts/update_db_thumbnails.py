#!/usr/bin/env python3
"""Update DB thumbnail_url to /media/Thumbnails/Thumbnail_XX.jpg when that file exists.
Creates a backup at backend/universal_media_downloader.db.update-bak
"""
import shutil
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / 'backend' / 'universal_media_downloader.db'
BACKUP = DB.with_suffix('.update-bak')
THUMBS = REPO / 'Downloads' / 'Thumbnails'


def main():
    if not DB.exists():
        print('DB not found:', DB)
        return 1
    if not THUMBS.exists():
        print('Thumbnails dir not found:', THUMBS)
        return 1

    shutil.copy(DB, BACKUP)
    print('DB backup created:', BACKUP)

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    cur.execute(
        "SELECT id, file_path FROM downloads WHERE file_path IS NOT NULL ORDER BY id")
    rows = cur.fetchall()

    video_rows = []
    for rid, fpath in rows:
        if not fpath:
            continue
        p = Path(fpath)
        try:
            p = p.resolve()
        except Exception:
            continue
        try:
            p.relative_to((REPO / 'Downloads' / 'Video').resolve())
        except Exception:
            continue
        if not p.exists():
            continue
        video_rows.append((rid, p))

    # Ensure stable ordering by id
    video_rows.sort(key=lambda x: x[0])

    updated = []
    for idx, (rid, p) in enumerate(video_rows, start=1):
        expected_name = f"Thumbnail_{idx:02d}.jpg"
        expected_path = THUMBS / expected_name
        if expected_path.exists():
            expected_url = f"/media/Thumbnails/{expected_name}"
            # update DB
            cur.execute(
                "UPDATE downloads SET thumbnail_url=? WHERE id=?", (expected_url, rid))
            updated.append((rid, expected_url))

    conn.commit()
    conn.close()

    print(f'Updated {len(updated)} rows')
    for rid, url in updated[:50]:
        print(rid, url)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
