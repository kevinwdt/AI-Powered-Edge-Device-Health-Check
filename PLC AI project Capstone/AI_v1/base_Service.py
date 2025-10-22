# base_Service.py

class BaseService:
    """Parent base class with empty lifecycle methods."""
    def __init__(self, name: str):
        self.name = name;
        self.running = False;
    
    def start(self) -> None:
        self.running = True;# Start the service
    
    def stop(self):
        self.running = False;# Stop the service