"""
Custom Exceptions
Define application-specific exceptions for better error handling
"""


class YouTubeDownloaderException(Exception):
    """Base exception for all application errors"""
    pass


class InvalidURLError(YouTubeDownloaderException):
    """Raised when a YouTube URL is invalid"""
    pass


class DownloadError(YouTubeDownloaderException):
    """Raised when a download fails"""
    pass


class QueueFullError(YouTubeDownloaderException):
    """Raised when the download queue is full"""
    pass


class DownloadNotFoundError(YouTubeDownloaderException):
    """Raised when a download ID is not found"""
    pass


class FFmpegError(YouTubeDownloaderException):
    """Raised when FFmpeg processing fails"""
    pass


class YTDLPError(YouTubeDownloaderException):
    """Raised when yt-dlp encounters an error"""
    pass


class ServiceUnavailableError(YouTubeDownloaderException):
    """Raised when an external service (yt-dlp, ffmpeg) is unavailable"""
    pass
