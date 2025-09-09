"""
Flask Application Factory

Main application setup and configuration.
"""

from flask import Flask
from flask_socketio import SocketIO

from game_server.models.game_state import GameState
from game_server.services.controller_service import ControllerService
from game_server.services.team_service import TeamService
from game_server.services.game_service import GameService
from game_server.routes.api import api_bp, init_api_routes
from game_server.routes.pages import pages_bp, init_page_routes
from game_server.routes.websocket import (
    init_websocket_handlers, register_socketio_handlers
)


def create_app():
    """Create and configure the Flask application."""
    # Create Flask app
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    
    # Create SocketIO instance
    socketio = SocketIO(app)
    
    # Initialize game state
    game_state = GameState()
    
    # Initialize services
    controller_service = ControllerService(game_state, socketio)
    team_service = TeamService(game_state, socketio)
    game_service = GameService(game_state, socketio)
    
    # Initialize route handlers with dependencies
    init_api_routes(game_state, controller_service, team_service,
                    game_service, socketio)
    init_page_routes(game_state, team_service)
    init_websocket_handlers(game_state, team_service)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(pages_bp)
    
    # Register WebSocket handlers
    register_socketio_handlers(socketio)
    
    return app, socketio


def run_server():
    """Run the game server."""
    from utils import get_host_ip
    
    app, socketio = create_app()
    
    print(f"Game server running at http://{get_host_ip()}:5002/")
    socketio.run(app, host="0.0.0.0", port=5002, debug=True)
