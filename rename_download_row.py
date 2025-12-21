#!/usr/bin/env python3
import sqlite3
import shutil
import sys
import json
import os
DB = 'backend/universal_media_downloader.db'
if len(sys.argv) != 2:
    print("Usage: rename_download_row.py <mappings.json>")
    sys.exit(2)
mfile = sys.argv[1]
mappings = json.load(open(mfile))
shutil.copy(DB, DB+'.bak')
conn = sqlite3.connect(DB)
c = conn.cursor()
c.execute('PRAGMA foreign_keys=OFF')
for m in mappings:
    src_id = m.get('src_id')      # existing row id to move (required)
    dst_id = m.get('dst_id')      # desired id (required)
    # dict of column: value to set on dst row after move
    updates = m.get('fields', {})
    # ensure src exists
    c.execute('SELECT id FROM downloads WHERE id=?', (src_id,))
    if not c.fetchone():
        raise SystemExit(f"source id {src_id} not found")
    # ensure dst doesn't exist (or handle by moving dst to temp)
    c.execute('SELECT id FROM downloads WHERE id=?', (dst_id,))
    if c.fetchone():
        # move dst to a temporary id to avoid conflict
        tmp = -abs(dst_id)-1
        c.execute('UPDATE downloads SET id=? WHERE id=?', (tmp, dst_id))
        dst_was_temp = tmp
    else:
        dst_was_temp = None
    # move src -> dst
    c.execute('UPDATE downloads SET id=? WHERE id=?', (dst_id, src_id))
    # if dst had been moved to tmp, move it now to src_id (so data isn't lost)
    if dst_was_temp is not None:
        c.execute('UPDATE downloads SET id=? WHERE id=?',
                  (src_id, dst_was_temp))
    # apply field updates to dst_id
    if updates:
        cols = ', '.join(f"{k} = ?" for k in updates.keys())
        vals = list(updates.values()) + [dst_id]
        c.execute(f'UPDATE downloads SET {cols} WHERE id=?', vals)
conn.commit()
conn.close()
print("Done. Backup:", DB+'.bak')
