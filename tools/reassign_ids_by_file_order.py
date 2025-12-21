#!/usr/bin/env python3
"""
Renumber `downloads.id` to match the sorted order of files in `Downloads/Video`.

Behavior:
- Backup the DB to `backend/universal_media_downloader.db.bak`.
- Read video files sorted by name (lexical). For each file at position i (1-based), set
  the corresponding DB row's id to i and update `title`, `file_name`, `file_path`,
  and `thumbnail_url` to match the `Video_{:02d}.mp4` / `Thumbnail_{:02d}.jpg` scheme.
- Implementation uses a temporary high offset to avoid id collisions.

Run from repo root: `python tools/reassign_ids_by_file_order.py`
"""

import sqlite3
import shutil
from pathlib import Path
import json
import os
import sys

DB = Path('backend/universal_media_downloader.db')
BACKUP = DB.with_suffix('.db.bak')
VIDEOS_DIR = Path('Downloads') / 'Video'
THUMBS_DIR = Path('Downloads') / 'Thumbnails'


def load_rows(conn):
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT id, file_name, file_path, title, thumbnail_url FROM downloads')
    return {r['id']: dict(r) for r in c.fetchall()}


def find_row_for_file(rows, fname):
    # match by file_name or basename of file_path
    for id_, r in rows.items():
        if r.get('file_name') and os.path.basename(r['file_name']) == fname:
            return id_
        if r.get('file_path') and os.path.basename(r['file_path']) == fname:
            return id_
    # try match by numeric indicator in title or file_name
    if fname.lower().startswith('video_'):
        try:
            num = int(fname.split('_')[1].split('.')[0])
        except Exception:
            num = None
        if num is not None:
            for id_, r in rows.items():
                if r.get('file_name') and f"{num:02d}" in r['file_name']:
                    return id_
                if r.get('title') and f"{num}" in str(r['title']):
                    return id_
    return None


def main():
    if not DB.exists():
        print('DB not found:', DB)
        sys.exit(1)
    # list video files
    if not VIDEOS_DIR.exists():
        print('Videos dir not found:', VIDEOS_DIR)
        sys.exit(1)
    videos = sorted([p.name for p in VIDEOS_DIR.glob('*.mp4')])
    if not videos:
        print('No video files found under', VIDEOS_DIR)
        sys.exit(1)

    print('Backing up DB to', BACKUP)
    shutil.copy(DB, BACKUP)

    conn = sqlite3.connect(str(DB))
    rows = load_rows(conn)

    # Build mapping: current_id -> target_id
    mapping = {}  # current_id -> desired_id
    for idx, fname in enumerate(videos, start=1):
        cur = find_row_for_file(rows, fname)
        if cur is None:
            print(f'Warning: no DB row found for {fname}; skipping')
            continue
        mapping[cur] = idx

    if not mapping:
        print('No rows mapped; aborting')
        conn.close()
        sys.exit(1)

    print('Planned renumbering for', len(mapping), 'rows')

    # Compute temp offset
    max_id = max(rows.keys()) if rows else 0
    offset = max_id + 1000

    c = conn.cursor()
    try:
        c.execute('PRAGMA foreign_keys = OFF')
        c.execute('BEGIN')
        # Move all affected rows to temp ids
        for cur in mapping.keys():
            temp = cur + offset
            c.execute('UPDATE downloads SET id = ? WHERE id = ?', (temp, cur))
        # Now assign desired ids and update fields
        for cur, desired in mapping.items():
            temp = cur + offset
            video_name = f'Video_{desired:02d}.mp4'
            thumb_name = f'Thumbnail_{desired:02d}.jpg'
            abs_path = str((Path.cwd() / 'Downloads' /
                           'Video' / video_name).as_posix())
            # Use forward slashes for SQLite consistency on Windows as earlier rows used both
            thumb_url = f'/media/Thumbnails/{thumb_name}'
            title = f'Video_{desired:02d}'
            c.execute('UPDATE downloads SET id = ?, title = ?, file_name = ?, file_path = ?, thumbnail_url = ? WHERE id = ?',
                      (desired, title, video_name, abs_path, thumb_url, temp))
        c.execute('COMMIT')
        c.execute('PRAGMA foreign_keys = ON')
    except Exception as e:
        conn.rollback()
        print('Error during DB update:', e)
        conn.close()
        sys.exit(1)

    # Verify
    print('Verifying rows 1..{0}'.format(len(videos)))
    sel = c.execute(
        f"SELECT id,title,file_name,thumbnail_url FROM downloads WHERE id BETWEEN 1 AND {len(videos)} ORDER BY id").fetchall()
    for r in sel:
        print('|'.join(str(x) for x in r))

    conn.close()
    print('\nDone. Backup is at', BACKUP)


if __name__ == '__main__':
    main()
