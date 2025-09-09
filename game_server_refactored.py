#!/usr/bin/env python3
"""
Refactored Game Server Entry Point

This is the new entry point for the refactored game server.
Run this instead of the old game_server.py file.
"""

if __name__ == "__main__":
    from game_server.app import run_server
    run_server()
