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
    # Pick up to 3 unique random buttons
    chosen = random.sample(button_ids, min(3, len(button_ids)))
    # Assign unique buttons to teams, fill with 0 if not enough
    state["team_numbers"]["team1"] = chosen[0] if len(chosen) > 0 else 0
    state["team_numbers"]["team2"] = chosen[1] if len(chosen) > 1 else 0
    state["team_numbers"]["team3"] = chosen[2] if len(chosen) > 2 else 0
    # Emit update so team pages reload
    socketio.emit("controllers_update", {
        "controllers": list(state["controllers"]),
        "controller_infos": state.get("controller_infos", {})
    })
    socketio.emit('reload_team_pages')
    state['selected_controller'] = cid
    print(f"Selected controller set to: {cid}")
    socketio.emit('selected_controller', {'controller_id': cid})

@app.route("/api/register_controller", methods=["POST"])
def register_controller():
    data = request.json
    controller_id = data.get("controller_id")
    controller_info = {
        "id": controller_id,
        "ip": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
        "extra": data.get("extra", {})
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
        return jsonify({"status": "ok", "controllers": list(state["controllers"]), "controller_infos": state["controller_infos"]})
    return jsonify({"status": "error", "message": "No controller_id provided"}), 400

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

@app.route("/team1")
def team1_page():
    num = state["team_numbers"]["team1"]
    btn_name = get_team_button_name("team1")
    return render_template("team1.html", team_number=num, button_name=btn_name)

@app.route("/team2")
def team2_page():
    num = state["team_numbers"]["team2"]
    btn_name = get_team_button_name("team2")
    return render_template("team2.html", team_number=num, button_name=btn_name)

@app.route("/team3")
def team3_page():
    num = state["team_numbers"]["team3"]
    btn_name = get_team_button_name("team3")
    return render_template("team3.html", team_number=num, button_name=btn_name)

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
    # Store random numbers for each team, start at 0
    "team_numbers": {
        "team1": 0,
        "team2": 0,
        "team3": 0
    }
}
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
        return render_template("home.html", show_ip=state["show_ip"], ip=get_host_ip())
    else:
        q = questions[state["current_question"]]
        return render_template(
            "game.html",
            question=q,
            question_num=state["current_question"] + 1,
            total=len(questions),
            team_scores=state["team_scores"],
            last_team_pressed=state.get("last_team_pressed")
        )


@app.route("/master")
def master_ui():
    q = questions[state["current_question"]]
    return render_template(
        "game_master.html",
        question=q,
        question_num=state["current_question"] + 1,
        total=len(questions),
        controllers=list(state["controllers"]),
        controller_infos=state.get("controller_infos", {}),
        show_ip=state["show_ip"],
        game_started=state["game_started"],
        team_scores=state["team_scores"]
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
        # Emit event to all clients
        socketio.emit(
            "question_changed",
            {
                "current_question": state["current_question"],
                "question": questions[state["current_question"]],
            },
        )
    return jsonify(success=True)


@app.route("/api/prev", methods=["POST"])
def prev_question():
    if state["current_question"] > 0:
        state["current_question"] -= 1
        state["answers"] = {}
        # Emit event to all clients
        socketio.emit(
            "question_changed",
            {
                "current_question": state["current_question"],
                "question": questions[state["current_question"]],
            },
        )
    return jsonify(success=True)


@app.route("/api/answer", methods=["POST"])
def submit_answer():
    data = request.json
    controller_id = data.get("controller_id")
    answer = data.get("answer")
    print(f"Received input from controller: {controller_id}, input: {answer}")
    state["controllers"].add(controller_id)
    state["answers"][controller_id] = answer
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
                # Extract number from 'button_X' or use as int if already a number
                if isinstance(answer, str) and answer.startswith("button_"):
                    btn_num = int(answer.split("_")[1])
                else:
                    btn_num = int(answer)
                if btn_num == num:
                    matched_team = team
                    break
        except Exception:
            pass
    if matched_team:

        print(f"Team {matched_team[-1]} has matched!")
        os.system(f'afplay sounds/team_{matched_team[-1]}.mp3')
        state["last_team_pressed"] = matched_team
        # Regenerate all team numbers
        for t in state["team_numbers"]:
            state["team_numbers"][t] = random.randint(0, 3)
        socketio.emit("team_pressed", {"team": matched_team})
        socketio.emit("reload_post_buzz", {})
        socketio.emit("reload_team_pages", {})
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