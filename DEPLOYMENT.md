# Deployment, Build & Browser Setup Guide

**Version:** 1.1.3  
**Last Updated:** 2025-12-18

---

## Table of Contents

- [Local Development Setup](#local-development-setup)
- Pre-Deployment Checklist
- Build Guide (Windows Executable)
- Automated Build Script
- Browser Setup for Cookie Authentication
- Deployment Options
- Server Requirements
- Production Setup
- Deployment Methods (Server, Docker, Cloud)
- Post-Deployment
- Monitoring & Maintenance
- Troubleshooting
- Rollback Procedures

---

## Local Development Setup

### Prerequisites

1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **yt-dlp.exe** - [Download](https://github.com/yt-dlp/yt-dlp/releases)
4. **ffmpeg.exe** - [Download](https://ffmpeg.org/download.html)

Place `yt-dlp.exe` and `ffmpeg.exe` in the project root directory.

### Start Backend Server

Open a terminal and run:

```powershell
# Navigate to backend
cd backend

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
venv\Scripts\Activate      # Windows PowerShell
# venv\Scripts\activate.bat  # Windows CMD
# source venv/bin/activate   # macOS/Linux

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Backend URLs:**

- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health Check: http://localhost:8000/api/health

### Start Frontend Server

Open a **second terminal** and run:

```powershell
# Navigate to frontend
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Frontend URL:** http://localhost:5173

### Quick Start Script (Windows)

You can also use the included batch file:

```powershell
# From project root
.\start-dev.bat
```

This starts both servers in one command.

---

## Pre-Deployment Checklist

### Security

- [ ] Generate `SECRET_KEY` & `API_KEY` (`python generate_keys.py`)
- [ ] Set `DEBUG=False` in `.env`
- [ ] Enable API key auth (`ENABLE_API_KEY_AUTH=true`)
- [ ] Enable CSRF protection (`ENABLE_CSRF_PROTECTION=true`)
- [ ] Enable HTTPS redirect (`FORCE_HTTPS=true`)
- [ ] Update `CORS_ORIGINS` to production domain(s)
- [ ] Review rate limits
- [ ] Review rate limits
- [ ] Configure HTTPS/TLS
- [ ] Set up firewall

### Database

- [ ] Use PostgreSQL (not SQLite)
- [ ] Set up backups
- [ ] Configure pooling
- [ ] Test connectivity
- [ ] Run migrations

### Application

- [ ] Set disk space limits
- [ ] Configure concurrency
- [ ] Set up log rotation
- [ ] Error monitoring (Sentry, etc.)
- [ ] Test all API endpoints
- [ ] Verify yt-dlp & ffmpeg

### Infrastructure

- [ ] Set up reverse proxy (nginx/Caddy)
- [ ] Configure SSL/TLS (Let's Encrypt)

---

## Build Guide (Windows Executable)

### Prerequisites

1. **Python 3.10+** installed
2. **PyInstaller** installed:
   ```bash
   pip install pyinstaller
   ```
3. **yt-dlp.exe** and **ffmpeg.exe** available (they'll need to be bundled or accessible)

### Quick Build Process

#### 1. Clean Previous Builds

```powershell
Remove-Item -Recurse -Force build\ -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist\ -ErrorAction SilentlyContinue
Remove-Item -Force "YouTube Downloader.exe" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force __pycache__\ -ErrorAction SilentlyContinue
```

#### 2. Build the Executable

**Option A: Using the spec file (Recommended)**

```powershell
pyinstaller "YouTube Downloader.spec"
```

**Option B: Direct command (creates new spec file)**

```powershell
pyinstaller --name "UMD-Converter" --onefile --console UMDConverter.py
```

#### 3. Locate the Executable

The executable will be in:

```
dist\YouTube Downloader.exe
```

#### 4. Test the Executable

```powershell
.\dist\UMD-Converter.exe --help
.\dist\UMD-Converter.exe https://youtube.com/watch?v=VIDEO_ID --cookies-browser firefox
```

---

## Automated Build Script

Create `build-exe.ps1`:

```powershell
# build-exe.ps1
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist\UMD-Converter.exe") { Remove-Item -Force "dist\UMD-Converter.exe" }
if (Test-Path "__pycache__") { Remove-Item -Recurse -Force "__pycache__" }
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
Write-Host "Building executable..." -ForegroundColor Green
pyinstaller --name "UMD-Converter" `
    --onefile `
    --console `
    --clean `
    --add-data "config.example.json;." `
    UMDConverter.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild successful!" -ForegroundColor Green
    Write-Host "Executable location: dist\UMD-Converter.exe" -ForegroundColor Cyan
    Write-Host "`nTesting executable..." -ForegroundColor Yellow
    .\dist\UMD-Converter.exe --help
} else {
    Write-Host "`nBuild failed! Check errors above." -ForegroundColor Red
    exit 1
}
```

Run it:

```powershell
.\build-exe.ps1
```

---

## Browser Setup for Cookie Authentication

This section explains how to configure browser cookies for downloading from platforms that require authentication (Twitter/X, Instagram, etc.).

### Supported Browsers

- Chrome (`chrome`)
- Brave (`brave`)  
  **Note:** Brave locks its cookie database while running. **Close Brave before downloading.**
- Firefox (`firefox`)
- Edge (`edge`)
- Opera (`opera`)
- Chromium (`chromium`)
- Safari (`safari`)

#### Brave Browser

- Use `--cookies-browser brave` for standalone script
- Set `COOKIE_BROWSER=brave` in backend/.env for web app
- If you see "Could not copy Chrome cookie database" error, close Brave completely (check Task Manager)

#### Firefox with Tor

- Use `--cookies-browser firefox` or `COOKIE_BROWSER=firefox`
- Tor proxy routing does not affect cookie storage
- If using Tor Browser, privacy settings may limit cookie access

#### Quick Setup

```bash
# Standalone script
python UMDConverter.py <URL> --cookies-browser brave
# Backend
COOKIE_BROWSER=brave
```

#### Using Configuration File

Create `config.json`:

```json
{
  "url": "https://x.com/user/status/123456",
  "cookies_browser": "brave",
  "output_dir": "Downloads/Video"
}
```

Run:

```bash
python UMDConverter.py --config config.json
```

#### Testing

```bash
python UMDConverter.py https://x.com/user/status/123456 --cookies-browser brave --verbose
# If it works, you'll see the download start
# If it fails with authentication errors, check that you're logged into Twitter/X in Brave
```

#### Security Notes

- Cookies are read from your browser's cookie database
- No cookies are modified or sent anywhere except to the target platform
- The downloader only reads cookies, never writes them
- Your browser's security settings still apply

---

## Troubleshooting

### Build Issues

- "Module not found" errors: Add missing modules to `hiddenimports` in spec file or use `--hidden-import` flag
- Executable is too large: Use `upx=True` in spec file, `--exclude-module`, or `--onedir`
- Executable won't run: Check dependencies, run with `--debug=all`, test in a clean environment
- "yt-dlp.exe not found": Bundle with executable, place in same directory, add to PATH, or use `--yt-dlp-path`/`--ffmpeg-path`

### Cookie Issues

- "Could not copy Chrome cookie database": Close Brave/Chrome completely
- "No cookies found": Ensure browser is logged in, cookies not cleared, and browser is open (Firefox) or closed (Brave)
- Tor Browser: Use `firefox` as browser option, or try Brave/regular Firefox

---

## Distribution

Include the following when distributing:

1. UMD-Converter.exe
2. yt-dlp.exe
3. ffmpeg.exe
4. config.example.json
5. README.md

Directory structure:

```
UMD-Converter/
├── UMD-Converter.exe
├── yt-dlp.exe
├── ffmpeg.exe
├── config.example.json
└── README.md
```

---

## Build Checklist

- [ ] Clean previous builds
- [ ] Update spec file (if needed)
- [ ] Install PyInstaller: `pip install pyinstaller`
- [ ] Build executable: `pyinstaller spec_file.spec`
- [ ] Test executable: `.\dist\executable.exe --help`
- [ ] Test with actual download
- [ ] Verify all dependencies are accessible
- [ ] Create distribution package
- [ ] Test on clean system (if possible)

---

**Need help?** Check the main README.md or open an issue on GitHub.

- [ ] Set up reverse proxy (nginx/Caddy)
- [ ] Configure SSL/TLS (Let's Encrypt)
- [ ] Set up monitoring (uptime, performance)
- [ ] Configure automated backups
- [ ] Test disaster recovery procedures
- [ ] Set up log aggregation

---

## Deployment Options

### Option 1: Traditional Server (VPS/Dedicated)

**Best for**: Full control, predictable costs, custom requirements

**Platforms**: DigitalOcean, Linode, Vultr, AWS EC2, Google Compute Engine

### Option 2: Platform-as-a-Service (PaaS)

**Best for**: Simplified deployment, automatic scaling

**Platforms**: Heroku, Railway, Render, Fly.io

### Option 3: Containerized Deployment

**Best for**: Portability, microservices, scaling

**Platforms**: Docker, Kubernetes, AWS ECS, Google Cloud Run

---

## Server Requirements

### Minimum Requirements

- **OS**: Ubuntu 20.04+ / Debian 11+ / RHEL 8+
- **CPU**: 2 cores
- **RAM**: 2 GB
- **Storage**: 20 GB SSD (+ storage for downloads)
- **Network**: 100 Mbps

### Recommended for Production

- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4 cores
- **RAM**: 4 GB
- **Storage**: 50 GB SSD + separate volume for downloads
- **Network**: 1 Gbps

### Software Requirements

- Python 3.10 or higher
- Node.js 18 or higher
- PostgreSQL 13 or higher
- nginx or Caddy (reverse proxy)
- ffmpeg (latest stable)
- yt-dlp (auto-updates via app)

---

## Production Setup

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
  python3.10 \
  python3.10-venv \
  python3-pip \
  postgresql \
  postgresql-contrib \
  nginx \
  ffmpeg \
  git \
  curl

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Create Application User

```bash
# Create dedicated user for application
sudo adduser --system --group --home /opt/youtube-downloader ytdl

# Switch to application user
sudo su - ytdl
```

### 3. Clone and Setup Application

```bash
# Clone repository
cd /opt/youtube-downloader
git clone https://github.com/your-username/UMD.git .

# Set up backend
cd backend
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


# Download yt-dlp (official)
cd /opt/youtube-downloader
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o yt-dlp
chmod +x yt-dlp

# Ensure ffmpeg is available
which ffmpeg  # Should show /usr/bin/ffmpeg
```

### 4. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE youtube_downloader;
CREATE USER ytdl_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE youtube_downloader TO ytdl_user;
ALTER DATABASE youtube_downloader OWNER TO ytdl_user;
\q
```

### 5. Environment Configuration

```bash
# Copy environment template
cd /opt/youtube-downloader/backend
cp .env.example .env

# Generate secure keys
python generate_keys.py

# Edit .env file
nano .env
```

**Production `.env` configuration**:

```env
# Application
DEBUG=False
APP_NAME="YouTube Downloader API"
APP_VERSION="1.0.0"

# Server
HOST=0.0.0.0
PORT=8000
RELOAD=False

# Security - CRITICAL!
SECRET_KEY="<generated-secret-key-from-generate_keys.py>"
ENABLE_API_KEY_AUTH=true
API_KEY="<generated-api-key-from-generate_keys.py>"

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Database
DATABASE_URL="postgresql://ytdl_user:your-secure-password@localhost/youtube_downloader"

# CORS - Update with your domain!
CORS_ORIGINS='["https://yourdomain.com"]'

# Downloads
MAX_CONCURRENT_DOWNLOADS=3
MAX_QUEUE_SIZE=100
DEFAULT_VIDEO_FORMAT=mp4
DEFAULT_AUDIO_FORMAT=m4a

# Logging
LOG_LEVEL=INFO
```

### 6. Build Frontend

```bash
# Install dependencies
cd /opt/youtube-downloader/frontend
npm ci --production

# Build for production
npm run build

# The build output will be in frontend/dist/
```

---

## Deployment Methods

### Traditional Server Deployment

#### 1. Configure Systemd Service

Create `/etc/systemd/system/youtube-downloader.service`:

```ini
[Unit]
Description=YouTube Downloader API
After=network.target postgresql.service

[Service]
Type=simple
User=ytdl
Group=ytdl
WorkingDirectory=/opt/youtube-downloader/backend
Environment="PATH=/opt/youtube-downloader/backend/venv/bin"
ExecStart=/opt/youtube-downloader/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/youtube-downloader/Downloads

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable youtube-downloader
sudo systemctl start youtube-downloader
sudo systemctl status youtube-downloader
```

#### 2. Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/youtube-downloader`:

```nginx
# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# Upstream backend
upstream youtube_api {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client max body size (for uploads)
    client_max_body_size 10M;

    # Frontend (React build)
    location / {
        root /opt/youtube-downloader/frontend/dist;
        try_files $uri $uri/ /index.html;
        expires 1h;
    }

    # API Backend
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://youtube_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }

    # Download files
    location /downloads/ {
        alias /opt/youtube-downloader/Downloads/;
        autoindex off;
        internal;
    }

    # Health check
    location /health {
        access_log off;
        proxy_pass http://youtube_api/api/health;
    }
}
```

Enable site and reload nginx:

```bash
sudo ln -s /etc/nginx/sites-available/youtube-downloader /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 3. SSL Certificate with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

### Docker Deployment (Planned)

Create `Dockerfile` for backend:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download yt-dlp
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
  && chmod +x /usr/local/bin/yt-dlp

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: youtube_downloader
      POSTGRES_USER: ytdl_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://ytdl_user:${DB_PASSWORD}@db/youtube_downloader
      SECRET_KEY: ${SECRET_KEY}
      API_KEY: ${API_KEY}
      ENABLE_API_KEY_AUTH: true
      DEBUG: false
    volumes:
      - downloads:/app/Downloads
    depends_on:
      - db
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
      - certbot_conf:/etc/letsencrypt
      - certbot_www:/var/www/certbot
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  downloads:
  certbot_conf:
  certbot_www:
```

---

### Cloud Platform Deployment

#### Heroku

```bash
# Install Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login and create app
heroku login
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SECRET_KEY="your-generated-key"
heroku config:set API_KEY="your-generated-key"
heroku config:set ENABLE_API_KEY_AUTH=true
heroku config:set DEBUG=False

# Deploy
git push heroku main
```

#### Railway

1. Connect GitHub repository
2. Add PostgreSQL database
3. Set environment variables in dashboard
4. Deploy automatically on git push

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Check service status
sudo systemctl status youtube-downloader

# Check nginx status
sudo systemctl status nginx

# Test API health
curl https://yourdomain.com/api/health

# Test API endpoint
curl -H "X-API-Key: your-api-key" https://yourdomain.com/api/downloads/
```

### 2. Performance Testing

```bash
# Install Apache Bench
sudo apt install -y apache2-utils

# Test API performance
ab -n 1000 -c 10 -H "X-API-Key: your-api-key" https://yourdomain.com/api/health
```

### 3. Security Verification

```bash
# Run SSL test
curl https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com

# Check security headers
curl -I https://yourdomain.com

# Verify rate limiting
for i in {1..100}; do curl https://yourdomain.com/api/downloads/; done
```

---

## Monitoring & Maintenance

### Application Monitoring

#### Log Monitoring

```bash
# View application logs
sudo journalctl -u youtube-downloader -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# View application log file
tail -f /opt/youtube-downloader/backend/app.log
```

#### Uptime Monitoring

Use services like:

- **UptimeRobot** (free)
- **Pingdom**
- **StatusCake**
- **Better Uptime**

Configure monitoring for:

- HTTPS endpoint (https://yourdomain.com)
- API health check (https://yourdomain.com/api/health)

### Database Backups

#### Automated PostgreSQL Backup

Create `/usr/local/bin/backup-db.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="youtube_downloader"

mkdir -p $BACKUP_DIR

pg_dump -U ytdl_user $DB_NAME | gzip > $BACKUP_DIR/${DB_NAME}_${DATE}.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${DB_NAME}_${DATE}.sql.gz"
```

Make executable and add to cron:

```bash
sudo chmod +x /usr/local/bin/backup-db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-db.sh
```

### Log Rotation

Create `/etc/logrotate.d/youtube-downloader`:

```
/opt/youtube-downloader/backend/app.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 ytdl ytdl
    sharedscripts
    postrotate
        systemctl reload youtube-downloader
    endscript
}
```

### Update Procedures

```bash
# Stop service
sudo systemctl stop youtube-downloader

# Backup current version
cd /opt/youtube-downloader
git stash
git tag backup-$(date +%Y%m%d)

# Pull updates
git pull origin main

# Update backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations (if any)
# alembic upgrade head

# Rebuild frontend
cd ../frontend
npm ci
npm run build

# Restart service
sudo systemctl start youtube-downloader
sudo systemctl status youtube-downloader
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check service status
sudo systemctl status youtube-downloader

# View recent logs
sudo journalctl -u youtube-downloader -n 100

# Check if port is already in use
sudo netstat -tlnp | grep :8000

# Verify environment variables
sudo -u ytdl cat /opt/youtube-downloader/backend/.env
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
sudo -u postgres psql -c "\l"

# Check if database exists
sudo -u postgres psql -c "\l youtube_downloader"

# Test connection with app user
psql -U ytdl_user -d youtube_downloader -h localhost
```

### High Memory Usage

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Reduce concurrent downloads in .env
MAX_CONCURRENT_DOWNLOADS=2

# Restart application
sudo systemctl restart youtube-downloader
```

### Downloads Failing

```bash
# Check disk space
df -h

# Update yt-dlp
cd /opt/youtube-downloader
./yt-dlp --update

# Check ffmpeg
ffmpeg -version

# View download logs
tail -f /opt/youtube-downloader/backend/app.log | grep -i download
```

---

## Rollback Procedures

### Quick Rollback

```bash
# Stop service
sudo systemctl stop youtube-downloader

# Revert to previous git version
cd /opt/youtube-downloader
git log --oneline  # Find commit to rollback to
git reset --hard <commit-hash>

# Restore database backup (if needed)
gunzip < /opt/backups/postgres/youtube_downloader_YYYYMMDD.sql.gz | \
  psql -U ytdl_user youtube_downloader

# Restart service
sudo systemctl start youtube-downloader
```

### Complete Rollback

```bash
# Stop all services
sudo systemctl stop youtube-downloader nginx

# Restore from backup tag
git checkout backup-YYYYMMDD

# Restore database
# (same as above)

# Rebuild frontend
cd frontend
npm ci
npm run build

# Restart services
sudo systemctl start youtube-downloader nginx
```

---

## Security Considerations

### Firewall Configuration

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Regular Security Updates

```bash
# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Monitoring Security Logs

```bash
# Monitor failed authentication attempts
sudo tail -f /opt/youtube-downloader/backend/app.log | grep "401"

# Monitor rate limit violations
sudo tail -f /opt/youtube-downloader/backend/app.log | grep "429"
```

---

## Support & Resources

- **Documentation**: See README.md, SECURITY.md
- **Issue Tracker**: GitHub Issues
- **Security Issues**: [security-email@example.com]

---

**Deployment Status**: Ready for production with proper configuration
**Last Tested**: 2025-11-26
