#!/usr/bin/env python3
"""dedupe_db_rows.py

Find DB rows that reference the same `file_path` and non-destructively mark
duplicate rows as `REMOVED` (keeps one canonical row per path).

Run from repo root with venv active:
  python scripts/dedupe_db_rows.py

The script will list proposed changes and ask for confirmation before applying.
"""
import os
import sqlite3
import datetime
import sys

DB = os.path.join('backend', 'universal_media_downloader.db')
if not os.path.exists(DB):
    print('Database not found:', DB)
    sys.exit(1)


def find_duplicates(cur):
    # Select file_path values with more than one row
    cur.execute("SELECT file_path, COUNT(*) as cnt FROM downloads WHERE file_path IS NOT NULL AND file_path<>'' GROUP BY file_path HAVING cnt>1")
    return [r[0] for r in cur.fetchall()]


def get_rows_for_path(cur, path):
    cur.execute(
        'SELECT id, status, created_at FROM downloads WHERE file_path=? ORDER BY created_at ASC, id ASC', (path,))
    return cur.fetchall()


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    duplicates = find_duplicates(cur)
    if not duplicates:
        print('No DB rows sharing the same file_path were found.')
        conn.close()
        return

    proposed = []
    for path in duplicates:
        rows = get_rows_for_path(cur, path)
        # keep the first row (earliest created_at / id), mark others
        canonical = rows[0][0]
        dup_ids = [r[0] for r in rows[1:]]
        if dup_ids:
            proposed.append((path, canonical, dup_ids))

    if not proposed:
        print('No duplicate groups to process.')
        conn.close()
        return

    print('Found duplicate groups:')
    for path, can, dup_ids in proposed:
        print(f'Path: {path}\n  Keep id: {can}\n  Mark REMOVED: {dup_ids}\n')

    resp = input('Apply these changes? [y/N]: ').strip().lower()
    if resp != 'y':
        print('Aborted by user. No changes applied.')
        conn.close()
        return

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    applied = 0
    for path, can, dup_ids in proposed:
        for did in dup_ids:
            try:
                cur.execute(
                    'UPDATE downloads SET status=?, updated_at=? WHERE id=?', ('REMOVED', now, did))
                applied += 1
            except Exception as e:
                print('Failed to update id', did, e)
    conn.commit()
    conn.close()
    print('Done. Marked', applied, 'rows as REMOVED.')


if __name__ == '__main__':
    main()
