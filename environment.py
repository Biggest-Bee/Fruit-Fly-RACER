"""
Environment Module - 3D Obstacle Tunnel Racing Simulation
Creates a continuous 3D racing tunnel with dynamic wind fields and procedural obstacles.
"""

import numpy as np
import mujoco
import math
from typing import Dict, List, Tuple, Optional
import random


class RacingEnvironment:
    """
    3D racing tunnel environment with MuJoCo physics
    """
    
    def __init__(self, tunnel_length: float = 200.0, tunnel_radius: float = 10.0):
        """
        Initialize the racing environment
        
        Args:
            tunnel_length: Length of the tunnel (z-axis)
            tunnel_radius: Radius of the tunnel (x, y axes)
        """
        self.tunnel_length = tunnel_length
        self.tunnel_radius = tunnel_radius
        
        # Physics parameters
        self.max_speed = 5.0  # Maximum speed limit
        self.gravity = -9.81  # Gravity
        
        # Wind parameters
        self.wind_base_speed = 0.5
        self.wind_turbulence = 0.3
        self.wind_direction = np.array([1.0, 0.0, 0.0])  # Wind along tunnel
        
        # Obstacles
        self.obstacles = []
        self.obstacle_types = ['sphere', 'box', 'cylinder']
        
        # Physics limits
        self.current_speed = 0.0
        self.current_velocity = np.array([0.0, 0.0, 0.0])
        self.current_altitude = 0.0
        self.current_direction = np.array([0.0, 0.0, 1.0])
        self.current_position = np.array([0.0, 0.0, 0.0])
        
        print(f"Racing Environment initialized: {tunnel_length}m tunnel, {tunnel_radius}m radius")

    def reset(self):
        """Reset the environment to initial state"""
        # Reset wind
        self.wind_direction = np.array([1.0, 0.0, 0.0])
        self.wind_base_speed = 0.5
        self.wind_turbulence = 0.3

        # Reset physics state
        self.current_speed = 0.0
        self.current_velocity = np.array([0.0, 0.0, 0.0])
        self.current_altitude = 0.0
        self.current_direction = np.array([0.0, 0.0, 1.0])
        self.current_position = np.array([0.0, 0.0, -self.tunnel_length / 2])

        # Clear obstacles (will be regenerated)
        self.obstacles = []

        # Only print on first reset
        if not hasattr(self, '_reset_count'):
            self._reset_count = 0
        self._reset_count += 1
        if self._reset_count == 1:
            print("Environment reset")
    
    def generate_tunnel_mjcf(self) -> str:
        """
        Generate MuJoCo XML for the tunnel
        
        Returns:
            MuJoCo XML string
        """
        mjcf = f"""
<?xml version="1.0"?>
<mujoco>
    <world>
        <default>
            <geom solref="0.3" solrgba="0.7 0.7 0.7 1.0"/>
        <camera pos="0 2 {-self.tunnel_length/2}" quat="0 1 0 0"/>
        <light diffuse="0.8 0.8 0.8" specular="0.3 0.3 0.3" pos="0 10 0" dir="0 -1 0"/>
        <wind wind_type="0" direction="1 0 0" strength="{self.wind_base_speed}" turbulence="{self.wind_turbulence}"/>
        <global dt="0.02"/>
        <contact solver="0.01"/>
        <visual>
            <headlight diffuse="0.6 0.6 0.6" specular="0.3 0.3 0.3" ambient="0.1 0.1 0.1" back="0.02 0.02 0.02" fogstart="0" fogend="100" rgb1="0.3 0.3 0.3" rgb2="0.5 0.5 0.5"/>
        </visual>
    </default>
"""
        
        # Generate tunnel walls (cylinder)
        num_segments = 50
        segment_length = self.tunnel_length / num_segments
        
        for i in range(num_segments):
            z_pos = -self.tunnel_length/2 + i * segment_length
            
            # Generate curved tunnel walls
            num_wall_segments = 16
            for j in range(num_wall_segments):
                angle = 2 * math.pi * j / num_wall_segments
                x = self.tunnel_radius * math.cos(angle)
                y = self.tunnel_radius * math.sin(angle)
                
                mjcf += f"""
        <geom name="wall_{i}_{j}" type="cylinder" pos="{x} {y} {z_pos}" size="0.1 {self.tunnel_radius} {segment_length}" euler="0 0 {angle}" rgba="0.6 0.6 0.8 0.5"/>
"""
        
        # Generate finish line
        mjcf += f"""
        <geom name="finish_line" type="plane" pos="0 0 {self.tunnel_length/2}" size="{self.tunnel_radius*2} {self.tunnel_radius*2} 0.1" rgba="0.0 1.0 0.0 0.8"/>
        <site name="finish" pos="0 0 {self.tunnel_length/2}" size="0.01"/>
"""
        
        mjcf += "</world>\n</mujoco>"
        return mjcf
    
    def generate_obstacles(self, num_obstacles: int = 20, with_holes: bool = True):
        """
        Procedurally generate obstacles in the tunnel

        Args:
            num_obstacles: Number of obstacles to generate
            with_holes: Whether to include holes/apertures in obstacles

        Returns:
            List of obstacle dictionaries
        """
        self.obstacles = []
        errors = []

        try:
            for i in range(num_obstacles):
                try:
                    # Random position along tunnel
                    z_pos = random.uniform(-self.tunnel_length/2 + 5, self.tunnel_length/2 - 5)

                    # Random obstacle type
                    obs_type = random.choice(self.obstacle_types)

                    # Random position within tunnel
                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.uniform(0, self.tunnel_radius * 0.8)
                    x = radius * math.cos(angle)
                    y = radius * math.sin(angle)

                    # Random size
                    size = random.uniform(0.5, 2.0)

                    # Generate obstacle
                    obstacle = {
                        'type': obs_type,
                        'position': np.array([x, y, z_pos]),
                        'size': size,
                        'rotation': random.uniform(0, 2 * math.pi),
                        'has_hole': with_holes and random.random() < 0.5,  # 50% chance of hole
                        'hole_size': random.uniform(0.2, 0.5) if with_holes else 0.0
                    }

                    # Validate obstacle
                    if not self._validate_obstacle(obstacle):
                        errors.append(f"Obstacle {i} failed validation: {obstacle}")
                        continue

                    self.obstacles.append(obstacle)

                except Exception as e:
                    errors.append(f"Error generating obstacle {i}: {e}")
                    continue

        except Exception as e:
            errors.append(f"Critical error in generate_obstacles: {e}")
            import traceback
            errors.append(traceback.format_exc())

        # Count obstacles with holes
        hole_count = sum(1 for obs in self.obstacles if obs['has_hole'])

        # Log results
        if errors:
            print(f"ERRORS during obstacle generation:")
            for error in errors:
                print(f"  - {error}")

        print(f"Generated {len(self.obstacles)} obstacles ({hole_count} with holes, {len(self.obstacles) - hole_count} without)")

        # Log first few obstacles for debugging
        if self.obstacles:
            print(f"First 3 obstacles:")
            for i, obs in enumerate(self.obstacles[:3]):
                print(f"  {i}: type={obs['type']}, pos={obs['position']}, size={obs['size']:.2f}, has_hole={obs['has_hole']}")

        return self.obstacles

    def _validate_obstacle(self, obstacle: Dict) -> bool:
        """
        Validate obstacle parameters

        Args:
            obstacle: Obstacle dictionary

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['type', 'position', 'size', 'rotation', 'has_hole', 'hole_size']
            for field in required_fields:
                if field not in obstacle:
                    print(f"Missing field: {field}")
                    return False

            # Check position is within tunnel
            pos = obstacle['position']
            if abs(pos[0]) > self.tunnel_radius * 0.9:
                print(f"Obstacle X position out of bounds: {pos[0]}")
                return False
            if abs(pos[1]) > self.tunnel_radius * 0.9:
                print(f"Obstacle Y position out of bounds: {pos[1]}")
                return False
            if abs(pos[2]) > self.tunnel_length / 2:
                print(f"Obstacle Z position out of bounds: {pos[2]}")
                return False

            # Check size is reasonable
            if obstacle['size'] < 0.1 or obstacle['size'] > 5.0:
                print(f"Obstacle size out of range: {obstacle['size']}")
                return False

            # Check hole size is reasonable
            if obstacle['has_hole'] and (obstacle['hole_size'] < 0.1 or obstacle['hole_size'] > 1.0):
                print(f"Hole size out of range: {obstacle['hole_size']}")
                return False

            return True

        except Exception as e:
            print(f"Validation error: {e}")
            return False
    
    def get_obstacle_mjcf(self, obstacle: Dict) -> str:
        """
        Generate MuJoCo XML for a single obstacle
        
        Args:
            obstacle: Obstacle dictionary
            
        Returns:
            MuJoCo XML string for the obstacle
        """
        x, y, z = obstacle['position']
        size = obstacle['size']
        rot = obstacle['rotation']
        obs_type = obstacle['type']
        
        mjcf = ""
        
        if obs_type == 'cube':
            mjcf += f"""
        <geom name="obstacle" type="box" pos="{x} {y} {z}" size="{size} {size} {size}" euler="0 0 {rot}" rgba="0.8 0.4 0.4 0.8"/>
