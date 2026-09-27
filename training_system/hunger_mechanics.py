"""
Hunger Mechanics
Implements sophisticated hunger system for the fly's survival behaviors
"""

import numpy as np
from typing import Dict, List
import time
import sys
import os

# Add parent directory to path for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class HungerMechanics:
    """
    Manages hunger levels and survival drives for the fly
    """
    
    def __init__(self, initial_energy: float = 100.0, max_energy: float = 100.0):
        """
        Initialize hunger mechanics
        
        Args:
            initial_energy: Starting energy level (0-100)
            max_energy: Maximum energy capacity
        """
        self.max_energy = max_energy
        self.energy = initial_energy
        self.hunger_level = 0.0  # 0 = not hungry, 100 = starving
        self.enabled = True  # When False the fly never gets hungry
        
        # Hunger parameters
        self.base_hunger_rate = 0.5  # Energy loss per second at rest
        self.activity_multiplier = 2.0  # Energy loss multiplier during activity
        self.starvation_threshold = 10.0  # Energy level where starvation begins
        self.critical_threshold = 5.0  # Energy level where critical health effects occur
        
        # Survival drives
        self.hunger_drive = 0.0  # Drive to seek food (0-1)
        self.survival_drive = 0.0  # Overall survival motivation (0-1)
        
        # Feeding history
        self.last_feeding_time = 0.0
        self.feeding_frequency = 0.0
        self.total_energy_consumed = 0.0
        
        # State tracking
        self.is_starving = False
        self.is_critical = False
        self.death_imminent = False
        
        print("Hunger mechanics initialized")
    
    def update_hunger(self, dt: float, activity_level: float = 0.0):
        """
        Update hunger level based on time and activity
        
        Args:
            dt: Time step in seconds
            activity_level: Current activity level (0-1)
        """
        if not self.enabled:
            self.hunger_level = 0.0
            self.hunger_drive = 0.0
            self.survival_drive = 0.0
            self.is_starving = False
            self.is_critical = False
            self.death_imminent = False
            return
        
        # Calculate energy loss
        energy_loss = self.base_hunger_rate * dt * (1 + activity_level * self.activity_multiplier)
        
        # Apply energy loss
        self.energy = max(0.0, self.energy - energy_loss)
        
        # Update hunger level (inverse of energy)
        self.hunger_level = 100.0 - (self.energy / self.max_energy * 100.0)
        
        # Update survival drives
        self._update_survival_drives()
        
        # Check starvation states
        self._check_starvation_states()
    
    def _update_survival_drives(self):
        """Update survival drive levels based on current state"""
        # Hunger drive increases as energy decreases
        if self.energy < 50.0:
            self.hunger_drive = (50.0 - self.energy) / 50.0
        else:
            self.hunger_drive = 0.0
        
        # Overall survival drive combines hunger with other factors
        self.survival_drive = max(self.hunger_drive, 0.0)
        
        # Critical states amplify survival drive
        if self.is_critical:
            self.survival_drive = min(1.0, self.survival_drive * 1.5)
        
        if self.is_starving:
            self.survival_drive = 1.0
    
    def _check_starvation_states(self):
        """Check and update starvation-related states"""
        self.is_starving = self.energy <= self.starvation_threshold
        self.is_critical = self.energy <= self.critical_threshold
        self.death_imminent = self.energy <= 0.0
    
    def consume_food(self, energy_gain: float):
        """
        Process food consumption and energy gain
        
        Args:
            energy_gain: Amount of energy gained from food
        """
        # Calculate actual energy gain (capped at max)
        actual_gain = min(energy_gain, self.max_energy - self.energy)
        
        # Apply energy gain
        self.energy += actual_gain
        self.total_energy_consumed += actual_gain
        
        # Update feeding history
        current_time = time.time()
        if self.last_feeding_time > 0:
            time_since_last_feed = current_time - self.last_feeding_time
            if time_since_last_feed > 0:
                self.feeding_frequency = 1.0 / time_since_last_feed
        
        self.last_feeding_time = current_time
        
        # Update hunger level immediately
        self.hunger_level = 100.0 - (self.energy / self.max_energy * 100.0)
        self._update_survival_drives()
        self._check_starvation_states()
    
    def set_enabled(self, enabled: bool):
        """
        Turn hunger on or off
        
        Args:
            enabled: When False, energy stops draining and all hunger drives are cleared
        """
        self.enabled = enabled
        if not enabled:
            self.hunger_level = 0.0
            self.hunger_drive = 0.0
            self.survival_drive = 0.0
            self.is_starving = False
            self.is_critical = False
            self.death_imminent = False
        else:
            self.hunger_level = 100.0 - (self.energy / self.max_energy * 100.0)
            self._update_survival_drives()
            self._check_starvation_states()
    
    def get_hunger_state(self) -> dict:
        """Get current hunger state information"""
        return {
            "enabled": self.enabled,
            "energy": self.energy,
            "max_energy": self.max_energy,
            "hunger_level": self.hunger_level,
            "hunger_drive": self.hunger_drive,
            "survival_drive": self.survival_drive,
            "is_starving": self.is_starving,
            "is_critical": self.is_critical,
            "death_imminent": self.death_imminent,
            "last_feeding_time": self.last_feeding_time,
            "feeding_frequency": self.feeding_frequency
        }
    
    def get_feeding_urgency(self) -> float:
        """
        Get urgency level for feeding (0-1)
        
        Returns:
            Urgency level: 0 = no urgency, 1 = critical urgency
        """
        if not self.enabled:
            return 0.0
        elif self.death_imminent:
            return 1.0
        elif self.is_critical:
            return 0.9
        elif self.is_starving:
            return 0.7
        elif self.hunger_drive > 0.5:
            return 0.5
        elif self.hunger_drive > 0.2:
            return 0.3
        else:
            return 0.0
    
    def should_seek_food(self) -> bool:
        """
        Determine if the fly should seek food based on current state
        
        Returns:
            True if food seeking is necessary
        """
        if not self.enabled:
            return False
        return self.hunger_drive > 0.3 or self.is_starving
    
    def reset(self, initial_energy: float = 100.0):
        """Reset hunger mechanics to initial state"""
        self.energy = initial_energy
        self.hunger_level = 0.0
        self.hunger_drive = 0.0
        self.survival_drive = 0.0
        self.last_feeding_time = 0.0
        self.feeding_frequency = 0.0
        self.total_energy_consumed = 0.0
        self.is_starving = False
        self.is_critical = False
        self.death_imminent = False
        print("Hunger mechanics reset")


