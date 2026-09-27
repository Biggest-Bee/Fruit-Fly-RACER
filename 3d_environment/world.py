"""
3D World Environment
Creates the virtual environment where the fly can navigate
"""

import numpy as np
from typing import List, Tuple, Dict
import time

class World3D:
    """
    3D virtual world for fly navigation
    """
    
    def __init__(self, size: Tuple[float, float, float] = (100.0, 100.0, 50.0)):
        """
        Initialize the 3D world
        
        Args:
            size: World dimensions (width, depth, height) in virtual units
        """
        self.size = size  # (x, y, z) dimensions
        self.width, self.depth, self.height = size
        
        # World objects and features
        self.objects = []
        self.food_locations = []
        self.obstacles = []
        
        # Environment properties
        self.gravity = -9.8  # m/s^2
        self.air_resistance = 0.1
        self.lighting_conditions = "normal"
        
        # Time tracking
        self.world_time = 0.0
        self.dt = 0.016  # ~60 FPS
        
        print(f"3D World initialized: {self.width}x{self.depth}x{self.height} units")
    
    def add_food_location(self, position: Tuple[float, float, float], 
                         food_type: str = "sugar", amount: float = 100.0):
        """
        Add a food location to the world
        
        Args:
            position: (x, y, z) coordinates
            food_type: Type of food (sugar, protein, etc.)
            amount: Amount of food available
        """
        food = {
            "position": np.array(position),
            "type": food_type,
            "amount": amount,
            "initial_amount": amount,
            "consumed": 0.0
        }
        self.food_locations.append(food)
        print(f"Added {food_type} at position {position}")
    
    def add_obstacle(self, position: Tuple[float, float, float], 
                    size: Tuple[float, float, float]):
        """
        Add an obstacle to the world
        
        Args:
            position: (x, y, z) coordinates of obstacle center
            size: (width, depth, height) dimensions
        """
        obstacle = {
            "position": np.array(position),
            "size": np.array(size)
        }
        self.obstacles.append(obstacle)
        print(f"Added obstacle at {position} with size {size}")
    
    def get_corners_for_food(self) -> List[Tuple[float, float, float]]:
        """Get corner positions for food placement (as per project plan)"""
        corners = [
            (5.0, 5.0, 10.0),      # Bottom-left-front corner
            (self.width - 5.0, 5.0, 10.0),      # Bottom-right-front corner
            (5.0, self.depth - 5.0, 10.0),     # Bottom-left-back corner
            (self.width - 5.0, self.depth - 5.0, 10.0)     # Bottom-right-back corner
        ]
        return corners
    
    def setup_food_in_corners(self):
        """Place food in the corners of the world (as per project plan)"""
        corners = self.get_corners_for_food()
        for i, corner in enumerate(corners):
            self.add_food_location(corner, food_type="sugar", amount=100.0)
            print(f"Placed food in corner {i+1}: {corner}")
    
    def check_collision(self, position: np.ndarray, radius: float = 1.0) -> bool:
        """
        Check if a position collides with any obstacles
        
        Args:
            position: Position to check
            radius: Collision radius
            
        Returns:
            True if collision detected
        """
        # Check world boundaries
        if (position[0] < radius or position[0] > self.width - radius or
            position[1] < radius or position[1] > self.depth - radius or
            position[2] < radius or position[2] > self.height - radius):
            return True
        
        # Check obstacles
        for obstacle in self.obstacles:
            obs_pos = obstacle["position"]
            obs_size = obstacle["size"]
            
            # Simple AABB collision detection
            if (abs(position[0] - obs_pos[0]) < (obs_size[0]/2 + radius) and
                abs(position[1] - obs_pos[1]) < (obs_size[1]/2 + radius) and
                abs(position[2] - obs_pos[2]) < (obs_size[2]/2 + radius)):
                return True
        
        return False
    
    def find_nearest_food(self, position: np.ndarray) -> Dict:
        """
        Find the nearest food location to a given position
        
        Args:
            position: Current position
            
        Returns:
            Dictionary with nearest food info or None if no food available
        """
        if not self.food_locations:
            return None
        
        nearest_food = None
        min_distance = float('inf')
        
        for food in self.food_locations:
            if food["amount"] > 0:  # Only consider available food
                distance = np.linalg.norm(food["position"] - position)
                if distance < min_distance:
                    min_distance = distance
                    nearest_food = food
        
        if nearest_food:
            return {
                "food": nearest_food,
                "distance": min_distance,
                "direction": (nearest_food["position"] - position) / min_distance
            }
        
        return None
    
    def consume_food(self, food_index: int, amount: float = 10.0) -> float:
        """
        Consume food from a specific location
        
        Args:
            food_index: Index of food location
            amount: Amount to consume
            
        Returns:
            Actual amount consumed
        """
        if 0 <= food_index < len(self.food_locations):
            food = self.food_locations[food_index]
            consumed = min(amount, food["amount"])
            food["amount"] -= consumed
            food["consumed"] += consumed
            return consumed
        return 0.0
    
    def update(self):
        """Update world state for one time step"""
        self.world_time += self.dt
        
        # Regenerate food over time (optional)
        for food in self.food_locations:
            if food["amount"] < food["initial_amount"]:
                food["amount"] += 0.01  # Slow regeneration
    
    def get_world_state(self) -> dict:
        """Get current world state"""
        return {
            "time": self.world_time,
            "size": self.size,
            "food_locations": len(self.food_locations),
            "obstacles": len(self.obstacles),
            "available_food": sum(f["amount"] for f in self.food_locations)
        }
    
    def reset(self):
        """Reset world to initial state"""
        self.world_time = 0.0
        for food in self.food_locations:
            food["amount"] = food["initial_amount"]
            food["consumed"] = 0.0
        print("World reset to initial state")


if __name__ == "__main__":
    # Test the 3D world
    print("Testing 3D World...")
    
    world = World3D(size=(100.0, 100.0, 50.0))
    
    # Setup food in corners
    world.setup_food_in_corners()
    
    # Add some obstacles
    world.add_obstacle((50.0, 50.0, 25.0), (10.0, 10.0, 20.0))
    
    # Test collision detection
    test_position = np.array([50.0, 50.0, 25.0])
    collision = world.check_collision(test_position)
    print(f"Collision at center: {collision}")
    
    # Test nearest food finding
    test_position = np.array([10.0, 10.0, 15.0])
    nearest = world.find_nearest_food(test_position)
    if nearest:
        print(f"Nearest food: {nearest['distance']:.2f} units away")
    
    # Test food consumption
    world_state = world.get_world_state()
    print(f"World state: {world_state}")
    
    print("3D World test completed!")