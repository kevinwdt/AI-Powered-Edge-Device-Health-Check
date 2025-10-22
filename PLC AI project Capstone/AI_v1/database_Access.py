# database_access.py
from base_Service import BaseService

class DatabaseAccess(BaseService):
    """Empty database access service skeleton."""
    def __init__(self):
        super().__init__("DatabaseAccess")

    def start(self) -> None:
        super().start()
        # TODO: open DB connection

    def stop(self) -> None:
        # TODO: close DB connection
        super().stop()
