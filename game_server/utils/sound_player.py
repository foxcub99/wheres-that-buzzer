"""
Sound Player Utility

Handles playing sound files for team buzzer events.
"""

import os
from typing import Optional


class SoundPlayer:
    """Handles sound playback for team events."""
    
    def __init__(self, sounds_dir: str = "sounds"):
        """Initialize with sounds directory path."""
        self.sounds_dir = sounds_dir
    
    def play_team_sound(self, team_number: Optional[str]):
        """Play sound for a specific team number."""
        if not team_number:
            return
        
        try:
            if team_number in ["1", "2", "3"]:
                # Play built-in sound for team 1, 2, or 3
                sound_path = f"{self.sounds_dir}/team_{team_number}.mp3"
                os.system(f'afplay "{sound_path}"')
            else:
                # Fallback to team 1 sound for other teams
                sound_path = f"{self.sounds_dir}/team_1.mp3"
                os.system(f'afplay "{sound_path}"')
        except Exception as e:
            print(f"Could not play sound for team {team_number}: {e}")
    
    def get_team_number_from_key(self, team_key: str, team_names: list) -> Optional[str]:
        """Extract team number from team key for sound playing."""
        # Check if it's a numbered team like "team1", "team2", etc.
        if team_key.startswith("team") and team_key[4:].isdigit():
            return team_key[4:]
        
        # For custom teams, try to find their index in the team list
        for i, team_name in enumerate(team_names):
            team_name_key = team_name.lower().replace(" ", "").replace("_", "")
            if team_name_key == team_key:
                return str(i + 1)
        
        return None
