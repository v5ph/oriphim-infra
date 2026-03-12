"""
app/core/onboarding.py - Enterprise Onboarding Infrastructure

Implements:
1. Tenant provisioning and multi-tenancy
2. Role-based access control (RBAC)
3. API key management with automatic rotation
4. Identity audit logging
5. Self-serve provisioning workflows
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import hashlib
import hmac
import secrets
import bcrypt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum
from uuid import uuid4
import logging

try:
    import sqlcipher3.dbapi2 as sqlcipher
    ENCRYPTION_AVAILABLE = True
except ImportError:
    sqlcipher = None
    ENCRYPTION_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if env vars set via system

logger = logging.getLogger(__name__)

_DUMMY_API_KEY_HASH = bcrypt.hashpw(b"oriphim-invalid-api-key", bcrypt.gensalt(rounds=12))

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / ".watcher_demo.db"


def _get_db_path() -> str:
    """Resolve database path from environment at runtime.

    This avoids import-time path caching during tests where env vars may change.
    """
    raw_path = os.getenv("SQLITE_DB_PATH", str(_DEFAULT_DB_PATH))
    if raw_path == ":memory:":
        return raw_path
    return Path(raw_path).expanduser().resolve().as_posix()

_LOCK = threading.Lock()
_BOOTSTRAP_LOCKS: Dict[str, threading.Lock] = {}  # Per-tenant bootstrap locks
_BOOTSTRAP_LOCKS_LOCK = threading.Lock()  # Protect _BOOTSTRAP_LOCKS dict


def _get_bootstrap_lock(tenant_id: str) -> threading.Lock:
    """Get or create a per-tenant bootstrap lock.
    
    Prevents TOCTOU race condition during first user creation.
    Multiple threads racing to create the first user will serialize via this lock.
    """
    with _BOOTSTRAP_LOCKS_LOCK:
        if tenant_id not in _BOOTSTRAP_LOCKS:
            _BOOTSTRAP_LOCKS[tenant_id] = threading.Lock()
        return _BOOTSTRAP_LOCKS[tenant_id]


class Role(str, Enum):
    """Supported roles in Oriphim multi-tenant system."""
    ADMIN = "admin"
    RISK_OFFICER = "risk-officer"
    ANALYST = "analyst"
    VIEWER = "viewer"


class SupportTier(str, Enum):
    """SLA support tiers."""
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant lifecycle states."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class APIKeyScope(str, Enum):
    """Fine-grained permission scopes for API keys."""
    VALIDATE_ONLY = "validate-only"  # Can only call /v2/validate
    ADMIN = "admin"  # Full access
    READ_METRICS = "read-metrics"  # Read-only audit trail + health


def _get_encryption_key() -> Optional[str]:
    """Get database encryption key from environment.

    Validates key format before using in PRAGMA statement.
    Only accepts 64-char hex strings to prevent SQL injection.
    """
    key = os.getenv("DATABASE_ENCRYPTION_KEY")
    if not key or len(key) != 64:
        return None
    if not all(c in "0123456789abcdefABCDEF" for c in key):
        raise ValueError("Invalid DATABASE_ENCRYPTION_KEY format: must be 64 hex characters")
    return f'"x\'{key}\'"'


def _connect() -> sqlite3.Connection:
    """
    Get database connection with row factory and optional encryption.
    
    Uses same encryption logic as storage.py for consistency.
    """
    encryption_key = _get_encryption_key()
    db_path = _get_db_path()
    
    if encryption_key and ENCRYPTION_AVAILABLE:
        try:
            conn = sqlcipher.connect(db_path, check_same_thread=False)
            conn.execute(f"PRAGMA key = {encryption_key}")
            conn.execute("PRAGMA cipher_page_size = 4096")
            conn.execute("PRAGMA kdf_iter = 256000")
            conn.execute("SELECT 1")
            conn.row_factory = sqlcipher.Row
            return conn
        except Exception:
            logger.warning(
                "SQLCipher connection failed for DB path '%s'. Falling back to standard SQLite.",
                db_path,
            )
    else:
        if encryption_key and not ENCRYPTION_AVAILABLE:
            logger.warning(
                "DATABASE_ENCRYPTION_KEY set but sqlcipher3 not available. "
                "Using UNENCRYPTED database."
            )
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn


def _get_table_columns(cur: sqlite3.Cursor, table_name: str) -> set[str]:
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def _ensure_column(cur: sqlite3.Cursor, table_name: str, column_name: str, definition: str) -> None:
    if column_name not in _get_table_columns(cur, table_name):
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def _api_key_digest(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def _ensure_role_permissions_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='role_permissions'"
    )
    table_exists = cur.fetchone() is not None

    if not table_exists:
        cur.execute(
            """
            CREATE TABLE role_permissions (
                permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                UNIQUE(role, action, resource)
            )
            """
        )
        return

    cur.execute("PRAGMA index_list(role_permissions)")
    indexes = cur.fetchall()
    role_unique_only = False
    for idx in indexes:
        if idx["unique"] != 1:
            continue
        index_name = idx["name"]
        cur.execute(f"PRAGMA index_info({index_name})")
        columns = [row["name"] for row in cur.fetchall()]
        if columns == ["role"]:
            role_unique_only = True
            break

    if role_unique_only:
        cur.execute("ALTER TABLE role_permissions RENAME TO role_permissions_old")
        cur.execute(
            """
            CREATE TABLE role_permissions (
                permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                UNIQUE(role, action, resource)
            )
            """
        )
        cur.execute(
            """
            INSERT INTO role_permissions (role, action, resource)
            SELECT role, action, resource FROM role_permissions_old
            """
        )
        cur.execute("DROP TABLE role_permissions_old")


def init_onboarding_db() -> None:
    """Initialize onboarding tables. Safe to call multiple times."""
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        # Tenants table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id TEXT PRIMARY KEY,
                org_name TEXT NOT NULL,
                domain TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'active',
                sso_enabled INTEGER DEFAULT 0,
                saml_endpoint TEXT,
                scim_endpoint TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT,
                support_tier TEXT DEFAULT 'standard'
            )
            """
        )
        
        # Users table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                mfa_enabled INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                FOREIGN KEY(tenant_id) REFERENCES tenants(tenant_id)
            )
            """
        )
        
        # API Keys table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                secret_hash TEXT NOT NULL,
                scope TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                expires_at TEXT,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                usage_count INTEGER DEFAULT 0,
                FOREIGN KEY(tenant_id) REFERENCES tenants(tenant_id),
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
            """
        )
        _ensure_column(cur, "api_keys", "api_key_digest", "TEXT")
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_tenant ON api_keys(tenant_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id)")
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_api_keys_digest ON api_keys(api_key_digest) WHERE api_key_digest IS NOT NULL"
        )
        
        # Identity audit log
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS identity_audit_log (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                actor_id TEXT,
                event_type TEXT NOT NULL,
                target TEXT,
                details_json TEXT,
                prev_hash TEXT,
                event_hash TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(tenant_id) REFERENCES tenants(tenant_id)
            )
            """
        )
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_tenant ON identity_audit_log(tenant_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON identity_audit_log(created_at)")
        
        # Roles and permissions matrix (ensure correct schema)
        _ensure_role_permissions_schema(conn)
        
        # Insert default permissions
        default_permissions = [
            ("admin", "validate", "all"),
            ("admin", "read_results", "all"),
            ("admin", "manage_config", "all"),
            ("admin", "manage_users", "all"),
            ("admin", "view_audit", "all"),
            ("risk-officer", "validate", "all"),
            ("risk-officer", "read_results", "all"),
            ("risk-officer", "manage_config", "own"),
            ("risk-officer", "view_audit", "all"),
            ("analyst", "validate", "all"),
            ("analyst", "read_results", "all"),
            ("analyst", "view_audit", "all"),
            ("viewer", "read_results", "all"),
            ("viewer", "view_audit", "all"),
        ]
        
        for role, action, resource in default_permissions:
            cur.execute(
                "INSERT OR IGNORE INTO role_permissions (role, action, resource) VALUES (?, ?, ?)",
                (role, action, resource)
            )
        
        conn.commit()
        conn.close()
        logger.info("Onboarding tables initialized")


# ============================================================================
# TENANT PROVISIONING
# ============================================================================

def create_tenant(org_name: str, domain: str, support_tier: str = "standard") -> Dict[str, Any]:
    """
    Create a new tenant organization.
    
    Args:
        org_name: Organization name (e.g., "Acme Trading Fund")
        domain: Organization domain (e.g., "acmetrading.com")
        support_tier: Support level (standard, premium, enterprise)
    
    Returns:
        New tenant object with tenant_id
    
    Raises:
        ValueError: If domain already registered
    """
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        # Check domain uniqueness
        cur.execute("SELECT tenant_id FROM tenants WHERE domain = ?", (domain,))
        if cur.fetchone():
            raise ValueError(f"Domain {domain} already registered")
        
        tenant_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        
        cur.execute(
            """
            INSERT INTO tenants (tenant_id, org_name, domain, status, created_at, support_tier)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            (tenant_id, org_name, domain, now, support_tier)
        )
        
        # Audit event
        _insert_audit_log(
            conn,
            tenant_id=tenant_id,
            event_type="tenant_created",
            target=tenant_id,
            details={"org_name": org_name, "domain": domain, "support_tier": support_tier}
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Tenant created: {tenant_id} ({org_name})")
        
        return {
            "tenant_id": tenant_id,
            "org_name": org_name,
            "domain": domain,
            "status": "active",
            "support_tier": support_tier,
            "created_at": now
        }


def get_tenant(tenant_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve tenant by ID."""
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,))
        row = cur.fetchone()
        conn.close()
        
        return dict(row) if row else None


def list_tenants(status: str = "active") -> List[Dict[str, Any]]:
    """List all tenants with given status."""
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tenants WHERE status = ? ORDER BY created_at DESC", (status,))
        rows = cur.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


# ============================================================================
# USER MANAGEMENT
# ============================================================================

def create_user(
    tenant_id: str,
    email: str,
    role: str,
    mfa_enabled: bool = True,
    actor_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add user to tenant with role-based access.
    
    Args:
        tenant_id: Tenant this user belongs to
        email: User email address
        role: One of [admin, risk-officer, analyst, viewer]
        mfa_enabled: Whether to require MFA
        actor_id: User who initiated this action (for audit)
    
    Returns:
        New user object
    
    Raises:
        ValueError: If role invalid or email already exists
    """
    # Validate role
    if role not in [r.value for r in Role]:
        raise ValueError(f"Invalid role: {role}")
    
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        # Check email uniqueness
        cur.execute("SELECT user_id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            raise ValueError(f"Email {email} already registered")
        
        user_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        
        cur.execute(
            """
            INSERT INTO users (user_id, tenant_id, email, role, mfa_enabled, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, 'active')
            """,
            (user_id, tenant_id, email, role, 1 if mfa_enabled else 0, now)
        )
        
        # Audit event
        _insert_audit_log(
            conn,
            tenant_id=tenant_id,
            actor_id=actor_id,
            event_type="user_created",
            target=user_id,
            details={"email": email, "role": role, "mfa_enabled": mfa_enabled}
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"User created: {user_id} ({email}) in tenant {tenant_id}")
        
        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "email": email,
            "role": role,
            "mfa_enabled": mfa_enabled,
            "status": "active",
            "created_at": now
        }


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve user by ID."""
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        
        return dict(row) if row else None


def list_tenant_users(tenant_id: str, status: str = "active") -> List[Dict[str, Any]]:
    """List all users in a tenant."""
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC",
            (tenant_id, status)
        )
        rows = cur.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


def change_user_role(
    user_id: str,
    new_role: str,
    actor_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Change user's role (permission escalation must be audited).
    
    Args:
        user_id: User to modify
        new_role: New role
        actor_id: Who made this change (for audit)
    
    Returns:
        Updated user object
    """
    if new_role not in [r.value for r in Role]:
        raise ValueError(f"Invalid role: {new_role}")
    
    user = get_user(user_id)
    if not user:
        raise ValueError(f"User not found: {user_id}")
    
    old_role = user["role"]
    
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        cur.execute("UPDATE users SET role = ? WHERE user_id = ?", (new_role, user_id))
        
        # Audit event (critical: role change)
        _insert_audit_log(
            conn,
            tenant_id=user["tenant_id"],
            actor_id=actor_id,
            event_type="user_role_changed",
            target=user_id,
            details={"old_role": old_role, "new_role": new_role}
        )
        
        conn.commit()
        conn.close()
        
        logger.warning(f"User role changed: {user_id} {old_role} -> {new_role} by {actor_id}")
        
        return {**user, "role": new_role}


# ============================================================================
# API KEY MANAGEMENT
# ============================================================================

def generate_api_key(
    tenant_id: str,
    user_id: str,
    scope: str,
    expires_in_days: int = 90,
    description: str = "",
    actor_id: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generate a new API key for a user.
    
    Key characteristics:
    - Secret is returned only once (never stored plaintext)
    - Secret hash stored in database (bcrypt)
    - Keys auto-expire after expires_in_days
    - Keys can be revoked immediately
    
    Args:
        tenant_id: Tenant that owns this key
        user_id: User that created/owns this key
        scope: Permission scope (validate-only, admin, read-metrics)
        expires_in_days: TTL in days (default 90)
    
    Returns:
        {"api_key": "...", "key_id": "...", "expires_at": "..."}
        
        WARNING: api_key is never returned again. Client must store it securely.
    """
    # Validate scope
    if scope not in [s.value for s in APIKeyScope]:
        raise ValueError(f"Invalid scope: {scope}")
    
    # Generate 32-byte random secret (base64-url encoded = 43 chars)
    api_key = secrets.token_urlsafe(32)
    key_id = str(uuid4())
    api_key_digest = _api_key_digest(api_key)
    
    # Hash secret with bcrypt (cost=12 = slow intentional)
    secret_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt(rounds=12))
    
    now = datetime.utcnow()
    expires_at = (now + timedelta(days=expires_in_days)).isoformat()
    
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        cur.execute(
            """
            INSERT INTO api_keys (
                key_id, tenant_id, user_id, secret_hash, api_key_digest, scope,
                status, expires_at, created_at, usage_count
            )
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, 0)
            """,
            (key_id, tenant_id, user_id, secret_hash.decode(), api_key_digest, scope, expires_at, now.isoformat())
        )
        
        # Audit event
        _insert_audit_log(
            conn,
            tenant_id=tenant_id,
            actor_id=actor_id or user_id,
            event_type="api_key_generated",
            target=key_id,
            details={"scope": scope, "expires_in_days": expires_in_days}
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"API key generated: {key_id} for {user_id} (scope={scope})")
        
        # Return plaintext secret ONLY ONCE
        return {
            "api_key": api_key,
            "key_id": key_id,
            "expires_at": expires_at,
            "scope": scope,
            "warning": "SAVE THIS KEY SECURELY. YOU WILL NOT SEE IT AGAIN."
        }


def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Validate an API key and return its metadata.
    
    Checks:
    - Key exists and is not revoked
    - Key has not expired
    - Returns: key_id, tenant_id, user_id, scope, usage_count
    
    Args:
        api_key: Plaintext API key (from Authorization header)
    
    Returns:
        Key metadata if valid, None if invalid
    """
    key_digest = _api_key_digest(api_key)
    now = datetime.utcnow()

    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT key_id, tenant_id, user_id, secret_hash, api_key_digest, scope, expires_at, status
            FROM api_keys
            WHERE status = 'active' AND api_key_digest = ?
            LIMIT 1
            """,
            (key_digest,),
        )
        row = cur.fetchone()

        stored_hash = _DUMMY_API_KEY_HASH
        digest_match = False
        if row is not None:
            stored_hash = row["secret_hash"].encode() if isinstance(row["secret_hash"], str) else row["secret_hash"]
            digest_match = hmac.compare_digest(row["api_key_digest"] or "", key_digest)

        secret_match = bcrypt.checkpw(api_key.encode(), stored_hash)
        if row is not None and digest_match and secret_match:
            expires_at = datetime.fromisoformat(row["expires_at"])
            if expires_at < now:
                conn.close()
                logger.warning(f"Key expired: {row['key_id']}")
                return None

            cur.execute(
                "UPDATE api_keys SET last_used_at = ?, usage_count = MIN(usage_count + 1, 9223372036854775807) WHERE key_id = ?",
                (now.isoformat(), row["key_id"])
            )
            conn.commit()
            conn.close()
            return {
                "key_id": row["key_id"],
                "tenant_id": row["tenant_id"],
                "user_id": row["user_id"],
                "scope": row["scope"]
            }

        cur.execute(
            """
            SELECT key_id, tenant_id, user_id, secret_hash, scope, expires_at
            FROM api_keys
            WHERE status = 'active' AND api_key_digest IS NULL
            """
        )
        legacy_rows = cur.fetchall()
        for legacy_row in legacy_rows:
            legacy_hash = legacy_row["secret_hash"].encode() if isinstance(legacy_row["secret_hash"], str) else legacy_row["secret_hash"]
            if not bcrypt.checkpw(api_key.encode(), legacy_hash):
                continue

            expires_at = datetime.fromisoformat(legacy_row["expires_at"])
            if expires_at < now:
                conn.close()
                logger.warning(f"Key expired: {legacy_row['key_id']}")
                return None

            cur.execute(
                """
                UPDATE api_keys
                SET api_key_digest = ?, last_used_at = ?, usage_count = MIN(usage_count + 1, 9223372036854775807)
                WHERE key_id = ?
                """,
                (key_digest, now.isoformat(), legacy_row["key_id"])
            )
            conn.commit()
            conn.close()
            return {
                "key_id": legacy_row["key_id"],
                "tenant_id": legacy_row["tenant_id"],
                "user_id": legacy_row["user_id"],
                "scope": legacy_row["scope"]
            }

        conn.close()
    
    return None


def revoke_api_key(key_id: str, actor_id: Optional[str] = None) -> bool:
    """
    Immediately revoke an API key.
    
    Args:
        key_id: Key to revoke
        actor_id: Who made this request
    
    Returns:
        True if successful
    """
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        # Get key before revoking (for audit)
        cur.execute("SELECT * FROM api_keys WHERE key_id = ?", (key_id,))
        key = cur.fetchone()
        
        if not key:
            conn.close()
            raise ValueError(f"Key not found: {key_id}")
        
        cur.execute("UPDATE api_keys SET status = 'revoked' WHERE key_id = ?", (key_id,))
        
        # Audit event (critical: key revocation)
        _insert_audit_log(
            conn,
            tenant_id=key["tenant_id"],
            actor_id=actor_id,
            event_type="api_key_revoked",
            target=key_id,
            details={}
        )
        
        conn.commit()
        conn.close()
        
        logger.warning(f"API key revoked: {key_id} by {actor_id}")
        
        return True


def list_api_keys(tenant_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List API keys (secret_hash not returned for security).
    
    Args:
        tenant_id: Tenant filter
        user_id: Optional user filter
    
    Returns:
        List of key metadata (without secret_hash)
    """
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        if user_id:
            cur.execute(
                """
                SELECT key_id, tenant_id, user_id, scope, status, expires_at, 
                       created_at, last_used_at, usage_count
                FROM api_keys
                WHERE tenant_id = ? AND user_id = ?
                ORDER BY created_at DESC
                """,
                (tenant_id, user_id)
            )
        else:
            cur.execute(
                """
                SELECT key_id, tenant_id, user_id, scope, status, expires_at, 
                       created_at, last_used_at, usage_count
                FROM api_keys
                WHERE tenant_id = ?
                ORDER BY created_at DESC
                """,
                (tenant_id,)
            )
        
        rows = cur.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


# ============================================================================
# AUDIT LOGGING (Immutable History)
# ============================================================================

def _insert_audit_log(
    conn: sqlite3.Connection,
    tenant_id: str,
    event_type: str,
    target: str,
    details: Dict[str, Any],
    actor_id: Optional[str] = None
) -> None:
    """
    Insert immutable audit log entry with hash chaining.
    
    Each entry includes hash of previous entry to prevent tampering.
    """
    cur = conn.cursor()
    
    # Get hash of last entry
    cur.execute(
        "SELECT event_hash FROM identity_audit_log WHERE tenant_id = ? ORDER BY audit_id DESC LIMIT 1",
        (tenant_id,)
    )
    last_row = cur.fetchone()
    prev_hash = last_row["event_hash"] if last_row else "0" * 64
    
    # Create this entry's hash
    now = datetime.utcnow().isoformat()
    entry_content = json.dumps({
        "tenant_id": tenant_id,
        "actor_id": actor_id,
        "event_type": event_type,
        "target": target,
        "details": details,
        "created_at": now,
        "prev_hash": prev_hash
    }, sort_keys=True)
    
    event_hash = hashlib.sha256(entry_content.encode()).hexdigest()
    
    cur.execute(
        """
        INSERT INTO identity_audit_log (
            tenant_id, actor_id, event_type, target, details_json, prev_hash, event_hash, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (tenant_id, actor_id, event_type, target, json.dumps(details), prev_hash, event_hash, now)
    )


def list_audit_log(
    tenant_id: str,
    event_type: Optional[str] = None,
    days_back: int = 90
) -> List[Dict[str, Any]]:
    """
    Retrieve audit log for a tenant.
    
    Args:
        tenant_id: Tenant to query
        event_type: Optional filter (e.g., "api_key_generated")
        days_back: How far back to query
    
    Returns:
        List of audit events (most recent first)
    """
    cutoff = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
    
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        if event_type:
            cur.execute(
                """
                SELECT * FROM identity_audit_log
                WHERE tenant_id = ? AND event_type = ? AND created_at > ?
                ORDER BY created_at DESC
                LIMIT 10000
                """,
                (tenant_id, event_type, cutoff)
            )
        else:
            cur.execute(
                """
                SELECT * FROM identity_audit_log
                WHERE tenant_id = ? AND created_at > ?
                ORDER BY created_at DESC
                LIMIT 10000
                """,
                (tenant_id, cutoff)
            )
        
        rows = cur.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            result.append({
                "audit_id": row["audit_id"],
                "event_type": row["event_type"],
                "target": row["target"],
                "actor_id": row["actor_id"],
                "details": json.loads(row["details_json"]),
                "created_at": row["created_at"],
                "prev_hash": row["prev_hash"],
                "event_hash": row["event_hash"]
            })
        
        return result


def verify_audit_chain(tenant_id: str) -> bool:
    """
    Verify audit log chain integrity (detect tampering).
    
    Returns:
        True if chain is unbroken, False if tampered
    """
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT * FROM identity_audit_log WHERE tenant_id = ? ORDER BY audit_id ASC",
            (tenant_id,)
        )
        
        rows = cur.fetchall()
        conn.close()
        
        prev_hash = "0" * 64
        
        for row in rows:
            # Verify that stored prev_hash matches actual previous hash
            if row["prev_hash"] != prev_hash:
                logger.error(f"Audit chain broken at {row['audit_id']}")
                return False
            
            # Verify current hash by recomputing
            entry_content = json.dumps({
                "tenant_id": row["tenant_id"],
                "actor_id": row["actor_id"],
                "event_type": row["event_type"],
                "target": row["target"],
                "details": json.loads(row["details_json"]),
                "created_at": row["created_at"],
                "prev_hash": prev_hash
            }, sort_keys=True)
            
            computed_hash = hashlib.sha256(entry_content.encode()).hexdigest()
            
            if computed_hash != row["event_hash"]:
                logger.error(f"Audit entry tampered: {row['audit_id']}")
                return False
            
            prev_hash = row["event_hash"]
        
        return True


# ============================================================================
# AUTHORIZATION CHECKS
# ============================================================================

def has_permission(user_id: str, action: str, resource: str = "all") -> bool:
    """
    Check if user has permission for action on resource.
    
    Args:
        user_id: User to check
        action: Action (e.g., "validate", "manage_config")
        resource: Resource type (e.g., "all", "own")
    
    Returns:
        True if authorized
    """
    user = get_user(user_id)
    if not user:
        return False
    
    role = user["role"]
    
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        cur.execute(
            """
            SELECT * FROM role_permissions
            WHERE role = ? AND action = ? AND (resource = 'all' OR resource = ?)
            """,
            (role, action, resource)
        )
        
        result = cur.fetchone()
        conn.close()
        
        return result is not None


if __name__ == "__main__":
    # Example usage
    init_onboarding_db()
    
    # Create tenant
    tenant = create_tenant("Acme Trading Fund", "acmetrading.com", support_tier="premium")
    print(f"Created tenant: {tenant['tenant_id']}")
    
    # Add admin user
    admin = create_user(tenant["tenant_id"], "admin@acmetrading.com", "admin")
    print(f"Created admin user: {admin['user_id']}")
    
    # Generate API key
    key = generate_api_key(tenant["tenant_id"], admin["user_id"], "admin", expires_in_days=90)
    print(f"Generated API key: {key['key_id']}")
    print(f"Secret (save securely): {key['api_key']}")
    
    # Validate key
    validated = validate_api_key(key["api_key"])
    print(f"Key validation: {validated}")
    
    # List audit log
    audit = list_audit_log(tenant["tenant_id"])
    print(f"Audit events: {len(audit)}")
    for event in audit[:3]:
        print(f"  - {event['event_type']}: {event['target']}")
    
    # Verify chain integrity
    chain_ok = verify_audit_chain(tenant["tenant_id"])
    print(f"Audit chain integrity: {chain_ok}")
