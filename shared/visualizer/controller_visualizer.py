"""
Controller Visualizer

Shared visualizer component that can be used by both game_server and 
controller_client to display controller states.
"""

from typing import Dict, List, Optional
from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import time

from shared.models.controller_info import ControllerInfo, ControllerType


class ControllerVisualizer:
    """
    Shared controller visualizer that can be embedded in different applications.
    """
    
    def __init__(self, standalone_mode: bool = True):
        """
        Initialize the controller visualizer.
        
        Args:
            standalone_mode: If True, creates its own Flask app. 
                           If False, can be integrated into existing app.
        """
        self.standalone_mode = standalone_mode
        self.controllers: Dict[str, ControllerInfo] = {}
        self.button_states: Dict[str, Dict] = {}
        self.flash_states: Dict[str, float] = {}
        
        if standalone_mode:
            self.app = Flask(__name__)
            self.socketio = SocketIO(self.app, cors_allowed_origins="*")
            self._setup_routes()
        else:
            self.app = None
            self.socketio = None
    
    def integrate_with_app(self, app: Flask, socketio: SocketIO, 
                          url_prefix: str = "/visualizer"):
        """
        Integrate with existing Flask app and SocketIO instance.
        
        Args:
            app: Existing Flask application
            socketio: Existing SocketIO instance
            url_prefix: URL prefix for visualizer routes
        """
        self.app = app
        self.socketio = socketio
        self.url_prefix = url_prefix
        self._setup_integrated_routes()
    
    def add_controller(self, controller_info: ControllerInfo):
        """Add or update a controller."""
        self.controllers[controller_info.id] = controller_info
        self.button_states[controller_info.id] = {}
        
        if self.socketio:
            self.socketio.emit('controller_added', {
                'controller': controller_info.to_dict()
            })
    
    def remove_controller(self, controller_id: str):
        """Remove a controller."""
        self.controllers.pop(controller_id, None)
        self.button_states.pop(controller_id, None)
        self.flash_states.pop(controller_id, None)
        
        if self.socketio:
            self.socketio.emit('controller_removed', {
                'controller_id': controller_id
            })
    
    def button_pressed(self, controller_id: str, button: str, 
                      button_name: str = None):
        """Handle button press event."""
        if controller_id in self.button_states:
            self.button_states[controller_id][button] = True
            
            if self.socketio:
                self.socketio.emit('button_pressed', {
                    'controller_id': controller_id,
                    'button': button,
                    'button_name': button_name or button
                })
    
    def button_released(self, controller_id: str, button: str,
                       button_name: str = None):
        """Handle button release event."""
        if controller_id in self.button_states:
            self.button_states[controller_id].pop(button, None)
            
            if self.socketio:
                self.socketio.emit('button_released', {
                    'controller_id': controller_id,
                    'button': button,
                    'button_name': button_name or button
                })
    
    def flash_controller(self, controller_id: str, duration: float = 0.5):
        """Flash a controller to indicate activity."""
        self.flash_states[controller_id] = time.time() + duration
        
        if self.socketio:
            self.socketio.emit('controller_flash', {
                'controller_id': controller_id,
                'duration': duration
            })
    
    def get_controller_html(self, controller_info: ControllerInfo) -> str:
        """Generate HTML for a specific controller type."""
        if controller_info.controller_type == ControllerType.KEYBOARD:
            return self._render_keyboard()
        elif controller_info.controller_type == ControllerType.XBOX:
            return self._render_xbox_controller()
        elif controller_info.controller_type == ControllerType.PLAYSTATION:
            return self._render_playstation_controller()
        else:
            return self._render_generic_controller(controller_info)
    
    def _setup_routes(self):
        """Setup routes for standalone mode."""
        @self.app.route('/')
        def index():
            return render_template_string(self._get_main_template())
        
        @self.app.route('/api/controllers')
        def get_controllers():
            return jsonify({
                'controllers': [c.to_dict() for c in self.controllers.values()],
                'button_states': self.button_states
            })
    
    def _setup_integrated_routes(self):
        """Setup routes when integrated with existing app."""
        # Register routes with the existing app using url_prefix
        pass  # Implementation would add routes to existing app
    
    def _render_keyboard(self) -> str:
        """Render keyboard layout."""
        return '''
        <div class="keyboard-layout">
            <div class="key-row">
                <div class="key" data-key="q">Q</div>
                <div class="key" data-key="w">W</div>
                <div class="key" data-key="e">E</div>
                <div class="key" data-key="r">R</div>
            </div>
            <!-- Add more key rows as needed -->
        </div>
        '''
    
    def _render_xbox_controller(self) -> str:
        """Render Xbox controller layout."""
        return '''
        <div class="xbox-controller">
            <svg viewBox="0 0 400 300" class="controller-svg">
                <!-- Xbox controller SVG elements -->
                <circle cx="320" cy="120" r="15" class="button" data-button="0"/>
                <circle cx="340" cy="100" r="15" class="button" data-button="1"/>
                <circle cx="340" cy="140" r="15" class="button" data-button="2"/>
                <circle cx="360" cy="120" r="15" class="button" data-button="3"/>
            </svg>
        </div>
        '''
    
    def _render_playstation_controller(self) -> str:
        """Render PlayStation controller layout."""
        return '''
        <div class="playstation-controller">
            <svg viewBox="0 0 400 300" class="controller-svg">
                <!-- PlayStation controller SVG elements -->
                <circle cx="320" cy="120" r="15" class="button" data-button="0"/>
                <circle cx="340" cy="100" r="15" class="button" data-button="1"/>
                <circle cx="340" cy="140" r="15" class="button" data-button="2"/>
                <circle cx="360" cy="120" r="15" class="button" data-button="3"/>
            </svg>
        </div>
        '''
    
    def _render_generic_controller(self, controller_info: ControllerInfo) -> str:
        """Render generic controller layout."""
        return f'''
        <div class="generic-controller">
            <h3>{controller_info.name}</h3>
            <div class="button-grid">
                <!-- Generic button grid -->
            </div>
        </div>
        '''
    
    def _get_main_template(self) -> str:
        """Get the main HTML template for the visualizer."""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Controller Visualizer</title>
            <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
            <style>
                .controller-container { 
                    display: flex; 
                    flex-wrap: wrap; 
                    gap: 20px; 
                    padding: 20px; 
                }
                .controller { 
                    border: 2px solid #ccc; 
                    border-radius: 10px; 
                    padding: 15px; 
                    background: #f9f9f9; 
                }
                .controller.active { border-color: #4CAF50; }
                .controller.flashing { 
                    animation: flash 0.5s ease-in-out; 
                }
                .button { 
                    fill: #e0e0e0; 
                    stroke: #999; 
                    stroke-width: 2; 
                }
                .button.pressed { fill: #ff6b6b; }
                
                @keyframes flash {
                    0%, 100% { background-color: #f9f9f9; }
                    50% { background-color: #ffeb3b; }
                }
            </style>
        </head>
        <body>
            <h1>Controller Visualizer</h1>
            <div id="controllers" class="controller-container"></div>
            
            <script>
                const socket = io();
                
                socket.on('controller_added', function(data) {
                    addController(data.controller);
                });
                
                socket.on('controller_removed', function(data) {
                    removeController(data.controller_id);
                });
                
                socket.on('button_pressed', function(data) {
                    highlightButton(data.controller_id, data.button, true);
                });
                
                socket.on('button_released', function(data) {
                    highlightButton(data.controller_id, data.button, false);
                });
                
                socket.on('controller_flash', function(data) {
                    flashController(data.controller_id, data.duration);
                });
                
                function addController(controller) {
                    // Implementation to add controller to DOM
                }
                
                function removeController(controllerId) {
                    // Implementation to remove controller from DOM
                }
                
                function highlightButton(controllerId, button, pressed) {
                    // Implementation to highlight button
                }
                
                function flashController(controllerId, duration) {
                    // Implementation to flash controller
                }
            </script>
        </body>
        </html>
        '''
    
    def run(self, host: str = '0.0.0.0', port: int = 5003, debug: bool = False):
        """Run the visualizer in standalone mode."""
        if not self.standalone_mode or not self.socketio:
            raise RuntimeError("Cannot run in standalone mode when integrated")
        
        print(f"Controller Visualizer running at http://{host}:{port}/")
        self.socketio.run(self.app, host=host, port=port, debug=debug)
