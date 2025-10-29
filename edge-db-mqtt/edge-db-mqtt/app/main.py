import os, json, hashlib, sqlite3, datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "edge.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "health.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

app = FastAPI(title="Edge Data Access API (SQLite, HTTP + MQTT-ready)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS devices(
            device_key TEXT PRIMARY KEY,
            hardware_type TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mqtt_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_key TEXT NOT NULL,
            topic TEXT NOT NULL,
            event_time TEXT,
            received_at TEXT DEFAULT (datetime('now')),
            payload TEXT NOT NULL,
            dedupe_hash BLOB,
            FOREIGN KEY(device_key) REFERENCES devices(device_key)
        );
    """)
    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_msg_dedupe
        ON mqtt_messages(device_key, topic, event_time, dedupe_hash);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_msg_dev_time
        ON mqtt_messages(device_key, event_time);
    """)
    conn.commit()
    conn.close()

init_db()

def upsert_device(cur, device_key, hw="unknown"):
    cur.execute(
        "INSERT OR IGNORE INTO devices(device_key, hardware_type) VALUES(?, ?)",
        (device_key, hw)
    )

def normalize_to_contract(vendor: dict) -> dict:
    if all(k in vendor for k in ("device_key","event_time","topic","payload")):
        return vendor
    device_key = vendor.get("device") or vendor.get("payload", {}).get("device")
    event_time = vendor.get("creationTime") or vendor.get("ts")
    topic = vendor.get("topic") or vendor.get("sourceTopic") or "unknown"
    version = str(vendor.get("version", "1.0"))
    metrics = (vendor.get("metrics")
               or vendor.get("payload", {}).get("metrics")
               or {})
    return {
        "device_key": device_key,
        "event_time": event_time,
        "topic": topic,
        "payload": {"version": version, "metrics": metrics}
    }

def insert_message(payload_dict: dict):
    payload_dict = normalize_to_contract(payload_dict)
    validate(instance=payload_dict, schema=SCHEMA)

    device_key = payload_dict["device_key"]
    event_time = payload_dict.get("event_time")
    topic = payload_dict.get("topic", "")

    if event_time:
        if isinstance(event_time, str) and event_time.endswith("Z"):
            try:
                dt = datetime.datetime.fromisoformat(event_time.replace("Z","+00:00"))
                event_time = dt.isoformat()
            except Exception:
                pass

    payload_text = json.dumps(payload_dict, sort_keys=True, ensure_ascii=False)
    dedupe_raw = f"{device_key}|{topic}|{event_time}|{payload_text}".encode("utf-8")
    dedupe_hash = hashlib.sha256(dedupe_raw).digest()

    conn = get_conn()
    cur = conn.cursor()
    upsert_device(cur, device_key)
    try:
        cur.execute(
            "INSERT OR IGNORE INTO mqtt_messages(device_key, topic, event_time, payload, dedupe_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            (device_key, topic, event_time, payload_text, dedupe_hash)
        )
        conn.commit()
    finally:
        conn.close()

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/ingest")
async def ingest_http(req: Request):
    try:
        data = await req.json()
    except Exception:
        raise HTTPException(400, "invalid json")
    try:
        insert_message(data)
    except ValidationError as e:
        raise HTTPException(400, f"schema_error: {e.message}")
    except Exception as e:
        raise HTTPException(500, f"ingest_error: {e}")
    return {"status": "ingested"}

@app.get("/devices")
def devices():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.device_key,
               (SELECT MAX(m.event_time) FROM mqtt_messages m WHERE m.device_key = d.device_key) AS last_event
        FROM devices d
        ORDER BY d.device_key;
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/devices/{key}/latest")
def latest(key: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, device_key, topic, event_time, received_at, payload
        FROM mqtt_messages
        WHERE device_key=?
        ORDER BY (event_time IS NULL),
                 COALESCE(event_time, received_at) DESC,
                 id DESC
        LIMIT 1;
    """, (key,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "no data")
    out = dict(row)
    if isinstance(out.get("payload"), str):
        try:
            out["payload"] = json.loads(out["payload"])
        except Exception:
            pass
    return out

@app.get("/devices/{key}/timeseries")
def timeseries(key: str, metric: str, limit: int = 200):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT event_time, payload
        FROM mqtt_messages
        WHERE device_key=?
        ORDER BY event_time DESC, received_at DESC
        LIMIT ?;
    """, (key, limit))
    rows = cur.fetchall()
    conn.close()

    ts = []
    for r in rows:
        try:
            p = json.loads(r["payload"])
            v = p.get("payload", {}).get("metrics", {}).get(metric)
            ts.append({"t": r["event_time"], "v": v})
        except Exception:
            ts.append({"t": r["event_time"], "v": None})
    return ts
