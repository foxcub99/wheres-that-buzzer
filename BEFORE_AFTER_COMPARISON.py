"""
Before vs After Comparison

This file shows a side-by-side comparison of the key improvements made
during the refactoring process.
"""

# ===============================================
# BEFORE: Functions inside main() - BAD PRACTICE
# ===============================================

def main():
    # 100+ lines of code here...
    
    def send_keyboard_event(device_id, answer):  # ❌ Function inside function
        def send():
            # Network request logic
            pass
        threading.Thread(target=send, daemon=True).start()
    
    def on_press(key):  # ❌ Function inside function
        # Keyboard handling logic
        pass
    
    def dynamic_controller_manager():  # ❌ Function inside function
        # Controller management logic
        pass
    
    # More nested functions...
    # Main game loop mixed with everything else...

# ===============================================
# AFTER: Proper class-based structure - GOOD PRACTICE
# ===============================================

class ControllerService:  # ✅ Proper class organization
    def __init__(self, game_state, socketio):
        self.game_state = game_state
        self.socketio = socketio
    
    def send_keyboard_event(self, device_id, answer):  # ✅ Class method
        # Clean, testable method
        pass
    
    def handle_key_press(self, key):  # ✅ Class method
        # Clean, testable method
        pass
    
    def manage_controllers(self):  # ✅ Class method
        # Clean, testable method
        pass

# ===============================================
# BEFORE: Global state dictionary - BAD PRACTICE
# ===============================================

state = {  # ❌ Global mutable state
    "current_question": 0,
    "answers": {},
    "controllers": set(),
    "team_scores": {"Team 1": 0, "Team 2": 0, "Team 3": 0},
    # ... dozens more fields
}

def some_function():
    global state  # ❌ Using global keyword
    state["current_question"] += 1

# ===============================================
# AFTER: Class-based state management - GOOD PRACTICE
# ===============================================

class GameState:  # ✅ Encapsulated state
    def __init__(self):
        self.current_question = 0
        self.answers = {}
        self.controllers = set()
        self.team_scores = {"Team 1": 0, "Team 2": 0, "Team 3": 0}
    
    def next_question(self):  # ✅ Method to modify state
        if self.current_question < len(self.questions) - 1:
            self.current_question += 1
            return True
        return False

# ===============================================
# BEFORE: 100+ line function - BAD PRACTICE
# ===============================================

@app.route("/api/answer", methods=["POST"])
def submit_answer():  # ❌ 100+ lines doing everything
    data = request.json
    controller_id = data.get("controller_id")
    answer = data.get("answer")
    
    # Controller registration logic (20 lines)
    # Answer processing logic (30 lines)
    # Team matching logic (40 lines)
    # Sound playing logic (10 lines)
    # Socket event emission (10 lines)
    # Error handling mixed throughout
    
    return jsonify(success=True)

# ===============================================
# AFTER: Clean, focused functions - GOOD PRACTICE
# ===============================================

@api_bp.route("/api/answer", methods=["POST"])
def submit_answer():  # ✅ Clean, focused function
    data = request.json
    controller_id = data.get("controller_id")
    answer = data.get("answer")
    
    # Delegate to services
    controller_service.handle_new_controller_in_answer(controller_id)
    game_state.answers[controller_id] = answer
    
    if answer and controller_id == game_state.selected_controller:
        matched_team = team_service.check_team_match(answer, controller_id)
        if matched_team:
            team_service.handle_team_match(matched_team)
    
    return jsonify(success=True)

# ===============================================
# MEASURABLE IMPROVEMENTS
# ===============================================

"""
BEFORE:
- 1 file: 711 lines
- Longest function: ~100 lines
- Global state: 1 large dictionary
- Testability: Very difficult
- Maintainability: Poor

AFTER:
- 12 files: Average ~50 lines each
- Longest function: ~30 lines
- State management: Proper class with methods
- Testability: Each service can be unit tested
- Maintainability: Excellent

BENEFITS:
✅ Easier to find bugs
✅ Easier to add features
✅ Easier to write tests
✅ Easier for other developers to understand
✅ Follows Python best practices
✅ Scalable architecture
"""
