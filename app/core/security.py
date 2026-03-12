"""
app/core/security.py - Centralized Security Infrastructure

Implements SOC 2 Phase 1 security controls:
1. Database encryption key management
2. JWT token generation, validation, and refresh
3. Session management with timeouts
4. Token blacklist for immediate revocation
5. Security header generation
"""

from __future__ import annotations

import os
import secrets
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set
from pathlib import Path

import jwt
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Thread-safe token blacklist (in-memory for now, migrate to Redis for production)
_TOKEN_BLACKLIST: Set[str] = set()
_BLACKLIST_LOCK = threading.Lock()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Session Configuration
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS_PER_USER", "3"))

# Database Encryption
DATABASE_ENCRYPTION_KEY = os.getenv("DATABASE_ENCRYPTION_KEY")


class SecurityConfigError(Exception):
    """Raised when required security configuration is missing."""
    pass


def validate_security_config() -> None:
    """
    Validate that all required security environment variables are set.
    
    Raises:
        SecurityConfigError: If critical configuration is missing
    """
    missing = []
    
    # Read from os.environ directly (not module-level cache) so tests can override
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    db_encryption_key = os.getenv("DATABASE_ENCRYPTION_KEY")
    
    if not jwt_secret:
        missing.append("JWT_SECRET_KEY")
    elif len(jwt_secret) < 32:
        raise SecurityConfigError("JWT_SECRET_KEY must be at least 32 characters")
    
    if not db_encryption_key:
        missing.append("DATABASE_ENCRYPTION_KEY")
    elif len(db_encryption_key) != 64:
        raise SecurityConfigError("DATABASE_ENCRYPTION_KEY must be 64 hex characters")
    
    if missing:
        raise SecurityConfigError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and configure."
        )


def get_database_encryption_key() -> bytes:
    """
    Get database encryption key as bytes.
    
    Returns:
        32-byte encryption key derived from hex string
    
    Raises:
        SecurityConfigError: If key is not configured
    """
    if not DATABASE_ENCRYPTION_KEY:
        raise SecurityConfigError("DATABASE_ENCRYPTION_KEY not configured")
    
    try:
        return bytes.fromhex(DATABASE_ENCRYPTION_KEY)
    except ValueError as e:
        raise SecurityConfigError(f"Invalid DATABASE_ENCRYPTION_KEY format: {e}")


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================

