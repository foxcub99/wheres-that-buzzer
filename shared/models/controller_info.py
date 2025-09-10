"""
Controller Information Models

Shared data models for representing controller information.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any
from enum import Enum


class ControllerType(Enum):
    """Enumeration of supported controller types."""
    XBOX = "Xbox"
    PLAYSTATION = "PlayStation" 
    NINTENDO_SWITCH = "Switch"
    KEYBOARD = "Keyboard"
    JOY_CON_L = "Joy-Con (L)"
    JOY_CON_R = "Joy-Con (R)"
    UNKNOWN = "Unknown"


@dataclass
class ControllerInfo:
    """Information about a connected controller."""
    id: str
    name: str
    controller_type: ControllerType
    ip_address: Optional[str] = None
    joystick_id: Optional[int] = None
    uuid: Optional[str] = None
    status: str = "active"
    extra: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize extra dict if None."""
        if self.extra is None:
            self.extra = {}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ControllerInfo':
        """Create ControllerInfo from dictionary data."""
        controller_type = ControllerType.UNKNOWN
        
        # Try to determine controller type from name
        name = data.get('extra', {}).get('name', '').lower()
        if 'xbox' in name:
            controller_type = ControllerType.XBOX
        elif 'playstation' in name or 'ps' in name:
            controller_type = ControllerType.PLAYSTATION
        elif 'switch' in name or 'nintendo' in name:
            controller_type = ControllerType.NINTENDO_SWITCH
        elif 'keyboard' in name or data.get('id') == 'keyboard':
            controller_type = ControllerType.KEYBOARD
        elif 'joy-con' in name:
            if 'left' in name or '(l)' in name:
                controller_type = ControllerType.JOY_CON_L
            else:
                controller_type = ControllerType.JOY_CON_R
        
        return cls(
            id=data.get('id', ''),
            name=data.get('extra', {}).get('name', 'Unknown Controller'),
            controller_type=controller_type,
            ip_address=data.get('ip'),
            joystick_id=data.get('extra', {}).get('joystick_id'),
            uuid=data.get('extra', {}).get('uuid'),
            status=data.get('status', 'active'),
            extra=data.get('extra', {})
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            'id': self.id,
            'ip': self.ip_address,
            'status': self.status,
            'extra': {
                'name': self.name,
                'joystick_id': self.joystick_id,
                'uuid': self.uuid,
                **self.extra
            }
        }
