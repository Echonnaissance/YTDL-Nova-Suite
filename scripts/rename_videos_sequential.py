#!/usr/bin/env python3
"""Rename video files and thumbnails to a simple sequential pattern: Video_01, Video_02, ...

Rules
- Operates only on downloads whose file_path exists under Downloads/Video.
- Keeps the original file extension (e.g., .mp4, .mkv).
- Thumbnails (if present) are renamed to Video_XX.jpg and thumbnail_url is updated.
- DB fields updated: file_path, file_name, thumbnail_url (when thumb renamed).

Usage (run from repo root with venv activated):
  python scripts/rename_videos_sequential.py
"""
from pathlib import Path
import sqlite3
import sys
import os


REPO = Path(__file__).resolve().parents[1]
DB = REPO / "backend" / "universal_media_downloader.db"
VIDEO_DIR = REPO / "Downloads" / "Video"
THUMB_DIR = REPO / "Downloads" / "Thumbnails"


def normalized_thumb_path(url: str) -> Path | None:
    if not url:
        return None
    # Expect paths like /media/Thumbnails/<name>.jpg
    name = url.split("/")[-1]
    if not name:
        return None
    return THUMB_DIR / name


def main():
    if not DB.exists():
        print("DB not found:", DB)
        return 1
    if not VIDEO_DIR.exists():
        print("Video directory not found:", VIDEO_DIR)
        return 1

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        "SELECT id, file_path, file_name, thumbnail_url FROM downloads WHERE file_path IS NOT NULL"
    )
    rows = cur.fetchall()

    # Filter to files physically under Downloads/Video
    video_rows = []
    for rid, fpath, fname, thumb in rows:
        if not fpath:
            continue
        p = Path(fpath)
        try:
            resolved = p.resolve()
        except Exception:
            continue
        try:
            resolved.relative_to(VIDEO_DIR)
        except Exception:
            continue
        if not resolved.exists():
            continue
        video_rows.append((rid, resolved, fname, thumb))

    if not video_rows:
        print("No video rows found under", VIDEO_DIR)
        conn.close()
        return 0

    video_rows.sort(key=lambda r: r[0])  # sort by id for stable ordering
    digits = max(2, len(str(len(video_rows))))

    updates = []
    for idx, (rid, path, fname, thumb) in enumerate(video_rows, start=1):
        new_base = f"Video_{idx:0{digits}d}"
        new_name = new_base + path.suffix
        new_path = path.with_name(new_name)

        # Rename the video file if needed
        if path != new_path:
            if new_path.exists():
                print(f"SKIP id={rid}: target exists {new_path}")
                continue
            try:
                path.rename(new_path)
                print(f"Renamed file: {path.name} -> {new_name}")
            except OSError as e:
                print(f"Failed to rename {path} -> {new_path}: {e}")
                continue

        # Handle thumbnail rename
        new_thumb_url = None
        if thumb:
            tpath = normalized_thumb_path(thumb)
            if tpath and tpath.exists():
                new_thumb_name = f"Thumbnail_{idx:0{digits}d}.jpg"
                new_tpath = tpath.with_name(new_thumb_name)
                if tpath != new_tpath:
                    if new_tpath.exists():
                        print(
                            f"SKIP thumb for id={rid}: target exists {new_tpath}")
                    else:
                        try:
                            tpath.rename(new_tpath)
                            print(
                                f"Renamed thumb: {tpath.name} -> {new_thumb_name}")
                            new_thumb_url = f"/media/Thumbnails/{new_thumb_name}"
                        except OSError as e:
                            print(
                                f"Failed to rename thumb {tpath} -> {new_tpath}: {e}")
                else:
                    new_thumb_url = thumb

        updates.append((str(new_path), new_name, new_thumb_url, rid))

    # Apply DB updates
    for fpath, fname, thumb_url, rid in updates:
        cur.execute(
            "UPDATE downloads SET file_path=?, file_name=? WHERE id=?", (fpath, fname, rid))
        if thumb_url:
            cur.execute(
                "UPDATE downloads SET thumbnail_url=? WHERE id=?", (thumb_url, rid))

    conn.commit()
    conn.close()
    print(f"Updated {len(updates)} rows. Pattern: Video_{{1..{len(updates)}}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
