# Security Implementation Guide

## Overview

This document describes the security features implemented in the YouTube Downloader API and how to configure them properly.

## Security Features Implemented

### 1. Rate Limiting ✅

**What it does:** Prevents abuse by limiting the number of requests per client

**Implementation:**

- Uses `slowapi` library for rate limiting
- Global rate limiting middleware
- Per-endpoint rate limits on critical routes
- Default: 60 requests/minute, 1000 requests/hour

**Configuration:**

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

**Routes protected:**

- `POST /api/downloads/` - 60/minute
- `POST /api/downloads/batch` - 1000/hour (stricter for batch operations)

### 2. Path Traversal Protection ✅

**What it does:** Prevents users from writing files to arbitrary locations on your system

**Implementation:**

- `validate_download_path()` function in `app/core/security.py`
- Validates all download locations in settings updates
- Ensures paths stay within allowed download directory
- Blocks suspicious patterns (.., ~, $)

**Example:**

```python
# BLOCKED - path traversal attempt
download_location = "../../etc/passwd"

# ALLOWED - within download directory
download_location = "C:/YouTube Downloads/My Videos"
```

### 3. Command Injection Prevention ✅

**What it does:** Prevents malicious URLs from executing shell commands

**Implementation:**

- `sanitize_url()` function checks for dangerous characters
- Applied to all download URLs before processing
- Blocks characters: `;`, `|`, `&`, `$`, `` ` ``, `\`, newlines, etc.

**Example:**

```python
# BLOCKED - command injection attempt
url = "https://youtube.com/watch?v=abc; rm -rf /"

# ALLOWED - normal URL
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### 4. Request Size Limits ✅

**What it does:** Prevents memory exhaustion attacks via large request bodies

**Implementation:**

- Middleware validates Content-Length header
- Rejects requests exceeding MAX_REQUEST_SIZE
- Default: 1 MB limit

**Configuration:**

```bash
MAX_REQUEST_SIZE=1048576  # 1 MB
```

### 5. Security Headers ✅

**What it does:** Protects against common web vulnerabilities (XSS, clickjacking, etc.)

**Implementation:**

- Middleware adds security headers to all responses
- Headers included:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Content-Security-Policy: default-src 'self'`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy: geolocation=(), microphone=(), camera=()`

### 6. Enhanced Logging ✅

**What it does:** Provides audit trail for security monitoring

**Implementation:**

- Request/response logging middleware
- Security event logging
- File-based logging (app.log)
- Logs include: timestamp, IP address, endpoint, status code, duration

**Log locations:**

- Console output
- `app.log` file in backend directory

### 7. API Key Authentication (Optional) ✅

**What it does:** Requires API key for all requests (when enabled)

**Implementation:**

- Header-based authentication: `X-API-Key: your-key`
- Constant-time comparison to prevent timing attacks
- Disabled by default for development

**How to enable:**

1. Generate an API key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. Set in `.env`:

```bash
ENABLE_API_KEY_AUTH=true
API_KEY="your-generated-key-here"
```

3. Include in requests:

```bash
curl -H "X-API-Key: your-generated-key-here" http://localhost:8000/api/downloads/
```

**Usage in code:**

```python
from app.core.security import get_api_key
from fastapi import Depends

@router.get("/protected")
async def protected_route(api_key: str = Depends(get_api_key)):
    return {"message": "Access granted"}
```

### 8. Secure SECRET_KEY ✅

**What it does:** Protects session tokens and cryptographic operations

**Configuration:**

1. Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. Set in `.env`:

```bash
SECRET_KEY="your-generated-secret-key-here"
```

**Note:** The application will refuse to start in production (DEBUG=False) with the default dev key.

## Production Deployment Checklist

Before deploying to production, complete these steps:

### Critical (Do Before Launch)

- [ ] Set `DEBUG=False` in `.env`
- [ ] Generate and set secure `SECRET_KEY`
- [ ] Enable API key authentication (`ENABLE_API_KEY_AUTH=true`)
- [ ] Generate and set secure `API_KEY`
- [ ] Configure HTTPS (use reverse proxy like nginx or Caddy)
- [ ] Update `CORS_ORIGINS` to your actual frontend domain
- [ ] Switch to PostgreSQL for `DATABASE_URL`

### Recommended

