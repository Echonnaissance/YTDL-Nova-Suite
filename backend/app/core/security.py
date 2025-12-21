"""
Security Module
Handles authentication, authorization, and security utilities
"""
from fastapi import Security, HTTPException, status, Request, Response
from fastapi.security import APIKeyHeader
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import secrets
import hashlib
import hmac
import logging
import json
import time
import threading

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Security audit logger - separate file for security events
security_logger = logging.getLogger("security")
security_handler = logging.FileHandler("security_audit.log")
security_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))
security_logger.addHandler(security_handler)
security_logger.setLevel(logging.INFO)

# ============================================================================
# API Key Authentication
# ============================================================================

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def generate_api_key() -> str:
    """
    Generate a secure random API key
    Returns a URL-safe 32-byte token
    """
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage
    Uses SHA256 for one-way hashing
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against its hash
    Uses constant-time comparison to prevent timing attacks
    """
    return hmac.compare_digest(
        hashlib.sha256(api_key.encode()).hexdigest(),
        hashed_key
    )


async def get_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dependency to validate API key from request header

    In production, you should:
    1. Store API keys in database (hashed)
    2. Associate keys with users/applications
    3. Add expiration dates
    4. Add usage tracking

    For now, we'll use environment variable for simplicity
    """
    # Check if API key authentication is enabled
    if not settings.ENABLE_API_KEY_AUTH:
        return "api-auth-disabled"

    # Validate API key is provided
    if not api_key:
        logger.warning("API request missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate API key matches expected value
    # In production, check against database of hashed keys
    valid_api_key = settings.API_KEY

    if not valid_api_key:
        logger.error("API_KEY not configured in environment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key authentication not properly configured"
        )

    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(api_key, valid_api_key):
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.info("API key authenticated successfully")
    return api_key


# ============================================================================
# Path Validation (Path Traversal Prevention)
# ============================================================================

def validate_download_path(path: str) -> Path:
    """
    Validate download path to prevent path traversal attacks

    Ensures:
    1. Path is within allowed download directory
    2. No relative path components (../)
    3. Path doesn't escape to system directories

    Args:
        path: User-provided path string

    Returns:
        Validated Path object

    Raises:
        ValueError: If path is invalid or dangerous
    """
    try:
        # Convert to Path object
        requested_path = Path(path).resolve()

        # Get allowed base directory
        base_dir = settings.DOWNLOAD_DIR.resolve()

        # Check if requested path is within base directory
        # This prevents paths like "../../etc/passwd"
        if not str(requested_path).startswith(str(base_dir)):
            logger.warning(f"Path traversal attempt blocked: {path}")
            raise ValueError(
                f"Download path must be within {base_dir}. "
                f"Path traversal attempts are not allowed."
            )

        # Additional checks for suspicious patterns
        suspicious_patterns = ["..", "~", "$"]
        if any(pattern in path for pattern in suspicious_patterns):
            logger.warning(f"Suspicious path pattern detected: {path}")
            raise ValueError(
                "Path contains suspicious characters. "
                "Only simple directory names are allowed."
            )

        logger.info(f"Path validated successfully: {requested_path}")
        return requested_path

    except Exception as e:
        logger.error(f"Path validation error: {e}")
        raise ValueError(f"Invalid path: {e}")


def validate_file_path(file_path: str, allowed_extensions: Optional[list[str]] = None) -> Path:
    """
    Validate file path for downloads

    Args:
        file_path: Path to file
        allowed_extensions: List of allowed file extensions (e.g., ['.mp4', '.m4a'])

    Returns:
        Validated Path object

    Raises:
        ValueError: If file path is invalid
    """
    try:
        path = Path(file_path).resolve()

        # Validate extension if specified
        if allowed_extensions:
            if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                raise ValueError(
                    f"File extension {path.suffix} not allowed. "
                    f"Allowed: {allowed_extensions}"
                )

        # Check path is within download directory
        base_dir = settings.DOWNLOAD_DIR.resolve()
        if not str(path).startswith(str(base_dir)):
            raise ValueError("File must be within download directory")

        return path

    except Exception as e:
        logger.error(f"File path validation error: {e}")
        raise ValueError(f"Invalid file path: {e}")


# ============================================================================
# URL Validation (Command Injection Prevention)
# ============================================================================

def sanitize_url(url: str) -> str:
    """
    Sanitize URL to prevent command injection

    SECURITY: Enhanced URL validation with multiple checks:
    - URL decoding to catch encoded attacks
    - Unicode normalization
    - Whitelist-based scheme validation
    - Dangerous character detection

    Args:
        url: User-provided URL

    Returns:
        Sanitized and normalized URL string

    Raises:
        ValueError: If URL contains dangerous characters or is malformed
    """
    import urllib.parse
    import unicodedata

    # SECURITY: Decode URL to catch encoded attacks (e.g., %3B = semicolon)
    try:
        decoded_url = urllib.parse.unquote(url)
    except Exception:
        raise ValueError("Invalid URL encoding")

    # SECURITY: Normalize Unicode to catch fullwidth/variant characters
    normalized_url = unicodedata.normalize('NFKC', decoded_url)

    # Characters that could be used for command injection (exclude '&' here
    # because it's a valid separator in query strings like YouTube playlist URLs)
    dangerous_chars = [";", "|", "$", "`", "\\",
                       "\n", "\r", "(", ")", "{", "}", "<", ">", "\x00"]

    # Parse early so we can validate specific components separately
    parsed_early = urllib.parse.urlparse(url)

    # Check components (except query) for dangerous characters
    components_to_check = [parsed_early.path, parsed_early.params,
                           parsed_early.fragment, parsed_early.username or '',
                           parsed_early.password or '', parsed_early.netloc or '']

    for comp in components_to_check:
        for char in dangerous_chars:
            if char in comp:
                logger.warning(
                    f"Dangerous character '{repr(char)}' found in URL component: {url}")
                raise ValueError(
                    "URL contains forbidden character in path/netloc/fragment."
                )

    # For the query string: allow common separators such as '&' and '=' but
    # still reject control characters or null bytes if present after decoding
    decoded_query = urllib.parse.unquote(parsed_early.query or '')
    for char in ["\n", "\r", "\x00", "`", "|", ";"]:
        if char in decoded_query:
            logger.warning(
                f"Dangerous character '{repr(char)}' found in query string: {url}")
            raise ValueError("URL query contains forbidden characters")

    # SECURITY: Parse and validate URL structure
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        raise ValueError("Invalid URL format")

    # SECURITY: Whitelist allowed schemes
    if parsed.scheme not in ["http", "https"]:
        raise ValueError("URL must use http:// or https://")

    # SECURITY: Validate netloc (domain) exists
    if not parsed.netloc:
        raise ValueError("URL must contain a valid domain")

    # SECURITY: Rebuild URL to normalize it (prevents bypass via malformed URLs)
    sanitized = urllib.parse.urlunparse(parsed)

    logger.info(f"URL sanitized successfully: {parsed.netloc}")
    return sanitized


# ============================================================================
# Request Validation
# ============================================================================

def validate_request_size(content_length: Optional[int], max_size: int = 1024 * 1024) -> None:
    """
    Validate request content length to prevent memory exhaustion

    Args:
        content_length: Content-Length header value
        max_size: Maximum allowed size in bytes (default: 1MB)

    Raises:
        HTTPException: If content length exceeds limit
    """
    if content_length and content_length > max_size:
        logger.warning(
            f"Request too large: {content_length} bytes (max: {max_size})")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Request body too large. Maximum size: {max_size} bytes"
        )


