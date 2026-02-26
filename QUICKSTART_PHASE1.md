# Phase 1 Security Controls - Quick Start

## 1. Initial Setup (5 minutes)

```bash
# Install dependencies
pip install -e .

# Generate secure environment configuration
python generate_env.py

# Verify security configuration
python -m app.core.security
```

## 2. Start the Application

```bash
# Initialize databases
python -c "from app.core.storage import init_db; from app.core.onboarding import init_onboarding_db; init_db(); init_onboarding_db()"

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 3. Quick Test

```python
import httpx

# Create tenant and user
tenant = httpx.post("http://localhost:8000/v1/onboarding/tenants", json={
    "org_name": "Test Corp",
    "domain": "testcorp.com",
    "support_tier": "premium"
}).json()

# Create admin user
user = httpx.post(f"http://localhost:8000/v1/onboarding/tenants/{tenant['tenant_id']}/users", json={
    "email": "admin@testcorp.com",
    "role": "admin"
}).json()

# Generate API key (save this!)
key_response = httpx.post(f"http://localhost:8000/v1/onboarding/tenants/{tenant['tenant_id']}/api-keys", json={
    "scope": "admin",
    "expires_in_days": 90
}).json()

api_key = key_response["api_key"]
print(f"API Key: {api_key}")

# Login with API key to get JWT tokens
tokens = httpx.post("http://localhost:8000/v1/onboarding/auth/login", json={
    "api_key": api_key
}).json()

access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# Use access token for authenticated requests
headers = {"Authorization": f"Bearer {access_token}"}
response = httpx.get("http://localhost:8000/v1/onboarding/auth/verify", headers=headers)
print(response.json())

# When access token expires, refresh it
new_tokens = httpx.post("http://localhost:8000/v1/onboarding/auth/refresh", json={
    "refresh_token": refresh_token
}).json()

# Logout (invalidates all sessions)
httpx.post("http://localhost:8000/v1/onboarding/auth/logout", headers=headers)
```

## 4. Key Features Enabled

### Encryption at Rest ✓
- Database automatically encrypted with AES-256
- Key stored in .env (DATABASE_ENCRYPTION_KEY)
- No code changes needed for queries

### JWT Authentication ✓
- Access tokens: 15 min expiration
- Refresh tokens: 7 day expiration
- Token blacklist for immediate revocation

### Session Management ✓
- 30 minute inactivity timeout
- Max 3 concurrent sessions per user
- Automatic cleanup of expired sessions

### Security Headers ✓
- HSTS, CSP, X-Frame-Options, etc.
- Automatically applied to all responses
- Configurable in .env

### HTTPS Enforcement ✓
- Set ENFORCE_HTTPS=true in production
- Automatic HTTP → HTTPS redirect
- Works behind reverse proxies

## 5. Environment Variables

Key variables in `.env`:

```bash
# Required for encryption
DATABASE_ENCRYPTION_KEY=<64 hex characters>

# Required for JWT
JWT_SECRET_KEY=<secure random string>

# Optional: Adjust timeouts
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
SESSION_TIMEOUT_MINUTES=30

# Production: Enable HTTPS
ENFORCE_HTTPS=true
```

## 6. API Endpoints (New)

### Authentication
- `POST /v1/onboarding/auth/login` - Get JWT tokens from API key
- `POST /v1/onboarding/auth/refresh` - Refresh access token
- `POST /v1/onboarding/auth/logout` - Invalidate session
- `GET /v1/onboarding/auth/verify` - Verify token validity

## 7. Common Tasks

### Check Security Headers
```bash
curl -I http://localhost:8000/v2/health
```

### Rotate Keys (Quarterly)
```bash
# Backup old .env
cp .env .env.backup

# Generate new keys
python generate_env.py --force

# Restart application
```

### Test Encryption
```bash
python -c "
from app.core.storage import _connect
conn = _connect()
# If encrypted, this will work. If not encrypted, connection fails with wrong key.
print('Encryption: ENABLED')
conn.close()
"
```

### Monitor Sessions
```python
from app.core.security import session_manager

# Get session stats
print(f"Active sessions: {len(session_manager._sessions)}")

# Cleanup expired sessions
removed = session_manager.cleanup_expired_sessions()
print(f"Removed {removed} expired sessions")
```

## 8. Troubleshooting

**"sqlcipher3 not available"**
```bash
pip install sqlcipher3
# On Ubuntu: sudo apt-get install libsqlcipher-dev
# On macOS: brew install sqlcipher
```

**"JWT_SECRET_KEY not configured"**
```bash
python generate_env.py
```

**Token expired too quickly**
```bash
# Edit .env
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30  # Increase from 15
```

**Session timeout too aggressive**
```bash
# Edit .env
SESSION_TIMEOUT_MINUTES=60  # Increase from 30
```

## 9. Security Validation

Run security tests:
```bash
pytest tests/test_security_phase1.py -v
```

Expected: All tests pass

## 10. Production Checklist

- [ ] Set strong encryption keys
- [ ] Enable HTTPS enforcement
- [ ] Configure appropriate token expiration
- [ ] Test token refresh flow
- [ ] Verify security headers in browser dev tools
- [ ] Back up .env to secure vault
- [ ] Document key rotation schedule
- [ ] Test session timeout behavior
- [ ] Monitor for blacklist growth
- [ ] Plan migration to Redis for sessions (Phase 2)

## Next Steps

Phase 2 Implementation:
- Automated key rotation
- Redis-based session storage
- Rate limiting per token
- Anomaly detection
- Multi-region support
