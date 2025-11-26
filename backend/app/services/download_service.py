"""
Download Service
Business logic for managing downloads
Coordinates between API, database, and yt-dlp service
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.database import Download, DownloadStatus, DownloadType
from app.models.schemas import DownloadRequest, DownloadResponse
from app.services.ytdlp_service import YTDLPService
from app.core.exceptions import DownloadNotFoundError, InvalidURLError


class DownloadService:
    """
    Service for managing downloads
    Handles creation, retrieval, updates, and deletion of downloads
    """

    def __init__(self, db: Session):
        self.db = db
        self.ytdlp = YTDLPService()

    async def create_download(self, request: DownloadRequest) -> DownloadResponse:
        """
        Create a new download
        1. Validate URL
        2. Extract video info
        3. Create database record
        4. Return download info
        """
        # Validate URL
        if not self.ytdlp.is_valid_url(request.url):
            raise InvalidURLError("Invalid YouTube URL")

        # Get video information
        video_info = await self.ytdlp.get_video_info(request.url)

        # Create download record
        download = Download(
            url=request.url,
            title=video_info.get("title"),
            thumbnail_url=video_info.get("thumbnail_url"),
            duration=video_info.get("duration"),
            download_type=request.download_type,
            format=request.format,
            quality=request.quality,
            embed_thumbnail=request.embed_thumbnail,
            status=DownloadStatus.PENDING,
            progress=0.0
        )

        self.db.add(download)
        self.db.commit()
        self.db.refresh(download)

        return DownloadResponse.model_validate(download)

    async def get_download(self, download_id: int) -> DownloadResponse:
        """
        Get download by ID
        """
        download = self.db.query(Download).filter(Download.id == download_id).first()

        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")

        return DownloadResponse.model_validate(download)

    async def get_all_downloads(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[DownloadStatus] = None
    ) -> List[DownloadResponse]:
        """
        Get all downloads with optional filtering
        """
        query = self.db.query(Download).order_by(desc(Download.created_at))

        if status:
            query = query.filter(Download.status == status)

        downloads = query.offset(skip).limit(limit).all()

        return [DownloadResponse.model_validate(d) for d in downloads]

    async def get_active_downloads(self) -> List[DownloadResponse]:
        """
        Get all currently active downloads
        """
        downloads = self.db.query(Download).filter(
            Download.status.in_([
                DownloadStatus.DOWNLOADING,
                DownloadStatus.PROCESSING,
                DownloadStatus.QUEUED
            ])
        ).all()

        return [DownloadResponse.model_validate(d) for d in downloads]

    async def update_download_status(
        self,
        download_id: int,
        status: DownloadStatus,
        progress: Optional[float] = None,
        speed: Optional[str] = None,
        eta: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> DownloadResponse:
        """
        Update download status and progress
        """
        download = self.db.query(Download).filter(Download.id == download_id).first()

        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")

        # Update fields
        download.status = status

        if progress is not None:
            download.progress = progress

        if speed is not None:
            download.speed = speed

        if eta is not None:
            download.eta = eta

        if error_message is not None:
            download.error_message = error_message

        # Update timestamps
        if status == DownloadStatus.DOWNLOADING and not download.started_at:
            download.started_at = datetime.now()

        if status == DownloadStatus.COMPLETED:
            download.completed_at = datetime.now()
            download.progress = 100.0

        self.db.commit()
        self.db.refresh(download)

        return DownloadResponse.model_validate(download)

    async def update_download_file_info(
        self,
        download_id: int,
        file_path: str,
        file_size: Optional[int] = None,
        file_name: Optional[str] = None
    ) -> DownloadResponse:
        """
        Update file information for a download
        """
        download = self.db.query(Download).filter(Download.id == download_id).first()

        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")

        download.file_path = file_path

        if file_size is not None:
            download.file_size = file_size

        if file_name is not None:
            download.file_name = file_name

        self.db.commit()
        self.db.refresh(download)

        return DownloadResponse.model_validate(download)

    async def delete_download(self, download_id: int) -> bool:
        """
        Delete a download record
        """
        download = self.db.query(Download).filter(Download.id == download_id).first()

        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")

        self.db.delete(download)
        self.db.commit()

        return True

    async def cancel_download(self, download_id: int) -> DownloadResponse:
        """
        Cancel an active download
        """
        return await self.update_download_status(
            download_id,
            DownloadStatus.CANCELLED
        )

    async def retry_download(self, download_id: int) -> DownloadResponse:
        """
        Retry a failed download
        """
        download = self.db.query(Download).filter(Download.id == download_id).first()

        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")

        download.status = DownloadStatus.PENDING
        download.progress = 0.0
        download.error_message = None
        download.retry_count += 1

        self.db.commit()
        self.db.refresh(download)

        return DownloadResponse.model_validate(download)

    async def get_download_stats(self) -> dict:
        """
        Get statistics about downloads
        """
        total = self.db.query(Download).count()
        pending = self.db.query(Download).filter(
            Download.status == DownloadStatus.PENDING
        ).count()
        downloading = self.db.query(Download).filter(
            Download.status == DownloadStatus.DOWNLOADING
        ).count()
        completed = self.db.query(Download).filter(
            Download.status == DownloadStatus.COMPLETED
        ).count()
        failed = self.db.query(Download).filter(
            Download.status == DownloadStatus.FAILED
        ).count()

        return {
            "total": total,
            "pending": pending,
            "downloading": downloading,
            "completed": completed,
            "failed": failed
        }
