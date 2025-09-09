"""
API Routes

Flask routes for API endpoints.
"""

from flask import Blueprint, request, jsonify
from flask_socketio import SocketIO

from game_server.services.controller_service import ControllerService
from game_server.services.team_service import TeamService
from game_server.services.game_service import GameService
from game_server.models.game_state import GameState

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global references (will be set by app.py)
game_state: GameState = None
controller_service: ControllerService = None
team_service: TeamService = None
game_service: GameService = None
socketio: SocketIO = None


def init_api_routes(gs: GameState, cs: ControllerService, ts: TeamService,
                    gms: GameService, sio: SocketIO):
    """Initialize API routes with service dependencies."""
    global game_state, controller_service, team_service, game_service, socketio
    game_state = gs
    controller_service = cs
    team_service = ts
    game_service = gms
    socketio = sio


@api_bp.route("/register_controller", methods=["POST"])
def register_controller():
    """Register a new controller."""
    data = request.json
    controller_id = data.get("controller_id")
    
    if not controller_id:
        return jsonify({
            "status": "error",
            "message": "No controller_id provided"
        }), 400
    
    result = controller_service.register_controller(
        controller_id,
        data.get("extra", {})
    )
    return jsonify(result)


@api_bp.route("/controller_status", methods=["POST"])
def update_controller_status():
    """Update controller status."""
    data = request.json
    controller_id = data.get("controller_id")
    status = data.get("status")
    
    if not controller_id or not status:
        return jsonify({
            "status": "error",
            "message": "Missing controller_id or status"
        }), 400
    
    result = controller_service.update_controller_status(controller_id, status)
    return jsonify(result)


@api_bp.route("/answer", methods=["POST"])
def submit_answer():
    """Submit controller answer/input."""
    data = request.json
    controller_id = data.get("controller_id")
    answer = data.get("answer")
    
    print(f"Received input from controller: {controller_id}, input: {answer}")
    
    # Check if this is a new controller
    controller_service.handle_new_controller_in_answer(controller_id)
    
    # Store the answer
    game_state.answers[controller_id] = answer
    
    # Only allow selected controller to trigger team actions
    selected = game_state.selected_controller
    if selected and controller_id != selected:
        # Still flash, but ignore for team actions
        if answer is not None:
            socketio.emit("controller_flash", {"controller_id": controller_id})
        return jsonify(success=True)
    
    # Emit flash event for this controller
    if answer is not None:
        socketio.emit("controller_flash", {"controller_id": controller_id})
    
    # Check for team match
    matched_team = team_service.check_team_match(answer, selected)
    
    if matched_team:
        team_service.handle_team_match(matched_team)
    
    return jsonify(success=True)


@api_bp.route("/score", methods=["POST"])
def change_score():
    """Update team score."""
    data = request.json
    team = data.get("team")
    delta = int(data.get("delta", 0))
    
    result = team_service.update_team_score(team, delta)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@api_bp.route("/team_number/<team>")
def get_team_number(team):
    """Get current random number for a team."""
    team = team.lower()
    if team in game_state.team_numbers:
        return jsonify(number=game_state.team_numbers[team])
    return jsonify(error="Invalid team"), 404


@api_bp.route("/team_number/<team>/regenerate", methods=["POST"])
def regenerate_team_number(team):
    """Regenerate a team's random number."""
    import random
    team = team.lower()
    if team in game_state.team_numbers:
        game_state.team_numbers[team] = random.randint(0, 3)
        return jsonify(number=game_state.team_numbers[team])
    return jsonify(error="Invalid team"), 404


@api_bp.route("/toggle_ip", methods=["POST"])
def toggle_ip():
    """Toggle IP address display."""
    result = game_service.toggle_ip_display()
    return jsonify(result)


@api_bp.route("/start_game", methods=["POST"])
def start_game():
    """Start the game."""
    result = game_service.start_game()
    return jsonify(result)


@api_bp.route("/next", methods=["POST"])
def next_question():
    """Move to next question."""
    result = game_service.next_question()
    return jsonify(result)


@api_bp.route("/prev", methods=["POST"])
def prev_question():
    """Move to previous question."""
    result = game_service.prev_question()
    return jsonify(result)


@api_bp.route("/add_team", methods=["POST"])
def add_team():
    """Add a new team."""
    data = request.json
    team_name = data.get("team_name", "")
    
    result = team_service.add_team(team_name)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@api_bp.route("/update_team_name", methods=["POST"])
def update_team_name():
    """Update a team's name."""
    data = request.json
    old_name = data.get("old_name", "")
    new_name = data.get("new_name", "")
    
    result = team_service.update_team_name(old_name, new_name)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@api_bp.route("/delete_team", methods=["POST"])
def delete_team():
    """Delete a team."""
    data = request.json
    team_name = data.get("team_name", "")
    
    result = team_service.delete_team(team_name)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@api_bp.route("/update_team_color", methods=["POST"])
def update_team_color():
    """Update a team's color."""
    data = request.json
    team_name = data.get("team_name", "")
    team_color = data.get("team_color", "")
    
    result = team_service.update_team_color(team_name, team_color)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@api_bp.route("/state")
def get_state():
    """Get current game state."""
    state_dict = game_service.get_state()
    return jsonify(state_dict)
