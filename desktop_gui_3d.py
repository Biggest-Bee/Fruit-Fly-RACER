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

        # 3D View - embedded MuJoCo renderer
        view_frame = ttk.LabelFrame(right_frame, text="3D View (MuJoCo)", padding=10)
        view_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create canvas for 3D rendering
        self.canvas = tk.Canvas(view_frame, bg="black", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Store current image for display
        self.current_image = None

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
        """Start MuJoCo renderer embedded in Tkinter"""
        if self.fly_model.model is None or self.fly_model.data is None:
            self.log("Error: Fly model not loaded")
            return

        try:
            # MuJoCo 3.16.0 uses mujoco.rendering.classic.renderer.Renderer
            from mujoco.rendering.classic.renderer import Renderer
            from PIL import Image, ImageTk
            import mujoco

            # Create renderer
            self.renderer = Renderer(self.fly_model.model, height=600, width=800)
            self.viewer_running = True

            self.log("MuJoCo renderer started")

            # Start render loop in separate thread
            def render_loop():
                try:
                    frame_count = 0
                    while self.viewer_running and self.simulation_running:
                        try:
                            # Update scene with camera
                            # Use "hero" camera for best view, or "track1" for tracking
                            cam_name = 'hero' if not self.spectator_mode else 'track1'
                            self.renderer.update_scene(self.fly_model.data, camera=cam_name)

                            # Render frame
                            frame = self.renderer.render()
                            frame_count += 1

                            # Debug: Log frame info every 30 frames
                            if frame_count % 30 == 0:
                                self.log(f"Frame {frame_count}: shape={frame.shape}, dtype={frame.dtype}, min={frame.min()}, max={frame.max()}")
                                self.log(f"Camera: {cam_name}")
                                self.log(f"Fly position: {self.fly_model.get_position()}")

                            # Convert to PIL Image and display in Tkinter
                            img = Image.fromarray(frame)
                            img_tk = ImageTk.PhotoImage(img)

                            # Update canvas in main thread
                            self.root.after(0, lambda: self.update_canvas(img_tk))

                            time.sleep(0.033)  # ~30 FPS
                        except Exception as e:
                            self.log(f"Render error: {e}")
                            import traceback
                            traceback.print_exc()
                            break

                    self.renderer.close()
                    self.log(f"MuJoCo renderer stopped after {frame_count} frames")

                except Exception as e:
                    self.log(f"Render loop error: {e}")
                    import traceback
                    traceback.print_exc()

            threading.Thread(target=render_loop, daemon=True).start()

        except Exception as e:
            self.log(f"Viewer error: {e}")

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
        if self.viewer is not None:
            self.viewer_running = False
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = FruitFlyRacer3D(root)
    root.mainloop()


if __name__ == "__main__":
    main()