if __name__ == "__main__":
    # Test the hunger mechanics
    print("Testing Hunger Mechanics...")
    
    hunger = HungerMechanics(initial_energy=100.0)
    
    # Test initial state
    state = hunger.get_hunger_state()
    print(f"Initial state: {state}")
    
    # Test hunger increase over time
    print("\nTesting hunger increase over time...")
    for i in range(10):
        hunger.update_hunger(dt=1.0, activity_level=0.5)
        state = hunger.get_hunger_state()
        print(f"Step {i}: Energy={state['energy']:.1f}, Hunger={state['hunger_level']:.1f}, Drive={state['hunger_drive']:.2f}")
    
    # Test food consumption
    print("\nTesting food consumption...")
    initial_energy = hunger.energy
    hunger.consume_food(30.0)
    state = hunger.get_hunger_state()
    print(f"Energy gain: {hunger.energy - initial_energy:.1f}")
    print(f"New state: {state}")
    
    # Test feeding urgency
    print("\nTesting feeding urgency...")
    print(f"Feeding urgency: {hunger.get_feeding_urgency()}")
    print(f"Should seek food: {hunger.should_seek_food()}")
    
    # Test starvation states
    print("\nTesting starvation states...")
    hunger.energy = 8.0  # Below critical threshold
    hunger.update_hunger(dt=0.1)
    state = hunger.get_hunger_state()
    print(f"Critical state: {state}")
    
    print("Hunger mechanics test completed!")