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
from fly_cns_brain import FlyCNSBrain as FlyBrain


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
        self._restart_episode = False
        self.simulation_thread = None
        self.current_simulation = 0
        self.num_simulations = 1000000
        self.best_score = 0.0
        self.best_progress = 0.0
        
        # Initialize modules
        self.environment = RacingEnvironment(tunnel_length=500.0, tunnel_radius=10.0)
        self.fly_model = MuJoCoFlyModel(environment=self.environment)
        self.fly_model.load_connectome()
        self.agent = AgentLogic(input_size=100)
        self.rewards = RewardSystem()
        # Fly memory lives in the user's app-data folder so learned
        # weights survive repo moves/reinstalls (not inside the repo)
        memory_dir = os.path.join(
            os.environ.get('LOCALAPPDATA') or os.path.expanduser('~'),
            'FruitFlyRacer')
        os.makedirs(memory_dir, exist_ok=True)
        checkpoint_path = os.path.join(memory_dir, 'fly_memory.pkl')
        # One-time migration from the old repo-local checkpoint
        old_ckpt = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'fly_memory.pkl')
        if not os.path.exists(checkpoint_path) and os.path.exists(old_ckpt):
            try:
                import shutil
                shutil.copy2(old_ckpt, checkpoint_path)
                print(f"Migrated fly memory to {checkpoint_path}")
            except Exception:
                pass
        self.sync_manager = SyncManager(
            checkpoint_file=checkpoint_path,
            remote_url=None
        )

        # Learned flight brain (connectome reservoir + trained readout)
        self.brain = FlyBrain()
        # Restore learned weights/gains from checkpoint if present
        try:
            ckpt = self.sync_manager.load_checkpoint()
            if ckpt:
                self.brain.set_weights(ckpt.get('brain_weights'))
                gains = ckpt.get('gains')
                if gains:
                    self.environment.steer_gain = gains[0]
                    self.environment.center_gain = gains[1]
                    self.environment.avoid_margin = gains[2]
                    print(f"Restored brain + steering gains from checkpoint")
        except Exception as e:
            print(f"No usable checkpoint ({e}) - starting fresh brain")
        # Gain hill-climbing state
        self._gain_best_score = -1.0
        self._best_gains = (self.environment.steer_gain,
                            self.environment.center_gain,
                            self.environment.avoid_margin)
        
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
        self._zoom_factor = 1.4
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
        self.left_frame = left_frame
        
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

        self.restart_btn = ttk.Button(left_frame, text="Restart Episode", command=self.restart_episode, state=tk.DISABLED)
        self.restart_btn.pack(fill=tk.X, pady=5)

        ttk.Button(left_frame, text="Fullscreen 3D View",
                   command=self.toggle_fullscreen).pack(fill=tk.X, pady=5)

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

        # Bulkhead walls toggle (off by default - hole seeker helper
        # only runs while enabled)
        self.bulkhead_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(left_frame, text="Bulkhead Walls",
                        variable=self.bulkhead_var,
                        command=self.toggle_bulkheads).pack(fill=tk.X, pady=5)

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
        self.right_frame = right_frame

        # 3D View - matplotlib 3D plot
        view_frame = ttk.LabelFrame(right_frame, text="3D View", padding=10)
        view_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.view_frame = view_frame

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
        self.root.bind('<Control-p>', self.exit_spectator)

        # Log panel
        log_frame = ttk.LabelFrame(right_frame, text="Simulation Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_frame = log_frame

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Don't draw tunnel yet - wait for obstacles to be generated
        self.log("3D view initialized - obstacles will appear when simulation starts")

        # Log the initialization
        self.log("Fruit Fly Racer 3D initialized")
        self.log("Click 'Start Simulation' to begin training")
        self.log("3D view renders in this window")
    
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

        # Keep the user's selected camera mode - don't force chase cam
        self._zoom_factor = 1.4
        self._cam_offset = np.array([0.0, 0.0, 0.0])
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.NORMAL, text="Pause Simulation")
        self.restart_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Running", foreground="green")
        
        # Fullscreen 3D view while sim runs - except in spectator mode,
        # where the user keeps the panels (fullscreen is a button there)
        self._set_fullscreen(not self.spectator_mode)
        self.log(f"Starting simulation: {self.num_simulations} runs")
        self.log("Keys: O=stop, P=pause, L=resume, Space/R=up, C/F=down, WASD=move cam")
        
        # Start simulation in separate thread
        self.simulation_thread = threading.Thread(target=self.run_simulation, daemon=True)
        self.simulation_thread.start()
    
    def _set_fullscreen(self, on):
        """Hide/show control panels so the 3D view fills the window"""
        on = bool(on)
        if on == getattr(self, '_fullscreen', False):
            return
        self._fullscreen = on
        if on:
            self.left_frame.pack_forget()
            self.log_frame.pack_forget()
        else:
            self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10),
                                 before=self.right_frame)
            self.log_frame.pack(fill=tk.BOTH, expand=True)
        self.root.update_idletasks()

    def toggle_fullscreen(self):
        """Button: manually toggle the fullscreen 3D view"""
        self._set_fullscreen(not getattr(self, '_fullscreen', False))

    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_running = False
        self.simulation_paused = False
        self.viewer_running = False
        self._set_fullscreen(False)
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.restart_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Stopped", foreground="orange")
        self.log("Simulation stopped by user")

    def restart_episode(self):
        """Restart the current episode: fly returns to start line"""
        self._restart_episode = True
        self.log(">>> Restarting episode - fly back to start line")

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
                obstacles = self.environment.generate_obstacles(num_obstacles=50, with_holes=True)
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

            # Draw tunnel + obstacles immediately (previously only drawn
            # on obstacle regen every 10 episodes - with slower episodes
            # the tunnel appeared to never generate)
            self.update_mujoco_scene()
            
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

                # User restarted: partial run doesn't count toward scores,
                # gain adaptation, or checkpoints - just fly again
                if result.get('restart'):
                    continue

                # Update best scores
                if result['score'] > self.best_score:
                    self.best_score = result['score']
                    self.best_progress = result['progress']
                    self.log(f"New best! Score: {self.best_score:.1f}, Progress: {self.best_progress:.1%}")

                # Update best time (only if finished)
                if result.get('finish_reached', False) and episode_time < self.best_time:
                    self.best_time = episode_time
                    self.log(f"New best time! {self.best_time:.2f}s")

                # Brain end-of-episode: decay exploration, adapt steering gains
                self.brain.end_episode(result['score'], result['score'] >= self.best_score)
                self._adapt_gains(result)
                if result['score'] >= self.best_score and self.best_score > 0:
                    self._save_checkpoint()
                elif episode_count % 20 == 0:
                    self._save_checkpoint()  # periodic save anyway

                # Update status labels after EVERY episode so finishing a
                # race immediately reflects in the status area
                self.root.after(0, self.update_status)

                # Update GUI every 10 episodes
                if episode_count % 10 == 0:
                    self.log(f"Completed {episode_count} episodes. Best: {self.best_score:.1f}")

                # Finish line: fly returns to start and a NEW course is
                # generated for the next race
                if result.get('finish_reached', False):
                    try:
                        self.environment.generate_obstacles(num_obstacles=50, with_holes=True)
                        self.update_mujoco_scene()
                        self.log(f"New course: {len(self.environment.obstacles)} obstacles generated")
                    except Exception as e:
                        self.log(f"ERROR regenerating course: {e}")

                # Regenerate obstacles periodically too (only log occasionally)
                if episode_count % 10 == 1 and not result.get('finish_reached', False):
                    try:
                        self.environment.generate_obstacles(num_obstacles=50, with_holes=True)
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
            self.brain.reset_episode()
            self._ground_hit = False
            self._bh_passed = set()   # bulkhead holes already threaded

            # Run until the fly reaches the finish line (no step cap)
            step = 0
            step_count = 0
            dt = 0.02
            finish_reached = False
            restarted = False

            while self.simulation_running:
                # Handle pause - wait while paused but keep GUI responsive
                while self.simulation_paused and self.simulation_running:
                    time.sleep(0.05)
                if not self.simulation_running:
                    break

                # User pressed Restart Episode - bail out; the outer loop
                # starts a fresh episode (fly back to start line)
                if getattr(self, '_restart_episode', False):
                    self._restart_episode = False
                    restarted = True
                    self.log(">>> Episode restarted - resetting fly")
                    break

                step += 1
                step_count += 1

                # Get current position and velocity from fly model
                position = self.fly_model.get_position()
                velocity = self.fly_model.get_velocity()
                
                # Update wind
                wind = self.environment.update_wind(step * dt)
                
                # Get neural inputs
                # Neural control: connectome brain drives the official
                # flybody's 59 actuators (motor/descending populations)
                if hasattr(self.brain, 'actuator_commands'):
                    actuator_commands = self.brain.actuator_commands()
                else:
                    neural_inputs = self.agent.get_neural_inputs(
                        self.environment.obstacles, wind)
                    actuator_commands = self.fly_model.connect_to_neural_network(
                        neural_inputs)

                # Apply actuator commands to the fly
                self.fly_model.apply_neural_control(actuator_commands)

                # Fly brain: sensory features -> reservoir -> learned steering
                feat = self.brain.features(position, velocity, self.environment.obstacles)
                brain_act, bstate = self.brain.act(feat)

                # Teacher policy: potential-field steering + organic bobbing
                steer = self.environment.get_steering(position)
                t = step * dt
                teacher_y = steer[1] + 0.6 * np.sin(t * 1.7)   # vertical
                teacher_z = steer[2] + 0.6 * np.cos(t * 1.3)   # lateral

                # Brain takes over gradually over ~100 episodes - the
                # guided phase is long enough to learn hole-seeking
                alpha = min(1.0, self.brain.episode_count / 100.0)
                lat_y = (1 - alpha) * teacher_y + alpha * brain_act[0]
                lat_z = (1 - alpha) * teacher_z + alpha * brain_act[1]

                # Bulkhead holes: direct guidance applied AFTER the blend
                # so the fly seeks holes even when the brain drives.
                # Only active while bulkheads are enabled.
                if self.bulkhead_var.get():
                    bh = self.environment.bulkhead_guidance(position)
                else:
                    bh = np.zeros(2)
                lat_y += bh[0]
                lat_z += bh[1]

                # Throttle: speed follows maneuvering demand - full pace
                # on clear straights, scrubbed when it needs to turn or
                # climb. Lat commands are clipped to +-4 so demand 1.0 =
                # max lateral authority.
                turn_demand = min(1.0, max(abs(lat_y), abs(lat_z)) / 4.0)
                fwd_speed = self.environment.max_speed * (0.9 - 0.5 * turn_demand)

                # Wall approach: if a bulkhead is close ahead and the fly
                # isn't lined up on the hole, bleed forward speed so it
                # can actually turn - ramming the wall earns nothing
                if self.bulkhead_var.get():
                    bh_obs, bh_dx = self.environment.nearest_bulkhead(position)
                    if bh_obs is not None and bh_dx < 18.0:
                        hy, hz = bh_obs['position'][1], bh_obs['position'][2]
                        d_hole = np.hypot(position[1] - hy,
                                          position[2] - hz)
                        hole = bh_obs['hole_size']
                        if d_hole > hole:
                            fwd_speed *= float(np.clip(
                                1.0 - (d_hole - hole) / (hole + 5.0),
                                0.2, 1.0))

                desired_velocity = np.array([
                    fwd_speed,                         # forward along tunnel
                    np.clip(lat_y, -4.0, 4.0),
                    np.clip(lat_z, -4.0, 4.0)
                ])
                desired_turn = np.array([0.0, 0.0])

                # Brain learns from teacher demonstrations - include the
                # bulkhead hole guidance so it learns to seek holes
                self.brain.record(bstate, np.array(
                    [teacher_y + bh[0], teacher_z + bh[1]]))
                if step % 10 == 0:
                    self.brain.learn(steps=5)

                # Step MuJoCo physics with flight force
                x_before = position[0]
                self.fly_model.step(dt, desired_velocity=desired_velocity, desired_turn=desired_turn)

                # Wind pushes the fly - gusts drift it off-line
                if self.fly_model._fly_vel is not None:
                    self.fly_model._fly_vel += wind * dt * 1.5

                # Get updated position from physics
                if self.fly_model.data is not None:
                    position = self.fly_model.get_position()
                    velocity = self.fly_model.get_velocity()

                # Solid obstacles: push fly out if overlapping, bounce off
                new_pos, hit = self.environment.resolve_collision(position)
                if hit is not None:
                    self.fly_model._set_position(new_pos)
                    position = new_pos
                    if hit.get('type') == 'bulkhead':
                        penalty = self.rewards.calculate_bulkhead_penalty()
                        self.log(f"BULKHEAD HIT! Penalty {penalty:.0f}")
                    else:
                        penalty = self.rewards.calculate_collision_penalty()
                    self.rewards.update_total_points(penalty=penalty)
                    # Collision response: bleed speed but KEEP moving
                    # forward - a backward bounce could trap the fly
                    # against obstacles and prevent finishing
                    self.fly_model._fly_vel[0] *= 0.4
                    self.fly_model._fly_vel[1:] *= 0.4

                # Ground strike: touching the tunnel floor (usually after
                # a stall) costs a heavy penalty - once per contact
                floor_y = -self.environment.tunnel_radius * 0.8 * 0.99
                if position[1] <= floor_y:
                    if not getattr(self, '_ground_hit', False):
                        self._ground_hit = True
                        penalty = self.rewards.calculate_crash_penalty()
                        self.rewards.update_total_points(penalty=penalty)
                        stalled = ' (STALLED)' if getattr(
                            self.fly_model, '_fly_stalled', False) else ''
                        self.log(f"CRASH: hit the ground{stalled}! "
                                 f"Penalty {penalty:.0f}")
                elif position[1] > floor_y + 0.5:
                    self._ground_hit = False

                # Bulkhead hole bonus: crossed the wall plane inside the
                # hole radius - once per wall per episode
                for obs in self.environment.obstacles:
                    if obs.get('type') != 'bulkhead' or id(obs) in self._bh_passed:
                        continue
                    ox = obs['position'][0]
                    if (x_before < ox <= position[0]
                            and np.hypot(position[1] - obs['position'][1],
                                         position[2] - obs['position'][2])
                            <= obs['hole_size']):
                        self._bh_passed.add(id(obs))
                        bonus = self.rewards.calculate_hole_bonus()
                        self.rewards.update_total_points(reward=bonus)
                        self.log(f"HOLE! +{bonus:.0f} "
                                 f"({len(self._bh_passed)} this episode)")

                # Slowdown reward: near a bulkhead but outside the hole
                # cone, going slow is the RIGHT move - reward it so the
                # fly learns to line up instead of ramming the wall
                if self.bulkhead_var.get():
                    spd = np.linalg.norm(velocity[:3])
                    if (spd < 2.5
                            and not self.environment.in_hole_cone(position)):
                        _, bh_dx2 = self.environment.nearest_bulkhead(
                            position, 18.0)
                        if bh_dx2 is not None:
                            self.rewards.update_total_points(
                                reward=self.rewards.calculate_slow_bonus())

                # Check progress
                progress = self.environment.get_progress_to_finish(position)
                reward = self.rewards.calculate_progress_reward(progress)
                self.rewards.update_total_points(reward=reward)

                # Check if fly crossed the finish line - end episode and reset
                if progress >= 1.0:
                    finish_reached = True
                    # Finish bonus: all accumulated reward x10
                    self.rewards.total_points = min(
                        self.rewards.total_points * 10.0,
                        self.rewards.max_points * 10.0)
                    self.log(f"Finish line reached! Score x10: {self.rewards.total_points:.1f}")
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
                'finish_reached': finish_reached,
                'restart': restarted
            }

        except Exception as e:
            self.log(f"Error in episode: {e}")
            return {'score': 0.0, 'progress': 0.0, 'collisions': 0, 'finish_reached': False}
    
    def _adapt_gains(self, result):
        """Hill-climb steering gains: keep what scored well, perturb what didn't"""
        env = self.environment
        score = result['score']
        if score >= self._gain_best_score:
            self._gain_best_score = score
            self._best_gains = (env.steer_gain, env.center_gain, env.avoid_margin)
        else:
            # Revert to best-known gains, then perturb for exploration
            env.steer_gain, env.center_gain, env.avoid_margin = self._best_gains
            env.steer_gain = float(np.clip(
                env.steer_gain * np.exp(self.brain.rng.normal(0, 0.15)), 0.3, 2.5))
            env.center_gain = float(np.clip(
                env.center_gain * np.exp(self.brain.rng.normal(0, 0.15)), 0.02, 0.3))
            env.avoid_margin = float(np.clip(
                env.avoid_margin + self.brain.rng.normal(0, 0.5), 1.0, 6.0))

    def _save_checkpoint(self):
        """Persist brain weights + steering gains to fly_memory.pkl"""
        try:
            self.sync_manager.save_checkpoint({
                'brain_weights': self.brain.get_weights(),
                'gains': (self.environment.steer_gain,
                          self.environment.center_gain,
                          self.environment.avoid_margin),
                'best_score': self.best_score,
            })
        except Exception as e:
            self.log(f"Checkpoint save failed: {e}")

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
        coll = Poly3DCollection(polys, alpha=0.55, facecolor=color,
                                edgecolor='black', linewidth=0.4)
        self.ax.add_collection3d(coll)

    def _draw_cap_fan(self, center, rim_yz, color):
        """Draw a filled circular cap as a triangle fan.
        center: (3,) array, rim_yz: (N,2) array of (y,z) rim points."""
        n = len(rim_yz)
        c = np.asarray(center, dtype=float)
        polys = []
        for i in range(n):
            j = (i + 1) % n
            p1 = np.array([c[0], rim_yz[i, 0], rim_yz[i, 1]])
            p2 = np.array([c[0], rim_yz[j, 0], rim_yz[j, 1]])
            polys.append([c, p1, p2])
        coll = Poly3DCollection(polys, alpha=0.35, facecolor=color,
                                edgecolor='none')
        self.ax.add_collection3d(coll)

    # ---------------- real flybody rendering ----------------

    def _ensure_fly_render_data(self):
        """Precompute ellipsoid approximations of every official flybody geom.

        The flybody model is ~0.4 model units long; we scale it up to
        ~0.45 m in the scene. Geom poses are static (no physics stepping),
        so world-space verts are precomputed once and just translated
        with the fly each frame.
        """
        if getattr(self, '_fly_render_ready', False):
            return
        m = self.fly_model.model
        d = self.fly_model.data
        mujoco.mj_forward(m, d)

        # Low-poly unit sphere template (6x4 -> ~18 quad faces per geom)
        nu, nv = 6, 4
        u = np.linspace(0, 2 * np.pi, nu, endpoint=False)
        v = np.linspace(0, np.pi, nv)
        tpl = []
        for vi in range(nv):
            for ui in range(nu):
                tpl.append([np.sin(v[vi]) * np.cos(u[ui]),
                            np.sin(v[vi]) * np.sin(u[ui]),
                            np.cos(v[vi])])
        tpl = np.array(tpl)
        faces = []
        for vi in range(nv - 1):
            for ui in range(nu):
                a = vi * nu + ui
                faces.append([a, vi * nu + (ui + 1) % nu,
                              (vi + 1) * nu + (ui + 1) % nu,
                              (vi + 1) * nu + ui])
        tpl_faces = np.array(faces)
        n_tpl_faces = len(tpl_faces)

        # Axis remap: flybody model is Z-up with +X forward (head at +X,
        # mouthparts below). Display coords are [x=tunnel, y=up, z=lateral]
        # -> swap model Y and Z.
        P = np.array([[1., 0., 0.],
                      [0., 0., 1.],
                      [0., 1., 0.]])

        # MuJoCo geom type enum: plane=0 hfield=1 sphere=2 capsule=3
        # ellipsoid=4 cylinder=5 box=6 mesh=7
        def semi_axes(i, gt):
            s = m.geom_size[i]
            if gt == 2:    # sphere
                return np.array([s[0]] * 3)
            if gt == 3:    # capsule: radius + half-length along z
                return np.array([s[0], s[0], s[0] + s[1]])
            if gt == 4:    # ellipsoid: geom_size IS the semi-axes
                return np.maximum(s, 1e-4)
            if gt == 5:    # cylinder
                return np.array([s[0], s[0], s[1] + s[0] * 0.3])
            if gt == 6:    # box: half extents -> inscribed ellipsoid
                return np.maximum(s * 0.85, 1e-4)
            if gt == 7:    # mesh: AABB of real mesh vertices
                try:
                    mid = int(m.geom_dataid[i])
                    adr = int(m.mesh_vertadr[mid])
                    num = int(m.mesh_vertnum[mid])
                    mv = m.mesh_vert
                    mv = mv.reshape(-1, 3) if mv.ndim == 1 else mv
                    vv = mv[adr:adr + num]
                    ext = (vv.max(axis=0) - vv.min(axis=0)) / 2.0
                    if np.all(ext > 1e-6):
                        return np.maximum(ext * 0.9, 1e-4)
                except Exception:
                    pass
                return np.maximum(np.asarray(s[:3]), 1e-4)
            return np.array([0.01] * 3)

        base_verts = []
        face_idx = []
        face_cols = []
        wing_mask_parts = []
        wing_pivot_parts = []
        wing_side_parts = []
        max_r = 1e-6
        vbase = 0
        brown = np.array([0.42, 0.26, 0.15, 0.9])
        for i in range(m.ngeom):
            gt = int(m.geom_type[i])
            if gt == 0:      # skip floor plane
                continue
            # offset from the ROOT body (thorax, body 1 = the body we
            # teleport to fly_pos) so limbs keep their place in the pose
            off = (d.geom_xpos[i] - d.xpos[1]).astype(np.float64)
            R = d.geom_xmat[i].reshape(3, 3).astype(np.float64)
            semi = semi_axes(i, gt)
            # transform model frame -> display frame
            R = P @ R
            off = P @ off
            # real fly colors come from materials (body cuticle, red eyes,
            # translucent wing membranes) via geom_matid -> mat_rgba
            matid = int(m.geom_matid[i]) if hasattr(m, 'geom_matid') else -1
            if matid >= 0 and hasattr(m, 'mat_rgba'):
                col = np.array(m.mat_rgba[matid], dtype=np.float64)
                col[3] = max(col[3], 0.85)   # keep parts visible
            else:
                rgba = m.geom_rgba[i] if hasattr(m, 'geom_rgba') else brown
                col = np.array([rgba[0], rgba[1], rgba[2], 0.9])

            # scaled + rotated + offset verts (fly_pos added per frame)
            bv = (tpl * semi) @ R.T + off
            base_verts.append(bv)
            face_idx.append(tpl_faces + vbase)
            face_cols.append(np.tile(col, (n_tpl_faces, 1)))

            # wing geoms get a per-frame flap: pivot on the body centerline
            # at the wing's x/y, rotating about the forward (X) axis
            body_name = (mujoco.mj_id2name(
                m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[i])) or '')
            is_wing = 'wing' in body_name
            n_v = len(bv)
            wing_mask_parts.append(np.full(n_v, is_wing))
            wing_pivot_parts.append(np.tile(
                [off[0], off[1], 0.0], (n_v, 1)))
            wing_side_parts.append(np.full(n_v, np.sign(off[2]) or 1.0))
            vbase += n_v
            max_r = max(max_r, float(np.linalg.norm(off)) + float(np.max(semi)))

        self._fly_base_verts = np.vstack(base_verts)
        self._fly_faces_idx = np.vstack(face_idx)
        self._fly_facecolors = np.vstack(face_cols)
        self._fly_wing_mask = np.concatenate(wing_mask_parts)
        self._fly_wing_pivot = np.vstack(wing_pivot_parts)
        self._fly_wing_side = np.concatenate(wing_side_parts)
        # real fly ~0.4 units -> ~0.8 m in the scene (enlarged so it's
        # visible in the tight chase-cam window)
        self._fly_vis_scale = 0.8 / (2.0 * max_r)
        self._fly_base_verts *= self._fly_vis_scale
        self._fly_wing_pivot *= self._fly_vis_scale
        self._fly_render_ready = True
        print(f"Flybody renderer: {m.ngeom} geoms -> "
              f"{len(self._fly_faces_idx)} faces, scale={self._fly_vis_scale:.3f}")

    def _draw_flybody(self, fly_pos, fly_vel):
        """Draw the real flybody geoms as one merged Poly3DCollection.

        Per frame: wing geoms flap about the forward axis, then the whole
        fly is rotated to face its velocity (yaw+pitch) and banked into
        turns like a real fly.
        """
        try:
            self._ensure_fly_render_data()
        except Exception as e:
            self.log(f"Flybody render init failed: {e}")
            return

        now = time.monotonic()
        dt = min(now - getattr(self, '_fly_anim_t', now), 0.1)
        self._fly_anim_t = now

        V = self._fly_base_verts.copy()

        # --- wing flap: rotate wing verts about the forward (X) axis ---
        # through a pivot on the body centerline; opposite signs per side
        # so both wingtips beat upward together (~8 Hz)
        wm = self._fly_wing_mask
        if wm.any():
            phase = 2.0 * np.pi * 8.0 * now
            flap = 0.55 * np.sin(phase)          # ~0.55 rad stroke
            theta = -self._fly_wing_side[wm] * flap
            c, s = np.cos(theta), np.sin(theta)
            rel = V[wm] - self._fly_wing_pivot[wm]
            y_new = rel[:, 1] * c - rel[:, 2] * s
            z_new = rel[:, 1] * s + rel[:, 2] * c
            V[wm, 1] = y_new + self._fly_wing_pivot[wm][:, 1]
            V[wm, 2] = z_new + self._fly_wing_pivot[wm][:, 2]

        # --- orientation: face velocity, pitch with it, bank into turns ---
        speed = float(np.linalg.norm(fly_vel))
        if speed > 0.3:
            f = fly_vel / speed                     # fly forward axis
            # keep a stable heading when nearly vertical
            if abs(f[1]) > 0.95:
                f = np.array([f[0], 0.05 * np.sign(f[1]) or 1.0, f[2]])
                f /= np.linalg.norm(f)
            world_up = np.array([0.0, 1.0, 0.0])
            r = np.cross(f, world_up)               # lateral (right) axis
            rn = np.linalg.norm(r)
            if rn < 1e-6:
                r = np.array([0.0, 0.0, 1.0])
            else:
                r /= rn
            u = np.cross(r, f)                      # dorsal axis
            u /= np.linalg.norm(u)

            # bank angle comes from the physics model (yaw-rate estimate)
            # so the visual roll always matches the aerodynamic state
            bank = getattr(self.fly_model, '_fly_bank', 0.0)
            cb, sb = np.cos(bank), np.sin(bank)
            # rotate u,r about f: u' = u*cb + (f x u)*sb ; f x u = r
            u2 = u * cb + r * sb
            r2 = r * cb - u * sb

            # R columns = fly axes expressed in world coords;
            # row-vector verts: V @ R (since R maps local->world, use R.T)
            R = np.column_stack([f, u2, r2])
            V = V @ R.T
        # else: keep last orientation (identity on first frames)

        V += np.asarray(fly_pos, dtype=np.float64)
        polys = V[self._fly_faces_idx]
        coll = Poly3DCollection(polys, facecolors=self._fly_facecolors,
                                alpha=0.9, edgecolor='none')
        coll._is_fly = True
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

        # Single semi-transparent wall - visible from both sides so the
        # tunnel interior (fly + obstacles) can be seen from any camera angle.
        # (matplotlib cameras always render from outside the bounding box,
        #  so an opaque wall would hide everything inside)
        self.ax.plot_surface(x_grid, y_grid, z_grid, alpha=0.35, color='blue', edgecolor='none')

        # Draw tunnel end caps (start and finish) - enclosed
        # Start cap ring (X = -tunnel_length/2)
        theta_cap = np.linspace(0, 2*np.pi, 60)
        y_cap = tunnel_radius * np.cos(theta_cap)
        z_cap = tunnel_radius * np.sin(theta_cap)
        x_cap = np.full_like(theta_cap, -tunnel_length/2)
        self.ax.plot(x_cap, y_cap, z_cap, color='green', linewidth=3, label='Start')

        # Finish line ring - 10m before the end wall so the fly finishes
        # before reaching the cap (matches get_progress_to_finish)
        x_cap_finish = np.full_like(theta_cap, tunnel_length/2 - 10.0)
        self.ax.plot(x_cap_finish, y_cap, z_cap, color='red', linewidth=3, label='Finish')

        # Filled end caps as triangle fans (proper enclosed tunnel - no see-through)
        center_start = np.array([-tunnel_length/2, 0.0, 0.0])
        center_finish = np.array([tunnel_length/2, 0.0, 0.0])
        rim = np.stack([y_cap, z_cap], axis=1)  # (N,2) y,z pairs
        self._draw_cap_fan(center_start, rim, 'darkgreen')
        self._draw_cap_fan(center_finish, rim, 'darkgreen')

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
                self.ax.plot_surface(x_obs, y_obs, z_obs, alpha=0.55, color='red')

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
                self.ax.plot_surface(x_grid_obs_cyl, y_grid_obs, z_grid_obs, alpha=0.55, color='lime')

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

            elif obs_type == 'bulkhead':
                # Bulkhead wall: semi-transparent disk spanning the tunnel
                # cross-section at pos[0]; pos[1:]=hole center, hole_size
                # = hole radius. Yellow ring marks the passable hole.
                Rw = self.environment.tunnel_radius * 0.98
                th = np.linspace(0, 2 * np.pi, 48)
                rr = np.linspace(0, Rw, 10)
                tg, rg = np.meshgrid(th, rr)
                xs = np.full_like(tg, pos[0])
                ys = rg * np.cos(tg)
                zs = rg * np.sin(tg)
                self.ax.plot_surface(xs, ys, zs, alpha=0.35, color='gray')
                hr = obs['hole_size']
                ring_x = np.full_like(th, pos[0])
                ring_y = pos[1] + hr * np.cos(th)
                ring_z = pos[2] + hr * np.sin(th)
                self.ax.plot(ring_x, ring_y, ring_z,
                             color='yellow', linewidth=2)

            else:
                # Fallback: big sphere
                u = np.linspace(0, 2 * np.pi, 24)
                v = np.linspace(0, np.pi, 24)
                x_obs = pos[0] + size * np.outer(np.cos(u), np.sin(v))
                y_obs = pos[1] + size * np.outer(np.sin(u), np.sin(v))
                z_obs = pos[2] + size * np.outer(np.ones(np.size(u)), np.cos(v))
                self.ax.plot_surface(x_obs, y_obs, z_obs, alpha=0.55, color='purple')

        # Log obstacle count
        self.log(f"Drawn {obstacle_count} obstacles in 3D view")

        # Set axis limits - horizontal tunnel
        self.ax.set_xlim(-tunnel_length/2, tunnel_length/2)
        self.ax.set_ylim(-tunnel_radius*1.5, tunnel_radius*1.5)
        self.ax.set_zlim(-tunnel_radius*1.5, tunnel_radius*1.5)

        # Clean cinematic view: no ticks, labels, grid, or pane chrome
        self.ax.set_xticks([]); self.ax.set_yticks([]); self.ax.set_zticks([])
        self.ax.set_xlabel(''); self.ax.set_ylabel(''); self.ax.set_zlabel('')
        self.ax.set_title('')
        self.ax.grid(False)
        self.ax.xaxis.pane.set_visible(False)
        self.ax.yaxis.pane.set_visible(False)
        self.ax.zaxis.pane.set_visible(False)
        # axis spines/lines themselves (the remaining "ticks frame")
        self.ax.xaxis.line.set_visible(False)
        self.ax.yaxis.line.set_visible(False)
        self.ax.zaxis.line.set_visible(False)

        # Set initial view angle only once - camera modes manage view afterwards
        if not getattr(self, '_view_initialized', False):
            # vertical_axis='y': elev = height above fly, azim orbits about
            # the up axis; azim=270 puts the camera behind the fly (+x fwd)
            self.ax.view_init(elev=20, azim=270, vertical_axis='y')

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
        zoom = getattr(self, '_zoom_factor', 1.4)

        if camera_view == 'flypov' and not self.spectator_mode:
            # Fly POV: first-person view from the fly looking down the tunnel (+x)
            # Camera sits at the fly; window wide enough to see tunnel walls
            center = fly_pos + getattr(self, '_cam_offset', np.zeros(3))
            self.ax.set_xlim(center[0] - 2.0 * zoom, center[0] + 40.0 * zoom)
            self.ax.set_ylim(center[1] - tunnel_radius * 0.95 * zoom, center[1] + tunnel_radius * 0.95 * zoom)
            self.ax.set_zlim(center[2] - tunnel_radius * 0.95 * zoom, center[2] + tunnel_radius * 0.95 * zoom)
            if not getattr(self, '_view_initialized', False):
                # eye-level behind the fly, looking down-tunnel (+x)
                self.ax.view_init(elev=2, azim=270, vertical_axis='y')
                self._view_initialized = True
        elif user_control:
            # User controls camera. Spectator uses a fixed world-space
            # camera position; paused-mode pan stays relative to the fly.
            if self.spectator_mode:
                center = getattr(self, '_cam_world',
                                 self.fly_model.get_position())
            else:
                center = fly_pos + getattr(self, '_cam_offset', np.zeros(3))
            half_x = 20.0 * zoom
            half_yz = tunnel_radius * zoom
            self.ax.set_xlim(center[0] - half_x, center[0] + half_x)
            self.ax.set_ylim(center[1] - half_yz, center[1] + half_yz)
            self.ax.set_zlim(center[2] - half_yz, center[2] + half_yz)
            if not getattr(self, '_view_initialized', False):
                self.ax.view_init(elev=15, azim=270, vertical_axis='y')
                self._view_initialized = True
        else:
            # Chase cam: tight window just behind/above the fly's torso,
            # biased ahead so obstacles come into view. Camera yaw/pitch is
            # fixed - it does NOT follow the fly's bank angle.
            self.ax.set_xlim(fly_pos[0] - 2.5 * zoom, fly_pos[0] + 11.5 * zoom)
            self.ax.set_ylim(fly_pos[1] - 3.5 * zoom, fly_pos[1] + 3.5 * zoom)
            self.ax.set_zlim(fly_pos[2] - 3.5 * zoom, fly_pos[2] + 3.5 * zoom)
            if not getattr(self, '_view_initialized', False):
                # elev=25: camera above the torso, behind the fly
                self.ax.view_init(elev=25, azim=270, vertical_axis='y')
                self._view_initialized = True

        # Draw the real official flybody model (all geoms: body, eyes,
        # antennae, legs, wings) instead of a proxy shape
        self._draw_flybody(fly_pos, fly_vel)

        # Draw velocity vector (direction of flight)
        if np.linalg.norm(fly_vel) > 0.1:
            vel_scale = 2.0  # Scale velocity vector
            vel_end = fly_pos + fly_vel * vel_scale
            vel_line, = self.ax.plot([fly_pos[0], vel_end[0]],
                                   [fly_pos[1], vel_end[1]],
                                   [fly_pos[2], vel_end[2]],
                                   color='yellow', linewidth=3)
            vel_line._is_fly = True

        # (title removed for clean view - stall state is in fly_model._fly_stalled)

        # HUD: live coordinates, top-left of the 3D view
        if self.spectator_mode:
            cam_center = getattr(self, '_cam_world', fly_pos)
        else:
            cam_center = fly_pos + getattr(self, '_cam_offset', np.zeros(3))
        hud = (f"Fly: {fly_pos[0]:.1f}, {fly_pos[1]:.1f}, {fly_pos[2]:.1f}   "
               f"You: {cam_center[0]:.1f}, {cam_center[1]:.1f}, {cam_center[2]:.1f}")
        if getattr(self, '_coord_text', None) is None:
            self._coord_text = self.fig.text(
                0.01, 0.98, hud, fontsize=10, color='white',
                va='top', ha='left',
                bbox=dict(facecolor='black', alpha=0.5, pad=3))
        else:
            self._coord_text.set_text(hud)

        # Zoom readout, top-right: factor + actual view window size
        try:
            xl = self.ax.get_xlim(); yl = self.ax.get_ylim(); zl = self.ax.get_zlim()
            view_txt = (f"Zoom {getattr(self, '_zoom_factor', 1.4):.2f}x | "
                        f"view {xl[1]-xl[0]:.1f}x{yl[1]-yl[0]:.1f}m")
        except Exception:
            view_txt = f"Zoom {getattr(self, '_zoom_factor', 1.4):.2f}x"
        if getattr(self, '_zoom_text', None) is None:
            self._zoom_text = self.fig.text(
                0.99, 0.98, view_txt, fontsize=10, color='white',
                va='top', ha='right',
                bbox=dict(facecolor='black', alpha=0.5, pad=3))
        else:
            self._zoom_text.set_text(view_txt)

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
            # Don't kill the render loop on a transient frame error -
            # log it and keep rendering or the view freezes completely
            self.log(f"Render error: {e}")
            import traceback
            traceback.print_exc()

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
            self._zoom_factor = 1.4

        # event.step is +1 (up) / -1 (down); fall back to button name for
        # backends that don't populate it
        step = getattr(event, 'step', 0) or 0
        if step == 0:
            btn = getattr(event, 'button', '')
            step = 1 if btn in ('up', 'scroll_up', 1) else -1

        if step > 0:
            self._zoom_factor /= 1.15  # zoom in
        else:
            self._zoom_factor *= 1.15  # zoom out

        # Clamp: can't zoom out beyond whole tunnel. Min zoom 0.7 - below
        # ~0.66 the camera gets close enough that matplotlib's depth
        # sorting degenerates and obstacle faces flash over the fly
        max_zoom_out = max(tunnel_length / 40.0, tunnel_radius / 10.0)
        self._zoom_factor = float(np.clip(self._zoom_factor, 0.7, max_zoom_out))

        # NOTE: don't set _user_moved_camera here - scrolling should zoom
        # without kicking the user out of chase-cam mode
        self.canvas.draw_idle()

    def on_mouse_press(self, event):
        """Handle mouse press for rotation"""
        if event.inaxes == self.ax:
            self._dragging = True
            self._last_x = event.x
            self._last_y = event.y

    def on_mouse_move(self, event):
        """Handle mouse drag for 3D rotation - in spectator mode the view
        follows the mouse with no click required"""
        if event.inaxes != self.ax:
            return
        if not getattr(self, '_dragging', False) and not self.spectator_mode:
            # keep baseline fresh so entering spectator doesn't jump
            self._last_x = event.x
            self._last_y = event.y
            return

        # No baseline yet (just entered spectator / released mouse)
        if getattr(self, '_last_x', None) is None:
            self._last_x = event.x
            self._last_y = event.y
            return

        dx = event.x - self._last_x
        dy = event.y - self._last_y

        # Get current view angles
        elev = self.ax.elev
        azim = self.ax.azim

        # Update angles (clamp elevation to avoid flipping)
        new_elev = np.clip(elev + dy * 0.5, -90, 90)
        new_azim = azim - dx * 0.5

        # preserve vertical_axis='y' so +y stays screen-up and elev/azim
        # behave like a normal chase camera; keep user's roll if any
        kw = {'vertical_axis': 'y'}
        if hasattr(self.ax, 'roll') and self.ax.roll:
            kw['roll'] = self.ax.roll
        self.ax.view_init(elev=new_elev, azim=new_azim, **kw)
        self._user_moved_camera = True
        self._cam_input_t = time.monotonic()

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
            self._zoom_factor = 1.4
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
            # Anchor the free camera at the fly's current position - it
            # stays fixed in world space and does NOT follow the fly
            self._cam_world = self.fly_model.get_position().copy()
            self._last_x = None
            self._last_y = None
            self.log("=== SPECTATOR MODE ENABLED ===")
            self.log("You can now:")
            self.log("  - Look: move mouse (no click needed) or drag")
            self.log("  - Zoom: Use mouse wheel")
            self.log("  - WASD: move camera through tunnel")
            self.log("  - Space/R: up, C/F: down")
            self.log("  - Ctrl+P: exit spectator")
            self.log("  - Camera stays fixed - it does NOT follow the fly")
            self.log("=============================")
            self._user_moved_camera = True
        elif not self.spectator_mode and old_mode:
            self.log("=== SPECTATOR MODE DISABLED ===")
            self.log("Camera will now follow the fly")
            self.log("=============================")
            self._user_moved_camera = False
            self._zoom_factor = 1.4
            self._cam_offset = np.array([0.0, 0.0, 0.0])

    def toggle_bulkheads(self):
        """Enable/disable bulkhead walls + hole-seeker helper.
        Takes effect on the next generated course."""
        enabled = self.bulkhead_var.get()
        self.environment.set_bulkheads(enabled)
        self.log(f"Bulkhead walls {'ENABLED' if enabled else 'DISABLED'} "
                 f"- {'hole seeker active' if enabled else 'no hole seeker'} "
                 f"(next course)")

    def exit_spectator(self, event=None):
        """Ctrl+P: exit spectator mode; if not in spectator, exit fullscreen"""
        if self.spectator_mode:
            self.spectator_var.set(False)
            self.toggle_spectator_mode()
            self.log("=== SPECTATOR MODE DISABLED (Ctrl+P) ===")
        elif getattr(self, '_fullscreen', False):
            self._set_fullscreen(False)
            self.log("=== FULLSCREEN OFF (Ctrl+P) ===")

    # ---- WASD camera movement ----
    _MOVE_KEYS = {
        'w': np.array([1.0, 0.0, 0.0]),    # forward along tunnel (+x)
        's': np.array([-1.0, 0.0, 0.0]),   # backward along tunnel (-x)
        'a': np.array([0.0, 0.0, -1.0]),   # strafe left (-z lateral)
        'd': np.array([0.0, 0.0, 1.0]),    # strafe right (+z lateral)
        'r': np.array([0.0, 1.0, 0.0]),    # up (+y vertical)
        'f': np.array([0.0, -1.0, 0.0]),   # down (-y vertical)
        'space': np.array([0.0, 1.0, 0.0]),  # up (alt)
        'c': np.array([0.0, -1.0, 0.0]),   # down (alt)
        'q': np.array([0.0, 0.0, 0.0]),    # reserved
        'e': np.array([0.0, 0.0, 0.0]),    # reserved
    }

    def on_key_press(self, event):
        """Track held keys for WASD camera movement"""
        # Don't hijack keys while typing in an entry widget
        if isinstance(self.root.focus_get(), (tk.Entry, ttk.Entry, ttk.Combobox)):
            return
        # If a button has keyboard focus, move focus away so Space doesn't
        # re-trigger it and camera keys keep working
        if isinstance(self.root.focus_get(), (tk.Button, ttk.Button)):
            self.root.focus_set()
        key = event.keysym.lower()

        # Ignore Control combos here - <Control-p> etc have their own binds
        if event.state & 0x4:
            return

        # Simulation control keys (work in fullscreen where panels are hidden)
        if self.simulation_running:
            if key == 'o':
                self.stop_simulation()
                return
            if key == 'p' and not self.simulation_paused:
                self.pause_simulation()
                return
            if key == 'l' and self.simulation_paused:
                self.pause_simulation()
                return

        if key in self._MOVE_KEYS:
            if not hasattr(self, '_keys_down'):
                self._keys_down = set()
            self._keys_down.add(key)
            self._user_moved_camera = True
            self._cam_input_t = time.monotonic()

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
        speed = 8.0 * getattr(self, '_zoom_factor', 1.4) * dt
        move = np.zeros(3)
        for key in self._keys_down:
            move += self._MOVE_KEYS[key]

        if np.linalg.norm(move) > 0:
            self._cam_offset += move / np.linalg.norm(move) * speed * 4.0

            # Clamp camera offset so view center stays inside tunnel
            tunnel_length = self.environment.tunnel_length
            tunnel_radius = self.environment.tunnel_radius
            if self.spectator_mode:
                # World-anchored free camera: move the camera itself
                if not hasattr(self, '_cam_world'):
                    self._cam_world = self.fly_model.get_position().copy()
                self._cam_world += (move / np.linalg.norm(move)
                                    * speed * 4.0)
                center = self._cam_world
            else:
                fly_pos = self.fly_model.get_position()
                center = fly_pos + self._cam_offset
            center[0] = np.clip(center[0], -tunnel_length/2, tunnel_length/2)
            radial = np.sqrt(center[1]**2 + center[2]**2)
            if radial > tunnel_radius * 0.85:
                scale = tunnel_radius * 0.85 / radial
                center[1] *= scale
                center[2] *= scale
            if self.spectator_mode:
                self._cam_world = center
            else:
                self._cam_offset = center - fly_pos
            self._user_moved_camera = True

    def update_status(self):
        """Update status display"""
        self.sim_count_label.config(text=f"Simulation: {self.current_simulation}")
        self.best_score_label.config(text=f"Best Score: {self.best_score:.1f}")
        self.best_progress_label.config(text=f"Best Progress: {self.best_progress*100:.2f}%")

        # Live status text: shows current episode so finishing a race is
        # visible immediately (runs every episode now)
        if self.simulation_running and not self.simulation_paused:
            self.status_label.config(
                text=f"Running - Episode {self.current_simulation}",
                foreground="green")

        # Update best time display
        if self.best_time != float('inf'):
            self.best_time_label.config(text=f"Best Time: {self.best_time:.2f}s")
        else:
            self.best_time_label.config(text="Best Time: --")
    
    def simulation_complete(self):
        """Handle simulation completion"""
        self.simulation_running = False
        self.simulation_paused = False
        self._set_fullscreen(False)
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED, text="Pause Simulation")
        self.restart_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Complete", foreground="blue")
        self.log(f"Simulation complete! Total: {self.current_simulation}")
        self.log(f"Best Score: {self.best_score}")
        self.log(f"Best Progress: {self.best_progress*100:.2f}%")
    
    def simulation_error(self):
        """Handle simulation error"""
        self.simulation_running = False
        self.simulation_paused = False
        self._set_fullscreen(False)
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED, text="Pause Simulation")
        self.restart_btn.config(state=tk.DISABLED)
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
