"""
Controller Input Handler

Handles game controller input events using pygame.
"""

import pygame
import time
from typing import Optional

from controllers import controller_mapping
from controller_client.models.client_state import ClientState
from controller_client.services.network_service import NetworkService
from controller_client.services.visualizer_service import VisualizerService


class ControllerHandler:
    """Handles game controller input events."""
    
    def __init__(self, client_state: ClientState,
                 network_service: NetworkService,
                 visualizer_service: Optional[VisualizerService] = None):
        """Initialize controller handler."""
        self.client_state = client_state
        self.network_service = network_service
        self.visualizer_service = visualizer_service
        self._running = False
    
    def start_event_loop(self):
        """Start the controller event processing loop."""
        self._running = True
        print("Controller event loop started")
        
        while self._running:
            try:
                self._process_events()
                time.sleep(0.01)  # Small delay to prevent excessive CPU usage
            except Exception as e:
                print(f"Error in controller event loop: {e}")
                time.sleep(0.1)  # Longer delay on error
    
    def stop_event_loop(self):
        """Stop the controller event processing loop."""
        self._running = False
        print("Controller event loop stopped")
    
    def _process_events(self):
        """Process pygame events for controller input."""
        for event in pygame.event.get():
            if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
                self._handle_button_event(event)
    
    def _handle_button_event(self, event):
        """Handle controller button press/release events."""
        joystick_id = event.joy
        button = event.button
        pressed = event.type == pygame.JOYBUTTONDOWN
        
        # Check if controller is still connected
        if joystick_id not in self.client_state.controllers:
            return
        
        joystick = self.client_state.controllers[joystick_id]
        controller_id = self.client_state.get_controller_id(joystick_id)
        
        # Get button name for display
        button_name = controller_mapping.get_button_name(
            joystick.get_name(), button
        )
        
        status = 'pressed' if pressed else 'released'
        print(f"Controller {joystick_id} Button {button_name} {status}")
        
        # Send to server
        answer = f"button_{button}" if pressed else None
        self.network_service.send_input_event(controller_id, answer)
        
        # Update visualizer
        if self.visualizer_service:
            if pressed:
                self.visualizer_service.button_pressed(
                    controller_id, str(button), button_name
                )
            else:
                self.visualizer_service.button_released(
                    controller_id, str(button), button_name
                )
