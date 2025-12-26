
# main.py
import time

from database_Access import DatabaseAccess
from ai_Model import AIModel
from mqtt_Client import MqttClient
from web_Server import WebServer


def start_all(services):
    print("Server is running")
    for s in services:
        s.start()
        print(f"{s.name} started.")

def stop_all(services):
    for s in reversed(services):
        s.stop()


def main():
    db = DatabaseAccess(db_path="plc_health.db")
    ai = AIModel(model_path="model.pkl")

    mqtt = MqttClient(
        db=db,
        ai=ai,
        broker_host="test.mosquitto.org",
        broker_port=1883,
        topic="plc/devices/diagnostic/#",
        username=None,
        password=None
    )

    web = WebServer(db=db, host="127.0.0.1", port=5000)

    services = [db, ai, mqtt, web]
    start_all(services)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_all(services)
        print("System stopped.")


if __name__ == "__main__":
    main()
