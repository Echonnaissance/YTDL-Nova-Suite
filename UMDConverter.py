"""
YouTube/Twitter Video Downloader
A command-line tool for downloading videos from YouTube, Twitter/X, and other platforms supported by yt-dlp.

Usage:
    python UMDConverter.py <URL> [options]
    python UMDConverter.py --config config.json
"""
import subprocess
import os
import sys
import argparse
import logging
import json
import re
from pathlib import Path
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def find_executable(name: str, possible_paths: List[str]) -> Optional[str]:
    """
    Find an executable in multiple possible locations.

    Args:
        name: Name of the executable (e.g., 'yt-dlp.exe', 'ffmpeg.exe')
        possible_paths: List of paths to check

    Returns:
        Path to executable if found, None otherwise
    """
    # Check each possible path
    for path in possible_paths:
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            logger.info(f"Found {name} at: {full_path}")
            return full_path

    # Check system PATH
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                [name.replace('.exe', ''), '--version'],
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Found {name} in system PATH")
                return name.replace('.exe', '')
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    else:  # Linux/macOS
        try:
            result = subprocess.run(
                ['which', name.replace('.exe', '')],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                found_path = result.stdout.strip()
                logger.info(f"Found {name} at: {found_path}")
                return found_path
        except FileNotFoundError:
            pass

    return None


def find_ytdlp(script_dir: str, project_root: str) -> Optional[str]:
    """
    Find yt-dlp executable in common locations.

    Args:
        script_dir: Directory where this script is located
        project_root: Project root directory

    Returns:
        Path to yt-dlp executable or None if not found
    """
    executable_name = 'yt-dlp.exe' if sys.platform == 'win32' else 'yt-dlp'

    possible_paths = [
        os.path.join(script_dir, executable_name),
        os.path.join(project_root, executable_name),
        os.path.join(project_root, 'dist', executable_name),
        os.path.join(project_root, 'backend', executable_name),
    ]

    return find_executable(executable_name, possible_paths)


def find_ffmpeg(script_dir: str, project_root: str) -> Optional[str]:
    """
    Find ffmpeg executable in common locations.

    Args:
        script_dir: Directory where this script is located
        project_root: Project root directory

    Returns:
        Path to ffmpeg executable or None if not found
    """
    executable_name = 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'

    possible_paths = [
        os.path.join(script_dir, executable_name),
        os.path.join(project_root, executable_name),
        os.path.join(project_root, 'dist', executable_name),
        os.path.join(project_root, 'backend', executable_name),
    ]

    return find_executable(executable_name, possible_paths)


def parse_progress(line: str) -> Optional[dict]:
    """
    Parse progress information from yt-dlp output.

    Args:
        line: Output line from yt-dlp

    Returns:
        Dictionary with progress info or None
    """
    progress = {}

    # Parse percentage
    percent_match = re.search(r'(\d+\.?\d*)%', line)
    if percent_match:
        progress['progress'] = float(percent_match.group(1))

    # Parse speed
    speed_match = re.search(r'at\s+([\d.]+\w+/s)', line)
    if speed_match:
        progress['speed'] = speed_match.group(1)

    # Parse ETA
    eta_match = re.search(r'ETA\s+(\d+:\d+)', line)
    if eta_match:
        progress['eta'] = eta_match.group(1)

    # Parse file size
    size_match = re.search(r'of\s+([\d.]+\w+)', line)
    if size_match:
        progress['size'] = size_match.group(1)

    return progress if progress else None


def download_video_from_url(
    url: str,
    output_template: str,
    yt_dlp_executable: str,
    ffmpeg_executable: Optional[str] = None,
    cookies_browser: Optional[str] = None,
    format: str = "mp4",
    quality: str = "best"
) -> bool:
    """
    Download a video from a given URL using yt-dlp.

    Args:
        url: URL to download
        output_template: Output filename template
        yt_dlp_executable: Path to yt-dlp executable
        ffmpeg_executable: Optional path to ffmpeg executable
        cookies_browser: Optional browser name for cookies (e.g., 'chrome', 'firefox')
        format: Output format (mp4, webm, etc.)
        quality: Quality setting (best, 1080p, 720p, etc.)

    Returns:
        True if download successful, False otherwise
    """
    if not os.path.exists(yt_dlp_executable) and not yt_dlp_executable in ['yt-dlp', 'yt-dlp.exe']:
        logger.error(f"yt-dlp executable not found at '{yt_dlp_executable}'")
        logger.error(
            "Please ensure yt-dlp is in the correct location or accessible via your system's PATH.")
        return False

    command = [yt_dlp_executable]

    # Output template
    command.extend(["-o", output_template])

    # FFmpeg location
    if ffmpeg_executable:
        command.extend(["--ffmpeg-location", ffmpeg_executable])
    else:
        logger.info(
            "FFmpeg location not specified. yt-dlp will try to find it in PATH.")

    # Format selection
    if quality == "best":
        command.extend(["-f", "bv*+ba/b"])
    else:
        # For specific quality, use format selector
        command.extend(
            ["-f", f"bestvideo[height<={quality.replace('p', '')}]+bestaudio/best[height<={quality.replace('p', '')}]"])

    command.extend(["--merge-output-format", format])

    # Cookies from browser
    if cookies_browser:
        command.extend(["--cookies-from-browser", cookies_browser])
        logger.info(f"Using cookies from '{cookies_browser}' browser")

    command.append(url)

    logger.info("=" * 60)
    logger.info("Executing command:")
    logger.info(' '.join(f'"{arg}"' if ' ' in arg else arg for arg in command))
    logger.info("=" * 60)

    process = None
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1
        )

        if not process.stdout:
            logger.error("Could not capture stdout from yt-dlp process.")
            return False

        last_progress = {}
        error_lines = []
        for line in process.stdout:
            line = line.rstrip()
            if line:
                # Capture error lines for later analysis
                if 'ERROR' in line or 'error' in line.lower():
                    error_lines.append(line)

                # Parse and log progress
                progress = parse_progress(line)
                if progress:
                    last_progress.update(progress)
                    if 'progress' in progress:
                        progress_msg = f"Progress: {progress['progress']:.1f}%"
                        if 'speed' in progress:
                            progress_msg += f" | Speed: {progress['speed']}"
                        if 'eta' in progress:
                            progress_msg += f" | ETA: {progress['eta']}"
                        logger.info(progress_msg)
                else:
                    # Log other important messages
                    if any(keyword in line.lower() for keyword in ['error', 'warning', 'downloading', 'merging', 'complete']):
                        logger.info(line)

        # Store error lines for error handling
        last_progress['error_lines'] = error_lines

        process.wait()

        if process.returncode == 0:
            logger.info("=" * 60)
            logger.info("Download successful!")
            logger.info("=" * 60)
            return True
        else:
            logger.error("=" * 60)
            logger.error(
                f"yt-dlp process exited with code {process.returncode}")
            logger.error(
                "Please review the output above for specific error messages.")

            # Check for common cookie database errors
            error_output = '\n'.join(last_progress.get('error_lines', []))
            if "Could not copy Chrome cookie database" in error_output or "cookie database" in error_output.lower():
                logger.error("")
                logger.error("⚠️  COOKIE DATABASE ERROR DETECTED")
                logger.error(
                    "This usually happens when your browser is running and locks its cookie database.")
                logger.error("")
                logger.error("Solutions:")
                logger.error(
                    "  1. Close Brave browser completely, then try again")
                logger.error(
                    "  2. Use Firefox instead: --cookies-browser firefox")
                logger.error(
                    "  3. Export cookies manually and use --cookies option (see yt-dlp docs)")
                logger.error("")

            logger.error(
                "Make sure the URL is correct, the content is accessible, and yt-dlp/ffmpeg are correctly configured.")
            logger.error("=" * 60)
            return False

    except FileNotFoundError:
        logger.error(f"Could not find yt-dlp executable '{yt_dlp_executable}'")
        logger.error(
            "Please ensure it is in the correct location or in your system's PATH.")
        return False
    except KeyboardInterrupt:
        logger.warning("\nDownload interrupted by user")
        if process:
            process.terminate()
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return False


