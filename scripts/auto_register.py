#!/usr/bin/env python3
"""auto_register.py - interactive helper to move/copy a file into Downloads/Video

This script is interactive and requires no flags. It moves (default) or copies
the provided file into Downloads/Video, then runs project maintenance commands
to register and populate metadata.
"""
import subprocess
from pathlib import Path
import shutil
import sys
import os


REPO = Path(__file__).resolve().parents[1]
DOWNLOADS_VIDEO = REPO / 'Downloads' / 'Video'


def unique_dest(dest: Path) -> Path:
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
    cmd = [sys.executable, str(REPO / 'scripts' / 'manage_media.py'), command]
    print(f"Running: {' '.join(cmd)}")
    res = subprocess.run(cmd)
    return res.returncode


def main():
    print('Interactive auto-register: move a local file into Downloads/Video and run meta commands.')
    src = input('Enter path to source file (or drag it here): ').strip()
    if not src:
        print('No source file provided. Exiting.')
        sys.exit(1)
    src = Path(src).expanduser()
    if not src.exists():
        print('Source file not found:', src)
        sys.exit(2)

    use_copy = input('Copy instead of move? [y/N]: ').strip().lower() == 'y'

    DOWNLOADS_VIDEO.mkdir(parents=True, exist_ok=True)
    dest = DOWNLOADS_VIDEO / src.name
    dest = unique_dest(dest)

    try:
        if use_copy:
            print(f'Copying {src} -> {dest}')
            shutil.copy2(src, dest)
        else:
            print(f'Moving {src} -> {dest}')
            shutil.move(str(src), str(dest))
    except (OSError, shutil.Error, PermissionError) as e:
        print('Failed to move/copy file:', e)
        sys.exit(3)

    # Run maintenance commands automatically
    steps = [
        ('scan-fix-paths', True),
        ('populate-meta', True),
        ('fill-durations', True),
    ]
    for cmd, required in steps:
        rc = run_manage(cmd)
        if rc != 0:
            print(f'{cmd} failed (rc={rc})')

    print('Done. New file placed at:', dest)


if __name__ == '__main__':
    main()
