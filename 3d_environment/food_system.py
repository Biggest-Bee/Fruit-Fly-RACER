"""
Food System
Manages food locations, consumption, and feeding mechanics
"""

import numpy as np
from typing import List, Dict, Tuple
import time

class FoodSystem:
    """
    Manages food distribution and feeding mechanics
    """
    
    def __init__(self, world_size: Tuple[float, float, float] = (100.0, 100.0, 50.0)):
        """
        Initialize the food system
        
        Args:
            world_size: Dimensions of the world
        """
        self.world_size = world_size
        self.food_locations = []
        self.total_food_consumed = 0.0
        self.feeding_events = []
        
        # Food types and their properties
        self.food_types = {
            "sugar": {"energy_value": 20.0, "consumption_rate": 5.0},
            "protein": {"energy_value": 15.0, "consumption_rate": 3.0},
            "carbohydrate": {"energy_value": 10.0, "consumption_rate": 4.0}
        }
        
        print("Food system initialized")
    
    def add_food_location(self, position: Tuple[float, float, float], 
                         food_type: str = "sugar", amount: float = 100.0):
        """
        Add a food location to the system
        
        Args:
            position: (x, y, z) coordinates
            food_type: Type of food
            amount: Initial amount of food
        """
        if food_type not in self.food_types:
            print(f"Warning: Unknown food type '{food_type}', using 'sugar'")
            food_type = "sugar"
        
        food = {
            "position": np.array(position),
            "type": food_type,
            "amount": amount,
            "initial_amount": amount,
            "energy_value": self.food_types[food_type]["energy_value"],
            "consumption_rate": self.food_types[food_type]["consumption_rate"],
            "last_consumed": 0.0
        }
        self.food_locations.append(food)
        print(f"Added {food_type} food at {position} with {amount} units")
    
    def setup_corner_food(self):
        """Setup food in the corners of the world (as per project plan)"""
        width, depth, height = self.world_size
        corners = [
            (5.0, 5.0, 10.0),
            (width - 5.0, 5.0, 10.0),
            (5.0, depth - 5.0, 10.0),
            (width - 5.0, depth - 5.0, 10.0)
        ]
        
        for corner in corners:
            self.add_food_location(corner, food_type="sugar", amount=100.0)
        
        print(f"Food placed in {len(corners)} corners")
    
    def find_nearest_food(self, position: np.ndarray, max_distance: float = 50.0) -> Dict:
        """
        Find the nearest available food location
        
        Args:
            position: Current position
            max_distance: Maximum search distance
            
        Returns:
            Dictionary with nearest food info or None
        """
        nearest_food = None
        min_distance = float('inf')
        
        for food in self.food_locations:
            if food["amount"] > 0:  # Only available food
                distance = np.linalg.norm(food["position"] - position)
                if distance < min_distance and distance < max_distance:
                    min_distance = distance
                    nearest_food = food
        
        if nearest_food:
            return {
                "food": nearest_food,
                "distance": min_distance,
                "direction": (nearest_food["position"] - position) / min_distance,
                "index": self.food_locations.index(nearest_food)
            }
        
        return None
    
    def consume_food(self, food_index: int, consumption_time: float = 1.0) -> float:
        """
        Consume food from a specific location
        
        Args:
            food_index: Index of food location
            consumption_time: Time spent eating
            
        Returns:
            Energy gained from consumption
        """
        if 0 <= food_index < len(self.food_locations):
            food = self.food_locations[food_index]
            
            if food["amount"] > 0:
                # Calculate consumption amount
                consumption_amount = min(food["consumption_rate"] * consumption_time, food["amount"])
                
                # Calculate energy gained
                energy_gained = (consumption_amount / food["initial_amount"]) * food["energy_value"]
                
                # Update food amount
                food["amount"] -= consumption_amount
                food["last_consumed"] = time.time()
                self.total_food_consumed += consumption_amount
                
                # Record feeding event
                self.feeding_events.append({
                    "time": time.time(),
                    "food_index": food_index,
                    "amount_consumed": consumption_amount,
                    "energy_gained": energy_gained
                })
                
                return energy_gained
        
        return 0.0
    
    def regenerate_food(self, regeneration_rate: float = 0.01):
        """
        Slowly regenerate food over time
        
        Args:
            regeneration_rate: Rate of regeneration per time step
        """
        for food in self.food_locations:
            if food["amount"] < food["initial_amount"]:
                food["amount"] = min(food["initial_amount"], 
                                    food["amount"] + regeneration_rate)
    
    def get_food_status(self) -> dict:
        """Get current status of all food locations"""
        available_food = sum(f["amount"] for f in self.food_locations)
        total_capacity = sum(f["initial_amount"] for f in self.food_locations)
        
        return {
            "total_locations": len(self.food_locations),
            "available_food": available_food,
            "total_capacity": total_capacity,
            "food_percentage": (available_food / total_capacity * 100) if total_capacity > 0 else 0,
            "total_consumed": self.total_food_consumed,
            "feeding_events": len(self.feeding_events)
        }
    
    def get_food_location_info(self, index: int) -> dict:
        """Get detailed information about a specific food location"""
        if 0 <= index < len(self.food_locations):
            food = self.food_locations[index]
            return {
                "position": food["position"].tolist(),
                "type": food["type"],
                "amount": food["amount"],
                "initial_amount": food["initial_amount"],
                "energy_value": food["energy_value"],
                "available": food["amount"] > 0
            }
        return None
    
    def check_feeding_allowed(self, training_mode: bool, last_performance: str = "neutral") -> bool:
        """
        Check if feeding is allowed based on training mode and performance
        
        Args:
            training_mode: Whether fly is in training mode
            last_performance: Performance of last task ("correct", "incorrect", "neutral")
            
        Returns:
            True if feeding is allowed
        """
        if not training_mode:
            # Free feeding mode - always allowed
            return True
        else:
            # Training mode - only allowed if performance was correct
            return last_performance == "correct"
    
    def reset(self):
        """Reset food system to initial state"""
        for food in self.food_locations:
            food["amount"] = food["initial_amount"]
            food["last_consumed"] = 0.0
        
        self.total_food_consumed = 0.0
        self.feeding_events = []
        print("Food system reset to initial state")


