from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import requests
import threading
from utils import get_host_ip
from pynput import keyboard
import pygame

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



# Pygame gamepad thread for Xbox, DualSense, Switch Pro
def pygame_thread():
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    print("Detected controllers:")
    for joystick in joysticks:
        print(f"- {joystick.get_name()} (ID: {joystick.get_id()})")
    for joystick in joysticks:
        joystick.init()
        device_id = f"controller_{joystick.get_id()}_{joystick.get_name()}"
        if device_id not in input_state:
            input_state[device_id] = {"name": joystick.get_name()}
    emit_input_update()
    while True:
        for joystick in joysticks:
            device_id = f"controller_{joystick.get_id()}_{joystick.get_name()}"
            if device_id not in input_state:
                input_state[device_id] = {"name": joystick.get_name()}
            # Poll axes
            for a in range(joystick.get_numaxes()):
                axis_val = joystick.get_axis(a)
                input_state[device_id][f"axis_{a}"] = axis_val
            # Poll buttons
            for b in range(joystick.get_numbuttons()):
                prev_val = input_state[device_id].get(f"button_{b}", False)
                btn_val = joystick.get_button(b)
                input_state[device_id][f"button_{b}"] = bool(btn_val)
                if bool(btn_val) and not prev_val:
                    print(f"{joystick.get_name()} (ID: {joystick.get_id()}): Button {b} PRESSED")
                elif not bool(btn_val) and prev_val:
                    print(f"{joystick.get_name()} (ID: {joystick.get_id()}): Button {b} RELEASED")
            # Poll hats
            for h in range(joystick.get_numhats()):
                hat_val = joystick.get_hat(h)
                input_state[device_id][f"hat_{h}"] = hat_val
        emit_input_update()
        pygame.time.wait(20)


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
    threading.Thread(target=pygame_thread, daemon=True).start()
    threading.Thread(target=keyboard_thread, daemon=True).start()


if __name__ == "__main__":
    print(f"Controller client running at http://{get_host_ip()}:5001/")
    import multiprocessing
    # Start Flask in a separate process
    def run_flask():
        start_input_threads()
        socketio.run(app, host="0.0.0.0", port=5001, debug=True)

    flask_proc = multiprocessing.Process(target=run_flask)
    flask_proc.start()

    # Minimal pygame window and event loop for controller events
    import pygame
    pygame.init()
    pygame.joystick.init()
    screen = pygame.display.set_mode((200, 100))
    pygame.display.set_caption("Controller Input Event Loop")
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joystick in joysticks:
        joystick.init()
        print(f"Detected: {joystick.get_name()} (ID: {joystick.get_instance_id()})")
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.JOYBUTTONDOWN:
                print(f"Controller {event.instance_id}: Button {event.button} PRESSED")
            elif event.type == pygame.JOYBUTTONUP:
                print(f"Controller {event.instance_id}: Button {event.button} RELEASED")
        pygame.time.wait(10)
    pygame.quit()
    flask_proc.terminate()
