import os, json, pathlib, sys
from dotenv import load_dotenv
from paho.mqtt import client as mqtt

# Ensure local imports work when running from project root
sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from main import insert_message  # reuse validation + idempotent insert

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_TOPICS = [t.strip() for t in os.getenv("MQTT_TOPICS", "#").split(",") if t.strip()]
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "edge-ingestor")

def on_connect(client, userdata, flags, reason_code, properties=None):
    print("Connected to MQTT:", reason_code)
    for t in MQTT_TOPICS:
        client.subscribe(t, qos=0)
        print("Subscribed:", t)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8", errors="ignore"))
        if "topic" not in data:
            data["topic"] = msg.topic
        insert_message(data)
    except Exception as e:
        print("ingest_error:", e, "topic=", msg.topic)

def main():
    client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)


    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    # TLS example (uncomment and configure if needed)
    # import ssl
    # client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    client.on_connect = on_connect
    client.on_message = on_message
    print(f"Connecting to {MQTT_HOST}:{MQTT_PORT} ...")
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    main()
