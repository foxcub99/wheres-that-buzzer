"""
Controller Service

Handles controller registration, status updates, and management.
"""

from typing import Dict
from flask import request
from flask_socketio import SocketIO

from game_server.models.game_state import GameState


class ControllerService:
    """Service for managing controller operations."""
    
    def __init__(self, game_state: GameState, socketio: SocketIO):
        """Initialize with game state and socketio instance."""
        self.game_state = game_state
        self.socketio = socketio
    
    def register_controller(self, controller_id: str, extra_data: Dict = None) -> Dict:
        """Register a new controller with the game."""
        controller_info = {
            "id": controller_id,
            "ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent"),
            "extra": extra_data or {},
            "status": "active"
        }
        
        self.game_state.register_controller(controller_id, controller_info)
        
        # Emit update to all clients
        self._emit_controller_update()
        
        return {
            "status": "ok",
            "controllers": list(self.game_state.controllers),
            "controller_infos": self.game_state.controller_infos
        }
    
    def update_controller_status(self, controller_id: str, status: str) -> Dict:
        """Update controller status (active/inactive)."""
        if controller_id not in self.game_state.controller_infos:
            # Create minimal entry for status tracking
            self.game_state.controller_infos[controller_id] = {
                "id": controller_id,
                "ip": request.remote_addr,
                "status": status,
                "extra": {}
            }
        else:
            self.game_state.controller_infos[controller_id]["status"] = status
        
        self.game_state.update_controller_status(controller_id, status)
        
        # Emit update to all clients
        self.socketio.emit("controller_status_update", {
            "controller_id": controller_id,
            "status": status,
            "controllers": list(self.game_state.controllers),
            "controller_infos": self.game_state.controller_infos
        })
        
        return {"status": "ok"}
    
    def handle_new_controller_in_answer(self, controller_id: str) -> bool:
        """Handle registration of new controller during answer submission."""
        if controller_id in self.game_state.controllers:
            return False
        
        # Set proper controller info based on controller_id
        extra_info = {}
        if controller_id == "keyboard":
            extra_info["name"] = "Keyboard"
        
        controller_info = {
            "id": controller_id,
            "ip": request.remote_addr,
            "status": "active",
            "extra": extra_info,
            "user_agent": request.headers.get("User-Agent")
        }
        
        self.game_state.register_controller(controller_id, controller_info)
        
        # Emit update for new controller
        self._emit_controller_update()
        return True
    
    def _emit_controller_update(self):
        """Emit controller update to all clients."""
        self.socketio.emit("controllers_update", {
            "controllers": list(self.game_state.controllers),
            "controller_infos": self.game_state.controller_infos
        })