"""
        elif obs_type == 'sphere':
            mjcf += f"""
        <geom name="obstacle" type="sphere" pos="{x} {y} {z}" size="{size}" rgba="0.8 0.4 0.4 0.8"/>
"""
        elif obs_type == 'triangle':
            mjcf += f"""
        <geom name="obstacle" type="triangle" pos="{x} {y} {z}" size="{size} {size} {size}" euler="0 0 {rot}" rgba="0.8 0.4 0.4 0.8"/>
"""
        elif obs_type == 'plane':
            mjcf += f"""
        <geom name="obstacle" type="plane" pos="{x} {y} {z}" size="{size} {size} 0.1" euler="0 0 {rot}" rgba="0.8 0.4 0.4 0.8"/>
"""
        elif obs_type == 'wall':
            mjcf += f"""
        <geom name="obstacle" type="box" pos="{x} {y} {z}" size="{size} {size} {size*2}" euler="0 0 {rot}" rgba="0.8 0.4 0.4 0.8"/>
"""
        elif obs_type == 'cone':
            mjcf += f"""
        <geom name="obstacle" type="cylinder" pos="{x} {y} {z}" size="{size} {size*2} {size}" euler="0 0 {rot}" rgba="0.8 0.4 0.4 0.8"/>
"""
        
        # Add hole if applicable
        if obstacle['has_hole']:
            hole_size = obstacle['hole_size']
            hole_x = x + hole_size * 0.5
            mjcf += f"""
        <geom name="hole" type="sphere" pos="{hole_x} {y} {z}" size="{hole_size}" rgba="0.0 0.0 0.0 0.0"/>
