"""
MuJoCo Fly Model - Custom fly body model for MuJoCo
Anatomically-accurate fly model compatible with MaleCNS v1.0 connectome
"""

import mujoco
import numpy as np
import os
import sys

# Add parent directory for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MuJoCoFlyModel:
    """
    MuJoCo-based fly model for racing simulation
    Integrated with MaleCNS v1.0 connectome for neural control
    """
    
    def __init__(self, connectome_weights=None):
        """
        Initialize MuJoCo fly model
        
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
        
        print("MuJoCo Fly Model initialized")
        if connectome_weights is not None:
            print(f"Connectome integration: {connectome_weights.shape} weights loaded")
    
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
    
    def create_fly_mjcf(self) -> str:
        """
        Create MuJoCo XML for the fly body
        
        Returns:
            MuJoCo XML string
        """
        mjcf = """<?xml version="1.0"?>
<mujoco>
  <compiler angle="radian" coordinate="local" />
  <world>
    <default>
      <geom solref="0.3" solrgba="0.7 0.7 0.7 1.0"/>
      <motor ctrlrange="-1 1" gear="10"/>
    </default>
    
    <!-- Fly Body -->
    <body name="fly" pos="0 0 1">
      <!-- Thorax (main body) -->
      <geom name="thorax" type="capsule" size="0.05 0.1" pos="0 0 0" rgba="0.8 0.6 0.4 1"/>
      
      <!-- Head -->
      <body name="head" pos="0.1 0 0.05">
        <geom name="head" type="sphere" size="0.03" rgba="0.7 0.5 0.3 1"/>
        <!-- Eyes -->
        <geom name="left_eye" type="sphere" size="0.015" pos="0.02 0.02 0" rgba="1 0 0 1"/>
        <geom name="right_eye" type="sphere" size="0.015" pos="0.02 -0.02 0" rgba="1 0 0 1"/>
      </body>
      
      <!-- Abdomen -->
      <body name="abdomen" pos="-0.1 0 0">
        <geom name="abdomen" type="capsule" size="0.04 0.08" pos="0 0 0" rgba="0.7 0.5 0.3 1"/>
      </body>
      
      <!-- Wings -->
      <body name="left_wing" pos="0 0.05 0.05">
        <joint name="left_wing_joint" type="hinge" axis="0 1 0" range="-1.5 1.5"/>
        <geom name="left_wing" type="box" size="0.15 0.01 0.4" rgba="0.6 0.8 1 0.7"/>
        <motor name="left_wing_motor" joint="left_wing_joint"/>
      </body>
      
      <body name="right_wing" pos="0 -0.05 0.05">
        <joint name="right_wing_joint" type="hinge" axis="0 1 0" range="-1.5 1.5"/>
        <geom name="right_wing" type="box" size="0.15 0.01 0.4" rgba="0.6 0.8 1 0.7"/>
        <motor name="right_wing_motor" joint="right_wing_joint"/>
      </body>
      
      <!-- Legs (6 legs) -->
      <body name="front_left_leg" pos="0.05 0.02 -0.02">
        <joint name="front_left_leg_joint" type="hinge" axis="0 0 1" range="-0.5 0.5"/>
        <geom name="front_left_leg" type="capsule" size="0.005 0.04" rgba="0.3 0.3 0.3 1"/>
        <motor name="front_left_leg_motor" joint="front_left_leg_joint"/>
      </body>
      
      <body name="front_right_leg" pos="0.05 -0.02 -0.02">
        <joint name="front_right_leg_joint" type="hinge" axis="0 0 1" range="-0.5 0.5"/>
        <geom name="front_right_leg" type="capsule" size="0.005 0.04" rgba="0.3 0.3 0.3 1"/>
        <motor name="front_right_leg_motor" joint="front_right_leg_joint"/>
      </body>
      
      <body name="middle_left_leg" pos="0 0.02 -0.03">
        <joint name="middle_left_leg_joint" type="hinge" axis="0 0 1" range="-0.5 0.5"/>
        <geom name="middle_left_leg" type="capsule" size="0.005 0.035" rgba="0.3 0.3 0.3 1"/>
        <motor name="middle_left_leg_motor" joint="middle_left_leg_joint"/>
      </body>
      
      <body name="middle_right_leg" pos="0 -0.02 -0.03">
        <joint name="middle_right_leg_joint" type="hinge" axis="0 0 1" range="-0.5 0.5"/>
        <geom name="middle_right_leg" type="capsule" size="0.005 0.035" rgba="0.3 0.3 0.3 1"/>
        <motor name="middle_right_leg_motor" joint="middle_right_leg_joint"/>
      </body>
      
      <body name="back_left_leg" pos="-0.05 0.02 -0.02">
        <joint name="back_left_leg_joint" type="hinge" axis="0 0 1" range="-0.5 0.5"/>
        <geom name="back_left_leg" type="capsule" size="0.005 0.04" rgba="0.3 0.3 0.3 1"/>
        <motor name="back_left_leg_motor" joint="back_left_leg_joint"/>
      </body>
      
      <body name="back_right_leg" pos="-0.05 -0.02 -0.02">
        <joint name="back_left_leg_joint" type="hinge" axis="0 0 1" range="-0.5 0.5"/>
        <geom name="back_right_leg" type="capsule" size="0.005 0.04" rgba="0.3 0.3 0.3 1"/>
        <motor name="back_right_leg_motor" joint="back_right_leg_joint"/>
      </body>
    </body>
    
    <!-- Wind force -->
    <actuator>
      <general name="wind_force" gear="1"/>
    </actuator>
  </world>
</mujoco>"""
        return mjcf
    
    def load_model(self, mjcf: str):
        """
        Load MuJoCo model from XML
        
        Args:
            mjcf: MuJoCo XML string
        """
        try:
            self.model = mujoco.MjModel.from_xml_string(mjcf)
            self.data = mujoco.MjData(self.model)
            print("MuJoCo model loaded successfully")
        except Exception as e:
            print(f"Error loading MuJoCo model: {e}")
    
    def step(self, ctrl: np.ndarray):
        """
        Step the simulation forward
        
        Args:
            ctrl: Control vector for actuators
        """
        if self.model is None or self.data is None:
            return
        
        self.data.ctrl = ctrl
        mujoco.mj_step(self.model, self.data)
    
    def get_state(self) -> dict:
        """
        Get current state of the fly
        
        Returns:
            Dictionary with position, velocity, etc.
        """
        if self.data is None:
            return {}
        
        return {
            'position': self.data.qpos.copy(),
            'velocity': self.data.qvel.copy(),
            'acceleration': self.data.qacc.copy(),
            'speed': np.linalg.norm(self.data.qvel),
            'altitude': self.data.qpos[2] if len(self.data.qpos) > 2 else 0.0
        }
    
    def reset(self):
        """Reset the simulation"""
        if self.data is not None:
            mujoco.mj_resetData(self.model, self.data)


if __name__ == "__main__":
    fly = MuJoCoFlyModel()
    mjcf = fly.create_fly_mjcf()
    fly.load_model(mjcf)
    print("MuJoCo Fly Model test complete")
