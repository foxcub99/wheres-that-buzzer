"""
Controller Client Application

Main application orchestrating all controller client components.
"""

import argparse
import pygame
import signal
import sys
from typing import Optional

from utils import get_host_ip
from controller_client.models.client_state import ClientState, ClientConfig
from controller_client.services.network_service import NetworkService
from controller_client.services.controller_detection_service import (
    ControllerDetectionService
)
from controller_client.services.visualizer_service import VisualizerService
from controller_client.handlers.keyboard_handler import KeyboardHandler
from controller_client.handlers.controller_handler import ControllerHandler


class ControllerClientApp:
    """Main controller client application."""
    
    def __init__(self, config: ClientConfig):
        """Initialize the controller client application."""
        self.config = config
        self.client_state = ClientState(config)
        
        # Services
        self.network_service = NetworkService(self.client_state)
        self.controller_detection_service = ControllerDetectionService(
            self.client_state, self.network_service
        )
        self.visualizer_service: Optional[VisualizerService] = None
        
        # Handlers
        self.keyboard_handler: Optional[KeyboardHandler] = None
        self.controller_handler: Optional[ControllerHandler] = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self):
        """Initialize all components."""
        # Initialize pygame
        pygame.init()
        pygame.joystick.init()
        
        # Initialize visualizer if requested
        if self.config.enable_visualizer:
            self.visualizer_service = VisualizerService(self.client_state)
            self.visualizer_service.start_visualizer()
        
        # Initialize handlers
        self.keyboard_handler = KeyboardHandler(
            self.client_state,
            self.network_service,
            self.visualizer_service
        )
        
        self.controller_handler = ControllerHandler(
            self.client_state,
            self.network_service,
            self.visualizer_service
        )
        
        # Start keyboard listener
        self.keyboard_handler.start_listening()
        
        # Start controller detection
        self.controller_detection_service.start_detection_loop()
        
        # Detect initial controllers
        initial_controllers = self.controller_detection_service.detect_controllers()
        for joystick_id, joystick in initial_controllers.items():
            print(f"Detected controller {joystick_id}: {joystick.get_name()}")
            self.client_state.add_controller(joystick_id, joystick)
            
            # Add to visualizer
            if self.visualizer_service:
                self.visualizer_service.add_controller(
                    joystick_id, joystick.get_name()
                )
        
        if not initial_controllers:
            print("No controllers detected. Keyboard input will still work.")
        
        print("Controller client initialized successfully")
    
    def run(self):
        """Run the main application loop."""
        try:
            print("Starting controller client...")
            self.initialize()
            
            # Run the controller event loop (this blocks)
            self.controller_handler.start_event_loop()
            
        except KeyboardInterrupt:
            print("\nShutdown requested by user")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the application."""
        print("Shutting down controller client...")
        
        # Stop handlers
        if self.keyboard_handler:
            self.keyboard_handler.stop_listening()
        
        if self.controller_handler:
            self.controller_handler.stop_event_loop()
        
        # Stop services
        self.controller_detection_service.stop_detection_loop()
        
        # Send inactive status for all controllers
        for joystick_id in list(self.client_state.controllers.keys()):
            controller_id = self.client_state.get_controller_id(joystick_id)
            self.network_service.send_controller_inactive(controller_id)
        
        # Clean up pygame
        pygame.quit()
        
        print("Controller client shut down successfully")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        print(f"\nReceived signal {signum}")
        self.shutdown()
        sys.exit(0)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Controller Client for Buzzer Game'
    )
    parser.add_argument(
        '--visualizer',
        action='store_true',
        help='Start visual controller interface'
    )
    parser.add_argument(
        '--server-url',
        default="http://localhost:5002",
        help='Game server URL (default: http://localhost:5002)'
    )
    parser.add_argument(
        '--visualizer-port',
        type=int,
        default=5003,
        help='Port for visualizer web interface (default: 5003)'
    )
    
    return parser.parse_args()


def create_config_from_args(args: argparse.Namespace) -> ClientConfig:
    """Create client configuration from command line arguments."""
    return ClientConfig(
        game_server_url=args.server_url,
        controller_id=get_host_ip(),
        enable_visualizer=args.visualizer,
        visualizer_port=args.visualizer_port
    )


def main():
    """Main entry point."""
    args = parse_arguments()
    config = create_config_from_args(args)
    
    app = ControllerClientApp(config)
    app.run()


if __name__ == "__main__":
    main()
