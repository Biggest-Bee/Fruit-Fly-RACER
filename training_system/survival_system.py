"""
Survival System
Integrates hunger mechanics and behavior priorities for complete survival behaviors
"""

import numpy as np
from typing import Dict, List, Optional
import time
import sys
import os

# Add parent directory to path for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from .hunger_mechanics import HungerMechanics
    from .behavior_priorities import BehaviorPriorities
except ImportError:
    from hunger_mechanics import HungerMechanics
    from behavior_priorities import BehaviorPriorities

class SurvivalSystem:
    """
    Complete survival system integrating hunger, drives, and behavior decisions
    """
    
    def __init__(self, initial_energy: float = 100.0):
        """
        Initialize the survival system
        
        Args:
            initial_energy: Starting energy level
        """
        # Initialize subsystems
        self.hunger_mechanics = HungerMechanics(initial_energy=initial_energy)
        self.behavior_priorities = BehaviorPriorities()
        
        # Additional drives
        self.fear_drive = 0.0
        self.training_drive = 0.0
        self.exploration_drive = 0.5
        
        # Context information
        self.context = {
            "food_nearby": False,
            "danger_nearby": False,
            "safe_location": False,
            "training_available": False
        }
        
        # Survival state
        self.is_alive = True
        self.survival_time = 0.0
        self.death_time = None
        
        # Performance tracking
        self.feeding_events = 0
        self.behavior_transitions = 0
        self.critical_survival_events = 0
        
        print("Survival system initialized")
    
    def update(self, dt: float, activity_level: float = 0.0, 
               context_updates: Dict = None):
        """
        Update the entire survival system for one time step
        
        Args:
            dt: Time step in seconds
            activity_level: Current activity level (0-1)
            context_updates: Optional context information updates
        """
        # Update context if provided
        if context_updates:
            self.context.update(context_updates)
        
        # Update hunger mechanics
        self.hunger_mechanics.update_hunger(dt, activity_level)
        
        # Check if fly is still alive
        if self.hunger_mechanics.death_imminent:
            self.is_alive = False
            if self.death_time is None:
                self.death_time = time.time()
            return
        
        # Update survival time
        self.survival_time += dt
        
        # Update drives
        self._update_drives()
        
        # Update behavior priorities
        drives = {
            "hunger_drive": self.hunger_mechanics.hunger_drive,
            "survival_drive": self.hunger_mechanics.survival_drive,
            "fear_drive": self.fear_drive,
            "training_drive": self.training_drive
        }
        self.behavior_priorities.update_priorities(drives, self.context)
        
        # Select current behavior
        current_behavior = self.behavior_priorities.select_behavior()
        
        # Track behavior transitions
        if len(self.behavior_priorities.behavior_history) > self.behavior_transitions:
            self.behavior_transitions = len(self.behavior_priorities.behavior_history)
    
    def _update_drives(self):
        """Update various drives based on current state"""
        hunger_state = self.hunger_mechanics.get_hunger_state()
        
        # Fear drive based on critical states
        if hunger_state["is_critical"]:
            self.fear_drive = 0.8
        elif hunger_state["is_starving"]:
            self.fear_drive = 0.5
        else:
            self.fear_drive = 0.0
        
        # Training drive decreases when hungry
        if hunger_state["hunger_drive"] > 0.5:
            self.training_drive = max(0.0, self.training_drive - 0.1)
        elif self.context["training_available"]:
            self.training_drive = min(1.0, self.training_drive + 0.05)
        
        # Exploration drive varies with hunger
        if hunger_state["hunger_drive"] < 0.3:
            self.exploration_drive = 0.7
        elif hunger_state["hunger_drive"] < 0.6:
            self.exploration_drive = 0.4
        else:
            self.exploration_drive = 0.1
    
    def process_feeding(self, energy_gain: float):
        """
        Process a feeding event
        
        Args:
            energy_gain: Energy gained from food
        """
        self.hunger_mechanics.consume_food(energy_gain)
        self.feeding_events += 1
        
        # Update context - food was nearby
        self.context["food_nearby"] = False  # Reset after feeding
    
    def get_current_behavior(self) -> str:
        """Get the current survival behavior"""
        return self.behavior_priorities.get_current_behavior()
    
    def get_action_recommendation(self) -> Dict:
        """
        Get recommended action based on current state
        
        Returns:
            Dictionary with action recommendations
        """
        current_behavior = self.get_current_behavior()
        hunger_state = self.hunger_mechanics.get_hunger_state()
        
        action = {
            "behavior": current_behavior,
            "priority": self.behavior_priorities.current_priorities[current_behavior]["base_priority"],
            "urgency": self.hunger_mechanics.get_feeding_urgency(),
            "energy": hunger_state["energy"],
            "recommended_actions": []
        }
        
        # Add specific action recommendations based on behavior
        if current_behavior == "seek_food":
            action["recommended_actions"].append("navigate_to_food")
            action["recommended_actions"].append("land_and_eat")
            if hunger_state["is_critical"]:
                action["recommended_actions"].append("immediate_feeding")
        
        elif current_behavior == "explore":
            action["recommended_actions"].append("random_movement")
            action["recommended_actions"].append("environmental_scan")
        
        elif current_behavior == "rest":
            action["recommended_actions"].append("find_safe_location")
            action["recommended_actions"].append("reduce_activity")
        
        elif current_behavior == "flee":
            action["recommended_actions"].append("move_away_from_danger")
            action["recommended_actions"].append("increase_speed")
        
        elif current_behavior == "train":
            action["recommended_actions"].append("engage_training_task")
            action["recommended_actions"].append("focus_on_learning")
        
        return action
    
    def check_survival_status(self) -> dict:
        """
        Check overall survival status
        
        Returns:
            Dictionary with survival status information
        """
        hunger_state = self.hunger_mechanics.get_hunger_state()
        priority_summary = self.behavior_priorities.get_priority_summary()
        
        return {
            "is_alive": self.is_alive,
            "survival_time": self.survival_time,
            "energy": hunger_state["energy"],
            "hunger_level": hunger_state["hunger_level"],
            "current_behavior": self.get_current_behavior(),
            "survival_drive": hunger_state["survival_drive"],
            "feeding_urgency": self.hunger_mechanics.get_feeding_urgency(),
            "should_seek_food": self.hunger_mechanics.should_seek_food(),
            "feeding_events": self.feeding_events,
            "behavior_transitions": self.behavior_transitions
        }
    
    def set_training_mode(self, training_active: bool):
        """
        Set training mode status
        
        Args:
            training_active: Whether training is currently active
        """
        self.context["training_available"] = training_active
        if training_active:
            self.training_drive = 0.7
        else:
            self.training_drive = 0.0
    
    def update_context(self, context_updates: Dict):
        """
        Update environmental context
        
        Args:
            context_updates: Dictionary of context updates
        """
        self.context.update(context_updates)
    
    def reset(self, initial_energy: float = 100.0):
        """Reset survival system to initial state"""
        self.hunger_mechanics.reset(initial_energy)
        self.behavior_priorities.reset()
        
        self.fear_drive = 0.0
        self.training_drive = 0.0
        self.exploration_drive = 0.5
        
        self.context = {
            "food_nearby": False,
            "danger_nearby": False,
            "safe_location": False,
            "training_available": False
        }
        
        self.is_alive = True
        self.survival_time = 0.0
        self.death_time = None
        
        self.feeding_events = 0
        self.behavior_transitions = 0
        self.critical_survival_events = 0
        
        print("Survival system reset")


