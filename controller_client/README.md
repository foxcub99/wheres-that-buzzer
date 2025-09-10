# Refactored Controller Client

This directory contains the refactored, modularized version of the controller client following the same architectural patterns as the game server.

## Structure

```
controller_client/
├── __init__.py              # Package initialization
├── app.py                   # Main application orchestrator
├── models/
│   ├── __init__.py         # Models package
│   └── client_state.py     # Client state and configuration management
├── services/
│   ├── __init__.py         # Services package
│   ├── network_service.py  # Server communication
│   ├── controller_detection_service.py  # Controller detection and management
│   └── visualizer_service.py  # Integration with shared visualizer
├── handlers/
│   ├── __init__.py         # Handlers package
│   ├── keyboard_handler.py # Keyboard input processing
│   └── controller_handler.py  # Game controller input processing
└── utils/
    └── __init__.py         # Utils package (for future utilities)
```

## Key Improvements Over Original

### 1. **Modular Architecture**
- **Models**: Configuration and state management (`ClientState`, `ClientConfig`)
- **Services**: Business logic (network communication, controller detection, visualizer)
- **Handlers**: Input processing (keyboard and controller events)
- **Clear separation** between input handling, business logic, and network communication

### 2. **Better State Management**
- `ClientState` class replaces global variables
- Centralized configuration with `ClientConfig`
- Proper tracking of controller registration status

### 3. **Improved Error Handling**
- Graceful shutdown with signal handlers
- Better exception handling throughout
- Non-blocking network operations using threading

### 4. **Service Separation**
- **NetworkService**: All server communication in one place
- **ControllerDetectionService**: Dedicated controller discovery and management
- **VisualizerService**: Clean integration with shared visualizer component

### 5. **Thread Management**
- Proper thread lifecycle management
- Graceful shutdown of all threads
- Daemon threads for background operations

## Usage

### Running the Refactored Client

```bash
# Basic usage (keyboard only)
python controller_client_new.py

# With visualizer
python controller_client_new.py --visualizer

# Custom server URL
python controller_client_new.py --server-url http://192.168.1.100:5002

# Custom visualizer port
python controller_client_new.py --visualizer --visualizer-port 5004
```

### Key Features

1. **Automatic Controller Detection**: Detects controllers as they connect/disconnect
2. **Keyboard Support**: Full keyboard input support with proper key mapping
3. **Visualizer Integration**: Uses shared visualizer component for real-time display
4. **Robust Network Handling**: Non-blocking server communication
5. **Graceful Shutdown**: Proper cleanup on exit (Ctrl+C, signals)

## Architecture Benefits

### **Compared to Original controller_client.py:**

| Aspect | Original | Refactored |
|--------|----------|------------|
| **Structure** | Single 268-line file | Modular packages |
| **State** | Global variables | Centralized `ClientState` class |
| **Threading** | Functions inside main() | Proper service classes |
| **Error Handling** | Basic try/catch | Comprehensive error handling |
| **Testability** | Hard to test | Each component testable |
| **Maintainability** | Monolithic | Clear separation of concerns |
| **Extensibility** | Difficult to extend | Easy to add new features |

### **Shared Code Reuse**

The refactored client integrates cleanly with the shared visualizer:

```python
# In VisualizerService
from shared.visualizer.controller_visualizer import ControllerVisualizer
from shared.models.controller_info import ControllerInfo

# Can run standalone or integrate with game server
self.visualizer = ControllerVisualizer(standalone_mode=True)
```

## Migration Path

1. **Phase 1**: Keep using original `controller_client.py`
2. **Phase 2**: Test new version with `controller_client_new.py`  
3. **Phase 3**: Switch to refactored version when confident
4. **Phase 4**: Remove original file

Both versions maintain the same API compatibility with the game server.

## Future Enhancements

The modular structure makes it easy to add:

1. **Configuration Files**: Replace command-line args with config files
2. **Plugin System**: Hot-swappable input handlers
3. **Advanced Visualizer**: Enhanced controller visualization
4. **Input Recording**: Record and replay input sequences
5. **Multiple Server Support**: Connect to multiple game servers
6. **Input Filtering**: Advanced button mapping and macros

## Dependencies

- `pygame`: Controller input handling
- `pynput`: Keyboard input handling  
- `requests`: HTTP communication with server
- `shared.visualizer`: Shared visualizer component (if using --visualizer)

## Compatibility

- **Python 3.7+**
- **Same game server API** as original client
- **Cross-platform** (Windows, macOS, Linux)
- **Multiple controller types** (Xbox, PlayStation, Nintendo Switch, etc.)

The refactored version is a drop-in replacement that provides better organization, reliability, and extensibility while maintaining full backward compatibility.
