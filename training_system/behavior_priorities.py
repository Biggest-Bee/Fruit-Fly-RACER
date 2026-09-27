"""
Behavior Priorities
Implements priority-based decision making for survival behaviors
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add parent directory to path for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class BehaviorPriorities:
    """
    Manages behavior priorities and decision making for the fly
    """
    
    def __init__(self):
        """Initialize behavior priorities system"""
        # Behavior types and their base priorities
        self.behaviors = {
            "seek_food": {"base_priority": 0.8, "active": False},
            "explore": {"base_priority": 0.3, "active": False},
            "rest": {"base_priority": 0.1, "active": False},
            "flee": {"base_priority": 0.9, "active": False},
            "social": {"base_priority": 0.2, "active": False},
            "train": {"base_priority": 0.5, "active": False}
        }
        
        # Current priorities (can be modified by drives)
        self.current_priorities = self.behaviors.copy()
        
        # Decision context
        self.current_behavior = None
        self.behavior_history = []
        self.max_history = 10
        
        print("Behavior priorities system initialized")
    
    def update_priorities(self, drives: Dict[str, float], context: Dict = None):
        """
        Update behavior priorities based on drives and context
        
        Args:
            drives: Dictionary of drive levels (hunger, fear, etc.)
            context: Environmental context information
        """
        if context is None:
            context = {}
        
        # Get drive values with defaults
        hunger_drive = drives.get("hunger_drive", 0.0)
        survival_drive = drives.get("survival_drive", 0.0)
        fear_drive = drives.get("fear_drive", 0.0)
        training_drive = drives.get("training_drive", 0.0)
        
        # Update priorities based on drives
        # Hunger dramatically increases food-seeking priority
        self.current_priorities["seek_food"]["base_priority"] = 0.3 + (hunger_drive * 0.7)
        
        # Survival drive amplifies food-seeking
        if survival_drive > 0.5:
            self.current_priorities["seek_food"]["base_priority"] = min(1.0, 
                self.current_priorities["seek_food"]["base_priority"] + 0.2)
        
        # Fear increases fleeing priority
        self.current_priorities["flee"]["base_priority"] = 0.1 + (fear_drive * 0.8)
        
        # Training drive affects training priority
        self.current_priorities["train"]["base_priority"] = 0.2 + (training_drive * 0.6)
        
        # Context-based modifications
        if context.get("food_nearby", False):
            self.current_priorities["seek_food"]["base_priority"] = min(1.0,
                self.current_priorities["seek_food"]["base_priority"] + 0.3)
        
        if context.get("danger_nearby", False):
            self.current_priorities["flee"]["base_priority"] = 1.0
        
        if context.get("safe_location", False) and hunger_drive < 0.3:
            self.current_priorities["rest"]["base_priority"] = 0.4
        
        # Ensure priorities are in valid range
        for behavior in self.current_priorities:
            self.current_priorities[behavior]["base_priority"] = np.clip(
                self.current_priorities[behavior]["base_priority"], 0.0, 1.0)
    
    def select_behavior(self) -> str:
        """
        Select the highest priority behavior
        
        Returns:
            Selected behavior name
        """
        # Find behavior with highest priority
        max_priority = 0.0
        selected_behavior = "explore"  # Default behavior
        
        for behavior_name, behavior_data in self.current_priorities.items():
            if behavior_data["base_priority"] > max_priority:
                max_priority = behavior_data["base_priority"]
                selected_behavior = behavior_name
        
        # Update current behavior
        if self.current_behavior != selected_behavior:
            self._record_behavior_change(self.current_behavior, selected_behavior)
            self.current_behavior = selected_behavior
        
        # Activate selected behavior, deactivate others
        for behavior_name in self.current_priorities:
            self.current_priorities[behavior_name]["active"] = (behavior_name == selected_behavior)
        
        return selected_behavior
    
    def _record_behavior_change(self, old_behavior: str, new_behavior: str):
        """Record behavior change in history"""
        self.behavior_history.append({
            "from": old_behavior,
            "to": new_behavior,
            "time": len(self.behavior_history)
        })
        
        # Keep history at reasonable size
        if len(self.behavior_history) > self.max_history:
            self.behavior_history.pop(0)
    
    def get_behavior_weights(self) -> Dict[str, float]:
        """
        Get current behavior weights for decision making
        
        Returns:
            Dictionary mapping behavior names to weights
        """
        total_priority = sum(b["base_priority"] for b in self.current_priorities.values())
        
        if total_priority == 0:
            return {name: 0.0 for name in self.current_priorities.keys()}
        
        return {
            name: data["base_priority"] / total_priority
            for name, data in self.current_priorities.items()
        }
    
    def get_current_behavior(self) -> str:
        """Get the currently active behavior"""
        return self.current_behavior if self.current_behavior else "explore"
    
    def force_behavior(self, behavior_name: str):
        """
        Force a specific behavior (for testing or special circumstances)
        
        Args:
            behavior_name: Behavior to force
        """
        if behavior_name in self.current_priorities:
            self.current_behavior = behavior_name
            for name in self.current_priorities:
                self.current_priorities[name]["active"] = (name == behavior_name)
            print(f"Forced behavior: {behavior_name}")
        else:
            print(f"Unknown behavior: {behavior_name}")
    
    def get_priority_summary(self) -> dict:
        """Get summary of current priorities"""
        return {
            "current_behavior": self.current_behavior,
            "priorities": {name: data["base_priority"] 
                          for name, data in self.current_priorities.items()},
            "active_behaviors": [name for name, data in self.current_priorities.items() 
                                 if data["active"]],
            "behavior_changes": len(self.behavior_history)
        }
    
    def reset(self):
        """Reset behavior priorities to initial state"""
        self.current_priorities = {name: {"base_priority": data["base_priority"], "active": False}
                                  for name, data in self.behaviors.items()}
        self.current_behavior = None
        self.behavior_history = []
        print("Behavior priorities reset")


if __name__ == "__main__":
    # Test the behavior priorities
    print("Testing Behavior Priorities...")
    
    priorities = BehaviorPriorities()
    
    # Test initial state
    summary = priorities.get_priority_summary()
    print(f"Initial priorities: {summary}")
    
    # Test priority updates with different drives
    print("\nTesting priority updates...")
    
    # High hunger drive
    drives = {"hunger_drive": 0.8, "survival_drive": 0.6}
    priorities.update_priorities(drives)
    selected = priorities.select_behavior()
    print(f"High hunger - Selected: {selected}")
    print(f"Priorities: {priorities.get_priority_summary()}")
    
    # Fear drive
    drives = {"hunger_drive": 0.2, "fear_drive": 0.9}
    priorities.update_priorities(drives)
    selected = priorities.select_behavior()
    print(f"Fear drive - Selected: {selected}")
    
    # Training drive
    drives = {"hunger_drive": 0.1, "training_drive": 0.7}
    priorities.update_priorities(drives)
    selected = priorities.select_behavior()
    print(f"Training drive - Selected: {selected}")
    
    # Context effects
    context = {"food_nearby": True}
    drives = {"hunger_drive": 0.4}
    priorities.update_priorities(drives, context)
    selected = priorities.select_behavior()
    print(f"Food nearby - Selected: {selected}")
    
    # Test behavior weights
    print("\nTesting behavior weights...")
    weights = priorities.get_behavior_weights()
    print(f"Behavior weights: {weights}")
    
    # Test forced behavior
    print("\nTesting forced behavior...")
    priorities.force_behavior("rest")
    print(f"Forced rest - Current: {priorities.get_current_behavior()}")
    
    print("Behavior priorities test completed!")