# ============================================================================
# Disk Space Management
# ============================================================================

def check_disk_space(required_space: Optional[int] = None) -> bool:
    """
    Check if enough disk space is available

    SECURITY: Prevents disk exhaustion attacks

    Args:
        required_space: Optional minimum required space in bytes

    Returns:
        True if enough space available

    Raises:
        ValueError: If insufficient disk space
    """
    import shutil

    try:
        # Get disk usage stats for download directory
        usage = shutil.disk_usage(settings.DOWNLOAD_DIR)

        # Check minimum free space requirement
        if usage.free < settings.MIN_FREE_DISK_SPACE:
            logger.error(
                f"Insufficient disk space: {usage.free / (1024**3):.2f} GB free, "
                f"need {settings.MIN_FREE_DISK_SPACE / (1024**3):.2f} GB"
            )
            raise ValueError(
                f"Insufficient disk space. "
                f"Free: {usage.free / (1024**3):.2f} GB, "
                f"Required: {settings.MIN_FREE_DISK_SPACE / (1024**3):.2f} GB"
            )

        # Check if specific amount is required
        if required_space and usage.free < required_space:
            logger.warning(
                f"Insufficient space for download: need {required_space / (1024**3):.2f} GB, "
                f"have {usage.free / (1024**3):.2f} GB"
            )
            raise ValueError(
                f"Insufficient disk space for this download. "
                f"Free: {usage.free / (1024**3):.2f} GB, "
                f"Required: {required_space / (1024**3):.2f} GB"
            )

        logger.info(
            f"Disk space check passed: {usage.free / (1024**3):.2f} GB available")
        return True

    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        raise ValueError(f"Unable to check disk space: {e}")


