import os
import sqlite3
import sys
import datetime
DB = os.path.join('backend', 'universal_media_downloader.db')
# ID to fix
DOWNLOAD_ID = 45
# Filename as present in Downloads/Video
FNAME = '🌸 ᗰEᖇᑌᑕᑕᑌᗷᑌS 🔞 - ➜ Come here for NSFW AI realistic and hentai image generation and unf....mp4'
file_path = os.path.join(os.getcwd(), 'Downloads', 'Video', FNAME)
if not os.path.exists(file_path):
    print('File not found:', file_path)
    sys.exit(1)
size = os.path.getsize(file_path)
conn = sqlite3.connect(DB)
cur = conn.cursor()
completed_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# Update record
cur.execute('''UPDATE downloads SET file_path=?, file_name=?, file_size=?, status=?, completed_at=?, updated_at=? WHERE id=?''',
            (file_path, FNAME, size, 'COMPLETED', completed_at, completed_at, DOWNLOAD_ID))
conn.commit()
print('Updated download', DOWNLOAD_ID, '->', file_path, 'size', size)
conn.close()
