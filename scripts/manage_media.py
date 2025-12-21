#!/usr/bin/env python3
"""
manage_media.py - combined utilities for managing local media and DB

Subcommands:
  scan-fix-paths   - match files under Downloads/Video to DB and insert missing rows
  fix-enums        - normalize enum values in DB
  populate-meta    - extract thumbnails and metadata and update DB
  fill-durations   - probe files and fill missing duration values
  db-recent        - print recent DB rows
  check-id-range   - test HEAD with Range for a given download id

Usage: python manage_media.py <subcommand> [options]
"""
import argparse
import subprocess
from pathlib import Path
import sqlite3
import difflib
import urllib.request
import urllib.parse
import urllib.error
import json
import re

REPO = Path(__file__).resolve().parents[1]
DB = REPO / 'backend' / 'universal_media_downloader.db'
DOWNLOADS_VIDEO = REPO / 'Downloads' / 'Video'
THUMBS_DIR = REPO / 'Downloads' / 'Thumbnails'


def scan_and_fix_paths():
    files = {}
    for p in DOWNLOADS_VIDEO.rglob('*'):
        if p.is_file():
            files[p.name.lower()] = str(p.resolve())

    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, file_name, file_path FROM downloads WHERE status='COMPLETED'")
    rows = cur.fetchall()

    assigned = set()
    updated = 0
    for r in rows:
        did = r['id']
        title = r['title'] or ''
        fname = r['file_name'] or ''
        fpath = r['file_path'] or ''
        if fpath and Path(fpath).exists():
            continue
        chosen = None
        if fname:
            key = fname.lower()
            if key in files and key not in assigned:
                chosen = files[key]
                assigned.add(key)
        if not chosen and fname:
            base = Path(fname).stem.lower()
            for k, v in files.items():
                if Path(k).stem.lower() == base and k not in assigned:
                    chosen = v
                    assigned.add(k)
                    break
        if not chosen and title:
            s = ''.join(c.lower() if c.isalnum()
                        else ' ' for c in title).strip()
            best = None
            best_ratio = 0.0
            for k, v in files.items():
                fname_slug = ''.join(
                    c.lower() if c.isalnum() else ' ' for c in k).strip()
                ratio = difflib.SequenceMatcher(a=s, b=fname_slug).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best = v
            if best:
                best_key = Path(best).name.lower()
                if best_key not in assigned:
                    chosen = best
                    assigned.add(best_key)
        if chosen:
            cur.execute(
                "UPDATE downloads SET file_path=? WHERE id=?", (chosen, did))
            updated += 1

    # insert unreferenced files as completed downloads
    cur.execute("SELECT file_path FROM downloads WHERE file_path IS NOT NULL")
    existing = {str(Path(r[0]).resolve()).lower() for r in cur.fetchall()}
    to_insert = [p for p in files.values() if str(
        Path(p).resolve()).lower() not in existing]
    inserted = 0
    for p in to_insert:
        size = None
        try:
            size = Path(p).stat().st_size
        except Exception:
            size = None
        url = f"file://{p}"
        title = Path(p).stem
        fmt = Path(p).suffix.lstrip('.') or 'mp4'
        sql = (
            "INSERT INTO downloads (url, title, download_type, format, quality, "
            "status, progress, file_path, file_size, file_name) VALUES (?,?,?,?,?,?,?,?,?,?)"
        )
        cur.execute(
            sql,
            (
                url,
                title,
                'VIDEO',
                fmt,
                'best',
                'COMPLETED',
                100.0,
                p,
                size,
                Path(p).name,
            ),
        )
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Updated {updated} rows, inserted {inserted} new rows")


def fix_enum_values():
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        "UPDATE downloads SET download_type='VIDEO' WHERE download_type='video'")
    cur.execute(
        "UPDATE downloads SET download_type='AUDIO' WHERE download_type='audio'")
    cur.execute(
        "UPDATE downloads SET download_type='PLAYLIST' WHERE download_type='playlist'")
    cur.execute("UPDATE downloads SET status='PENDING' WHERE status='pending'")
    cur.execute("UPDATE downloads SET status='QUEUED' WHERE status='queued'")
    cur.execute(
        "UPDATE downloads SET status='DOWNLOADING' WHERE status='downloading'")
    cur.execute(
        "UPDATE downloads SET status='PROCESSING' WHERE status='processing'")
    cur.execute(
        "UPDATE downloads SET status='COMPLETED' WHERE status='completed'")
    cur.execute("UPDATE downloads SET status='FAILED' WHERE status='failed'")
    cur.execute(
        "UPDATE downloads SET status='CANCELLED' WHERE status='cancelled'")
    conn.commit()
    conn.close()
    print('Normalized enum values')


