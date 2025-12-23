#!/usr/bin/env python3
"""Check thumbnail filename mismatches between DB and Filesystem."""
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DB = REPO / 'backend' / 'universal_media_downloader.db'
THUMBS = REPO / 'Downloads' / 'Thumbnails'


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT id,file_path,thumbnail_url FROM downloads WHERE file_path IS NOT NULL ORDER BY id").fetchall()
    conn.close()

    video_rows = []
    for rid, fpath, thumb in rows:
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
        video_rows.append((rid, str(p), thumb))

    mismatches = []
    for idx, (rid, fpath, thumb) in enumerate(video_rows, start=1):
        expected = f'Thumbnail_{idx:02d}.jpg'
        actual = (thumb.split('/')[-1] if thumb else None)
        actual_exists = (THUMBS / actual).exists() if actual else False
        expected_exists = (THUMBS / expected).exists()
        if actual != expected or (not expected_exists and actual_exists):
            mismatches.append({
                'id': rid,
                'index': idx,
                'file': Path(fpath).name,
                'db_thumb': actual,
                'db_thumb_exists': actual_exists,
                'expected': expected,
                'expected_exists': expected_exists,
            })

    print('total_videos=', len(video_rows))
    print('mismatches=', len(mismatches))
    for m in mismatches:
        print(f"id={m['id']} idx={m['index']} file={m['file']} db_thumb={m['db_thumb']} db_exists={m['db_thumb_exists']} expected={m['expected']} expected_exists={m['expected_exists']}")


if __name__ == '__main__':
    main()
