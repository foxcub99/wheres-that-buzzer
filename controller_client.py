from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import requests
import threading
from utils import get_host_ip
from inputs import devices, get_gamepad
from pynput import keyboard

app = Flask(__name__)
socketio = SocketIO(app)

# Config
GAME_SERVER_URL = "http://localhost:5000"  # Change to actual server IP if needed
controller_id = get_host_ip()


# Input state: {device_id: {button: pressed}}
input_state = {}

# Track connected devices
connected_devices = set()


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
@socketio.on("connect")
def handle_connect():
    socketio.emit(
        "input_update", {"controller_id": controller_id, "input_state": input_state}
    )


def emit_input_update():
    socketio.emit(
        "input_update", {"controller_id": controller_id, "input_state": input_state}
    )


def gamepad_thread():
    while True:
        try:
            events = get_gamepad()
            for event in events:
                device_id = "gamepad"
                if device_id not in input_state:
                    input_state[device_id] = {}
                input_state[device_id][event.code] = event.state
            emit_input_update()
        except Exception:
            pass


def keyboard_thread():
    def on_press(key):
        device_id = "keyboard"
        if device_id not in input_state:
            input_state[device_id] = {}
        try:
            k = key.char
        except:
            k = str(key)
        input_state[device_id][k] = True
        emit_input_update()

    def on_release(key):
        device_id = "keyboard"
        if device_id not in input_state:
            input_state[device_id] = {}
        try:
            k = key.char
        except:
            k = str(key)
        input_state[device_id][k] = False
        emit_input_update()

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()


def start_input_threads():
    threading.Thread(target=gamepad_thread, daemon=True).start()
    threading.Thread(target=keyboard_thread, daemon=True).start()


if __name__ == "__main__":
    print(f"Controller client running at http://{get_host_ip()}:5001/")
    start_input_threads()
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
