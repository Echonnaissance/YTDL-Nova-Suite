"""
Download Service
Business logic for managing downloads and building media URLs
"""
from app.config import settings
from app.core.exceptions import DownloadNotFoundError, InvalidURLError
from app.services.ytdlp_service import YTDLPService
from app.models.schemas import DownloadRequest, DownloadResponse
from app.models.database import Download, DownloadStatus
from sqlalchemy.orm import Session
import requests
import os
from pathlib import Path
from datetime import datetime
from typing import Any, List, Optional
from typing import Any
from sqlalchemy import desc
from typing import List, Optional
from typing import List, Optional, Any
"""
Download Service
Business logic for managing downloads and building media URLs
"""


def _make_absolute_media_urls(data: dict) -> dict:
    from urllib.parse import urlparse
    try:
        scheme = "https" if getattr(settings, "FORCE_HTTPS", False) else "http"
        host = getattr(settings, "HOST", "127.0.0.1")
        port = getattr(settings, "PORT", 8000)
        base = f"{scheme}://{host}:{port}"

        for key in ("thumbnail_url", "media_url"):
            val = data.get(key)
            if not val or not isinstance(val, str):
                continue
            parsed = urlparse(val)
            if parsed.scheme:
                continue
            if not val.startswith("/"):
                val = "/" + val
            data[key] = base + val
    except Exception:
        pass
    return data


def _build_media_url_from_path(file_path: str) -> Optional[str]:
    try:
        p = Path(file_path)
        resolved = p.resolve(strict=False)
        download_dir = settings.DOWNLOAD_DIR.resolve()
        if not str(resolved).startswith(str(download_dir)):
            return None
        rel = str(resolved).replace(str(download_dir), "").lstrip("/\\")
        return f"/media/{rel.replace(os.sep, '/')}"
    except Exception:
        return None


def _set_attr(obj: Any, name: str, value: Any) -> None:
    try:
        setattr(obj, name, value)
    except Exception:
        pass