"""
        
        return mjcf
    
    def get_full_mjcf(self) -> str:
        """
        Generate complete MuJoCo XML with tunnel and obstacles
        
        Returns:
            Complete MuJoCo XML string
        """
        mjcf = self.generate_tunnel_mjcf()
        
        # Add obstacles
        for obstacle in self.obstacles:
            mjcf += self.get_obstacle_mjcf(obstacle)
        
        return mjcf
    
    def update_wind(self, time_step: float):
        """
        Update wind field with turbulence
        
        Args:
            time_step: Current simulation time
        """
        # Add turbulence to wind
        turbulence = np.random.normal(0, self.wind_turbulence, 3)
        current_wind = self.wind_direction * (self.wind_base_speed + turbulence)
        
        return current_wind
    
    def check_collision(self, position: np.ndarray) -> bool:
        """
        Check if position collides with obstacles or walls
        
        Args:
            position: Current 3D position
            
        Returns:
            True if collision detected
        """
        x, y, z = position
        
        # Check tunnel walls
        if np.sqrt(x**2 + y**2) > self.tunnel_radius:
            return True
        
        # Check obstacles (more lenient collision detection)
        for obstacle in self.obstacles:
            obs_pos = obstacle['position']
            obs_size = obstacle['size']

            # Only check obstacles ahead of the fly
            if obs_pos[2] > z + 2.0:  # Skip obstacles behind or too close
                continue

            # Simple distance-based collision (less aggressive)
            distance = np.linalg.norm(position - obs_pos)
            if distance < obs_size * 0.5:  # Reduced collision radius

                # Check if hole (pass through)
                if obstacle['has_hole']:
                    hole_pos = obs_pos + np.array([obstacle['hole_size'] * 0.5, 0, 0])
                    if np.linalg.norm(position - hole_pos) < obstacle['hole_size']:
                        return False  # Pass through hole
                else:
                    return True  # Collision
        
        return False
    
    def get_progress_to_finish(self, position: np.ndarray) -> float:
        """
        Calculate progress to finish line (0 to 1)

        Args:
            position: Current 3D position [x, y, z] where x is tunnel direction

        Returns:
            Progress value between 0 and 1
        """
        # For horizontal tunnel, progress is along X-axis
        x = position[0]
        start_x = -self.tunnel_length / 2
        finish_x = self.tunnel_length / 2

        progress = (x - start_x) / (finish_x - start_x)
        return np.clip(progress, 0.0, 1.0)


if __name__ == "__main__":
    env = RacingEnvironment()
    env.generate_obstacles(num_obstacles=10, with_holes=True)
    mjcf = env.get_full_mjcf()
    
    print("Generated MuJoCo XML for racing environment")
    print(f"Tunnel length: {env.tunnel_length}m")
    print(f"Tunnel radius: {env.tunnel_radius}m")
    print(f"Max speed: {env.max_speed} m/s")
    print(f"Obstacles: {len(env.obstacles)}")