if __name__ == "__main__":
    # Test the survival system
    print("Testing Survival System...")
    
    try:
        from hunger_mechanics import HungerMechanics
        from behavior_priorities import BehaviorPriorities
    except ImportError:
        from training_system.hunger_mechanics import HungerMechanics
        from training_system.behavior_priorities import BehaviorPriorities
    
    survival = SurvivalSystem(initial_energy=100.0)
    
    # Test initial state
    status = survival.check_survival_status()
    print(f"Initial status: {status}")
    
    # Test normal operation
    print("\nTesting normal operation...")
    for i in range(5):
        survival.update(dt=1.0, activity_level=0.3)
        status = survival.check_survival_status()
        action = survival.get_action_recommendation()
        print(f"Step {i}: Behavior={action['behavior']}, Energy={status['energy']:.1f}")
    
    # Test hunger-driven behavior change
    print("\nTesting hunger-driven behavior...")
    survival.hunger_mechanics.energy = 30.0  # Make fly hungry
    survival.update(dt=0.1)
    status = survival.check_survival_status()
    action = survival.get_action_recommendation()
    print(f"Hungry state: Behavior={action['behavior']}, Urgency={action['urgency']}")
    
    # Test feeding
    print("\nTesting feeding event...")
    survival.process_feeding(25.0)
    status = survival.check_survival_status()
    print(f"After feeding: Energy={status['energy']:.1f}, Events={status['feeding_events']}")
    
    # Test training mode
    print("\nTesting training mode...")
    survival.set_training_mode(True)
    survival.update(dt=0.1)
    action = survival.get_action_recommendation()
    print(f"Training mode: Behavior={action['behavior']}")
    
    # Test context updates
    print("\nTesting context updates...")
    survival.update_context({"food_nearby": True})
    survival.update(dt=0.1)
    action = survival.get_action_recommendation()
    print(f"Food nearby: Behavior={action['behavior']}")
    
    # Test critical state
    print("\nTesting critical survival state...")
    survival.hunger_mechanics.energy = 3.0
    survival.update(dt=0.1)
    status = survival.check_survival_status()
    action = survival.get_action_recommendation()
    print(f"Critical state: Behavior={action['behavior']}, Alive={status['is_alive']}")
    
    print("Survival system test completed!")