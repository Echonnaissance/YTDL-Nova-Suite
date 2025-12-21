# Automatic Metadata Population

## Overview

Downloads now automatically populate metadata (thumbnail + duration) when they complete, eliminating the need for manual script execution.

## What Changed

### New Service: `metadata_service.py`

- `MetadataService` class handles automatic thumbnail generation and metadata extraction
- Uses ffmpeg to extract thumbnails from videos/audio (tries embedded cover art first)
- Uses ffmpeg to extract duration from media files
- Automatically updates DB with `thumbnail_url`, `duration`, and `file_size`

### Updated Service: `download_queue.py`

- Added `MetadataService` initialization in `DownloadQueue.__init__()`
- Added `_process_metadata_async()` method to handle background metadata processing
- Hooked metadata processing into `_process_download()` immediately after status=COMPLETED
- Background task runs in parallel without blocking download queue

## How It Works

1. User initiates download via frontend/API
2. `DownloadQueue` processes download using `YTDLPService`
3. When download succeeds:
   - Status set to `COMPLETED`
   - `file_path` saved to DB
   - **NEW**: `_process_metadata_async()` spawned as background task
4. Background task:
   - Opens new DB session (isolated from download queue)
   - Extracts duration using ffmpeg
   - Generates thumbnail (tries embedded cover, falls back to video frame)
   - Updates DB with `thumbnail_url`, `duration`, `file_size`
5. Frontend refreshes and immediately shows video with thumbnail + formatted duration

## Benefits

- **Zero manual steps**: No need to run `populate-meta` or `fill-durations` scripts
- **Instant availability**: Downloads appear in Video Player immediately after completion
- **Non-blocking**: Metadata processing runs in background, doesn't slow down queue
- **Automatic retries**: If metadata extraction fails, download still succeeds (graceful degradation)

## Thumbnail Storage

- Thumbnails saved to `Downloads/Thumbnails/`
- Naming pattern: `{download_id}_{filename_stem}.jpg`
- Database stores relative URL: `/media/Thumbnails/{thumbnail_name}.jpg`

## Manual Override

If automatic processing fails or you need to regenerate metadata:

```bash
# Regenerate all metadata
python scripts/cli_tools.py populate-meta
python scripts/cli_tools.py fill-durations

# Or use manage_media.py
python scripts/manage_media.py populate-meta
python scripts/manage_media.py fill-durations
```

## Testing

To test the automatic workflow:

1. Start backend: `cd backend && uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Download any video via the UI
4. Watch terminal for metadata processing logs:
   ```
   [+] Download 40 completed: Downloads/Video/example.mp4
   [*] Processing metadata for download 40
   [+] Extracted duration for download 40: 180.50s
   [+] Created thumbnail for download 40
   ```
5. Refresh Video Player page - video appears with thumbnail and formatted duration

## Troubleshooting

If thumbnails/durations don't appear:

- Check backend terminal for error messages
- Verify ffmpeg.exe is in project root or PATH
- Check file permissions on Downloads/Thumbnails/ directory
- Manually run: `python scripts/cli_tools.py inspect` to see DB state
