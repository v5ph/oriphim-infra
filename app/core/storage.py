from __future__ import annotations

import json
import os
import sqlite3
import threading
import hashlib
from datetime import datetime, timedelta, timezone
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


def _snapshot_cache_key(tenant_id: Optional[str], agent_id: str) -> str:
    return f"{tenant_id or 'public'}:{agent_id}"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _fingerprint_payload(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def _minute_bucket(ts: Optional[datetime] = None) -> str:
    current = ts or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    else:
        current = current.astimezone(timezone.utc)
    return current.replace(second=0, microsecond=0).isoformat()


def _get_table_columns(cur: sqlite3.Cursor, table_name: str) -> set[str]:
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def _ensure_column(cur: sqlite3.Cursor, table_name: str, column_name: str, definition: str) -> None:
    if column_name not in _get_table_columns(cur, table_name):
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def _parse_execution_decision_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "decision_id": row["decision_id"],
        "tenant_id": row["tenant_id"],
        "agent_id": row["agent_id"],
        "decision": row["decision"],
        "reason": row["reason"],
        "triggered_controls": json.loads(row["triggered_controls_json"]),
        "order": json.loads(row["order_json"]),
        "account": json.loads(row["account_json"]),
        "policy": json.loads(row["policy_json"]),
        "modified_order": json.loads(row["modified_order_json"]) if row["modified_order_json"] else None,
        "idempotency_key": row["idempotency_key"],
        "request_fingerprint": row["request_fingerprint"],
        "created_at": row["created_at"],
    }


def _parse_simulation_run_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "simulation_id": row["simulation_id"],
        "tenant_id": row["tenant_id"],
        "strategy_name": row["strategy_name"],
        "request": json.loads(row["request_json"]),
        "summary": json.loads(row["summary_json"]),
        "policy_blocks": json.loads(row["policy_blocks_json"]),
        "timeline": json.loads(row["timeline_json"]),
        "idempotency_key": row["idempotency_key"],
        "request_fingerprint": row["request_fingerprint"],
        "created_at": row["created_at"],
    }


