#!/usr/bin/env python3
"""Fix enum string values in the downloads DB inserted by scripts (normalize to uppercase names)."""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / \
    'backend' / 'universal_media_downloader.db'


def main():
    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()
    cur.execute(
        "UPDATE downloads SET download_type='VIDEO' WHERE download_type='video'")
    cur.execute(
        "UPDATE downloads SET download_type='AUDIO' WHERE download_type='audio'")
    cur.execute(
        "UPDATE downloads SET download_type='PLAYLIST' WHERE download_type='playlist'")
    # normalize status values
    cur.execute("UPDATE downloads SET status='PENDING' WHERE status='pending'")
    cur.execute(
        "UPDATE downloads SET status='QUEUED' WHERE status='queued'")
    cur.execute(
        "UPDATE downloads SET status='DOWNLOADING' WHERE status='downloading'")
    cur.execute(
        "UPDATE downloads SET status='PROCESSING' WHERE status='processing'")
    cur.execute(
        "UPDATE downloads SET status='COMPLETED' WHERE status='completed'")
    cur.execute(
        "UPDATE downloads SET status='FAILED' WHERE status='failed'")
    cur.execute(
        "UPDATE downloads SET status='CANCELLED' WHERE status='cancelled'")
    conn.commit()
    cur.execute(
        "SELECT COUNT(*) FROM downloads WHERE download_type IN ('video','audio','playlist')")
    print('Remaining lowercase enum rows:', cur.fetchone()[0])
    conn.close()


if __name__ == '__main__':
    main()