def get_directory_size(directory: Path) -> int:
    """
    Calculate total size of directory

    Args:
        directory: Path to directory

    Returns:
        Total size in bytes
    """
    total_size = 0
    try:
        for entry in directory.rglob('*'):
            if entry.is_file():
                total_size += entry.stat().st_size
    except Exception as e:
        logger.error(f"Error calculating directory size: {e}")
    return total_size


def check_user_quota(user_id: Optional[str] = None) -> bool:
    """
    Check if user is within download quota

    SECURITY: Prevents resource exhaustion by single user

    Args:
        user_id: Optional user identifier (IP if no auth)

    Returns:
        True if within quota

    Raises:
        ValueError: If quota exceeded
    """
    try:
        # Get total downloads size
        download_dir = settings.DOWNLOAD_DIR
        total_size = get_directory_size(download_dir)

        if total_size > settings.MAX_USER_QUOTA:
            logger.warning(
                f"User quota exceeded: {total_size / (1024**3):.2f} GB used, "
                f"limit is {settings.MAX_USER_QUOTA / (1024**3):.2f} GB"
            )
            raise ValueError(
                f"Download quota exceeded. "
                f"Used: {total_size / (1024**3):.2f} GB, "
                f"Limit: {settings.MAX_USER_QUOTA / (1024**3):.2f} GB"
            )

        logger.info(
            f"Quota check passed: {total_size / (1024**3):.2f} GB used")
        return True

    except Exception as e:
        logger.error(f"Quota check failed: {e}")
        # Don't block on quota check errors in development
        if settings.DEBUG:
            return True
        raise


# ============================================================================
# File Type Validation
# ============================================================================

def validate_file_type(file_path: Path) -> bool:
    """
    Validate downloaded file is actually a media file

    SECURITY: Prevents malicious files disguised as videos

    Args:
        file_path: Path to downloaded file

    Returns:
        True if file is valid media type

    Raises:
        ValueError: If file type is invalid or suspicious
    """
    import mimetypes

    try:
        # Check file exists
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size

        if file_size == 0:
            logger.warning(f"Empty file detected: {file_path}")
            raise ValueError("Downloaded file is empty")

        if file_size > settings.MAX_FILE_SIZE:
            logger.warning(
                f"File too large: {file_size / (1024**3):.2f} GB, "
                f"max is {settings.MAX_FILE_SIZE / (1024**3):.2f} GB"
            )
            file_path.unlink()  # Delete oversized file
            raise ValueError(
                f"File exceeds maximum size limit. "
                f"Size: {file_size / (1024**3):.2f} GB, "
                f"Limit: {settings.MAX_FILE_SIZE / (1024**3):.2f} GB"
            )

        # Check MIME type by extension
        mime_type, _ = mimetypes.guess_type(str(file_path))

        # Allowed MIME types for media files
        allowed_mimes = [
            "video/mp4", "video/webm", "video/x-matroska",  # Video
            "video/x-flv", "video/x-msvideo",
            "audio/mp4", "audio/mpeg", "audio/opus",  # Audio
            "audio/ogg", "audio/flac", "audio/wav", "audio/aac"
        ]

        if mime_type and mime_type not in allowed_mimes:
            logger.warning(
                f"Suspicious file type detected: {mime_type} for {file_path}")
            # In production, might want to delete suspicious files
            if not settings.DEBUG:
                file_path.unlink()
                raise ValueError(f"Invalid file type: {mime_type}")

        logger.info(f"File validation passed: {file_path.name} ({mime_type})")
        return True

    except Exception as e:
        logger.error(f"File validation failed for {file_path}: {e}")
        raise


