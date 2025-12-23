#!/usr/bin/env python3
"""bulk_import.py

Interactive bulk-import helper:
- Prompt for a source directory containing media files
- Move (default) or copy files into `Downloads/Video` (unique names preserved)
- Run the standard maintenance commands once at the end:
  - scan-fix-paths
  - populate-meta
  - fill-durations

Run from repository root with the repo venv active:
  python scripts/bulk_import.py
"""
from pathlib import Path
import shutil
import sys
import subprocess
import os


VIDEO_EXTS = {'.mp4', '.mkv', '.webm', '.mov',
              '.m4v', '.avi', '.flv', '.mp3', '.m4a', '.aac'}


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


def run_manage(repo_root: Path, command: str) -> int:
    cmd = [sys.executable, str(
        repo_root / 'scripts' / 'manage_media.py'), command]
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def gather_files(src: Path):
    files = []
    for p in src.rglob('*'):
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
            files.append(p)
    return sorted(files)


def main():
    repo = Path(__file__).resolve().parents[1]
    downloads_video = repo / 'Downloads' / 'Video'

    print('Bulk import helper: move or copy many files into Downloads/Video and register them in the DB.')
    src_input = input('Enter source directory (or drag it here): ').strip()
    if not src_input:
        print('No directory provided. Exiting.')
        sys.exit(1)
    src = Path(src_input).expanduser()
    if not src.exists() or not src.is_dir():
        print('Source directory not found or not a directory:', src)
        sys.exit(2)

    files = gather_files(src)
    if not files:
        print('No media files found in', src)
        sys.exit(0)

    print(f'Found {len(files)} media files (extensions: {sorted(VIDEO_EXTS)})')
    do_copy = input('Copy instead of move? [y/N]: ').strip().lower() == 'y'
    confirm = input(
        f"Proceed to {'copy' if do_copy else 'move'} these files into {downloads_video}? [y/N]: ").strip().lower()
    if confirm != 'y':
        print('Aborted by user.')
        sys.exit(0)

    downloads_video.mkdir(parents=True, exist_ok=True)
    moved = 0
    skipped = 0
    for f in files:
        dest = downloads_video / f.name
        dest = unique_dest(dest)
        try:
            if do_copy:
                shutil.copy2(f, dest)
                print('Copied:', f, '->', dest)
            else:
                shutil.move(str(f), str(dest))
                print('Moved:', f, '->', dest)
            moved += 1
        except Exception as e:
            print('Failed to move/copy', f, ':', e)
            skipped += 1

    print(f'Done. {moved} files processed, {skipped} skipped.')

    run_now = input(
        'Run maintenance commands to register and populate metadata now? [Y/n]: ').strip().lower()
    if run_now == 'n':
        print('Skipping maintenance commands. Run these when ready:')
        print('  python scripts/manage_media.py scan-fix-paths')
        print('  python scripts/manage_media.py populate-meta')
        print('  python scripts/manage_media.py fill-durations')
        sys.exit(0)

    steps = ['scan-fix-paths', 'populate-meta', 'fill-durations']
    for step in steps:
        rc = run_manage(repo, step)
        if rc != 0:
            print(f'{step} returned code {rc} (continuing)')

    print('Maintenance complete. Verify with: python scripts/inspect_db.py')


if __name__ == '__main__':
    main()
