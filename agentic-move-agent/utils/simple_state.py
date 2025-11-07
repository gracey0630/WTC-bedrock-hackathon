"""Simple in-memory state management with proper serialization"""
import json
from datetime import datetime

class SimpleStateManager:
    def __init__(self):
        self._states = {}
    
    def save_state(self, session_id, state_data):
        """Save state to memory (excluding non-serializable objects)"""
        # Create a copy without PIL images
        serializable_state = {}
        for key, value in state_data.items():
            # Skip PIL images and other non-serializable objects
            if key == "uploaded_photos":
                serializable_state[key] = f"[{len(value)} images]"
            else:
                try:
                    # Test if serializable
                    json.dumps(value)
                    serializable_state[key] = value
                except (TypeError, ValueError):
                    serializable_state[key] = str(value)
        
        self._states[session_id] = serializable_state
        print(f"💾 State saved for session: {session_id}")
    
    def load_state(self, session_id):
        """Load state from memory"""
        return self._states.get(session_id, {})
    
    def update_state(self, session_id, updates):
        """Update state"""
        current_state = self.load_state(session_id)
        current_state.update(updates)
        self.save_state(session_id, current_state)

# Global singleton
state_manager = SimpleStateManager()