def populate_metadata():
    ffmpeg = find_ffmpeg()
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        "SELECT id, file_path, thumbnail_url FROM downloads WHERE file_path IS NOT NULL")
    rows = cur.fetchall()
    created = 0
    upd = 0
    for rid, fpath, thumb in rows:
        if not fpath:
            continue
        p = Path(fpath)
        if not p.exists():
            continue
        file_size = p.stat().st_size
        file_name = p.name
        duration = get_duration_local(ffmpeg, str(p))
        thumb_name = f"{rid}_{p.stem}.jpg"
        thumb_path = THUMBS_DIR / thumb_name
        thumb_url = f"/media/Thumbnails/{thumb_name}"
        thumb_created = False
        if not thumb_path.exists():
            thumb_created = make_thumbnail_local(
                ffmpeg, str(p), str(thumb_path))
            if thumb_created:
                created += 1
        cur.execute("UPDATE downloads SET file_size=?, file_name=? WHERE id=?",
                    (file_size, file_name, rid))
        if duration is not None:
            cur.execute(
                "UPDATE downloads SET duration=? WHERE id=?", (duration, rid))
        if thumb_created or (thumb and str(thumb).startswith('/media/Thumbnails')):
            cur.execute(
                "UPDATE downloads SET thumbnail_url=? WHERE id=?", (thumb_url, rid))
        upd += 1
    conn.commit()
    conn.close()
    print(
        f'Processed {len(rows)} rows, updated {upd}, thumbnails created {created}')


def find_ffmpeg():
    candidate = REPO / 'ffmpeg.exe'
    if candidate.exists():
        return str(candidate)
    return 'ffmpeg'


def get_duration_local(ffmpeg, path: str):
    try:
        p = subprocess.run([ffmpeg, '-i', path],
                           capture_output=True, text=True)
        stderr = p.stderr
        m = re.search(r'Duration: (\d\d):(\d\d):(\d\d)\.(\d+)', stderr)
        if m:
            h, mm, s, ms = m.groups()
            return int(h)*3600 + int(mm)*60 + int(s) + float('0.'+ms)
    except Exception:
        return None


def make_thumbnail_local(ffmpeg, src: str, dst: str):
    try:
        subprocess.run(
            [
                ffmpeg,
                '-ss',
                '00:00:01',
                '-i',
                src,
                '-frames:v',
                '1',
                '-q:v',
                '2',
                dst,
                '-y',
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def fill_durations():
    ffprobe = find_ffprobe()
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        "SELECT id, file_path FROM downloads WHERE file_path IS NOT NULL AND duration IS NULL")
    rows = cur.fetchall()
    updated = 0
    for rid, fpath in rows:
        if not fpath:
            continue
        p = Path(fpath)
        if not p.exists():
            continue
        dur = probe_duration_local(ffprobe, str(p))
        if dur is not None:
            cur.execute(
                'UPDATE downloads SET duration=? WHERE id=?', (dur, rid))
            updated += 1
    conn.commit()
    conn.close()
    print('Updated', updated, 'rows')


def find_ffprobe():
    candidate = REPO / 'ffprobe.exe'
    if candidate.exists():
        return str(candidate)
    return 'ffprobe'


def probe_duration_local(ffprobe, path: str):
    try:
        res = subprocess.run([ffprobe, '-v', 'error', '-show_entries', 'format=duration', '-of',
                             'default=noprint_wrappers=1:nokey=1', path], capture_output=True, text=True, check=True)
        out = res.stdout.strip()
        if out:
            return float(out)
    except Exception:
        return None


def db_recent():
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        'SELECT id, title, status, file_path, file_name FROM downloads ORDER BY id DESC LIMIT 20')
    for r in cur.fetchall():
        print(r)
    conn.close()


def check_id_range(id_):
    API = f'http://127.0.0.1:8000/api/downloads/{id_}'
    BASE = 'http://127.0.0.1:8000'
    with urllib.request.urlopen(API) as r:
        d = json.load(r)
    media = d.get('media_url')
    if not media:
        print('No media_url for id', id_)
        return
    if media.startswith('/'):
        enc = urllib.parse.quote(media, safe='/')
        url = BASE + enc
    else:
        enc = urllib.parse.quote(media.replace('\\', '/'), safe='/')
        if not enc.startswith('/media'):
            enc = '/media/' + enc.lstrip('/')
        url = BASE + enc
    req = urllib.request.Request(
        url, method='HEAD', headers={'Range': 'bytes=0-1'})
    try:
        with urllib.request.urlopen(req) as r:
            print('HEAD', r.status)
            for k, v in r.getheaders():
                print(k + ':', v)
    except urllib.error.HTTPError as e:
        print('HEAD error', e.code)


def main():
    parser = argparse.ArgumentParser(prog='manage_media')
    sub = parser.add_subparsers(dest='cmd')
    sub.add_parser('scan-fix-paths')
    sub.add_parser('fix-enums')
    sub.add_parser('populate-meta')
    sub.add_parser('fill-durations')
    sub.add_parser('db-recent')
    p = sub.add_parser('check-id-range')
    p.add_argument('id')
    args = parser.parse_args()
    if args.cmd == 'scan-fix-paths':
        scan_and_fix_paths()
    elif args.cmd == 'fix-enums':
        fix_enum_values()
    elif args.cmd == 'populate-meta':
        populate_metadata()
    elif args.cmd == 'fill-durations':
        fill_durations()
    elif args.cmd == 'db-recent':
        db_recent()
    elif args.cmd == 'check-id-range':
        check_id_range(args.id)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
