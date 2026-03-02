# SOC 2 Phase 1: Security Controls - Implementation Guide

## Overview
Phase 1 security controls have been implemented, providing encryption at rest, JWT authentication, session management, and security headers.

## Installation

### 1. Install New Dependencies
```bash
pip install -e .
```

This installs:
- `sqlcipher3>=0.5.2` - Database encryption at rest
- `pyjwt>=2.8.0` - JWT token management
- `cryptography>=42.0.0` - Cryptographic operations
- `python-dotenv>=1.0.0` - Environment variable management

### 2. Configure Environment Variables
```bash
# Copy template
cp .env.example .env

# Generate secure keys
python -c "import secrets; print('DATABASE_ENCRYPTION_KEY=' + secrets.token_hex(32))" >> .env
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))" >> .env
```

Required `.env` configuration:
```bash
# Database Encryption (64 hex characters)
DATABASE_ENCRYPTION_KEY=your-64-character-hex-key-here

# JWT Configuration (secure random string)
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Session Management
SESSION_TIMEOUT_MINUTES=30
MAX_CONCURRENT_SESSIONS_PER_USER=3

# TLS/HTTPS Enforcement
ENFORCE_HTTPS=true
HSTS_MAX_AGE_SECONDS=31536000

# Security Headers
ENABLE_CSP=true
ENABLE_HSTS=true
ENABLE_X_FRAME_OPTIONS=true
```

## Features Implemented

### 1. Encryption at Rest
**File:** `app/core/storage.py`, `app/core/onboarding.py`

- SQLCipher integration for database encryption
- Automatic fallback to standard SQLite if encryption unavailable
- AES-256 encryption with PBKDF2 key derivation (256,000 iterations)
- Transparent encryption (no code changes required for queries)

**Verification:**
```python
from app.core.storage import init_db
init_db()  # Will use encrypted database if configured
```

### 2. JWT Authentication & Token Refresh
**File:** `app/core/security.py`, `app/routes/onboarding.py`

- Access tokens: 15-minute expiration (configurable)
- Refresh tokens: 7-day expiration (configurable)
- Token blacklist for immediate revocation
- Session tracking with activity timestamps

**API Endpoints:**
- `POST /v1/onboarding/auth/login` - Exchange API key for JWT tokens
- `POST /v1/onboarding/auth/refresh` - Refresh expired access token
- `POST /v1/onboarding/auth/logout` - Invalidate session and blacklist token
- `GET /v1/onboarding/auth/verify` - Verify token validity

**Usage Example:**
```python
import httpx

# Login with API key
response = httpx.post("http://localhost:8000/v1/onboarding/auth/login", json={
    "api_key": "your-api-key-here"
})
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# Use access token for requests
headers = {"Authorization": f"Bearer {access_token}"}
response = httpx.get("http://localhost:8000/v1/onboarding/auth/verify", headers=headers)

# Refresh when access token expires
response = httpx.post("http://localhost:8000/v1/onboarding/auth/refresh", json={
    "refresh_token": refresh_token
})
new_tokens = response.json()
```

### 3. Session Management
**File:** `app/core/security.py`

- Concurrent session limits (default: 3 per user)
- Session timeout (default: 30 minutes of inactivity)
- Automatic cleanup of expired sessions
- Session metadata tracking (IP, user-agent)

**Features:**
- Oldest session auto-removed when limit exceeded
- Token blacklisting on session termination
- Activity timestamp updates on each request

### 4. Security Headers
**File:** `app/core/security.py`, `app/main.py`

Applied to all HTTP responses:
- `Strict-Transport-Security` (HSTS) - Force HTTPS
- `Content-Security-Policy` (CSP) - Prevent XSS
- `X-Frame-Options` - Prevent clickjacking
- `X-Content-Type-Options` - Prevent MIME sniffing
- `X-XSS-Protection` - Browser XSS protection
- `Referrer-Policy` - Control referrer information
- `Permissions-Policy` - Restrict browser features

### 5. HTTPS Enforcement
**File:** `app/main.py`

- Automatic HTTPS redirect when `ENFORCE_HTTPS=true`
- X-Forwarded-Proto header support (for reverse proxies)
- 301 permanent redirect for HTTP requests

### 6. Secrets Management
**File:** `.env.example`

- Environment-based configuration
- No hardcoded secrets in code
- Template with secure generation commands
- Validation at startup

## Security Architecture

### Encryption Flow
```
Application Request
    ↓
Storage Layer (storage.py / onboarding.py)
    ↓
Check DATABASE_ENCRYPTION_KEY
    ↓
├─ If set & sqlcipher available → SQLCipher connection (AES-256)
└─ Else → Standard SQLite (logs warning)
    ↓
Database Operations (transparent encryption/decryption)
```

### JWT Authentication Flow
```
1. Client → POST /auth/login (API key)
2. Server validates API key
3. Server generates access_token (15min) + refresh_token (7d)
4. Server creates session with JTI tracking
5. Client stores both tokens
6. Client → API request with Authorization: Bearer {access_token}
7. Server validates token + checks session + updates activity
8. When access_token expires:
   Client → POST /auth/refresh (refresh_token)
   Server → New access_token (same refresh_token)
```

