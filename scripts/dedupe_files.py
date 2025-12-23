#!/usr/bin/env python3
"""dedupe_files.py

Safe dedupe for Downloads/Video:
- Finds files with identical SHA256 content
- Keeps one canonical file, moves duplicates to Downloads/duplicates_archive/<ts>/
- Updates any DB rows referencing moved files to point to the canonical path

Run from repo root with venv active:
  python scripts/dedupe_files.py
"""
import os
import hashlib
import shutil
import sqlite3
import datetime
import sys


def sha256_of_file(path, block_size=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(block_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def find_video_files(root):
    exts = {'.mp4', '.mkv', '.webm', '.mov', '.m4v',
            '.avi', '.flv', '.mp3', '.m4a', '.aac'}
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in exts:
                files.append(os.path.join(dirpath, fn))
    return files


def main():
    repo = os.getcwd()
    downloads_dir = os.path.join(repo, 'Downloads', 'Video')
    if not os.path.exists(downloads_dir):
        print('Downloads/Video not found:', downloads_dir)
        sys.exit(1)

    print('Scanning files under', downloads_dir)
    files = find_video_files(downloads_dir)
    if not files:
        print('No media files found')
        return

    print(f'Found {len(files)} files; hashing (this may take a while)')
    hash_map = {}
    for p in files:
        try:
            h = sha256_of_file(p)
        except Exception as e:
            print('Failed to hash', p, e)
            continue
        hash_map.setdefault(h, []).append(p)

    duplicates = {h: ps for h, ps in hash_map.items() if len(ps) > 1}
    if not duplicates:
        print('No duplicate-content files found')
        return

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_dir = os.path.join(repo, 'Downloads', 'duplicates_archive_' + ts)
    os.makedirs(archive_dir, exist_ok=True)

    DB = os.path.join(repo, 'backend', 'universal_media_downloader.db')
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    total_moved = 0
    for h, paths in duplicates.items():
        # pick canonical: the one with earliest mtime
        paths_sorted = sorted(paths, key=lambda p: os.path.getmtime(p))
        canonical = paths_sorted[0]
        dupes = paths_sorted[1:]
        print(f'Hash {h}: canonical={canonical}, duplicates={len(dupes)}')
        for d in dupes:
            dest = os.path.join(archive_dir, os.path.basename(d))
            # ensure dest doesn't collide
            i = 1
            base, ext = os.path.splitext(dest)
            while os.path.exists(dest):
                dest = f"{base}-{i}{ext}"
                i += 1
            try:
                shutil.move(d, dest)
                print('Moved duplicate', d, '->', dest)
                total_moved += 1
            except Exception as e:
                print('Failed to move', d, e)
                continue

            # update DB rows that referenced the moved path -> point to canonical
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            try:
                cur.execute('SELECT id FROM downloads WHERE file_path=?', (d,))
                rows = cur.fetchall()
                if rows:
                    size = os.path.getsize(canonical)
                    for (rid,) in rows:
                        cur.execute('UPDATE downloads SET file_path=?, file_name=?, file_size=?, updated_at=? WHERE id=?',
                                    (canonical, os.path.basename(canonical), size, now, rid))
                    conn.commit()
                    print('Updated DB rows for moved file to canonical path')
            except Exception as e:
                print('DB update failed for moved file', d, e)

    conn.close()
    print('Done. moved', total_moved, 'files to', archive_dir)


if __name__ == '__main__':
    main()
