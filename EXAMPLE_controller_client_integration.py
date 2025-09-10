"""
Example integration of shared visualizer with controller client.

This shows how the controller client would use the shared controller 
visualizer as a standalone web interface.
"""

from shared.visualizer.controller_visualizer import ControllerVisualizer
from shared.models.controller_info import ControllerInfo, ControllerType

# In your future controller_client/services/visualizer_service.py
class ControllerClientVisualizerService:
    """Manage controller visualization for controller client."""
    
    def __init__(self):
        """Initialize standalone visualizer."""
        # Run as standalone Flask app on different port
        self.visualizer = ControllerVisualizer(standalone_mode=True)
    
    def add_detected_controller(self, joystick_id: int, joystick_name: str, 
                               controller_id: str):
        """Add a newly detected controller."""
        controller_info = ControllerInfo(
            id=controller_id,
            name=joystick_name,
            controller_type=self._determine_controller_type(joystick_name),
            joystick_id=joystick_id,
            status="active"
        )
        self.visualizer.add_controller(controller_info)
    
    def add_keyboard_controller(self, host_ip: str):
        """Add keyboard as a controller."""
        controller_info = ControllerInfo(
            id="keyboard",
            name="Keyboard",
            controller_type=ControllerType.KEYBOARD,
            ip_address=host_ip,
            status="active"
        )
        self.visualizer.add_controller(controller_info)
    
    def handle_input_event(self, controller_id: str, button: str, 
                          pressed: bool, button_name: str = None):
        """Handle input from controllers/keyboard."""
        if pressed:
            self.visualizer.button_pressed(controller_id, button, button_name)
            # Also flash to show activity
            self.visualizer.flash_controller(controller_id)
        else:
            self.visualizer.button_released(controller_id, button, button_name)
    
    def remove_controller(self, controller_id: str):
        """Remove disconnected controller."""
        self.visualizer.remove_controller(controller_id)
    
    def run_visualizer(self, port: int = 5003):
        """Start the visualizer web interface."""
        self.visualizer.run(port=port)
    
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

# Usage in refactored controller_client main:
"""
# In controller_client/app.py
def create_controller_client():
    # ... other setup ...
    
    if args.visualizer:
        visualizer_service = ControllerClientVisualizerService()
        # Run visualizer in separate thread
        visualizer_thread = threading.Thread(
            target=visualizer_service.run_visualizer,
            kwargs={'port': 5003},
            daemon=True
        )
        visualizer_thread.start()
    
    return controller_client, visualizer_service
"""
