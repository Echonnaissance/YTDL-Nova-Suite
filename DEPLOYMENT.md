# Deployment Guide

This guide covers deploying the YouTube Downloader application to production environments.

**Version**: 1.0.0
**Last Updated**: 2025-11-26

---

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Deployment Options](#deployment-options)
- [Server Requirements](#server-requirements)
- [Production Setup](#production-setup)
- [Deployment Methods](#deployment-methods)
  - [Traditional Server Deployment](#traditional-server-deployment)
  - [Docker Deployment](#docker-deployment-planned)
  - [Cloud Platform Deployment](#cloud-platform-deployment)
- [Post-Deployment](#post-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Checklist

### Security Configuration

- [ ] Generate secure `SECRET_KEY` using `python generate_keys.py`
- [ ] Generate secure `API_KEY` using `python generate_keys.py`
- [ ] Set `DEBUG=False` in production `.env`
- [ ] Enable API key authentication (`ENABLE_API_KEY_AUTH=true`)
- [ ] Update `CORS_ORIGINS` to production domain(s) with HTTPS
- [ ] Review and adjust rate limits for expected traffic
- [ ] Configure HTTPS/TLS certificates
- [ ] Set up firewall rules

### Database Configuration

- [ ] Switch from SQLite to PostgreSQL
- [ ] Set up database backups
- [ ] Configure connection pooling
- [ ] Test database connectivity
- [ ] Run database migrations

### Application Configuration

- [ ] Review and set appropriate disk space limits
- [ ] Configure download concurrency limits
- [ ] Set up log rotation
- [ ] Configure error monitoring (Sentry, etc.)
- [ ] Test all API endpoints
- [ ] Verify external dependencies (yt-dlp, ffmpeg)

### Infrastructure

- [ ] Set up reverse proxy (nginx/Caddy)
- [ ] Configure SSL/TLS certificates (Let's Encrypt)
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
git clone https://github.com/your-username/YT2MP3url.git .

# Set up backend
cd backend
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Download yt-dlp
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
version: '3.8'

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
