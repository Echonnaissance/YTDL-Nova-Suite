#!/usr/bin/env python3
import sqlite3
import shutil
from pathlib import Path
DB = Path('backend/universal_media_downloader.db')
BACKUP = DB.with_suffix('.db.bak')
shutil.copy(DB, BACKUP)
conn = sqlite3.connect(str(DB))
c = conn.cursor()
for i in range(1, 46):
    nn = f"{i:02d}"
    c.execute("UPDATE downloads SET thumbnail_url=? WHERE id=?",
              (f"/media/Thumbnails/Thumbnail_{nn}.jpg", i))
conn.commit()
for row in c.execute("SELECT id,thumbnail_url FROM downloads WHERE id BETWEEN 1 AND 45 ORDER BY id"):
    print(f"{row[0]}|{row[1]}")
conn.close()
print('done; backup at', BACKUP)
