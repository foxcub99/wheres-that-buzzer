from pynput import keyboard
import uuid
import os

from controllers import controller_mapping


import pygame
import requests
import time
import threading
from utils import get_host_ip

GAME_SERVER_URL = "http://localhost:5002"  # Update if needed
CONTROLLER_ID = get_host_ip()


UUID_FILE = "controller_uuid.txt"
def get_or_create_uuid():
    if os.path.exists(UUID_FILE):
        with open(UUID_FILE, "r") as f:
            return f.read().strip()
    u = str(uuid.uuid4())
    with open(UUID_FILE, "w") as f:
        f.write(u)
    return u

## Legacy send_input removed: always use per-controller ID in event loop below
def register_controllers(controllers):
    try:
        for idx, joystick in controllers.items():
            name = joystick.get_name()
            joy_id = joystick.get_id()
            unique_id = get_or_create_uuid() + f"_{joy_id}"
            extra = {"name": name, "joystick_id": joy_id, "uuid": unique_id}
            resp = requests.post(
                f"{GAME_SERVER_URL}/api/register_controller",
                json={"controller_id": f"{CONTROLLER_ID}_{joy_id}", "extra": extra},
                timeout=1
            )
            if resp.ok:
                print(f"Controller {joy_id} registered with server.")
            else:
                print(f"Failed to register controller {joy_id}: {resp.text}")
    except Exception as e:
        print(f"Exception during controller registration: {e}")

def main():
    # Keyboard input using pynput
    def send_keyboard_event(device_id, answer):
        def send():
            try:
                requests.post(
                    f"{GAME_SERVER_URL}/api/answer",
                    json={
                        "controller_id": device_id,
                        "answer": answer
                    },
                    timeout=0.5
                )
            except Exception as e:
                print(f"Failed to send keyboard input: {e}")
        threading.Thread(target=send, daemon=True).start()

    def on_press(key):
        device_id = "keyboard"
        try:
            k = key.char if hasattr(key, 'char') and key.char else str(key)
        except Exception:
            k = str(key)
        print(f"Keyboard key {controller_mapping.get_button_name('Keyboard', k)} pressed")
        send_keyboard_event(device_id, k)

    def on_release(key):
        device_id = "keyboard"
        try:
            k = key.char if hasattr(key, 'char') and key.char else str(key)
        except Exception:
            k = str(key)
        print(f"Keyboard key {controller_mapping.get_button_name('Keyboard', k)} released")
        send_keyboard_event(device_id, None)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    pygame.init()
    pygame.joystick.init()
    controllers = {}
    # Detect all connected controllers
    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        controllers[i] = joystick
        print(f"Detected controller {i}: {joystick.get_name()}")
    if not controllers:
        print("No controllers detected. Keyboard input will still be processed.")

    # Register all controllers on startup and periodically
    def periodic_register():
        while True:
            register_controllers(controllers)
            time.sleep(5)

    threading.Thread(target=periodic_register, daemon=True).start()

    while True:
        for event in pygame.event.get():
            if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
                joy_id = event.joy
                button = event.button
                pressed = event.type == pygame.JOYBUTTONDOWN
                print(f"Controller {joy_id} Button {controller_mapping.get_button_name(pygame.joystick.Joystick(event.joy).get_name(), button)} {'pressed' if pressed else 'released'}")
                # Use unique controller_id for each controller
                try:
                    requests.post(
                        f"{GAME_SERVER_URL}/api/answer",
                        json={
                            "controller_id": f"{CONTROLLER_ID}_{joy_id}",
                            "answer": f"button_{button}" if pressed else None
                        },
                        timeout=0.5
                    )
                except Exception as e:
                    print(f"Failed to send input: {e}")
        time.sleep(0.01)

if __name__ == "__main__":
    main()