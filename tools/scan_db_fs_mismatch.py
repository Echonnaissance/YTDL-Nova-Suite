#!/usr/bin/env python3
import sqlite3
import os
import json
from pathlib import Path

DB = 'backend/universal_media_downloader.db'
ROOT = Path('.')
VIDEOS_DIR = ROOT / 'Downloads' / 'Video'
THUMBS_DIR = ROOT / 'Downloads' / 'Thumbnails'


def get_db_rows():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM downloads')
    rows = c.fetchall()
    conn.close()
    return rows


def find_row_by_file_name(rows, fname):
    for r in rows:
        if r['file_name'] and os.path.basename(r['file_name']) == fname:
            return r
        if r['file_path'] and os.path.basename(r['file_path']) == fname:
            return r
    return None


def find_rows_by_thumbnail(rows, tname):
    matches = []
    for r in rows:
        if not r['thumbnail_url']:
            continue
        if tname in r['thumbnail_url'] or os.path.basename(r['thumbnail_url']) == tname:
            matches.append(r)
    return matches


def main():
    rows = get_db_rows()
    videos = sorted([p.name for p in VIDEOS_DIR.glob('*.mp4')]
                    ) if VIDEOS_DIR.exists() else []
    thumbs = sorted([p.name for p in THUMBS_DIR.glob('*')]
                    ) if THUMBS_DIR.exists() else []

    report = {'videos': [], 'thumbnails': []}

    for v in videos:
        row = find_row_by_file_name(rows, v)
        if row:
            report['videos'].append({'file': v, 'status': 'matched', 'id': row['id'],
                                    'title': row['title'], 'thumbnail_url': row['thumbnail_url']})
        else:
            # try to find candidate by numeric index in filename (Video_XX)
            cand = None
            if v.lower().startswith('video_'):
                try:
                    num = int(v.split('_')[1].split('.')[0])
                except Exception:
                    num = None
                if num is not None:
                    # search rows where file_name or title contains that number
                    for r in rows:
                        if r['file_name'] and f"{num:02d}" in r['file_name']:
                            cand = r
                            break
                        if r['title'] and str(num) in str(r['title']):
                            cand = r
                            break
            report['videos'].append({'file': v, 'status': 'unmatched', 'candidate': (
                {'id': cand['id'], 'title': cand['title']} if cand else None)})

    for t in thumbs:
        matches = find_rows_by_thumbnail(rows, t)
        if matches:
            report['thumbnails'].append(
                {'file': t, 'status': 'matched', 'ids': [r['id'] for r in matches]})
        else:
            report['thumbnails'].append({'file': t, 'status': 'unmatched'})

    # Also detect rows that reference thumbnails that don't exist on disk
    missing_thumbs = []
    for r in rows:
        if r['thumbnail_url']:
            bn = os.path.basename(r['thumbnail_url'])
            if bn and not (THUMBS_DIR / bn).exists():
                missing_thumbs.append(
                    {'id': r['id'], 'thumbnail_url': r['thumbnail_url']})
    report['missing_thumbnails'] = missing_thumbs

    # Print concise human-readable output
    print('--- Video files mapping ---')
    for v in report['videos']:
        if v['status'] == 'matched':
            print(
                f"{v['file']} -> id={v['id']}, title={v['title']}, thumbnail={v['thumbnail_url']}")
        else:
            cand = v.get('candidate')
            if cand:
                print(
                    f"{v['file']} -> UNMATCHED; suggested id={cand['id']} (title={cand['title']})")
            else:
                print(f"{v['file']} -> UNMATCHED; no candidate found")

    print('\n--- Thumbnails mapping ---')
    for t in report['thumbnails']:
        if t['status'] == 'matched':
            ids = ','.join(map(str, t['ids']))
            print(f"{t['file']} -> referenced by id(s): {ids}")
        else:
            print(f"{t['file']} -> UNMATCHED")

    print('\n--- DB rows with missing thumbnail files ---')
    for m in report['missing_thumbnails']:
        print(f"id={m['id']} references {m['thumbnail_url']} (missing on disk)")

    # Save JSON for later use
    out = Path('tools') / 'scan_report.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print('\nReport saved to', out)


if __name__ == '__main__':
    main()
