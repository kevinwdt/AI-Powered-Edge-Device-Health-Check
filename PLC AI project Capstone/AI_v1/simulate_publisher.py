# simulate_publisher.py
"""
Simulated MQTT publisher for PLC Group AI-Powered Edge Device Health Check project.

What it does:
- Publishes fake (but realistic-looking) device JSON messages to MQTT topics
- Lets you test: MQTT subscriber -> DB -> AI model -> Web dashboard

Usage:
1) pip install paho-mqtt
2) python simulate_publisher.py

Config:
- Edit BROKER_HOST / BROKER_PORT / USERNAME / PASSWORD / TOPIC_* below.
"""

import json
import time
import random
import uuid
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


# =========================
# MQTT CONFIG (EDIT THESE)
# =========================
BROKER_HOST = "test.mosquitto.org"   # change later to PLC broker
BROKER_PORT = 1883
USERNAME = None                     # set to string if needed
PASSWORD = None                     # set to string if needed
CLIENT_ID = f"sim-publisher-{uuid.uuid4().hex[:8]}"

# Topics (match whatever your subscriber expects)
TOPIC_DIAGNOSTIC = "plc/devices/diagnostic/test"
TOPIC_BMS = "plc/bms"
TOPIC_ENERGY = "plc/energy"
TOPIC_ENV = "plc/environment"

PUBLISH_INTERVAL_SEC = 2            # seconds between publish cycles
QOS = 0
RETAIN = False


# =========================
# SIMULATION CONFIG
# =========================
SITE_IDS = [
    "PH-NCR-02206", "PH-RIZ-01727", "PH-NCR-02466", "PH-NCR-01728",
    "PH-NCR-01461", "PH-NCR-01788", "PH-BUL-01141"
]

GATEWAY_MODELS = [
    "Raspberry Pi Compute Module 4 Rev 1.1",
    "Raspberry Pi 4 Model B Rev 1.5",
]

PRODUCT_MODELS = ["Gateway"]

SOFTWARE_VERSIONS = ["3.7.0v2v1wds1s2S", "3.9.1_epv1wds1S", "3.9.1_epv1wds1s2S"]
HARDWARE_VERSION = "1.4"

TOTAL_MEMORY = 1873.92
STORAGE_TOTAL = 4249.6


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def maybe_null(val, p=0.10):
    """Return None some of the time to simulate NULLs in real data."""
    return None if random.random() < p else val


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def rand_gateway_id() -> str:
    # Your sample gateways look like long hex strings. We'll generate similar.
    return uuid.uuid4().hex[:16]


