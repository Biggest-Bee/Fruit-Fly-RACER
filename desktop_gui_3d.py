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
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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
        self.simulation_paused = False
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

        # Camera control state
        self._user_moved_camera = False
        self._zoom_factor = 1.0
        self._cam_offset = np.array([0.0, 0.0, 0.0])
        self._view_initialized = False
        self._keys_down = set()

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

        self.pause_btn = ttk.Button(left_frame, text="Pause Simulation", command=self.pause_simulation, state=tk.DISABLED)
        self.pause_btn.pack(fill=tk.X, pady=5)

        # Camera view mode: Chase Cam / Fly POV / Spectator
        self.camera_view = "chase"  # 'chase', 'flypov', 'spectator'
        ttk.Label(left_frame, text="Camera View:").pack(anchor=tk.W, pady=5)
        self.view_mode_var = tk.StringVar(value="Chase Cam")
        view_combo = ttk.Combobox(left_frame, textvariable=self.view_mode_var,
                                  values=["Chase Cam", "Fly POV", "Spectator"],
                                  state="readonly", width=12)
        view_combo.pack(anchor=tk.W, pady=5)
        view_combo.bind('<<ComboboxSelected>>', self.on_view_mode_change)

        # Spectator mode (synced with combobox)
        self.spectator_var = tk.BooleanVar(value=False)
        spectator_check = ttk.Checkbutton(left_frame, text="Spectator Mode", variable=self.spectator_var,
                                         command=self.toggle_spectator_mode)
        spectator_check.pack(fill=tk.X, pady=5)

        # Camera controls hint
        ttk.Label(left_frame, text="Camera: drag=rotate, wheel=zoom, WASD=move", 
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

        # WASD camera movement keys
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)

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
        self.simulation_paused = False
        self.current_simulation = 0
        self.best_score = 0.0
        self.best_progress = 0.0

        # Reset camera state
        self.camera_view = "chase"
        self.view_mode_var.set("Chase Cam")
        self._user_moved_camera = False
        self._zoom_factor = 1.0
        self._cam_offset = np.array([0.0, 0.0, 0.0])
        self._view_initialized = False
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.NORMAL, text="Pause Simulation")
        self.status_label.config(text="Running", foreground="green")
        
        self.log(f"Starting simulation: {self.num_simulations} runs")
        
        # Start simulation in separate thread
        self.simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)
        self.simulation_thread.start()
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_running = False
        self.simulation_paused = False
        self.viewer_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Stopped", foreground="orange")
        self.log("Simulation stopped by user")

    def pause_simulation(self):
        """Pause/resume the simulation - camera controls stay active while paused"""
        self.simulation_paused = not self.simulation_paused
        if self.simulation_paused:
            self.pause_btn.config(text="Resume Simulation")
            self.status_label.config(text="Paused", foreground="orange")
            self.log("=== SIMULATION PAUSED ===")
            self.log("You can now move the camera:")
            self.log("  - Drag mouse: rotate view")
            self.log("  - Scroll: zoom in/out")
            self.log("  - WASD: move camera position")
            self.log("Click 'Resume Simulation' to continue")
            self.log("=========================")
        else:
            self.pause_btn.config(text="Pause Simulation")
            self.status_label.config(text="Running", foreground="green")
            self.log("=== SIMULATION RESUMED ===")
    
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
            # Reset environment and fly model - fly returns to start line
            self.environment.reset()
            self.fly_model.reset()
            self.rewards.reset()

            # Run for max steps
            max_steps = 1000
            step = 0
            step_count = 0
            dt = 0.02
            finish_reached = False

            while step < max_steps and self.simulation_running:
                # Handle pause - wait while paused but keep GUI responsive
                while self.simulation_paused and self.simulation_running:
                    time.sleep(0.05)
                if not self.simulation_running:
                    break

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

                # Check if fly crossed the finish line - end episode and reset
                if progress >= 1.0:
                    finish_reached = True
                    self.log(f"Finish line reached! Score: {self.rewards.total_points:.1f}")
                    break

                # Step MuJoCo viewer (if available)
                if self.viewer is not None:
                    try:
                        self.viewer.sync()
                    except:
                        pass
            
            return {
                'score': self.rewards.total_points,
                'progress': self.rewards.best_progress,
                'collisions': self.rewards.collision_count,
                'finish_reached': finish_reached
            }

        except Exception as e:
            self.log(f"Error in episode: {e}")
            return {'score': 0.0, 'progress': 0.0, 'collisions': 0, 'finish_reached': False}
    
    def create_mujoco_scene(self):
        """Create MuJoCo scene with tunnel and obstacles"""
        # Create a simple world with the fly and tunnel
        # For now, we'll use the flybody model and add a floor
        # In production, we'd add the tunnel walls and obstacles to the XML
        pass
    
    def update_mujoco_scene(self):
        """Update 3D scene with new obstacles - marshalled to Tkinter main thread"""
        # Matplotlib is NOT thread-safe - must run on the main thread
        self.root.after(0, self._draw_scene_main_thread)

    def _draw_scene_main_thread(self):
        """Draw tunnel/obstacles on the Tkinter main thread"""
        try:
            self.draw_tunnel()
            self.log(f"Updated 3D scene with {len(self.environment.obstacles)} obstacles")
        except Exception as e:
            self.log(f"ERROR drawing 3D scene: {e}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")
    
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

    # Face indices for a cuboid with 8 vertices (see _cuboid_verts ordering:
    # sx outer, sy middle, sz inner -> v0=(-,-,-) ... v7=(+,+,+))
    _CUBOID_FACES = [
        [0, 2, 6, 4],  # z-min face
        [1, 3, 7, 5],  # z-max face
        [0, 1, 5, 4],  # y-min face
        [2, 3, 7, 6],  # y-max face
        [0, 1, 3, 2],  # x-min face
        [4, 5, 7, 6],  # x-max face
    ]

    @staticmethod
    def _rot_yz(dy, dz, angle):
        """Rotate an offset in the Y-Z cross-section plane (around tunnel X-axis)"""
        c, s = np.cos(angle), np.sin(angle)
        return dy * c - dz * s, dy * s + dz * c

    def _cuboid_verts(self, center, hx, hy, hz, rot=0.0):
        """Generate 8 vertices of a box centered at `center` with half-extents"""
        cx, cy, cz = center
        verts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    dy = sy * hy
                    dz = sz * hz
                    ry, rz = self._rot_yz(dy, dz, rot)
                    verts.append([cx + sx * hx, cy + ry, cz + rz])
        return np.array(verts)

    def _draw_polyhedron(self, verts, faces, color):
        """Draw a solid 3D polyhedron from vertices and face index lists"""
        polys = [[verts[i] for i in face] for face in faces]
        coll = Poly3DCollection(polys, alpha=1.0, facecolor=color,
                                edgecolor='black', linewidth=0.4)
        self.ax.add_collection3d(coll)

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

        # Draw obstacles - position is already [x=tunnel, y=vertical, z=lateral]
        obstacle_count = 0
        for i, obs in enumerate(self.environment.obstacles):
            pos = obs['position']
            size = obs['size']
            obs_type = obs.get('type', 'sphere')
            obstacle_count += 1

            # Debug: Log first few obstacles
            if i < 5:
                self.log(f"Drawing obstacle {i}: type={obs_type}, pos={obs['position']}, converted={pos}, size={size}")

            # Draw obstacle based on type - all solid 3D shapes
            rot = obs.get('rotation', 0.0)

            if obs_type == 'sphere':
                # Circle -> big 3D sphere
                u = np.linspace(0, 2 * np.pi, 24)
                v = np.linspace(0, np.pi, 24)
                x_obs = pos[0] + size * np.outer(np.cos(u), np.sin(v))
                y_obs = pos[1] + size * np.outer(np.sin(u), np.sin(v))
                z_obs = pos[2] + size * np.outer(np.ones(np.size(u)), np.cos(v))
                self.ax.plot_surface(x_obs, y_obs, z_obs, alpha=1.0, color='red')

            elif obs_type == 'box':
                # Rectangle -> solid 3D rectangular box (flat cuboid)
                hx, hy, hz = size / 2, size * 0.3, size * 0.6
                verts = self._cuboid_verts(pos, hx, hy, hz, rot)
                self._draw_polyhedron(verts, self._CUBOID_FACES, 'orange')

            elif obs_type == 'cylinder':
                # 3D cylinder along tunnel X-axis
                theta_obs = np.linspace(0, 2*np.pi, 24)
                x_obs_cyl = np.linspace(pos[0] - size/2, pos[0] + size/2, 12)
                theta_grid_obs, x_grid_obs_cyl = np.meshgrid(theta_obs, x_obs_cyl)
                y_grid_obs = pos[1] + size/2 * np.cos(theta_grid_obs)
                z_grid_obs = pos[2] + size/2 * np.sin(theta_grid_obs)
                self.ax.plot_surface(x_grid_obs_cyl, y_grid_obs, z_grid_obs, alpha=1.0, color='lime')

            elif obs_type == 'cube':
                # Square -> solid 3D cube
                h = size / 2
                verts = self._cuboid_verts(pos, h, h, h, rot)
                self._draw_polyhedron(verts, self._CUBOID_FACES, 'cyan')

            elif obs_type == 'pyramid':
                # Triangle -> solid 3D pyramid (square base, apex on top)
                h = size / 2
                y_base = pos[1] - h
                base_center = np.array([pos[0], y_base, pos[2]])
                corners = []
                for dy, dz in [(-h, -h), (-h, h), (h, h), (h, -h)]:
                    ry, rz = self._rot_yz(dy, dz, rot)
                    corners.append(base_center + np.array([0.0, ry, rz]))
                apex = np.array([pos[0], pos[1] + size * 1.2, pos[2]])
                verts = np.array(corners + [apex])
                faces = [[0, 3, 2, 1], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]]
                self._draw_polyhedron(verts, faces, 'magenta')

            elif obs_type == 'tetrahedron':
                # Triangle -> solid 3D tetrahedron (4 triangular faces)
                h = size / 2
                base_center = np.array([pos[0], pos[1] - h * 0.6, pos[2]])
                base = []
                for dy, dz in [(-h * 0.5, -h), (h * 0.5, -h), (0.0, h)]:
                    ry, rz = self._rot_yz(dy, dz, rot)
                    base.append(base_center + np.array([0.0, ry, rz]))
                v0 = np.array([pos[0], pos[1] + h, pos[2]])
                verts = np.array([v0] + base)
                faces = [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]]
                self._draw_polyhedron(verts, faces, 'yellow')

            else:
                # Fallback: big sphere
                u = np.linspace(0, 2 * np.pi, 24)
                v = np.linspace(0, np.pi, 24)
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

        # Set initial view angle only once - camera modes manage view afterwards
        if not getattr(self, '_view_initialized', False):
            self.ax.view_init(elev=20, azim=0)

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

        # Get fly position and velocity - already in display coords [x=tunnel, y=vertical, z=lateral]
        fly_pos = self.fly_model.get_position()
        fly_vel = self.fly_model.get_velocity()

        # Update camera limits - only auto-follow when user isn't controlling camera
        tunnel_length = self.environment.tunnel_length
        tunnel_radius = self.environment.tunnel_radius

        user_control = self.spectator_mode or self.simulation_paused or getattr(self, '_user_moved_camera', False)
        camera_view = getattr(self, 'camera_view', 'chase')
        zoom = getattr(self, '_zoom_factor', 1.0)

        if camera_view == 'flypov' and not self.spectator_mode:
            # Fly POV: first-person view from the fly looking down the tunnel (+x)
            # Camera sits at the fly; tight window shows tunnel ahead
            center = fly_pos + getattr(self, '_cam_offset', np.zeros(3))
            self.ax.set_xlim(center[0] - 2.0 * zoom, center[0] + 40.0 * zoom)
            self.ax.set_ylim(center[1] - 5.0 * zoom, center[1] + 5.0 * zoom)
            self.ax.set_zlim(center[2] - 5.0 * zoom, center[2] + 5.0 * zoom)
            if not getattr(self, '_view_initialized', False):
                # elev=0, azim=0 looks along +x; roll=90 puts world +y (up) on screen top
                self.ax.view_init(elev=0, azim=0, roll=90)
                self._view_initialized = True
        elif user_control:
            # User controls camera: center on fly + manual pan offset, keep user zoom/rotation
            center = fly_pos + getattr(self, '_cam_offset', np.zeros(3))
            half_x = 20.0 * zoom
            half_yz = tunnel_radius * zoom
            self.ax.set_xlim(center[0] - half_x, center[0] + half_x)
            self.ax.set_ylim(center[1] - half_yz, center[1] + half_yz)
            self.ax.set_zlim(center[2] - half_yz, center[2] + half_yz)
            if not getattr(self, '_view_initialized', False):
                self.ax.view_init(elev=10, azim=0)
                self._view_initialized = True
        else:
            # Auto-follow (chase cam): center view on fly
            half_x = 20.0 * zoom
            half_yz = tunnel_radius * zoom
            self.ax.set_xlim(fly_pos[0] - half_x, fly_pos[0] + half_x)
            self.ax.set_ylim(-half_yz, half_yz)
            self.ax.set_zlim(-half_yz, half_yz)
            if not getattr(self, '_view_initialized', False):
                self.ax.view_init(elev=10, azim=0)
                self._view_initialized = True

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
        # Keep rendering while paused so camera controls work
        if not self.viewer_running and not self.simulation_running:
            return

        try:
            # Handle WASD camera movement (paused or spectator mode)
            self.update_camera_move(0.033)

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
        """Handle mouse scroll for zoom - stays inside tunnel bounds"""
        if event.inaxes != self.ax:
            return

        tunnel_length = self.environment.tunnel_length
        tunnel_radius = self.environment.tunnel_radius

        # Adjust zoom factor (1.0 = default follow view)
        if not hasattr(self, '_zoom_factor'):
            self._zoom_factor = 1.0

        if event.step > 0:
            self._zoom_factor /= 1.15  # zoom in
        else:
            self._zoom_factor *= 1.15  # zoom out

        # Clamp: can't zoom out beyond whole tunnel, can't zoom in too close
        max_zoom_out = max(tunnel_length / 40.0, tunnel_radius / 10.0)
        self._zoom_factor = float(np.clip(self._zoom_factor, 0.15, max_zoom_out))

        # Mark that user took camera control so follow-mode doesn't fight us
        self._user_moved_camera = True
        self.canvas.draw_idle()

    def on_mouse_press(self, event):
        """Handle mouse press for rotation"""
        if event.inaxes == self.ax:
            self._dragging = True
            self._last_x = event.x
            self._last_y = event.y

    def on_mouse_move(self, event):
        """Handle mouse drag for 3D rotation"""
        if not getattr(self, '_dragging', False):
            return
        if event.inaxes != self.ax:
            return

        dx = event.x - self._last_x
        dy = event.y - self._last_y

        # Get current view angles
        elev = self.ax.elev
        azim = self.ax.azim

        # Update angles (clamp elevation to avoid flipping)
        new_elev = np.clip(elev + dy * 0.5, -90, 90)
        new_azim = azim - dx * 0.5

        self.ax.view_init(elev=new_elev, azim=new_azim)
        self._user_moved_camera = True

        self._last_x = event.x
        self._last_y = event.y
        self.canvas.draw_idle()

    def on_mouse_release(self, event):
        """Handle mouse release"""
        self._dragging = False

    def on_view_mode_change(self, event=None):
        """Handle camera view mode selection from combobox"""
        mode_text = self.view_mode_var.get()
        if mode_text == "Chase Cam":
            self.camera_view = "chase"
            self.spectator_mode = False
            self.spectator_var.set(False)
            self._user_moved_camera = False
            self._zoom_factor = 1.0
            self._cam_offset = np.array([0.0, 0.0, 0.0])
            self._view_initialized = False
            self.log("=== CAMERA VIEW: CHASE CAM ===")
            self.log("Camera follows the fly from behind/above")
        elif mode_text == "Fly POV":
            self.camera_view = "flypov"
            self.spectator_mode = False
            self.spectator_var.set(False)
            self._user_moved_camera = False
            self._view_initialized = False  # force POV view angle
            self.log("=== CAMERA VIEW: FLY POV ===")
            self.log("First-person view from the fly's eyes looking down the tunnel")
            self.log("Drag mouse to look around, scroll to zoom")
        elif mode_text == "Spectator":
            self.camera_view = "spectator"
            self.spectator_var.set(True)
            self.toggle_spectator_mode()

    def toggle_spectator_mode(self):
        """Toggle spectator mode - free camera, fly keeps flying"""
        old_mode = self.spectator_mode
        self.spectator_mode = self.spectator_var.get()

        # Sync combobox if changed via checkbox
        if self.spectator_mode and self.view_mode_var.get() != "Spectator":
            self.view_mode_var.set("Spectator")
            self.camera_view = "spectator"
        elif not self.spectator_mode and self.view_mode_var.get() == "Spectator":
            self.view_mode_var.set("Chase Cam")
            self.camera_view = "chase"

        if self.spectator_mode and not old_mode:
            self.log("=== SPECTATOR MODE ENABLED ===")
            self.log("You can now:")
            self.log("  - Rotate view: Click and drag mouse")
            self.log("  - Zoom: Use mouse wheel")
            self.log("  - WASD: move camera through tunnel")
            self.log("  - Fly continues flying normally")
            self.log("=============================")
            self._user_moved_camera = True
        elif not self.spectator_mode and old_mode:
            self.log("=== SPECTATOR MODE DISABLED ===")
            self.log("Camera will now follow the fly")
            self.log("=============================")
            self._user_moved_camera = False
            self._zoom_factor = 1.0
            self._cam_offset = np.array([0.0, 0.0, 0.0])

    # ---- WASD camera movement ----
    _MOVE_KEYS = {
        'w': np.array([1.0, 0.0, 0.0]),    # forward along tunnel (+x)
        's': np.array([-1.0, 0.0, 0.0]),   # backward along tunnel (-x)
        'a': np.array([0.0, 0.0, -1.0]),   # strafe left (-z lateral)
        'd': np.array([0.0, 0.0, 1.0]),    # strafe right (+z lateral)
        'r': np.array([0.0, 1.0, 0.0]),    # up (+y vertical)
        'f': np.array([0.0, -1.0, 0.0]),   # down (-y vertical)
        'q': np.array([0.0, 0.0, 0.0]),    # reserved
        'e': np.array([0.0, 0.0, 0.0]),    # reserved
    }

    def on_key_press(self, event):
        """Track held keys for WASD camera movement"""
        # Don't hijack keys while typing in an entry widget
        if isinstance(self.root.focus_get(), (tk.Entry, ttk.Entry, ttk.Combobox)):
            return
        key = event.keysym.lower()
        if key in self._MOVE_KEYS:
            if not hasattr(self, '_keys_down'):
                self._keys_down = set()
            self._keys_down.add(key)
            self._user_moved_camera = True

    def on_key_release(self, event):
        """Track released keys"""
        if isinstance(self.root.focus_get(), (tk.Entry, ttk.Entry, ttk.Combobox)):
            return
        key = event.keysym.lower()
        if hasattr(self, '_keys_down') and key in self._keys_down:
            self._keys_down.discard(key)

    def update_camera_move(self, dt):
        """Move camera position with WASD while paused or in spectator mode"""
        if not (self.simulation_paused or self.spectator_mode):
            return
        if not hasattr(self, '_keys_down') or not self._keys_down:
            return
        if not hasattr(self, '_cam_offset'):
            self._cam_offset = np.array([0.0, 0.0, 0.0])

        # Camera move speed scales with zoom (closer = slower precise movement)
        speed = 8.0 * getattr(self, '_zoom_factor', 1.0) * dt
        move = np.zeros(3)
        for key in self._keys_down:
            move += self._MOVE_KEYS[key]

        if np.linalg.norm(move) > 0:
            self._cam_offset += move / np.linalg.norm(move) * speed * 4.0

            # Clamp camera offset so view center stays inside tunnel
            tunnel_length = self.environment.tunnel_length
            tunnel_radius = self.environment.tunnel_radius
            fly_pos = self.fly_model.get_position()
            center = fly_pos + self._cam_offset
            center[0] = np.clip(center[0], -tunnel_length/2, tunnel_length/2)
            radial = np.sqrt(center[1]**2 + center[2]**2)
            if radial > tunnel_radius * 0.85:
                scale = tunnel_radius * 0.85 / radial
                center[1] *= scale
                center[2] *= scale
            self._cam_offset = center - fly_pos
            self._user_moved_camera = True

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
        self.simulation_paused = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED, text="Pause Simulation")
        self.status_label.config(text="Complete", foreground="blue")
        self.log(f"Simulation complete! Total: {self.current_simulation}")
        self.log(f"Best Score: {self.best_score}")
        self.log(f"Best Progress: {self.best_progress*100:.2f}%")
    
    def simulation_error(self):
        """Handle simulation error"""
        self.simulation_running = False
        self.simulation_paused = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED, text="Pause Simulation")
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
