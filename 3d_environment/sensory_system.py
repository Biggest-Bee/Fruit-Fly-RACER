"""
Sensory System
Simulates the fly's sensory inputs (visual, proprioception, chemical)
"""

import numpy as np
from typing import Dict, List, Tuple
import math

class SensorySystem:
    """
    Simulates the fly's sensory inputs for processing by the brain
    """
    
    def __init__(self, world_size: Tuple[float, float, float] = (100.0, 100.0, 50.0)):
        """
        Initialize the sensory system
        
        Args:
            world_size: Dimensions of the world
        """
        self.world_size = world_size
        
        # Visual system parameters
        self.visual_range = 30.0  # Maximum visual distance
        self.visual_field = 120.0  # Visual field angle in degrees
        self.eyes_separation = 2.0  # Distance between compound eyes
        
        # Chemical sensors
        self.chemical_range = 15.0  # Range for chemical detection
        self.chemical_sensitivity = 0.8  # Sensitivity to chemical signals
        
        # Proprioception
        self.position_tolerance = 0.5  # Position sensing accuracy
        self.velocity_tolerance = 0.1  # Velocity sensing accuracy
        
        # Current sensory state
        self.visual_input = np.zeros((20, 20))  # Simplified visual field
        self.chemical_input = {}  # Chemical signals by type
        self.proprioception_input = {}
        
        print("Sensory system initialized")
    
    def process_visual_input(self, fly_position: np.ndarray, fly_orientation: dict,
                            food_locations: List[Dict], obstacles: List[Dict]) -> np.ndarray:
        """
        Process visual input from the environment
        
        Args:
            fly_position: Current fly position
            fly_orientation: Current fly orientation (yaw, pitch, roll)
            food_locations: List of food locations in the world
            obstacles: List of obstacles in the world
            
        Returns:
            Visual input array (simplified representation)
        """
        # Create simplified visual field (20x20 grid)
        visual_field = np.zeros((20, 20))
        
        # Process each food location
        for food in food_locations:
            if food["amount"] > 0:
                food_pos = food["position"]
                distance = np.linalg.norm(food_pos - fly_position)
                
                if distance < self.visual_range:
                    # Calculate angle to food
                    direction = food_pos - fly_position
                    angle = math.atan2(direction[1], direction[0])
                    
                    # Adjust for fly orientation
                    relative_angle = angle - fly_orientation["yaw"]
                    
                    # Normalize angle
                    while relative_angle > math.pi:
                        relative_angle -= 2 * math.pi
                    while relative_angle < -math.pi:
                        relative_angle += 2 * math.pi
                    
                    # Map to visual field
                    if abs(relative_angle) < math.radians(self.visual_field / 2):
                        # Calculate position in visual field
                        field_x = int((relative_angle / math.radians(self.visual_field / 2) + 1) * 10)
                        # Avoid division by zero
                        safe_distance = max(distance, 0.1)
                        field_y = int((direction[2] / safe_distance + 1) * 10)
                        
                        # Clamp to field bounds
                        field_x = np.clip(field_x, 0, 19)
                        field_y = np.clip(field_y, 0, 19)
                        
                        # Set intensity based on distance
                        intensity = 1.0 - (distance / self.visual_range)
                        visual_field[field_y, field_x] = max(visual_field[field_y, field_x], intensity)
        
        # Process obstacles
        for obstacle in obstacles:
            obs_pos = obstacle["position"]
            distance = np.linalg.norm(obs_pos - fly_position)
            
            if distance < self.visual_range:
                # Similar processing as food
                direction = obs_pos - fly_position
                angle = math.atan2(direction[1], direction[0])
                relative_angle = angle - fly_orientation["yaw"]
                
                while relative_angle > math.pi:
                    relative_angle -= 2 * math.pi
                while relative_angle < -math.pi:
                    relative_angle += 2 * math.pi
                
                if abs(relative_angle) < math.radians(self.visual_field / 2):
                    field_x = int((relative_angle / math.radians(self.visual_field / 2) + 1) * 10)
                    # Avoid division by zero
                    safe_distance = max(distance, 0.1)
                    field_y = int((direction[2] / safe_distance + 1) * 10)
                    field_x = np.clip(field_x, 0, 19)
                    field_y = np.clip(field_y, 0, 19)
                    
                    # Obstacles appear as dark spots
                    intensity = 1.0 - (distance / self.visual_range)
                    visual_field[field_y, field_x] = min(visual_field[field_y, field_x], -intensity)
        
        self.visual_input = visual_field
        return visual_field
    
    def process_chemical_input(self, fly_position: np.ndarray, 
                             food_locations: List[Dict]) -> Dict[str, float]:
        """
        Process chemical input (smell/taste) from the environment
        
        Args:
            fly_position: Current fly position
            food_locations: List of food locations
            
        Returns:
            Dictionary of chemical signals by type
        """
        chemical_signals = {}
        
        for food in food_locations:
            if food["amount"] > 0:
                food_pos = food["position"]
                distance = np.linalg.norm(food_pos - fly_position)
                
                if distance < self.chemical_range:
                    # Chemical signal strength decreases with distance
                    signal_strength = (1.0 - distance / self.chemical_range) * self.chemical_sensitivity
                    signal_strength *= (food["amount"] / food["initial_amount"])  # More food = stronger signal
                    
                    food_type = food["type"]
                    chemical_signals[food_type] = chemical_signals.get(food_type, 0.0) + signal_strength
        
        self.chemical_input = chemical_signals
        return chemical_signals
    
    def process_proprioception(self, fly_position: np.ndarray, fly_velocity: np.ndarray,
                              fly_orientation: dict) -> Dict[str, np.ndarray]:
        """
        Process proprioceptive input (body position, movement, orientation)
        
        Args:
            fly_position: Current fly position
            fly_velocity: Current fly velocity
            fly_orientation: Current fly orientation
            
        Returns:
            Dictionary with proprioceptive information
        """
        proprioception = {
            "position": fly_position + np.random.normal(0, self.position_tolerance, 3),
            "velocity": fly_velocity + np.random.normal(0, self.velocity_tolerance, 3),
            "orientation": {
                "yaw": fly_orientation["yaw"] + np.random.normal(0, 0.05),
                "pitch": fly_orientation["pitch"] + np.random.normal(0, 0.05),
                "roll": fly_orientation["roll"] + np.random.normal(0, 0.05)
            },
            "speed": np.linalg.norm(fly_velocity)
        }
        
        self.proprioception_input = proprioception
        return proprioception
    
    def get_sensory_summary(self) -> dict:
        """Get summary of current sensory input"""
        return {
            "visual_intensity": float(np.mean(np.abs(self.visual_input))),
            "chemical_signals": self.chemical_input,
            "proprioception": {
                "position": self.proprioception_input.get("position"),
                "speed": self.proprioception_input.get("speed")
            }
        }
    
    def convert_to_brain_input(self) -> Dict[str, float]:
        """
        Convert sensory input to brain activation patterns
        
        Returns:
            Dictionary mapping sensory concepts to activation levels
        """
        brain_input = {}
        
        # Visual input
        visual_intensity = float(np.mean(np.abs(self.visual_input)))
        if visual_intensity > 0.001:  # Even lower threshold
            brain_input["sensory"] = visual_intensity * 30.0
        
        # Chemical input (food smell)
        for chemical_type, strength in self.chemical_input.items():
            if strength > 0.001:  # Even lower threshold
                brain_input["sensory"] = brain_input.get("sensory", 0.0) + strength * 25.0
        
        # Proprioceptive input
        speed = self.proprioception_input.get("speed", 0.0)
        if speed > 5.0:
            brain_input["motor"] = speed * 2.0
        
        return brain_input


