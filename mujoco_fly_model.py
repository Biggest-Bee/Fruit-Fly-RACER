"""
MuJoCo Fly Model - Official flybody model for MuJoCo
Uses the official TuragaLab/DeepMind fruit fly body model
"""

import mujoco
import numpy as np
import os
import sys


class MuJoCoFlyModel:
    """
    MuJoCo-based fly model using official flybody XML
    Integrated with MaleCNS v1.0 connectome for neural control
    """
    
    def __init__(self, connectome_weights=None):
        """
        Initialize MuJoCo fly model using official flybody
        
        Args:
            connectome_weights: Optional connectome weight matrix for neural control
        """
        self.model = None
        self.data = None
        self.viewer = None
        
        # Physics parameters - realistic flight constraints
        self.max_speed = 5.0              # m/s (max forward speed)
        self.max_acceleration = 10.0      # m/s² (takes 0.5s to reach max speed)
        self.max_turn_rate = 3.0          # rad/s (~172°/s, 90° turn takes ~1.5s)
        self.max_pitch_rate = 2.0         # rad/s (up/down turning speed)
        self.drag_coefficient = 0.1       # Air resistance (gradual deceleration)
        
        # Current flight state
        self.current_speed = 0.0
        self.current_acceleration = np.array([0.0, 0.0, 0.0])
        self.angular_velocity = np.array([0.0, 0.0, 0.0])  # yaw, pitch, roll
        self.orientation = np.array([0.0, 0.0, 0.0])      # yaw, pitch, roll
        
        # Connectome integration
        self.connectome_weights = connectome_weights
        self.neural_control = None
        
        # Load official flybody model
        self.load_official_flybody()
        
        print("MuJoCo Fly Model initialized with official flybody")
        print(f"Physics constraints: max_speed={self.max_speed}m/s, max_accel={self.max_acceleration}m/s²")
        print(f"Turn rate: {self.max_turn_rate} rad/s (90° turn in {np.pi/2/self.max_turn_rate:.2f}s)")
        if connectome_weights is not None:
            print(f"Connectome integration: {connectome_weights.shape} weights loaded")
    
    def load_official_flybody(self):
        """Load the official flybody MuJoCo XML model"""
        try:
            # Path to official flybody XML (from embedded flybody folder)
            flybody_xml = "flybody/flybody/fruitfly/assets/fruitfly.xml"
            
            if not os.path.exists(flybody_xml):
                raise FileNotFoundError(f"flybody XML not found at {flybody_xml}")
            
            # Load the official model
            self.model = mujoco.MjModel.from_xml_path(flybody_xml)
            self.data = mujoco.MjData(self.model)
            
            print(f"Loaded official flybody model: {self.model.nq} DOF, {self.model.nu} actuators")
            print(f"Body count: {self.model.nbody}, Joint count: {self.model.njnt}")
            
        except Exception as e:
            print(f"Error loading official flybody: {e}")
            raise
    
    def load_connectome(self):
        """Load MaleCNS v1.0 connectome if available (limited for performance)"""
        try:
            import pandas as pd
            connectome_file = "data/connectome-weights-male-cns-v1.0-minconf-0.5.feather"

            if os.path.exists(connectome_file):
                print(f"Loading connectome from {connectome_file}")
                weights_df = pd.read_feather(connectome_file)
                # Limit connectome size for performance (use first 1000 rows)
                self.connectome_weights = weights_df.values[:1000, :]
                print(f"Loaded connectome (limited): {self.connectome_weights.shape}")
                return True
            else:
                print("Connectome file not found")
                return False
        except Exception as e:
            print(f"Error loading connectome: {e}")
            return False
    
    def connect_to_neural_network(self, neural_inputs: np.ndarray) -> tuple:
        """
        Connect sensory inputs to neural network (connectome-based)
        
        Args:
            neural_inputs: Sensory input vector
            
        Returns:
            Tuple of (desired_velocity, desired_turn)
        """
        if self.connectome_weights is not None:
            # Use connectome weights for neural processing
            # Simplified: multiply inputs by connectome weights
            # In production, this would use actual spiking simulation
            try:
                # Resize inputs to match connectome dimensions
                input_size = neural_inputs.shape[0]
                if input_size < self.connectome_weights.shape[0]:
                    # Pad inputs
                    padded_inputs = np.zeros(self.connectome_weights.shape[0])
                    padded_inputs[:input_size] = neural_inputs
                    neural_inputs = padded_inputs
                
                # Process through connectome
                # Connectome has limited output dimensions, so use available columns
                num_outputs = min(5, self.connectome_weights.shape[1])
                motor_output = np.dot(neural_inputs, self.connectome_weights[:len(neural_inputs), :num_outputs])

                # Extract velocity and turn commands
                if num_outputs >= 3:
                    # Normalize motor output to reasonable range before scaling
                    motor_output = np.tanh(motor_output)  # Normalize to [-1, 1]
                    desired_velocity = motor_output[:3] * self.max_speed
                    # Ensure forward motion (positive z direction along tunnel)
                    if desired_velocity[2] < 0:
                        desired_velocity[2] = abs(desired_velocity[2])  # Flip to forward
                else:
                    desired_velocity = np.zeros(3)
                    desired_velocity[2] = 0.5 * self.max_speed  # Default forward

                if num_outputs >= 5:
                    desired_turn = np.tanh(motor_output[3:5]) * 1.0  # Normalize to [-1, 1]
                elif num_outputs >= 4:
                    desired_turn = np.array([np.tanh(motor_output[3]), 0.0])  # Only yaw available
                else:
                    desired_turn = np.array([0.0, 0.0])  # No turn control available

                return desired_velocity, desired_turn
            except Exception as e:
                print(f"Error processing through connectome: {e}")
                return np.array([0.0, 0.0, 0.5]), np.array([0.0, 0.0])
        else:
            # Fallback: move forward slowly
            return np.array([0.0, 0.0, 0.5]), np.array([0.0, 0.0])
    
    def apply_acceleration(self, desired_velocity: np.ndarray, dt: float):
        """
        Apply realistic acceleration (not instant velocity change)
        
        Args:
            desired_velocity: Target velocity vector
            dt: Time step
        """
        if self.data is None:
            return
        
        # Get current velocity
        current_vel = self.get_velocity()
        
        # Calculate acceleration needed
        accel = (desired_velocity - current_vel) / dt
        
        # Clamp acceleration (can't accelerate faster than max)
        accel_mag = np.linalg.norm(accel)
        if accel_mag > self.max_acceleration:
            accel = accel / accel_mag * self.max_acceleration
        
        # Store acceleration for telemetry
        self.current_acceleration = accel
        
        # Apply acceleration to MuJoCo velocity
        self.data.qvel[:3] += accel * dt
        
        # Clamp speed
        speed = np.linalg.norm(self.data.qvel[:3])
        if speed > self.max_speed:
            self.data.qvel[:3] = self.data.qvel[:3] / speed * self.max_speed
        
        self.current_speed = np.linalg.norm(self.data.qvel[:3])
    
    def apply_turn(self, desired_yaw: float, desired_pitch: float, dt: float):
        """
        Apply realistic turning limits (not instant direction change)
        
        Args:
            desired_yaw: Desired yaw change (radians)
            desired_pitch: Desired pitch change (radians)
            dt: Time step
        """
        # Calculate angular acceleration
        angular_accel_yaw = (desired_yaw - self.angular_velocity[0]) / dt
        angular_accel_pitch = (desired_pitch - self.angular_velocity[1]) / dt
        
        # Clamp angular velocity (gradual turning)
        self.angular_velocity[0] = np.clip(
            self.angular_velocity[0] + angular_accel_yaw * dt,
            -self.max_turn_rate, self.max_turn_rate
        )
        self.angular_velocity[1] = np.clip(
            self.angular_velocity[1] + angular_accel_pitch * dt,
            -self.max_pitch_rate, self.max_pitch_rate
        )
        
        # Bank when turning (like real aircraft)
        bank_angle = -self.angular_velocity[0] * 0.5  # Roll when yawing
        self.angular_velocity[2] = bank_angle
        
        # Update orientation
        self.orientation += self.angular_velocity * dt
        
        # Apply orientation to MuJoCo (simplified - affects actuators)
        # Real implementation would set qpos for orientation joints
        if self.model.nq > 3:
            # If there are orientation DOFs, update them
            for i in range(min(3, self.model.nq - 3)):
                self.data.qpos[3 + i] = self.orientation[i]
    
    def apply_drag(self, dt: float):
        """
        Apply air resistance (gradual deceleration)
        
        Args:
            dt: Time step
        """
        if self.data is None:
            return
        
        # Apply drag to velocity (gradual slowdown)
        drag_factor = 1.0 - (self.drag_coefficient * dt)
        self.data.qvel[:3] *= drag_factor
        self.current_speed = np.linalg.norm(self.data.qvel[:3])
    
    def step(self, dt: float = 0.02, desired_velocity=None, desired_turn=None):
        """
        Step the physics simulation forward

        Args:
            dt: Time step in seconds
            desired_velocity: Optional target velocity from neural network (ignored for now)
            desired_turn: Optional target (yaw, pitch) from neural network (ignored for now)
        """
        if self.model is None or self.data is None:
            raise RuntimeError("Model not loaded. Call load_official_flybody() first.")

        # Let MuJoCo handle physics naturally
        # The flybody model has actuators that control wing/leg movements
        # Neural network should output actuator commands, not velocity/turn

        # Step MuJoCo physics
        mujoco.mj_step(self.model, self.data)
    
    def reset(self):
        """Reset the simulation to initial state"""
        if self.data is not None:
            mujoco.mj_resetData(self.model, self.data)
    
    def get_position(self) -> np.ndarray:
        """Get current fly position"""
        if self.data is None:
            return np.array([0.0, 0.0, 0.0])
        return self.data.qpos[:3]  # First 3 DOF are usually position
    
    def get_velocity(self) -> np.ndarray:
        """Get current fly velocity"""
        if self.data is None:
            return np.array([0.0, 0.0, 0.0])
        return self.data.qvel[:3]  # First 3 velocities
    
    def apply_neural_control(self, motor_commands: np.ndarray):
        """
        Apply neural control commands to actuators
        
        Args:
            motor_commands: Motor command vector
        """
        if self.data is None:
            return
        
        # Apply motor commands to actuators
        num_actuators = min(len(motor_commands), self.model.nu)
        self.data.ctrl[:num_actuators] = motor_commands[:num_actuators]
    
    def close(self):
        """Clean up resources"""
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None


if __name__ == "__main__":
    # Test loading the official flybody
    fly = MuJoCoFlyModel()
    print("Official flybody loaded successfully!")
    print(f"Position: {fly.get_position()}")
    print(f"Velocity: {fly.get_velocity()}")
