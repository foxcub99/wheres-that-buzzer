"""
Game State Management

This module contains the GameState class that manages all game state
in a centralized, organized way.
"""

import json
import random
from typing import Dict, Set, Optional, Any


class GameState:
    """Centralized game state management."""
    
    def __init__(self):
        """Initialize game state with default values."""
        # Load questions from file
        with open("questions.json", "r", encoding="utf-8") as f:
            self.questions = json.load(f)["questions"]
        
        # Core game state
        self.current_question = 0
        self.answers: Dict[str, Any] = {}
        self.controllers: Set[str] = set()
        self.controller_infos: Dict[str, Dict] = {}
        self.game_started = False
        self.show_ip = False
        self.selected_controller: Optional[str] = None
        self.last_team_pressed: Optional[str] = None
        
        # Team management
        self.team_scores = {
            "Team 1": 0,
            "Team 2": 0,
            "Team 3": 0
        }
        
        self.team_colors = {
            "Team 1": "#2a7ae2",
            "Team 2": "#e74c3c",
            "Team 3": "#27ae60"
        }
        
        self.team_numbers: Dict[str, int] = {}
        self._initialize_team_numbers()
    
    def _initialize_team_numbers(self):
        """Initialize team numbers based on current teams."""
        for team_name in self.team_scores:
            team_key = team_name.lower().replace(" ", "").replace("_", "")
            if team_key not in self.team_numbers:
                self.team_numbers[team_key] = 0
    
    # Question management
    def next_question(self) -> bool:
        """Move to the next question. Returns True if successful."""
        if self.current_question < len(self.questions) - 1:
            self.current_question += 1
            self.answers = {}
            self.last_team_pressed = None
            return True
        return False
    
    def prev_question(self) -> bool:
        """Move to the previous question. Returns True if successful."""
        if self.current_question > 0:
            self.current_question -= 1
            self.answers = {}
            self.last_team_pressed = None
            return True
        return False
    
    def get_current_question(self) -> Dict:
        """Get the current question data."""
        return self.questions[self.current_question]
    
    def get_prev_question(self) -> Optional[Dict]:
        """Get the previous question if it exists."""
        if self.current_question > 0:
            return self.questions[self.current_question - 1]
        return None
    
    def get_next_question(self) -> Optional[Dict]:
        """Get the next question if it exists."""
        if self.current_question < len(self.questions) - 1:
            return self.questions[self.current_question + 1]
        return None
    
    # Controller management
    def register_controller(self, controller_id: str, controller_info: Dict):
        """Register a new controller."""
        self.controllers.add(controller_id)
        self.controller_infos[controller_id] = controller_info
    
    def update_controller_status(self, controller_id: str, status: str):
        """Update controller status (active/inactive)."""
        if controller_id in self.controller_infos:
            self.controller_infos[controller_id]["status"] = status
        
        if status == "inactive":
            self.controllers.discard(controller_id)
        else:
            self.controllers.add(controller_id)
    
    def set_selected_controller(self, controller_id: Optional[str]):
        """Set the selected controller for team actions."""
        self.selected_controller = controller_id
    
    def clear_selected_controller(self):
        """Clear controller selection and reset team numbers."""
        self.selected_controller = None
        for team_key in self.team_numbers:
            self.team_numbers[team_key] = 0
        self.last_team_pressed = None
    
    # Team management
    def add_team(self, team_name: str) -> bool:
        """Add a new team. Returns True if successful."""
        if team_name in self.team_scores:
            return False
        
        self.team_scores[team_name] = 0
        
        # Assign default color
        default_colors = [
            "#2a7ae2", "#e74c3c", "#27ae60", "#f39c12",
            "#9b59b6", "#34495e", "#e67e22", "#1abc9c"
        ]
        team_index = len(self.team_colors)
        self.team_colors[team_name] = default_colors[team_index % len(default_colors)]
        
        # Generate team key
        team_key = team_name.lower().replace(" ", "").replace("_", "")
        if team_key not in self.team_numbers:
            self.team_numbers[team_key] = 0
        
        return True
    
    def update_team_name(self, old_name: str, new_name: str) -> bool:
        """Update a team's name. Returns True if successful."""
        if old_name not in self.team_scores or (
            new_name != old_name and new_name in self.team_scores
        ):
            return False
        
        # Update scores
        score = self.team_scores.pop(old_name)
        self.team_scores[new_name] = score
        
        # Update colors
        if old_name in self.team_colors:
            color = self.team_colors.pop(old_name)
            self.team_colors[new_name] = color
        
        # Update team numbers if key changed
        old_key = old_name.lower().replace(" ", "").replace("_", "")
        new_key = new_name.lower().replace(" ", "").replace("_", "")
        
        if old_key != new_key and old_key in self.team_numbers:
            self.team_numbers[new_key] = self.team_numbers.pop(old_key)
        
        return True
    
    def delete_team(self, team_name: str) -> bool:
        """Delete a team. Returns True if successful."""
        if team_name not in self.team_scores or len(self.team_scores) <= 1:
            return False
        
        # Remove from scores and colors
        self.team_scores.pop(team_name)
        self.team_colors.pop(team_name, None)
        
        # Remove from team numbers
        team_key = team_name.lower().replace(" ", "").replace("_", "")
        self.team_numbers.pop(team_key, None)
        
        return True
    
    def update_team_color(self, team_name: str, color: str) -> bool:
        """Update a team's color. Returns True if successful."""
        if team_name not in self.team_scores:
            return False
        
        self.team_colors[team_name] = color
        return True
    
    def update_team_score(self, team_name: str, delta: int) -> bool:
        """Update a team's score. Returns True if successful."""
        if team_name not in self.team_scores:
            return False
        
        self.team_scores[team_name] += delta
        if self.team_scores[team_name] < 0:
            self.team_scores[team_name] = 0
        
        return True
    
    def get_team_urls(self, host_ip: str) -> list:
        """Get list of team URLs for display."""
        team_urls = []
        for team_name in self.team_scores.keys():
            team_key = team_name.lower().replace(" ", "").replace("_", "")
            team_urls.append({
                "name": team_name,
                "url": f"{host_ip}:5002/{team_key}"
            })
        return team_urls
    
    def get_team_display_name(self, team_key: str) -> Optional[str]:
        """Get team display name from team key."""
        for display_name in self.team_scores.keys():
            display_key = display_name.lower().replace(" ", "").replace("_", "")
            if display_key == team_key:
                return display_name
        return None
    
    def find_team_by_key(self, team_key: str) -> Optional[str]:
        """Find team name that matches the given key."""
        # First try exact match with existing team names
        for name in self.team_scores.keys():
            if name.lower().replace(" ", "").replace("_", "") == team_key:
                return name
        
        # Check legacy team mappings
        team_mapping = {
            "team1": "Team 1",
            "team2": "Team 2", 
            "team3": "Team 3"
        }
        team_name = team_mapping.get(team_key)
        if team_name and team_name in self.team_scores:
            return team_name
        
        return None
    
    def regenerate_team_numbers(self, button_ids: list):
        """Regenerate team numbers from available button IDs."""
        team_keys = list(self.team_numbers.keys())
        chosen = random.sample(button_ids, min(len(team_keys), len(button_ids)))
        
        for i, team_key in enumerate(team_keys):
            self.team_numbers[team_key] = chosen[i] if i < len(chosen) else 0
    
    def get_state_dict(self) -> Dict:
        """Get current state as dictionary for API responses."""
        return {
            "current_question": self.current_question,
            "answers": self.answers,
            "controllers": list(self.controllers),
            "controller_infos": self.controller_infos,
            "game_started": self.game_started,
            "show_ip": self.show_ip,
            "selected_controller": self.selected_controller,
            "team_scores": self.team_scores,
            "team_colors": self.team_colors,
            "team_numbers": self.team_numbers,
            "last_team_pressed": self.last_team_pressed,
            "question": self.get_current_question()
        }