def load_config(config_path: str) -> dict:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file: {e}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Download videos from YouTube, Twitter/X, and other platforms',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python UMDConverter.py https://youtube.com/watch?v=VIDEO_ID
  python UMDConverter.py https://x.com/user/status/123456 --cookies-browser chrome
  python UMDConverter.py https://youtube.com/watch?v=VIDEO_ID --output-dir Downloads/Video --format mp4
  python UMDConverter.py --config config.json
        """
    )

    parser.add_argument(
        'url',
        nargs='?',
        help='URL to download (YouTube, Twitter/X, etc.)'
    )

    parser.add_argument(
        '--output-dir',
        default='Downloads/Video',
        help='Output directory for downloaded videos (default: Downloads/Video)'
    )

    parser.add_argument(
        '--cookies-browser',
        choices=['chrome', 'firefox', 'edge',
                 'opera', 'chromium', 'brave', 'safari'],
        help='Browser to use for cookies (required for Twitter/X downloads). '
             'Note: Brave is fully supported. Firefox with Tor proxy works normally. '
             'For Tor Browser specifically, use "firefox" but cookies may be limited.'
    )

    parser.add_argument(
        '--format',
        default='mp4',
        choices=['mp4', 'webm', 'mkv', 'flv'],
        help='Output format (default: mp4)'
    )

    parser.add_argument(
        '--quality',
        default='best',
        help='Video quality (default: best). Examples: best, 1080p, 720p, 480p'
    )

    parser.add_argument(
        '--yt-dlp-path',
        help='Path to yt-dlp executable (auto-detected if not specified)'
    )

    parser.add_argument(
        '--ffmpeg-path',
        help='Path to ffmpeg executable (auto-detected if not specified)'
    )

    parser.add_argument(
        '--config',
        help='Path to JSON configuration file (overrides command-line arguments)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load config if provided
    config = {}
    if args.config:
        config = load_config(args.config)
        # Merge config with command-line args (CLI args take precedence)
        url = args.url or config.get('url')
        output_dir = args.output_dir or config.get(
            'output_dir', 'Downloads/Video')
        cookies_browser = args.cookies_browser or config.get('cookies_browser')
        format_type = args.format or config.get('format', 'mp4')
        quality = args.quality or config.get('quality', 'best')
        yt_dlp_path = args.yt_dlp_path or config.get('yt_dlp_path')
        ffmpeg_path = args.ffmpeg_path or config.get('ffmpeg_path')
    else:
        url = args.url
        output_dir = args.output_dir
        cookies_browser = args.cookies_browser
        format_type = args.format
        quality = args.quality
        yt_dlp_path = args.yt_dlp_path
        ffmpeg_path = args.ffmpeg_path

    # Validate URL
    if not url:
        parser.error("URL is required (either as argument or in config file)")

    # Get script and project directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) if os.path.basename(
        script_dir) != os.path.basename(os.getcwd()) else os.getcwd()

    # Find executables
    if not yt_dlp_path:
        yt_dlp_path = find_ytdlp(script_dir, project_root)
        if not yt_dlp_path:
            logger.error("yt-dlp executable not found!")
            logger.error(
                "Please specify --yt-dlp-path or place yt-dlp in one of these locations:")
            logger.error(
                f"  - {os.path.join(script_dir, 'yt-dlp.exe' if sys.platform == 'win32' else 'yt-dlp')}")
            logger.error(
                f"  - {os.path.join(project_root, 'yt-dlp.exe' if sys.platform == 'win32' else 'yt-dlp')}")
            logger.error("  - System PATH")
            sys.exit(1)

    if not ffmpeg_path:
        ffmpeg_path = find_ffmpeg(script_dir, project_root)
        if not ffmpeg_path:
            logger.warning("FFmpeg executable not found!")
            logger.warning(
                "Video/audio merging may fail if formats need to be merged.")
            logger.warning(
                "You can specify --ffmpeg-path or place ffmpeg in the project directory.")

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        logger.info(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)

    # Construct output template
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    # Download video
    success = download_video_from_url(
        url=url,
        output_template=output_template,
        yt_dlp_executable=yt_dlp_path,
        ffmpeg_executable=ffmpeg_path,
        cookies_browser=cookies_browser,
        format=format_type,
        quality=quality
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
