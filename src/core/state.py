"""Shared state management for the swarm."""
from typing import Dict, Any, List
from datetime import datetime

class SwarmState:
    """Manages shared state across agents."""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
    
    def update(self, key: str, value: Any):
        """Update state."""
        self.data[key] = value
        self.history.append({
            "timestamp": datetime.now(),
            "key": key,
            "action": "update"
        })
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        return self.data.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.data.copy()