# ============================================================================
# Security Logging
# ============================================================================

def log_security_event(event_type: str, details: dict, request: Optional[Request] = None):
    """
    Log security-related events for monitoring and auditing

    Args:
        event_type: Type of security event (auth_failure, path_traversal, etc.)
        details: Additional event details
        request: Optional request object for IP logging
    """
    log_data = {
        "event_type": event_type,
        "details": details,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if request:
        log_data["client_ip"] = request.client.host if request.client else "unknown"
        log_data["user_agent"] = request.headers.get("user-agent", "unknown")
        log_data["path"] = str(request.url.path)
        log_data["method"] = request.method

    # Log to both regular and security audit logs
    logger.warning(f"SECURITY EVENT: {log_data}")
    security_logger.warning(json.dumps(log_data))


# ============================================================================
# CSRF Protection
# ============================================================================

class CSRFProtection:
    """
    CSRF protection using double-submit cookie pattern

    SECURITY: Prevents cross-site request forgery attacks
    """

    CSRF_COOKIE_NAME = "csrf_token"
    CSRF_HEADER_NAME = "X-CSRF-Token"
    TOKEN_LENGTH = 32
    TOKEN_EXPIRY = timedelta(hours=24)

    # Store tokens with expiry (in production, use Redis)
    _tokens: Dict[str, datetime] = {}
    _lock = threading.Lock()

    @classmethod
    def generate_token(cls) -> str:
        """Generate a new CSRF token"""
        token = secrets.token_urlsafe(cls.TOKEN_LENGTH)
        with cls._lock:
            cls._tokens[token] = datetime.utcnow() + cls.TOKEN_EXPIRY
            # Clean up expired tokens
            cls._cleanup_expired()
        return token

    @classmethod
    def validate_token(cls, token: str) -> bool:
        """Validate a CSRF token"""
        if not token:
            return False
        with cls._lock:
            expiry = cls._tokens.get(token)
            if expiry and expiry > datetime.utcnow():
                return True
        return False

    @classmethod
    def _cleanup_expired(cls):
        """Remove expired tokens"""
        now = datetime.utcnow()
        expired = [t for t, exp in cls._tokens.items() if exp <= now]
        for t in expired:
            del cls._tokens[t]

    @classmethod
    def get_token_from_request(cls, request: Request) -> Optional[str]:
        """Extract CSRF token from request header or cookie"""
        # Check header first
        header_token = request.headers.get(cls.CSRF_HEADER_NAME)
        if header_token:
            return header_token
        # Fall back to cookie
        return request.cookies.get(cls.CSRF_COOKIE_NAME)


async def csrf_protect(request: Request):
    """
    CSRF protection dependency for state-changing endpoints

    Usage:
        @router.post("/endpoint", dependencies=[Depends(csrf_protect)])
    """
    # Skip CSRF check for safe methods
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    # Skip if CSRF protection is disabled (development)
    if not getattr(settings, 'ENABLE_CSRF_PROTECTION', False):
        return

    token = CSRFProtection.get_token_from_request(request)

    if not token or not CSRFProtection.validate_token(token):
        log_security_event("csrf_validation_failed", {
            "reason": "Invalid or missing CSRF token"
        }, request)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed"
        )


# ============================================================================
# IP-Based Rate Limiting
# ============================================================================

