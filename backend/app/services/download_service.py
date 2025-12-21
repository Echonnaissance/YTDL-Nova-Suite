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
from app.config import settings
from pathlib import Path
import os
from typing import Any


def _make_absolute_media_urls(data: dict) -> dict:
    """
    Ensure `thumbnail_url` and `media_url` are absolute URLs pointing at the backend.
    This prevents the browser from resolving relative `/media/...` paths to the
    frontend dev server origin (Vite) which runs on a different port.
    """
    try:
        scheme = "https" if getattr(settings, "FORCE_HTTPS", False) else "http"
        host = getattr(settings, "HOST", "127.0.0.1")
        port = getattr(settings, "PORT", 8000)
        base = f"{scheme}://{host}:{port}".rstrip("/")

        # Normalize thumbnail_url
        tu = data.get("thumbnail_url")
        if tu and isinstance(tu, str):
            if tu.startswith("http"):
                # If absolute but points at a different host/port (e.g. Vite dev server),
                # rewrite to backend base while preserving path and query.
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(tu)
                netloc = f"{host}:{port}"
                if parsed.netloc != netloc:
                    new = parsed._replace(scheme=scheme, netloc=netloc)
                    data["thumbnail_url"] = urlunparse(new)
            else:
                # Ensure leading slash
                if not tu.startswith("/"):
                    tu = "/" + tu
                data["thumbnail_url"] = base + tu

        # Normalize media_url if present
        mu = data.get("media_url")
        if mu and isinstance(mu, str):
            if mu.startswith("http"):
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(mu)
                netloc = f"{host}:{port}"
                if parsed.netloc != netloc:
                    new = parsed._replace(scheme=scheme, netloc=netloc)
                    data["media_url"] = urlunparse(new)
            else:
                if not mu.startswith("/"):
                    mu = "/" + mu
                data["media_url"] = base + mu

    except Exception:
        # If anything goes wrong, don't block response; return original data
        return data
    return data


def _set_attr(obj: Any, name: str, value: Any) -> None:
    """Safely set attribute on SQLAlchemy model instances to avoid static type checks."""
    setattr(obj, name, value)


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
            raise InvalidURLError(
                "Invalid or unsupported URL. Please provide a link from a supported platform (YouTube, Twitter/X, Instagram, TikTok, etc.)")

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

        resp = DownloadResponse.model_validate(download)
        # Attach media_url if file_path present
        if resp.file_path:
            rel = str(Path(resp.file_path).resolve()).replace(
                str(settings.DOWNLOAD_DIR.resolve()), "").lstrip("/\\")
            media_url = f"/media/{rel.replace(os.sep, '/')}"
            data = resp.model_dump()
            data["media_url"] = media_url
            data = _make_absolute_media_urls(data)
            return DownloadResponse.model_validate(data)

        return resp

    async def get_download(self, download_id: int) -> DownloadResponse:
        """
        Get download by ID
        """
        download = self.db.query(Download).filter(
            Download.id == download_id).first()

        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")

        resp = DownloadResponse.model_validate(download)
        if resp.file_path:
            rel = str(Path(resp.file_path).resolve()).replace(
                str(settings.DOWNLOAD_DIR.resolve()), "").lstrip("/\\")
            media_url = f"/media/{rel.replace(os.sep, '/')}"
            data = resp.model_dump()
            data["media_url"] = media_url
            data = _make_absolute_media_urls(data)
            return DownloadResponse.model_validate(data)
        return resp

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

        results = []
        for d in downloads:
            resp = DownloadResponse.model_validate(d)
            if resp.file_path:
                rel = str(Path(resp.file_path).resolve()).replace(
                    str(settings.DOWNLOAD_DIR.resolve()), "").lstrip("/\\")
                media_url = f"/media/{rel.replace(os.sep, '/')}"
                data = resp.model_dump()
                data["media_url"] = media_url
                data = _make_absolute_media_urls(data)
                results.append(DownloadResponse.model_validate(data))
            else:
                results.append(resp)

        return results

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

        results = []
        for d in downloads:
            resp = DownloadResponse.model_validate(d)
            if resp.file_path:
                rel = str(Path(resp.file_path).resolve()).replace(
                    str(settings.DOWNLOAD_DIR.resolve()), "").lstrip("/\\")
                media_url = f"/media/{rel.replace(os.sep, '/')}"
                data = resp.model_dump()
                data["media_url"] = media_url
                data = _make_absolute_media_urls(data)
                results.append(DownloadResponse.model_validate(data))
            else:
                results.append(resp)

        return results

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
        download = self.db.query(Download).filter(
            Download.id == download_id).first()

        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")

        # Update fields (use helper to avoid static type-checker issues)
        _set_attr(download, 'status', status)

        if progress is not None:
            _set_attr(download, 'progress', progress)

        if speed is not None:
            _set_attr(download, 'speed', speed)

        if eta is not None:
            _set_attr(download, 'eta', eta)

        if error_message is not None:
            _set_attr(download, 'error_message', error_message)

        # Update timestamps
        if status == DownloadStatus.DOWNLOADING and (download.started_at is None):
            _set_attr(download, 'started_at', datetime.now())

        if status == DownloadStatus.COMPLETED:
            _set_attr(download, 'completed_at', datetime.now())
            _set_attr(download, 'progress', 100.0)

        self.db.commit()
        self.db.refresh(download)

        resp = DownloadResponse.model_validate(download)
        if resp.file_path:
            rel = str(Path(resp.file_path).resolve()).replace(
                str(settings.DOWNLOAD_DIR.resolve()), "").lstrip("/\\")
            media_url = f"/media/{rel.replace(os.sep, '/')}"
            data = resp.model_dump()
            data["media_url"] = media_url
            data = _make_absolute_media_urls(data)
            return DownloadResponse.model_validate(data)
        return resp

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
        download = self.db.query(Download).filter(
            Download.id == download_id).first()

        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")

        _set_attr(download, 'file_path', file_path)

        if file_size is not None:
            _set_attr(download, 'file_size', file_size)

        if file_name is not None:
            _set_attr(download, 'file_name', file_name)

        self.db.commit()
        self.db.refresh(download)

        resp = DownloadResponse.model_validate(download)
        if resp.file_path:
            rel = str(Path(resp.file_path).resolve()).replace(
                str(settings.DOWNLOAD_DIR.resolve()), "").lstrip("/\\")
            media_url = f"/media/{rel.replace(os.sep, '/')}"
            data = resp.model_dump()
            data["media_url"] = media_url
            data = _make_absolute_media_urls(data)
            return DownloadResponse.model_validate(data)
        return resp

    async def delete_download(self, download_id: int) -> bool:
        """
        Delete a download record
        """
        download = self.db.query(Download).filter(
            Download.id == download_id).first()

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
        download = self.db.query(Download).filter(
            Download.id == download_id).first()

        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")

        _set_attr(download, 'status', DownloadStatus.PENDING)
        _set_attr(download, 'progress', 0.0)
        _set_attr(download, 'error_message', None)
        # increment retry_count safely
        _set_attr(download, 'retry_count', (download.retry_count or 0) + 1)

        self.db.commit()
        self.db.refresh(download)

        resp = DownloadResponse.model_validate(download)
        if resp.file_path:
            rel = str(Path(resp.file_path).resolve()).replace(
                str(settings.DOWNLOAD_DIR.resolve()), "").lstrip("/\\")
            media_url = f"/media/{rel.replace('\\\\', '/')}"
            data = resp.model_dump()
            data["media_url"] = media_url
            data = _make_absolute_media_urls(data)
            return DownloadResponse.model_validate(data)
        return resp

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
