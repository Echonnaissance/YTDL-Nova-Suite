"""
YT-DLP Service
Wrapper for yt-dlp executable with progress tracking and error handling
"""
import subprocess
import shutil
import logging
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
        # Detect available JS runtime for yt-dlp (node preferred)
        self.js_runtime_args = self._detect_js_runtime_args()

        # Module logger
        self.logger = logging.getLogger(__name__)

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
        Check if URL is a valid http/https URL.
        yt-dlp supports 1000+ sites, so we just validate the URL format
        and let yt-dlp handle site-specific validation.
        """
        return url.lower().startswith(("http://", "https://"))

    def _add_cookie_args(self, cmd: list) -> None:
        """
        Add cookie arguments to yt-dlp command.
        Prefers cookies file over browser cookies to avoid DPAPI issues on Windows.
        """
        # Prefer cookies file (avoids Windows DPAPI decryption issues)
        import os
        if settings.COOKIES_FILE:
            if os.path.exists(settings.COOKIES_FILE):
                cmd.extend(["--cookies", settings.COOKIES_FILE])
                return

        # If COOKIE_BROWSER is set, try to export cookies to a file using
        # browser_cookie3 to avoid DPAPI decryption issues on Windows.
        if settings.COOKIE_BROWSER:
            try:
                exported = self._export_cookies_via_browser(
                    settings.COOKIE_BROWSER)
                if exported:
                    cmd.extend(["--cookies", exported])
                    return
            except Exception:
                # Fall back to yt-dlp native browser cookie reader (may trigger DPAPI)
                pass

            # Fall back: use yt-dlp's --cookies-from-browser (may fail on some systems)
            cmd.extend(["--cookies-from-browser", settings.COOKIE_BROWSER])

    def _export_cookies_via_browser(self, browser_name: Optional[str]) -> Optional[str]:
        """
        Try to export cookies from the user's browser to a Netscape-format file.
        Returns the path to the exported cookies file, or None on failure.
        """
        try:
            import importlib
            browser_cookie3 = importlib.import_module("browser_cookie3")
        except Exception:
            return None

        # Map common names to browser_cookie3 helpers
        helpers = {
            "chrome": getattr(browser_cookie3, "chrome", None),
            "chromium": getattr(browser_cookie3, "chromium", None),
            "edge": getattr(browser_cookie3, "edge", None),
            "brave": getattr(browser_cookie3, "brave", None),
            "opera": getattr(browser_cookie3, "opera", None),
            "firefox": getattr(browser_cookie3, "firefox", None),
            "safari": getattr(browser_cookie3, "safari", None),
        }

        helper = helpers.get(browser_name.lower()) if browser_name else None
        if helper is None:
            # If no specific helper, try generic loader
            try:
                cj = browser_cookie3.load()
            except Exception:
                return None
        else:
            try:
                cj = helper()
            except Exception:
                try:
                    cj = browser_cookie3.load()
                except Exception:
                    return None

        # Write Netscape-format cookies file
        try:
            output_path = Path(settings.BASE_DIR) / "backend" / "cookies.txt"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                f.write("# Netscape HTTP Cookie File\n")
                for cookie in cj:
                    domain = cookie.domain
                    flag = "TRUE" if getattr(
                        cookie, "domain_specified", False) else "FALSE"
                    path = cookie.path
                    secure = "TRUE" if getattr(
                        cookie, "secure", False) else "FALSE"
                    expires_val = getattr(cookie, "expires", None)
                    expires = str(int(expires_val)
                                  ) if expires_val is not None else "0"
                    name = cookie.name
                    value = cookie.value
                    f.write(
                        f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

            return str(output_path)
        except Exception:
            return None

    def _detect_js_runtime_args(self) -> Optional[list]:
        """Detect node or deno in PATH and return yt-dlp js runtime args."""
        try:
            node_path = shutil.which("node")
            if node_path:
                return ["--js-runtimes", "node"]
            deno_path = shutil.which("deno")
            if deno_path:
                return ["--js-runtimes", "deno"]
        except Exception:
            pass
        return None

    def _add_js_runtime_args(self, cmd: list) -> None:
        """Append detected js runtime args to command if available."""
        if self.js_runtime_args:
            # insert before the URL (assume URL is last positional arg)
            # but simply extend early so flags appear before URL
            # many commands append URL at the end, so safe to extend now
            cmd.extend(self.js_runtime_args)

    def _get_video_info_sync(self, url: str) -> Dict[str, Any]:
        """Synchronous helper for get_video_info"""
        cmd = [
            self.ytdlp_path,
            "--dump-json",
            "--no-playlist",
            "--socket-timeout", "60",  # Increased from default for slow networks
        ]

        # Add cookie support (needed for Twitter/X, Instagram, etc.)
        self._add_cookie_args(cmd)

        # Prefer a JS runtime when available to avoid SABR streaming issues
        self._add_js_runtime_args(cmd)

        cmd.append(url)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # Increased from 30s to allow metadata extraction
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
            raise InvalidURLError(
                f"Unsupported URL: {url}. Please provide a valid URL from a supported platform.")

        try:
            # Use to_thread to avoid blocking (Windows-compatible)
            return await asyncio.to_thread(self._get_video_info_sync, url)
        except subprocess.TimeoutExpired:
            raise YTDLPError("Video info extraction timed out")
        except subprocess.CalledProcessError as e:
            msg = f"Failed to extract video info: {e.stderr}"
            # Detect DPAPI/browser cookie errors and attempt automated export+retry
            if "DPAPI" in e.stderr or "Could not copy Chrome cookie database" in e.stderr:
                exported = None
                try:
                    exported = self._export_cookies_via_browser(
                        settings.COOKIE_BROWSER)
                    if exported:
                        settings.COOKIES_FILE = exported
                        return await asyncio.to_thread(self._get_video_info_sync, url)
                except Exception:
                    pass
            raise YTDLPError(msg)
        except json.JSONDecodeError:
            raise YTDLPError("Failed to parse video information")

    def _get_playlist_info_sync(self, url: str) -> Dict[str, Any]:
        """Synchronous helper for get_playlist_info"""
        cmd = [
            self.ytdlp_path,
            "--flat-playlist",
            "--dump-json",
        ]

        # Add cookie support (needed for Twitter/X, Instagram, etc.)
        self._add_cookie_args(cmd)
        # Prefer a JS runtime when available to avoid SABR streaming issues
        self._add_js_runtime_args(cmd)

        cmd.append(url)

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
            raise InvalidURLError(
                f"Unsupported URL: {url}. Please provide a valid URL from a supported platform.")

        try:
            return await asyncio.to_thread(self._get_playlist_info_sync, url)
        except subprocess.TimeoutExpired:
            raise YTDLPError("Playlist info extraction timed out")
        except subprocess.CalledProcessError as e:
            msg = f"Failed to extract playlist info: {e.stderr}"
            if "DPAPI" in e.stderr or "Could not copy Chrome cookie database" in e.stderr:
                try:
                    exported = self._export_cookies_via_browser(
                        settings.COOKIE_BROWSER)
                    if exported:
                        settings.COOKIES_FILE = exported
                        return await asyncio.to_thread(self._get_playlist_info_sync, url)
                except Exception:
                    pass
            raise YTDLPError(msg)
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
            "--socket-timeout", "60",  # Prevent socket timeouts on slow/large downloads
            "--retries", "3",  # Retry failed chunks
            "--fragment-retries", "10",  # Retry HLS/DASH fragments
        ]

        # Add cookie support (needed for Twitter/X, Instagram, etc.)
        self._add_cookie_args(cmd)

        # Prefer a JS runtime when available to avoid SABR streaming issues
        self._add_js_runtime_args(cmd)

        cmd.append(url)

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
            "-f", "bestvideo+bestaudio/best",
            "--extract-audio",
            "--audio-format", format,
            "--no-playlist",
            "--socket-timeout", "60",  # Prevent socket timeouts on slow/large downloads
            "--retries", "3",  # Retry failed chunks
            "--fragment-retries", "10",  # Retry HLS/DASH fragments
        ]

        # Add cookie support (needed for Twitter/X, Instagram, etc.)
        self._add_cookie_args(cmd)

        # Prefer a JS runtime when available to avoid SABR streaming issues
        self._add_js_runtime_args(cmd)

        if embed_thumbnail:
            cmd.append("--embed-thumbnail")

        cmd.append(url)

        return await self._execute_download(cmd, progress_callback)

    def _execute_download_sync(self, cmd: list, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> str:
        """Synchronous helper for _execute_download with retry/backoff for 403 errors"""
        import time

        # Keep an immutable base copy of the command so retries start fresh
        base_cmd = list(cmd)
        max_retries = 3
        base_delay = 2  # seconds

        for attempt in range(max_retries):
            # Rebuild cmd for each attempt
            cmd = list(base_cmd)

            # On subsequent attempts, try adding UA to mimic a browser
            if attempt >= 1 and '--user-agent' not in cmd:
                try:
                    cmd.insert(-1, '--user-agent')
                    cmd.insert(-1, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36')
                except Exception:
                    pass

            # On later attempts, disable part files and resume to avoid ranged 403s
            if attempt >= 2 and '--no-part' not in cmd and getattr(settings, 'YTDLP_NO_PART_FALLBACK', False):
                cmd.extend(['--no-part', '--no-continue'])

            # Log the final command for debugging (sanitized). Respect YTDLP_DEBUG
            try:
                if getattr(settings, 'YTDLP_DEBUG', False):
                    # Make this more visible when debugging is enabled
                    self.logger.info(
                        "Running yt-dlp command: %s", " ".join(cmd))
                else:
                    self.logger.debug(
                        "Running yt-dlp command: %s", " ".join(cmd))
            except Exception:
                pass

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
                    raise YTDLPError(
                        f"Download timed out after {timeout_seconds} seconds")

            return_code = process.poll()
            if return_code == 0:
                # Success, extract filename
                downloaded_file = None

                # Debug: print last 10 lines of output to see what we got
                print("[*] yt-dlp output (last 10 lines):")
                for line in output_lines[-10:]:
                    print(f"    {line}")

                for line in output_lines:
                    # Try various patterns to extract the file path
                    if "Destination:" in line:
                        match = re.search(r'Destination:\s+(.+)$', line)
                        if match:
                            downloaded_file = match.group(1).strip()
                            print(
                                f"[*] Matched 'Destination:' pattern: {downloaded_file}")
                    elif "Merging formats into" in line:
                        match = re.search(r'into\s+"(.+?)"', line)
                        if match:
                            downloaded_file = match.group(1).strip()
                            print(
                                f"[*] Matched 'Merging' pattern: {downloaded_file}")
                    elif "has already been downloaded" in line:
                        match = re.search(
                            r'\[download\]\s+(.+?)\s+has already been downloaded', line)
                        if match:
                            downloaded_file = match.group(1).strip()
                            print(
                                f"[*] Matched 'already downloaded' pattern: {downloaded_file}")
                    # Add more comprehensive patterns
                    elif "[download] 100%" in line and not downloaded_file:
                        # Pattern: [download] 100% of 123.45MiB in 00:12
                        # Look for the filename in subsequent lines or use output template
                        pass
                    elif "[Merger]" in line and "into" in line.lower():
                        # Pattern: [Merger] Merging formats into "filename.ext"
                        match = re.search(r'into\s+"([^"]+)"', line)
                        if match:
                            downloaded_file = match.group(1).strip()
                            print(
                                f"[*] Matched '[Merger]' pattern: {downloaded_file}")

                if downloaded_file and os.path.exists(downloaded_file):
                    print(f"[+] File found via regex: {downloaded_file}")
                    return downloaded_file
                elif downloaded_file:
                    print(
                        f"[!] Regex matched '{downloaded_file}' but exact path doesn't exist")
                    # Try finding a similar file (handle Unicode/character variations)
                    try:
                        from pathlib import Path
                        import glob

                        parent_dir = str(Path(downloaded_file).parent)
                        # filename without extension
                        base_name = Path(downloaded_file).stem
                        # .mp4, .m4a, etc
                        extension = Path(downloaded_file).suffix

                        print(
                            f"[*] Searching for similar files: {base_name}*{extension}")

                        # Search for files with similar names
                        if os.path.exists(parent_dir):
                            for file in os.listdir(parent_dir):
                                file_path = os.path.join(parent_dir, file)
                                if os.path.isfile(file_path):
                                    # Check if filename is similar (case-insensitive, handles character variations)
                                    file_stem = Path(file).stem
                                    file_ext = Path(file).suffix

                                    # Match extension and similar base name (accounting for Unicode variations)
                                    if file_ext.lower() == extension.lower():
                                        # Normalize both names for comparison (remove special chars, lowercase)
                                        normalized_expected = ''.join(
                                            c.lower() for c in base_name if c.isalnum() or c.isspace())
                                        normalized_actual = ''.join(
                                            c.lower() for c in file_stem if c.isalnum() or c.isspace())

                                        if normalized_expected == normalized_actual:
                                            print(
                                                f"[+] Found matching file with character variations: {file}")
                                            return file_path
                    except Exception as e:
                        print(f"[!] Similar file search failed: {e}")

                # Fallback: Find the most recently created file in the download directory
                print("[*] Primary file path detection failed, trying fallback...")
                try:
                    import glob
                    from pathlib import Path

                    # Determine target directory based on command
                    target_dir = None
                    for i, arg in enumerate(cmd):
                        if arg == '-o' and i + 1 < len(cmd):
                            # Extract directory from output template
                            output_template = cmd[i + 1]
                            target_dir = str(Path(output_template).parent)
                            break

                    print(f"[*] Looking for recent files in: {target_dir}")

                    if target_dir and os.path.exists(target_dir):
                        # Find most recent file (modified in last 120 seconds)
                        current_time = time.time()
                        recent_files = []
                        for file_path in glob.glob(os.path.join(target_dir, "*")):
                            if os.path.isfile(file_path):
                                # Use modification time (more reliable than creation)
                                file_age = current_time - \
                                    os.path.getmtime(file_path)
                                if file_age < 120:  # Modified within last 120 seconds
                                    recent_files.append((file_age, file_path))
                                    print(
                                        f"[*] Found recent file ({file_age:.1f}s ago): {os.path.basename(file_path)}")

                        if recent_files:
                            # Return the newest file
                            recent_files.sort()
                            most_recent = recent_files[0][1]
                            print(
                                f"[+] Detected downloaded file via fallback: {most_recent}")
                            return most_recent
                        else:
                            print("[!] No recent files found in target directory")
                    else:
                        print(
                            f"[!] Target directory not found or doesn't exist: {target_dir}")
                except Exception as e:
                    import traceback
                    print(f"[!] Fallback file detection failed: {e}")
                    traceback.print_exc()

                print("[!] All file detection methods failed")
                return "Download complete (file path could not be determined)"

            # Non-zero return code: check recent output for 403/Forbidden
            error_output = '\n'.join(output_lines[-20:])
            if ('403' in error_output or 'Forbidden' in error_output) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(
                    f"[!] Retry {attempt + 1} in {delay}s due to 403/Forbidden response...")
                time.sleep(delay)
                # Add a browser-like user-agent on retries if not already present
                if '--user-agent' not in base_cmd:
                    # Insert before the URL argument (assume URL is last arg)
                    try:
                        # Place UA right before the final URL argument (insert flag first)
                        base_cmd.insert(-1, '--user-agent')
                        base_cmd.insert(
                            -1, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36')
                    except Exception:
                        pass
                continue

            # If not a 403 or retries exhausted, raise error
            raise YTDLPError(f"Download failed: {error_output}")

        # Should not reach here
        raise YTDLPError("Max retries exceeded for download")

    async def _execute_download(
        self,
        cmd: list,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> str:
        """Execute download command with progress tracking (async, Windows-compatible)"""
        try:
            return await asyncio.to_thread(self._execute_download_sync, cmd, progress_callback)
        except Exception as e:
            err_str = str(e)
            # On DPAPI/browser cookie errors, attempt export and retry once
            if "DPAPI" in err_str or "Could not copy Chrome cookie database" in err_str:
                try:
                    exported = self._export_cookies_via_browser(
                        settings.COOKIE_BROWSER)
                    if exported:
                        settings.COOKIES_FILE = exported
                        # rebuild cmd to prefer --cookies if necessary
                        if "--cookies-from-browser" in cmd:
                            # remove --cookies-from-browser and its arg
                            try:
                                idx = cmd.index("--cookies-from-browser")
                                # remove flag and following browser name
                                del cmd[idx:idx+2]
                            except ValueError:
                                pass
                        if "--cookies" not in cmd:
                            cmd = [*cmd, "--cookies", exported]
                        return await asyncio.to_thread(self._execute_download_sync, cmd, progress_callback)
                except Exception:
                    pass
            raise YTDLPError(f"Download execution failed: {err_str}")

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
            print(
                f"[!] Unexpected error checking yt-dlp availability: {str(e)}")
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
