# web_server.py
from base_Service import BaseService

class WebServer(BaseService):
    """Empty web server service skeleton."""
    def __init__(self):
        super().__init__("WebServer")

    def start(self) -> None:
        super().start()
        # TODO: start HTTP server

    def stop(self) -> None:
        # TODO: stop HTTP server gracefully
        super().stop()
