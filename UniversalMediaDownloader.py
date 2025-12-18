
"""
Universal Media Downloader
A command-line tool for downloading videos and audio from YouTube, Twitter/X, Instagram, TikTok, and other platforms supported by yt-dlp.

Usage:
	python UniversalMediaDownloader.py <URL> [options]
	python UniversalMediaDownloader.py --config config.json
"""
# --- migrated and renamed from YTMP3urlConverter.py ---
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

# ...existing code from YTMP3urlConverter.py, with all references to YTMP3urlConverter, YT2MP3, etc. replaced with UniversalMediaDownloader...


def find_executable(name: str, possible_paths: List[str]) -> Optional[str]:
    # ...existing code...

    # ...rest of the code from YTMP3urlConverter.py, unchanged except for docstrings, CLI help, and script name...
