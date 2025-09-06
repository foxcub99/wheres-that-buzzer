# ...existing code...

# --- Controller Registration Endpoint ---
from flask import Flask, render_template, request, jsonify
# ...existing code...
# Register controller endpoint
import os


import random
from flask_socketio import SocketIO, emit
import json
from utils import get_host_ip
from controllers import controller_mapping

app = Flask(__name__)
socketio = SocketIO(app)

@socketio.on('get_selected_controller')
def handle_get_selected_controller():
    cid = state.get('selected_controller')
    socketio.emit('selected_controller', {'controller_id': cid})

# Track selected controller in state
state = globals().get('state', {})
if 'selected_controller' not in state:
    state['selected_controller'] = None
# Team random number pages
@socketio.on('select_controller')
def handle_select_controller(data):
    cid = data.get('controller_id')
    prev = state.get('selected_controller')
    if cid != prev:
        # Only regenerate numbers if a new controller is selected
        # Get button mapping for this controller
        controller_type = None
        if cid and 'controller_infos' in state and cid in state['controller_infos']:
            controller_type = state['controller_infos'][cid]['extra'].get('name', 'Xbox')
        elif cid == 'keyboard':
            controller_type = 'Keyboard'  # Handle keyboard controllers specifically
        else:
            controller_type = 'Xbox'  # fallback
        # Get all button ids for this controller type
        if hasattr(controller_mapping, 'get_all_button_ids'):
            button_ids = controller_mapping.get_all_button_ids(controller_type)
        else:
            # fallback: try 0-15
            button_ids = list(range(0, 15))
        # Remove unmapped buttons
        button_ids = [bid for bid in button_ids if controller_mapping.get_button_name(controller_type, bid) != 'Not Mapped']
    # Pick unique random buttons for all teams
    team_keys = list(state["team_numbers"].keys())
    chosen = random.sample(button_ids, min(len(team_keys), len(button_ids)))
    
    # Assign unique buttons to teams, fill with 0 if not enough
    for i, team_key in enumerate(team_keys):
        state["team_numbers"][team_key] = chosen[i] if i < len(chosen) else 0
    
    # Emit update so team pages reload
    socketio.emit("controllers_update", {
        "controllers": list(state["controllers"]),
        "controller_infos": state.get("controller_infos", {})
    })
    socketio.emit('reload_team_pages')
    state['selected_controller'] = cid
    print(f"Selected controller set to: {cid}")
    socketio.emit('selected_controller', {'controller_id': cid})


@socketio.on('clear_controller')
def handle_clear_controller():
    state["selected_controller"] = None
    # Reset all team numbers to 0
    for team_key in state["team_numbers"]:
        state["team_numbers"][team_key] = 0
    # Clear any previous team buzz
    state["last_team_pressed"] = None
    socketio.emit("team_pressed", {"team": None})
    # Emit update so team pages reload
    socketio.emit("reload_team_pages", {})
    socketio.emit('selected_controller', {'controller_id': None})
    print("Controller selection cleared")

@app.route("/api/register_controller", methods=["POST"])
def register_controller():
    data = request.json
    controller_id = data.get("controller_id")
    controller_info = {
        "id": controller_id,
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
        "extra": data.get("extra", {}),
        "status": "active"  # Default to active when registering
    }
    if controller_id:
        # Store info in a dict keyed by id
        if "controller_infos" not in state:
            state["controller_infos"] = {}
        state["controller_infos"][controller_id] = controller_info
        state["controllers"].add(controller_id)
        # Emit full info to master page
        socketio.emit("controllers_update", {
            "controllers": list(state["controllers"]),
            "controller_infos": state["controller_infos"]
        })
        return jsonify({
            "status": "ok", 
            "controllers": list(state["controllers"]), 
            "controller_infos": state["controller_infos"]
        })
    return jsonify({
        "status": "error", 
        "message": "No controller_id provided"
    }), 400


