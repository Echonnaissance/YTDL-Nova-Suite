#!/usr/bin/env python3
"""auto_fix_fuzzy.py

Attempt fuzzy matching for DB rows where exact filename lookup failed.
It builds a short search token from the DB `file_name` (strip extension, ellipses,
and non-alphanumerics) and searches `Downloads` for filenames containing that token.
If a unique match is found, it updates the DB row.
"""
import os
import re
import sqlite3
import datetime
import sys

DB = os.path.join('backend', 'universal_media_downloader.db')
if not os.path.exists(DB):
    print('Database not found:', DB)
    sys.exit(1)


def normalize_token(name):
    # remove extension
    name = os.path.splitext(name)[0]
    # remove trailing ellipsis or repeated dots
    name = re.sub(r'\.{2,}$', '', name)
    # keep alphanumeric and a few unicode ranges; replace others with space
    name = re.sub(r"[^\w\u0080-\uFFFF]+", ' ', name)
    token = name.strip()[:30]
    return token


def find_candidates(download_dir, token):
    if not token:
        return []
    token_low = token.lower()
    matches = []
    for root, dirs, files in os.walk(download_dir):
        for f in files:
            if token_low in f.lower():
                matches.append(os.path.abspath(os.path.join(root, f)))
    return matches


def main():
    # determine download_dir
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
        from app.config import settings
        download_dir = str(settings.DOWNLOAD_DIR)
    except Exception:
        download_dir = os.path.abspath(os.path.join(os.getcwd(), 'Downloads'))

    print('Using download_dir =', download_dir)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('SELECT id, file_name, file_path FROM downloads ORDER BY id')
    rows = cur.fetchall()
    updated = 0
    for id_, file_name, file_path in rows:
        needs_fix = False
        if not file_path:
            needs_fix = True
        else:
            p = os.path.abspath(file_path)
            if not os.path.exists(p):
                needs_fix = True
        if not needs_fix:
            continue
        if not file_name:
            continue
        token = normalize_token(file_name)
        if not token:
            continue
        candidates = find_candidates(download_dir, token)
        if len(candidates) == 1:
            found = candidates[0]
            size = os.path.getsize(found)
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute(
                'UPDATE downloads SET file_path=?, file_size=?, status=?, completed_at=?, updated_at=? WHERE id=?',
                (found, size, 'COMPLETED', now, now, id_),
            )
            conn.commit()
            updated += 1
            print(f'Updated id={id_} -> {found}')
        elif len(candidates) > 1:
            print(
                f'id={id_} ambiguous matches ({len(candidates)}), token={token}')
        else:
            print(f'id={id_} no matches for token={token}')

    print('Done. Updated', updated, 'rows')
    conn.close()


if __name__ == '__main__':
    main()
