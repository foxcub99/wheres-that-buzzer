from pynput import keyboard
import uuid
import os
import argparse
import threading

from controllers import controller_mapping


import pygame
import requests
import time
from utils import get_host_ip

GAME_SERVER_URL = "http://localhost:5002"  # Update if needed
CONTROLLER_ID = get_host_ip()

# Global visualizer instance
visualizer_instance = None


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

def send_controller_status(controller_id, status):
    """Send controller status update to game server"""
    try:
        requests.post(
            f"{GAME_SERVER_URL}/api/controller_status",
            json={
                "controller_id": controller_id,
                "status": status  # "active" or "inactive"
            },
            timeout=0.5
        )
    except requests.RequestException as e:
        print(f"Failed to send controller status: {e}")


def detect_controllers():
    """Detect currently connected controllers"""
    pygame.joystick.quit()
    pygame.joystick.init()
    current_controllers = {}
    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        current_controllers[i] = joystick
    return current_controllers


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Controller Client')
    parser.add_argument('--visualizer', action='store_true',
                        help='Start visual controller interface')
    args = parser.parse_args()
    
    # Start visualizer if requested
    if args.visualizer:
        from controller_visualizer import ControllerVisualizer
        global visualizer_instance
        visualizer_instance = ControllerVisualizer()
        visualizer_thread = threading.Thread(
            target=visualizer_instance.run,
            kwargs={'port': 5003, 'debug': False},
            daemon=True
        )
        visualizer_thread.start()
        host_ip = get_host_ip()
        print(f"Visual controller interface started at http://{host_ip}:5003/")
    
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
            except requests.RequestException as e:
                print(f"Failed to send keyboard input: {e}")
        threading.Thread(target=send, daemon=True).start()

    def on_press(key):
        device_id = "keyboard"
        try:
            k = key.char if hasattr(key, 'char') and key.char else str(key)
        except Exception:
            k = str(key)
        button_name = controller_mapping.get_button_name('Keyboard', k)
        print(f"Keyboard key {button_name} pressed")
        send_keyboard_event(device_id, k)
        
        # Update visualizer if running
        if visualizer_instance:
            visualizer_instance.button_pressed(device_id, k, button_name)

    def on_release(key):
        device_id = "keyboard"
        try:
            k = key.char if hasattr(key, 'char') and key.char else str(key)
        except Exception:
            k = str(key)
        button_name = controller_mapping.get_button_name('Keyboard', k)
        print(f"Keyboard key {button_name} released")
        send_keyboard_event(device_id, None)
        
        # Update visualizer if running
        if visualizer_instance:
            visualizer_instance.button_released(device_id, k, button_name)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    pygame.init()
    pygame.joystick.init()
    
    # Register keyboard with visualizer if running
    if visualizer_instance:
        keyboard_info = {
            "id": "keyboard",
            "ip": get_host_ip(),
            "extra": {"name": "Keyboard"}
        }
        visualizer_instance.update_controller("keyboard", keyboard_info)
    
    # Track controllers and their status
    controllers = {}
    last_controller_count = 0

    # Initial controller detection
    controllers = detect_controllers()
    for i, joystick in controllers.items():
        print(f"Detected controller {i}: {joystick.get_name()}")
    if not controllers:
        print("No controllers detected. Keyboard input will still work.")

    # Dynamic controller detection and registration
    def dynamic_controller_manager():
        nonlocal controllers, last_controller_count
        while True:
            try:
                # Detect current controllers
                current_controllers = detect_controllers()
                current_count = len(current_controllers)
                
                # Check for newly connected controllers
                for i, joystick in current_controllers.items():
                    if i not in controllers:
                        print(f"New controller detected {i}: "
                              f"{joystick.get_name()}")
                        controllers[i] = joystick
                        # Register new controller immediately
                        register_controllers({i: joystick})
                        send_controller_status(f"{CONTROLLER_ID}_{i}",
                                               "active")
                        
                        # Update visualizer if running
                        if visualizer_instance:
                            controller_info = {
                                "id": f"{CONTROLLER_ID}_{i}",
                                "ip": get_host_ip(),
                                "extra": {
                                    "name": joystick.get_name(),
                                    "joystick_id": i
                                }
                            }
                            visualizer_instance.update_controller(
                                f"{CONTROLLER_ID}_{i}", controller_info)
                
                # Check for disconnected controllers
                for i in list(controllers.keys()):
                    if i not in current_controllers:
                        print(f"Controller {i} disconnected")
                        send_controller_status(f"{CONTROLLER_ID}_{i}",
                                               "inactive")
                        # Update visualizer if running
                        if visualizer_instance:
                            visualizer_instance.remove_controller(
                                f"{CONTROLLER_ID}_{i}")
                        del controllers[i]
                
                # Re-register all active controllers periodically
                if controllers:
                    register_controllers(controllers)
                    for i in controllers.keys():
                        send_controller_status(f"{CONTROLLER_ID}_{i}",
                                               "active")
                
                last_controller_count = current_count
            except Exception as e:
                print(f"Error in controller detection: {e}")
            
            time.sleep(2)  # Check every 2 seconds

    threading.Thread(target=dynamic_controller_manager, daemon=True).start()

    while True:
        for event in pygame.event.get():
            if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
                joy_id = event.joy
                button = event.button
                pressed = event.type == pygame.JOYBUTTONDOWN
                joystick = pygame.joystick.Joystick(event.joy)
                button_name = controller_mapping.get_button_name(
                    joystick.get_name(), button)
                status = 'pressed' if pressed else 'released'
                print(f"Controller {joy_id} Button {button_name} {status}")
                # Use unique controller_id for each controller
                controller_id = f"{CONTROLLER_ID}_{joy_id}"
                try:
                    requests.post(
                        f"{GAME_SERVER_URL}/api/answer",
                        json={
                            "controller_id": controller_id,
                            "answer": f"button_{button}" if pressed else None
                        },
                        timeout=0.5
                    )
                    
                    # Update visualizer if running
                    if visualizer_instance:
                        if pressed:
                            visualizer_instance.button_pressed(
                                controller_id, button, button_name)
                        else:
                            visualizer_instance.button_released(
                                controller_id, button, button_name)
                                
                except requests.RequestException as e:
                    print(f"Failed to send input: {e}")
        time.sleep(0.01)


if __name__ == "__main__":
    main()
