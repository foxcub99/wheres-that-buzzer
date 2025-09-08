#!/usr/bin/env python3
"""
Test script for the controller visualizer
"""

import time
import threading
from controller_visualizer import ControllerVisualizer

def test_controller_visualizer():
    """Test the controller visualizer with fake data"""
    visualizer = ControllerVisualizer()
    
    # Start visualizer in a thread
    visualizer_thread = threading.Thread(
        target=visualizer.run,
        kwargs={'port': 5003, 'debug': False},
        daemon=True
    )
    visualizer_thread.start()
    
    print("Controller Visualizer started at http://localhost:5003/")
    print("Adding test controllers...")
    
    # Add test controllers
    time.sleep(1)
    
    # Add Xbox controller
    xbox_info = {
        "id": "test_xbox_0",
        "ip": "192.168.1.100",
        "extra": {"name": "Xbox Wireless Controller", "joystick_id": 0}
    }
    visualizer.update_controller("test_xbox_0", xbox_info)
    
    # Add PS controller
    ps_info = {
        "id": "test_ps_1", 
        "ip": "192.168.1.100",
        "extra": {"name": "DualSense Wireless Controller", "joystick_id": 1}
    }
    visualizer.update_controller("test_ps_1", ps_info)
    
    # Add keyboard
    keyboard_info = {
        "id": "keyboard",
        "ip": "192.168.1.100", 
        "extra": {"name": "Keyboard"}
    }
    visualizer.update_controller("keyboard", keyboard_info)
    
    print("Test controllers added. Simulating button presses...")
    
    # Simulate button presses
    time.sleep(2)
    
    # Xbox A button
    visualizer.button_pressed("test_xbox_0", 0, "A")
    time.sleep(0.5)
    visualizer.button_released("test_xbox_0", 0, "A")
    
    # PS X button  
    time.sleep(1)
    visualizer.button_pressed("test_ps_1", 0, "X")
    time.sleep(0.5)
    visualizer.button_released("test_ps_1", 0, "X")
    
    # Keyboard key
    time.sleep(1)
    visualizer.button_pressed("keyboard", "a", "A")
    time.sleep(0.5)
    visualizer.button_released("keyboard", "a", "A")
    
    print("Test complete. Open http://localhost:5003/ to see the visualizer.")
    print("Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping test...")

if __name__ == "__main__":
    test_controller_visualizer()
