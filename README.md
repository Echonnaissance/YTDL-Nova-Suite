# Universal Media Downloader

A modern, full-stack universal media downloader built with FastAPI (backend) and React (frontend). Supports YouTube, Twitter/X, Instagram, TikTok, and more.

- Place `ffmpeg.exe` and `yt-dlp.exe` in the project root (same directory as `backend/` and `frontend/`).
  - [yt-dlp Download](https://github.com/yt-dlp/yt-dlp/releases)
    UniversalMediaDownloader/
    ├── yt-dlp.exe
- Download video/audio from YouTube, Twitter/X, Instagram, TikTok, and more.
- **yt-dlp** - Universal video/audio downloader
  UniversalMediaDownloader/
  │ │ │ └── ytdlp_service.py # yt-dlp wrapper
  ├── yt-dlp.exe # Video downloader
- **yt-dlp.exe** - Download from [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases)
  Place `yt-dlp.exe` and `ffmpeg.exe` in the project root directory.
  "url": "https://media.com/watch?v=...",
  "url": "https://media.com/watch?v=..."
  DATABASE_URL=sqlite:///./universal_media_downloader.db
  **"yt-dlp.exe not found"**
- Download yt-dlp.exe from [GitHub releases](https://github.com/yt-dlp/yt-dlp/releases)
- Download yt-dlp.exe from [GitHub releases](https://github.com/yt-dlp/yt-dlp/releases)
- Download yt-dlp.exe from [GitHub releases](https://github.com/yt-dlp/yt-dlp/releases)
- Download yt-dlp.exe from [GitHub releases](https://github.com/yt-dlp/yt-dlp/releases)
- Delete `universal_media_downloader.db` file
  The project includes a standalone command-line script (`UniversalMediaDownloader.py`) for quick downloads without running the full web application.
  python UniversalMediaDownloader.py https://media.com/watch?v=VIDEO_ID
  python UniversalMediaDownloader.py https://media.com/watch?v=VIDEO_ID
  python UniversalMediaDownloader.py https://x.com/user/status/123456 --cookies-browser chrome --output-dir Downloads/Video
  python UniversalMediaDownloader.py --config config.json
- `--yt-dlp-path` - Custom path to yt-dlp executable (auto-detected if not specified)
  "url": "https://media.com/watch?v=VIDEO_ID",
  The standalone script supports all platforms that yt-dlp supports, including:

# YouTube Downloader

**Version:** 1.1.0  
**Last Updated:** 2025-12-18

A modern, full-stack video/audio downloader built with FastAPI (backend) and React (frontend). Supports YouTube, Twitter/X, Instagram, TikTok, and 1000+ sites via yt-dlp.

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **yt-dlp.exe** - [Download](https://github.com/yt-dlp/yt-dlp/releases) → Place in project root
4. **ffmpeg.exe** - [Download](https://ffmpeg.org/download.html) → Place in project root

### Start Backend (Terminal 1)

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate      # Windows
# source venv/bin/activate # macOS/Linux
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend runs at: **http://localhost:8000**  
API Docs at: **http://localhost:8000/api/docs**

### Start Frontend (Terminal 2)

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:5173**

### Project Structure

```
UMD/
├── ffmpeg.exe      # Required - media processing
├── yt-dlp.exe      # Required - video downloader
├── backend/        # FastAPI server
└── frontend/       # React app
```

---

## ✨ Features

- Download video/audio from YouTube, Twitter/X, Instagram, TikTok, etc.
- Real-time progress & download queue
- Playlist support & preview
- Download history with search/filter
- User settings persistence
- Modern, responsive UI
- Standalone CLI script

### UX Features (v1.1.0)

- **Compact Layout** - All options visible without scrolling
- **Paste Detection** - Auto-fetches video info when pasting URL
- **Keyboard Shortcut** - `Ctrl+Enter` to download instantly
- **Clear Button** - Quick ✕ to clear URL input
- **Recent URLs** - Dropdown of last 5 downloaded URLs
- **Real-time Progress** - Live progress bar with speed and ETA

### Supported Formats

- **Video**: MP4, WebM, MKV, MOV, AVI, WMV, OGV
- **Audio**: M4A, MP3, Opus
- **Quality**: Best, 1080p, 720p, 480p

### Backend (FastAPI)

- RESTful API with full endpoints
- Asynchronous download queue system
- SQLAlchemy ORM with SQLite database
- Pydantic schemas for data validation
- Custom exception handling
- CORS support for frontend integration
- Health check and monitoring endpoints
- **Security Features**:
  - Rate limiting to prevent abuse
  - Path traversal protection
  - Command injection prevention
  - Request size limits
  - Security headers (XSS, clickjacking protection)
  - Optional API key authentication
  - Comprehensive security logging

### Frontend (React + Vite)

- Multiple pages: Home, Downloads, History, Settings
- Zustand for state management
- Reusable component library
- Real-time UI updates
- Form validation
- Responsive design

---

## Technology Stack

### Backend

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - SQL toolkit and ORM
- **Pydantic** - Data validation using Python type annotations
- **yt-dlp** - YouTube video/audio downloader
- **FFmpeg** - Media processing
- **Uvicorn** - ASGI server

### Frontend

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Axios** - HTTP client for API communication
- **Zustand** - Lightweight state management
- **React Router** - Client-side routing

---

## Project Structure

```
UMD/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── api/                      # API Layer
│   │   │   └── routes/
│   │   │       ├── downloads.py      # Download endpoints
│   │   │       └── settings.py       # Settings endpoints
│   │   ├── services/                 # Business Logic
│   │   │   ├── download_service.py   # Download orchestration
│   │   │   ├── download_queue.py     # Queue management
│   │   │   └── ytdlp_service.py      # yt-dlp wrapper
│   │   ├── models/                   # Data Layer
│   │   │   ├── database.py           # SQLAlchemy models
│   │   │   └── schemas.py            # Pydantic schemas
│   │   ├── core/                     # Core Utilities
│   │   │   ├── database.py           # DB connection
│   │   │   └── exceptions.py         # Custom exceptions
│   │   ├── utils/                    # Helper functions
│   │   ├── config.py                 # Configuration
│   │   └── main.py                   # Application entry point
│   ├── requirements.txt              # Python dependencies
│   └── venv/                         # Virtual environment
│
├── frontend/                         # React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   └── Navigation.jsx    # App navigation
│   │   │   └── features/
│   │   │       ├── DownloadForm.jsx  # URL input form
│   │   │       ├── DownloadList.jsx  # Active downloads
│   │   │       └── PlaylistPreview.jsx # Playlist viewer
│   │   ├── pages/
│   │   │   ├── HomePage.jsx          # Landing page
│   │   │   ├── DownloadPage.jsx      # Main download page
│   │   │   ├── HistoryPage.jsx       # Download history
│   │   │   └── SettingsPage.jsx      # User settings
│   │   ├── services/
│   │   │   ├── api.js                # Axios instance
│   │   │   ├── downloadService.js    # Download API calls
│   │   │   └── settingsService.js    # Settings API calls
│   │   ├── store/
│   │   │   └── slices/
│   │   │       ├── downloadStore.js  # Download state
│   │   │       └── settingsStore.js  # Settings state
│   │   ├── App.jsx                   # Root component
│   │   └── main.jsx                  # Entry point
│   ├── package.json                  # Node dependencies
│   └── vite.config.js                # Vite configuration
│
├── ffmpeg.exe                        # Media processor
├── yt-dlp.exe                        # Video downloader
└── README.md                         # This file
```

---

## Getting Started

### Prerequisites

- **Python 3.10+** installed
- **Node.js 18+** and npm installed
- **yt-dlp.exe** - Download from [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases)
- **ffmpeg.exe** - Download from [ffmpeg.org](https://ffmpeg.org/download.html)

Place `yt-dlp.exe` and `ffmpeg.exe` in the project root directory.

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy .env.example to .env and update)
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Generate secure keys for production
python generate_keys.py

# Run the backend server
python -m app.main
```

The backend API will start on **http://localhost:8000**

- **API Documentation**: http://localhost:8000/api/docs
- **Alternative Docs**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/api/health

### 2. Frontend Setup

```bash
# Open a new terminal and navigate to frontend
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend will start on **http://localhost:5173**

---

## API Documentation

### Downloads API

#### Create Download

```http
POST /api/downloads/
Content-Type: application/json

{
  "url": "https://youtube.com/watch?v=...",
  "download_type": "audio",
  "format": "m4a",
  "quality": "best"
}
```

#### Get All Downloads

```http
GET /api/downloads/?skip=0&limit=100&status=completed
```

#### Get Active Downloads

```http
GET /api/downloads/active
```

#### Get Download by ID

```http
GET /api/downloads/{download_id}
```

#### Cancel Download

```http
POST /api/downloads/{download_id}/cancel
```

#### Retry Failed Download

```http
POST /api/downloads/{download_id}/retry
```

#### Delete Download

```http
DELETE /api/downloads/{download_id}
```

#### Get Video Info

```http
POST /api/downloads/video-info
Content-Type: application/json

{
  "url": "https://youtube.com/watch?v=..."
}
```

#### Get Download Statistics

```http
GET /api/downloads/stats
```

### Settings API

#### Get Settings

```http
GET /api/settings/
```

#### Update Settings

```http
PATCH /api/settings/
Content-Type: application/json

{
  "default_format": "mp4",
  "default_quality": "1080p",
  "download_location": "C:/Downloads",
  "theme": "dark",
  "auto_download": false
}
```

### System API

#### Health Check

```http
GET /api/health
```

---

## Database Schema

### Download Model

```python
id: Integer (Primary Key)
url: String (required)
title: String
thumbnail_url: String
duration: Integer (seconds)
download_type: Enum (video, audio, playlist)
format: String (mp4, m4a, webm, etc.)
quality: String (best, 1080p, 720p, etc.)
status: Enum (pending, queued, downloading, processing, completed, failed, cancelled)
progress: Float (0.0 - 100.0)
speed: String (e.g., "1.5MB/s")
eta: String (e.g., "00:05")
file_path: String
file_size: Integer (bytes)
error_message: Text
created_at: DateTime
started_at: DateTime
completed_at: DateTime
```

### UserSettings Model

```python
id: Integer (Primary Key)
default_format: String (default: "m4a")
default_quality: String (default: "best")
download_location: String
theme: String (default: "light")
auto_download: Boolean (default: False)
created_at: DateTime
updated_at: DateTime
```

---

## Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory (or copy from `.env.example`):

```env
# Server
DEBUG=True
HOST=0.0.0.0
PORT=8000
RELOAD=True

# Database
DATABASE_URL=sqlite:///./youtube_downloader.db

# Downloads
MAX_CONCURRENT_DOWNLOADS=3
MAX_QUEUE_SIZE=100
DEFAULT_VIDEO_FORMAT=mp4
DEFAULT_AUDIO_FORMAT=m4a
DEFAULT_QUALITY=best

# Cookie Browser (for Twitter/X, Instagram, etc.)
# Options: chrome, firefox, edge, opera, chromium, brave, safari, or leave empty
# Note: Brave is fully supported. Firefox with Tor proxy works normally (use 'firefox').
# For Tor Browser specifically, use 'firefox' but cookies may be limited.
COOKIE_BROWSER=brave

# Security (IMPORTANT for production!)
SECRET_KEY=your-secret-key-here  # Generate with: python generate_keys.py
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Key Authentication (optional, recommended for production)
ENABLE_API_KEY_AUTH=false
API_KEY=  # Generate with: python generate_keys.py

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Request Size Limits
MAX_REQUEST_SIZE=10485760  # MAX REQUEST SIZE(IN BYTES) || 10 MB

# Logging
LOG_LEVEL=INFO
```

**For production deployment**, see [SECURITY_IMPLEMENTATION.md](backend/SECURITY_IMPLEMENTATION.md) for complete security configuration guide.

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
```

---

## Features in Detail

### Download Queue System

- Automatic queue management with configurable concurrency
- Priority-based processing
- Automatic retry on failure
- Progress tracking with ETA and speed

### Playlist Support

- Detect and preview playlists before downloading
- Batch download all videos in a playlist
- Individual video selection from playlists

### Download History

- Complete history of all downloads
- Filter by status (completed, failed, cancelled)
- Search by title or URL
- Delete individual or bulk downloads

### User Settings

- Persistent settings stored in database
- Default format and quality preferences
- Custom download location
- Theme customization (light/dark)
- Auto-download option

---

## Development

### Running in Development Mode

**Backend** (with auto-reload):

```bash
cd backend
python -m app.main
```

**Frontend** (with hot module replacement):

```bash
cd frontend
npm run dev
```

### Building for Production

**Frontend**:

```bash
cd frontend
npm run build
```

The production build will be in `frontend/dist/`

---

## Troubleshooting

### Backend Issues

**"yt-dlp.exe not found"**

- Download yt-dlp.exe from [GitHub releases](https://github.com/yt-dlp/yt-dlp/releases)
- Place it in the project root directory (same level as backend/ and frontend/)

**"ffmpeg.exe not found"**

- Download ffmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
- Extract `ffmpeg.exe` from the archive
- Place it in the project root directory

**Database errors**

- Delete `youtube_downloader.db` file
- Restart the backend server
- Database will be recreated automatically

**Import errors**

- Make sure you're in the virtual environment: `venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend Issues

**Cannot connect to backend**

- Verify backend is running on http://localhost:8000
- Check `VITE_API_URL` in frontend/.env
- Verify CORS settings in backend/app/config.py

**Dependencies not installing**

- Delete `node_modules/` and `package-lock.json`
- Run `npm install` again
- Make sure you have Node.js 18+ installed

**Build errors**

- Clear cache: `npm cache clean --force`
- Delete `node_modules/` and reinstall
- Check for syntax errors in .jsx files

---

## Architecture Principles

### Backend (Layered Architecture)

1. **API Layer** (`api/routes/`) - HTTP request/response handling
2. **Service Layer** (`services/`) - Business logic and orchestration
3. **Data Layer** (`models/`) - Database models and schemas
4. **Core Layer** (`core/`) - Database connection, exceptions, utilities

### Frontend (Component-Based Architecture)

1. **Pages** - Route-level components
2. **Components** - Reusable UI elements
3. **Services** - API communication
4. **Store** - Global state management
5. **Utils** - Helper functions

---

## Security

This application includes comprehensive security features to protect against common vulnerabilities:

### Security Features

- **Rate Limiting**: Prevents abuse and DDoS attacks (60 req/min, 1000 req/hour)
- **Path Traversal Protection**: Validates download locations to prevent unauthorized file access
- **Command Injection Prevention**: Sanitizes URLs to prevent shell command injection
- **Request Size Limits**: Protects against memory exhaustion (1 MB default)
- **Security Headers**: XSS, clickjacking, and other OWASP protection headers
- **API Key Authentication**: Optional authentication layer (disabled by default)
- **Security Logging**: Comprehensive logging for security monitoring

### Quick Security Setup

```bash
# 1. Generate secure keys
cd backend
python generate_keys.py

# 2. Copy output to .env file
# 3. For production, set DEBUG=False and ENABLE_API_KEY_AUTH=true
```

### Production Security Checklist

Before deploying to production:

- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate and set secure `SECRET_KEY`
- [ ] Enable API key authentication (`ENABLE_API_KEY_AUTH=true`)
- [ ] Generate and set secure `API_KEY`
- [ ] Configure HTTPS (use reverse proxy)
- [ ] Update `CORS_ORIGINS` to your domain
- [ ] Switch to PostgreSQL
- [ ] Review rate limits
- [ ] Set up log monitoring

**See [SECURITY_IMPLEMENTATION.md](backend/SECURITY_IMPLEMENTATION.md) for complete security documentation.**

---

## Standalone CLI Script

The project includes a standalone command-line script (`UniversalMediaDownloader.py`) for quick downloads without running the full web application.

### Usage

```bash
# Basic usage
python UniversalMediaDownloader.py https://youtube.com/watch?v=VIDEO_ID

# With options
python UniversalMediaDownloader.py https://x.com/user/status/123456 --cookies-browser chrome --output-dir Downloads/Video

# Using configuration file
python UniversalMediaDownloader.py --config config.json
```

### Options

- `url` - URL to download (required, unless using --config)
- `--output-dir` - Output directory (default: Downloads/Video)
- `--cookies-browser` - Browser for cookies (chrome, firefox, edge, brave, etc.)
- `--cookies-file` - Path to exported cookies file (Netscape format) - **Recommended for Twitter/X**
  - Use a browser extension like "Get cookies.txt LOCALLY" to export cookies
  - Avoids Windows DPAPI decryption issues with `--cookies-browser`
- `--format` - Output format: mp4, webm, mkv, mov, avi, wmv, ogv (default: mp4)
- `--quality` - Video quality: best, 1080p, 720p, 480p (default: best)
- `--yt-dlp-path` - Custom path to yt-dlp executable (auto-detected if not specified)
- `--ffmpeg-path` - Custom path to ffmpeg executable (auto-detected if not specified)
- `--config` - Path to JSON configuration file
- `--verbose, -v` - Enable verbose logging

### Cookie Authentication (for Twitter/X, Instagram, etc.)

**Option 1: Cookies File (Recommended)**

Export cookies using a browser extension and set in `.env`:

```
COOKIES_FILE=C:\path\to\cookies.txt
```

**Option 2: Browser Cookies**

```
COOKIE_BROWSER=brave
```

Note: May fail on Windows due to DPAPI encryption. Use cookies file if you see decryption errors.

### Configuration File

Create a `config.json` file (see `config.example.json`):

```json
{
  "url": "https://youtube.com/watch?v=VIDEO_ID",
  "output_dir": "Downloads/Video",
  "cookies_browser": "chrome",
  "format": "mp4",
  "quality": "best"
}
```

### Supported Platforms

The standalone script supports all platforms that yt-dlp supports, including:

- YouTube
- **yt-dlp** - Powerful video downloader
- Twitter/X (requires `--cookies-browser`)
- Instagram
- TikTok
- Vimeo
- Dailymotion
- Twitch
- Facebook
- Reddit
- And many more...

---

## Future Enhancements

- [ ] WebSocket support for real-time progress updates
- [ ] User authentication and multi-user support
- [ ] Scheduled downloads
- [ ] Video format conversion
- [ ] Download speed limiting
- [ ] Automatic subtitle download
- [ ] Browser extension
- [ ] Mobile app (React Native)
- [ ] Docker containerization
- [ ] Cloud storage integration

---

## License

This project is for educational purposes.

---

## Acknowledgments

- **yt-dlp** - Powerful video downloader
- **FastAPI** - Modern Python web framework
- **React** - Component-based UI library
- **FFmpeg** - Media processing tool

---

**Status**: Fully functional web application ready for use!
