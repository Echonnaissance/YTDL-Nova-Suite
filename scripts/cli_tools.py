#!/usr/bin/env python3
"""Consolidated admin CLI for scripts/ helpers.

Usage examples:
  python scripts/cli_tools.py inspect
  python scripts/cli_tools.py scan-fix-paths
  python scripts/cli_tools.py populate-meta
  python scripts/cli_tools.py fill-durations
  python scripts/cli_tools.py register --path "C:/path/to/file.mp4"
  python scripts/cli_tools.py dedup --path "C:/path/to/file.mp4"
  python scripts/cli_tools.py find-thumb --prefix 52_
  python scripts/cli_tools.py delete-thumb --prefix 52_
  python scripts/cli_tools.py remove-ids 53 54
"""
from pathlib import Path
import argparse
import sqlite3
import subprocess
import sys
import os

REPO = Path(__file__).resolve().parents[1]
DB = REPO / 'backend' / 'universal_media_downloader.db'
THUMBS = REPO / 'Downloads' / 'Thumbnails'


def run_manage(subcmd):
    cmd = [sys.executable, str(REPO / 'scripts' / 'manage_media.py'), subcmd]
    return subprocess.run(cmd).returncode


def inspect_recent(limit=50):
    def esc(s):
        if s is None:
            return 'None'
        try:
            return s.encode('unicode_escape').decode('ascii')
        except Exception:
            return repr(s)

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        'SELECT id, title, duration, thumbnail_url, file_path, file_name FROM downloads ORDER BY id DESC LIMIT ?', (
            limit,)
    )
    rows = cur.fetchall()
    for r in rows:
        print(r[0], esc(r[1]), r[2], esc(r[3]), esc(r[4]), esc(r[5]))
    conn.close()


def register_file(path_str):
    p = Path(path_str)
    if not p.exists():
        print('File not found:', p)
        return 2
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    # try to find existing by resolved file_path
    cur.execute(
        'SELECT id, file_path FROM downloads WHERE file_path IS NOT NULL')
    for r in cur.fetchall():
        if r[1] and Path(r[1]).resolve() == p.resolve():
            print('Found existing DB row for file:', r[0])
            conn.close()
            # regenerate metadata/durations
            run_manage('populate-meta')
            run_manage('fill-durations')
            return 0

    # fallback: filename match
    cur.execute('SELECT id, file_name FROM downloads')
    for r in cur.fetchall():
        fn = r[1] or ''
        if fn == p.name:
            print('Found row by file_name for file:', r[0])
            conn.close()
            run_manage('populate-meta')
            run_manage('fill-durations')
            return 0

    # insert new completed row
    url = f'file://{str(p)}'
    title = p.stem
    fmt = p.suffix.lstrip('.') or 'mp4'
    try:
        size = p.stat().st_size
    except Exception:
        size = None
    sql = (
        "INSERT INTO downloads (url, title, download_type, format, quality, status, progress, file_path, file_size, file_name) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)"
    )
    cur.execute(sql, (url, title, 'video', fmt, 'best',
                'completed', 100.0, str(p), size, p.name))
    conn.commit()
    newid = cur.lastrowid
    conn.close()
    print('Inserted row id:', newid)
    run_manage('populate-meta')
    run_manage('fill-durations')
    return 0


def dedup(path_str):
    p = Path(path_str)
    if not p.exists():
        print('File not found:', p)
        return 2
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        'SELECT id, file_path, thumbnail_url FROM downloads WHERE file_path IS NOT NULL')
    rows = [(r[0], r[1], r[2]) for r in cur.fetchall() if r[1]]
    matches = [r for r in rows if Path(r[1]).resolve() == p.resolve()]
    if not matches:
        print('No DB rows found for target file')
        conn.close()
        return 0
    print('Found rows for target:', matches)
    keep = max(m[0] for m in matches)
    remove = [m[0] for m in matches if m[0] != keep]
    print('Keeping id', keep, 'removing', remove)
    for rid in remove:
        for fp in THUMBS.glob(f"{rid}_*"):
            try:
                fp.unlink()
                print('Deleted thumbnail', fp)
            except Exception:
                pass
        cur.execute('DELETE FROM downloads WHERE id=?', (rid,))
        print('Deleted DB row', rid)
    conn.commit()
    conn.close()
    print('Regenerating metadata for kept row')
    run_manage('populate-meta')
    return 0


def find_thumb(prefix):
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        'SELECT id, thumbnail_url FROM downloads WHERE thumbnail_url LIKE ?', (f'%{prefix}%',))
    rows = cur.fetchall()
    for r in rows:
        print(r[0], r[1])
    conn.close()


def delete_thumb(prefix):
    # delete files starting with prefix in THUMBS
    removed = 0
    for p in THUMBS.glob(f"{prefix}*"):
        try:
            p.unlink()
            print('Deleted', p)
            removed += 1
        except Exception as e:
            print('Failed to delete', p, e)
    print('Deleted files:', removed)


def remove_ids(ids):
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    for i in ids:
        try:
            cur.execute('DELETE FROM downloads WHERE id=?', (i,))
            print('Deleted id', i)
        except Exception as e:
            print('Failed to delete id', i, e)
    conn.commit()
    conn.close()


def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd')

    sub.add_parser('inspect')
    sub.add_parser('scan-fix-paths')
    sub.add_parser('populate-meta')
    sub.add_parser('fill-durations')

    reg = sub.add_parser('register')
    reg.add_argument('--path', required=True)

    ded = sub.add_parser('dedup')
    ded.add_argument('--path', required=True)

    fnd = sub.add_parser('find-thumb')
    fnd.add_argument('--prefix', required=True)

    dlt = sub.add_parser('delete-thumb')
    dlt.add_argument('--prefix', required=True)

    rem = sub.add_parser('remove-ids')
    rem.add_argument('ids', nargs='+', type=int)

    args = p.parse_args(argv)
    if args.cmd == 'inspect':
        inspect_recent()
    elif args.cmd == 'scan-fix-paths':
        return run_manage('scan-fix-paths')
    elif args.cmd == 'populate-meta':
        return run_manage('populate-meta')
    elif args.cmd == 'fill-durations':
        return run_manage('fill-durations')
    elif args.cmd == 'register':
        return register_file(args.path)
    elif args.cmd == 'dedup':
        return dedup(args.path)
    elif args.cmd == 'find-thumb':
        return find_thumb(args.prefix)
    elif args.cmd == 'delete-thumb':
        return delete_thumb(args.prefix)
    elif args.cmd == 'remove-ids':
        return remove_ids(args.ids)
    else:
        p.print_help()


if __name__ == '__main__':
    sys.exit(main())
