"""
Visualizer Integration Service

Handles integration with the shared controller visualizer component.
"""

import threading
from typing import Optional

from shared.visualizer.controller_visualizer import ControllerVisualizer
from shared.models.controller_info import ControllerInfo, ControllerType
from controller_client.models.client_state import ClientState


class VisualizerService:
    """Manages the controller visualizer for the client."""
    
    def __init__(self, client_state: ClientState):
        """Initialize visualizer service."""
        self.client_state = client_state
        self.visualizer: Optional[ControllerVisualizer] = None
        self.visualizer_thread: Optional[threading.Thread] = None
    
    def start_visualizer(self):
        """Start the standalone visualizer web interface."""
        if not self.client_state.config.enable_visualizer:
            return
        
        self.visualizer = ControllerVisualizer(standalone_mode=True)
        
        # Add keyboard controller
        self._add_keyboard_controller()
        
        # Start visualizer in separate thread
        self.visualizer_thread = threading.Thread(
            target=self.visualizer.run,
            kwargs={
                'port': self.client_state.config.visualizer_port,
                'debug': False
            },
            daemon=True
        )
        self.visualizer_thread.start()
        
        print(f"Visual controller interface started at "
              f"http://{self.client_state.config.controller_id}:"
              f"{self.client_state.config.visualizer_port}/")
    
    def add_controller(self, joystick_id: int, joystick_name: str):
        """Add a controller to the visualizer."""
        if not self.visualizer:
            return
        
        controller_info = ControllerInfo(
            id=self.client_state.get_controller_id(joystick_id),
            name=joystick_name,
            controller_type=self._determine_controller_type(joystick_name),
            ip_address=self.client_state.config.controller_id,
            joystick_id=joystick_id
        )
        
        self.visualizer.add_controller(controller_info)
    
    def remove_controller(self, joystick_id: int):
        """Remove a controller from the visualizer."""
        if not self.visualizer:
            return
        
        controller_id = self.client_state.get_controller_id(joystick_id)
        self.visualizer.remove_controller(controller_id)
    
    def button_pressed(self, device_id: str, button: str, 
                      button_name: str = None):
        """Handle button press event for visualizer."""
        if not self.visualizer:
            return
        
        self.visualizer.button_pressed(device_id, button, button_name)
    
    def button_released(self, device_id: str, button: str,
                       button_name: str = None):
        """Handle button release event for visualizer."""
        if not self.visualizer:
            return
        
        self.visualizer.button_released(device_id, button, button_name)
    
    def flash_controller(self, device_id: str):
        """Flash a controller to show activity."""
        if not self.visualizer:
            return
        
        self.visualizer.flash_controller(device_id)
    
    def _add_keyboard_controller(self):
        """Add keyboard as a controller to visualizer."""
        if not self.visualizer:
            return
        
        keyboard_info = ControllerInfo(
            id="keyboard",
            name="Keyboard",
            controller_type=ControllerType.KEYBOARD,
            ip_address=self.client_state.config.controller_id
        )
        
        self.visualizer.add_controller(keyboard_info)
    
    def _determine_controller_type(self, name: str) -> ControllerType:
        """Determine controller type from name."""
        name_lower = name.lower()
        
        if 'xbox' in name_lower:
            return ControllerType.XBOX
        elif 'playstation' in name_lower or 'ps' in name_lower:
            return ControllerType.PLAYSTATION
        elif 'switch' in name_lower or 'nintendo' in name_lower:
            return ControllerType.NINTENDO_SWITCH
        elif 'joy-con' in name_lower:
            if 'left' in name_lower or '(l)' in name_lower:
                return ControllerType.JOY_CON_L
            else:
                return ControllerType.JOY_CON_R
        else:
            return ControllerType.UNKNOWN
