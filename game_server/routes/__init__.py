"""
Routes package initialization.
"""

from .api import api_bp, init_api_routes
from .pages import pages_bp, init_page_routes
from .websocket import init_websocket_handlers, register_socketio_handlers

__all__ = [
    "api_bp", "init_api_routes",
    "pages_bp", "init_page_routes", 
    "init_websocket_handlers", "register_socketio_handlers"
]
