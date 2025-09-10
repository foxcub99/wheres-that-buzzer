"""
Network Service

Handles communication with the game server including controller registration
and input forwarding.
"""

import requests
import threading
from typing import Dict, Any

from controller_client.models.client_state import ClientState


class NetworkService:
    """Handles network communication with the game server."""
    
    def __init__(self, client_state: ClientState):
        """Initialize with client state."""
        self.client_state = client_state
    
    def register_controller(self, joystick_id: int, 
                           joystick_name: str) -> bool:
        """Register a controller with the game server."""
        try:
            controller_id = self.client_state.get_controller_id(joystick_id)
            unique_id = f"{self.client_state.uuid}_{joystick_id}"
            
            extra_data = {
                "name": joystick_name,
                "joystick_id": joystick_id,
                "uuid": unique_id
            }
            
            response = requests.post(
                f"{self.client_state.config.game_server_url}/api/register_controller",
                json={
                    "controller_id": controller_id,
                    "extra": extra_data
                },
                timeout=1
            )
            
            if response.ok:
                print(f"Controller {joystick_id} registered with server.")
                self.client_state.mark_controller_registered(controller_id)
                return True
            else:
                print(f"Failed to register controller {joystick_id}: {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"Network error during controller registration: {e}")
            return False
    
    def register_controllers_batch(self, controllers: Dict[int, Any]) -> None:
        """Register multiple controllers with the game server."""
        for joystick_id, joystick in controllers.items():
            self.register_controller(joystick_id, joystick.get_name())
    
    def send_controller_status(self, controller_id: str, status: str) -> None:
        """Send controller status update to game server."""
        def send_async():
            try:
                requests.post(
                    f"{self.client_state.config.game_server_url}/api/controller_status",
                    json={
                        "controller_id": controller_id,
                        "status": status
                    },
                    timeout=0.5
                )
            except requests.RequestException as e:
                print(f"Failed to send controller status: {e}")
        
        # Send asynchronously to avoid blocking
        threading.Thread(target=send_async, daemon=True).start()
    
    def send_input_event(self, controller_id: str, answer: Any) -> None:
        """Send input event to game server."""
        def send_async():
            try:
                requests.post(
                    f"{self.client_state.config.game_server_url}/api/answer",
                    json={
                        "controller_id": controller_id,
                        "answer": answer
                    },
                    timeout=0.5
                )
            except requests.RequestException as e:
                print(f"Failed to send input event: {e}")
        
        # Send asynchronously to avoid blocking
        threading.Thread(target=send_async, daemon=True).start()
    
    def send_controller_active(self, controller_id: str) -> None:
        """Mark controller as active."""
        self.send_controller_status(controller_id, "active")
    
    def send_controller_inactive(self, controller_id: str) -> None:
        """Mark controller as inactive."""
        self.send_controller_status(controller_id, "inactive")
