# Edge DB — MQTT Edition (No Docker, SQLite)

This package adds **MQTT ingestion** on top of the HTTP version. It reuses the same DB (SQLite) and read APIs.
You need access to an MQTT broker (company broker or a public one like `test.mosquitto.org:1883` for testing).

## Quickstart
1) Create & activate venv
```bash
python -m venv .venv
# Windows PowerShell
. .\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
```
2) Install deps
```bash
pip install -r app/requirements.txt
```
3) Configure `.env` at the project root (sample below).
4) Run API (port 8000)
```bash
python -m uvicorn app.main:app --reload --port 8000
```
5) In another terminal, run **MQTT Ingestor**
```bash
python app/ingest_mqtt.py
```
6) (Optional) Mock publish to MQTT
```bash
python app/mock_pub_mqtt.py
```

Test endpoints:
- http://localhost:8000/healthz
- http://localhost:8000/devices
- http://localhost:8000/devices/bms-1/latest
- http://localhost:8000/devices/bms-1/timeseries?metric=voltagebank1

## .env sample
```
MQTT_HOST=test.mosquitto.org
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPICS=demo/edge/mqtt_bms/#
MQTT_CLIENT_ID=edge-ingestor

# If you already have a broker:
# MQTT_HOST=<your-broker-host>
# MQTT_PORT=1883
# MQTT_TOPICS=site/edge/+/mqtt_bms/#,site/edge/+/mqtt_environmental/#
```
