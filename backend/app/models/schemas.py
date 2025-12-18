"""
Pydantic Schemas
Define API request/response models and validation
These are the "contracts" between frontend and backend
"""
from pydantic import BaseModel, HttpUrl, Field, field_validator
from datetime import datetime
from typing import Optional, ClassVar
from app.models.database import DownloadStatus, DownloadType


# ============================================================================
# Download Schemas
# ============================================================================

class DownloadRequest(BaseModel):
    """Request schema for creating a new download"""
    url: str = Field(...,
                     description="Media URL (YouTube, Twitter/X, Instagram, TikTok, etc.)")
    download_type: DownloadType = Field(
        DownloadType.AUDIO, description="Type of download")
    quality: str = Field(
        "best", description="Video quality (best, 1080p, 720p, etc.)")
    format: str = Field(
        "m4a", description="Output format (mp4, m4a, webm, etc.)")
    embed_thumbnail: bool = Field(
        True, description="Embed thumbnail in audio files")

    # SECURITY: Whitelist allowed values to prevent injection
    ALLOWED_QUALITIES: ClassVar[list[str]] = [
        "best", "worst", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
    ALLOWED_VIDEO_FORMATS: ClassVar[list[str]] = [
        "mp4", "webm", "mkv", "flv", "avi"]
    ALLOWED_AUDIO_FORMATS: ClassVar[list[str]] = [
        "m4a", "mp3", "opus", "vorbis", "flac", "wav", "aac"]

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL looks like a supported media URL"""
        # Accept any URL, let backend service check support
        if not v.lower().startswith("http"):
            raise ValueError("Must be a valid URL")
        return v

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, v: str) -> str:
        """SECURITY: Whitelist quality values to prevent command injection"""
        if v not in cls.ALLOWED_QUALITIES:
            raise ValueError(
                f"Quality must be one of: {', '.join(cls.ALLOWED_QUALITIES)}")
        return v

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """SECURITY: Whitelist format values to prevent command injection"""
        all_formats = cls.ALLOWED_VIDEO_FORMATS + cls.ALLOWED_AUDIO_FORMATS
        if v not in all_formats:
            raise ValueError(
                f"Format must be one of: {', '.join(all_formats)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "download_type": "audio",
                "quality": "best",
                "format": "m4a",
                "embed_thumbnail": True
            }
        }


class DownloadResponse(BaseModel):
    """Response schema for download information"""
    id: int
    url: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None  # seconds (can be fractional)
    download_type: DownloadType
    format: str
    quality: str
    status: DownloadStatus
    progress: float
    speed: Optional[str] = None
    eta: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    playlist_title: Optional[str] = None
    playlist_index: Optional[int] = None

    model_config = {
        "from_attributes": True  # Allows creating from SQLAlchemy models
    }


class DownloadUpdate(BaseModel):
    """Schema for updating download status"""
    status: Optional[DownloadStatus] = None
    progress: Optional[float] = None
    speed: Optional[str] = None
    eta: Optional[str] = None
    error_message: Optional[str] = None


class DownloadListResponse(BaseModel):
    """Response schema for list of downloads"""
    downloads: list[DownloadResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# Video Info Schemas
# ============================================================================

class VideoInfoRequest(BaseModel):
    """Request schema for getting video information"""
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL looks like a supported media URL"""
        if not v.lower().startswith("http"):
            raise ValueError("Must be a valid URL")
        return v


class VideoInfoResponse(BaseModel):
    """Response schema for video information"""
    url: str
    title: str
    thumbnail_url: Optional[str] = None
    duration: float  # seconds (can be fractional)
    uploader: Optional[str] = None
    view_count: Optional[int] = None
    is_playlist: bool = False
    playlist_count: Optional[int] = None


class PlaylistVideoInfo(BaseModel):
    """Individual video in a playlist"""
    id: str
    title: str
    url: str
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None


class PlaylistInfoResponse(BaseModel):
    """Response schema for playlist information"""
    url: str
    title: str
    video_count: int
    videos: list[PlaylistVideoInfo]


# ============================================================================
# Queue Schemas
# ============================================================================

class QueueStatus(BaseModel):
    """Current queue status"""
    total: int
    pending: int
    downloading: int
    completed: int
    failed: int
    queue_size: int
    active_downloads: list[DownloadResponse]


# ============================================================================
# Settings Schemas
# ============================================================================

class UserSettingsResponse(BaseModel):
    """Response schema for user settings"""
    dark_mode: bool
    notifications_enabled: bool
    default_download_type: DownloadType
    default_video_quality: str
    default_audio_format: str
    default_embed_thumbnail: bool
    max_concurrent_downloads: int
    auto_cleanup_temp_files: bool
    download_location: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class UserSettingsUpdate(BaseModel):
    """Request schema for updating user settings"""
    dark_mode: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    default_download_type: Optional[DownloadType] = None
    default_video_quality: Optional[str] = None
    default_audio_format: Optional[str] = None
    default_embed_thumbnail: Optional[bool] = None
    max_concurrent_downloads: Optional[int] = None
    auto_cleanup_temp_files: Optional[bool] = None
    download_location: Optional[str] = None


# ============================================================================
# WebSocket Schemas
# ============================================================================

class WSMessage(BaseModel):
    """WebSocket message schema"""
    type: str  # "progress", "status", "error", "complete"
    download_id: int
    data: dict


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Health Check
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    ytdlp_available: bool
    ffmpeg_available: bool
    database_ok: bool
