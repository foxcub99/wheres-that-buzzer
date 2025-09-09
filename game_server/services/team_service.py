"""
Team Service

Handles team management operations including scoring, colors, and matching.
"""

import random
from typing import Dict, Optional, List
from flask_socketio import SocketIO

from controllers import controller_mapping
from game_server.models.game_state import GameState
from game_server.utils.sound_player import SoundPlayer


class TeamService:
    """Service for managing team operations."""
    
    def __init__(self, game_state: GameState, socketio: SocketIO):
        """Initialize with game state and socketio instance."""
        self.game_state = game_state
        self.socketio = socketio
        self.sound_player = SoundPlayer()
    
    def add_team(self, team_name: str) -> Dict:
        """Add a new team."""
        if not team_name or not team_name.strip():
            return {"success": False, "error": "Team name cannot be empty"}
        
        team_name = team_name.strip()
        
        if not self.game_state.add_team(team_name):
            return {"success": False, "error": "Team name already exists"}
        
        # Emit updates
        self._emit_team_updates()
        
        return {"success": True}
    
    def update_team_name(self, old_name: str, new_name: str) -> Dict:
        """Update a team's name."""
        if not new_name or not new_name.strip():
            return {"success": False, "error": "Team name cannot be empty"}
        
        old_name = old_name.strip()
        new_name = new_name.strip()
        
        if old_name not in self.game_state.team_scores:
            return {"success": False, "error": "Original team not found"}
        
        if not self.game_state.update_team_name(old_name, new_name):
            return {"success": False, "error": "New team name already exists"}
        
        # Emit updates
        self._emit_team_updates()
        
        return {"success": True}
    
    def delete_team(self, team_name: str) -> Dict:
        """Delete a team."""
        if not team_name or not team_name.strip():
            return {"success": False, "error": "Team name cannot be empty"}
        
        team_name = team_name.strip()
        
        if not self.game_state.delete_team(team_name):
            if team_name not in self.game_state.team_scores:
                return {"success": False, "error": "Team not found"}
            else:
                return {"success": False, "error": "Cannot delete the last team"}
        
        # Emit updates
        self._emit_team_updates()
        
        return {"success": True}
    
    def update_team_color(self, team_name: str, team_color: str) -> Dict:
        """Update a team's color."""
        if not team_name or not team_name.strip():
            return {"success": False, "error": "Team name cannot be empty"}
        
        if not team_color or not team_color.strip():
            return {"success": False, "error": "Team color cannot be empty"}
        
        team_name = team_name.strip()
        team_color = team_color.strip()
        
        # Validate hex color format
        if not team_color.startswith("#") or len(team_color) != 7:
            return {"success": False, "error": "Invalid color format"}
        
        if not self.game_state.update_team_color(team_name, team_color):
            return {"success": False, "error": "Team not found"}
        
        # Emit update
        self.socketio.emit("team_color_updated", {
            "team_name": team_name,
            "team_color": team_color
        })
        
        return {"success": True}
    
    def update_team_score(self, team_name: str, delta: int) -> Dict:
        """Update a team's score."""
        if not self.game_state.update_team_score(team_name, delta):
            return {"success": False, "error": "Invalid team"}
        
        # Emit update
        self.socketio.emit("score_update", {
            "team_scores": self.game_state.team_scores
        })
        
        return {
            "success": True,
            "team_scores": self.game_state.team_scores
        }
    
    def get_team_button_name(self, team_key: str) -> str:
        """Get button name for a team's assigned number."""
        btn_num = self.game_state.team_numbers.get(team_key, 0)
        
        # Get controller type from selected controller
        controller_type = self._get_selected_controller_type()
        
        return controller_mapping.get_button_name(controller_type, btn_num)
    
    def check_team_match(self, answer, selected_controller: str) -> Optional[str]:
        """Check if answer matches any team number and return matched team."""
        if not answer:
            return None
        
        print("Current team numbers:", self.game_state.team_numbers)
        print("Raw answer value and type:", answer, type(answer))
        
        matched_team = None
        
        for team_key, team_num in self.game_state.team_numbers.items():
            try:
                if selected_controller == "keyboard":
                    # Handle keyboard controller
                    matched_team = self._check_keyboard_match(
                        answer, team_key, team_num
                    )
                    if matched_team:
                        break
                else:
                    # Handle game controller
                    matched_team = self._check_controller_match(
                        answer, team_key, team_num
                    )
                    if matched_team:
                        break
                        
            except Exception as e:
                print(f"Error matching answer: {e}")
                continue
        
        return matched_team
    
    def handle_team_match(self, matched_team: str):
        """Handle when a team successfully matches their button."""
        team_display_name = self.game_state.get_team_display_name(matched_team)
        
        if not team_display_name:
            return
        
        print(f"Team '{team_display_name}' (key: {matched_team}) has matched!")
        
        # Play team sound
        team_names = list(self.game_state.team_scores.keys())
        team_number = self.sound_player.get_team_number_from_key(
            matched_team, team_names
        )
        self.sound_player.play_team_sound(team_number)
        
        # Update game state
        self.game_state.last_team_pressed = matched_team
        
        # Regenerate all team numbers
        self._regenerate_all_team_numbers()
        
        # Emit events
        self.socketio.emit("team_pressed", {
            "team": matched_team,
            "team_display_name": team_display_name
        })
        self.socketio.emit("reload_post_buzz", {})
        self.socketio.emit("reload_team_pages", {})
    
    def select_controller_and_regenerate(self, controller_id: str):
        """Select controller and regenerate team numbers."""
        prev_controller = self.game_state.selected_controller
        
        if controller_id != prev_controller:
            # Get controller type
            controller_type = self._get_controller_type(controller_id)
            
            # Get available button IDs
            button_ids = self._get_available_button_ids(controller_type)
            
            # Regenerate team numbers
            self.game_state.regenerate_team_numbers(button_ids)
            
            # Update selected controller
            self.game_state.set_selected_controller(controller_id)
            
            # Emit updates
            self._emit_controller_selection_update(controller_id)
    
    def clear_controller_selection(self):
        """Clear controller selection."""
        self.game_state.clear_selected_controller()
        
        # Emit updates
        self.socketio.emit("reload_team_pages", {})
        self.socketio.emit('selected_controller', {'controller_id': None})
        self.socketio.emit("team_pressed", {"team": None})
        
        print("Controller selection cleared")
    
    def _check_keyboard_match(self, answer, team_key: str, team_num: int) -> Optional[str]:
        """Check if keyboard answer matches team number."""
        expected_key_name = controller_mapping.get_button_name("Keyboard", team_num)
        actual_key_name = controller_mapping.get_button_name("Keyboard", str(answer))
        
        if expected_key_name == actual_key_name and expected_key_name != "Not Mapped":
            return team_key
        
        return None
    
    def _check_controller_match(self, answer, team_key: str, team_num: int) -> Optional[str]:
        """Check if controller answer matches team number."""
        # Extract number from 'button_X' or use as int
        if isinstance(answer, str) and answer.startswith("button_"):
            btn_num = int(answer.split("_")[1])
        else:
            btn_num = int(answer)
        
        if btn_num == team_num:
            return team_key
        
        return None
    
    def _get_selected_controller_type(self) -> str:
        """Get the type of the currently selected controller."""
        selected = self.game_state.selected_controller
        return self._get_controller_type(selected)
    
    def _get_controller_type(self, controller_id: Optional[str]) -> str:
        """Get controller type from controller ID."""
        if not controller_id:
            return 'Xbox'  # fallback
        
        if controller_id == 'keyboard':
            return 'Keyboard'
        
        if controller_id in self.game_state.controller_infos:
            return self.game_state.controller_infos[controller_id]['extra'].get(
                'name', 'Xbox'
            )
        
        return 'Xbox'  # fallback
    
    def _get_available_button_ids(self, controller_type: str) -> List[int]:
        """Get available button IDs for controller type."""
        if hasattr(controller_mapping, 'get_all_button_ids'):
            button_ids = controller_mapping.get_all_button_ids(controller_type)
        else:
            # fallback: try 0-15
            button_ids = list(range(0, 15))
        
        # Remove unmapped buttons
        return [
            bid for bid in button_ids 
            if controller_mapping.get_button_name(controller_type, bid) != 'Not Mapped'
        ]
    
    def _regenerate_all_team_numbers(self):
        """Regenerate random numbers for all teams."""
        for team_key in self.game_state.team_numbers:
            self.game_state.team_numbers[team_key] = random.randint(0, 3)
    
    def _emit_team_updates(self):
        """Emit team-related updates to all clients."""
        self.socketio.emit("team_list_updated", {
            "team_scores": self.game_state.team_scores
        })
        self.socketio.emit("reload_home_page", {})
    
    def _emit_controller_selection_update(self, controller_id: str):
        """Emit controller selection updates."""
        self.socketio.emit("controllers_update", {
            "controllers": list(self.game_state.controllers),
            "controller_infos": self.game_state.controller_infos
        })
        self.socketio.emit('reload_team_pages')
        self.socketio.emit('selected_controller', {'controller_id': controller_id})
        print(f"Selected controller set to: {controller_id}")
