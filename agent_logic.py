"""
Agent Logic Module - Sensory & Neural Inputs
Feeds telemetry and environmental data into the fly's neural network.
"""

import numpy as np
from typing import Dict, List, Tuple
import math


class AgentLogic:
    """
    Processes sensory inputs and generates neural network inputs for the fly
    """
    
    def __init__(self, input_size: int = 100):
        """
        Initialize agent logic
        
        Args:
            input_size: Size of neural network input vector
        """
        self.input_size = input_size
        
        # Physics tracking
        self.current_altitude = 0.0
        self.current_direction = np.array([0.0, 0.0, 1.0])
        self.current_speed = 0.0
        self.current_velocity = np.array([0.0, 0.0, 0.0])
        self.current_position = np.array([0.0, 0.0, 0.0])
        
        # Visual field parameters
        self.visual_field_radius = 5.0  # meters
        self.visual_fov = 120.0  # degrees
        
        # Obstacle detection
        self.detected_obstacles = []
        
        print(f"Agent Logic initialized with {input_size} inputs")
    
    def update_physics(self, position: np.ndarray, velocity: np.ndarray, dt: float):
        """
        Update physics tracking
        
        Args:
            position: Current 3D position
            velocity: Current velocity vector
            dt: Time step
        """
        self.current_position = position
        self.current_velocity = velocity
        
        # Calculate speed (magnitude of velocity)
        self.current_speed = np.linalg.norm(velocity)
        
        # Calculate direction (normalized velocity)
        if self.current_speed > 0.01:
            self.current_direction = velocity / self.current_speed
        else:
            self.current_direction = np.array([0.0, 0.0, 1.0])
        
        # Calculate altitude (z position)
        self.current_altitude = position[2]
    
    def get_neural_inputs(self, obstacles: List[Dict], wind_vector: np.ndarray = None) -> np.ndarray:
        """
        Generate neural network inputs from sensory data
        
        Args:
            obstacles: List of obstacle dictionaries
            wind_vector: Wind direction vector (optional)
            
        Returns:
            Neural input vector
        """
        inputs = np.zeros(self.input_size)
        
        # Input[0-2]: Altitude (normalized)
        inputs[0] = self.current_altitude / 10.0  # Normalize to 0-1 range
        inputs[1] = self.current_direction[0]
        inputs[2] = self.current_direction[1]
        inputs[3] = self.current_direction[2]
        
        # Input[4-6]: Speed (normalized)
        inputs[4] = self.current_speed / 5.0  # Normalize to max speed
        inputs[5] = self.current_velocity[0] / 5.0
        inputs[6] = self.current_velocity[1] / 5.0
        inputs[7] = self.current_velocity[2] / 5.0
        
        # Input[8-10]: Position (normalized)
        inputs[8] = self.current_position[0] / 10.0
        inputs[9] = self.current_position[1] / 10.0
        inputs[10] = self.current_position[2] / 50.0
        
        # Input[11-13]: Wind direction (normalized)
        if wind_vector is not None:
            inputs[11] = wind_vector[0] / 2.0
            inputs[12] = wind_vector[1] / 2.0
            inputs[13] = wind_vector[2] / 2.0
        else:
            inputs[11:14] = 0.0
        
        # Input[14-33]: Visual field (20 bins)
        visual_inputs = self.get_visual_field_inputs(obstacles)
        inputs[14:34] = visual_inputs
        
        # Input[34-53]: Obstacle proximity (20 nearest obstacles)
        obstacle_inputs = self.get_obstacle_proximity(obstacles)
        inputs[34:54] = obstacle_inputs
        
        # Input[54-73]: Relative obstacle layout data
        layout_inputs = self.get_obstacle_layout(obstacles)
        inputs[54:74] = layout_inputs
        
        # Input[74-99]: Reserved for additional sensors
        # (acceleration, angular velocity, etc.)
        
        return inputs
    
    def get_visual_field_inputs(self, obstacles: List[Dict]) -> np.ndarray:
        """
        Get visual field inputs (what the fly can see)
        
        Args:
            obstacles: List of obstacle dictionaries
            
        Returns:
            Visual field vector (20 bins)
        """
        visual_field = np.zeros(20)
        
        # Divide visual field into angular bins
        for i in range(20):
            angle_start = (i / 20) * 2 * math.pi
            angle_end = ((i + 1) / 20) * 2 * math.pi
            
            # Check if any obstacle in this angular bin
            for obstacle in obstacles:
                obs_pos = obstacle['position']
                obs_size = obstacle['size']
                
                # Calculate angle to obstacle
                dx = obs_pos[0] - self.current_position[0]
                dy = obs_pos[1] - self.current_position[1]
                angle = math.atan2(dy, dx)
                
                # Normalize angle to 0-2π
                angle = angle % (2 * math.pi)
                
                # Check if in bin
                if angle_start <= angle < angle_end:
                    # Check distance
                    distance = np.linalg.norm(obs_pos - self.current_position)
                    if distance < self.visual_field_radius:
                        # Input value based on distance (closer = higher)
                        visual_field[i] = 1.0 - (distance / self.visual_field_radius)
                        break
        
        return visual_field
    
    def get_obstacle_proximity(self, obstacles: List[Dict]) -> np.ndarray:
        """
        Get proximity to nearest obstacles
        
        Args:
            obstacles: List of obstacle dictionaries
            
        Returns:
        Proximity vector (20 nearest obstacles)
        """
        proximity = np.zeros(20)
        
        # Calculate distances to all obstacles
        distances = []
        for obstacle in obstacles:
            distance = np.linalg.norm(obstacle['position'] - self.current_position)
            distances.append(distance)
        
        # Sort and take 20 nearest
        distances.sort()
        for i in range(min(20, len(distances))):
            proximity[i] = 1.0 - (distances[i] / self.visual_field_radius)
        
        return proximity
    
    def get_obstacle_layout(self, obstacles: List[Dict]) -> np.ndarray:
        """
        Get relative obstacle layout data
        
        Args:
            obstacles: List of obstacle dictionaries
            
        Returns:
        Layout vector (20 nearest obstacles)
        """
        layout = np.zeros(20)
        
        # Get relative positions of 20 nearest obstacles
        distances = []
        for obstacle in obstacles:
            rel_pos = obstacle['position'] - self.current_position
            distances.append((np.linalg.norm(rel_pos), rel_pos))
        
        distances.sort(key=lambda x: x[0])
        
        for i in range(min(20, len(distances))):
            _, rel_pos = distances[i]
            # Normalize position
            layout[i*3] = rel_pos[0] / 10.0
            layout[i*3+1] = rel_pos[1] / 10.0
            layout[i*3+2] = rel_pos[2] / 50.0
        
        return layout
    
    def enforce_speed_limit(self, velocity: np.ndarray, max_speed: float = 5.0) -> np.ndarray:
        """
        Enforce speed limit on velocity
        
        Args:
            velocity: Current velocity vector
            max_speed: Maximum allowed speed
            
        Returns:
            Clamped velocity
        """
        speed = np.linalg.norm(velocity)
        if speed > max_speed:
            velocity = (velocity / speed) * max_speed
        return velocity


if __name__ == "__main__":
    agent = AgentLogic()
    print("Agent Logic module loaded")
