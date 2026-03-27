#!/usr/bin/env python3
"""
pi_publisher.py — Real Raspberry Pi telemetry publisher (MQTT)

Publishes JSON payload compatible with your subscriber (mqtt_Client.py):
- totalmemory, remainingmemory, storagetotal, remainingstorage, cpuusage, temperature
- time, gateway, siteid

Default topic format (matches your subscriber "plc/devices/diagnostic/#"):
  plc/devices/diagnostic/<DEVICE_ID>

Install:
  pip3 install paho-mqtt

Run:
  python3 pi_publisher.py --broker 192.168.1.25 --device pi4-01 --site WAREHOUSE

Optional:
  --interval 2
  --disk-path /
  --username xxx --password yyy
"""

import argparse
import json
import os
import shutil
import subprocess
import time
from typing import Optional

import paho.mqtt.client as mqtt


# -----------------------
# Metric collection utils
# -----------------------

def read_cpu_usage_percent(sample_sec: float = 0.5) -> Optional[float]:
    """
    Approx CPU usage % using /proc/stat (no external deps).
    """
    try:
        def read():
            with open("/proc/stat", "r", encoding="utf-8") as f:
                line = f.readline().strip()
            parts = line.split()
            # cpu user nice system idle iowait irq softirq steal guest guest_nice
            vals = list(map(int, parts[1:]))
            idle = vals[3] + vals[4]  # idle + iowait
            total = sum(vals)
            return idle, total

        idle1, total1 = read()
        time.sleep(sample_sec)
        idle2, total2 = read()

        idle_delta = idle2 - idle1
        total_delta = total2 - total1
        if total_delta <= 0:
            return None

        usage = 100.0 * (1.0 - (idle_delta / total_delta))
        return round(max(0.0, min(100.0, usage)), 1)
    except Exception:
        return None


def read_mem_mb() -> tuple[Optional[float], Optional[float]]:
    """
    Returns (total_mb, remaining_mb) from /proc/meminfo.
    remaining = MemAvailable (best estimate of free memory).
    """
    try:
        meminfo = {}
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            for line in f:
                key, val = line.split(":", 1)
                meminfo[key.strip()] = val.strip()

        total_kb = float(meminfo["MemTotal"].split()[0])
        avail_kb = float(meminfo.get("MemAvailable", meminfo["MemFree"]).split()[0])

        total_mb = round(total_kb / 1024.0, 2)
        remaining_mb = round(avail_kb / 1024.0, 2)
        return total_mb, remaining_mb
    except Exception:
        return None, None


def read_disk_mb(path: str = "/") -> tuple[Optional[float], Optional[float]]:
    """
    Returns (total_mb, remaining_mb) for the filesystem containing `path`.
    """
    try:
        usage = shutil.disk_usage(path)
        total_mb = round(usage.total / (1024.0 * 1024.0), 1)
        free_mb = round(usage.free / (1024.0 * 1024.0), 1)
        return total_mb, free_mb
    except Exception:
        return None, None


def read_temp_c() -> Optional[float]:
    """
    Try vcgencmd first (Pi OS usually has it).
    Fallback to thermal_zone0.
    """
    # vcgencmd
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True).strip()
        # temp=48.6'C
        if out.startswith("temp="):
            val = out.split("=", 1)[1].split("'")[0]
            return round(float(val), 1)
    except Exception:
        pass

    # thermal zone
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r", encoding="utf-8") as f:
            milli = float(f.read().strip())
        return round(milli / 1000.0, 1)
    except Exception:
        return None


# -----------------------
# Main publisher loop
# -----------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", required=True, help="MQTT broker IP/hostname (warehouse laptop IP)")
    ap.add_argument("--port", type=int, default=1883, help="MQTT broker port (default 1883)")
    ap.add_argument("--device", required=True, help="Device ID, e.g., pi4-01 (used as gateway + topic suffix)")
    ap.add_argument("--site", default="UNKNOWN", help="Site ID label, e.g., WAREHOUSE")
    ap.add_argument("--interval", type=float, default=2.0, help="Publish interval seconds (default 2)")
    ap.add_argument("--disk-path", default="/", help="Disk path to measure usage for (default /)")
    ap.add_argument("--username", default=None, help="MQTT username (optional)")
    ap.add_argument("--password", default=None, help="MQTT password (optional)")
    args = ap.parse_args()

    topic = f"plc/devices/diagnostic/{args.device}"

    client_id = f"{args.device}-publisher"
    client = mqtt.Client(client_id=client_id, clean_session=True)

    if args.username and args.password:
        client.username_pw_set(args.username, args.password)

    def on_connect(c, u, f, rc):
        if rc == 0:
            print(f"[PiPublisher] Connected to {args.broker}:{args.port} as {client_id}")
            print(f"[PiPublisher] Publishing to topic: {topic}")
        else:
            print(f"[PiPublisher] Connect failed rc={rc}")

    client.on_connect = on_connect

    print(f"[PiPublisher] Connecting to broker {args.broker}:{args.port} ...")
    client.connect(args.broker, args.port, keepalive=60)
    client.loop_start()

    try:
        while True:
            cpu = read_cpu_usage_percent()
            total_mem, remaining_mem = read_mem_mb()
            total_disk, remaining_disk = read_disk_mb(args.disk_path)
            temp = read_temp_c()

            payload = {
                "time": int(time.time()),
                "gateway": args.device,   # your subscriber reads "gateway"
                "siteid": args.site,      # your subscriber reads "siteid"

                "cpuusage": cpu,
                "temperature": temp,

                "totalmemory": total_mem,
                "remainingmemory": remaining_mem,

                "storagetotal": total_disk,
                "remainingstorage": remaining_disk,
            }

            client.publish(topic, json.dumps(payload), qos=0, retain=False)

            print(
                f"[publish] device={args.device} cpu={cpu} temp={temp} "
                f"mem_rem={remaining_mem}/{total_mem}MB "
                f"disk_rem={remaining_disk}/{total_disk}MB"
            )

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[PiPublisher] Stopping...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
