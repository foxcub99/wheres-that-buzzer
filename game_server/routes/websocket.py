"""
WebSocket Event Handlers

Socket.IO event handlers for real-time communication.
"""

from flask_socketio import emit

from game_server.services.team_service import TeamService
from game_server.models.game_state import GameState

# Global references (will be set by app.py)
game_state: GameState = None
team_service: TeamService = None


def init_websocket_handlers(gs: GameState, ts: TeamService):
    """Initialize WebSocket handlers with service dependencies."""
    global game_state, team_service
    game_state = gs
    team_service = ts


def register_socketio_handlers(socketio):
    """Register all Socket.IO event handlers."""
    
    @socketio.on('get_selected_controller')
    def handle_get_selected_controller():
        """Get currently selected controller."""
        cid = game_state.selected_controller
        emit('selected_controller', {'controller_id': cid})
    
    @socketio.on('select_controller')
    def handle_select_controller(data):
        """Select a controller for team actions."""
        controller_id = data.get('controller_id')
        team_service.select_controller_and_regenerate(controller_id)
    
    @socketio.on('clear_controller')
    def handle_clear_controller():
        """Clear controller selection."""
        team_service.clear_controller_selection()
