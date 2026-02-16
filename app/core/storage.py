from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parents[2] / ".watcher_demo.db"

_LOCK = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH.as_posix(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _LOCK:
        conn = _connect()
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
                created_at TEXT
            )
            """
        )
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
    with _LOCK:
        conn = _connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO audit_log
            (request_id, agent_id, event_type, violations_json, regulatory_articles_json, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                agent_id,
                event_type,
                json.dumps(violations),
                json.dumps(regulatory_articles),
                message,
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
        return int(snapshot_id)


def get_latest_valid_snapshot(agent_id: str) -> Optional[Dict[str, Any]]:
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
        return {
            "snapshot_id": row["snapshot_id"],
            "agent_id": row["agent_id"],
            "request_id": row["request_id"],
            "system_prompt": row["system_prompt"],
            "context": json.loads(row["context_json"]),
            "variables": json.loads(row["variables_json"]),
            "created_at": row["created_at"],
        }


init_db()
