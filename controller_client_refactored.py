"""
Refactored controller client following Python best practices.
This is an example of better structure - you don't need to use this file.
"""
from pynput import keyboard
import uuid
import os
import argparse
import threading
import pygame
import requests
import time
from controllers import controller_mapping
from utils import get_host_ip

GAME_SERVER_URL = "http://localhost:5002"
CONTROLLER_ID = get_host_ip()
UUID_FILE = "controller_uuid.txt"


class ControllerClient:
    """Main controller client class to manage state and operations."""
    
    def __init__(self):
        self.visualizer_instance = None
        self.controllers = {}
        self.last_controller_count = 0
        
    def get_or_create_uuid(self):
        """Get or create a unique UUID for this controller client."""
        if os.path.exists(UUID_FILE):
            with open(UUID_FILE, "r") as f:
                return f.read().strip()
        u = str(uuid.uuid4())
        with open(UUID_FILE, "w") as f:
            f.write(u)
        return u

    def register_controllers(self, controllers):
        """Register controllers with the game server."""
        try:
            for idx, joystick in controllers.items():
                name = joystick.get_name()
                joy_id = joystick.get_id()
                unique_id = self.get_or_create_uuid() + f"_{joy_id}"
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

    def send_controller_status(self, controller_id, status):
        """Send controller status update to game server."""
        try:
            requests.post(
                f"{GAME_SERVER_URL}/api/controller_status",
                json={"controller_id": controller_id, "status": status},
                timeout=0.5
            )
        except requests.RequestException as e:
            print(f"Failed to send controller status: {e}")

    def detect_controllers(self):
        """Detect currently connected controllers."""
        pygame.joystick.quit()
        pygame.joystick.init()
        current_controllers = {}
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            current_controllers[i] = joystick
        return current_controllers

    def send_keyboard_event(self, device_id, answer):
        """Send keyboard event to server in a separate thread."""
        def send():
            try:
                requests.post(
                    f"{GAME_SERVER_URL}/api/answer",
                    json={"controller_id": device_id, "answer": answer},
                    timeout=0.5
                )
            except requests.RequestException as e:
                print(f"Failed to send keyboard input: {e}")
        threading.Thread(target=send, daemon=True).start()

    def on_key_press(self, key):
        """Handle keyboard key press events."""
        device_id = "keyboard"
        try:
            k = key.char if hasattr(key, 'char') and key.char else str(key)
        except Exception:
            k = str(key)
        button_name = controller_mapping.get_button_name('Keyboard', k)
        print(f"Keyboard key {button_name} pressed")
        self.send_keyboard_event(device_id, k)
        
        if self.visualizer_instance:
            self.visualizer_instance.button_pressed(device_id, k, button_name)

    def on_key_release(self, key):
        """Handle keyboard key release events."""
        device_id = "keyboard"
        try:
            k = key.char if hasattr(key, 'char') and key.char else str(key)
        except Exception:
            k = str(key)
        button_name = controller_mapping.get_button_name('Keyboard', k)
        print(f"Keyboard key {button_name} released")
        self.send_keyboard_event(device_id, None)
        
        if self.visualizer_instance:
            self.visualizer_instance.button_released(device_id, k, button_name)

    def setup_keyboard_listener(self):
        """Set up keyboard input listener."""
        listener = keyboard.Listener(
            on_press=self.on_key_press, 
            on_release=self.on_key_release
        )
        listener.start()
        
        # Register keyboard with visualizer if running
        if self.visualizer_instance:
            keyboard_info = {
                "id": "keyboard",
                "ip": get_host_ip(),
                "extra": {"name": "Keyboard"}
            }
            self.visualizer_instance.update_controller("keyboard", keyboard_info)

    def dynamic_controller_manager(self):
        """Continuously monitor for controller connections/disconnections."""
        while True:
            try:
                current_controllers = self.detect_controllers()
                
                # Check for newly connected controllers
                for i, joystick in current_controllers.items():
                    if i not in self.controllers:
                        print(f"New controller detected {i}: {joystick.get_name()}")
                        self.controllers[i] = joystick
                        self.register_controllers({i: joystick})
                        self.send_controller_status(f"{CONTROLLER_ID}_{i}", "active")
                        
                        if self.visualizer_instance:
                            controller_info = {
                                "id": f"{CONTROLLER_ID}_{i}",
                                "ip": get_host_ip(),
                                "extra": {"name": joystick.get_name(), "joystick_id": i}
                            }
                            self.visualizer_instance.update_controller(
                                f"{CONTROLLER_ID}_{i}", controller_info)
                
                # Check for disconnected controllers
                for i in list(self.controllers.keys()):
                    if i not in current_controllers:
                        print(f"Controller {i} disconnected")
                        self.send_controller_status(f"{CONTROLLER_ID}_{i}", "inactive")
                        if self.visualizer_instance:
                            self.visualizer_instance.remove_controller(f"{CONTROLLER_ID}_{i}")
                        del self.controllers[i]
                
                # Re-register all active controllers periodically
                if self.controllers:
                    self.register_controllers(self.controllers)
                    for i in self.controllers.keys():
                        self.send_controller_status(f"{CONTROLLER_ID}_{i}", "active")
                        
            except Exception as e:
                print(f"Error in controller detection: {e}")
            
            time.sleep(2)

    def setup_visualizer(self):
        """Set up the controller visualizer if requested."""
        from controller_visualizer import ControllerVisualizer
        self.visualizer_instance = ControllerVisualizer()
        visualizer_thread = threading.Thread(
            target=self.visualizer_instance.run,
            kwargs={'port': 5003, 'debug': False},
            daemon=True
        )
        visualizer_thread.start()
        host_ip = get_host_ip()
        print(f"Visual controller interface started at http://{host_ip}:5003/")

    def handle_controller_events(self):
        """Main event loop for handling controller input."""
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
                        
                        if self.visualizer_instance:
                            if pressed:
                                self.visualizer_instance.button_pressed(
                                    controller_id, button, button_name)
                            else:
                                self.visualizer_instance.button_released(
                                    controller_id, button, button_name)
                                    
                    except requests.RequestException as e:
                        print(f"Failed to send input: {e}")
            time.sleep(0.01)

    def run(self, enable_visualizer=False):
        """Main run method to start the controller client."""
        # Set up visualizer if requested
        if enable_visualizer:
            self.setup_visualizer()
        
        # Set up keyboard listener
        self.setup_keyboard_listener()
        
        # Initialize pygame
        pygame.init()
        pygame.joystick.init()
        
        # Initial controller detection
        self.controllers = self.detect_controllers()
        for i, joystick in self.controllers.items():
            print(f"Detected controller {i}: {joystick.get_name()}")
        if not self.controllers:
            print("No controllers detected. Keyboard input will still work.")
        
        # Start controller monitoring thread
        threading.Thread(target=self.dynamic_controller_manager, daemon=True).start()
        
        # Start main event loop
        self.handle_controller_events()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Controller Client')
    parser.add_argument('--visualizer', action='store_true',
                        help='Start visual controller interface')
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    client = ControllerClient()
    client.run(enable_visualizer=args.visualizer)


if __name__ == "__main__":
    main()
