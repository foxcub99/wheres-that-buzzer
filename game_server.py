from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
from utils import get_host_ip

app = Flask(__name__)
socketio = SocketIO(app)

# Load questions
with open("questions.json") as f:
    questions = json.load(f)["questions"]

# Game state
state = {
    "current_question": 0,
    "answers": {},  # {controller_id: answer}
    "controllers": set(),
    "show_ip": False,
    "game_started": False,
}


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
        show_ip=state["show_ip"],
        game_started=state["game_started"],
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
    state["controllers"].add(controller_id)
    state["answers"][controller_id] = answer
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
