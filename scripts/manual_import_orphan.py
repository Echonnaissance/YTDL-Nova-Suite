#!/usr/bin/env python3
from app.models.database import Download, DownloadStatus, DownloadType
from app.core.database import SessionLocal
from app.config import settings
from datetime import datetime
import subprocess
import re
import os
import sys
from pathlib import Path

# Ensure backend is importable
sys.path.insert(0, str(Path.cwd() / 'backend'))


VIDEO_DIR = Path.cwd() / 'Downloads' / 'Video'
THUMBS_DIR = Path.cwd() / 'Downloads' / 'Thumbnails'

print(f"Scanning video dir: {VIDEO_DIR}")
if not VIDEO_DIR.exists():
    print("Video directory not found. Exiting.")
    sys.exit(1)

files = [f for f in VIDEO_DIR.iterdir() if f.is_file()]
# gather used numbers
used = set()
for f in files:
    m = re.match(r'^Video_(\d+)\.', f.name)
    if m:
        try:
            used.add(int(m.group(1)))
        except ValueError:
            pass

n = 1
while n in used:
    n += 1

# find orphan file (not matching Video_XX.mp4)
orphan = None
for f in files:
    if not re.match(r'^Video_\d{2}\.mp4$', f.name):
        orphan = f
        break

if not orphan:
    print('No orphan file found.')
    sys.exit(0)

new_name = f'Video_{n:02d}' + orphan.suffix
new_path = VIDEO_DIR / new_name
print(f'Renaming {orphan.name} -> {new_name}')
try:
    orphan.rename(new_path)
except Exception as e:
    print(f'Failed to rename file: {e}')
    sys.exit(1)

THUMBS_DIR.mkdir(parents=True, exist_ok=True)
thumb_path = THUMBS_DIR / f'Thumbnail_{n:02d}.jpg'

# Find ffmpeg/ffprobe paths
ffmpeg_path = str(settings.FFMPEG_PATH) if getattr(
    settings, 'FFMPEG_PATH', None) and Path(settings.FFMPEG_PATH).exists() else 'ffmpeg'
ffprobe_path = str(settings.FFPROBE_PATH) if getattr(
    settings, 'FFPROBE_PATH', None) and Path(settings.FFPROBE_PATH).exists() else 'ffprobe'

print(f'Using ffmpeg: {ffmpeg_path}')
print(f'Using ffprobe: {ffprobe_path}')

# Create thumbnail (seek to 1s)
try:
    subprocess.run([
        ffmpeg_path, '-ss', '00:00:01', '-i', str(
            new_path), '-frames:v', '1', '-q:v', '2', str(thumb_path), '-y'
    ], check=True)
    print(f'Created thumbnail: {thumb_path}')
except Exception as e:
    print(f'ffmpeg failed to create thumbnail: {e}')

# Probe duration
duration_seconds = None
try:
    r = subprocess.run([
        ffprobe_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(
            new_path)
    ], capture_output=True, text=True)
    out = r.stdout.strip()
    if out:
        duration_seconds = int(float(out))
        print(f'Duration: {duration_seconds}s')
except Exception as e:
    print(f'ffprobe failed: {e}')

# Insert DB record
try:
    db = SessionLocal()
    d = Download(
        url='manual-import',
        title=f'Video_{n:02d}',
        thumbnail_url=f'/media/Thumbnails/Thumbnail_{n:02d}.jpg' if thumb_path.exists(
        ) else None,
        duration=duration_seconds,
        download_type=DownloadType.VIDEO,
        format=new_path.suffix.lstrip('.'),
        quality='best',
        status=DownloadStatus.COMPLETED,
        progress=100.0,
        file_path=str(new_path.resolve()),
        file_size=new_path.stat().st_size,
        file_name=new_path.name,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    db.add(d)
    db.commit()
    print('Inserted DB record id:', d.id)
    db.close()
except Exception as e:
    print('Failed to insert DB record:', e)
    sys.exit(1)

print('Manual import completed successfully.')