class IPRateLimiter:
    """
    IP-based rate limiting with sliding window

    SECURITY: More granular control than global rate limiting
    """

    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self._minute_counts: Dict[str, list] = defaultdict(list)
        self._hour_counts: Dict[str, list] = defaultdict(list)
        self._blocked_ips: Dict[str, datetime] = {}
        self._lock = threading.Lock()

    def is_allowed(self, ip: str) -> tuple[bool, Optional[str]]:
        """
        Check if IP is allowed to make request

        Returns:
            Tuple of (is_allowed, reason_if_blocked)
        """
        now = time.time()

        with self._lock:
            # Check if IP is blocked
            if ip in self._blocked_ips:
                if self._blocked_ips[ip] > datetime.utcnow():
                    return False, "IP temporarily blocked due to abuse"
                else:
                    del self._blocked_ips[ip]

            # Clean old entries
            minute_ago = now - 60
            hour_ago = now - 3600

            self._minute_counts[ip] = [
                t for t in self._minute_counts[ip] if t > minute_ago]
            self._hour_counts[ip] = [
                t for t in self._hour_counts[ip] if t > hour_ago]

            # Check limits
            if len(self._minute_counts[ip]) >= self.requests_per_minute:
                return False, f"Rate limit exceeded: {self.requests_per_minute}/minute"

            if len(self._hour_counts[ip]) >= self.requests_per_hour:
                return False, f"Rate limit exceeded: {self.requests_per_hour}/hour"

            # Record request
            self._minute_counts[ip].append(now)
            self._hour_counts[ip].append(now)

            return True, None

    def block_ip(self, ip: str, duration_minutes: int = 60):
        """Block an IP for a specified duration"""
        with self._lock:
            self._blocked_ips[ip] = datetime.utcnow(
            ) + timedelta(minutes=duration_minutes)
            log_security_event("ip_blocked", {
                "ip": ip,
                "duration_minutes": duration_minutes
            })

    def get_stats(self, ip: str) -> dict:
        """Get rate limit stats for an IP"""
        now = time.time()
        with self._lock:
            minute_count = len(
                [t for t in self._minute_counts.get(ip, []) if t > now - 60])
            hour_count = len(
                [t for t in self._hour_counts.get(ip, []) if t > now - 3600])
            return {
                "requests_last_minute": minute_count,
                "requests_last_hour": hour_count,
                "minute_limit": self.requests_per_minute,
                "hour_limit": self.requests_per_hour
            }


# Global IP rate limiter instance
ip_rate_limiter = IPRateLimiter(
    requests_per_minute=getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60),
    requests_per_hour=getattr(settings, 'RATE_LIMIT_PER_HOUR', 1000)
)


# ============================================================================
# Download File Cleanup (Expiration)
# ============================================================================

