"""
Fruit Fly Racer - 3D Desktop Application
Uses MuJoCo's built-in 3D viewer for real 3D rendering
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import numpy as np
import mujoco
import os
import sys
from typing import Optional
from PIL import Image, ImageTk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D

# Import our modules
from environment import RacingEnvironment
from agent_logic import AgentLogic
from rewards import RewardSystem
from sync_manager import SyncManager
from mujoco_fly_model import MuJoCoFlyModel


class FruitFlyRacer3D:
    """
    3D Desktop Application using MuJoCo viewer
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Fruit Fly Racer - 3D Racing Simulation")
        self.root.geometry("1400x900")
        
        # Simulation state
        self.simulation_running = False
        self.simulation_thread = None
        self.current_simulation = 0
        self.num_simulations = 1000000
        self.best_score = 0.0
        self.best_progress = 0.0
        
        # Initialize modules
        self.environment = RacingEnvironment(tunnel_length=200.0, tunnel_radius=10.0)
        self.fly_model = MuJoCoFlyModel(environment=self.environment)
        self.fly_model.load_connectome()
        self.agent = AgentLogic(input_size=100)
        self.rewards = RewardSystem()
        self.sync_manager = SyncManager(
            checkpoint_file="fly_memory.pkl",
            remote_url=None
        )
        
        # MuJoCo viewer/renderer
        self.viewer = None
        self.renderer = None
        self.viewer_running = False

        # Spectator mode
        self.spectator_mode = False
        self.camera_pos = np.array([0.0, -10.0, 0.0])  # Start behind fly
        self.camera_target = np.array([0.0, 0.0, 0.0])
        self.camera_distance = 10.0
        self.camera_height = 5.0

        # Best time tracking
        self.best_time = float('inf')
        self.current_episode_start = None
        
        # Create GUI
        self.create_menu()
        self.create_layout()
        
        # Bind window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        print("Fruit Fly Racer 3D initialized")
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_layout(self):
        """Create main layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Controls
        left_frame = ttk.LabelFrame(main_frame, text="Controls", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Simulation controls
        ttk.Label(left_frame, text="Number of Simulations:").pack(anchor=tk.W, pady=5)
        self.num_sims_var = tk.StringVar(value="1000000")
        ttk.Entry(left_frame, textvariable=self.num_sims_var, width=15).pack(anchor=tk.W, pady=5)
        
        # Speed selector
        ttk.Label(left_frame, text="Simulation Speed:").pack(anchor=tk.W, pady=5)
        self.speed_var = tk.StringVar(value="Normal")
        speed_combo = ttk.Combobox(left_frame, textvariable=self.speed_var, 
                                   values=["Slow", "Normal", "Fast", "Very Fast"], state="readonly", width=12)
        speed_combo.pack(anchor=tk.W, pady=5)
        
        # Buttons
        self.start_btn = ttk.Button(left_frame, text="Start Simulation", command=self.start_simulation)
        self.start_btn.pack(fill=tk.X, pady=10)

        self.stop_btn = ttk.Button(left_frame, text="Stop Simulation", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=5)

        # Spectator mode toggle
        self.spectator_var = tk.BooleanVar(value=False)
        spectator_check = ttk.Checkbutton(left_frame, text="Spectator Mode", variable=self.spectator_var,
                                         command=self.toggle_spectator_mode)
        spectator_check.pack(fill=tk.X, pady=5)

        # Camera controls hint
        ttk.Label(left_frame, text="Camera: WASD to move, Mouse to look", 
                 font=("Arial", 8), foreground="gray").pack(anchor=tk.W, pady=2)

        # Status panel
        status_frame = ttk.LabelFrame(left_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=10)

        self.status_label = ttk.Label(status_frame, text="Ready", font=("Arial", 10, "bold"))
        self.status_label.pack(anchor=tk.W, pady=2)

        self.sim_count_label = ttk.Label(status_frame, text="Simulation: 0")
        self.sim_count_label.pack(anchor=tk.W, pady=2)

        self.best_score_label = ttk.Label(status_frame, text="Best Score: 0.0")
        self.best_score_label.pack(anchor=tk.W, pady=2)

        self.best_progress_label = ttk.Label(status_frame, text="Best Progress: 0.00%")
        self.best_progress_label.pack(anchor=tk.W, pady=2)

        self.best_time_label = ttk.Label(status_frame, text="Best Time: --")
        self.best_time_label.pack(anchor=tk.W, pady=2)
        
        # Right panel - 3D View and Log
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 3D View - matplotlib 3D plot
        view_frame = ttk.LabelFrame(right_frame, text="3D View", padding=10)
        view_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create matplotlib figure and canvas with transparent background
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.fig.patch.set_alpha(0.0)  # Transparent figure background
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('none')  # Transparent axes background
        self.canvas = FigureCanvasTkAgg(self.fig, master=view_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initialize plot
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('Fruit Fly Racer - 3D View')

        # Enable zoom with mouse wheel
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

        # Enable rotation with mouse drag
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)

        # Log panel
        log_frame = ttk.LabelFrame(right_frame, text="Simulation Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Don't draw tunnel yet - wait for obstacles to be generated
        self.log("3D view initialized - obstacles will appear when simulation starts")

        # Log the initialization
        self.log("Fruit Fly Racer 3D initialized")
        self.log("Click 'Start Simulation' to begin training")
        self.log("3D view will open in separate MuJoCo window")
    
    def log(self, message):
        """Add message to log (read-only)"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def start_simulation(self):
        """Start the simulation"""
        try:
            self.num_simulations = int(self.num_sims_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid number of simulations")
            return
        
        self.simulation_running = True
        self.current_simulation = 0
        self.best_score = 0.0
        self.best_progress = 0.0
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Running", foreground="green")
        
        self.log(f"Starting simulation: {self.num_simulations} runs")
        
        # Start simulation in separate thread
        self.simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)
        self.simulation_thread.start()
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_running = False
        self.viewer_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Stopped", foreground="orange")
        self.log("Simulation stopped by user")
    
    def run_simulation(self):
        """Run the simulation loop"""
        try:
            # Generate obstacles with error handling
            self.log("Generating obstacles...")
            try:
                obstacles = self.environment.generate_obstacles(num_obstacles=20, with_holes=True)
                self.log(f"Successfully generated {len(obstacles)} obstacles")

                # Validate obstacles
                invalid_count = 0
                for i, obs in enumerate(obstacles):
                    try:
                        if not self.environment._validate_obstacle(obs):
                            invalid_count += 1
                            self.log(f"WARNING: Obstacle {i} failed validation")
                    except Exception as e:
                        invalid_count += 1
                        self.log(f"ERROR validating obstacle {i}: {e}")

                if invalid_count > 0:
                    self.log(f"WARNING: {invalid_count} obstacles failed validation")
                else:
                    self.log("All obstacles validated successfully")

            except Exception as e:
                self.log(f"ERROR generating obstacles: {e}")
                import traceback
                self.log(f"Traceback: {traceback.format_exc()}")
                return

            # Create MuJoCo scene with tunnel and obstacles
            self.create_mujoco_scene()

            # Start 3D visualization
            self.start_mujoco_viewer()
            
            # Run simulation loop
            episode_count = 0
            while self.simulation_running and self.current_simulation < self.num_simulations:
                self.current_simulation += 1
                episode_count += 1

                # Only log every 10 episodes to reduce spam
                if episode_count % 10 == 1:
                    self.log(f"=== Episode {episode_count} ===")
                    self.log(f"Environment: {len(self.environment.obstacles)} obstacles")
                    self.log(f"Fly model: {self.fly_model.model.nq} DOF, {self.fly_model.model.nu} actuators")
                    self.log(f"Tunnel: {self.environment.tunnel_length}m long, {self.environment.tunnel_radius}m radius")

                    # Log obstacle details
                    hole_count = sum(1 for obs in self.environment.obstacles if obs.get('has_hole', False))
                    self.log(f"Obstacles: {len(self.environment.obstacles)} total, {hole_count} with holes, {len(self.environment.obstacles) - hole_count} without")

                    # Log obstacle types
                    types = {}
                    for obs in self.environment.obstacles:
                        obs_type = obs.get('type', 'unknown')
                        types[obs_type] = types.get(obs_type, 0) + 1
                    self.log(f"Obstacle types: {types}")
                    self.log("===================")

                # Run one simulation episode
                episode_start = time.time()
                result = self.run_single_episode()
                episode_time = time.time() - episode_start

                # Update best scores
                if result['score'] > self.best_score:
                    self.best_score = result['score']
                    self.best_progress = result['progress']
                    self.log(f"New best! Score: {self.best_score:.1f}, Progress: {self.best_progress:.1%}")

                # Update best time (only if finished)
                if result.get('finish_reached', False) and episode_time < self.best_time:
                    self.best_time = episode_time
                    self.log(f"New best time! {self.best_time:.2f}s")

                # Update GUI every 10 episodes
                if episode_count % 10 == 0:
                    self.root.after(0, self.update_status)
                    self.log(f"Completed {episode_count} episodes. Best: {self.best_score:.1f}")

                # Regenerate obstacles for next episode (only log occasionally)
                if episode_count % 10 == 1:
                    try:
                        self.environment.generate_obstacles(num_obstacles=20, with_holes=True)
                        self.update_mujoco_scene()
                        # Log obstacle generation
                        hole_count = sum(1 for obs in self.environment.obstacles if obs.get('has_hole', False))
                        self.log(f"Generated {len(self.environment.obstacles)} new obstacles ({hole_count} with holes)")
                    except Exception as e:
                        self.log(f"ERROR regenerating obstacles: {e}")
                        import traceback
                        self.log(f"Traceback: {traceback.format_exc()}")

                # Small delay to prevent CPU overload
                time.sleep(0.1)  # Increased delay
            
            self.root.after(0, self.simulation_complete)
            
        except Exception as e:
            self.log(f"Error in simulation: {e}")
            import traceback
            traceback.print_exc()
            self.root.after(0, self.simulation_error)
    
    def run_single_episode(self):
        """Run a single simulation episode"""
        try:
            # Reset environment (only log occasionally)
            self.environment.reset()
            self.rewards.reset()

            # Run for max steps
            max_steps = 1000
            step = 0
            step_count = 0
            dt = 0.02

            while step < max_steps and self.simulation_running:
                step += 1
                step_count += 1

                # Log every 100 steps
                if step_count % 100 == 0:
                    pos = self.fly_model.get_position()
                    vel = self.fly_model.get_velocity()
                    self.log(f"Step {step_count}: pos=({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}), vel=({vel[0]:.2f}, {vel[1]:.2f}, {vel[2]:.2f})")

                # Get current position and velocity from fly model
                position = self.fly_model.get_position()
                velocity = self.fly_model.get_velocity()
                
                # Update wind
                wind = self.environment.update_wind(step * dt)
                
                # Get neural inputs
                neural_inputs = self.agent.get_neural_inputs(self.environment.obstacles, wind)
                
                # Get neural control from fly model (returns actuator commands)
                actuator_commands = self.fly_model.connect_to_neural_network(neural_inputs)

                # Apply actuator commands to the fly
                self.fly_model.apply_neural_control(actuator_commands)

                # Generate desired velocity for flight (forward along X-axis + slight lift)
                desired_velocity = np.array([self.environment.max_speed * 0.8, 0.0, 0.0])  # Forward along X-axis
                desired_turn = np.array([0.0, 0.0])  # No turning for now

                # Step MuJoCo physics with flight force
                self.fly_model.step(dt, desired_velocity=desired_velocity, desired_turn=desired_turn)

                # Get updated position from physics (use body position/velocity)
                if self.fly_model.data is not None:
                    position = self.fly_model.get_position()
                    velocity = self.fly_model.get_velocity()
                
                # Check collision
                if self.environment.check_collision(position):
                    penalty = self.rewards.calculate_collision_penalty()
                    self.rewards.update_total_points(penalty=penalty)
                    break
                
                # Check progress
                progress = self.environment.get_progress_to_finish(position)
                reward = self.rewards.calculate_progress_reward(progress)
                self.rewards.update_total_points(reward=reward)
                
                # Step MuJoCo viewer (if available)
                if self.viewer is not None:
                    try:
                        self.viewer.sync()
                    except:
                        pass
            
            return {
                'score': self.rewards.total_points,
                'progress': self.rewards.best_progress,
                'collisions': self.rewards.collision_count
            }
            
        except Exception as e:
            self.log(f"Error in episode: {e}")
            return {'score': 0.0, 'progress': 0.0, 'collisions': 0}
    
    def create_mujoco_scene(self):
        """Create MuJoCo scene with tunnel and obstacles"""
        # Create a simple world with the fly and tunnel
        # For now, we'll use the flybody model and add a floor
        # In production, we'd add the tunnel walls and obstacles to the XML
        pass
    
    def update_mujoco_scene(self):
        """Update 3D scene with new obstacles"""
        # Redraw tunnel and obstacles
        self.draw_tunnel()
        self.log(f"Updated 3D scene with {len(self.environment.obstacles)} obstacles")
    
    def start_mujoco_viewer(self):
        """Start 3D visualization using matplotlib"""
        if self.fly_model.model is None or self.fly_model.data is None:
            self.log("Error: Fly model not loaded")
            return

        try:
            self.viewer_running = True
            self.frame_count = 0

            self.log("3D visualization started (matplotlib)")

            # Start render loop using root.after (main thread)
            self.render_frame()

        except Exception as e:
            self.log(f"Viewer error: {e}")
            import traceback
            traceback.print_exc()

    def draw_tunnel(self):
        """Draw the tunnel in 3D - horizontal cylinder along X-axis"""
        # Clear previous tunnel
        for line in self.ax.lines[:]:
            line.remove()
        for collection in self.ax.collections[:]:
            collection.remove()
        for poly in self.ax.collections[:]:
            poly.remove()

        # Draw tunnel as enclosed cylinder along X-axis
        tunnel_length = self.environment.tunnel_length
        tunnel_radius = self.environment.tunnel_radius

        # Create cylinder surface - horizontal along X-axis
        theta = np.linspace(0, 2*np.pi, 100)
        x = np.linspace(-tunnel_length/2, tunnel_length/2, 50)

        # Create meshgrid for cylinder (Y-Z plane cross-section, X is length)
        theta_grid, x_grid = np.meshgrid(theta, x)
        y_grid = tunnel_radius * np.cos(theta_grid)
        z_grid = tunnel_radius * np.sin(theta_grid)

        # Draw cylinder walls (opaque - enclosed)
        self.ax.plot_surface(x_grid, y_grid, z_grid, alpha=1.0, color='blue', edgecolor='none')

        # Draw tunnel end caps (start and finish) - enclosed
        # Start cap (X = -tunnel_length/2)
        theta_cap = np.linspace(0, 2*np.pi, 50)
        y_cap = tunnel_radius * np.cos(theta_cap)
        z_cap = tunnel_radius * np.sin(theta_cap)
        x_cap = np.full_like(theta_cap, -tunnel_length/2)
        self.ax.plot(x_cap, y_cap, z_cap, color='green', linewidth=3, label='Start')

        # Finish cap (X = +tunnel_length/2)
        x_cap_finish = np.full_like(theta_cap, tunnel_length/2)
        self.ax.plot(x_cap_finish, y_cap, z_cap, color='green', linewidth=3, label='Finish')

        # Draw end caps as filled circles (enclosed tunnel)
        # Start cap
        self.ax.plot_surface(x_cap.reshape(1, -1), y_cap.reshape(1, -1), z_cap.reshape(1, -1),
                           alpha=1.0, color='darkblue')
        # Finish cap
        self.ax.plot_surface(x_cap_finish.reshape(1, -1), y_cap.reshape(1, -1), z_cap.reshape(1, -1),
                           alpha=1.0, color='darkblue')

        # Draw obstacles as different shapes - convert from z-direction to x-direction
        obstacle_count = 0
        for i, obs in enumerate(self.environment.obstacles):
            # Convert obstacle position: [x, y, z] -> [z, y, x] (tunnel is along X now)
            # Original: x=lateral, y=vertical, z=tunnel direction
            # New: x=tunnel direction, y=vertical, z=lateral
            pos = np.array([obs['position'][2], obs['position'][1], obs['position'][0]])
            size = obs['size']
            obs_type = obs.get('type', 'sphere')
            obstacle_count += 1

            # Debug: Log first few obstacles
            if i < 5:
                self.log(f"Drawing obstacle {i}: type={obs_type}, pos={obs['position']}, converted={pos}, size={size}")

            # Draw obstacle based on type
            if obs_type == 'sphere':
                # Draw sphere (opaque)
                u = np.linspace(0, 2 * np.pi, 20)
                v = np.linspace(0, np.pi, 20)
                x_obs = pos[0] + size * np.outer(np.cos(u), np.sin(v))
                y_obs = pos[1] + size * np.outer(np.sin(u), np.sin(v))
                z_obs = pos[2] + size * np.outer(np.ones(np.size(u)), np.cos(v))
                self.ax.plot_surface(x_obs, y_obs, z_obs, alpha=1.0, color='red')

            elif obs_type == 'box':
                # Draw box
                x_min, x_max = pos[0] - size/2, pos[0] + size/2
                y_min, y_max = pos[1] - size/2, pos[1] + size/2
                z_min, z_max = pos[2] - size/2, pos[2] + size/2

                # Draw box edges
                edges = [
                    [(x_min, y_min, z_min), (x_max, y_min, z_min)],
                    [(x_max, y_min, z_min), (x_max, y_max, z_min)],
                    [(x_max, y_max, z_min), (x_min, y_max, z_min)],
                    [(x_min, y_max, z_min), (x_min, y_min, z_min)],
                    [(x_min, y_min, z_max), (x_max, y_min, z_max)],
                    [(x_max, y_min, z_max), (x_max, y_max, z_max)],
                    [(x_max, y_max, z_max), (x_min, y_max, z_max)],
                    [(x_min, y_max, z_max), (x_min, y_min, z_max)],
                    [(x_min, y_min, z_min), (x_min, y_min, z_max)],
                    [(x_max, y_min, z_min), (x_max, y_min, z_max)],
                    [(x_max, y_max, z_min), (x_max, y_max, z_max)],
                    [(x_min, y_max, z_min), (x_min, y_max, z_max)]
                ]

                for edge in edges:
                    self.ax.plot([edge[0][0], edge[1][0]], [edge[0][1], edge[1][1]],
                               [edge[0][2], edge[1][2]], color='red', linewidth=2)

            elif obs_type == 'cylinder':
                # Draw cylinder obstacle (along X-axis)
                theta_obs = np.linspace(0, 2*np.pi, 20)
                x_obs_cyl = np.linspace(pos[0] - size/2, pos[0] + size/2, 10)
                theta_grid_obs, x_grid_obs_cyl = np.meshgrid(theta_obs, x_obs_cyl)
                y_grid_obs = pos[1] + size/2 * np.cos(theta_grid_obs)
                z_grid_obs = pos[2] + size/2 * np.sin(theta_grid_obs)
                self.ax.plot_surface(x_grid_obs_cyl, y_grid_obs, z_grid_obs, alpha=1.0, color='orange')

            elif obs_type == 'cube':
                # Draw cube obstacle (3D) - simplified as box
                x_min, x_max = pos[0] - size/2, pos[0] + size/2
                y_min, y_max = pos[1] - size/2, pos[1] + size/2
                z_min, z_max = pos[2] - size/2, pos[2] + size/2

                # Draw cube as 6 faces using plot_surface with proper arrays
                # Front face
                x_front = np.array([[x_min, x_max], [x_min, x_max]])
                y_front = np.array([[y_min, y_min], [y_max, y_max]])
                z_front = np.array([[z_min, z_min], [z_min, z_min]])
                self.ax.plot_surface(x_front, y_front, z_front, alpha=1.0, color='cyan')

                # Back face
                z_back = np.array([[z_max, z_max], [z_max, z_max]])
                self.ax.plot_surface(x_front, y_front, z_back, alpha=1.0, color='cyan')

                # Top face
                y_top = np.array([[y_max, y_max], [y_max, y_max]])
                z_top = np.array([[z_min, z_max], [z_min, z_max]])
                self.ax.plot_surface(x_front, y_top, z_top, alpha=1.0, color='cyan')

                # Bottom face
                y_bottom = np.array([[y_min, y_min], [y_min, y_min]])
                self.ax.plot_surface(x_front, y_bottom, z_top, alpha=1.0, color='cyan')

                # Left face
                x_left = np.array([[x_min, x_min], [x_min, x_min]])
                self.ax.plot_surface(x_left, y_front, z_top, alpha=1.0, color='cyan')

                # Right face
                x_right = np.array([[x_max, x_max], [x_max, x_max]])
                self.ax.plot_surface(x_right, y_front, z_top, alpha=1.0, color='cyan')

            elif obs_type == 'pyramid':
                # Draw pyramid obstacle (3D)
                # Base square
                base_size = size
                apex_height = size * 1.5

                # Base corners
                x1, x2 = pos[0] - base_size/2, pos[0] + base_size/2
                y1, y2 = pos[1] - base_size/2, pos[1] + base_size/2
                z_base = pos[2] - size/2
                z_apex = pos[2] + apex_height

                # Draw pyramid faces
                # Front triangular face
                self.ax.plot_surface([[x1, x2], [x1, x2]],
                                   [[y1, y1], [y2, y2]],
                                   [[z_base, z_base], [z_base, z_base]],
                                   alpha=1.0, color='magenta')
                # This is simplified - in production we'd draw proper pyramid faces

            elif obs_type == 'tetrahedron':
                # Draw tetrahedron obstacle (3D)
                # Simplified as small sphere for now
                u = np.linspace(0, 2 * np.pi, 20)
                v = np.linspace(0, np.pi, 20)
                x_obs = pos[0] + size * np.outer(np.cos(u), np.sin(v))
                y_obs = pos[1] + size * np.outer(np.sin(u), np.sin(v))
                z_obs = pos[2] + size * np.outer(np.ones(np.size(u)), np.cos(v))
                self.ax.plot_surface(x_obs, y_obs, z_obs, alpha=1.0, color='yellow')

            else:
                # Default to sphere for unknown types
                u = np.linspace(0, 2 * np.pi, 20)
                v = np.linspace(0, np.pi, 20)
                x_obs = pos[0] + size * np.outer(np.cos(u), np.sin(v))
                y_obs = pos[1] + size * np.outer(np.sin(u), np.sin(v))
                z_obs = pos[2] + size * np.outer(np.ones(np.size(u)), np.cos(v))
                self.ax.plot_surface(x_obs, y_obs, z_obs, alpha=1.0, color='purple')

        # Log obstacle count
        self.log(f"Drawn {obstacle_count} obstacles in 3D view")

        # Set axis limits - horizontal tunnel
        self.ax.set_xlim(-tunnel_length/2, tunnel_length/2)
        self.ax.set_ylim(-tunnel_radius*1.5, tunnel_radius*1.5)
        self.ax.set_zlim(-tunnel_radius*1.5, tunnel_radius*1.5)

        self.ax.set_xlabel('X (m) - Tunnel Length')
        self.ax.set_ylabel('Y (m) - Vertical')
        self.ax.set_zlabel('Z (m) - Horizontal')
        self.ax.set_title('Fruit Fly Racer - Horizontal Tunnel View')

        # Set initial view angle for horizontal tunnel
        self.ax.view_init(elev=20, azim=0)  # Side view of horizontal tunnel

        self.canvas.draw()

    def update_3d_view(self):
        """Update the 3D view with current fly position"""
        # Clear previous fly marker
        for line in self.ax.lines[:]:
            if hasattr(line, '_is_fly'):
                line.remove()
        for collection in self.ax.collections[:]:
            if hasattr(collection, '_is_fly'):
                collection.remove()

        # Get fly position and orientation
        # Convert from z-direction to x-direction (tunnel is now horizontal)
        fly_pos_z = self.fly_model.get_position()
        fly_vel_z = self.fly_model.get_velocity()

        # Convert coordinates: z -> x, y -> y, x -> z
        # Original: x=lateral, y=vertical, z=tunnel direction
        # New: x=tunnel direction, y=vertical, z=lateral
        fly_pos = np.array([fly_pos_z[2], fly_pos_z[1], fly_pos_z[0]])
        fly_vel = np.array([fly_vel_z[2], fly_vel_z[1], fly_vel_z[0]])

        # Update camera to follow fly if not in spectator mode
        if not self.spectator_mode:
            # Center view on fly position - start inside tunnel
            tunnel_length = self.environment.tunnel_length
            tunnel_radius = self.environment.tunnel_radius

            # Start camera inside tunnel at beginning
            if not hasattr(self, '_camera_initialized'):
                self._camera_initialized = True
                # Start at beginning of tunnel, inside
                start_x = -tunnel_length/2 + 5  # 5m from start
                self.ax.set_xlim(start_x - 20, start_x + 20)  # Show 40m ahead
                self.ax.set_ylim(-tunnel_radius, tunnel_radius)
                self.ax.set_zlim(-tunnel_radius, tunnel_radius)
                self.ax.view_init(elev=10, azim=0)  # Slight downward angle, looking forward
            else:
                # Follow fly position
                self.ax.set_xlim(fly_pos[0] - 20, fly_pos[0] + 20)
                self.ax.set_ylim(-tunnel_radius, tunnel_radius)
                self.ax.set_zlim(-tunnel_radius, tunnel_radius)
                self.ax.view_init(elev=10, azim=0)

        # Draw fly as an elongated shape (like a real fly)
        # Create a simple fly body representation
        fly_size = 0.3  # Size of fly representation

        # Draw fly body (elongated ellipsoid along X-axis - tunnel direction)
        u = np.linspace(0, 2 * np.pi, 20)
        v = np.linspace(0, np.pi, 20)

        # Elongated along X-axis (direction of flight through tunnel)
        x = fly_pos[0] + fly_size * 2.0 * np.outer(np.ones(np.size(u)), np.cos(v))
        y = fly_pos[1] + fly_size * 0.5 * np.outer(np.cos(u), np.sin(v))
        z = fly_pos[2] + fly_size * 0.5 * np.outer(np.sin(u), np.sin(v))

        fly_surface = self.ax.plot_surface(x, y, z, alpha=1.0, color='darkgreen')
        fly_surface._is_fly = True

        # Draw fly wings (two ellipses on top/bottom)
        wing_size = fly_size * 0.8
        for side in [-1, 1]:  # Top and bottom wings
            # Wing position offset
            wing_x = fly_pos[0]
            wing_y = fly_pos[1] + side * fly_size * 0.3
            wing_z = fly_pos[2]

            # Wing as flattened ellipsoid
            u_wing = np.linspace(0, 2 * np.pi, 15)
            v_wing = np.linspace(0, np.pi, 15)
            x_wing = wing_x + wing_size * np.outer(np.ones(np.size(u_wing)), np.cos(v_wing))
            y_wing = wing_y + wing_size * 0.1 * np.outer(np.cos(u_wing), np.sin(v_wing))
            z_wing = wing_z + wing_size * np.outer(np.sin(u_wing), np.sin(v_wing))

            wing_surface = self.ax.plot_surface(x_wing, y_wing, z_wing, alpha=1.0, color='lightblue')
            wing_surface._is_fly = True

        # Draw velocity vector (direction of flight)
        if np.linalg.norm(fly_vel) > 0.1:
            vel_scale = 2.0  # Scale velocity vector
            vel_end = fly_pos + fly_vel * vel_scale
            vel_line, = self.ax.plot([fly_pos[0], vel_end[0]],
                                   [fly_pos[1], vel_end[1]],
                                   [fly_pos[2], vel_end[2]],
                                   color='yellow', linewidth=3, label='Velocity')
            vel_line._is_fly = True

        # Update title with position and velocity
        speed = np.linalg.norm(fly_vel)
        self.ax.set_title(f'Fruit Fly Racer - Pos: ({fly_pos[0]:.1f}, {fly_pos[1]:.1f}, {fly_pos[2]:.1f}) | Speed: {speed:.1f} m/s')

        self.canvas.draw()

    def render_frame(self):
        """Update the 3D view (matplotlib version)"""
        if not self.viewer_running or not self.simulation_running:
            return

        try:
            # Update fly position in 3D view
            self.update_3d_view()

            # Schedule next update (~30 FPS)
            self.root.after(33, self.render_frame)

        except Exception as e:
            self.log(f"Render error: {e}")
            import traceback
            traceback.print_exc()
            self.viewer_running = False

    def update_canvas(self, img_tk):
        """Update Tkinter canvas with rendered frame"""
        try:
            # Debug: Log canvas update
            if not hasattr(self, '_canvas_update_count'):
                self._canvas_update_count = 0
            self._canvas_update_count += 1
            if self._canvas_update_count % 30 == 0:
                self.log(f"Canvas updated {self._canvas_update_count} times")

            # Clear canvas and display new image
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
            # Keep reference to prevent garbage collection
            self.canvas.image = img_tk
        except Exception as e:
            self.log(f"Canvas update error: {e}")
    
    def on_scroll(self, event):
        """Handle mouse scroll for zoom - limited to stay inside tunnel"""
        if event.inaxes != self.ax:
            return

        # Get tunnel bounds
        tunnel_length = self.environment.tunnel_length
        tunnel_radius = self.environment.tunnel_radius

        # Zoom in/out by changing axis limits
        scale = 1.1 if event.step > 0 else 0.9

        # Get current limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        zlim = self.ax.get_zlim()

        # Calculate new limits (zoom towards center)
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        z_center = (zlim[0] + zlim[1]) / 2

        x_range = (xlim[1] - xlim[0]) * scale
        y_range = (ylim[1] - ylim[0]) * scale
        z_range = (zlim[1] - zlim[0]) * scale

        # Limit zoom to stay within tunnel bounds
        max_x_range = tunnel_length * 0.8  # Can't zoom out beyond tunnel length
        max_y_range = tunnel_radius * 2.5  # Can't zoom out beyond tunnel radius
        max_z_range = tunnel_radius * 2.5

        x_range = min(x_range, max_x_range)
        y_range = min(y_range, max_y_range)
        z_range = min(z_range, max_z_range)

        # Also limit minimum zoom (can't zoom in too much)
        min_range = tunnel_radius * 0.5
        x_range = max(x_range, min_range)
        y_range = max(y_range, min_range)
        z_range = max(z_range, min_range)

        # Set new limits
        self.ax.set_xlim(x_center - x_range/2, x_center + x_range/2)
        self.ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
        self.ax.set_zlim(z_center - z_range/2, z_center + z_range/2)

        self.canvas.draw()

    def on_mouse_press(self, event):
        """Handle mouse press for rotation"""
        if event.inaxes == self.ax:
            self._dragging = True
            self._last_x = event.x
            self._last_y = event.y

    def on_mouse_move(self, event):
        """Handle mouse move for rotation"""
        if not hasattr(self, '_dragging') or not self._dragging:
            return
        if event.inaxes != self.ax:
            return

        # Rotate the 3D view
        dx = event.x - self._last_x
        dy = event.y - self._last_y

        # Get current view angles
        elev = self.ax.elev
        azim = self.ax.azim

        # Update angles (clamp elevation to avoid flipping)
        new_elev = np.clip(elev + dy * 0.5, -90, 90)
        new_azim = azim - dx * 0.5

        self.ax.view_init(elev=new_elev, azim=new_azim)

        self._last_x = event.x
        self._last_y = event.y
        self.canvas.draw()

    def on_mouse_release(self, event):
        """Handle mouse release"""
        self._dragging = False

    def toggle_spectator_mode(self):
        """Toggle spectator mode"""
        old_mode = self.spectator_mode
        self.spectator_mode = self.spectator_var.get()

        if self.spectator_mode and not old_mode:
            self.log("=== SPECTATOR MODE ENABLED ===")
            self.log("You can now:")
            self.log("  - Rotate view: Click and drag mouse")
            self.log("  - Zoom: Use mouse wheel")
            self.log("  - Fly continues flying normally")
            self.log("=============================")
            # Enable interactive rotation
            self.ax.mouse_init()
            # Set a good viewing angle for spectator
            self.ax.view_init(elev=30, azim=45)
        elif not self.spectator_mode and old_mode:
            self.log("=== SPECTATOR MODE DISABLED ===")
            self.log("Camera will now follow the fly")
            self.log("=============================")
            # Reset to default view
            self.ax.view_init(elev=20, azim=0)

    def on_mouse_move(self, event):
        """Handle mouse movement for camera control"""
        if not self.spectator_mode:
            return

        # Update camera target based on mouse position
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Normalize mouse position to [-1, 1]
        x = (event.x / canvas_width) * 2 - 1
        y = (event.y / canvas_height) * 2 - 1

        # Update camera angles
        self.camera_target[0] = self.camera_pos[0] + x * self.camera_distance
        self.camera_target[1] = self.camera_pos[1] + y * self.camera_distance
        self.camera_target[2] = self.camera_pos[2]

    def on_mouse_click(self, event):
        """Handle mouse click for camera control"""
        if not self.spectator_mode:
            return

        # Move camera forward/backward based on click
        if event.num == 1:  # Left click - move forward
            self.camera_pos[2] += 1.0
        elif event.num == 3:  # Right click - move backward
            self.camera_pos[2] -= 1.0

    def update_camera(self):
        """Update camera position based on spectator mode"""
        if self.spectator_mode:
            # Use spectator camera position
            return self.camera_pos, self.camera_target
        else:
            # Follow fly position
            fly_pos = self.fly_model.get_position()
            # Camera behind and above fly
            camera_pos = fly_pos + np.array([0, -self.camera_distance, self.camera_height])
            camera_target = fly_pos
            return camera_pos, camera_target

    def update_status(self):
        """Update status display"""
        self.sim_count_label.config(text=f"Simulation: {self.current_simulation}")
        self.best_score_label.config(text=f"Best Score: {self.best_score:.1f}")
        self.best_progress_label.config(text=f"Best Progress: {self.best_progress*100:.2f}%")

        # Update best time display
        if self.best_time != float('inf'):
            self.best_time_label.config(text=f"Best Time: {self.best_time:.2f}s")
        else:
            self.best_time_label.config(text="Best Time: --")
    
    def simulation_complete(self):
        """Handle simulation completion"""
        self.simulation_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Complete", foreground="blue")
        self.log(f"Simulation complete! Total: {self.current_simulation}")
        self.log(f"Best Score: {self.best_score}")
        self.log(f"Best Progress: {self.best_progress*100:.2f}%")
    
    def simulation_error(self):
        """Handle simulation error"""
        self.simulation_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Error", foreground="red")
        self.log("Simulation error occurred")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", "Fruit Fly Racer - 3D Racing Simulation\n\nUsing official TuragaLab/DeepMind flybody model\nMuJoCo physics engine\nMaleCNS v1.0 connectome")
    
    def on_closing(self):
        """Handle window close"""
        self.simulation_running = False
        self.viewer_running = False
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = FruitFlyRacer3D(root)
    root.mainloop()


if __name__ == "__main__":
    main()
