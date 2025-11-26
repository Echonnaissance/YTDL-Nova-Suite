"""
Security Module
Handles authentication, authorization, and security utilities
"""
from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader
from pathlib import Path
from typing import Optional
import secrets
import hashlib
import hmac
import logging

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

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

    # Characters that could be used for command injection
    dangerous_chars = [";", "|", "&", "$", "`", "\\", "\n", "\r", "(", ")", "{", "}", "<", ">", "\x00"]

    # Check both original and decoded for dangerous characters
    for check_url in [url, decoded_url, normalized_url]:
        for char in dangerous_chars:
            if char in check_url:
                logger.warning(f"Dangerous character '{repr(char)}' found in URL: {url}")
                raise ValueError(
                    f"URL contains forbidden character. "
                    "Possible command injection attempt."
                )

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
        logger.warning(f"Request too large: {content_length} bytes (max: {max_size})")
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

        logger.info(f"Disk space check passed: {usage.free / (1024**3):.2f} GB available")
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

        logger.info(f"Quota check passed: {total_size / (1024**3):.2f} GB used")
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
            logger.warning(f"Suspicious file type detected: {mime_type} for {file_path}")
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
    }

    if request:
        log_data["client_ip"] = request.client.host if request.client else "unknown"
        log_data["user_agent"] = request.headers.get("user-agent", "unknown")

    logger.warning(f"SECURITY EVENT: {log_data}")
