# mqtt_client.py
from base_Service import BaseService

class MqttClient(BaseService):
    def __init__(self):
        super().__init__("MqttClient")

    def start(self) -> None:
        super().start()
        # TODO: connect to MQTT broker

    def stop(self) -> None:
        # TODO: disconnect from MQTT broker
        super().stop()
