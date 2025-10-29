import os, json, time, random, datetime
from dotenv import load_dotenv
from paho.mqtt import client as mqtt

load_dotenv()
MQTT_HOST = os.getenv("MQTT_HOST", "test.mosquitto.org")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = os.getenv("MQTT_PUB_TOPIC", "demo/edge/mqtt_bms/status")

c = mqtt.Client(client_id="mockpub-mqtt", protocol=mqtt.MQTTv311)

c.connect(MQTT_HOST, MQTT_PORT, 60)

def make_bms(device="bms-1"):
    now = datetime.datetime.utcnow().isoformat()+"Z"
    return {
        "device_key": device,
        "event_time": now,
        "topic": TOPIC,
        "payload": {
            "version": "1.0",
            "metrics": {
                "voltagebank1": round(48 + random.random(), 3),
                "currentbank1": round(10 + 2*random.random(), 3)
            }
        }
    }

if __name__ == "__main__":
    print(f"Publishing mock data to mqtt://{MQTT_HOST}:{MQTT_PORT} topic={TOPIC}")
    while True:
        msg = make_bms()
        c.publish(TOPIC, json.dumps(msg))
        time.sleep(1.0)
