import subprocess
import datetime
import sqlite3
import sys
import os
#!/usr/bin/env python3
"""fix_download.py - interactively update a download DB row's file_path/status

This script no longer requires CLI arguments. Run it and follow prompts.
"""


def run_inspect():
    """Run scripts/inspect_db.py to show recent downloads."""
    script = os.path.join(os.getcwd(), 'scripts', 'inspect_db.py')
    try:
        subprocess.run([sys.executable, script], check=True)
    except Exception:
        print('Failed to run inspect_db.py')


def prompt(prompt_text, default=None):
    if default is not None:
        prompt_text = f"{prompt_text} [{default}]: "
    else:
        prompt_text = f"{prompt_text}: "
    val = input(prompt_text).strip()
    if val == '' and default is not None:
        return default
    return val


def main():
    print('This helper updates a download record to point to a local file and mark it COMPLETED.')
    print('If you do not remember the id, press Enter to list recent rows.')
    id_in = input(
        'Enter download id (or press Enter to list recent): ').strip()
    if id_in == '':
        run_inspect()
        id_in = input('Enter download id: ').strip()
    try:
        download_id = int(id_in)
    except Exception:
        print('Invalid id.')
        sys.exit(2)

    file_path = input(
        'Enter absolute path to file (or drag a file here): ').strip()
    if not file_path:
        print('No file path provided. Aborting.')
        sys.exit(3)
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        print('File not found:', file_path)
        sys.exit(4)

    DB = os.path.join('backend', 'universal_media_downloader.db')
    if not os.path.exists(DB):
        print('Database not found:', DB)
        sys.exit(5)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    size = os.path.getsize(file_path)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur.execute(
        'UPDATE downloads SET file_path=?, file_name=?, file_size=?, status=?, completed_at=?, updated_at=? WHERE id=?',
        (file_path, os.path.basename(file_path),
         size, 'COMPLETED', now, now, download_id),
    )
    conn.commit()
    print('Updated download', download_id)
    conn.close()


if __name__ == '__main__':
    main()