if __name__ == "__main__":
    # Test the food system
    print("Testing Food System...")
    
    food_system = FoodSystem(world_size=(100.0, 100.0, 50.0))
    
    # Setup corner food
    food_system.setup_corner_food()
    
    # Test finding nearest food
    test_position = np.array([10.0, 10.0, 15.0])
    nearest = food_system.find_nearest_food(test_position)
    if nearest:
        print(f"Nearest food: {nearest['distance']:.2f} units away")
        print(f"Food type: {nearest['food']['type']}")
    
    # Test food consumption
    if nearest:
        food_index = nearest["index"]
        energy = food_system.consume_food(food_index, consumption_time=2.0)
        print(f"Consumed food, gained {energy:.1f} energy")
    
    # Test food status
    status = food_system.get_food_status()
    print(f"Food status: {status}")
    
    # Test feeding permission logic
    print("\nTesting feeding permission logic:")
    print(f"Training mode, correct performance: {food_system.check_feeding_allowed(True, 'correct')}")
    print(f"Training mode, incorrect performance: {food_system.check_feeding_allowed(True, 'incorrect')}")
    print(f"Free feeding mode: {food_system.check_feeding_allowed(False)}")
    
    # Test regeneration
    print("\nTesting food regeneration...")
    for i in range(5):
        food_system.regenerate_food(0.5)
        status = food_system.get_food_status()
        print(f"Step {i}: Available food: {status['available_food']:.1f}")
    
    print("Food system test completed!")