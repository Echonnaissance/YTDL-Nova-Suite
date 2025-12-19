# Changelog & Improvements

All notable changes, improvements, and applied fixes for the YouTube Downloader project are documented here.

---

## [1.2.0] - 2025-12-18

### New Features

- **Theme Toggle** - Dark/Light mode switcher in the navigation bar
  - Respects system preference on first visit
  - Persists preference in localStorage
  - Full light theme color palette
- **Toast Notifications** - Beautiful slide-in notifications for all actions
  - Success, error, warning, and info variants
  - Auto-dismiss with close button
  - Replaces inline messages throughout the app
- **API Documentation Page** - New `/api-docs` route with:
  - Complete endpoint reference
  - Request/response examples
  - Supported formats and quality options
  - Links to Swagger UI and ReDoc

### UI Improvements

- **Symmetrical Home Page** - Two-column layout with Features and Supported Sites
- **Quick Tips Section** - Keyboard shortcuts displayed on home page
- **Footer Navigation** - Uses React Router links for smoother navigation

---

## [1.1.0] - 2025-12-18

### UI/UX Overhaul

- **Compact Layout** - Redesigned download form with all options visible on one screen
  - Inline Video/Audio toggle buttons
  - Compact quality and format dropdowns
  - Streamlined video preview with small thumbnails
  - Reduced vertical space and scrolling

### New Features

- **Paste Detection** - Auto-fetches video info when pasting a URL
- **Keyboard Shortcut** - `Ctrl+Enter` (or `Cmd+Enter`) to instantly start download
- **Clear Button** - ✕ button in URL input to quickly clear and refocus
- **Recent URLs Dropdown** - Shows last 5 downloaded URLs (session storage)
- **Real-time Progress Bar** - Live progress, speed, and ETA during downloads

### Format Support

- **New Video Formats**: MOV, AVI, WMV, OGV (via ffmpeg conversion)
- **Existing Formats**: MP4, WebM, MKV (native), M4A, MP3, Opus (audio)

### Backend Improvements

- **Cookies File Support** - Added `COOKIES_FILE` environment variable as preferred method over `--cookies-from-browser` to avoid Windows DPAPI issues
- **Universal URL Support** - Removed domain whitelist, now accepts any http/https URL (yt-dlp supports 1000+ sites)
- **Fixed Duration Type** - Changed from `int` to `float` in schemas for accurate timestamps
- **Download Directory** - Now uses `project/Downloads/Video` and `project/Downloads/Audio`

### Bug Fixes

- Fixed 422 API errors caused by middleware consuming request body
- Fixed Pylance import errors (SQLAlchemy, Pydantic)
- Fixed path traversal in middleware request validation

### UI Clarity

- Batch mode button now shows "📋 Batch" with tooltip
- Coverart embed button now shows "🖼️ Coverart" with tooltip

---

## [1.0.0] - 2025-11-26

### Major Features

- Desktop Application (UniversalMediaDownloader.py):
  - Modern GUI (tkinter/ttk)
  - Video/audio download, playlist preview, batch mode
  - Progress tracking, thumbnail embedding, dark mode
  - CLI argument parsing, smart path resolution, logging, error handling
- Web Application (FastAPI backend, React frontend):
  - RESTful API, async download queue, SQLAlchemy ORM
  - Real-time progress, download history, user settings
  - Health checks, interactive API docs
  - Multi-platform support: YouTube, Twitter/X, Instagram, TikTok, etc.
- Security:
  - Rate limiting, path traversal & command injection protection
  - Request size limits, security headers, API key auth, logging
  - Disk space checks, download quotas, file type validation, CORS validation
- Documentation:
  - Quick Start, config guides, troubleshooting, security overview

### Improvements & Fixes

- Standalone script: CLI, config file, logging, error handling, progress tracking
- Backend: Extended URL validation, cookie browser support, better error messages
- Frontend: Multi-platform URL validation, improved feedback
- Docker support, CI/CD pipeline, type hints, batch download support
- Disk space management, log rotation, streaming size enforcement
- Security: Subprocess timeout, quality/format whitelisting, enhanced sanitization

### Usage Examples

```bash
# Basic usage
python UniversalMediaDownloader.py https://youtube.com/watch?v=VIDEO_ID
# With options
python UniversalMediaDownloader.py https://x.com/user/status/123456 --cookies-browser chrome
# Using config file
python UniversalMediaDownloader.py --config config.json
```

---

## [Unreleased]

### Planned Features

- WebSocket real-time progress
- User authentication, multi-user support
- Scheduled downloads, video format conversion
- Download speed limiting, subtitle download
- Browser extension, mobile app, cloud storage

---

## Implementation & Applied Changes

### Key Improvements

- No more hardcoded values in scripts
- Professional CLI interface, smart executable detection
- Comprehensive error handling, progress tracking
- Multi-platform support, configuration files, command-line options
- Cross-platform and production-ready

### Backend & Frontend

- Multi-platform URL support, cookie browser integration
- Better error messages, flexible configuration
- Unit tests, improved documentation

### Security

- Multi-layer input validation, resource exhaustion protection
- Enhanced rate limiting, disk space management
- File type validation, production config validation

---

## Version History Format

### [X.Y.Z] - YYYY-MM-DD

#### Added

- New features and capabilities

#### Changed

- Changes to existing functionality

#### Deprecated

- Features that will be removed in future versions

#### Removed

- Features that have been removed

#### Fixed

- Bug fixes and corrections

#### Security

- Security-related changes and improvements

---

**Maintained by:** Echonnaissance  
**License:** Educational purposes  
**Repository:** UMD