def _insert_audit_event_with_cursor(
    cur: sqlite3.Cursor,
    request_id: str,
    tenant_id: Optional[str],
    agent_id: Optional[str],
    event_type: str,
    violations: List[str],
    regulatory_articles: List[str],
    message: str,
) -> int:
    if tenant_id is None:
        cur.execute(
            "SELECT event_hash FROM audit_log WHERE tenant_id IS NULL ORDER BY audit_id DESC LIMIT 1"
        )
    else:
        cur.execute(
            "SELECT event_hash FROM audit_log WHERE tenant_id = ? ORDER BY audit_id DESC LIMIT 1",
            (tenant_id,),
        )

    prev_row = cur.fetchone()
    prev_hash = prev_row["event_hash"] if prev_row else "0" * 64
    event_data = {
        "request_id": request_id,
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "event_type": event_type,
        "violations": violations,
        "regulatory_articles": regulatory_articles,
        "message": message,
    }
    event_hash = hashlib.sha256((prev_hash + _stable_json(event_data)).encode("utf-8")).hexdigest()
    cur.execute(
        """
        INSERT INTO audit_log
        (request_id, tenant_id, agent_id, event_type, violations_json, regulatory_articles_json, message, prev_hash, event_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_id,
            tenant_id,
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
    return int(cur.lastrowid)


def _get_encryption_key() -> Optional[str]:
    """Get database encryption key from environment.
    
    Validates key format before using in PRAGMA statement.
    Only accepts 64-char hex strings to prevent SQL injection.
    """
    key = os.getenv("DATABASE_ENCRYPTION_KEY")
    if not key or len(key) != 64:
        return None
    
    # Validate hex-only characters to prevent injection
    if not all(c in "0123456789abcdefABCDEF" for c in key):
        raise ValueError(f"Invalid DATABASE_ENCRYPTION_KEY format: must be 64 hex characters")
    
    # Safe format: PRAGMA key uses hex string literal
    return f'"x\'{key}\'"'


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
        conn = None
        try:
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
            _ensure_column(cur, "requests", "tenant_id", "TEXT")

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
            _ensure_column(cur, "validation_results", "tenant_id", "TEXT")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT,
                    tenant_id TEXT,
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
            _ensure_column(cur, "audit_log", "tenant_id", "TEXT")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_log(agent_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_log(tenant_id)")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS state_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT,
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
            _ensure_column(cur, "state_snapshots", "tenant_id", "TEXT")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_agent_valid ON state_snapshots(agent_id, valid)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_agent_created ON state_snapshots(agent_id, created_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_tenant_agent_valid ON state_snapshots(tenant_id, agent_id, valid)")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS execution_decisions (
                    decision_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    agent_id TEXT,
                    decision TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    triggered_controls_json TEXT NOT NULL,
                    order_json TEXT NOT NULL,
                    account_json TEXT NOT NULL,
                    policy_json TEXT NOT NULL,
                    modified_order_json TEXT,
                    idempotency_key TEXT,
                    request_fingerprint TEXT,
                    created_at TEXT
                )
                """
            )
            _ensure_column(cur, "execution_decisions", "idempotency_key", "TEXT")
            _ensure_column(cur, "execution_decisions", "request_fingerprint", "TEXT")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_exec_decisions_tenant ON execution_decisions(tenant_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_exec_decisions_created ON execution_decisions(created_at)")
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_exec_decisions_tenant_idempotency ON execution_decisions(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL"
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS pre_trade_frequency_windows (
                    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    bucket_start TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_pre_trade_frequency_tenant_idempotency ON pre_trade_frequency_windows(tenant_id, idempotency_key)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_pre_trade_frequency_bucket ON pre_trade_frequency_windows(tenant_id, agent_id, bucket_start)"
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS simulation_runs (
                    simulation_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    request_json TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    policy_blocks_json TEXT NOT NULL,
                    timeline_json TEXT NOT NULL,
                    idempotency_key TEXT,
                    request_fingerprint TEXT,
                    created_at TEXT
                )
                """
            )
            _ensure_column(cur, "simulation_runs", "idempotency_key", "TEXT")
            _ensure_column(cur, "simulation_runs", "request_fingerprint", "TEXT")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sim_runs_tenant ON simulation_runs(tenant_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sim_runs_created ON simulation_runs(created_at)")
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_sim_runs_tenant_idempotency ON simulation_runs(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL"
            )

            conn.commit()
        finally:
            if conn is not None:
                conn.close()


def insert_request(
    request_id: str,
    agent_id: Optional[str],
    intent: Optional[str],
    desired_state: Optional[str],
    samples: List[str],
    payload: Dict[str, Any],
    tenant_id: Optional[str] = None,
) -> None:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO requests
            (request_id, tenant_id, agent_id, intent, desired_state, samples_json, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                tenant_id,
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
    tenant_id: Optional[str] = None,
) -> None:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO validation_results
            (request_id, tenant_id, status_code, action, divergence_score, violations_json, confidence_json,
             severity_json, drift_json, recommendation, context_reset, latency_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                tenant_id,
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


def get_validation_result(request_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        if tenant_id is not None:
            cur.execute(
                "SELECT * FROM validation_results WHERE request_id = ? AND tenant_id = ?",
                (request_id, tenant_id),
            )
        else:
            cur.execute(
                "SELECT * FROM validation_results WHERE request_id = ?",
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
    tenant_id: Optional[str],
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
        audit_id = _insert_audit_event_with_cursor(
            cur=cur,
            request_id=request_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            event_type=event_type,
            violations=violations,
            regulatory_articles=regulatory_articles,
            message=message,
        )
        conn.commit()
        conn.close()
        return int(audit_id)


def list_audit_events(tenant_id: str, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        if agent_id:
            cur.execute(
                """
                SELECT * FROM audit_log WHERE tenant_id = ? AND agent_id = ? ORDER BY audit_id DESC
                """,
                (tenant_id, agent_id),
            )
        else:
            cur.execute("SELECT * FROM audit_log WHERE tenant_id = ? ORDER BY audit_id DESC", (tenant_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "audit_id": row["audit_id"],
                "request_id": row["request_id"],
                "tenant_id": row["tenant_id"],
                "agent_id": row["agent_id"],
                "event_type": row["event_type"],
                "violations": json.loads(row["violations_json"]),
                "regulatory_articles": json.loads(row["regulatory_articles_json"]),
                "message": row["message"],
                "prev_hash": row["prev_hash"],
                "chain_hash": row["event_hash"],
                "event_hash": row["event_hash"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


def reserve_pre_trade_frequency_slot(
    tenant_id: str,
    agent_id: Optional[str],
    idempotency_key: str,
    bucket_start: Optional[str] = None,
) -> int:
    effective_agent_id = agent_id or "__tenant__"
    current_bucket = bucket_start or _minute_bucket()
    retention_cutoff = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()

    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM pre_trade_frequency_windows WHERE created_at < ?",
            (retention_cutoff,),
        )
        cur.execute(
            "SELECT bucket_start FROM pre_trade_frequency_windows WHERE tenant_id = ? AND idempotency_key = ?",
            (tenant_id, idempotency_key),
        )
        existing_row = cur.fetchone()
        bucket_to_count = current_bucket
        if existing_row is None:
            cur.execute(
                """
                INSERT INTO pre_trade_frequency_windows
                (tenant_id, agent_id, bucket_start, idempotency_key, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tenant_id, effective_agent_id, current_bucket, idempotency_key, datetime.now(timezone.utc).isoformat()),
            )
        else:
            bucket_to_count = existing_row["bucket_start"]

        cur.execute(
            """
            SELECT COUNT(*) AS reservation_count
            FROM pre_trade_frequency_windows
            WHERE tenant_id = ? AND agent_id = ? AND bucket_start = ?
            """,
            (tenant_id, effective_agent_id, bucket_to_count),
        )
        reservation_count = int(cur.fetchone()["reservation_count"])
        conn.commit()
        conn.close()
        return reservation_count


def verify_runtime_audit_chain(tenant_id: str) -> bool:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM audit_log WHERE tenant_id = ? ORDER BY audit_id ASC",
            (tenant_id,),
        )
        rows = cur.fetchall()
        conn.close()

    prev_hash = "0" * 64
    for row in rows:
        if row["prev_hash"] != prev_hash:
            return False

        event_data = {
            "request_id": row["request_id"],
            "tenant_id": row["tenant_id"],
            "agent_id": row["agent_id"],
            "event_type": row["event_type"],
            "violations": json.loads(row["violations_json"]),
            "regulatory_articles": json.loads(row["regulatory_articles_json"]),
            "message": row["message"],
        }
        expected_hash = hashlib.sha256((prev_hash + _stable_json(event_data)).encode("utf-8")).hexdigest()
        if row["event_hash"] != expected_hash:
            return False
        prev_hash = row["event_hash"]

    return True


def insert_state_snapshot(
    tenant_id: Optional[str],
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
            (tenant_id, agent_id, request_id, system_prompt, context_json, variables_json, valid, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tenant_id,
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
        cache_key = _snapshot_cache_key(tenant_id, agent_id)
        if cache_key in _SNAPSHOT_MEMOIZER:
            del _SNAPSHOT_MEMOIZER[cache_key]
        
        return int(snapshot_id)


def get_latest_valid_snapshot(agent_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    """Fast-lane retrieval with in-memory memoization. Target: <100ms latency.
    
    Two-tier lookup under lock to prevent TOCTOU race:
    1. Check hot cache (_SNAPSHOT_MEMOIZER) → O(1) instant
    2. Query DB only if cache miss → O(log n) with index
    """
    with _LOCK:
        cache_key = _snapshot_cache_key(tenant_id, agent_id)
        # Check cache first within lock
        if cache_key in _SNAPSHOT_MEMOIZER:
            return _SNAPSHOT_MEMOIZER[cache_key]
        
        # Query DB if cache miss
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM state_snapshots
            WHERE tenant_id = ? AND agent_id = ? AND valid = 1
            ORDER BY snapshot_id DESC LIMIT 1
            """,
            (tenant_id, agent_id),
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
        _SNAPSHOT_MEMOIZER[cache_key] = result
        return result


def insert_execution_decision(
    decision_id: str,
    tenant_id: str,
    agent_id: Optional[str],
    decision: str,
    reason: str,
    triggered_controls: List[str],
    order: Dict[str, Any],
    account: Dict[str, Any],
    policy: Dict[str, Any],
    modified_order: Optional[Dict[str, Any]],
    idempotency_key: Optional[str],
) -> Dict[str, Any]:
    request_payload = {
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "decision": decision,
        "reason": reason,
        "triggered_controls": triggered_controls,
        "order": order,
        "account": account,
        "policy": policy,
        "modified_order": modified_order,
    }
    request_fingerprint = _fingerprint_payload(request_payload)

    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        if idempotency_key:
            cur.execute(
                "SELECT * FROM execution_decisions WHERE tenant_id = ? AND idempotency_key = ?",
                (tenant_id, idempotency_key),
            )
            existing_row = cur.fetchone()
            if existing_row is not None:
                conn.close()
                existing_decision = _parse_execution_decision_row(existing_row)
                if existing_decision["request_fingerprint"] != request_fingerprint:
                    raise ValueError("Idempotency key already used with a different pre-trade request")
                return existing_decision

        created_at = datetime.utcnow().isoformat()
        cur.execute(
            """
            INSERT INTO execution_decisions
            (decision_id, tenant_id, agent_id, decision, reason, triggered_controls_json,
             order_json, account_json, policy_json, modified_order_json, idempotency_key, request_fingerprint, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                tenant_id,
                agent_id,
                decision,
                reason,
                json.dumps(triggered_controls),
                json.dumps(order),
                json.dumps(account),
                json.dumps(policy),
                json.dumps(modified_order) if modified_order else None,
                idempotency_key,
                request_fingerprint,
                created_at,
            ),
        )
        _insert_audit_event_with_cursor(
            cur=cur,
            request_id=decision_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            event_type=f"PRE_TRADE_{decision}",
            violations=triggered_controls,
            regulatory_articles=[],
            message=f"Pre-trade decision {decision}: {reason}",
        )
        conn.commit()
        conn.close()
        return {
            "decision_id": decision_id,
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "decision": decision,
            "reason": reason,
            "triggered_controls": triggered_controls,
            "order": order,
            "account": account,
            "policy": policy,
            "modified_order": modified_order,
            "idempotency_key": idempotency_key,
            "request_fingerprint": request_fingerprint,
            "created_at": created_at,
        }


def get_execution_decision(decision_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM execution_decisions WHERE decision_id = ? AND tenant_id = ?",
            (decision_id, tenant_id),
        )
        row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        return _parse_execution_decision_row(row)


def insert_simulation_run(
    simulation_id: str,
    tenant_id: str,
    strategy_name: str,
    request_payload: Dict[str, Any],
    summary: Dict[str, Any],
    policy_blocks: List[str],
    timeline: List[Dict[str, Any]],
    idempotency_key: Optional[str],
) -> Dict[str, Any]:
    request_fingerprint = _fingerprint_payload(
        {
            "tenant_id": tenant_id,
            "strategy_name": strategy_name,
            "request": request_payload,
        }
    )

    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        if idempotency_key:
            cur.execute(
                "SELECT * FROM simulation_runs WHERE tenant_id = ? AND idempotency_key = ?",
                (tenant_id, idempotency_key),
            )
            existing_row = cur.fetchone()
            if existing_row is not None:
                conn.close()
                existing_run = _parse_simulation_run_row(existing_row)
                if existing_run["request_fingerprint"] != request_fingerprint:
                    raise ValueError("Idempotency key already used with a different simulation request")
                return existing_run

        created_at = datetime.utcnow().isoformat()
        cur.execute(
            """
            INSERT INTO simulation_runs
            (simulation_id, tenant_id, strategy_name, request_json, summary_json, policy_blocks_json, timeline_json, idempotency_key, request_fingerprint, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                simulation_id,
                tenant_id,
                strategy_name,
                json.dumps(request_payload),
                json.dumps(summary),
                json.dumps(policy_blocks),
                json.dumps(timeline),
                idempotency_key,
                request_fingerprint,
                created_at,
            ),
        )
        _insert_audit_event_with_cursor(
            cur=cur,
            request_id=simulation_id,
            tenant_id=tenant_id,
            agent_id=None,
            event_type="SIMULATION_COMPLETED",
            violations=policy_blocks,
            regulatory_articles=[],
            message=f"Simulation completed for strategy {strategy_name}",
        )
        conn.commit()
        conn.close()
        return {
            "simulation_id": simulation_id,
            "tenant_id": tenant_id,
            "strategy_name": strategy_name,
            "request": request_payload,
            "summary": summary,
            "policy_blocks": policy_blocks,
            "timeline": timeline,
            "idempotency_key": idempotency_key,
            "request_fingerprint": request_fingerprint,
            "created_at": created_at,
        }


def get_simulation_run(simulation_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM simulation_runs WHERE simulation_id = ? AND tenant_id = ?",
            (simulation_id, tenant_id),
        )
        row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        return _parse_simulation_run_row(row)


init_db()
