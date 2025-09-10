"""
Keyboard Input Handler

Handles keyboard input events using pynput.
"""

from pynput import keyboard
from typing import Optional

from controllers import controller_mapping
from controller_client.models.client_state import ClientState
from controller_client.services.network_service import NetworkService
from controller_client.services.visualizer_service import VisualizerService


class KeyboardHandler:
    """Handles keyboard input events."""
    
    def __init__(self, client_state: ClientState, 
                 network_service: NetworkService,
                 visualizer_service: Optional[VisualizerService] = None):
        """Initialize keyboard handler."""
        self.client_state = client_state
        self.network_service = network_service
        self.visualizer_service = visualizer_service
        self.listener: Optional[keyboard.Listener] = None
    
    def start_listening(self):
        """Start listening for keyboard events."""
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()
        print("Keyboard input handler started")
    
    def stop_listening(self):
        """Stop listening for keyboard events."""
        if self.listener:
            self.listener.stop()
            self.listener = None
            print("Keyboard input handler stopped")
    
    def _on_press(self, key):
        """Handle keyboard key press."""
        device_id = "keyboard"
        key_string = self._key_to_string(key)
        button_name = controller_mapping.get_button_name('Keyboard', key_string)
        
        print(f"Keyboard key {button_name} pressed")
        
        # Send to server
        self.network_service.send_input_event(device_id, key_string)
        
        # Update visualizer
        if self.visualizer_service:
            self.visualizer_service.button_pressed(
                device_id, key_string, button_name
            )
    
    def _on_release(self, key):
        """Handle keyboard key release."""
        device_id = "keyboard"
        key_string = self._key_to_string(key)
        button_name = controller_mapping.get_button_name('Keyboard', key_string)
        
        print(f"Keyboard key {button_name} released")
        
        # Send to server (None indicates release)
        self.network_service.send_input_event(device_id, None)
        
        # Update visualizer
        if self.visualizer_service:
            self.visualizer_service.button_released(
                device_id, key_string, button_name
            )
    
    def _key_to_string(self, key) -> str:
        """Convert key object to string representation."""
        try:
            return key.char if hasattr(key, 'char') and key.char else str(key)
        except AttributeError:
            return str(key)
