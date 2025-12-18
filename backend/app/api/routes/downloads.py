"""
Downloads API Routes
Handles HTTP endpoints for download operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

from app.core.database import get_db
from app.services.download_service import DownloadService
from app.models.schemas import (
    DownloadRequest,
    DownloadResponse,
    VideoInfoRequest,
    VideoInfoResponse,
    DownloadListResponse,
    PlaylistInfoResponse
)
from app.models.database import DownloadStatus
from app.core.exceptions import (
    DownloadNotFoundError,
    InvalidURLError,
    YouTubeDownloaderException
)
from app.services.download_queue import get_download_queue
from app.core.security import sanitize_url, check_disk_space, check_user_quota
from app.config import settings

logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/downloads", tags=["downloads"])


def get_download_service(db: Session = Depends(get_db)) -> DownloadService:
    """
    Dependency to get DownloadService instance
    """
    return DownloadService(db)


@router.post("/", response_model=DownloadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def create_download(
    request: Request,
    download_request: DownloadRequest = Body(...),
    service: DownloadService = Depends(get_download_service)
):
    """
    Create a new download

    - **url**: Media URL (YouTube, Twitter/X, Instagram, TikTok, etc.)
    - **download_type**: Type of download (video, audio, playlist)
    - **quality**: Video quality (best, 1080p, 720p, etc.)
    - **format**: Output format (mp4, m4a, webm, etc.)
    - **embed_thumbnail**: Embed thumbnail in audio files

    Returns the created download with status PENDING

    SECURITY: Rate limited to prevent abuse, URL sanitized to prevent command injection
    """
    # Log the raw request body and headers for debugging
    raw_body = await request.body()
    logger.error(f"RAW REQUEST BODY: {raw_body}")
    logger.error(f"REQUEST HEADERS: {dict(request.headers)}")
    logger.error(f"PARSED download_request: {download_request}")
    # Validate download_request and url
    if download_request is None or getattr(download_request, "url", None) is None:
        logger.error(
            f"Missing or invalid download_request: {download_request}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must include a valid 'url' field."
        )
    try:
        # SECURITY: Sanitize URL to prevent command injection
        download_request.url = sanitize_url(download_request.url)
        logger.info(f"Creating download for URL: {download_request.url}")

        # SECURITY: Check disk space before allowing download
        check_disk_space()

        # SECURITY: Check user quota (uses total download directory size)
        check_user_quota()

        # Create download record
        download = await service.create_download(download_request)

        # Add to download queue for processing
        queue = get_download_queue()
        await queue.add_download(download.id)

        return download
    except ValueError as e:
        # URL sanitization failed
        logger.warning(
            f"Invalid URL rejected: {getattr(download_request, 'url', None)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidURLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except YouTubeDownloaderException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[DownloadResponse])
async def get_all_downloads(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000,
                       description="Maximum number of records to return"),
    status: Optional[DownloadStatus] = Query(
        None, description="Filter by status"),
    service: DownloadService = Depends(get_download_service)
):
    """
    Get all downloads with optional filtering

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **status**: Filter by download status
    """
    downloads = await service.get_all_downloads(skip=skip, limit=limit, status=status)
    return downloads


@router.get("/active", response_model=List[DownloadResponse])
async def get_active_downloads(
    service: DownloadService = Depends(get_download_service)
):
    """
    Get all currently active downloads
    (downloading, processing, or queued)
    """
    downloads = await service.get_active_downloads()
    return downloads


@router.get("/stats")
async def get_download_stats(
    service: DownloadService = Depends(get_download_service)
):
    """
    Get download statistics
    Returns counts by status
    """
    stats = await service.get_download_stats()
    return stats


@router.get("/{download_id}", response_model=DownloadResponse)
async def get_download(
    download_id: int,
    service: DownloadService = Depends(get_download_service)
):
    """
    Get a specific download by ID
    """
    try:
        download = await service.get_download(download_id)
        return download
    except DownloadNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{download_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_download(
    download_id: int,
    service: DownloadService = Depends(get_download_service)
):
    """
    Delete a download record
    """
    try:
        await service.delete_download(download_id)
        return None
    except DownloadNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{download_id}/cancel", response_model=DownloadResponse)
async def cancel_download(
    download_id: int,
    service: DownloadService = Depends(get_download_service)
):
    """
    Cancel an active download
    """
    try:
        download = await service.cancel_download(download_id)
        return download
    except DownloadNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{download_id}/retry", response_model=DownloadResponse)
async def retry_download(
    download_id: int,
    service: DownloadService = Depends(get_download_service)
):
    """
    Retry a failed download
    Resets status to PENDING and clears error message
    """
    try:
        download = await service.retry_download(download_id)
        return download
    except DownloadNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/video-info", response_model=VideoInfoResponse)
# SECURITY: Rate limit info endpoint
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_video_info(
    request: Request,
    video_info_request: VideoInfoRequest,
    service: DownloadService = Depends(get_download_service)
):
    """
    Get information about a video from a supported platform without downloading

    - **url**: Media URL (YouTube, Twitter/X, Instagram, TikTok, etc.)

    Returns video metadata (title, duration, thumbnail, etc.)

    SECURITY: Rate limited to prevent reconnaissance attacks
    """
    try:
        # SECURITY: Sanitize URL
        video_info_request.url = sanitize_url(video_info_request.url)

        info = await service.ytdlp.get_video_info(video_info_request.url)
        return info
    except ValueError as e:
        logger.warning(
            f"Invalid URL rejected in video-info: {video_info_request.url}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidURLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except YouTubeDownloaderException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/playlist-info", response_model=PlaylistInfoResponse)
# SECURITY: Rate limit info endpoint
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def get_playlist_info(
    request: Request,
    playlist_info_request: VideoInfoRequest,
    service: DownloadService = Depends(get_download_service)
):
    """
    Get information about a playlist from a supported platform without downloading

    - **url**: Playlist URL (YouTube, etc.)

    Returns playlist metadata (title, video count, video list, etc.)

    SECURITY: Rate limited to prevent reconnaissance attacks
    """
    try:
        # SECURITY: Sanitize URL
        playlist_info_request.url = sanitize_url(playlist_info_request.url)

        info = await service.ytdlp.get_playlist_info(playlist_info_request.url)
        return info
    except ValueError as e:
        logger.warning(
            f"Invalid URL rejected in playlist-info: {playlist_info_request.url}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidURLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except YouTubeDownloaderException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/batch", response_model=List[DownloadResponse], status_code=status.HTTP_201_CREATED)
# Stricter limit for batch
@limiter.limit(f"{settings.RATE_LIMIT_PER_HOUR}/hour")
async def create_batch_downloads(
    request: Request,
    requests: List[DownloadRequest],
    service: DownloadService = Depends(get_download_service)
):
    """
    Create multiple downloads at once (batch mode)

    - **requests**: List of download requests

    Returns list of created downloads

    SECURITY: Stricter rate limit (per hour), URL sanitization for all requests
    """
    try:
        # SECURITY: Limit batch size to prevent abuse
        MAX_BATCH_SIZE = 50
        if len(requests) > MAX_BATCH_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size too large. Maximum: {MAX_BATCH_SIZE} downloads"
            )

        downloads = []
        queue = get_download_queue()

        for download_request in requests:
            # SECURITY: Sanitize URL to prevent command injection
            download_request.url = sanitize_url(download_request.url)

            # Create download record
            download = await service.create_download(download_request)
            downloads.append(download)

            # Add to download queue for processing
            await queue.add_download(download.id)

        logger.info(f"Batch download created: {len(downloads)} items")
        return downloads
    except ValueError as e:
        # URL sanitization failed
        logger.warning(f"Invalid URL in batch rejected")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except InvalidURLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except YouTubeDownloaderException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
