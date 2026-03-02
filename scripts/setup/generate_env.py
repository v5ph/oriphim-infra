#!/usr/bin/env python3
"""
Generate secure .env file for Oriphim Watcher Protocol

This script creates a .env file with cryptographically secure random keys.
Run once during initial setup or when rotating keys.
"""

import secrets
import os
from pathlib import Path


def generate_env_file(force: bool = False) -> None:
    """
    Generate .env file with secure random keys.
    
    Args:
        force: If True, overwrite existing .env file
    """
    env_path = Path(".env")
    
    if env_path.exists() and not force:
        print(f"ERROR: {env_path} already exists")
        print("Use --force to overwrite, or manually edit the file")
        return
    
    # Generate secure keys
    database_key = secrets.token_hex(32)  # 64 hex characters
    jwt_key = secrets.token_urlsafe(64)   # Base64-url encoded
    
    env_content = f"""# Oriphim Watcher Protocol - Environment Configuration
# Generated on: {os.environ.get('DATE', 'unknown')}
# KEEP THIS FILE SECURE - NEVER COMMIT TO VERSION CONTROL

# Database Encryption (AES-256)
DATABASE_ENCRYPTION_KEY={database_key}

# JWT Token Configuration
JWT_SECRET_KEY={jwt_key}
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Session Management
SESSION_TIMEOUT_MINUTES=30
MAX_CONCURRENT_SESSIONS_PER_USER=3
TOKEN_BLACKLIST_CLEANUP_HOURS=24

# TLS/HTTPS Configuration (set to true in production)
ENFORCE_HTTPS=false
HSTS_MAX_AGE_SECONDS=31536000

# Database Configuration
SQLITE_DB_PATH=.watcher_demo.db

# API Configuration
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_BURST=100

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Security Headers (all enabled by default)
ENABLE_CSP=true
ENABLE_HSTS=true
ENABLE_X_FRAME_OPTIONS=true
"""
    
    # Write file
    with open(env_path, "w") as f:
        f.write(env_content)
    
    # Set restrictive permissions (Unix only)
    try:
        os.chmod(env_path, 0o600)
        print(f"Set {env_path} permissions to 600 (owner read/write only)")
    except Exception:
        pass  # Windows doesn't support chmod
    
    print(f"\nGenerated {env_path} with secure keys")
    print("\nIMPORTANT:")
    print("1. Back up this file in a secure location (password manager, vault)")
    print("2. Add .env to .gitignore (should already be there)")
    print("3. Never commit .env to version control")
    print("4. Rotate keys periodically (quarterly recommended)")
    print("\nKeys generated:")
    print(f"  DATABASE_ENCRYPTION_KEY: {database_key[:16]}... (64 chars)")
    print(f"  JWT_SECRET_KEY: {jwt_key[:32]}... (86+ chars)")
    print("\nFor production deployment:")
    print("  - Set ENFORCE_HTTPS=true")
    print("  - Review and adjust timeout values")
    print("  - Consider using environment-specific secrets manager")


if __name__ == "__main__":
    import sys
    
    force = "--force" in sys.argv
    
    if force:
        print("WARNING: This will overwrite existing .env file")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted")
            sys.exit(0)
    
    generate_env_file(force=force)