- [ ] Review and adjust rate limits based on expected traffic
- [ ] Set up log aggregation (e.g., ELK stack, Splunk)
- [ ] Configure security monitoring/alerting
- [ ] Set up automated backups
- [ ] Implement IP whitelisting if needed
- [ ] Add healthcheck monitoring
- [ ] Configure firewall rules

### Ongoing

- [ ] Regularly update dependencies (`pip install -U -r requirements.txt`)
- [ ] Monitor logs for suspicious activity
- [ ] Review and rotate API keys periodically
- [ ] Keep OS and system packages updated
- [ ] Conduct security audits

## Example Production Configuration

### .env (Production)

```bash
DEBUG=False
SECRET_KEY="zK9_xNpQ7wR2vY8mL3jH6gF4dS1aP5cB9nM7kJ2hG4fE8tR3wQ6yU1iO5pA8sD3f"
ENABLE_API_KEY_AUTH=true
API_KEY="tL4_yMqR8xW3vZ9nK2jH7gF5dS6aP4cB1nM8kJ3hG9fE2tR7wQ4yU6iO1pA3sD8f"
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=30
RATE_LIMIT_PER_HOUR=500
MAX_REQUEST_SIZE=524288
DATABASE_URL="postgresql://ytdl_user:secure_password@localhost:5432/ytdl_db"
CORS_ORIGINS='["https://yourdomain.com"]'
LOG_LEVEL="WARNING"
```

### Nginx Reverse Proxy (Example)

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Rate limiting at nginx level (additional layer)
        limit_req zone=api burst=20 nodelay;
    }
}
```

## Testing Security Features

### Test Rate Limiting

```bash
# Send 100 requests rapidly
for i in {1..100}; do
    curl http://localhost:8000/api/downloads/ &
done
# Should see 429 Too Many Requests after hitting limit
```

### Test Path Traversal Protection

```bash
curl -X PATCH http://localhost:8000/api/settings/ \
  -H "Content-Type: application/json" \
  -d '{"download_location": "../../etc/passwd"}'
# Should return 400 Bad Request
```

### Test Command Injection Prevention

```bash
curl -X POST http://localhost:8000/api/downloads/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=abc; rm -rf /"}'
# Should return 400 Bad Request
```

### Test Request Size Limit

```bash
# Create 2MB file
dd if=/dev/zero of=large.json bs=1M count=2

curl -X POST http://localhost:8000/api/downloads/ \
  -H "Content-Type: application/json" \
  -d @large.json
# Should return 413 Request Entity Too Large
```

### Test API Key Authentication

```bash
# With valid key (when enabled)
curl -H "X-API-Key: your-key" http://localhost:8000/api/downloads/
# Should return 200 OK

# Without key
curl http://localhost:8000/api/downloads/
# Should return 401 Unauthorized
```

## Monitoring Security Events

Security events are logged to `app.log` with the prefix `SECURITY EVENT:`.

**Example log entries:**

```
2025-01-26 10:15:23 - app.core.security - WARNING - SECURITY EVENT: {'event_type': 'path_traversal', 'details': {...}, 'client_ip': '192.168.1.100'}
2025-01-26 10:16:45 - app.core.security - WARNING - Invalid API key attempted: tL4_yMqR...
2025-01-26 10:17:12 - app.api.routes.downloads - WARNING - Dangerous character ';' found in URL: https://youtube.com/watch?v=abc;
```

Set up monitoring to alert on:

- Multiple failed API key attempts
- Path traversal attempts
- Command injection attempts
- Rate limit violations
- Unusually large requests

## Additional Recommendations

### For Enhanced Security

1. **Use HTTPS Only**: Never run in production without TLS
2. **Implement JWT Tokens**: For user-specific authentication (beyond API keys)
3. **Add Database Encryption**: Encrypt sensitive data at rest
4. **Use Secrets Manager**: Store secrets in AWS Secrets Manager, Azure Key Vault, etc.
5. **Enable 2FA**: For admin/management interfaces
6. **Implement CSRF Protection**: If using browser-based authentication
7. **Regular Security Audits**: Use tools like `bandit`, `safety`, `snyk`

### Security Scanning

```bash
# Install security tools
pip install bandit safety

# Scan for vulnerabilities
bandit -r app/
safety check

# Keep dependencies updated
pip-audit
```

## Need Help?

For security issues or questions:

1. Check the logs in `app.log`
2. Review this documentation
3. Check the code in `app/core/security.py`
4. Review SECURITY.md for threat model

**Never commit `.env` files to version control!**
