#!/usr/bin/env python3
"""
auto_register.py

Automate post-download tasks for a single file:
 - move file into Downloads/Video
 - run scan-and-fix to register file in DB
 - generate thumbnails and populate metadata
 - fill durations

Usage: python scripts/auto_register.py /path/to/file.mp4 [--no-move]
"""
import argparse
import shutil
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
DOWNLOADS_VIDEO = REPO / 'Downloads' / 'Video'


def unique_dest(dest: Path) -> Path:
    """Return a non-colliding destination path by appending a suffix if needed."""
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    i = 1
    while True:
        candidate = dest.with_name(f"{stem}-{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def run_manage(command: str) -> int:
    """Run the manage_media.py subcommand and stream output."""
    cmd = [sys.executable, str(REPO / 'scripts' / 'manage_media.py'), command]
    print(f"Running: {' '.join(cmd)}")
    res = subprocess.run(cmd)
    return res.returncode


def main():
    p = argparse.ArgumentParser()
    p.add_argument('file', type=Path)
    p.add_argument('--no-move', action='store_true',
                   help='Copy instead of move')
    p.add_argument('--skip-populate', action='store_true')
    p.add_argument('--skip-duration', action='store_true')
    args = p.parse_args()

    src = args.file
    if not src.exists():
        print('Source file not found:', src)
        sys.exit(2)

    DOWNLOADS_VIDEO.mkdir(parents=True, exist_ok=True)
    dest = DOWNLOADS_VIDEO / src.name
    dest = unique_dest(dest)

    try:
        if args.no_move:
            print(f'Copying {src} -> {dest}')
            shutil.copy2(src, dest)
        else:
            print(f'Moving {src} -> {dest}')
            shutil.move(str(src), str(dest))
    except (OSError, shutil.Error, PermissionError) as e:
        print('Failed to move/copy file:', e)
        sys.exit(3)

    # Run scan to register or update DB rows
    rc = run_manage('scan-fix-paths')
    if rc != 0:
        print('scan-fix-paths failed (rc=', rc, ')')

    if not args.skip_populate:
        rc = run_manage('populate-meta')
        if rc != 0:
            print('populate-meta failed (rc=', rc, ')')

    if not args.skip_duration:
        rc = run_manage('fill-durations')
        if rc != 0:
            print('fill-durations failed (rc=', rc, ')')

    print('Done. New file placed at:', dest)


if __name__ == '__main__':
    main()
