"""Universal Media Downloader

A command-line tool for downloading videos from YouTube, Twitter/X, and other
platforms supported by yt-dlp.

Usage:
    python UniversalMediaDownloader.py <URL> [options]
    python UniversalMediaDownloader.py --config config.json
"""
from pathlib import Path
import subprocess
import os
import sys
import argparse
import logging
import json
import shutil
from typing import Optional, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def find_executable(name: str, possible_paths: List[str]) -> Optional[str]:
    """Find an executable in several common locations or on PATH."""
    # Check explicit candidate paths first
    for path in possible_paths:
        full = os.path.abspath(path)
        if os.path.exists(full):
            logger.info("Found %s at: %s", name, full)
            return full

    # Try shutil.which for system PATH (works cross-platform)
    # Try both the provided name and the name without a trailing ".exe"
    candidates = [name]
    if name.endswith(".exe"):
        candidates.append(name[:-4])
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            logger.info("Found %s in system PATH: %s", name, found)
            return found

    return None


def find_ytdlp(script_dir: str, project_root: str) -> Optional[str]:
    exe = "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp"
    candidates = [
        os.path.join(script_dir, exe),
        os.path.join(project_root, exe),
        os.path.join(project_root, "dist", exe),
        os.path.join(project_root, "backend", exe),
    ]
    return find_executable(exe, candidates)


def find_ffmpeg(script_dir: str, project_root: str) -> Optional[str]:
    exe = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    candidates = [
        os.path.join(script_dir, exe),
        os.path.join(project_root, exe),
        os.path.join(project_root, "dist", exe),
        os.path.join(project_root, "backend", exe),
    ]
    return find_executable(exe, candidates)


def build_yt_dlp_command(url: str, output_dir: str, audio_only: bool = False, format_str: Optional[str] = None) -> List[str]:
    cmd = ["yt-dlp", url]
    if audio_only:
        cmd += ["-x", "--audio-format", "mp3"]
    if format_str:
        cmd += ["-f", format_str]
    cmd += ["-o", os.path.join(output_dir, "%(title)s.%(ext)s")]
    return cmd


def main(argv: Optional[List[str]] = None) -> int:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))

    # If the user runs the script from a different working directory, and the
    # bundled `yt-dlp` lives next to the script but isn't on PATH, show a
    # clearer error that explains how to run the script from the project root
    # or using the full script path.
    cwd = os.path.abspath(os.getcwd())
    bundled_exe = 'yt-dlp.exe' if sys.platform == 'win32' else 'yt-dlp'
    bundled_path = os.path.join(script_dir, bundled_exe)

    # Locate yt-dlp (searches PATH and common locations)
    ytdlp_path = find_ytdlp(script_dir, project_root)

    # If user ran from a different cwd, the bundled exe exists next to the
    # script, but it wasn't found in PATH, provide a helpful error and exit.
    if cwd != script_dir and os.path.exists(bundled_path) and not ytdlp_path:
        print(f"Error: it looks like you ran the script from {cwd},")
        print(f"but the bundled {bundled_exe} is located in {script_dir}.")
        print("Run from the project root or invoke the script with its full path:")
        print(
            f"  python \"{os.path.join(script_dir, os.path.basename(__file__))}\" --help")
        print("Or add the project directory to your PATH so bundled executables are found.")
        return 4
    _ = find_ffmpeg(script_dir, project_root)

    parser = argparse.ArgumentParser(description="Universal Media Downloader")
    parser.add_argument("url", nargs="?", help="URL to download")
    parser.add_argument("--config", help="Path to config file", default=None)
    parser.add_argument("--audio-only", action="store_true",
                        help="Extract audio as MP3")
    parser.add_argument(
        "--format", help="Format string for yt-dlp", default=None)
    parser.add_argument("--output", help="Output directory",
                        default="Downloads")

    args = parser.parse_args(argv)

    if args.config:
        try:
            with open(args.config, "r", encoding="utf-8") as f:
                json.load(f)
            logger.info("Loaded config from %s", args.config)
        except Exception as e:
            logger.error("Failed to load config: %s", e)
            return 2

    if not args.url:
        try:
            args.url = input(
                'Enter URL to download (or press Enter to cancel): ').strip()
        except (EOFError, KeyboardInterrupt):
            args.url = ''
        if not args.url:
            print('No URL provided. Exiting.')
            return 1

    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)

    cmd = build_yt_dlp_command(
        args.url, output_dir, audio_only=args.audio_only, format_str=args.format)
    if ytdlp_path:
        cmd[0] = ytdlp_path

    try:
        logger.info("Running: %s", " ".join(cmd))
        proc = subprocess.run(cmd, check=False)
        return proc.returncode
    except FileNotFoundError:
        logger.error(
            "yt-dlp not found. Please install yt-dlp or place it in the project root.")
        return 3


if __name__ == "__main__":
    import sys
    # Try to detect a live debugger more robustly. Prefer debugpy if available
    # (used by VS Code), fallback to sys.gettrace().
    debugging = False
    try:
        from importlib import util, import_module

        spec = util.find_spec("debugpy")
        if spec is not None:
            debugpy = import_module("debugpy")
            try:
                debugging = debugpy.is_client_connected()
            except Exception:
                debugging = bool(sys.gettrace())
        else:
            debugging = bool(sys.gettrace())
    except Exception:
        debugging = bool(sys.gettrace())

    try:
        rc = main()
        # If main returned a non-zero integer, exit when not debugging
        if isinstance(rc, int) and rc != 0:
            if debugging:
                # running under a debugger: avoid terminating the session
                print(f"Program would exit with code {rc}")
            else:
                sys.exit(rc)
    except SystemExit as e:
        # If under a debugger, print the exit code and avoid re-raising so the debugger doesn't stop
        if debugging:
            print(f"Program exited with code {e.code}")
        else:
            raise
