#!/usr/bin/env python3
"""
Extract thumbnails and metadata from local media files and update the downloads DB.

Requirements: `ffmpeg.exe` present in repo root or available on PATH.

Saves thumbnails to `Downloads/Thumbnails` and sets `thumbnail_url` to
`/media/Thumbnails/<name>.jpg`. Also fills `duration`, `file_size`, `file_name`.
"""
import subprocess
import sqlite3
from pathlib import Path
import re
import os
import sys

REPO = Path(__file__).resolve().parents[1]
DB = REPO / 'backend' / 'universal_media_downloader.db'
DOWNLOADS = REPO / 'Downloads' / 'Video'
THUMBS_DIR = REPO / 'Downloads' / 'Thumbnails'


def find_ffmpeg():
    # prefer bundled ffmpeg.exe at repo root
    candidate = REPO / 'ffmpeg.exe'
    if candidate.exists():
        return str(candidate)
    # fall back to ffmpeg on PATH
    return 'ffmpeg'


def get_duration(ffmpeg, path: str):
    # run ffmpeg -i and parse stderr for Duration
    try:
        p = subprocess.run([ffmpeg, '-i', path],
                           capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        stderr = p.stderr
        m = re.search(r'Duration: (\d\d):(\d\d):(\d\d)\.(\d+)', stderr)
        if m:
            h, m2, s, ms = m.groups()
            secs = int(h) * 3600 + int(m2) * 60 + int(s) + float('0.' + ms)
            return secs
    except Exception:
        pass
    return None


def make_thumbnail(ffmpeg, src: str, dst: str):
    # First, try to extract an attached cover art / image stream (common in audio files)
    try:
        p = subprocess.run([
            ffmpeg, '-i', src, '-map', '0:v:0', '-frames:v', '1', '-q:v', '2', dst, '-y'
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if p.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 0:
            return True
    except Exception:
        pass

    # Fallback: seek to 1 second to avoid black frames (video files)
    try:
        subprocess.run([ffmpeg, '-ss', '00:00:01', '-i', src, '-frames:v', '1', '-q:v', '2', dst, '-y'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        # Capture stderr to surface ffmpeg error (utf-8, replace undecodable bytes)
        try:
            p = subprocess.run([ffmpeg, '-ss', '00:00:01', '-i', src, '-frames:v', '1', '-q:v', '2', dst, '-y'],
                               capture_output=True, text=True, encoding='utf-8', errors='replace')
            stderr = p.stderr or ''
            print(f"FFmpeg thumbnail error for '{src}':\n{stderr}")
        except Exception as e:
            print(f"Failed to run ffmpeg for thumbnail on '{src}': {e}")
        return False


def main():
    if not DB.exists():
        print('DB not found:', DB)
        sys.exit(1)

    if not DOWNLOADS.exists():
        print('Downloads folder not found:', DOWNLOADS)
        sys.exit(1)

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)

    ffmpeg = find_ffmpeg()

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    # select rows with file_path present and missing thumbnail or metadata
    cur.execute(
        "SELECT id, file_path, thumbnail_url FROM downloads WHERE file_path IS NOT NULL")
    rows = cur.fetchall()

    updated = 0
    created_thumbs = 0

    for rid, fpath, thumb in rows:
        if not fpath:
            continue
        p = Path(fpath)
        if not p.exists():
            continue

        # gather metadata
        file_size = p.stat().st_size
        file_name = p.name
        duration = get_duration(ffmpeg, str(p))

        # create thumbnail file name safe
        thumb_name = f"{rid}_{p.stem}.jpg"
        thumb_path = THUMBS_DIR / thumb_name
        thumb_url = f"/media/Thumbnails/{thumb_name}"

        thumb_created = False
        if not thumb_path.exists():
            thumb_created = make_thumbnail(ffmpeg, str(p), str(thumb_path))
            if thumb_created:
                created_thumbs += 1

        # update DB fields (only set if value present)
        cur.execute("UPDATE downloads SET file_size=?, file_name=? WHERE id=?",
                    (file_size, file_name, rid))
        if duration is not None:
            cur.execute(
                "UPDATE downloads SET duration=? WHERE id=?", (duration, rid))
        if thumb_created or (thumb and thumb.startswith('/media/Thumbnails')):
            cur.execute(
                "UPDATE downloads SET thumbnail_url=? WHERE id=?", (thumb_url, rid))

        updated += 1

    conn.commit()
    conn.close()

    print(
        f'Processed {len(rows)} rows, updated {updated}, thumbnails created {created_thumbs}')


if __name__ == '__main__':
    main()