@app.route("/api/controller_status", methods=["POST"])
def update_controller_status():
    data = request.json
    controller_id = data.get("controller_id")
    status = data.get("status")  # "active" or "inactive"
    
    if controller_id and status:
        if "controller_infos" not in state:
            state["controller_infos"] = {}
        
        if controller_id in state["controller_infos"]:
            state["controller_infos"][controller_id]["status"] = status
        else:
            # Create minimal entry for status tracking
            state["controller_infos"][controller_id] = {
                "id": controller_id,
                "ip": request.remote_addr,
                "status": status,
                "extra": {}
            }
        
        if status == "inactive":
            # Remove from active controllers but keep in infos for history
            state["controllers"].discard(controller_id)
        else:
            # Add back to active controllers
            state["controllers"].add(controller_id)
        
        # Emit update to all clients
        socketio.emit("controller_status_update", {
            "controller_id": controller_id,
            "status": status,
            "controllers": list(state["controllers"]),
            "controller_infos": state["controller_infos"]
        })
        
        return jsonify({"status": "ok"})
    
    return jsonify({
        "status": "error", 
        "message": "Missing controller_id or status"
    }), 400

# Team random number pages

# Helper to get button name for team page
def get_team_button_name(team):
    btn_num = state["team_numbers"][team]
    # Try to get the selected controller type
    selected = state.get('selected_controller')
    controller_type = None
    if selected and 'controller_infos' in state and selected in state['controller_infos']:
        controller_type = state['controller_infos'][selected]['extra'].get('name', 'Xbox')
    elif selected == 'keyboard':
        controller_type = 'Keyboard'  # Handle keyboard controllers specifically
    else:
        controller_type = 'Xbox'  # fallback
    return controller_mapping.get_button_name(controller_type, btn_num)

@app.route("/<team_key>")
def dynamic_team_page(team_key):
    # Find the team name that matches this key
    team_name = None
    for name in state["team_scores"].keys():
        if name.lower().replace(" ", "").replace("_", "") == team_key:
            team_name = name
            break
    
    if not team_name:
        # Check if it's one of the original team keys
        team_mapping = {
            "team1": "Team 1",
            "team2": "Team 2",
            "team3": "Team 3"
        }
        team_name = team_mapping.get(team_key)
        if not team_name or team_name not in state["team_scores"]:
            return "Team not found", 404
    
    # Get team number for this team key
    num = state["team_numbers"].get(team_key, 0)
    btn_name = get_team_button_name(team_key)
    selected_controller = state.get("selected_controller")
    
    # Get team index for styling purposes
    team_names = list(state["team_scores"].keys())
    team_index = team_names.index(team_name) + 1
    
    # Get team color
    team_color = state["team_colors"].get(team_name, "#2a7ae2")
    
    # Use the generic team template
    return render_template("team.html",
                           team_number=num,
                           button_name=btn_name,
                           game_started=state["game_started"],
                           selected_controller=selected_controller,
                           team_name=team_name,
                           team_index=team_index,
                           team_color=team_color)


@app.route("/team1")
def team1_page():
    return dynamic_team_page("team1")


@app.route("/team2")
def team2_page():
    return dynamic_team_page("team2")


@app.route("/team3")
def team3_page():
    return dynamic_team_page("team3")


# Load questions
with open("questions.json") as f:
    questions = json.load(f)["questions"]

# Game state
# Game state
state = {
    "current_question": 0,
    "answers": {},  # {controller_id: answer}
    "controllers": set(),
    "show_ip": False,
    "game_started": False,
    "team_scores": {
        "Team 1": 0,
        "Team 2": 0,
        "Team 3": 0
    },
    # Team colors (hex codes)
    "team_colors": {
        "Team 1": "#2a7ae2",
        "Team 2": "#e74c3c",
        "Team 3": "#27ae60"
    },
    # Store random numbers for each team, start at 0
    "team_numbers": {}
}

# Initialize team_numbers based on team_scores
def initialize_team_numbers():
    """Initialize team numbers based on current teams"""
    for team_name in state["team_scores"]:
        team_key = team_name.lower().replace(" ", "").replace("_", "")
        if team_key not in state["team_numbers"]:
            state["team_numbers"][team_key] = 0

# Initialize team numbers on startup
initialize_team_numbers()
# API to get the current random number for a team
@app.route("/api/team_number/<team>")
def get_team_number(team):
    team = team.lower()
    if team in state["team_numbers"]:
        return jsonify(number=state["team_numbers"][team])
    return jsonify(error="Invalid team"), 404

# API to regenerate a team's random number
@app.route("/api/team_number/<team>/regenerate", methods=["POST"])
def regenerate_team_number(team):
    team = team.lower()
    if team in state["team_numbers"]:
        state["team_numbers"][team] = random.randint(0, 3)
        return jsonify(number=state["team_numbers"][team])
    return jsonify(error="Invalid team"), 404

