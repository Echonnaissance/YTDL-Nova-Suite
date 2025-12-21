"""
Metadata Service
Automatically generates thumbnails and extracts metadata for completed downloads
"""
import subprocess
import re
import asyncio
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models.database import Download, DownloadType
from app.config import settings


class MetadataService:
    """Service for extracting metadata and generating thumbnails from media files"""

    def __init__(self):
        self.ffmpeg_path = self._find_ffmpeg()
        self.ffprobe_path = self._find_ffprobe()

    def _find_ffmpeg(self) -> str:
        """Locate ffmpeg executable"""
        # Use configured FFMPEG_PATH from settings
        if settings.FFMPEG_PATH.exists():
            return str(settings.FFMPEG_PATH)
        return "ffmpeg"  # fallback to PATH

    def _find_ffprobe(self) -> str:
        """Locate ffprobe executable"""
        # Check same directory as ffmpeg
        ffprobe_path = settings.BASE_DIR / "ffprobe.exe"
        if ffprobe_path.exists():
            return str(ffprobe_path)
        return "ffprobe"  # fallback to PATH

    def _get_duration(self, file_path: str) -> Optional[float]:
        """Extract duration from media file using ffmpeg"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-i", file_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30
            )
            stderr = result.stderr
            match = re.search(r"Duration: (\d\d):(\d\d):(\d\d)\.(\d+)", stderr)
            if match:
                h, m, s, ms = match.groups()
                return int(h) * 3600 + int(m) * 60 + int(s) + float(f"0.{ms}")
        except Exception as e:
            print(f"[!] Failed to extract duration from {file_path}: {e}")
        return None

    def _create_thumbnail(self, file_path: str, output_path: str) -> bool:
        """Generate thumbnail from video file"""
        try:
            # Try extracting attached cover art first (common in audio)
            result = subprocess.run(
                [
                    self.ffmpeg_path, "-i", file_path,
                    "-map", "0:v:0",
                    "-frames:v", "1",
                    "-q:v", "2",
                    output_path, "-y"
                ],
                timeout=30,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0 and Path(output_path).exists() and Path(output_path).stat().st_size > 0:
                return True

            # Fallback: seek to 1 second for video files
            result = subprocess.run(
                [
                    self.ffmpeg_path, "-ss", "00:00:01",
                    "-i", file_path,
                    "-frames:v", "1",
                    "-q:v", "2",
                    output_path, "-y"
                ],
                timeout=30,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return result.returncode == 0 and Path(output_path).exists()
        except Exception as e:
            print(f"[!] Failed to create thumbnail for {file_path}: {e}")
        return False

    async def _allocate_sequential_number(self, video_dir: Path) -> int:
        """Find the smallest available sequential number by scanning existing Video_* files.

        Uses an async lock to avoid duplicate allocations under concurrency.
        """
        # Global/module-level lock to serialize allocations
        if not hasattr(self, "_numbering_lock"):
            self._numbering_lock = asyncio.Lock()

        async with self._numbering_lock:
            used_numbers = set()
            try:
                for f in video_dir.iterdir():
                    if f.is_file():
                        # Match stems like "Video_01", "Video_123"
                        m = re.match(r"^Video_(\d{2,})$", f.stem)
                        if m:
                            try:
                                used_numbers.add(int(m.group(1)))
                            except ValueError:
                                pass
            except Exception:
                # If directory iteration fails, fall back to 1
                pass

            # Smallest missing positive integer starting from 1
            n = 1
            while n in used_numbers:
                n += 1
            return n

    async def process_download(self, download: Download, db: Session) -> bool:
        """
        Process a completed download: extract metadata and generate thumbnail

        Args:
            download: Download model instance
            db: Database session

        Returns:
            bool: True if processing succeeded
        """
        # Type hints for Pylance - at runtime these are actual values, not Columns
        file_path_str: Optional[str] = download.file_path  # type: ignore

        if not file_path_str:
            print(f"[!] No file_path for download {download.id}")
            return False

        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"[!] File not found: {file_path}")
            return False

        try:
            # Determine directory and allocate the next available sequential number
            file_extension = file_path.suffix
            video_dir = file_path.parent

            # Only use continuous numbering for VIDEO downloads; otherwise default to DB id
            dl_type = getattr(download, "download_type", None)
            if dl_type == DownloadType.VIDEO or dl_type == getattr(DownloadType, "VIDEO", None) or dl_type == "VIDEO":
                sequential_num = await self._allocate_sequential_number(video_dir)
            else:
                sequential_num = download.id  # type: ignore

            # Rename video file to sequential format (Video_XX.mp4)
            new_video_name = f"Video_{sequential_num:02d}{file_extension}"
            new_video_path = file_path.parent / new_video_name

            # Only rename if name is different
            if file_path != new_video_path:
                file_path.rename(new_video_path)
                file_path = new_video_path
                download.file_path = str(new_video_path)  # type: ignore
                download.file_name = new_video_name  # type: ignore
                download.title = f"Video_{sequential_num:02d}"  # type: ignore
                print(f"[+] Renamed video to: {new_video_name}")

            # Extract duration
            duration = self._get_duration(str(file_path))
            if duration:
                download.duration = duration  # type: ignore
                print(
                    f"[+] Extracted duration for download {download.id}: {duration:.2f}s")

            # Update file metadata
            download.file_size = file_path.stat().st_size  # type: ignore

            # Generate thumbnail with sequential naming
            thumbs_dir = settings.DOWNLOAD_DIR / "Thumbnails"
            thumbs_dir.mkdir(parents=True, exist_ok=True)

            thumb_name = f"Thumbnail_{sequential_num:02d}.jpg"
            thumb_path = thumbs_dir / thumb_name

            if self._create_thumbnail(str(file_path), str(thumb_path)):
                # Update the thumbnail_url using SQLAlchemy's update pattern
                setattr(download, "thumbnail_url",
                        f"/media/Thumbnails/{thumb_name}")
                print(f"[+] Created thumbnail for download {download.id}")
            else:
                print(
                    f"[*] Could not create thumbnail for download {download.id}")

            db.commit()
            return True

        except Exception as e:
            print(
                f"[!] Error processing metadata for download {download.id}: {e}")
            return False
