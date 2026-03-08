from __future__ import annotations

import json
import os
import sqlite3
import threading
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
_SNAPSHOT_MEMOIZER: Dict[str, Dict[str, Any]] = {}  # agent_id -> latest valid snapshot (hot cache)


def _get_encryption_key() -> Optional[str]:
    """Get database encryption key from environment."""
    key = os.getenv("DATABASE_ENCRYPTION_KEY")
    if key and len(key) == 64:
        return f'"x\'{key}\'"'
    return None


def _connect() -> sqlite3.Connection:
    """
    Create database connection with optional encryption.
    
    If DATABASE_ENCRYPTION_KEY is set and sqlcipher3 available, uses encrypted connection.
    Otherwise falls back to standard SQLite (logs warning).
    """
    encryption_key = _get_encryption_key()
    db_path = _get_db_path()
    
    if encryption_key and ENCRYPTION_AVAILABLE:
        try:
            conn = sqlcipher.connect(db_path, check_same_thread=False)
            conn.execute(f"PRAGMA key = {encryption_key}")
            conn.execute("PRAGMA cipher_page_size = 4096")
            conn.execute("PRAGMA kdf_iter = 256000")  # PBKDF2 iterations
            conn.execute("SELECT 1")
            conn.row_factory = sqlcipher.Row
            return conn
        except Exception as e:
            import logging
            logging.warning(
                "SQLCipher connection failed for DB path '%s' (error: %s). "
                "Falling back to standard SQLite. "
                "If encryption is required, delete the DB and regenerate .env keys.",
                db_path,
                str(e)
            )
            # Fall through to standard SQLite
    
    # Standard SQLite fallback
    if encryption_key and not ENCRYPTION_AVAILABLE:
        import logging
        logging.warning(
            "DATABASE_ENCRYPTION_KEY set but sqlcipher3 not available. "
            "Install with: pip install sqlcipher3. "
            "Using UNENCRYPTED database."
        )
    
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _LOCK:
        conn = _connect()
        if conn is None:
            raise RuntimeError(
                "Database connection failed. Check DATABASE_ENCRYPTION_KEY in .env "
                "or delete .watcher_demo.db and regenerate keys with: "
                "python scripts/setup/generate_env.py --force"
            )
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                request_id TEXT PRIMARY KEY,
                agent_id TEXT,
                intent TEXT,
                desired_state TEXT,
                samples_json TEXT,
                payload_json TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS validation_results (
                request_id TEXT PRIMARY KEY,
                status_code INTEGER,
                action TEXT,
                divergence_score REAL,
                violations_json TEXT,
                confidence_json TEXT,
                severity_json TEXT,
                drift_json TEXT,
                recommendation TEXT,
                context_reset INTEGER,
                latency_ms REAL,
                created_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                agent_id TEXT,
                event_type TEXT,
                violations_json TEXT,
                regulatory_articles_json TEXT,
                message TEXT,
                prev_hash TEXT,
                event_hash TEXT,
                created_at TEXT
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_log(agent_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at)")
        
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS state_snapshots (
                snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                request_id TEXT,
                system_prompt TEXT,
                context_json TEXT,
                variables_json TEXT,
                valid INTEGER,
                created_at TEXT
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_agent_valid ON state_snapshots(agent_id, valid)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_agent_created ON state_snapshots(agent_id, created_at)")
        
        conn.commit()
        conn.close()


def insert_request(
    request_id: str,
    agent_id: Optional[str],
    intent: Optional[str],
    desired_state: Optional[str],
    samples: List[str],
    payload: Dict[str, Any],
) -> None:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO requests
            (request_id, agent_id, intent, desired_state, samples_json, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                agent_id,
                intent,
                desired_state,
                json.dumps(samples),
                json.dumps(payload),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()


def insert_validation_result(
    request_id: str,
    status_code: int,
    action: str,
    divergence_score: float,
    violations: List[str],
    confidence: Dict[str, Any],
    severity: Dict[str, Any],
    drift: Dict[str, Any],
    recommendation: str,
    context_reset: bool,
    latency_ms: float,
) -> None:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO validation_results
            (request_id, status_code, action, divergence_score, violations_json, confidence_json,
             severity_json, drift_json, recommendation, context_reset, latency_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                status_code,
                action,
                divergence_score,
                json.dumps(violations),
                json.dumps(confidence),
                json.dumps(severity),
                json.dumps(drift),
                recommendation,
                1 if context_reset else 0,
                latency_ms,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        conn.close()


def get_validation_result(request_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM validation_results WHERE request_id = ?
            """,
            (request_id,),
        )
        row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        return {
            "request_id": request_id,
            "status_code": row["status_code"],
            "action": row["action"],
            "divergence_score": row["divergence_score"],
            "violations": json.loads(row["violations_json"]),
            "confidence": json.loads(row["confidence_json"]),
            "severity": json.loads(row["severity_json"]),
            "drift": json.loads(row["drift_json"]),
            "recommendation": row["recommendation"],
            "context_reset": bool(row["context_reset"]),
            "latency_ms": row["latency_ms"],
            "created_at": row["created_at"],
        }


def insert_audit_event(
    request_id: str,
    agent_id: Optional[str],
    event_type: str,
    violations: List[str],
    regulatory_articles: List[str],
    message: str,
) -> int:
    """Insert audit event with hash chaining for cryptographic immutability.
    
    Each event includes prev_hash (chain link) and event_hash (content hash).
    Regulators can verify: hash(prev_hash + event_json) == event_hash
    """
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        
        # Get previous audit event hash for chaining
        cur.execute(
            "SELECT event_hash FROM audit_log WHERE agent_id = ? ORDER BY audit_id DESC LIMIT 1",
            (agent_id,) if agent_id else (None,),
        )
        prev_row = cur.fetchone()
        prev_hash = prev_row["event_hash"] if prev_row else "0" * 64
        
        # Build event JSON for hashing
        event_data = {
            "request_id": request_id,
            "agent_id": agent_id,
            "event_type": event_type,
            "violations": violations,
            "regulatory_articles": regulatory_articles,
            "message": message,
        }
        event_json = json.dumps(event_data, sort_keys=True)
        
        # Hash chain: SHA256(prev_hash + event_json)
        chain_input = (prev_hash + event_json).encode("utf-8")
        event_hash = hashlib.sha256(chain_input).hexdigest()
        
        cur.execute(
            """
            INSERT INTO audit_log
            (request_id, agent_id, event_type, violations_json, regulatory_articles_json, message, prev_hash, event_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                agent_id,
                event_type,
                json.dumps(violations),
                json.dumps(regulatory_articles),
                message,
                prev_hash,
                event_hash,
                datetime.utcnow().isoformat(),
            ),
        )
        audit_id = cur.lastrowid
        conn.commit()
        conn.close()
        return int(audit_id)


def list_audit_events(agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        if agent_id:
            cur.execute(
                """
                SELECT * FROM audit_log WHERE agent_id = ? ORDER BY audit_id DESC
                """,
                (agent_id,),
            )
        else:
            cur.execute("SELECT * FROM audit_log ORDER BY audit_id DESC")
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "audit_id": row["audit_id"],
                "request_id": row["request_id"],
                "agent_id": row["agent_id"],
                "event_type": row["event_type"],
                "violations": json.loads(row["violations_json"]),
                "regulatory_articles": json.loads(row["regulatory_articles_json"]),
                "message": row["message"],
                "prev_hash": row["prev_hash"],
                "chain_hash": row["event_hash"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


def insert_state_snapshot(
    agent_id: str,
    request_id: str,
    system_prompt: str,
    context: Dict[str, Any],
    variables: Dict[str, Any],
    valid: bool,
) -> int:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO state_snapshots
            (agent_id, request_id, system_prompt, context_json, variables_json, valid, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                request_id,
                system_prompt,
                json.dumps(context),
                json.dumps(variables),
                1 if valid else 0,
                datetime.utcnow().isoformat(),
            ),
        )
        snapshot_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        # Invalidate hot cache for this agent (new snapshot is more recent)
        if agent_id in _SNAPSHOT_MEMOIZER:
            del _SNAPSHOT_MEMOIZER[agent_id]
        
        return int(snapshot_id)


def get_latest_valid_snapshot(agent_id: str) -> Optional[Dict[str, Any]]:
    """Fast-lane retrieval with in-memory memoization. Target: <100ms latency.
    
    Two-tier lookup:
    1. Check hot cache (_SNAPSHOT_MEMOIZER) → O(1) instant
    2. Query DB only if cache miss → O(log n) with index
    """
    # Tier 1: Hot cache (already loaded this session)
    if agent_id in _SNAPSHOT_MEMOIZER:
        return _SNAPSHOT_MEMOIZER[agent_id]
    
    # Tier 2: Database lookup with index
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM state_snapshots
            WHERE agent_id = ? AND valid = 1
            ORDER BY snapshot_id DESC LIMIT 1
            """,
            (agent_id,),
        )
        row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        
        result = {
            "snapshot_id": row["snapshot_id"],
            "agent_id": row["agent_id"],
            "request_id": row["request_id"],
            "system_prompt": row["system_prompt"],
            "context": json.loads(row["context_json"]),
            "variables": json.loads(row["variables_json"]),
            "created_at": row["created_at"],
        }
        
        # Populate hot cache for next access
        _SNAPSHOT_MEMOIZER[agent_id] = result
        return result


init_db()