# --- Place the score route here, after app/socketio/state ---
@app.route("/api/score", methods=["POST"])
def change_score():
    data = request.json
    team = data.get("team")
    delta = int(data.get("delta", 0))
    if team in state["team_scores"]:
        state["team_scores"][team] += delta
        # Prevent negative scores
        if state["team_scores"][team] < 0:
            state["team_scores"][team] = 0
        # Emit update to all clients
        socketio.emit("score_update", {"team_scores": state["team_scores"]})
        return jsonify(success=True, team_scores=state["team_scores"])
    return jsonify(success=False, error="Invalid team"), 400


@app.route("/")
def home_or_game():
    if not state["game_started"]:
        host_ip = get_host_ip()
        # Create team URLs list
        team_urls = []
        for team_name in state["team_scores"].keys():
            team_key = team_name.lower().replace(" ", "").replace("_", "")
            team_urls.append({
                "name": team_name,
                "url": f"{host_ip}:5002/{team_key}"
            })
        
        return render_template("home.html",
                               show_ip=state["show_ip"],
                               ip=host_ip,
                               team_urls=team_urls)
    else:
        q = questions[state["current_question"]]
        
        # Convert last_team_pressed key to display name
        last_team_display_name = None
        if state.get("last_team_pressed"):
            team_key = state["last_team_pressed"]
            for display_name in state["team_scores"].keys():
                display_key = (display_name.lower()
                               .replace(" ", "").replace("_", ""))
                if display_key == team_key:
                    last_team_display_name = display_name
                    break
        
        return render_template(
            "game.html",
            question=q,
            question_num=state["current_question"] + 1,
            total=len(questions),
            team_scores=state["team_scores"],
            last_team_pressed=last_team_display_name
        )


@app.route("/master")
def master_ui():
    # Restrict access to localhost only
    client_ip = request.remote_addr
    host_ip = get_host_ip()
    
    # Only allow localhost access
    if not (client_ip == "127.0.0.1" or client_ip == host_ip):
        return ("Access denied: Master interface only available "
                "on local machine"), 403
    
    q = questions[state["current_question"]]
    current_idx = state["current_question"]
    
    # Get previous and next questions if they exist
    prev_question = questions[current_idx - 1] if current_idx > 0 else None
    next_question = (questions[current_idx + 1]
                     if current_idx < len(questions) - 1 else None)
    
    return render_template(
        "game_master.html",
        question=q,
        question_num=state["current_question"] + 1,
        total=len(questions),
        prev_question=prev_question,
        next_question=next_question,
        controllers=list(state["controllers"]),
        controller_infos=state.get("controller_infos", {}),
        show_ip=state["show_ip"],
        game_started=state["game_started"],
        team_scores=state["team_scores"],
        team_colors=state["team_colors"]
    )


@app.route("/api/toggle_ip", methods=["POST"])
def toggle_ip():
    state["show_ip"] = not state["show_ip"]
    socketio.emit("ip_toggled", {"show_ip": state["show_ip"]})
    return jsonify(show_ip=state["show_ip"])


@app.route("/api/start_game", methods=["POST"])
def start_game():
    state["game_started"] = True
    socketio.emit("game_started", {})
    return jsonify(game_started=True)


@app.route("/api/next", methods=["POST"])
def next_question():
    if state["current_question"] < len(questions) - 1:
        state["current_question"] += 1
        state["answers"] = {}
        state["last_team_pressed"] = None  # Clear team pressed message
        # Emit event to all clients
        socketio.emit(
            "question_changed",
            {
                "current_question": state["current_question"],
                "question": questions[state["current_question"]],
            },
        )
        # Clear team pressed message on game page
        socketio.emit("team_pressed", {"team": None})
    return jsonify(success=True)


@app.route("/api/prev", methods=["POST"])
def prev_question():
    if state["current_question"] > 0:
        state["current_question"] -= 1
        state["answers"] = {}
        state["last_team_pressed"] = None  # Clear team pressed message
        # Emit event to all clients
        socketio.emit(
            "question_changed",
            {
                "current_question": state["current_question"],
                "question": questions[state["current_question"]],
            },
        )
        # Clear team pressed message on game page
        socketio.emit("team_pressed", {"team": None})
    return jsonify(success=True)


