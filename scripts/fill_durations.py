#!/usr/bin/env python3
"""
Fill missing `duration` values in the downloads DB by probing local media files.

Requires `ffprobe` (bundled `ffmpeg.exe` provides `ffprobe.exe`) available at repo root or on PATH.
"""
import sqlite3
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]
DB = REPO / 'backend' / 'universal_media_downloader.db'


def find_ffprobe():
    candidate = REPO / 'ffprobe.exe'
    if candidate.exists():
        return str(candidate)
    # sometimes ffmpeg.exe is present and ffprobe next to it
    candidate2 = REPO / 'ffmpeg.exe'
    if candidate2.exists():
        alt = candidate2.with_name('ffprobe.exe')
        if alt.exists():
            return str(alt)
    return 'ffprobe'


def probe_duration(ffprobe, path: str):
    try:
        res = subprocess.run([ffprobe, '-v', 'error', '-show_entries', 'format=duration', '-of',
                             'default=noprint_wrappers=1:nokey=1', path], capture_output=True, text=True, check=True)
        out = res.stdout.strip()
        if out:
            return float(out)
    except Exception:
        return None


def main():
    if not DB.exists():
        print('DB not found:', DB)
        sys.exit(1)

    ffprobe = find_ffprobe()
    print('Using ffprobe:', ffprobe)

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        "SELECT id, file_path FROM downloads WHERE file_path IS NOT NULL AND duration IS NULL")
    rows = cur.fetchall()
    print('Rows to update:', len(rows))

    updated = 0
    for rid, fpath in rows:
        if not fpath:
            continue
        p = Path(fpath)
        if not p.exists():
            continue
        dur = probe_duration(ffprobe, str(p))
        if dur is not None:
            cur.execute(
                'UPDATE downloads SET duration=? WHERE id=?', (dur, rid))
            updated += 1
            print(f'Updated id={rid} duration={dur:.2f}')
        else:
            print(f'Could not probe id={rid} file={p.name}')

    conn.commit()
    conn.close()
    print('Updated', updated, 'rows')


if __name__ == "__main__":
    main()
