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
        self.environment = RacingEnvironment(tunnel_length=100.0, tunnel_radius=5.0)
        self.fly_model = MuJoCoFlyModel()
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

        # Create matplotlib figure and canvas
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasTkAgg(self.fig, master=view_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initialize plot
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.ax.set_title('Fruit Fly Racer - 3D View')

        # Draw tunnel
        self.draw_tunnel()

        # Log panel
        log_frame = ttk.LabelFrame(right_frame, text="Simulation Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

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
            # Generate obstacles
            self.environment.generate_obstacles(num_obstacles=20, with_holes=True)
            
            # Create MuJoCo scene with tunnel and obstacles
            self.create_mujoco_scene()
            
            # Start MuJoCo viewer
            self.start_mujoco_viewer()
            
            # Run simulation loop
            episode_count = 0
            while self.simulation_running and self.current_simulation < self.num_simulations:
                self.current_simulation += 1
                episode_count += 1

                # Only log every 10 episodes to reduce spam
                if episode_count % 10 == 1:
                    self.log(f"Episode {episode_count}: Starting...")
                    self.log(f"Environment: {len(self.environment.obstacles)} obstacles")
                    self.log(f"Fly model: {self.fly_model.model.nq} DOF, {self.fly_model.model.nu} actuators")

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
                    self.environment.generate_obstacles(num_obstacles=20, with_holes=True)
                    self.update_mujoco_scene()

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

                # Generate desired velocity for flight (forward + slight lift)
                desired_velocity = np.array([0.0, 0.0, self.environment.max_speed * 0.8])  # Forward at 80% max speed
                desired_turn = np.array([0.0, 0.0])  # No turning for now

                # Step MuJoCo physics with flight force
                self.fly_model.step(dt, desired_velocity=desired_velocity, desired_turn=desired_turn)

                # Get updated position from physics
                if self.fly_model.data is not None:
                    position = self.fly_model.data.qpos[:3]
                    velocity = self.fly_model.data.qvel[:3]
                
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
        """Update MuJoCo scene with new obstacles"""
        # Update obstacle positions in MuJoCo scene
        # This would modify the MuJoCo model to reflect new obstacles
        pass
    
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
        """Draw the tunnel in 3D"""
        # Clear previous tunnel
        for line in self.ax.lines[:]:
            line.remove()
        for collection in self.ax.collections[:]:
            collection.remove()
        for poly in self.ax.collections[:]:
            poly.remove()

        # Draw tunnel as cylinder
        tunnel_length = self.environment.tunnel_length
        tunnel_radius = self.environment.tunnel_radius

        # Create cylinder surface
        theta = np.linspace(0, 2*np.pi, 100)
        z = np.linspace(-tunnel_length/2, tunnel_length/2, 50)

        # Create meshgrid for cylinder
        theta_grid, z_grid = np.meshgrid(theta, z)
        x_grid = tunnel_radius * np.cos(theta_grid)
        y_grid = tunnel_radius * np.sin(theta_grid)

        # Draw cylinder walls (semi-transparent)
        self.ax.plot_surface(x_grid, y_grid, z_grid, alpha=0.3, color='blue', edgecolor='none')

        # Draw tunnel end caps (start and finish)
        # Start cap
        theta_cap = np.linspace(0, 2*np.pi, 50)
        x_cap = tunnel_radius * np.cos(theta_cap)
        y_cap = tunnel_radius * np.sin(theta_cap)
        z_cap = np.full_like(theta_cap, -tunnel_length/2)
        self.ax.plot(x_cap, y_cap, z_cap, color='green', linewidth=2, label='Start')

        # Finish cap
        z_cap_finish = np.full_like(theta_cap, tunnel_length/2)
        self.ax.plot(x_cap, y_cap, z_cap_finish, color='green', linewidth=2, label='Finish')

        # Draw obstacles as different shapes
        for i, obs in enumerate(self.environment.obstacles):
            pos = obs['position']
            size = obs['size']
            obs_type = obs.get('type', 'sphere')

            # Draw obstacle based on type
            if obs_type == 'sphere':
                # Draw sphere
                u = np.linspace(0, 2 * np.pi, 20)
                v = np.linspace(0, np.pi, 20)
                x = pos[0] + size * np.outer(np.cos(u), np.sin(v))
                y = pos[1] + size * np.outer(np.sin(u), np.sin(v))
                z = pos[2] + size * np.outer(np.ones(np.size(u)), np.cos(v))
                self.ax.plot_surface(x, y, z, alpha=0.7, color='red')

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
                # Draw cylinder obstacle
                theta_obs = np.linspace(0, 2*np.pi, 20)
                z_obs = np.linspace(pos[2] - size/2, pos[2] + size/2, 10)
                theta_grid_obs, z_grid_obs = np.meshgrid(theta_obs, z_obs)
                x_grid_obs = pos[0] + size/2 * np.cos(theta_grid_obs)
                y_grid_obs = pos[1] + size/2 * np.sin(theta_grid_obs)
                self.ax.plot_surface(x_grid_obs, y_grid_obs, z_grid_obs, alpha=0.7, color='orange')

            else:
                # Default to sphere for unknown types
                u = np.linspace(0, 2 * np.pi, 20)
                v = np.linspace(0, np.pi, 20)
                x = pos[0] + size * np.outer(np.cos(u), np.sin(v))
                y = pos[1] + size * np.outer(np.sin(u), np.sin(v))
                z = pos[2] + size * np.outer(np.ones(np.size(u)), np.cos(v))
                self.ax.plot_surface(x, y, z, alpha=0.7, color='purple')

        # Set axis limits
        self.ax.set_xlim(-tunnel_radius*1.5, tunnel_radius*1.5)
        self.ax.set_ylim(-tunnel_radius*1.5, tunnel_radius*1.5)
        self.ax.set_zlim(-tunnel_length/2, tunnel_length/2)

        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Z (m) - Tunnel Length')
        self.ax.set_title('Fruit Fly Racer - 3D Tunnel View')

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
        fly_pos = self.fly_model.get_position()
        fly_vel = self.fly_model.get_velocity()

        # Draw fly as an elongated shape (like a real fly)
        # Create a simple fly body representation
        fly_size = 0.3  # Size of fly representation

        # Draw fly body (elongated ellipsoid)
        u = np.linspace(0, 2 * np.pi, 20)
        v = np.linspace(0, np.pi, 20)

        # Elongated along z-axis (direction of flight)
        x = fly_pos[0] + fly_size * 0.5 * np.outer(np.cos(u), np.sin(v))
        y = fly_pos[1] + fly_size * 0.5 * np.outer(np.sin(u), np.sin(v))
        z = fly_pos[2] + fly_size * 2.0 * np.outer(np.ones(np.size(u)), np.cos(v))

        fly_surface = self.ax.plot_surface(x, y, z, alpha=0.8, color='darkgreen')
        fly_surface._is_fly = True

        # Draw fly wings (two ellipses on sides)
        wing_size = fly_size * 0.8
        for side in [-1, 1]:  # Left and right wings
            # Wing position offset
            wing_x = fly_pos[0] + side * fly_size * 0.3
            wing_y = fly_pos[1]
            wing_z = fly_pos[2]

            # Wing as flattened ellipsoid
            u_wing = np.linspace(0, 2 * np.pi, 15)
            v_wing = np.linspace(0, np.pi, 15)
            x_wing = wing_x + wing_size * np.outer(np.cos(u_wing), np.sin(v_wing))
            y_wing = wing_y + wing_size * 0.1 * np.outer(np.sin(u_wing), np.sin(v_wing))
            z_wing = wing_z + wing_size * np.outer(np.ones(np.size(u_wing)), np.cos(v_wing))

            wing_surface = self.ax.plot_surface(x_wing, y_wing, z_wing, alpha=0.6, color='lightblue')
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
    
    def toggle_spectator_mode(self):
        """Toggle spectator mode"""
        self.spectator_mode = self.spectator_var.get()
        if self.spectator_mode:
            self.log("Spectator mode enabled - you can move camera freely")
            # Bind mouse and keyboard events
            self.canvas.bind("<Motion>", self.on_mouse_move)
            self.canvas.bind("<ButtonPress-1>", self.on_mouse_click)
            self.canvas.focus_set()
        else:
            self.log("Spectator mode disabled - camera follows fly")
            self.canvas.unbind("<Motion>")
            self.canvas.unbind("<ButtonPress-1>")

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
