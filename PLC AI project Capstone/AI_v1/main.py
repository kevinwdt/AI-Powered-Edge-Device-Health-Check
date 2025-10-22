# main.py
import time
from mqtt_Client import MqttClient
from database_Access import DatabaseAccess
from web_Server import WebServer
from ai_Model import AIModel


def start_all(services):
    for s in services:
        s.start();


def stop_all(services):
    for s in reversed(services):
        s.stop();


def main():
    mqtt = MqttClient();
    db = DatabaseAccess();
    web = WebServer();
    ai = AIModel();

    services = [mqtt, db, web, ai];
    start_all(services);

    try:
        while True:
            # TODO: add loop logic or heartbeat here
            time.sleep(1);
    except KeyboardInterrupt:
        stop_all(services);


if __name__ == "__main__":
    main();
