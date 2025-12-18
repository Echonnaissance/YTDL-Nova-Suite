"""
Database Models
SQLAlchemy ORM models for database tables
"""
from typing import cast
import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, Float, Boolean, Text
from sqlalchemy.sql import func

from app.core.database import Base


class DownloadStatus(str, enum.Enum):
    """Download status enumeration"""
    PENDING = "pending"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadType(str, enum.Enum):
    """Download type enumeration"""
    VIDEO = "video"
    AUDIO = "audio"
    PLAYLIST = "playlist"


class Download(Base):
    """
    Download model - represents a download job
    Tracks all information about a video/audio download
    """
    __tablename__ = "downloads"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Basic info
    url = Column(String, nullable=False, index=True)
    title = Column(String)
    thumbnail_url = Column(String)
    duration = Column(Integer)  # Duration in seconds

    # Download configuration
    download_type = Column(SAEnum(DownloadType), default=DownloadType.VIDEO)
    format = Column(String, default="mp4")  # mp4, m4a, webm, etc.
    quality = Column(String, default="best")  # best, 1080p, 720p, etc.
    embed_thumbnail = Column(Boolean, default=True)

    # Status tracking
    status = Column(SAEnum(DownloadStatus),
                    default=DownloadStatus.PENDING, index=True)
    progress = Column(Float, default=0.0)  # 0.0 to 100.0
    speed = Column(String)  # Download speed (e.g., "2.5MB/s")
    eta = Column(String)  # Estimated time remaining (e.g., "00:45")

    # File info
    file_path = Column(String)
    file_size = Column(Integer)  # Size in bytes
    file_name = Column(String)

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, onupdate=func.now())

    # Playlist info (if applicable)
    playlist_id = Column(String)  # For grouping playlist downloads
    playlist_index = Column(Integer)  # Position in playlist
    playlist_title = Column(String)

    def __repr__(self) -> str:
        return f"<Download(id={self.id}, title='{self.title}', status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if download is currently active"""
        return cast(bool, self.status in {
            DownloadStatus.DOWNLOADING,
            DownloadStatus.PROCESSING,
            DownloadStatus.QUEUED,
        })

    @property
    def is_complete(self) -> bool:
        """Check if download is completed"""
        return cast(bool, self.status == DownloadStatus.COMPLETED)

    @property
    def is_failed(self) -> bool:
        """Check if download failed"""
        return cast(bool, self.status in {DownloadStatus.FAILED, DownloadStatus.CANCELLED})


class UserSettings(Base):
    """
    User settings model
    Stores user preferences and configuration
    """
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True)

    # UI preferences
    dark_mode = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=True)

    # Download defaults
    default_download_type = Column(
        SAEnum(DownloadType), default=DownloadType.AUDIO)
    default_video_quality = Column(String, default="best")
    default_audio_format = Column(String, default="m4a")
    default_embed_thumbnail = Column(Boolean, default=True)

    # Advanced settings
    max_concurrent_downloads = Column(Integer, default=3)
    auto_cleanup_temp_files = Column(Boolean, default=True)
    download_location = Column(String)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self) -> str:
        return f"<UserSettings(id={self.id})>"