@app.route("/api/answer", methods=["POST"])
def submit_answer():
    data = request.json
    controller_id = data.get("controller_id")
    answer = data.get("answer")
    print(f"Received input from controller: {controller_id}, input: {answer}")
    
    # Check if this is a new controller
    is_new_controller = controller_id not in state["controllers"]
    
    state["controllers"].add(controller_id)
    state["answers"][controller_id] = answer
    
    # If new controller and not in controller_infos, create minimal entry
    controller_infos = state.get("controller_infos", {})
    if is_new_controller and controller_id not in controller_infos:
        if "controller_infos" not in state:
            state["controller_infos"] = {}
        
        # Set proper controller info based on controller_id
        extra_info = {}
        if controller_id == "keyboard":
            extra_info["name"] = "Keyboard"
        
        state["controller_infos"][controller_id] = {
            "id": controller_id,
            "ip": request.remote_addr,
            "status": "active",
            "extra": extra_info,
            "user_agent": request.headers.get("User-Agent")
        }
        # Emit update for new controller
        socketio.emit("controllers_update", {
            "controllers": list(state["controllers"]),
            "controller_infos": state["controller_infos"]
        })
    
    # Only allow selected controller to trigger team actions
    selected = state.get('selected_controller')
    if selected and controller_id != selected:
        # Still flash, but ignore for team actions
        if answer is not None:
            socketio.emit("controller_flash", {"controller_id": controller_id})
        return jsonify(success=True)
    # Emit a flash event for this controller
    if answer is not None:
        socketio.emit("controller_flash", {"controller_id": controller_id})
    print("Current team numbers:", state["team_numbers"])
    print("Raw answer value and type:", answer, type(answer))
    # Check if answer matches any team number
    matched_team = None
    for team, num in state["team_numbers"].items():
        try:
            if answer is not None:
                # Handle keyboard controller differently
                if selected == "keyboard":
                    # For keyboard, map the raw key to the team number
                    # Answer contains raw key (like "a", "b", "Key.esc")
                    # Find which team number corresponds to this key
                    for team_key, team_num in state["team_numbers"].items():
                        expected_key_name = controller_mapping.get_button_name(
                            "Keyboard", team_num)
                        # Check if the answer matches this key
                        actual_key_name = controller_mapping.get_button_name(
                            "Keyboard", str(answer))
                        if (expected_key_name == actual_key_name and
                                expected_key_name != "Not Mapped"):
                            matched_team = team_key
                            break
                else:
                    # Extract number from 'button_X' or use as int
                    if (isinstance(answer, str) and
                            answer.startswith("button_")):
                        btn_num = int(answer.split("_")[1])
                    else:
                        btn_num = int(answer)
                    if btn_num == num:
                        matched_team = team
                        break
        except Exception as e:
            print(f"Error matching answer: {e}")
            pass
    if matched_team:
        # Find the team display name from the team key
        team_display_name = None
        for display_name, score in state["team_scores"].items():
            display_key = (display_name.lower()
                           .replace(" ", "").replace("_", ""))
            if display_key == matched_team:
                team_display_name = display_name
                break
        
        if team_display_name:
            print(f"Team '{team_display_name}' "
                  f"(key: {matched_team}) has matched!")
            
            # Try to play sound file - check for team number at end of key
            team_number = None
            if matched_team.startswith("team") and matched_team[4:].isdigit():
                team_number = matched_team[4:]
            else:
                # For custom teams, try to find their index
                team_names = list(state["team_scores"].keys())
                if team_display_name in team_names:
                    team_number = str(team_names.index(team_display_name) + 1)
            
            if team_number:
                try:
                    if team_number in ["1", "2", "3"]:
                        # Play built-in sound for team 1, 2, or 3
                        os.system(f'afplay sounds/team_{team_number}.mp3')
                    else:
                        os.system(f'afplay sounds/team_1.mp3')
                except Exception as e:
                    print(f"Could not play sound for team {team_number}: {e}")
            
            state["last_team_pressed"] = matched_team
            # Regenerate all team numbers
            for t in state["team_numbers"]:
                state["team_numbers"][t] = random.randint(0, 3)
            socketio.emit("team_pressed", {
                "team": matched_team,
                "team_display_name": team_display_name
            })
            socketio.emit("reload_post_buzz", {})
            socketio.emit("reload_team_pages", {})
    return jsonify(success=True)


