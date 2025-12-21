#!/usr/bin/env python3
import sqlite3
import requests
import shutil
import os
import subprocess
from urllib.parse import urlparse, unquote
from typing import Any, cast
# yt_dlp will be imported lazily inside yt_dlp_filename if available; otherwise the yt-dlp executable is used

DB = 'backend/universal_media_downloader.db'
shutil.copy(DB, DB+'.bak')
conn = sqlite3.connect(DB)
c = conn.cursor()


def head_filename(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=10)
        cd = r.headers.get('content-disposition')
        if cd and 'filename=' in cd:
            return cd.split('filename=')[-1].strip(' \'"')
    except Exception:
        pass
    return None


def url_path_filename(url):
    p = urlparse(url).path
    name = os.path.basename(p)
    return unquote(name) if name else None


def yt_dlp_filename(url):
    # Try the Python package first (if installed)
    try:
        from yt_dlp import YoutubeDL  # type: ignore
        with YoutubeDL(cast(Any, {'quiet': True, 'skip_download': True})) as ydl:
            info = ydl.extract_info(url, download=False)
            return ydl.prepare_filename(info)
    except Exception:
        pass

    # Fallback: try to call the yt-dlp executable to get the filename
    # search common executable names and repository locations
    exe_candidates = ['yt-dlp', 'yt-dlp.exe']
    search_paths = [
        os.path.join(os.path.dirname(__file__), '..'),
        os.path.join(os.path.dirname(__file__), '..', 'dist'),
        os.path.join(os.path.dirname(__file__), '..', 'backend'),
        os.getcwd()
    ]
    for exe in exe_candidates:
        path = shutil.which(exe)
        if not path:
            for sp in search_paths:
                candidate = os.path.join(sp, exe)
                if os.path.exists(candidate):
                    path = os.path.abspath(candidate)
                    break
        if not path:
            continue
        try:
            proc = subprocess.run(
                [path, '--no-playlist', '--skip-download',
                    '--get-filename', '-o', '%(title)s.%(ext)s', url],
                capture_output=True, text=True, timeout=30
            )
            if proc.returncode == 0:
                out = proc.stdout.strip().splitlines()
                if out:
                    return out[0]
        except Exception:
            continue

    return None


c.execute("SELECT id, url, file_path, file_name FROM downloads")
rows = c.fetchall()
for id_, url, fp, fn in rows:
    if not url:
        continue
    # skip if already local Downloads path
    if fp and ('Downloads/Video' in (fp.replace('\\', '/')) or fp.startswith('file:')):
        continue
    name = head_filename(url) or url_path_filename(url) or yt_dlp_filename(url)
    if not name:
        print('could not determine name for id', id_)
        continue
    # optionally normalize extension to .mp4 or keep original
    # build local path (you can adapt to Preferred naming)
    local_name = name
    local_path = os.path.abspath(
        os.path.join('Downloads', 'Video', local_name))
    print('id', id_, '->', local_name)
    c.execute("UPDATE downloads SET file_name=?, file_path=? WHERE id=?",
              (local_name, local_path, id_))
conn.commit()
conn.close()
print('done; DB backed up to', DB+'.bak')
