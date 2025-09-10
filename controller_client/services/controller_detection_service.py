"""
Controller Detection Service

Handles detection and management of connected game controllers.
"""

import pygame
import time
import threading
from typing import Dict

from controller_client.models.client_state import ClientState
from controller_client.services.network_service import NetworkService


class ControllerDetectionService:
    """Manages detection and tracking of connected controllers."""
    
    def __init__(self, client_state: ClientState, 
                 network_service: NetworkService):
        """Initialize with client state and network service."""
        self.client_state = client_state
        self.network_service = network_service
        self._running = False
        self._detection_thread = None
    
    def detect_controllers(self) -> Dict[int, pygame.joystick.Joystick]:
        """Detect currently connected controllers."""
        pygame.joystick.quit()
        pygame.joystick.init()
        
        current_controllers = {}
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            current_controllers[i] = joystick
        
        return current_controllers
    
    def start_detection_loop(self):
        """Start the controller detection loop in a separate thread."""
        if self._running:
            return
        
        self._running = True
        self._detection_thread = threading.Thread(
            target=self._detection_loop,
            daemon=True
        )
        self._detection_thread.start()
    
    def stop_detection_loop(self):
        """Stop the controller detection loop."""
        self._running = False
        if self._detection_thread:
            self._detection_thread.join(timeout=1.0)
    
    def _detection_loop(self):
        """Main controller detection loop."""
        while self._running:
            try:
                current_controllers = self.detect_controllers()
                
                # Check for newly connected controllers
                for joystick_id, joystick in current_controllers.items():
                    if joystick_id not in self.client_state.controllers:
                        print(f"New controller detected {joystick_id}: "
                              f"{joystick.get_name()}")
                        
                        # Add to client state
                        self.client_state.add_controller(joystick_id, joystick)
                        
                        # Register with server
                        self.network_service.register_controller(
                            joystick_id, joystick.get_name()
                        )
                        
                        # Send active status
                        controller_id = self.client_state.get_controller_id(
                            joystick_id
                        )
                        self.network_service.send_controller_active(controller_id)
                
                # Check for disconnected controllers
                disconnected = []
                for joystick_id in self.client_state.controllers:
                    if joystick_id not in current_controllers:
                        disconnected.append(joystick_id)
                
                for joystick_id in disconnected:
                    print(f"Controller {joystick_id} disconnected")
                    
                    controller_id = self.client_state.get_controller_id(
                        joystick_id
                    )
                    self.network_service.send_controller_inactive(controller_id)
                    self.client_state.remove_controller(joystick_id)
                
                # Re-register all active controllers periodically
                if self.client_state.controllers:
                    self.network_service.register_controllers_batch(
                        self.client_state.controllers
                    )
                    
                    for joystick_id in self.client_state.controllers:
                        controller_id = self.client_state.get_controller_id(
                            joystick_id
                        )
                        self.network_service.send_controller_active(controller_id)
                
            except Exception as e:
                print(f"Error in controller detection: {e}")
            
            time.sleep(2)  # Check every 2 seconds