@app.route("/api/add_team", methods=["POST"])
def add_team():
    data = request.json
    team_name = data.get("team_name", "").strip()
    
    if not team_name:
        return jsonify(success=False, error="Team name cannot be empty")
    
    if team_name in state["team_scores"]:
        return jsonify(success=False, error="Team name already exists")
    
    # Add team to scores
    state["team_scores"][team_name] = 0
    
    # Assign a default color (generate from team name or use a default palette)
    default_colors = ["#2a7ae2", "#e74c3c", "#27ae60", "#f39c12",
                      "#9b59b6", "#34495e", "#e67e22", "#1abc9c"]
    team_index = len(state["team_colors"])
    default_color = default_colors[team_index % len(default_colors)]
    state["team_colors"][team_name] = default_color
    
    # Generate team key for URL routing
    team_key = team_name.lower().replace(" ", "").replace("_", "")
    if team_key not in state["team_numbers"]:
        state["team_numbers"][team_key] = 0
    
    # Emit updates to all clients
    socketio.emit("team_list_updated", {"team_scores": state["team_scores"]})
    socketio.emit("reload_home_page", {})
    
    return jsonify(success=True)


@app.route("/api/update_team_name", methods=["POST"])
def update_team_name():
    data = request.json
    old_name = data.get("old_name", "").strip()
    new_name = data.get("new_name", "").strip()
    
    if not new_name:
        return jsonify(success=False, error="Team name cannot be empty")
    
    if old_name not in state["team_scores"]:
        return jsonify(success=False, error="Original team not found")
    
    if new_name != old_name and new_name in state["team_scores"]:
        return jsonify(success=False, error="New team name already exists")
    
    # Update team scores dictionary
    score = state["team_scores"].pop(old_name)
    state["team_scores"][new_name] = score
    
    # Update team color dictionary
    if old_name in state["team_colors"]:
        color = state["team_colors"].pop(old_name)
        state["team_colors"][new_name] = color
    
    # Update team numbers if the key changed
    old_key = old_name.lower().replace(" ", "").replace("_", "")
    new_key = new_name.lower().replace(" ", "").replace("_", "")
    
    if old_key != new_key and old_key in state["team_numbers"]:
        state["team_numbers"][new_key] = state["team_numbers"].pop(old_key)
    
    # Emit updates to all clients
    socketio.emit("team_list_updated", {"team_scores": state["team_scores"]})
    socketio.emit("reload_home_page", {})
    
    return jsonify(success=True)


@app.route("/api/delete_team", methods=["POST"])
def delete_team():
    data = request.json
    team_name = data.get("team_name", "").strip()
    
    if not team_name:
        return jsonify(success=False, error="Team name cannot be empty")
    
    if team_name not in state["team_scores"]:
        return jsonify(success=False, error="Team not found")
    
    if len(state["team_scores"]) <= 1:
        return jsonify(success=False, error="Cannot delete the last team")
    
    # Remove team from scores
    state["team_scores"].pop(team_name)
    
    # Remove team color
    if team_name in state["team_colors"]:
        state["team_colors"].pop(team_name)
    
    # Remove from team numbers if exists
    team_key = team_name.lower().replace(" ", "").replace("_", "")
    if team_key in state["team_numbers"]:
        state["team_numbers"].pop(team_key)
    
    # Emit updates to all clients
    socketio.emit("team_list_updated", {"team_scores": state["team_scores"]})
    socketio.emit("reload_home_page", {})
    
    return jsonify(success=True)


@app.route("/api/update_team_color", methods=["POST"])
def update_team_color():
    data = request.json
    team_name = data.get("team_name", "").strip()
    team_color = data.get("team_color", "").strip()
    
    if not team_name:
        return jsonify(success=False, error="Team name cannot be empty")
    
    if not team_color:
        return jsonify(success=False, error="Team color cannot be empty")
    
    if team_name not in state["team_scores"]:
        return jsonify(success=False, error="Team not found")
    
    # Validate hex color format
    if not team_color.startswith("#") or len(team_color) != 7:
        return jsonify(success=False, error="Invalid color format")
    
    # Update team color
    state["team_colors"][team_name] = team_color
    
    # Emit updates to all clients
    socketio.emit("team_color_updated", {
        "team_name": team_name,
        "team_color": team_color
    })
    
    return jsonify(success=True)


@app.route("/api/state")
def get_state():
    return jsonify(
        {
            "current_question": state["current_question"],
            "answers": state["answers"],
            "controllers": list(state["controllers"]),
            "question": questions[state["current_question"]],
        }
    )


if __name__ == "__main__":
    print(f"Game server running at http://{get_host_ip()}:5002/")
    socketio.run(app, host="0.0.0.0", port=5002, debug=True)