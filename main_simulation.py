"""
Main Simulation Runner - Fruit Fly Racer
Integrates all modules and runs the racing simulation with automatic repetition.
"""

import numpy as np
import os
import time
from typing import Dict, Optional
import sys

# Import modules
from environment import RacingEnvironment
from agent_logic import AgentLogic
from rewards import RewardSystem
from sync_manager import SyncManager
from mujoco_fly_model import MuJoCoFlyModel

# Try to import brain engine (optional)
try:
    from brain_sim.brain_engine import BrainEngine
    BRAIN_AVAILABLE = True
except ImportError:
    print("Warning: Brain engine not available, using simple neural network")
    BRAIN_AVAILABLE = False


class FruitFlyRacer:
    """
    Main simulation runner for Fruit Fly Racer
    """
    
    def __init__(self, num_simulations: int = 1000000):
        """
        Initialize the simulation runner
        
        Args:
            num_simulations: Number of simulations to run
        """
        self.num_simulations = num_simulations
        self.current_simulation = 0
        
        # Initialize modules
        print("Initializing Fruit Fly Racer...")
        
        # Environment
        self.environment = RacingEnvironment(
            tunnel_length=100.0,
            tunnel_radius=5.0
        )
        
        # MuJoCo Fly Model
        self.fly_model = MuJoCoFlyModel()
        self.fly_model.load_connectome()  # Load MaleCNS v1.0 connectome
        fly_mjcf = self.fly_model.create_fly_mjcf()
        self.fly_model.load_model(fly_mjcf)
        
        # Agent Logic
        self.agent = AgentLogic(input_size=100)
        
        # Reward System
        self.rewards = RewardSystem()
        
        # Sync Manager (neural memory)
        self.sync_manager = SyncManager(
            checkpoint_file="fly_memory.pkl",
            remote_url=None  # Can be set via environment variable
        )
        
        # Brain Engine (connectome) - optional
        if BRAIN_AVAILABLE:
            try:
                # Check if connectome files exist
                annotations_file = "data/body-annotations-male-cns-v1.0-minconf-0.5.feather"
                connectome_file = "data/connectome-weights-male-cns-v1.0-minconf-0.5.feather"
                
                if os.path.exists(annotations_file) and os.path.exists(connectome_file):
                    self.brain = BrainEngine(
                        annotations_file=annotations_file,
                        connectome_file=connectome_file,
                        enable_enhanced_regions=False,
                        max_neurons=10000  # Use larger subset for better control
                    )
                    print("Brain engine loaded from connectome with 10,000 neurons")
                else:
                    print("Connectome files not found, using simple neural network")
                    self.brain = None
            except Exception as e:
                print(f"Warning: Could not load brain engine: {e}")
                self.brain = None
        else:
            self.brain = None
        
        # Load neural memory if exists
        self.neural_weights = self.sync_manager.load_checkpoint()
        if not self.neural_weights:
            print("No neural memory found, starting fresh")
            # Initialize with random weights if no brain engine
            if not self.brain:
                self.neural_weights = {
                    'input_weights': np.random.randn(100, 200) * 0.1,
                    'hidden_weights': np.random.randn(200, 20) * 0.1,
                    'learning_history': []
                }
        else:
            print(f"Loaded neural memory with {len(self.neural_weights.get('learning_history', []))} training steps")
        
        # Simulation state
        self.simulation_running = False
        self.simulation_paused = False
        
        print("Fruit Fly Racer initialized")
    
    def run_single_simulation(self) -> Dict:
        """
        Run a single simulation through the obstacle course using MuJoCo physics
        
        Returns:
            Dictionary with simulation results
        """
        # Generate new random obstacles (map regenerates)
        self.environment.generate_obstacles(
            num_obstacles=20,
            with_holes=True
        )
        
        # Reset reward system
        self.rewards.reset()
        
        # Reset MuJoCo fly model
        self.fly_model.reset()
        
        # Initialize fly position (start of tunnel)
        # Set MuJoCo fly position
        if self.fly_model.data is not None:
            self.fly_model.data.qpos = np.array([0.0, 0.0, -self.environment.tunnel_length / 2, 0, 0, 0, 0])  # x, y, z, rotations
            self.fly_model.data.qvel = np.zeros_like(self.fly_model.data.qvel)
        
        dt = 0.02  # Time step (50 Hz)
        max_steps = int(self.environment.tunnel_length / (self.environment.max_speed * dt)) * 2
        
        # Track progress
        collision = False
        finish_reached = False
        progress_history = []
        
        for step in range(max_steps):
            if not self.simulation_running:
                break
            
            # Get current state from MuJoCo
            if self.fly_model.data is not None:
                position = self.fly_model.data.qpos[:3]  # x, y, z
                velocity = self.fly_model.data.qvel[:3]  # vx, vy, vz
            else:
                position = np.array([0.0, 0.0, -self.environment.tunnel_length / 2])
                velocity = np.array([0.0, 0.0, 0.0])
            
            # Update physics tracking
            self.agent.update_physics(position, velocity, dt)
            
            # Update wind
            wind = self.environment.update_wind(step * dt)
            
            # Get neural inputs including wind direction
            neural_inputs = self.agent.get_neural_inputs(self.environment.obstacles, wind)
            
            # Process through neural network (fly brain)
            if self.brain:
                # Use actual brain engine - step simulation
                self.brain.step()
                # Get motor output from motor neurons
                motor_output = np.random.randn(20) * 0.1  # Placeholder - need to map to actual motor neurons
            else:
                # Use simple neural network
                motor_output = self._simple_forward_pass(neural_inputs)
            
            # Get desired velocity and turn from fly model's neural control
            # The connectome decides where to fly (not keyboard presses)
            desired_velocity, desired_turn = self.fly_model.connect_to_neural_network(neural_inputs)
            
            # Step MuJoCo physics with realistic constraints
            self.fly_model.step(dt, desired_velocity=desired_velocity, desired_turn=desired_turn)
            
            # Update wind
            wind = self.environment.update_wind(step * dt)
            # Wind affects MuJoCo simulation through external forces
            
            # Get updated position
            if self.fly_model.data is not None:
                position = self.fly_model.data.qpos[:3]
                velocity = self.fly_model.data.qvel[:3]
            
            # Enforce speed limit
            velocity = self.agent.enforce_speed_limit(velocity, self.environment.max_speed)
            
            # Check collision
            if self.environment.check_collision(position):
                collision = True
                penalty = self.rewards.calculate_collision_penalty()
                self.rewards.update_total_points(penalty=penalty)
                break
            
            # Check progress
            progress = self.environment.get_progress_to_finish(position)
            progress_history.append(progress)
            
            # Reward progress
            reward = self.rewards.calculate_progress_reward(progress)
            self.rewards.update_total_points(reward=reward)
            
            # Check if finished
            if progress >= 1.0:
                finish_reached = True
                break
        
        # Final results
        results = {
            'simulation_id': self.current_simulation,
            'collision': collision,
            'finish_reached': finish_reached,
            'final_progress': self.environment.get_progress_to_finish(position),
            'total_points': self.rewards.total_points,
            'collision_count': self.rewards.collision_count,
            'steps': step + 1,
            'progress_history': progress_history,
            'position': position
        }
        
        return results
    
    def _simple_forward_pass(self, inputs: np.ndarray) -> np.ndarray:
        """
        Simple forward pass through neural network (if brain engine not available)
        
        Args:
            inputs: Neural input vector
            
        Returns:
            Motor output vector
        """
        # Input layer
        input_weights = self.neural_weights.get('input_weights', np.random.randn(100, 200) * 0.1)
        hidden = np.tanh(np.dot(inputs, input_weights))
        
        # Hidden layer
        hidden_weights = self.neural_weights.get('hidden_weights', np.random.randn(200, 20) * 0.1)
        output = np.tanh(np.dot(hidden, hidden_weights))
        
        return output
    
    def _motor_to_ctrl(self, motor_output: np.ndarray) -> np.ndarray:
        """
        Convert motor output to MuJoCo control vector
        
        Args:
            motor_output: Motor output from neural network
            
        Returns:
            MuJoCo control vector
        """
        # MuJoCo fly has 8 motors: 2 wings + 6 legs
        ctrl = np.zeros(8)
        
        # Wing motors (first 2 outputs)
        ctrl[0] = motor_output[0]  # Left wing
        ctrl[1] = motor_output[1]  # Right wing
        
        # Leg motors (next 6 outputs)
        ctrl[2:8] = motor_output[2:8]
        
        return ctrl
    
    def _motor_to_velocity(self, motor_output: np.ndarray) -> np.ndarray:
        """
        Convert motor output to velocity vector (for non-MuJoCo fallback)
        
        Args:
            motor_output: Motor output from neural network
            
        Returns:
            Velocity vector (vx, vy, vz)
        """
        # Motor output: [0-3] for x/y/z velocity, [4-6] for acceleration
        vx = motor_output[0] * self.environment.max_speed
        vy = motor_output[1] * self.environment.max_speed
        vz = motor_output[2] * self.environment.max_speed * 0.5  # Forward bias
        
        return np.array([vx, vy, vz])
    
    def update_neural_weights(self, results: Dict):
        """
        Update neural weights based on simulation results (reinforcement learning)
        
        Args:
            results: Simulation results
        """
        # Simple learning rule: adjust weights based on reward
        learning_rate = 0.001
        
        if results['total_points'] > 0:
            # If positive result, reinforce current weights
            input_weights = self.neural_weights.get('input_weights', np.random.randn(100, 200) * 0.1)
            hidden_weights = self.neural_weights.get('hidden_weights', np.random.randn(200, 20) * 0.1)
            
            # Add small random perturbation (exploration)
            input_weights += np.random.randn(*input_weights.shape) * learning_rate * results['total_points'] / 1000.0
            hidden_weights += np.random.randn(*hidden_weights.shape) * learning_rate * results['total_points'] / 1000.0
            
            self.neural_weights['input_weights'] = input_weights
            self.neural_weights['hidden_weights'] = hidden_weights
        
        # Record learning history
        if 'learning_history' not in self.neural_weights:
            self.neural_weights['learning_history'] = []
        
        self.neural_weights['learning_history'].append({
            'simulation_id': results['simulation_id'],
            'total_points': results['total_points'],
            'collision': results['collision'],
            'finish_reached': results['finish_reached'],
            'final_progress': results['final_progress']
        })
    
    def run_simulation_loop(self):
        """
        Run the full simulation loop with automatic repetition
        """
        print(f"\n{'='*60}")
        print(f"Starting Simulation Loop: {self.num_simulations} simulations")
        print(f"{'='*60}\n")
        
        self.simulation_running = True
        
        best_score = 0.0
        best_progress = 0.0
        
        for sim_id in range(self.num_simulations):
            if not self.simulation_running:
                print("\nSimulation stopped by user")
                break
            
            self.current_simulation = sim_id + 1
            
            print(f"\nSimulation {self.current_simulation}/{self.num_simulations}")
            print("-" * 40)
            
            # Run single simulation
            start_time = time.time()
            results = self.run_single_simulation()
            elapsed = time.time() - start_time
            
            # Print results
            print(f"Completed in {elapsed:.2f}s")
            print(f"Progress: {results['final_progress']:.2%}")
            print(f"Points: {results['total_points']:.1f}")
            print(f"Collisions: {results['collision_count']}")
            print(f"Finished: {'Yes' if results['finish_reached'] else 'No'}")
            
            # Track best
            if results['total_points'] > best_score:
                best_score = results['total_points']
                print(f"NEW BEST SCORE: {best_score:.1f}")
            
            if results['final_progress'] > best_progress:
                best_progress = results['final_progress']
                print(f"NEW BEST PROGRESS: {best_progress:.2%}")
            
            # Update neural weights (learn from this simulation)
            self.update_neural_weights(results)
            
            # Save checkpoint every 100 simulations
            if self.current_simulation % 100 == 0:
                self.sync_manager.save_checkpoint(self.neural_weights)
                print(f"Checkpoint saved at simulation {self.current_simulation}")
            
            # Print summary every 10 simulations
            if self.current_simulation % 10 == 0:
                print(f"\nSummary (every 10 simulations):")
                print(f"Best Score: {best_score:.1f}")
                print(f"Best Progress: {best_progress:.2%}")
                print(f"Learning History: {len(self.neural_weights.get('learning_history', []))} steps")
        
        # Final save
        self.sync_manager.save_checkpoint(self.neural_weights)
        print(f"\n{'='*60}")
        print(f"Simulation Loop Complete")
        print(f"{'='*60}")
        print(f"Total Simulations: {self.current_simulation}")
        print(f"Best Score: {best_score:.1f}")
        print(f"Best Progress: {best_progress:.2%}")
        print(f"Learning History: {len(self.neural_weights.get('learning_history', []))} steps")
        print(f"Neural memory saved to: {self.sync_manager.checkpoint_file}")
    
    def stop_simulation(self):
        """Stop the simulation loop"""
        self.simulation_running = False
        print("Stopping simulation...")


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("FRUIT FLY RACER - Racing Simulation")
    print("="*60)
    print("\nBased on MaleCNS v1.0 Fruit Fly Connectome")
    print("211,577 neurons / ~151.8M connections")
    print("\nInitializing simulation...\n")
    
    # Create racer
    racer = FruitFlyRacer(num_simulations=1000000)
    
    # Run simulation loop
    try:
        racer.run_simulation_loop()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
        racer.stop_simulation()
    except Exception as e:
        print(f"\n\nError during simulation: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nPress Enter to exit...")
    input()


if __name__ == "__main__":
    main()
