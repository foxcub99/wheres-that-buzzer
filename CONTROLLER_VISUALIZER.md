# Controller Visualizer

The controller visualizer provides a real-time visual interface showing connected controllers and their button presses, similar to gamepadviewer.com.

## Features

- **Real-time Visualization**: See all connected controllers (Xbox, PlayStation, Keyboard)
- **Button Press Animation**: Buttons light up when pressed with smooth animations
- **Multiple Controller Support**: Display multiple controllers simultaneously
- **Web-based Interface**: Accessible via any web browser
- **SVG Graphics**: Scalable vector graphics for crisp controller images

## Usage

### Starting the Controller Client with Visualizer

Run the controller client with the visualizer flag:

```bash
python controller_client.py --visualizer
```

This will:
1. Start the normal controller client (connects to game server)
2. Launch the visual interface at `http://[your-ip]:5003/`
3. Show real-time controller connections and button presses

### Accessing the Visualizer

Once started, open your web browser to:
- `http://localhost:5003/` (if running locally)
- `http://[your-ip]:5003/` (to access from other devices on your network)

## Files

### Core Components
- `controller_visualizer.py` - Flask server for visual interface
- `templates/controller_visualizer.html` - Web interface with real-time updates
- `images/` - SVG controller graphics

### Controller SVG Files
- `images/xbox_controller.svg` - Xbox controller layout
- `images/ps_controller.svg` - PlayStation controller layout  
- `images/keyboard.svg` - Keyboard layout

### Test Script
- `test_visualizer.py` - Test the visualizer with simulated controllers

## How It Works

1. **Integration**: The visualizer integrates with `controller_client.py`
2. **WebSocket Communication**: Uses Flask-SocketIO for real-time updates
3. **SVG Manipulation**: Dynamically highlights pressed buttons in SVG graphics
4. **Multi-Controller**: Tracks multiple controllers with unique IDs

## Customization

### Adding New Controller Types

1. Create an SVG file in `images/` folder
2. Add button mapping in `templates/controller_visualizer.html`
3. Update `getControllerType()` function to detect your controller

### Button Mappings

Button mappings are defined in the HTML template:

```javascript
const buttonMappings = {
    xbox: {
        0: 'button_A',
        1: 'button_B', 
        2: 'button_X',
        3: 'button_Y',
        // ... more buttons
    },
    // ... other controller types
};
```

## Technical Details

- **Flask + SocketIO**: Real-time web server
- **SVG Animation**: CSS transforms and filters for button press effects
- **Responsive Design**: Works on desktop and mobile browsers
- **Cross-Platform**: Compatible with Windows, macOS, and Linux