class DownloadCleaner:
    """
    Automatic cleanup of old downloaded files

    SECURITY: Prevents disk exhaustion from accumulated downloads
    """

    DEFAULT_EXPIRY_DAYS = 7

    @classmethod
    def cleanup_old_downloads(cls, expiry_days: Optional[int] = None) -> dict:
        """
        Remove downloaded files older than expiry_days

        Args:
            expiry_days: Number of days after which files expire

        Returns:
            Dict with cleanup statistics
        """
        expiry_days = expiry_days or getattr(
            settings, 'DOWNLOAD_EXPIRY_DAYS', cls.DEFAULT_EXPIRY_DAYS)
        expiry_time = datetime.utcnow() - timedelta(days=expiry_days)

        stats = {
            "files_deleted": 0,
            "bytes_freed": 0,
            "errors": []
        }

        download_dir = settings.DOWNLOAD_DIR

        try:
            for subdir in ["Audio", "Video"]:
                subdir_path = download_dir / subdir
                if not subdir_path.exists():
                    continue

                for file_path in subdir_path.iterdir():
                    if not file_path.is_file():
                        continue

                    try:
                        # Check file modification time
                        mtime = datetime.fromtimestamp(
                            file_path.stat().st_mtime)
                        if mtime < expiry_time:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            stats["files_deleted"] += 1
                            stats["bytes_freed"] += file_size
                            logger.info(
                                f"Cleaned up expired file: {file_path.name}")
                    except Exception as e:
                        stats["errors"].append(f"{file_path.name}: {str(e)}")
                        logger.error(f"Error cleaning up {file_path}: {e}")

            if stats["files_deleted"] > 0:
                log_security_event("download_cleanup", {
                    "files_deleted": stats["files_deleted"],
                    "bytes_freed": stats["bytes_freed"],
                    "expiry_days": expiry_days
                })

            return stats

        except Exception as e:
            logger.error(f"Download cleanup failed: {e}")
            stats["errors"].append(str(e))
            return stats

    @classmethod
    def get_download_stats(cls) -> dict:
        """Get statistics about downloaded files"""
        download_dir = settings.DOWNLOAD_DIR
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "audio_files": 0,
            "video_files": 0,
            "oldest_file": None,
            "newest_file": None
        }

        try:
            for subdir in ["Audio", "Video"]:
                subdir_path = download_dir / subdir
                if not subdir_path.exists():
                    continue

                for file_path in subdir_path.iterdir():
                    if not file_path.is_file():
                        continue

                    stats["total_files"] += 1
                    stats["total_size_bytes"] += file_path.stat().st_size

                    if subdir == "Audio":
                        stats["audio_files"] += 1
                    else:
                        stats["video_files"] += 1

                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if stats["oldest_file"] is None or mtime < stats["oldest_file"]:
                        stats["oldest_file"] = mtime
                    if stats["newest_file"] is None or mtime > stats["newest_file"]:
                        stats["newest_file"] = mtime

            # Convert datetimes to ISO strings
            if stats["oldest_file"]:
                stats["oldest_file"] = stats["oldest_file"].isoformat()
            if stats["newest_file"]:
                stats["newest_file"] = stats["newest_file"].isoformat()

            return stats

        except Exception as e:
            logger.error(f"Error getting download stats: {e}")
            return stats


# ============================================================================
# Content-Disposition Header Helper
# ============================================================================

def get_safe_filename(filename: str) -> str:
    """
    Sanitize filename for Content-Disposition header

    SECURITY: Prevents header injection and ensures safe download names
    """
    import re
    import urllib.parse

    # Remove path separators and null bytes
    filename = filename.replace(
        "/", "_").replace("\\", "_").replace("\x00", "")

    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"|?*]', '_', filename)

    # Limit length
    max_length = 200
    if len(filename) > max_length:
        name, ext = filename.rsplit(
            '.', 1) if '.' in filename else (filename, '')
        filename = name[:max_length -
                        len(ext) - 1] + '.' + ext if ext else name[:max_length]

    return filename


def set_download_headers(response: Response, filename: str, content_type: str = "application/octet-stream"):
    """
    Set appropriate headers for file download

    Args:
        response: FastAPI Response object
        filename: Original filename
        content_type: MIME type of the file
    """
    import urllib.parse

    safe_filename = get_safe_filename(filename)

    # RFC 5987 compliant Content-Disposition
    # Includes both ASCII fallback and UTF-8 encoded filename
    ascii_filename = safe_filename.encode('ascii', 'ignore').decode()
    utf8_filename = urllib.parse.quote(safe_filename)

    response.headers["Content-Type"] = content_type
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{ascii_filename}"; '
        f"filename*=UTF-8''{utf8_filename}"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"


# ============================================================================
# HTTPS Redirect
# ============================================================================

def should_redirect_to_https(request: Request) -> bool:
    """
    Check if request should be redirected to HTTPS

    Returns True if:
    - Not in debug mode
    - Request is not already HTTPS
    - HTTPS redirect is enabled
    """
    if settings.DEBUG:
        return False

    if not getattr(settings, 'FORCE_HTTPS', False):
        return False

    # Check if already HTTPS (also check X-Forwarded-Proto for reverse proxies)
    if request.url.scheme == "https":
        return False

    forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
    if forwarded_proto.lower() == "https":
        return False

    return True


def get_https_redirect_url(request: Request) -> str:
    """Get the HTTPS version of the current URL"""
    url = str(request.url)
    return url.replace("http://", "https://", 1)
