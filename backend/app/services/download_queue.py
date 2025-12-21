"""
Download Queue Manager
Handles background execution of downloads using asyncio
"""
import asyncio
from typing import Optional
from datetime import datetime

from app.models.database import Download, DownloadStatus, DownloadType, UserSettings
from app.core.database import SessionLocal
from app.services.ytdlp_service import YTDLPService
from app.services.metadata_service import MetadataService
from app.core.exceptions import YTDLPError, ServiceUnavailableError
from app.config import settings as app_settings


class DownloadQueue:
    """
    Manages background download execution using asyncio
    """

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.queue: asyncio.Queue = asyncio.Queue()
        self.active_downloads: set = set()
        self.running = False
        self.worker_task: Optional[asyncio.Task] = None
        self.ytdlp = YTDLPService()
        self.metadata = MetadataService()

    async def start(self):
        """Start the download queue worker"""
        if self.running:
            return

        self.running = True
        self.worker_task = asyncio.create_task(self._worker())
        print("[+] Download queue started")

    async def stop(self):
        """Stop the download queue worker"""
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        print("[*] Download queue stopped")

    async def add_download(self, download_id: int):
        """Add a download to the queue"""
        await self.queue.put(download_id)
        print(
            f"[+] Added download {download_id} to queue (queue size: {self.queue.qsize()})")

    async def _worker(self):
        """Main worker loop that processes downloads"""
        while self.running:
            try:
                # Wait for a download or timeout to check if we should stop
                try:
                    download_id = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Check if we've hit the concurrent download limit
                while len(self.active_downloads) >= self.max_concurrent:
                    await asyncio.sleep(0.5)

                # Process the download
                self.active_downloads.add(download_id)
                asyncio.create_task(self._process_download(download_id))

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[!] Error in download queue worker: {str(e)}")
                await asyncio.sleep(1)

    async def _process_download(self, download_id: int):
        """Process a single download"""
        db = SessionLocal()
        try:
            # Get download from database
            download = db.query(Download).filter(
                Download.id == download_id).first()
            if not download:
                print(f"[!] Download {download_id} not found in database")
                return

            # Get custom download location from user settings
            user_settings = db.query(UserSettings).first()
            custom_download_dir = None
            if user_settings and user_settings.download_location:
                custom_download_dir = user_settings.download_location
            else:
                custom_download_dir = str(app_settings.DOWNLOAD_DIR)

            # Update status to processing
            download.status = DownloadStatus.PROCESSING
            download.started_at = datetime.utcnow()
            db.commit()
            print(f"[*] Starting download {download_id}: {download.title}")

            # Execute the download based on type
            try:
                if download.download_type == DownloadType.AUDIO:
                    file_path = await self.ytdlp.download_audio(
                        url=download.url,
                        format=download.format,
                        embed_thumbnail=True,
                        custom_download_dir=custom_download_dir
                    )
                elif download.download_type == DownloadType.VIDEO:
                    file_path = await self.ytdlp.download_video(
                        url=download.url,
                        quality=download.quality,
                        format=download.format,
                        custom_download_dir=custom_download_dir
                    )
                else:
                    raise ValueError(
                        f"Unsupported download type: {download.download_type}")

                # Download succeeded
                download.status = DownloadStatus.COMPLETED
                download.file_path = file_path
                download.progress = 100
                download.completed_at = datetime.utcnow()
                db.commit()
                print(f"[+] Download {download_id} completed: {file_path}")

                # Automatically extract metadata and generate thumbnail
                print(f"[*] Processing metadata for download {download_id}")
                asyncio.create_task(self._process_metadata_async(download_id))

            except (YTDLPError, ServiceUnavailableError) as e:
                # Download failed
                download.status = DownloadStatus.FAILED
                download.error_message = str(e)
                db.commit()
                print(f"[!] Download {download_id} failed: {str(e)}")

        except Exception as e:
            print(
                f"[!] Unexpected error processing download {download_id}: {str(e)}")
            try:
                download = db.query(Download).filter(
                    Download.id == download_id).first()
                if download:
                    download.status = DownloadStatus.FAILED
                    download.error_message = f"Internal error: {str(e)}"
                    db.commit()
            except:
                pass

        finally:
            self.active_downloads.discard(download_id)
            db.close()

    async def _process_metadata_async(self, download_id: int):
        """
        Process metadata in a background task
        Extracts duration and generates thumbnail for a completed download
        """
        # Use a new DB session for background processing
        db = SessionLocal()
        try:
            download = db.query(Download).filter(
                Download.id == download_id).first()
            if download and download.status == DownloadStatus.COMPLETED:
                await self.metadata.process_download(download, db)
        except Exception as e:
            print(
                f"[!] Error in background metadata processing for download {download_id}: {e}")
        finally:
            db.close()


# Global queue instance
_download_queue: Optional[DownloadQueue] = None


def get_download_queue() -> DownloadQueue:
    """Get the global download queue instance"""
    global _download_queue
    if _download_queue is None:
        from app.config import settings
        _download_queue = DownloadQueue(
            max_concurrent=settings.MAX_CONCURRENT_DOWNLOADS)
    return _download_queue
