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
        # Obstacle types - 3D shapes: squares=cube, triangles=pyramid/tetrahedron,
        # circles=sphere, rectangles=box
        self.obstacle_types = ['cube', 'box', 'sphere', 'cylinder', 'pyramid', 'tetrahedron']
        
        # Physics limits
        self.current_speed = 0.0
        self.current_velocity = np.array([0.0, 0.0, 0.0])
        self.current_altitude = 0.0
        self.current_direction = np.array([0.0, 0.0, 1.0])
        self.current_position = np.array([0.0, 0.0, 0.0])

        # Steering gains - learned/adjusted per episode based on score
        self.steer_gain = 1.0       # scales avoidance steering
        self.center_gain = 0.08     # pull toward tunnel center
        self.avoid_margin = 3.0     # extra margin around obstacles
        
        print(f"Racing Environment initialized: {tunnel_length}m tunnel, {tunnel_radius}m radius")

    def reset(self):
        """Reset the environment to initial state"""
        # Random wind per episode: mostly along the tunnel with a random
        # lateral component, gentle base speed and turbulence
        wind_angle = random.uniform(-0.5, 0.5)   # radians off tunnel axis
        self.wind_direction = np.array([
            math.cos(wind_angle),
            random.uniform(-0.3, 0.3),            # slight vertical
            math.sin(wind_angle) * random.uniform(-1, 1),  # lateral gusts
        ])
        self.wind_direction /= np.linalg.norm(self.wind_direction)
        self.wind_base_speed = random.uniform(0.2, 0.8)   # m/s - gentle
        self.wind_turbulence = random.uniform(0.1, 0.35)  # sigma

        # Reset physics state
        self.current_speed = 0.0
        self.current_velocity = np.array([0.0, 0.0, 0.0])
        self.current_altitude = 0.0
        self.current_direction = np.array([0.0, 0.0, 1.0])
        self.current_position = np.array([-self.tunnel_length / 2, 0.0, 0.0])

        # NOTE: obstacles are intentionally NOT cleared here - they persist
        # across episodes and are regenerated periodically by the simulation loop

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
                    # Random position along tunnel - keep obstacles before
                    # the finish line (10m before the end wall)
                    z_pos = random.uniform(-self.tunnel_length/2 + 5,
                                           self.tunnel_length/2 - 15)

                    # Random obstacle type
                    obs_type = random.choice(self.obstacle_types)

                    # Random size - bigger obstacles
                    size = random.uniform(2.5, min(5.0, self.tunnel_radius * 0.5))

                    # Generate normally at a random position in the tunnel
                    angle = random.uniform(0, 2 * math.pi)
                    radial = random.uniform(0, self.tunnel_radius * 0.85)

                    # If the obstacle's extent touches the tunnel wall, it
                    # becomes wall-mounted: snap it so it merges into the wall
                    wall_mounted = (radial + size) >= self.tunnel_radius
                    if wall_mounted:
                        radial = self.tunnel_radius - size * random.uniform(0.3, 0.5)
                    lateral = radial * math.cos(angle)   # -> position[2]
                    vertical = radial * math.sin(angle)  # -> position[1]

                    # Generate obstacle - position stored as [tunnel_x, vertical_y, lateral_z]
                    obstacle = {
                        'type': obs_type,
                        'position': np.array([z_pos, vertical, lateral]),
                        'size': size,
                        'rotation': random.uniform(0, 2 * math.pi),
                        'has_hole': with_holes and random.random() < 0.5,  # 50% chance of hole
                        'hole_size': random.uniform(0.03, 0.1) if with_holes else 0.0,  # small pinholes - mostly solid
                        'wall_mounted': wall_mounted
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
            # position = [x=tunnel direction, y=vertical, z=lateral]
            pos = obstacle['position']
            if abs(pos[0]) > self.tunnel_length / 2:
                print(f"Obstacle tunnel position out of bounds: {pos[0]}")
                return False
            cross_section_radius = np.sqrt(pos[1]**2 + pos[2]**2)
            if cross_section_radius > self.tunnel_radius * 0.95:
                print(f"Obstacle cross-section position out of bounds: {cross_section_radius}")
                return False

            # Check size is reasonable
            if obstacle['size'] < 0.1 or obstacle['size'] > 8.0:
                print(f"Obstacle size out of range: {obstacle['size']}")
                return False

            # Check hole size is reasonable (small pinholes)
            if obstacle['has_hole'] and (obstacle['hole_size'] < 0.02 or obstacle['hole_size'] > 0.15):
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
        # position = [x=tunnel direction, y=vertical, z=lateral]
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
            hole_z = z + hole_size * 0.5
            mjcf += f"""
        <geom name="hole" type="sphere" pos="{x} {y} {hole_z}" size="{hole_size}" rgba="0.0 0.0 0.0 0.0"/>
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
        # Add turbulence to wind, then cap total wind speed so it never
        # gets strong enough to overwhelm the fly (max ~1.5 m/s vs fly 4 m/s)
        turbulence = np.random.normal(0, self.wind_turbulence, 3)
        current_wind = self.wind_direction * (self.wind_base_speed + turbulence)
        wind_speed = np.linalg.norm(current_wind)
        if wind_speed > 1.5:
            current_wind *= 1.5 / wind_speed

        return current_wind
    
    # Approximate collision radii as fraction of obstacle size, per shape
    _COLLISION_RADIUS = {
        'sphere': 1.0,      # drawn as radius=size
        'cylinder': 0.6,
        'cube': 0.6,
        'box': 0.55,
        'pyramid': 0.55,
        'tetrahedron': 0.55,
    }

    def collision_radius(self, obstacle: Dict) -> float:
        """Get the solid collision radius for an obstacle"""
        return obstacle['size'] * self._COLLISION_RADIUS.get(obstacle.get('type', 'sphere'), 0.6)

    def resolve_collision(self, position: np.ndarray):
        """
        Push position out of any obstacle it overlaps - makes obstacles solid.
        Returns (new_position, hit_obstacle or None).
        """
        pos = np.array(position, dtype=float)
        for obs in self.obstacles:
            obs_pos = obs['position']
            # Broadphase: skip obstacles far away along the tunnel
            if abs(obs_pos[0] - pos[0]) > self.collision_radius(obs) + 1.0:
                continue
            d = pos - obs_pos
            dist = np.linalg.norm(d)
            radius = self.collision_radius(obs)
            if dist < radius:
                if dist > 1e-6:
                    pos = obs_pos + d / dist * radius
                else:
                    pos = obs_pos + np.array([0.0, 0.0, radius])
                return pos, obs
        return pos, None

    def get_steering(self, position: np.ndarray, lookahead: float = 20.0):
        """
        Compute lateral/vertical steering to avoid obstacles ahead.
        Returns a [0, vy, vz] steering vector (m/s scale).
        """
        steer = np.zeros(3)
        x, y, z = position

        for obs in self.obstacles:
            ox, oy, oz = obs['position']
            dx = ox - x
            if dx < 0.5 or dx > lookahead:
                continue  # only obstacles ahead of the fly

            dy, dz = oy - y, oz - z
            dist_yz = np.hypot(dy, dz)
            obs_radius = self.collision_radius(obs)
            margin = obs_radius + self.avoid_margin

            if dist_yz < margin:
                if dist_yz > 1e-6:
                    # Push away from obstacle in the cross-section plane
                    steer[1] -= (dy / dist_yz) * (margin - dist_yz)
                    steer[2] -= (dz / dist_yz) * (margin - dist_yz)
                else:
                    # Dead center - random jink
                    steer[1] += random.uniform(-1.0, 1.0)
                    steer[2] += random.uniform(-1.0, 1.0)

        # Gentle centering force keeps fly near tunnel middle between obstacles
        steer[1] += -y * self.center_gain
        steer[2] += -z * self.center_gain

        # Clamp steering magnitude (gain learned per episode)
        lat_norm = np.linalg.norm(steer[1:])
        max_steer = 3.0 * self.steer_gain
        if lat_norm > max_steer:
            steer[1:] *= max_steer / lat_norm
        return steer

    def check_collision(self, position: np.ndarray) -> bool:
        """
        Check if position collides with obstacles or walls
        
        Args:
            position: Current 3D position
            
        Returns:
            True if collision detected
        """
        # position = [x=tunnel direction, y=vertical, z=lateral]
        x, y, z = position

        # Check tunnel walls (radial distance in Y-Z cross-section)
        if np.sqrt(y**2 + z**2) > self.tunnel_radius:
            return True

        # Check obstacles (more lenient collision detection)
        for obstacle in self.obstacles:
            obs_pos = obstacle['position']
            obs_size = obstacle['size']

            # Only check obstacles ahead of the fly (along tunnel X-axis)
            if obs_pos[0] > x + 2.0:  # Skip obstacles behind or too close
                continue

            # Distance-based collision using per-shape solid radius
            distance = np.linalg.norm(position - obs_pos)
            if distance < self.collision_radius(obs):

                # Check if hole (pass through) - hole offset along lateral axis
                if obstacle['has_hole']:
                    hole_pos = obs_pos + np.array([0.0, 0.0, obstacle['hole_size'] * 0.5])
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
        # For horizontal tunnel, progress is along X-axis.
        # Finish line sits 10m before the end wall so the fly finishes
        # without slamming into the cap.
        x = position[0]
        start_x = -self.tunnel_length / 2
        finish_x = self.tunnel_length / 2 - 10.0

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
