#!/usr/bin/env python3
"""Print recent downloads with key fields for debugging thumbnails/durations.
Prints Unicode fields escaped to avoid console encoding errors on Windows.
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / \
    'backend' / 'universal_media_downloader.db'


def esc(s):
    if s is None:
        return 'None'
    try:
        return s.encode('unicode_escape').decode('ascii')
    except Exception:
        return repr(s)


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        'SELECT id, title, duration, thumbnail_url, file_path, file_name FROM downloads ORDER BY id DESC LIMIT 50')
    rows = cur.fetchall()
    for r in rows:
        print(r[0], esc(r[1]), r[2], esc(r[3]), esc(r[4]), esc(r[5]))
    conn.close()


if __name__ == '__main__':
    main()
