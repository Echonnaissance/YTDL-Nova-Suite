#!/usr/bin/env python3
"""
Scan Downloads/Video for media files and update DB `file_path` for completed downloads missing it.

Usage: run from repo root (script expects backend/universal_media_downloader.db and Downloads/Video)
"""
import sqlite3
import sys
from pathlib import Path
import difflib


REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "backend" / "universal_media_downloader.db"
DOWNLOADS_VIDEO = REPO_ROOT / "Downloads" / "Video"


def gather_files(root: Path):
    files = {}
    for p in root.rglob("*"):
        if p.is_file():
            files[p.name.lower()] = str(p.resolve())
    return files


def slugify(s: str):
    return ''.join(c.lower() if c.isalnum() else ' ' for c in (s or '')).strip()


def main():
    if not DB_PATH.exists():
        print(f"DB not found: {DB_PATH}")
        sys.exit(1)

    if not DOWNLOADS_VIDEO.exists():
        print(f"Downloads folder not found: {DOWNLOADS_VIDEO}")
        sys.exit(1)

    files = gather_files(DOWNLOADS_VIDEO)
    print(f"Found {len(files)} files under {DOWNLOADS_VIDEO}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        "SELECT id, title, file_name, file_path FROM downloads WHERE status='COMPLETED'")
    rows = cur.fetchall()
    print(f"DB completed downloads: {len(rows)}")

    updated = 0
    matched = []
    unmatched = []

    # keep track of which files have been assigned
    assigned = set()

    for r in rows:
        did = r['id']
        title = r['title'] or ''
        fname = r['file_name'] or ''
        fpath = r['file_path'] or ''

        # if file_path already valid, skip
        if fpath:
            if Path(fpath).exists():
                # ok
                continue

        chosen = None

        # exact filename match
        if fname:
            key = fname.lower()
            if key in files:
                if key not in assigned:
                    chosen = files[key]
                    assigned.add(key)

        # try matching by filename without extension
        if not chosen and fname:
            base = Path(fname).stem.lower()
            for k, v in files.items():
                if Path(k).stem.lower() == base and k not in assigned:
                    chosen = v
                    assigned.add(k)
                    break

        # fuzzy match against title using sequence matcher
        if not chosen and title:
            s = slugify(title)
            best = None
            best_ratio = 0.0
            for k, v in files.items():
                fname_slug = slugify(k)
                ratio = difflib.SequenceMatcher(a=s, b=fname_slug).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best = v
            if best_ratio >= 0.6:
                # ensure best isn't already assigned
                best_key = Path(best).name.lower() if best else None
                if best_key and best_key not in assigned:
                    chosen = best
                    assigned.add(best_key)
            else:
                # fallback: pick best match even if below threshold, prefer unassigned
                if best:
                    best_key = Path(best).name.lower()
                    if best_key not in assigned:
                        chosen = best
                        assigned.add(best_key)

        if chosen:
            print(f"Match for id={did}: {chosen}")
            cur.execute(
                "UPDATE downloads SET file_path=? WHERE id=?", (chosen, did))
            updated += 1
            matched.append((did, chosen))
        else:
            unmatched.append((did, title, fname))

    conn.commit()
    print(f"Updated {updated} rows")
    if unmatched:
        print("Unmatched records:")
        for u in unmatched:
            print(u)

    # Now insert any files that are not referenced in the DB as new completed downloads
    cur.execute("SELECT file_path FROM downloads WHERE file_path IS NOT NULL")
    existing = {str(Path(r[0]).resolve()).lower() for r in cur.fetchall()}

    to_insert = []
    for fname, p in files.items():
        rp = str(Path(p).resolve()).lower()
        if rp not in existing:
            to_insert.append(p)

    inserted = 0
    for p in to_insert:
        size = None
        try:
            size = Path(p).stat().st_size
        except Exception:
            size = None

        url = f"file://{p}"
        title = Path(p).stem
        fmt = Path(p).suffix.lstrip('.') or 'mp4'
        sql = (
            "INSERT INTO downloads (url, title, download_type, format, quality, "
            "status, progress, file_path, file_size, file_name) VALUES (?,?,?,?,?,?,?,?,?,?)"
        )
        cur.execute(
            sql,
            (
                url,
                title,
                'video',
                fmt,
                'best',
                'completed',
                100.0,
                p,
                size,
                Path(p).name,
            ),
        )
        inserted += 1

    if inserted:
        conn.commit()
    conn.close()

    print(
        "Inserted %d new DB rows for files not present in downloads table" % inserted
    )


if __name__ == '__main__':
    main()