def simulate_diagnostic(siteid: str, gateway: str, severity: str) -> dict:
    """
    severity: "healthy" | "warning" | "critical"
    Generates diagnostic JSON similar to your CSV fields.
    """
    # base ranges
    cpu = random.gauss(40, 12)
    temp = random.gauss(40, 7)          # assume Celsius for now
    mem_used_pct = random.gauss(45, 12)
    storage_used_pct = random.gauss(35, 15)

    # inject events
    if severity == "warning":
        cpu += random.uniform(15, 30)
        temp += random.uniform(8, 15)
        mem_used_pct += random.uniform(10, 25)
        storage_used_pct += random.uniform(10, 20)

    if severity == "critical":
        cpu += random.uniform(35, 55)
        temp += random.uniform(20, 30)
        mem_used_pct += random.uniform(25, 40)
        storage_used_pct += random.uniform(25, 40)

        # occasional extreme/unusual cases
        # (very low temp sensor glitch, or sudden spike)
        if random.random() < 0.20:
            temp = random.uniform(-15, 5)  # unrealistic low reading (sensor issue / environment extreme)
        if random.random() < 0.20:
            cpu = 100.0                    # pegged CPU
        if random.random() < 0.15:
            mem_used_pct = 99.0            # almost out of memory
        if random.random() < 0.15:
            storage_used_pct = 99.0        # almost out of storage

    cpu = clamp(cpu, 0, 100)
    temp = clamp(temp, -30, 100)
    mem_used_pct = clamp(mem_used_pct, 0, 99)
    storage_used_pct = clamp(storage_used_pct, 0, 99)

    remaining_memory = TOTAL_MEMORY * (1 - mem_used_pct / 100.0)
    remaining_storage = STORAGE_TOTAL * (1 - storage_used_pct / 100.0)

    ethernet_ok = True if random.random() < 0.9 else False
    wifi_ok = True if random.random() < 0.3 else False

    sim1_signal = int(clamp(random.gauss(-65, 8), -115, -40))
    sim2_signal = int(clamp(random.gauss(-72, 10), -115, -40))

    # make connectivity worse during critical sometimes
    if severity == "critical" and random.random() < 0.35:
        ethernet_ok = False
        sim1_signal = int(clamp(sim1_signal + random.uniform(-25, -10), -115, -40))

    # pings (1 good, 0 fail)
    dc1 = 1 if random.random() < (0.92 if severity != "critical" else 0.65) else 0
    dc2 = 1 if random.random() < (0.88 if severity != "critical" else 0.65) else 0

    payload = {
        "time": int(time.time()),
        "unixtime": utc_now_iso(),

        "gateway": gateway,
        "siteid": siteid,

        # core device vitals
        "totalmemory": TOTAL_MEMORY,
        "remainingmemory": maybe_null(round(remaining_memory, 2), p=0.03),
        "storagetotal": STORAGE_TOTAL,
        "remainingstorage": maybe_null(round(remaining_storage, 2), p=0.03),

        "cpucores": 4,
        "cpuusage": maybe_null(round(cpu, 1), p=0.05),
        "cputotalusage": maybe_null(round(clamp(cpu + random.gauss(0, 8), 0, 100), 1), p=0.25),

        # temperatures
        "temperature": maybe_null(round(temp, 1), p=0.10),
        "cputemperature": maybe_null(round(clamp(temp + random.gauss(3, 4), -30, 110), 1), p=0.35),
        "coretemperature": maybe_null(round(clamp(temp + random.gauss(5, 5), -30, 110), 1), p=0.30),

        # storage percent
        "storagepercentage": maybe_null(round(storage_used_pct, 1), p=0.07),
        "memorypercentage": maybe_null(round(mem_used_pct, 1), p=0.08),

        # networking
        "ethernetstatus": ethernet_ok,
        "wifistatus": wifi_ok,
        "ethernetip": "192.168.0.20" if ethernet_ok else None,
        "wifiip": f"169.254.{random.randint(0,255)}.{random.randint(0,255)}" if wifi_ok else None,
        "gatewayip": "192.168.0.1",
        "networkpriority": "eth0",
        "dns": "8.8.8.8\nnameserver 8.8.4.4",

        # identity
        "softwareversion": random.choice(SOFTWARE_VERSIONS),
        "hardwareversion": HARDWARE_VERSION,
        "timezone": 8,
        "uptime": random.randint(500_000, 5_000_000),
        "controlleruptime": random.randint(500_000, 5_000_000),
        "gatewaymodel": random.choice(GATEWAY_MODELS),
        "productmodel": random.choice(PRODUCT_MODELS),

        # SIM
        "numberofsims": 2,
        "sim1status": 1,
        "sim1signalstrength": sim1_signal,
        "sim2status": 1,
        "sim2signalstrength": sim2_signal,
        "simpriority": random.choice([1, 2]),

        # reachability
        "dcplant1ping": dc1,
        "dcplant2ping": dc2,
    }
    return payload