if __name__ == "__main__":
    # Test the sensory system
    print("Testing Sensory System...")
    
    sensory = SensorySystem(world_size=(100.0, 100.0, 50.0))
    
    # Create test environment
    fly_position = np.array([50.0, 50.0, 25.0])
    fly_orientation = {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
    fly_velocity = np.array([5.0, 0.0, 0.0])
    
    food_locations = [
        {"position": np.array([60.0, 60.0, 25.0]), "type": "sugar", "amount": 100.0, "initial_amount": 100.0}
    ]
    obstacles = [
        {"position": np.array([55.0, 55.0, 25.0]), "size": np.array([5.0, 5.0, 5.0])}
    ]
    
    # Test visual processing
    print("\nTesting visual processing...")
    visual = sensory.process_visual_input(fly_position, fly_orientation, food_locations, obstacles)
    print(f"Visual field shape: {visual.shape}")
    print(f"Visual intensity: {np.mean(np.abs(visual)):.3f}")
    
    # Test chemical processing
    print("\nTesting chemical processing...")
    chemical = sensory.process_chemical_input(fly_position, food_locations)
    print(f"Chemical signals: {chemical}")
    
    # Test proprioception
    print("\nTesting proprioception...")
    proprioception = sensory.process_proprioception(fly_position, fly_velocity, fly_orientation)
    print(f"Proprioception speed: {proprioception['speed']:.2f}")
    
    # Test brain input conversion
    print("\nTesting brain input conversion...")
    brain_input = sensory.convert_to_brain_input()
    print(f"Brain input: {brain_input}")
    
    # Test sensory summary
    print("\nSensory summary:")
    summary = sensory.get_sensory_summary()
    print(summary)
    
    print("Sensory system test completed!")