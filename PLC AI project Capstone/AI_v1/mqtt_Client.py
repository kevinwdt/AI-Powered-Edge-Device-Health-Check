# mqtt_client.py
import json
import time
import threading
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

from base_Service import BaseService
from database_Access import DatabaseAccess
from ai_Model import AIModel


class MqttClient(BaseService):
    """
    Persistent MQTT subscriber.
    - Receives device health JSON
    - Derives features
    - Runs AI prediction
    - Stores to DB
    """
    def __init__(
        self,
        db: DatabaseAccess,
        ai: AIModel,
        broker_host: str = "test.mosquitto.org",
        broker_port: int = 1883,
        topic: str = "plc/devices/diagnostic/#",
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        super().__init__("MqttClient")
        self.db = db
        self.ai = ai
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.username = username
        self.password = password

        self._client: Optional[mqtt.Client] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        super().start()
        self._client = mqtt.Client()
        if self.username and self.password:
            self._client.username_pw_set(self.username, self.password)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        print(f"[MQTT] Connecting to {self.broker_host}:{self.broker_port} ...")
        self._client.connect(self.broker_host, self.broker_port, keepalive=60)

        self._thread = threading.Thread(target=self._client.loop_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass
        super().stop()

    def _on_connect(self, client, userdata, flags, rc):
        print(f"[MQTT] Connected with result code {rc}. Subscribing to {self.topic}")
        client.subscribe(self.topic)

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="ignore")
            data = json.loads(payload) if payload.strip().startswith("{") else {"raw": payload}

            # Extract common identity
            siteid = str(data.get("siteid") or data.get("SiteId") or "UNKNOWN")
            gateway = str(data.get("gateway") or data.get("Gateway") or "UNKNOWN")
            ts = int(data.get("time") or data.get("updatetime") or time.time())

            # Derive features you specified
            totalmemory = _to_float(data.get("totalmemory"))
            remainingmemory = _to_float(data.get("remainingmemory"))
            storagetotal = _to_float(data.get("storagetotal"))
            remainingstorage = _to_float(data.get("remainingstorage"))
            cpuusage = _to_float(data.get("cpuusage"))
            temperature = _to_float(data.get("temperature"))

            used_memory = None
            if totalmemory is not None and remainingmemory is not None:
                used_memory = totalmemory - remainingmemory

            used_storage = None
            if storagetotal is not None and remainingstorage is not None:
                used_storage = storagetotal - remainingstorage

            # AI predict (if model loaded)
            health_status, reason = None, None
            if self.ai.artifacts is not None:
                health_status, reason = self.ai.predict_status({
                    "used_memory": used_memory,
                    "used_storage": used_storage,
                    "cpuusage": cpuusage,
                    "temperature": temperature,
                })

            # Store
            self.db.insert_telemetry(
                ts=ts,
                gateway=gateway,
                siteid=siteid,
                topic=msg.topic,
                raw=data,
                used_memory=used_memory,
                used_storage=used_storage,
                cpuusage=cpuusage,
                temperature=temperature,
                health_status=health_status,
                reason=reason
            )
        except Exception as e:
            print(f"[MQTT] Error handling message: {e}")


def _to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None
