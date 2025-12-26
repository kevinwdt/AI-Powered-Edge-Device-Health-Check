# server.py
from database_Access import DatabaseAccess
from ai_Model import AIModel
from mqtt_Client import MqttClient

class Server:
    def __init__(self) -> None:
        self.services = []

        self.db = DatabaseAccess()
        self.ai = AIModel(self.db, model_path="model.pkl")
        self.mqtt = MqttClient(self.ai)

        self.services.extend([self.db, self.ai, self.mqtt])

    def start_all(self):
        for s in self.services:
            s.start()

    def stop_all(self):
        for s in reversed(self.services):
            s.stop()

    def run_once_test(self):
        # Example incoming data (matches features AI expects)
        test_payload = {
            "used_memory": 1873.92 - 555.85,
            "used_storage": 4249.6 - 645.31,
            "cpuusage": 50.8,
            "temperature": 56
        }
        self.mqtt.invoke(test_payload)

if __name__ == "__main__":
    server = Server()
    server.start_all()
    server.run_once_test()
    server.stop_all()
