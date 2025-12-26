# db.py
import sqlite3
import json
import threading
from typing import Any, Dict, List, Optional

from base_Service import BaseService


class DatabaseAccess(BaseService):
    """
    SQLite DB wrapper.
    Stores:
      - raw telemetry JSON
      - derived features (used_memory, used_storage, cpuusage, temperature)
      - AI outputs (health_status, reason)
    """
    def __init__(self, db_path: str = "plc_health.db"):
        super().__init__("DatabaseAccess")
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None

    def start(self) -> None:
        super().start()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def stop(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
        super().stop()

    def _init_schema(self) -> None:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                gateway TEXT,
                siteid TEXT,
                topic TEXT,
                raw_json TEXT NOT NULL,

                used_memory REAL,
                used_storage REAL,
                cpuusage REAL,
                temperature REAL,

                health_status TEXT,
                reason TEXT
            );
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_site_ts ON telemetry(siteid, ts);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_gateway_ts ON telemetry(gateway, ts);")
            self._conn.commit()

    def insert_telemetry(
        self,
        ts: int,
        gateway: str,
        siteid: str,
        topic: str,
        raw: Dict[str, Any],
        used_memory: float | None,
        used_storage: float | None,
        cpuusage: float | None,
        temperature: float | None,
        health_status: str | None,
        reason: str | None,
    ) -> None:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                INSERT INTO telemetry
                (ts, gateway, siteid, topic, raw_json,
                 used_memory, used_storage, cpuusage, temperature,
                 health_status, reason)
                VALUES (?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?)
            """, (
                ts, gateway, siteid, topic, json.dumps(raw),
                used_memory, used_storage, cpuusage, temperature,
                health_status, reason
            ))
            self._conn.commit()

    def get_latest_per_device(self, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Latest row per siteid (device).
        """
        assert self._conn is not None
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                SELECT t1.*
                FROM telemetry t1
                INNER JOIN (
                    SELECT siteid, MAX(ts) AS max_ts
                    FROM telemetry
                    WHERE siteid IS NOT NULL
                    GROUP BY siteid
                ) t2
                ON t1.siteid = t2.siteid AND t1.ts = t2.max_ts
                ORDER BY t1.ts DESC
                LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_history(self, siteid: str, limit: int = 2000) -> List[Dict[str, Any]]:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                SELECT *
                FROM telemetry
                WHERE siteid = ?
                ORDER BY ts DESC
                LIMIT ?
            """, (siteid, limit))
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def get_latest_raw(self, siteid: str) -> Optional[Dict[str, Any]]:
        assert self._conn is not None
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("""
                SELECT raw_json
                FROM telemetry
                WHERE siteid = ?
                ORDER BY ts DESC
                LIMIT 1
            """, (siteid,))
            row = cur.fetchone()
        if not row:
            return None
        return json.loads(row["raw_json"])
