"""
YT-DLP Service
Wrapper for yt-dlp executable with progress tracking and error handling
"""
import subprocess
import asyncio
import json
import re
import os
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from app.config import settings
from app.core.exceptions import (
    YTDLPError,
    InvalidURLError,
    ServiceUnavailableError
)


class YTDLPService:
    """
    Service for interacting with yt-dlp
    Handles video info extraction, download, and progress tracking
    """

    def __init__(self):
        self.ytdlp_path = str(settings.YTDLP_PATH)
        self.ffmpeg_path = str(settings.FFMPEG_PATH)
        self.download_dir = str(settings.DOWNLOAD_DIR)
        self._ytdlp_available = os.path.exists(self.ytdlp_path)
        self._ffmpeg_available = os.path.exists(self.ffmpeg_path)

        # Log warning if tools are missing but don't crash
        if not self._ytdlp_available:
            print(f"[!] WARNING: yt-dlp not found at {self.ytdlp_path}")
        if not self._ffmpeg_available:
            print(f"[!] WARNING: ffmpeg not found at {self.ffmpeg_path}")

    def _check_ytdlp_available(self):
        """Check if yt-dlp is available, raise error if not"""
        if not self._ytdlp_available:
            raise ServiceUnavailableError(
                f"yt-dlp is not available. Please ensure yt-dlp.exe exists at {self.ytdlp_path}"
            )

    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL is a valid YouTube URL
        """
        valid_domains = ["youtube.com", "youtu.be", "youtube-nocookie.com"]
        return any(domain in url.lower() for domain in valid_domains)

    def _get_video_info_sync(self, url: str) -> Dict[str, Any]:
        """Synchronous helper for get_video_info"""
        cmd = [
            self.ytdlp_path,
            "--dump-json",
            "--no-playlist",
            url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        info = json.loads(result.stdout)
        return {
            "url": url,
            "title": info.get("title", "Unknown"),
            "thumbnail_url": info.get("thumbnail"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader"),
            "view_count": info.get("view_count"),
            "is_playlist": False
        }

    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Extract video information without downloading
        Returns metadata like title, duration, thumbnail, etc.
        """
        self._check_ytdlp_available()

        if not self.is_valid_url(url):
            raise InvalidURLError(f"Invalid YouTube URL: {url}")

        try:
            # Use to_thread to avoid blocking (Windows-compatible)
            return await asyncio.to_thread(self._get_video_info_sync, url)
        except subprocess.TimeoutExpired:
            raise YTDLPError("Video info extraction timed out")
        except subprocess.CalledProcessError as e:
            raise YTDLPError(f"Failed to extract video info: {e.stderr}")
        except json.JSONDecodeError:
            raise YTDLPError("Failed to parse video information")

    def _get_playlist_info_sync(self, url: str) -> Dict[str, Any]:
        """Synchronous helper for get_playlist_info"""
        cmd = [
            self.ytdlp_path,
            "--flat-playlist",
            "--dump-json",
            url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            check=True
        )

        videos = []
        for line in result.stdout.strip().split('\n'):
            if line:
                video_data = json.loads(line)
                videos.append({
                    "id": video_data.get("id", ""),
                    "title": video_data.get("title", "Unknown"),
                    "url": video_data.get("url", ""),
                    "thumbnail_url": video_data.get("thumbnail"),
                    "duration": video_data.get("duration", 0)
                })

        return {
            "url": url,
            "title": videos[0].get("title", "Playlist") if videos else "Playlist",
            "video_count": len(videos),
            "videos": videos
        }

    async def get_playlist_info(self, url: str) -> Dict[str, Any]:
        """Extract playlist information"""
        if not self.is_valid_url(url):
            raise InvalidURLError(f"Invalid YouTube URL: {url}")

        try:
            return await asyncio.to_thread(self._get_playlist_info_sync, url)
        except subprocess.TimeoutExpired:
            raise YTDLPError("Playlist info extraction timed out")
        except subprocess.CalledProcessError as e:
            raise YTDLPError(f"Failed to extract playlist info: {e.stderr}")
        except json.JSONDecodeError as e:
            raise YTDLPError(f"Failed to parse playlist information: {str(e)}")

    async def download_video(
        self,
        url: str,
        quality: str = "best",
        format: str = "mp4",
        output_template: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        custom_download_dir: Optional[str] = None
    ) -> str:
        """
        Download video with specified quality
        Returns path to downloaded file
        """
        self._check_ytdlp_available()

        if output_template is None:
            # Use custom download directory if provided, otherwise use default
            base_dir = custom_download_dir if custom_download_dir else self.download_dir
            # Create Video subdirectory if it doesn't exist
            video_dir = os.path.join(base_dir, "Video")
            os.makedirs(video_dir, exist_ok=True)
            output_template = os.path.join(video_dir, "%(title)s.%(ext)s")

        cmd = [
            self.ytdlp_path,
            "-o", output_template,
            "--ffmpeg-location", self.ffmpeg_path,
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", format,
            "--no-playlist",
            url
        ]

        return await self._execute_download(cmd, progress_callback)

    async def download_audio(
        self,
        url: str,
        format: str = "m4a",
        embed_thumbnail: bool = True,
        output_template: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        custom_download_dir: Optional[str] = None
    ) -> str:
        """
        Download audio only with specified format
        Returns path to downloaded file
        """
        self._check_ytdlp_available()

        if output_template is None:
            # Use custom download directory if provided, otherwise use default
            base_dir = custom_download_dir if custom_download_dir else self.download_dir
            # Create Audio subdirectory if it doesn't exist
            audio_dir = os.path.join(base_dir, "Audio")
            os.makedirs(audio_dir, exist_ok=True)
            output_template = os.path.join(audio_dir, "%(title)s.%(ext)s")

        cmd = [
            self.ytdlp_path,
            "-o", output_template,
            "--ffmpeg-location", self.ffmpeg_path,
            "-f", "bestaudio",
            "--extract-audio",
            "--audio-format", format,
            "--no-playlist",
        ]

        if embed_thumbnail:
            cmd.append("--embed-thumbnail")

        cmd.append(url)

        return await self._execute_download(cmd, progress_callback)

    def _execute_download_sync(self, cmd: list, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> str:
        """Synchronous helper for _execute_download"""
        import time

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            universal_newlines=True,
            bufsize=1
        )

        # SECURITY: Timeout for long-running downloads (30 minutes max)
        timeout_seconds = 1800  # 30 minutes
        start_time = time.time()

        output_lines = []
        while True:
            if process.stdout is None:
                break

            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break

            if line:
                output_lines.append(line.strip())
                if progress_callback:
                    progress_info = self._parse_progress(line)
                    if progress_info:
                        progress_callback(progress_info)

            # SECURITY: Check for timeout
            if time.time() - start_time > timeout_seconds:
                process.kill()
                raise YTDLPError(f"Download timed out after {timeout_seconds} seconds")

        return_code = process.poll()
        if return_code != 0:
            error_output = '\n'.join(output_lines[-10:])
            raise YTDLPError(f"Download failed: {error_output}")

        # Extract filename from output
        downloaded_file = None
        for line in output_lines:
            # Try various patterns to extract the file path
            if "Destination:" in line:
                match = re.search(r'Destination:\s+(.+)$', line)
                if match:
                    downloaded_file = match.group(1).strip()
            elif "Merging formats into" in line:
                match = re.search(r'into\s+"(.+?)"', line)
                if match:
                    downloaded_file = match.group(1).strip()
            elif "has already been downloaded" in line:
                match = re.search(r'\[download\]\s+(.+?)\s+has already been downloaded', line)
                if match:
                    downloaded_file = match.group(1).strip()

        if downloaded_file and os.path.exists(downloaded_file):
            return downloaded_file

        return "Download complete (file path could not be determined)"

    async def _execute_download(
        self,
        cmd: list,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> str:
        """Execute download command with progress tracking (async, Windows-compatible)"""
        try:
            return await asyncio.to_thread(self._execute_download_sync, cmd, progress_callback)
        except Exception as e:
            raise YTDLPError(f"Download execution failed: {str(e)}")

    def _parse_progress(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse progress information from yt-dlp output
        """
        progress = {}

        # Parse percentage
        percent_match = re.search(r'(\d+\.?\d*)%', line)
        if percent_match:
            progress["progress"] = float(percent_match.group(1))

        # Parse speed
        speed_match = re.search(r'at ([\d.]+\w+/s)', line)
        if speed_match:
            progress["speed"] = speed_match.group(1)

        # Parse ETA
        eta_match = re.search(r'ETA (\d+:\d+)', line)
        if eta_match:
            progress["eta"] = eta_match.group(1)

        # Check for status messages
        if "Downloading" in line:
            progress["status"] = "downloading"
        elif "Merging formats" in line:
            progress["status"] = "processing"
        elif "Embedding thumbnail" in line:
            progress["status"] = "processing"

        return progress if progress else None

    def _check_availability_sync(self) -> bool:
        """Synchronous helper for check_availability"""
        try:
            result = subprocess.run(
                [self.ytdlp_path, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (OSError, FileNotFoundError, subprocess.TimeoutExpired):
            return False

    async def check_availability(self) -> bool:
        """Check if yt-dlp is available and working"""
        try:
            return await asyncio.to_thread(self._check_availability_sync)
        except Exception as e:
            print(f"[!] Unexpected error checking yt-dlp availability: {str(e)}")
            return False

    def _get_version_sync(self) -> str:
        """Synchronous helper for get_version"""
        try:
            result = subprocess.run(
                [self.ytdlp_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "Unknown"
        except subprocess.TimeoutExpired:
            return "Unknown (timeout)"
        except (OSError, FileNotFoundError):
            return "Unknown (not found)"

    async def get_version(self) -> str:
        """Get yt-dlp version"""
        try:
            return await asyncio.to_thread(self._get_version_sync)
        except Exception as e:
            print(f"[!] Unexpected error getting yt-dlp version: {str(e)}")
            return "Unknown (error)"
