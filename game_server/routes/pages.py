"""
Page Routes

Flask routes for rendering HTML pages.
"""

from flask import Blueprint, render_template, request
from utils import get_host_ip

from game_server.models.game_state import GameState
from game_server.services.team_service import TeamService

# Create blueprint
pages_bp = Blueprint('pages', __name__)

# Global references (will be set by app.py)
game_state: GameState = None
team_service: TeamService = None


def init_page_routes(gs: GameState, ts: TeamService):
    """Initialize page routes with service dependencies."""
    global game_state, team_service
    game_state = gs
    team_service = ts


@pages_bp.route("/")
def home_or_game():
    """Home page or game page depending on game state."""
    if not game_state.game_started:
        host_ip = get_host_ip()
        team_urls = game_state.get_team_urls(host_ip)
        
        return render_template("home.html",
                               show_ip=game_state.show_ip,
                               ip=host_ip,
                               team_urls=team_urls)
    else:
        question = game_state.get_current_question()
        
        # Convert last_team_pressed key to display name
        last_team_display_name = None
        if game_state.last_team_pressed:
            last_team_display_name = game_state.get_team_display_name(
                game_state.last_team_pressed
            )
        
        return render_template(
            "game.html",
            question=question,
            question_num=game_state.current_question + 1,
            total=len(game_state.questions),
            team_scores=game_state.team_scores,
            last_team_pressed=last_team_display_name
        )


@pages_bp.route("/master")
def master_ui():
    """Master control interface (localhost only)."""
    # Restrict access to localhost only
    client_ip = request.remote_addr
    host_ip = get_host_ip()
    
    # Only allow localhost access
    if not (client_ip == "127.0.0.1" or client_ip == host_ip):
        return ("Access denied: Master interface only available "
                "on local machine"), 403
    
    question = game_state.get_current_question()
    
    return render_template(
        "game_master.html",
        question=question,
        question_num=game_state.current_question + 1,
        total=len(game_state.questions),
        prev_question=game_state.get_prev_question(),
        next_question=game_state.get_next_question(),
        controllers=list(game_state.controllers),
        controller_infos=game_state.controller_infos,
        show_ip=game_state.show_ip,
        game_started=game_state.game_started,
        team_scores=game_state.team_scores,
        team_colors=game_state.team_colors
    )


@pages_bp.route("/<team_key>")
def dynamic_team_page(team_key):
    """Dynamic team page based on team key."""
    team_name = game_state.find_team_by_key(team_key)
    
    if not team_name:
        return "Team not found", 404
    
    # Get team number and button name
    num = game_state.team_numbers.get(team_key, 0)
    btn_name = team_service.get_team_button_name(team_key)
    selected_controller = game_state.selected_controller
    
    # Get team index for styling
    team_names = list(game_state.team_scores.keys())
    team_index = team_names.index(team_name) + 1
    
    # Get team color
    team_color = game_state.team_colors.get(team_name, "#2a7ae2")
    
    return render_template("team.html",
                           team_number=num,
                           button_name=btn_name,
                           game_started=game_state.game_started,
                           selected_controller=selected_controller,
                           team_name=team_name,
                           team_index=team_index,
                           team_color=team_color)


# Legacy routes for backwards compatibility
@pages_bp.route("/team1")
def team1_page():
    """Team 1 page (legacy route)."""
    return dynamic_team_page("team1")


@pages_bp.route("/team2")
def team2_page():
    """Team 2 page (legacy route)."""
    return dynamic_team_page("team2")


@pages_bp.route("/team3")
def team3_page():
    """Team 3 page (legacy route)."""
    return dynamic_team_page("team3")
