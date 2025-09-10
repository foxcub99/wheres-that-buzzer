"""
Example integration of shared visualizer with game server.

This shows how the game server would use the shared controller visualizer
on the master page.
"""

from flask import Blueprint, render_template
from shared.visualizer.controller_visualizer import ControllerVisualizer
from shared.models.controller_info import ControllerInfo

# In your game_server/services/visualizer_service.py
class VisualizerService:
    """Service to manage controller visualization in game server."""
    
    def __init__(self, socketio):
        """Initialize with existing socketio instance."""
        # Integrate with existing Flask app instead of standalone
        self.visualizer = ControllerVisualizer(standalone_mode=False)
        self.visualizer.integrate_with_app(None, socketio, "/visualizer")
    
    def sync_controllers_from_game_state(self, controller_infos: dict):
        """Sync controllers from game state to visualizer."""
        # Clear existing controllers
        for controller_id in list(self.visualizer.controllers.keys()):
            if controller_id not in controller_infos:
                self.visualizer.remove_controller(controller_id)
        
        # Add/update controllers
        for controller_id, info_dict in controller_infos.items():
            controller_info = ControllerInfo.from_dict(info_dict)
            self.visualizer.add_controller(controller_info)
    
    def handle_button_event(self, controller_id: str, button: str, 
                           pressed: bool, button_name: str = None):
        """Handle button events from game input."""
        if pressed:
            self.visualizer.button_pressed(controller_id, button, button_name)
        else:
            self.visualizer.button_released(controller_id, button, button_name)
    
    def flash_controller(self, controller_id: str):
        """Flash a controller to show activity."""
        self.visualizer.flash_controller(controller_id)
    
    def get_visualizer_html_for_master(self) -> str:
        """Get HTML snippet for embedding in master page."""
        return '''
        <div id="controller-visualizer">
            <h3>Controller Status</h3>
            <div id="visualizer-container"></div>
        </div>
        <script>
            // JavaScript to render controllers and handle real-time updates
            // This would use the shared controller templates
        </script>
        '''

# In your master template (templates/game_master.html)
# You would add: {{ visualizer_html|safe }}
