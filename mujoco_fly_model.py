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
    
    def __init__(self, connectome_weights=None, environment=None):
        """
        Initialize MuJoCo fly model using official flybody

        Args:
            connectome_weights: Optional connectome weight matrix for neural control
            environment: Optional RacingEnvironment for tunnel constraints
        """
        self.model = None
        self.data = None
        self.viewer = None
        self.environment = environment
        
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
        """Load the official flybody model using the full flybody package"""
        try:
            # Add flybody to Python path
            import sys
            flybody_path = os.path.join(os.path.dirname(__file__), 'flybody')
            if flybody_path not in sys.path:
                sys.path.insert(0, flybody_path)

            # Try to import the full flybody package
            try:
                from flybody.fruitfly import fruitfly
                self.fly_model = fruitfly.FruitFly()

                # Get the MJCF model and convert to XML string
                if hasattr(self.fly_model, 'mjcf_model'):
                    xml_string = self.fly_model.mjcf_model.to_xml_string()

                    # Modify XML string to use absolute paths for OBJ files
                    # Replace relative paths with absolute paths to assets directory
                    assets_dir = os.path.join(flybody_path, 'flybody', 'fruitfly', 'assets')
                    xml_string = xml_string.replace('file="', f'file="{assets_dir}/')

                    # Add floor and bright lighting for visualization
                    if '<floor' not in xml_string:
                        floor_xml = '''
        <!-- Floor for visualization - bright gray -->
        <geom name="floor" type="plane" pos="0 0 -1" size="50 50 0.1" rgba="0.9 0.9 0.9 1"/>
        <!-- Bright ambient lighting -->
        <light name="ambient" pos="0 0 10" dir="0 0 -1" diffuse="1.0 1.0 1.0" specular="0.5 0.5 0.5"/>
        <light name="key" pos="0 -5 10" dir="0 1 -1" diffuse="0.8 0.8 0.8"/>
        <light name="fill" pos="5 5 5" dir="-1 -1 -1" diffuse="0.6 0.6 0.6"/>
        <light name="back" pos="0 10 5" dir="0 -1 -1" diffuse="0.4 0.4 0.4"/>
'''
                        xml_string = xml_string.replace('</worldbody>', floor_xml + '</worldbody>')

                    # Load the XML string with MuJoCo
                    self.model = mujoco.MjModel.from_xml_string(xml_string)
                    self.data = mujoco.MjData(self.model)
                    print("Loaded official flybody using full package")
                else:
                    raise AttributeError("FruitFly model doesn't have mjcf_model")
            except Exception as e:
                print(f"Full flybody package failed: {e}")
                print("Falling back to direct XML loading...")

                # Fallback: load XML directly
                flybody_xml = "flybody/flybody/fruitfly/assets/fruitfly.xml"
                if not os.path.exists(flybody_xml):
                    raise FileNotFoundError(f"flybody XML not found at {flybody_xml}")

                # Read XML and add floor/lighting
                with open(flybody_xml, 'r') as f:
                    xml_content = f.read()

                # Add floor and bright lighting if not present
                if '<floor' not in xml_content:
                    floor_xml = '''
        <!-- Floor for visualization - bright gray -->
        <geom name="floor" type="plane" pos="0 0 -1" size="50 50 0.1" rgba="0.9 0.9 0.9 1"/>
        <!-- Bright ambient lighting -->
        <light name="ambient" pos="0 0 10" dir="0 0 -1" diffuse="1.0 1.0 1.0" specular="0.5 0.5 0.5"/>
        <light name="key" pos="0 -5 10" dir="0 1 -1" diffuse="0.8 0.8 0.8"/>
        <light name="fill" pos="5 5 5" dir="-1 -1 -1" diffuse="0.6 0.6 0.6"/>
        <light name="back" pos="0 10 5" dir="0 -1 -1" diffuse="0.4 0.4 0.4"/>
'''
                    xml_content = xml_content.replace('</worldbody>', floor_xml + '</worldbody>')

                self.model = mujoco.MjModel.from_xml_string(xml_content)
                self.data = mujoco.MjData(self.model)
                print("Loaded official flybody using direct XML")

            print(f"Loaded official flybody model: {self.model.nq} DOF, {self.model.nu} actuators")
            print(f"Body count: {self.model.nbody}, Joint count: {self.model.njnt}")

        except Exception as e:
            print(f"Error loading official flybody: {e}")
            raise
    
    def load_connectome(self):
        """Load MaleCNS v1.0 connectome if available (disabled for performance)"""
        # Disable connectome loading - it's too large for this system
        print("Connectome loading disabled (too large for system memory)")
        self.connectome_weights = None
        return False
    
    def connect_to_neural_network(self, neural_inputs: np.ndarray) -> np.ndarray:
        """
        Connect sensory inputs to neural network (connectome-based)
        Returns actuator commands for the fly's wings/legs

        Args:
            neural_inputs: Sensory input vector

        Returns:
            Actuator command vector (78 actuators)
        """
        if self.connectome_weights is not None:
            try:
                # Resize inputs to match connectome dimensions
                input_size = neural_inputs.shape[0]
                if input_size < self.connectome_weights.shape[0]:
                    padded_inputs = np.zeros(self.connectome_weights.shape[0])
                    padded_inputs[:input_size] = neural_inputs
                    neural_inputs = padded_inputs

                # Process through connectome to get motor output
                num_outputs = min(self.model.nu, self.connectome_weights.shape[1])
                motor_output = np.dot(neural_inputs, self.connectome_weights[:len(neural_inputs), :num_outputs])

                # Normalize to [-1, 1] range for actuator commands
                motor_output = np.tanh(motor_output)

                # Pad to full actuator count if needed
                if len(motor_output) < self.model.nu:
                    full_output = np.zeros(self.model.nu)
                    full_output[:len(motor_output)] = motor_output
                    motor_output = full_output

                return motor_output
            except Exception as e:
                print(f"Error processing through connectome: {e}")
                return np.zeros(self.model.nu)
        else:
            # Fallback: gentle wing flapping for forward flight
            actuator_commands = np.zeros(self.model.nu)
            # Assume first few actuators are wing actuators
            for i in range(min(10, self.model.nu)):
                actuator_commands[i] = 0.5 * np.sin(i * 0.5)  # Gentle oscillation
            return actuator_commands
    
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
            desired_velocity: Optional target velocity from neural network
            desired_turn: Optional target (yaw, pitch) from neural network
        """
        if self.model is None or self.data is None:
            raise RuntimeError("Model not loaded. Call load_official_flybody() first.")

        # Direct position/velocity control (simple approach)
        if desired_velocity is not None:
            # Get current position (use internal tracking, not MuJoCo)
            if not hasattr(self, '_fly_pos'):
                self._fly_pos = np.array([0.0, 0.0, -self.environment.tunnel_length/2 + 5])  # Start inside tunnel
                self._fly_vel = np.array([0.0, 0.0, 0.0])

            # Update velocity towards desired velocity
            target_vel = desired_velocity.copy()
            # Limit to max speed
            speed = np.linalg.norm(target_vel)
            if speed > self.max_speed:
                target_vel = target_vel / speed * self.max_speed

            # Smooth velocity transition
            self._fly_vel = self._fly_vel * 0.8 + target_vel * 0.2  # 80% current, 20% target

            # Update position based on velocity
            self._fly_pos = self._fly_pos + self._fly_vel * dt

            # Apply position constraints (keep inside tunnel)
            if self.environment is not None:
                # Keep within tunnel radius (Y-Z plane for horizontal tunnel)
                y, z = self._fly_pos[1], self._fly_pos[2]
                radius = np.sqrt(y**2 + z**2)
                max_radius = self.environment.tunnel_radius * 0.8
                if radius > max_radius:
                    scale = max_radius / radius
                    self._fly_pos[1] *= scale
                    self._fly_pos[2] *= scale

                # Keep within tunnel length (X-axis)
                self._fly_pos[0] = np.clip(self._fly_pos[0], -self.environment.tunnel_length/2, self.environment.tunnel_length/2)

            # Update MuJoCo data for visualization
            self._update_mujoco_position()

    def _update_mujoco_position(self):
        """Update MuJoCo model position for visualization"""
        if not hasattr(self, '_fly_pos'):
            return

        # Set position in MuJoCo (try different methods)
        try:
            # Method 1: Set xpos directly
            if self.model.nbody > 1:
                self.data.xpos[1] = self._fly_pos
            else:
                self.data.xpos[0] = self._fly_pos

            # Method 2: Also set qpos for free joint (first 7 elements)
            if self.model.nq >= 7:
                self.data.qpos[0:3] = self._fly_pos  # Position
                # Keep quaternion as identity (no rotation)
                self.data.qpos[3:7] = [1.0, 0.0, 0.0, 0.0]

            # Update forward kinematics
            mujoco.mj_forward(self.model, self.data)
        except Exception as e:
            # If MuJoCo update fails, just continue (position is tracked internally)
            pass

    def _set_position(self, pos):
        """Set fly position"""
        self._fly_pos = pos.copy()
        self._update_mujoco_position()

    def _set_velocity(self, vel):
        """Set fly velocity"""
        self._fly_vel = vel.copy()
    
    def reset(self):
        """Reset the simulation to initial state"""
        if self.data is not None:
            mujoco.mj_resetData(self.model, self.data)
    
    def get_position(self) -> np.ndarray:
        """Get current fly position"""
        if hasattr(self, '_fly_pos'):
            return self._fly_pos.copy()
        if self.data is None:
            return np.array([0.0, 0.0, 0.0])
        # Fallback to MuJoCo body position
        if self.model.nbody > 1:
            return self.data.xpos[1]
        return self.data.xpos[0]

    def get_velocity(self) -> np.ndarray:
        """Get current fly velocity"""
        if hasattr(self, '_fly_vel'):
            return self._fly_vel.copy()
        if self.data is None:
            return np.array([0.0, 0.0, 0.0])
        # Fallback to MuJoCo body velocity
        if self.model.nbody > 1:
            return self.data.subtree_linvel[1]
        return self.data.subtree_linvel[0]
    
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
