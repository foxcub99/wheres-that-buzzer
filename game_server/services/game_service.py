"""
Game Service

Handles core game operations like question navigation and game state 
management.
"""

from typing import Dict
from flask_socketio import SocketIO

from game_server.models.game_state import GameState


class GameService:
    """Service for managing core game operations."""
    
    def __init__(self, game_state: GameState, socketio: SocketIO):
        """Initialize with game state and socketio instance."""
        self.game_state = game_state
        self.socketio = socketio
    
    def start_game(self) -> Dict:
        """Start the game."""
        self.game_state.game_started = True
        self.socketio.emit("game_started", {})
        return {"game_started": True}
    
    def toggle_ip_display(self) -> Dict:
        """Toggle IP address display."""
        self.game_state.show_ip = not self.game_state.show_ip
        self.socketio.emit("ip_toggled", {"show_ip": self.game_state.show_ip})
        return {"show_ip": self.game_state.show_ip}
    
    def next_question(self) -> Dict:
        """Move to the next question."""
        if self.game_state.next_question():
            self._emit_question_change()
            return {"success": True}
        return {"success": False}
    
    def prev_question(self) -> Dict:
        """Move to the previous question."""
        if self.game_state.prev_question():
            self._emit_question_change()
            return {"success": True}
        return {"success": False}
    
    def get_state(self) -> Dict:
        """Get current game state."""
        return self.game_state.get_state_dict()
    
    def _emit_question_change(self):
        """Emit question change events to all clients."""
        self.socketio.emit("question_changed", {
            "current_question": self.game_state.current_question,
            "question": self.game_state.get_current_question(),
        })
        # Clear team pressed message
        self.socketio.emit("team_pressed", {"team": None})
