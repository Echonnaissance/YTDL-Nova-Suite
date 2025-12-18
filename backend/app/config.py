"""
Application Configuration
Manages environment variables and application settings
"""
from typing import TYPE_CHECKING
from functools import lru_cache
from pathlib import Path
from typing import Optional, List
import os

# Make BaseSettings visible to static analyzers while keeping runtime compatibility
if TYPE_CHECKING:
    # Statically import from pydantic so Pylance treats it as a proper base class
    from pydantic import BaseSettings  # type: ignore

try:
    # Prefer pydantic v2 settings package at runtime
    from pydantic_settings import BaseSettings
except Exception:
    # Fall back to pydantic (v1 or compatibility)
    from pydantic import BaseSettings

# Ensure static analyzers see `BaseSettings` as a class/type
from typing import cast, Any
BaseSettings = cast(type, BaseSettings)  # type: ignore


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Application Info
    APP_NAME: str = "Universal Media Downloader API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Database Settings
    DATABASE_URL: str = "sqlite:///./youtube_downloader.db"
    # For PostgreSQL in production:
    # DATABASE_URL: str = "postgresql://user:password@localhost/dbname"

    # File Storage Settings
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DOWNLOAD_DIR: Path = BASE_DIR / "Downloads"
    TEMP_DIR: Path = BASE_DIR / "temp"

    # External Tools
    YTDLP_PATH: Path = BASE_DIR / "yt-dlp.exe"
    FFMPEG_PATH: Path = BASE_DIR / "ffmpeg.exe"

    # Download Settings
    MAX_CONCURRENT_DOWNLOADS: int = 3
    MAX_QUEUE_SIZE: int = 100
    DEFAULT_VIDEO_FORMAT: str = "mp4"
    DEFAULT_AUDIO_FORMAT: str = "m4a"
    DEFAULT_QUALITY: str = "best"

    # Cookie Browser (for Twitter/X and other platforms that require authentication)
    # Options: 'chrome', 'firefox', 'edge', 'opera', 'chromium', 'brave', 'safari', or None
    # Note: Brave is fully supported. Firefox with Tor proxy works normally (use 'firefox').
    # For Tor Browser specifically, use 'firefox' but cookies may be limited due to privacy settings.
    # To support authenticated downloads (Twitter/X, etc.), set COOKIE_BROWSER and provide cookies file path
    # Example: COOKIE_BROWSER='chrome' and COOKIES_FILE='C:/Users/YourUser/AppData/Local/Google/Chrome/User Data/Default/Cookies'
    COOKIE_BROWSER: Optional[str] = None
    COOKIES_FILE: Optional[str] = None

    # WebSocket Settings
    WS_MESSAGE_QUEUE_SIZE: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30

    # Security
    # IMPORTANT: Set SECRET_KEY environment variable in production!
    # Generate a secure key with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    SECRET_KEY: str = "dev-secret-key-CHANGE-ME-IN-PRODUCTION-OR-SET-ENV-VAR"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API Key Authentication
    # Set ENABLE_API_KEY_AUTH=true and API_KEY=<your-key> in production
    ENABLE_API_KEY_AUTH: bool = False
    API_KEY: str = ""  # Set via environment variable

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60  # Requests per minute
    RATE_LIMIT_PER_HOUR: int = 1000  # Requests per hour

    # Request Size Limits (in bytes)
    MAX_REQUEST_SIZE: int = 1024 * 1024  # 1 MB

    # Download Limits (SECURITY: Prevent disk exhaustion)
    MAX_FILE_SIZE: int = 5 * 1024 * 1024 * 1024  # 5 GB per file
    MAX_USER_QUOTA: int = 100 * 1024 * 1024 * 1024  # 100 GB total per user
    MIN_FREE_DISK_SPACE: int = 10 * 1024 * 1024 * 1024  # Require 10 GB free

    def validate_secret_key(self):
        """Validate secret key in production"""
        if not self.DEBUG and ("dev-secret-key" in self.SECRET_KEY or "your-secret-key" in self.SECRET_KEY):
            raise ValueError(
                "SECRET_KEY must be set to a secure value in production! "
                "Set the SECRET_KEY environment variable. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )

    def validate_cors_origins(self):
        """SECURITY: Validate CORS origins in production"""
        if not self.DEBUG:
            # Production validation
            for origin in self.CORS_ORIGINS:
                # Must be HTTPS in production
                if not origin.startswith("https://"):
                    raise ValueError(
                        f"Production CORS origin must use HTTPS: {origin}. "
                        "HTTP origins are not secure for production deployments."
                    )
                # Wildcard not allowed
                if "*" in origin:
                    raise ValueError(
                        "Wildcard CORS origins (*) are not allowed in production. "
                        "Specify exact domains for security."
                    )
            import logging
            logging.getLogger(__name__).info(
                f"CORS origins validated for production: {self.CORS_ORIGINS}")

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Using lru_cache ensures we only create one instance
    """
    import logging
    logger = logging.getLogger(__name__)

    settings = Settings()
    settings.validate_secret_key()
    settings.validate_cors_origins()
    return settings


# Create necessary directories on startup
def init_directories():
    """Create required directories if they don't exist"""
    settings = get_settings()
    settings.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Create Audio and Video subdirectories
    audio_dir = settings.DOWNLOAD_DIR / "Audio"
    video_dir = settings.DOWNLOAD_DIR / "Video"
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)


# Export settings instance
settings = get_settings()