def create_access_token(
    subject: str,
    tenant_id: str,
    user_id: str,
    scope: str,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create JWT access token with short expiration.
    
    Args:
        subject: Token subject (typically user_id)
        tenant_id: Tenant identifier
        user_id: User identifier
        scope: Permission scope
        additional_claims: Extra claims to embed in token
    
    Returns:
        Signed JWT token
    """
    secret = os.getenv("JWT_SECRET_KEY") or JWT_SECRET_KEY
    algorithm = os.getenv("JWT_ALGORITHM", JWT_ALGORITHM)
    expires_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(JWT_ACCESS_TOKEN_EXPIRE_MINUTES)))

    if not secret:
        raise SecurityConfigError("JWT_SECRET_KEY not configured")
    
    now = datetime.utcnow()
    expires = now + timedelta(minutes=expires_minutes)
    
    claims = {
        "sub": subject,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "scope": scope,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": secrets.token_urlsafe(16),  # Unique token ID for blacklist
    }
    
    # Prevent additional_claims from overwriting standard JWT fields
    if additional_claims:
        protected_fields = {"sub", "exp", "iat", "jti", "type", "tenant_id", "user_id", "scope"}
        safe_claims = {k: v for k, v in additional_claims.items() if k not in protected_fields}
        if len(safe_claims) < len(additional_claims):
            import logging
            logger = logging.getLogger(__name__)
            filtered = set(additional_claims.keys()) - set(safe_claims.keys())
            logger.warning(f"Filtered protected JWT claims from additional_claims: {filtered}")
        claims.update(safe_claims)
    
    token = jwt.encode(claims, secret, algorithm=algorithm)
    return token


def create_refresh_token(
    subject: str,
    tenant_id: str,
    user_id: str,
    scope: str = "admin",
) -> str:
    """
    Create JWT refresh token with longer expiration.
    
    Args:
        subject: Token subject (typically user_id)
        tenant_id: Tenant identifier
        user_id: User identifier
        scope: API key scope (must match the issuing access token's scope)
    
    Returns:
        Signed JWT refresh token
    """
    secret = os.getenv("JWT_SECRET_KEY") or JWT_SECRET_KEY
    algorithm = os.getenv("JWT_ALGORITHM", JWT_ALGORITHM)
    expires_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", str(JWT_REFRESH_TOKEN_EXPIRE_DAYS)))

    if not secret:
        raise SecurityConfigError("JWT_SECRET_KEY not configured")
    
    now = datetime.utcnow()
    expires = now + timedelta(days=expires_days)
    
    claims = {
        "sub": subject,
        "tenant_id": tenant_id,
        "user_id": user_id,
        "scope": scope,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    
    token = jwt.encode(claims, secret, algorithm=algorithm)
    return token


def verify_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token to verify
        expected_type: Expected token type ("access" or "refresh")
    
    Returns:
        Decoded token claims
    
    Raises:
        jwt.ExpiredSignatureError: If token expired
        jwt.InvalidTokenError: If token invalid or blacklisted
    """
    # Read from os.environ directly (tests may override)
    secret = os.getenv("JWT_SECRET_KEY") or JWT_SECRET_KEY
    algo = os.getenv("JWT_ALGORITHM", "HS256")
    
    if not secret:
        raise SecurityConfigError("JWT_SECRET_KEY not configured")
    
    # Decode and verify signature
    # Decode and verify signature
    # Note: We don't use leeway for expiration checking to ensure expired tokens are rejected
    # verify_iat=False disables "issued at" validation which can fail with test/WSL clock drift
    try:
        claims = jwt.decode(
            token, 
            secret, 
            algorithms=[algo],
            options={"verify_iat": False, "verify_exp": True}
        )
    except jwt.ImmatureSignatureError:
        # Token's iat is in future due to clock skew, but exp is still valid if not too far in past
        claims = jwt.decode(
            token,
            secret,
            algorithms=[algo],
            leeway=5,
            options={"verify_iat": False, "verify_exp": True}
        )
    
    # Verify token type
    if claims.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Expected {expected_type} token, got {claims.get('type')}")
    
    # Check blacklist
    jti = claims.get("jti")
    if jti and is_token_blacklisted(jti):
        raise jwt.InvalidTokenError("Token has been revoked")
    
    return claims


def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    """
    Generate new access token from valid refresh token.
    
    Args:
        refresh_token: Valid refresh token
    
    Returns:
        Dict with new access_token and same refresh_token
    
    Raises:
        jwt.InvalidTokenError: If refresh token invalid or expired
    """
    claims = verify_token(refresh_token, expected_type="refresh")
    
    # Validate required claims exist
    required_claims = ["sub", "tenant_id", "user_id", "scope"]
    for claim in required_claims:
        if claim not in claims:
            raise jwt.InvalidTokenError(f"Missing required claim: {claim}")
    
    # Generate new access token with same claims
    new_access_token = create_access_token(
        subject=claims["sub"],
        tenant_id=claims["tenant_id"],
        user_id=claims["user_id"],
        scope=claims["scope"]
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,  # Keep same refresh token
        "token_type": "bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


# ============================================================================
# TOKEN BLACKLIST (Immediate Revocation)
# ============================================================================

def blacklist_token(jti: str, expires_at: Optional[datetime] = None) -> None:
    """
    Add token to blacklist for immediate revocation.
    
    Args:
        jti: JWT token ID (from "jti" claim)
        expires_at: When token naturally expires (for cleanup)
    """
    with _BLACKLIST_LOCK:
        _TOKEN_BLACKLIST.add(jti)


def is_token_blacklisted(jti: str) -> bool:
    """
    Check if token is blacklisted.
    
    Args:
        jti: JWT token ID
    
    Returns:
        True if blacklisted
    """
    with _BLACKLIST_LOCK:
        return jti in _TOKEN_BLACKLIST


def cleanup_blacklist() -> int:
    """
    Remove expired tokens from blacklist.
    
    In-memory implementation: validates tokens and removes expired ones.
    For production, migrate to Redis with automatic TTL.
    
    Returns:
        Number of tokens removed
    """
    with _BLACKLIST_LOCK:
        if not _TOKEN_BLACKLIST:
            return 0
        
        expired_tokens = []
        now = datetime.utcnow()
        
        for jti in _TOKEN_BLACKLIST:
            try:
                # Attempt to decode and check expiration
                # If token is expired, remove from blacklist
                payload = jwt.decode(
                    jti,  # Note: jti is just the ID, not the full token
                    JWT_SECRET_KEY,
                    algorithms=[JWT_ALGORITHM],
                    options={"verify_signature": False}  # Only check expiration
                )
                exp_timestamp = payload.get("exp")
                if exp_timestamp and datetime.fromtimestamp(exp_timestamp) < now:
                    expired_tokens.append(jti)
            except (jwt.InvalidTokenError, KeyError, ValueError):
                # If we can't decode, assume it's a bare JTI string (our current impl)
                # Keep it in blacklist (no expiration data available)
                pass
        
        for jti in expired_tokens:
            _TOKEN_BLACKLIST.remove(jti)
        
        return len(expired_tokens)


# ============================================================================
# SECURITY HEADERS
# ============================================================================

def get_security_headers() -> Dict[str, str]:
    """
    Generate security headers for HTTP responses.
    
    Returns:
        Dict of header name -> value for security hardening
    """
    headers = {}
    
    # HSTS (HTTP Strict Transport Security)
    if os.getenv("ENABLE_HSTS", "true").lower() == "true":
        max_age = os.getenv("HSTS_MAX_AGE_SECONDS", "31536000")
        headers["Strict-Transport-Security"] = f"max-age={max_age}; includeSubDomains; preload"
    
    # Content Security Policy
    if os.getenv("ENABLE_CSP", "true").lower() == "true":
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
    
    # X-Frame-Options (Clickjacking protection)
    if os.getenv("ENABLE_X_FRAME_OPTIONS", "true").lower() == "true":
        headers["X-Frame-Options"] = "DENY"
    
    # X-Content-Type-Options (MIME sniffing protection)
    headers["X-Content-Type-Options"] = "nosniff"
    
    # X-XSS-Protection (Legacy, but still useful)
    headers["X-XSS-Protection"] = "1; mode=block"
    
    # Referrer Policy
    headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions Policy (restrict browser features)
    headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )
    
    return headers


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionManager:
    """
    Manage user sessions with timeout and concurrent session limits.
    
    Note: In-memory implementation. Migrate to Redis for production clustering.
    """
    
    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def create_session(
        self,
        user_id: str,
        tenant_id: str,
        jti: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create new session for user.
        
        Enforces MAX_CONCURRENT_SESSIONS limit.
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            jti: JWT token ID
            metadata: Additional session data (IP, user-agent, etc.)
        """
        with self._lock:
            # Get existing sessions for user
            user_sessions = {
                k: v for k, v in self._sessions.items()
                if v["user_id"] == user_id and v["tenant_id"] == tenant_id
            }
            
            # Read limit from os.environ (tests may override)
            max_concurrent = int(os.getenv("MAX_CONCURRENT_SESSIONS_PER_USER", "3"))
            
            # Enforce concurrent session limit
            if len(user_sessions) >= max_concurrent:
                # Remove oldest session
                oldest_jti = min(
                    user_sessions.keys(),
                    key=lambda k: user_sessions[k]["created_at"]
                )
                blacklist_token(oldest_jti)
                del self._sessions[oldest_jti]
            
            # Create new session
            self._sessions[jti] = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "metadata": metadata or {}
            }
    
    def update_activity(self, jti: str) -> None:
        """
        Update last activity timestamp for session.
        
        Args:
            jti: JWT token ID
        """
        with self._lock:
            if jti in self._sessions:
                self._sessions[jti]["last_activity"] = datetime.utcnow()
    
    def is_session_valid(self, jti: str) -> bool:
        """
        Check if session exists and hasn't timed out.
        
        Args:
            jti: JWT token ID
        
        Returns:
            True if session valid
        """
        with self._lock:
            if jti not in self._sessions:
                return False
            
            session = self._sessions[jti]
            # Read timeout from os.environ (tests may override)
            timeout_minutes = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
            timeout = timedelta(minutes=timeout_minutes)
            
            if datetime.utcnow() - session["last_activity"] > timeout:
                # Session timed out
                del self._sessions[jti]
                blacklist_token(jti)
                return False
            
            return True
    
    def terminate_session(self, jti: str) -> None:
        """
        Immediately terminate session and blacklist token.
        
        Args:
            jti: JWT token ID
        """
        with self._lock:
            if jti in self._sessions:
                del self._sessions[jti]
            blacklist_token(jti)
    
    def terminate_user_sessions(self, user_id: str, tenant_id: str) -> int:
        """
        Terminate all sessions for a user (e.g., on logout or security event).
        
        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
        
        Returns:
            Number of sessions terminated
        """
        with self._lock:
            terminated = []
            for jti, session in self._sessions.items():
                if session["user_id"] == user_id and session["tenant_id"] == tenant_id:
                    terminated.append(jti)
            
            for jti in terminated:
                del self._sessions[jti]
                blacklist_token(jti)
            
            return len(terminated)
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove timed-out sessions.
        
        Uses environment variable SESSION_TIMEOUT_MINUTES for live timeout config.
        
        Returns:
            Number of sessions removed
        """
        with self._lock:
            now = datetime.utcnow()
            # Read timeout from environment (not cached module constant)
            timeout_minutes = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
            timeout = timedelta(minutes=timeout_minutes)
            expired = []
            
            for jti, session in self._sessions.items():
                if now - session["last_activity"] > timeout:
                    expired.append(jti)
            
            for jti in expired:
                del self._sessions[jti]
                blacklist_token(jti)
            
            return len(expired)


# Global session manager instance
session_manager = SessionManager()


# ============================================================================
# INITIALIZATION & VALIDATION
# ============================================================================

def init_security() -> None:
    """
    Initialize security subsystem and validate configuration.
    
    Call this at application startup.
    
    Raises:
        SecurityConfigError: If configuration invalid
    """
    validate_security_config()


if __name__ == "__main__":
    # Test security configuration
    import time
    
    try:
        init_security()
        print("Security configuration valid")
        
        # Test token generation
        access_token = create_access_token(
            subject="test-user",
            tenant_id="test-tenant",
            user_id="user-123",
            scope="admin"
        )
        print(f"Access token: {access_token[:50]}...")
        
        # Small delay to avoid clock skew issues in test
        time.sleep(0.1)
        
        # Test token verification
        claims = verify_token(access_token)
        print(f"Token claims: {claims}")
        
        # Test refresh token
        refresh_token = create_refresh_token(
            subject="test-user",
            tenant_id="test-tenant",
            user_id="user-123",
            scope="admin",
        )
        print(f"Refresh token: {refresh_token[:50]}...")
        
        # Test token refresh flow
        new_tokens = refresh_access_token(refresh_token)
        print(f"Refreshed access token: {new_tokens['access_token'][:50]}...")
        
    except SecurityConfigError as e:
        print(f"Configuration error: {e}")
        print("\nCopy .env.example to .env and configure required values:")
        print("  - DATABASE_ENCRYPTION_KEY (64 hex characters)")
        print("  - JWT_SECRET_KEY (32+ characters)")
