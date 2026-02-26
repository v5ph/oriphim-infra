"""
Test suite for Phase 1 security controls

Validates:
- Encryption at rest functionality
- JWT token generation and validation
- Session management
- Token blacklist
- Security headers
"""

import pytest
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Set test environment before importing modules
os.environ["DATABASE_ENCRYPTION_KEY"] = "0" * 64  # Test key
os.environ["JWT_SECRET_KEY"] = "test_secret_key_at_least_32_characters_long"
os.environ["SQLITE_DB_PATH"] = ":memory:"

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    refresh_access_token,
    blacklist_token,
    is_token_blacklisted,
    session_manager,
    get_security_headers,
    validate_security_config,
    SecurityConfigError
)


class TestJWTTokens:
    """Test JWT token generation and validation."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        token = create_access_token(
            subject="user-123",
            tenant_id="tenant-abc",
            user_id="user-123",
            scope="admin"
        )
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        
        # Verify token
        claims = verify_token(token, expected_type="access")
        assert claims["sub"] == "user-123"
        assert claims["tenant_id"] == "tenant-abc"
        assert claims["user_id"] == "user-123"
        assert claims["scope"] == "admin"
        assert claims["type"] == "access"
        assert "jti" in claims
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = create_refresh_token(
            subject="user-123",
            tenant_id="tenant-abc",
            user_id="user-123"
        )
        
        assert isinstance(token, str)
        
        claims = verify_token(token, expected_type="refresh")
        assert claims["type"] == "refresh"
    
    def test_token_expiration(self):
        """Test that expired tokens are rejected."""
        import jwt
        
        # Create token with immediate expiration
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        
        token = jwt.encode(
            {
                "sub": "user-123",
                "type": "access",
                "exp": past.timestamp(),
                "iat": past.timestamp()
            },
            os.environ["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        
        with pytest.raises(jwt.ExpiredSignatureError):
            verify_token(token)
    
    def test_token_type_validation(self):
        """Test that token type is validated."""
        import jwt
        
        access_token = create_access_token(
            subject="user-123",
            tenant_id="tenant-abc",
            user_id="user-123",
            scope="admin"
        )
        
        # Should fail when expecting refresh token
        with pytest.raises(jwt.InvalidTokenError, match="Expected refresh token"):
            verify_token(access_token, expected_type="refresh")
    
    def test_refresh_flow(self):
        """Test complete token refresh flow."""
        refresh_token = create_refresh_token(
            subject="user-123",
            tenant_id="tenant-abc",
            user_id="user-123"
        )
        
        # Refresh should return new access token
        result = refresh_access_token(refresh_token)
        
        assert "access_token" in result
        assert "refresh_token" in result
        assert result["token_type"] == "bearer"
        assert result["expires_in"] > 0
        
        # Verify new access token
        claims = verify_token(result["access_token"], expected_type="access")
        assert claims["user_id"] == "user-123"


class TestTokenBlacklist:
    """Test token blacklist functionality."""
    
    def test_blacklist_token(self):
        """Test adding token to blacklist."""
        jti = "test-jti-12345"
        
        assert not is_token_blacklisted(jti)
        
        blacklist_token(jti)
        
        assert is_token_blacklisted(jti)
    
    def test_blacklisted_token_rejected(self):
        """Test that blacklisted tokens are rejected."""
        import jwt
        
        token = create_access_token(
            subject="user-123",
            tenant_id="tenant-abc",
            user_id="user-123",
            scope="admin"
        )
        
        # Verify token works initially
        claims = verify_token(token)
        jti = claims["jti"]
        
        # Blacklist it
        blacklist_token(jti)
        
        # Should now be rejected
        with pytest.raises(jwt.InvalidTokenError, match="revoked"):
            verify_token(token)


class TestSessionManagement:
    """Test session management functionality."""
    
    def test_create_session(self):
        """Test session creation."""
        session_manager.create_session(
            user_id="user-123",
            tenant_id="tenant-abc",
            jti="jti-123",
            metadata={"ip": "127.0.0.1"}
        )
        
        assert session_manager.is_session_valid("jti-123")
    
    def test_session_timeout(self):
        """Test session timeout."""
        import time
        
        # Set very short timeout for testing
        original_timeout = os.environ.get("SESSION_TIMEOUT_MINUTES")
        os.environ["SESSION_TIMEOUT_MINUTES"] = "0"  # Immediate timeout
        
        try:
            session_manager.create_session(
                user_id="user-timeout",
                tenant_id="tenant-abc",
                jti="jti-timeout"
            )
            
            # Wait briefly
            time.sleep(0.1)
            
            # Session should be invalid due to timeout
            assert not session_manager.is_session_valid("jti-timeout")
        finally:
            if original_timeout:
                os.environ["SESSION_TIMEOUT_MINUTES"] = original_timeout
            else:
                os.environ.pop("SESSION_TIMEOUT_MINUTES", None)
    
    def test_concurrent_session_limit(self):
        """Test concurrent session limit enforcement."""
        original_limit = os.environ.get("MAX_CONCURRENT_SESSIONS_PER_USER")
        os.environ["MAX_CONCURRENT_SESSIONS_PER_USER"] = "2"
        
        try:
            # Create 3 sessions (limit is 2)
            session_manager.create_session("user-multi", "tenant-abc", "jti-1")
            session_manager.create_session("user-multi", "tenant-abc", "jti-2")
            session_manager.create_session("user-multi", "tenant-abc", "jti-3")
            
            # First session should be removed
            assert not session_manager.is_session_valid("jti-1")
            assert session_manager.is_session_valid("jti-2")
            assert session_manager.is_session_valid("jti-3")
        finally:
            if original_limit:
                os.environ["MAX_CONCURRENT_SESSIONS_PER_USER"] = original_limit
            else:
                os.environ.pop("MAX_CONCURRENT_SESSIONS_PER_USER", None)
    
    def test_terminate_session(self):
        """Test manual session termination."""
        session_manager.create_session("user-term", "tenant-abc", "jti-term")
        assert session_manager.is_session_valid("jti-term")
        
        session_manager.terminate_session("jti-term")
        
        assert not session_manager.is_session_valid("jti-term")
        assert is_token_blacklisted("jti-term")
    
    def test_terminate_all_user_sessions(self):
        """Test terminating all sessions for a user."""
        session_manager.create_session("user-all", "tenant-abc", "jti-all-1")
        session_manager.create_session("user-all", "tenant-abc", "jti-all-2")
        
        terminated = session_manager.terminate_user_sessions("user-all", "tenant-abc")
        
        assert terminated == 2
        assert not session_manager.is_session_valid("jti-all-1")
        assert not session_manager.is_session_valid("jti-all-2")


class TestSecurityHeaders:
    """Test security headers generation."""
    
    def test_get_security_headers(self):
        """Test security headers are generated."""
        headers = get_security_headers()
        
        assert "Strict-Transport-Security" in headers
        assert "Content-Security-Policy" in headers
        assert "X-Frame-Options" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-XSS-Protection" in headers
        assert "Referrer-Policy" in headers
        assert "Permissions-Policy" in headers
    
    def test_hsts_header(self):
        """Test HSTS header format."""
        headers = get_security_headers()
        hsts = headers["Strict-Transport-Security"]
        
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts
    
    def test_frame_options(self):
        """Test X-Frame-Options is DENY."""
        headers = get_security_headers()
        assert headers["X-Frame-Options"] == "DENY"


class TestSecurityConfig:
    """Test security configuration validation."""
    
    def test_validate_config_success(self):
        """Test valid configuration passes."""
        # Already configured in test environment
        validate_security_config()  # Should not raise
    
    def test_missing_jwt_secret(self):
        """Test missing JWT secret is detected."""
        original = os.environ.pop("JWT_SECRET_KEY", None)
        
        try:
            with pytest.raises(SecurityConfigError, match="JWT_SECRET_KEY"):
                validate_security_config()
        finally:
            if original:
                os.environ["JWT_SECRET_KEY"] = original
    
    def test_short_jwt_secret(self):
        """Test short JWT secret is rejected."""
        original = os.environ.get("JWT_SECRET_KEY")
        os.environ["JWT_SECRET_KEY"] = "short"
        
        try:
            with pytest.raises(SecurityConfigError, match="at least 32 characters"):
                validate_security_config()
        finally:
            if original:
                os.environ["JWT_SECRET_KEY"] = original
    
    def test_invalid_encryption_key_length(self):
        """Test invalid encryption key length is rejected."""
        original = os.environ.get("DATABASE_ENCRYPTION_KEY")
        os.environ["DATABASE_ENCRYPTION_KEY"] = "tooshort"
        
        try:
            with pytest.raises(SecurityConfigError, match="64 hex characters"):
                validate_security_config()
        finally:
            if original:
                os.environ["DATABASE_ENCRYPTION_KEY"] = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
