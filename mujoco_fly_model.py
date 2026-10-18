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
        
        # Physics parameters
        self.max_speed = 5.0
        self.gravity = -9.81
        
        # Connectome integration
        self.connectome_weights = connectome_weights
        self.neural_control = None
        
        # Load official flybody model
        self.load_official_flybody()
        
        print("MuJoCo Fly Model initialized with official flybody")
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
        """Load MaleCNS v1.0 connectome if available"""
        try:
            import pandas as pd
            connectome_file = "data/connectome-weights-male-cns-v1.0-minconf-0.5.feather"
            
            if os.path.exists(connectome_file):
                print(f"Loading connectome from {connectome_file}")
                weights_df = pd.read_feather(connectome_file)
                self.connectome_weights = weights_df.values
                print(f"Loaded connectome: {self.connectome_weights.shape}")
                return True
            else:
                print("Connectome file not found")
                return False
        except Exception as e:
            print(f"Error loading connectome: {e}")
            return False
    
    def connect_to_neural_network(self, neural_inputs: np.ndarray) -> np.ndarray:
        """
        Connect sensory inputs to neural network (connectome-based)
        
        Args:
            neural_inputs: Sensory input vector
            
        Returns:
            Motor output vector
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
                motor_output = np.dot(neural_inputs, self.connectome_weights[:len(neural_inputs), :8])
                return motor_output
            except Exception as e:
                print(f"Error processing through connectome: {e}")
                return np.random.randn(8) * 0.1
        else:
            # Fallback to random output
            return np.random.randn(8) * 0.1
    
    def step(self, dt: float = 0.02):
        """
        Step the physics simulation forward
        
        Args:
            dt: Time step in seconds
        """
        if self.model is None or self.data is None:
            raise RuntimeError("Model not loaded. Call load_official_flybody() first.")
        
        mujoco.mj_step(self.model, self.data, dt)
    
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
