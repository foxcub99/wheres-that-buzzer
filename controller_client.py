from flask import Flask, render_template, request, jsonify
import requests
import threading
from utils import get_host_ip

app = Flask(__name__)

# Config
GAME_SERVER_URL = "http://localhost:5000"  # Change to actual server IP if needed
controller_id = get_host_ip()

# Simulated input state
input_state = {
    "buttons": {},  # e.g., {"A": False, "B": True}
}


@app.route("/")
def controller_status():
    # Web UI for controller status
    return render_template(
        "controller_status.html", controller_id=controller_id, input_state=input_state
    )


@app.route("/api/input", methods=["POST"])
def receive_input():
    data = request.json
    button = data.get("button")
    pressed = data.get("pressed")
    input_state["buttons"][button] = pressed
    # Relay to game server
    requests.post(
        f"{GAME_SERVER_URL}/api/answer",
        json={"controller_id": controller_id, "answer": button if pressed else None},
    )
    return jsonify(success=True)


@app.route("/api/status")
def get_status():
    return jsonify({"controller_id": controller_id, "input_state": input_state})


if __name__ == "__main__":
    print(f"Controller client running at http://{get_host_ip()}:5001/")
    app.run(host="0.0.0.0", port=5001, debug=True)