class DownloadService:
    def __init__(self, db: Session):
        self.db = db
        self.ytdlp = YTDLPService()

    async def create_download(self, request: DownloadRequest) -> DownloadResponse:
        if not self.ytdlp.is_valid_url(request.url):
            raise InvalidURLError("Invalid or unsupported URL")

        download = Download(
            url=request.url,
            download_type=request.download_type,
            format=request.format,
            quality=request.quality,
            embed_thumbnail=request.embed_thumbnail,
            status=DownloadStatus.PENDING,
            progress=0.0,
        )

        # Try to extract metadata (non-fatal)
        try:
            info = await self.ytdlp.get_video_info(request.url)
            _set_attr(download, 'title', info.get('title'))
            _set_attr(download, 'thumbnail_url', info.get(
                'thumbnail_url') or info.get('thumbnail'))
            _set_attr(download, 'duration', int(info.get('duration') or 0))
        except Exception:
            pass

        self.db.add(download)
        self.db.commit()
        self.db.refresh(download)

        resp = DownloadResponse.model_validate(download)
        if resp.file_path:
            media_url = _build_media_url_from_path(resp.file_path)
            if media_url:
                data = resp.model_dump()
                data['media_url'] = media_url
                data = _make_absolute_media_urls(data)
                return DownloadResponse.model_validate(data)
        return resp

    async def get_all_downloads(self, skip: int = 0, limit: int = 100, status: Optional[DownloadStatus] = None) -> List[DownloadResponse]:
        query = self.db.query(Download).order_by(Download.id.desc())
        if status is not None:
            query = query.filter(Download.status == status)
        downloads = query.offset(skip).limit(limit).all()

        results: List[DownloadResponse] = []
        for d in downloads:
            resp = DownloadResponse.model_validate(d)
            if resp.file_path:
                media_url = _build_media_url_from_path(resp.file_path)
                if media_url:
                    data = resp.model_dump()
                    data['media_url'] = media_url
                    data = _make_absolute_media_urls(data)
                    results.append(DownloadResponse.model_validate(data))
                    continue
            results.append(resp)
        return results

    async def get_active_downloads(self) -> List[DownloadResponse]:
        downloads = self.db.query(Download).filter(
            Download.status.in_([
                DownloadStatus.DOWNLOADING,
                DownloadStatus.PROCESSING,
                DownloadStatus.QUEUED,
            ])
        ).all()

        results: List[DownloadResponse] = []
        for d in downloads:
            resp = DownloadResponse.model_validate(d)
            if resp.file_path:
                media_url = _build_media_url_from_path(resp.file_path)
                if media_url:
                    data = resp.model_dump()
                    data['media_url'] = media_url
                    data = _make_absolute_media_urls(data)
                    results.append(DownloadResponse.model_validate(data))
                    continue
            results.append(resp)
        return results

    async def get_download(self, download_id: int) -> DownloadResponse:
        download = self.db.query(Download).filter(
            Download.id == download_id).first()
        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")
        resp = DownloadResponse.model_validate(download)
        if resp.file_path:
            media_url = _build_media_url_from_path(resp.file_path)
            if media_url:
                data = resp.model_dump()
                data['media_url'] = media_url
                data = _make_absolute_media_urls(data)
                return DownloadResponse.model_validate(data)
        return resp

    async def update_download_status(self, download_id: int, status: DownloadStatus, progress: Optional[float] = None, speed: Optional[str] = None, eta: Optional[str] = None, error_message: Optional[str] = None) -> DownloadResponse:
        download = self.db.query(Download).filter(
            Download.id == download_id).first()
        if not download:
            raise DownloadNotFoundError(f"Download {download_id} not found")

        _set_attr(download, 'status', status)
        if progress is not None:
            _set_attr(download, 'progress', progress)
        if speed is not None:
            _set_attr(download, 'speed', speed)
        if eta is not None:
            _set_attr(download, 'eta', eta)
        if error_message is not None:
            _set_attr(download, 'error_message', error_message)

        if status == DownloadStatus.DOWNLOADING and download.started_at is None:
            _set_attr(download, 'started_at', datetime.now())
        if status == DownloadStatus.COMPLETED:
            _set_attr(download, 'completed_at', datetime.now())
            _set_attr(download, 'progress', 100.0)

        self.db.commit()
        self.db.refresh(download)

        resp = DownloadResponse.model_validate(download)
        if resp.file_path:
            media_url = _build_media_url_from_path(resp.file_path)
            if media_url:
                data = resp.model_dump()
                data['media_url'] = media_url
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

    async def validate_media_urls(self, data: dict) -> dict:
        """
        Validate and normalize media URLs in the download data
        """
        media_urls = [
            data.get("media_url"),
            data.get("thumbnail_url")
        ]

        # Base URL for constructing absolute URLs
        scheme = "https" if getattr(settings, "FORCE_HTTPS", False) else "http"
        host = getattr(settings, "HOST", "127.0.0.1")
        port = getattr(settings, "PORT", 8000)
        base = f"{scheme}://{host}:{port}"

        # iterate candidate media url fragments and validate them
        for mu in media_urls:
            # skip empty fragments
            if not mu:
                continue

            full_url = base + mu
            resp = None
            results = {}

            try:
                # prefer lightweight HEAD first
                resp = requests.head(full_url, timeout=5, allow_redirects=True)
                if resp.status_code != 200:
                    # fallback to GET if HEAD not successful
                    resp = requests.get(full_url, timeout=5, stream=True)
                results = resp.headers if resp is not None else {}
            except requests.RequestException:
                # network error or timeout; treat as no headers
                results = {}

            # assign media_url after attempting validation (even if headers empty)
            data["media_url"] = full_url
            # Prefer original thumbnail_url if present
            if "thumbnail_url" not in data or not data["thumbnail_url"]:
                data["thumbnail_url"] = full_url

        return data
        media_url = f"/media/{rel.replace(os.sep, '/')}"