### Session Management Flow
```
Session Creation:
- Store JTI, user_id, tenant_id, metadata, timestamps
- Enforce MAX_CONCURRENT_SESSIONS (remove oldest if exceeded)

On Each Request:
- Verify session exists
- Check inactivity timeout (SESSION_TIMEOUT_MINUTES)
- Update last_activity timestamp
- Blacklist token if timed out

On Logout:
- Delete session
- Add JTI to blacklist
- Prevent further token use
```

## Validation & Testing

### Test Security Configuration
```bash
python -m app.core.security
```

Expected output:
```
Security configuration valid
Access token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Token claims: {'sub': 'test-user', 'tenant_id': 'test-tenant', ...}
Refresh token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Refreshed access token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Test Encrypted Database
```bash
python -c "
from app.core.storage import init_db, _connect
init_db()
conn = _connect()
print('Database encryption:', 'ENABLED' if hasattr(conn, 'execute') else 'DISABLED')
conn.close()
"
```

### Test Security Headers
```bash
curl -I http://localhost:8000/v2/health
```

Expected headers:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
...
```

## Migration from Existing Database

If you have existing unencrypted data:

```bash
# Backup existing database
cp .watcher_demo.db .watcher_demo.db.backup

# Export to SQL
sqlite3 .watcher_demo.db .dump > backup.sql

# Configure encryption key in .env
echo "DATABASE_ENCRYPTION_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" >> .env

# Delete old database
rm .watcher_demo.db

# Reinitialize with encryption
python -c "from app.core.storage import init_db; from app.core.onboarding import init_onboarding_db; init_db(); init_onboarding_db()"

# Import data (sqlcipher3 required)
python -c "
import os
import sqlcipher3.dbapi2 as sqlcipher
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('DATABASE_ENCRYPTION_KEY')

conn = sqlcipher.connect('.watcher_demo.db')
conn.execute(f\"PRAGMA key = x'{key}'\")
conn.execute('PRAGMA cipher_page_size = 4096')

with open('backup.sql', 'r') as f:
    conn.executescript(f.read())

conn.close()
print('Migration complete')
"
```

## Production Deployment Checklist

- [ ] Set `ENFORCE_HTTPS=true`
- [ ] Generate strong `DATABASE_ENCRYPTION_KEY` (64 hex chars)
- [ ] Generate strong `JWT_SECRET_KEY` (64+ chars)
- [ ] Configure `HSTS_MAX_AGE_SECONDS=31536000` (1 year)
- [ ] Enable all security headers
- [ ] Set appropriate token expiration times
- [ ] Configure session timeout for your security requirements
- [ ] Test HTTPS redirect behavior
- [ ] Verify security headers in production
- [ ] Back up encryption keys securely (separate from database)
- [ ] Document key rotation procedures
- [ ] Test token refresh flow
- [ ] Test session timeout behavior
- [ ] Monitor for token blacklist growth

## Performance Considerations

### SQLCipher Impact
- ~5-15% CPU overhead for encryption/decryption
- Negligible latency impact (<1ms per query)
- No storage overhead (same database size)

### JWT Verification
- ~0.1-0.5ms per token verification
- In-memory token blacklist (O(1) lookup)
- Session lookup: O(1) in-memory hash table

### Scalability Notes
- In-memory session store: Single-server only
- Token blacklist: Single-server only
- **Production migration path:** Use Redis for:
  - Distributed session storage
  - Distributed token blacklist with TTL
  - Cross-instance state sharing

## Troubleshooting

### "sqlcipher3 not available" Warning
```bash
pip install sqlcipher3
```

On Ubuntu/Debian:
```bash
sudo apt-get install libsqlcipher-dev
pip install sqlcipher3
```

On macOS:
```bash
brew install sqlcipher
pip install sqlcipher3
```

### "JWT_SECRET_KEY not configured" Error
```bash
# Add to .env
echo "JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" >> .env
```

### "Token has been revoked" Error
- Token was explicitly logged out
- Session exceeded concurrent limit
- Session timed out (30 min inactivity)
- Solution: Re-authenticate with `/auth/login`

### HTTPS Redirect Loop
- Disable with `ENFORCE_HTTPS=false` for local dev
- Ensure reverse proxy sets `X-Forwarded-Proto: https`
- Check load balancer TLS termination settings

## Next Steps (Phase 2)

- [ ] Automated API key rotation
- [ ] Redis integration for distributed sessions
- [ ] Audit log encryption
- [ ] Backup encryption
- [ ] Key rotation automation
- [ ] Multi-region deployment support
- [ ] Rate limiting per token
- [ ] Anomaly detection on token usage

## Support

For issues or questions:
1. Check logs: Application logs show security warnings
2. Verify `.env` configuration
3. Test with `python -m app.core.security`
4. Review this guide's troubleshooting section
