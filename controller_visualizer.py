from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os
from utils import get_host_ip


class ControllerVisualizer:
    def __init__(self, controller_client_instance=None):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.controller_client = controller_client_instance
        self.connected_controllers = {}
        self.button_states = {}  # {controller_id: {button_id: is_pressed}}
        
        self.setup_routes()
        self.setup_socketio_events()
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('controller_visualizer.html')
        
        @self.app.route('/api/controllers')
        def get_controllers():
            return jsonify({
                'controllers': self.connected_controllers,
                'button_states': self.button_states
            })
        
        @self.app.route('/static/images/<path:filename>')
        def serve_images(filename):
            images_dir = os.path.join(os.path.dirname(__file__), 'images')
            return send_from_directory(images_dir, filename)
    
    def setup_socketio_events(self):
        @self.socketio.on('connect')
        def handle_connect():
            print('Client connected to visualizer')
            # Send current state to new client
            emit('controllers_update', {
                'controllers': self.connected_controllers,
                'button_states': self.button_states
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print('Client disconnected from visualizer')
    
    def update_controller(self, controller_id, controller_info):
        """Update controller information"""
        self.connected_controllers[controller_id] = controller_info
        if controller_id not in self.button_states:
            self.button_states[controller_id] = {}
        
        self.socketio.emit('controller_connected', {
            'controller_id': controller_id,
            'controller_info': controller_info
        })
    
    def remove_controller(self, controller_id):
        """Remove controller"""
        if controller_id in self.connected_controllers:
            del self.connected_controllers[controller_id]
        if controller_id in self.button_states:
            del self.button_states[controller_id]
        
        self.socketio.emit('controller_disconnected', {
            'controller_id': controller_id
        })
    
    def button_pressed(self, controller_id, button_id, button_name=None):
        """Handle button press"""
        if controller_id not in self.button_states:
            self.button_states[controller_id] = {}
        
        self.button_states[controller_id][button_id] = True
        
        self.socketio.emit('button_press', {
            'controller_id': controller_id,
            'button_id': button_id,
            'button_name': button_name,
            'pressed': True
        })
    
    def button_released(self, controller_id, button_id, button_name=None):
        """Handle button release"""
        if controller_id not in self.button_states:
            self.button_states[controller_id] = {}
        
        self.button_states[controller_id][button_id] = False
        
        self.socketio.emit('button_press', {
            'controller_id': controller_id,
            'button_id': button_id,
            'button_name': button_name,
            'pressed': False
        })
    
    def run(self, host='0.0.0.0', port=5003, debug=False):
        """Start the visualizer server"""
        host_ip = get_host_ip()
        print(f"Controller Visualizer running at http://{host_ip}:{port}/")
        self.socketio.run(self.app, host=host, port=port, debug=debug)


# Global visualizer instance
visualizer = None


def start_visualizer_server():
    """Start the visualizer server in a separate thread"""
    visualizer_instance = ControllerVisualizer()
    visualizer_instance.run(port=5003, debug=False)


def get_visualizer():
    """Get the global visualizer instance"""
    return visualizer
