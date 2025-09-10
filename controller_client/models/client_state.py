"""
Client State Management

Manages the state of the controller client including connected controllers,
server connection, and configuration.
"""

import uuid
import os
from typing import Dict, Set, Optional
from dataclasses import dataclass
import pygame


@dataclass
class ClientConfig:
    """Configuration for the controller client."""
    game_server_url: str = "http://localhost:5002"
    controller_id: str = ""
    uuid_file: str = "controller_uuid.txt"
    visualizer_port: int = 5003
    enable_visualizer: bool = False


class ClientState:
    """Manages controller client state."""
    
    def __init__(self, config: ClientConfig):
        """Initialize client state with configuration."""
        self.config = config
        self.controllers: Dict[int, pygame.joystick.Joystick] = {}
        self.registered_controllers: Set[str] = set()
        self.uuid = self._get_or_create_uuid()
        
    def _get_or_create_uuid(self) -> str:
        """Get or create a unique UUID for this client."""
        if os.path.exists(self.config.uuid_file):
            with open(self.config.uuid_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        
        client_uuid = str(uuid.uuid4())
        with open(self.config.uuid_file, "w", encoding="utf-8") as f:
            f.write(client_uuid)
        return client_uuid
    
    def add_controller(self, joystick_id: int, joystick: pygame.joystick.Joystick):
        """Add a detected controller."""
        self.controllers[joystick_id] = joystick
    
    def remove_controller(self, joystick_id: int):
        """Remove a disconnected controller."""
        self.controllers.pop(joystick_id, None)
        controller_id = f"{self.config.controller_id}_{joystick_id}"
        self.registered_controllers.discard(controller_id)
    
    def mark_controller_registered(self, controller_id: str):
        """Mark a controller as registered with the server."""
        self.registered_controllers.add(controller_id)
    
    def is_controller_registered(self, controller_id: str) -> bool:
        """Check if a controller is registered."""
        return controller_id in self.registered_controllers
    
    def get_controller_id(self, joystick_id: int) -> str:
        """Get the full controller ID for a joystick."""
        return f"{self.config.controller_id}_{joystick_id}"
    
    def get_controller_count(self) -> int:
        """Get the number of connected controllers."""
        return len(self.controllers)