def simulate_bms(device_key: str, severity: str) -> dict:
    # Battery-ish example fields (optional; good for later)
    v = random.uniform(44.0, 52.0)
    a = random.uniform(0.0, 30.0)
    temp = random.uniform(20.0, 50.0)
    soh = random.uniform(70, 100)

    if severity == "critical":
        v = random.uniform(40.0, 45.0)
        a = random.uniform(20.0, 35.0)
        temp = random.uniform(55.0, 85.0)
        soh = random.uniform(55, 75)
    elif severity == "warning":
        temp = random.uniform(45.0, 60.0)
        soh = random.uniform(65, 85)

    return {
        "time": int(time.time()),
        "device_key": device_key,
        "voltagebank1": round(v, 2),
        "currentbank1": round(a, 2),
        "temperature_max": round(temp, 1),
        "stateofhealthbank1": round(soh, 1),
    }


def simulate_env(device_key: str, severity: str) -> dict:
    hum = clamp(random.gauss(55, 10), 0, 100)
    temp = clamp(random.gauss(28, 6), -10, 60)
    door = random.choice(["Open", "Close"])

    if severity == "critical" and random.random() < 0.4:
        hum = clamp(hum + random.uniform(20, 35), 0, 100)
        temp = clamp(temp + random.uniform(10, 20), -10, 60)

    return {
        "time": int(time.time()),
        "device_key": device_key,
        "humidity": round(hum, 1),
        "temperature3": round(temp, 1),
        "door1": door,
    }


def simulate_energy(device_key: str, severity: str) -> dict:
    mains_v = random.uniform(208, 240)
    load_a = random.uniform(5, 80)
    pf = clamp(random.gauss(0.92, 0.05), 0, 1)

    if severity == "critical" and random.random() < 0.35:
        mains_v = random.uniform(160, 190)
        pf = clamp(pf - random.uniform(0.2, 0.35), 0, 1)

    return {
        "time": int(time.time()),
        "device_key": device_key,
        "mainsll1volt": round(mains_v, 1),
        "loadtotalcurrent": round(load_a, 1),
        "gen1powerfactor": round(pf, 2),
    }


def pick_severity() -> str:
    # Mostly healthy, some warning, some critical
    r = random.random()
    if r < 0.75:
        return "healthy"
    if r < 0.92:
        return "warning"
    return "critical"


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[simulate_publisher] Connected to {BROKER_HOST}:{BROKER_PORT} as {CLIENT_ID}")
    else:
        print(f"[simulate_publisher] Connect failed rc={rc}")


def main():
    client = mqtt.Client(client_id=CLIENT_ID, clean_session=True)

    if USERNAME and PASSWORD:
        client.username_pw_set(USERNAME, PASSWORD)

    client.on_connect = on_connect
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    client.loop_start()

    try:
        while True:
            severity = pick_severity()

            # choose a random site/device each cycle
            siteid = random.choice(SITE_IDS)
            gateway = rand_gateway_id()

            diagnostic_msg = simulate_diagnostic(siteid, gateway, severity)
            bms_msg = simulate_bms("bms-1", severity)
            env_msg = simulate_env("env-1", severity)
            energy_msg = simulate_energy("rectifier-1", severity)

            # Publish
            client.publish(TOPIC_DIAGNOSTIC, json.dumps(diagnostic_msg), qos=QOS, retain=RETAIN)
            client.publish(TOPIC_BMS, json.dumps(bms_msg), qos=QOS, retain=RETAIN)
            client.publish(TOPIC_ENV, json.dumps(env_msg), qos=QOS, retain=RETAIN)
            client.publish(TOPIC_ENERGY, json.dumps(energy_msg), qos=QOS, retain=RETAIN)

            print(
                f"[publish] severity={severity.upper():8s} siteid={siteid} "
                f"cpu={diagnostic_msg.get('cpuusage')} temp={diagnostic_msg.get('temperature')} "
                f"mem%={diagnostic_msg.get('memorypercentage')} stor%={diagnostic_msg.get('storagepercentage')}"
            )

            time.sleep(PUBLISH_INTERVAL_SEC)

    except KeyboardInterrupt:
        print("\n[simulate_publisher] Stopping...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
