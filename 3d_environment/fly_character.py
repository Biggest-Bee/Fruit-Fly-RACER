"""
Fly Character
Implements the fly character with flight mechanics and movement
"""

import numpy as np
from typing import Tuple, Dict
import math

class FlyCharacter:
    """
    Fly character with realistic flight mechanics
    """
    
    def __init__(self, start_position: Tuple[float, float, float] = (50.0, 50.0, 25.0)):
        """
        Initialize the fly character
        
        Args:
            start_position: Initial (x, y, z) position
        """
        # Position and orientation
        self.position = np.array(start_position, dtype=float)
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=float)
        self.acceleration = np.array([0.0, 0.0, 0.0], dtype=float)
        
        # Orientation (yaw, pitch, roll)
        self.yaw = 0.0  # Rotation around Z axis
        self.pitch = 0.0  # Rotation around Y axis
        self.roll = 0.0  # Rotation around X axis
        
        # Flight characteristics
        self.max_speed = 15.0  # units per second
        self.max_acceleration = 30.0  # units per second squared
        self.turn_rate = 5.0  # radians per second
        self.mass = 1.0  # arbitrary mass units
        
        # Wing beat frequency (for animation and sound)
        self.wing_beat_frequency = 200.0  # Hz (typical for fruit flies)
        self.wing_beat_phase = 0.0
        
        # Energy and state
        self.energy = 100.0  # Energy level (0-100)
        self.is_flying = True
        self.is_landed = False
        self.is_eating = False
        
        # Flight mode
        self.flight_mode = "free"  # "free", "navigating", "landing"
        self.target_position = None
        
        print(f"Fly character initialized at position {start_position}")
    
    def update(self, dt: float, control_input: Dict = None):
        """
        Update fly physics for one time step
        
        Args:
            dt: Time step in seconds
            control_input: Dictionary with control inputs (thrust, yaw, pitch, roll)
        """
        if control_input is None:
            control_input = {}
        
        # Extract control inputs with defaults
        thrust = control_input.get("thrust", 0.0)
        yaw_input = control_input.get("yaw", 0.0)
        pitch_input = control_input.get("pitch", 0.0)
        roll_input = control_input.get("roll", 0.0)
        lift = control_input.get("lift", 0.0)  # Vertical wing thrust (hovering)
        
        # Update orientation
        self.yaw += yaw_input * self.turn_rate * dt
        self.pitch += pitch_input * self.turn_rate * dt
        self.roll += roll_input * self.turn_rate * dt
        
        # Clamp pitch and roll to reasonable limits
        self.pitch = np.clip(self.pitch, -math.pi/3, math.pi/3)
        self.roll = np.clip(self.roll, -math.pi/4, math.pi/4)
        
        # Calculate thrust direction based on orientation
        thrust_direction = self._get_thrust_direction()
        
        # Apply thrust
        thrust_force = thrust_direction * thrust * self.max_acceleration
        
        # Apply vertical wing thrust
        lift_force = np.array([0.0, 0.0, lift * self.max_acceleration])
        
        # Apply gravity (counteracted by thrust when flying)
        gravity_force = np.array([0.0, 0.0, -9.8]) * self.mass
        
        # Calculate total force
        total_force = thrust_force + lift_force + gravity_force
        
        # Apply air resistance
        drag_force = -0.5 * self.velocity * np.linalg.norm(self.velocity) * 0.1
        total_force += drag_force
        
        # Update acceleration (F = ma)
        self.acceleration = total_force / self.mass
        
        # Update velocity
        self.velocity += self.acceleration * dt
        
        # Clamp velocity to max speed
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = (self.velocity / speed) * self.max_speed
        
        # Update position
        self.position += self.velocity * dt
        
        # Update wing beat phase
        self.wing_beat_phase += self.wing_beat_frequency * dt * 2 * math.pi
        self.wing_beat_phase %= 2 * math.pi
        
        # Update energy
        if self.is_flying:
            energy_consumption = (speed / self.max_speed) * 0.1 * dt
            self.energy = max(0.0, self.energy - energy_consumption)
    
    def _get_thrust_direction(self) -> np.ndarray:
        """Calculate thrust direction based on current orientation"""
        # Simple model: thrust direction based on pitch and yaw
        # Forward direction (x-axis) rotated by pitch and yaw
        
        # Base forward direction
        forward = np.array([1.0, 0.0, 0.0])
        
        # Apply pitch (rotation around Y axis)
        cos_pitch = math.cos(self.pitch)
        sin_pitch = math.sin(self.pitch)
        forward = np.array([
            forward[0] * cos_pitch + forward[2] * sin_pitch,
            forward[1],
            -forward[0] * sin_pitch + forward[2] * cos_pitch
        ])
        
        # Apply yaw (rotation around Z axis)
        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        forward = np.array([
            forward[0] * cos_yaw - forward[1] * sin_yaw,
            forward[0] * sin_yaw + forward[1] * cos_yaw,
            forward[2]
        ])
        
        return forward
    
    def navigate_to(self, target_position: np.ndarray, dt: float):
        """
        Auto-navigate to a target position
        
        Args:
            target_position: Target (x, y, z) coordinates
            dt: Time step
        """
        self.flight_mode = "navigating"
        self.target_position = target_position
        
        # Calculate direction to target
        direction = target_position - self.position
        distance = np.linalg.norm(direction)
        
        if distance > 0.1:  # Not at target yet
            direction = direction / distance
            
            # Calculate desired orientation
            desired_yaw = math.atan2(direction[1], direction[0])
            desired_pitch = math.asin(direction[2] / distance) if distance > 0 else 0
            
            # Smooth orientation changes
            yaw_diff = desired_yaw - self.yaw
            pitch_diff = desired_pitch - self.pitch
            
            # Normalize yaw difference
            while yaw_diff > math.pi:
                yaw_diff -= 2 * math.pi
            while yaw_diff < -math.pi:
                yaw_diff += 2 * math.pi
            
            # Apply control inputs
            control_input = {
                "thrust": 0.8,  # Moderate thrust
                "yaw": np.clip(yaw_diff * 2.0, -1.0, 1.0),
                "pitch": np.clip(pitch_diff * 2.0, -1.0, 1.0),
                "roll": 0.0
            }
            
            self.update(dt, control_input)
        else:
            # Arrived at target
            self.land()
    
    def land(self):
        """Land the fly"""
        self.is_flying = False
        self.is_landed = True
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.flight_mode = "landed"
        print("Fly has landed")
    
    def take_off(self):
        """Take off from current position"""
        self.is_flying = True
        self.is_landed = False
        self.velocity = np.array([0.0, 0.0, 5.0])  # Initial upward velocity
        self.flight_mode = "free"
        print("Fly has taken off")
    
    def eat(self, amount: float = 10.0):
        """Eat food (increases energy)"""
        if self.is_landed:
            self.is_eating = True
            self.energy = min(100.0, self.energy + amount)
            print(f"Fly ate {amount} units of food. Energy: {self.energy:.1f}")
            self.is_eating = False
        else:
            print("Fly must land to eat")
    
    def get_state(self) -> dict:
        """Get current fly state"""
        return {
            "position": self.position.tolist(),
            "velocity": self.velocity.tolist(),
            "speed": float(np.linalg.norm(self.velocity)),
            "orientation": {
                "yaw": self.yaw,
                "pitch": self.pitch,
                "roll": self.roll
            },
            "energy": self.energy,
            "is_flying": self.is_flying,
            "is_landed": self.is_landed,
            "is_eating": self.is_eating,
            "flight_mode": self.flight_mode,
            "wing_beat_phase": self.wing_beat_phase
        }
    
    def reset(self, position: Tuple[float, float, float] = (50.0, 50.0, 25.0)):
        """Reset fly to initial state"""
        self.position = np.array(position, dtype=float)
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=float)
        self.acceleration = np.array([0.0, 0.0, 0.0], dtype=float)
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.energy = 100.0
        self.is_flying = True
        self.is_landed = False
        self.is_eating = False
        self.flight_mode = "free"
        self.target_position = None
        print("Fly reset to initial state")


if __name__ == "__main__":
    # Test the fly character
    print("Testing Fly Character...")
    
    fly = FlyCharacter(start_position=(50.0, 50.0, 25.0))
    
    # Test basic flight
    print("\nTesting basic flight...")
    for i in range(10):
        control_input = {
            "thrust": 0.5,
            "yaw": 0.1,
            "pitch": 0.0,
            "roll": 0.0
        }
        fly.update(0.1, control_input)
        state = fly.get_state()
        print(f"Step {i}: Position {state['position']}, Speed {state['speed']:.2f}")
    
    # Test navigation
    print("\nTesting navigation to target...")
    target = np.array([70.0, 70.0, 30.0])
    for i in range(20):
        fly.navigate_to(target, 0.1)
        state = fly.get_state()
        print(f"Step {i}: Distance to target: {np.linalg.norm(target - fly.position):.2f}")
        
        if np.linalg.norm(target - fly.position) < 1.0:
            break
    
    # Test landing and eating
    print("\nTesting landing and eating...")
    fly.land()
    fly.eat(20.0)
    
    print(f"\nFinal fly state: {fly.get_state()}")
    print("Fly character test completed!")