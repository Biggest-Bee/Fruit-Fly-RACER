"""
Desktop GUI Application - Fruit Fly Racer
Tkinter-based desktop application with 3D visualization
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Canvas
import threading
import time
import sys
import os
import numpy as np
import math


class FruitFlyRacerGUI:
    """
    Desktop GUI for Fruit Fly Racer
    """
    
    def __init__(self, root):
        """
        Initialize the GUI
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Fruit Fly Racer - 3D Obstacle Course Racing Simulation")
        self.root.geometry("1200x800")
        
        # Simulation state
        self.simulation_running = False
        self.simulation_thread = None
        self.current_simulation = 0
        self.best_score = 0.0
        self.best_progress = 0.0
        
        # Create GUI
        self.create_menu()
        self.create_layout()
        self.create_control_panel()
        self.create_status_panel()
        self.create_log_panel()
        
        print("GUI initialized")
    
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Simulation menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        sim_menu.add_command(label="Start Simulation", command=self.start_simulation)
        sim_menu.add_command(label="Stop Simulation", command=self.stop_simulation)
        sim_menu.add_separator()
        sim_menu.add_command(label="Reset Statistics", command=self.reset_statistics)
        menubar.add_cascade(label="Simulation", menu=sim_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Clear Log", command=self.clear_log)
        menubar.add_cascade(label="View", menu=view_menu)
        
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
        
        # Left panel (controls and status)
        left_panel = ttk.Frame(main_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Right panel (log and visualization)
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 3D Visualization canvas
        viz_frame = ttk.LabelFrame(right_panel, text="3D Visualization")
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.viz_canvas = Canvas(viz_frame, bg="black", height=400)
        self.viz_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Log panel
        log_frame = ttk.LabelFrame(right_panel, text="Simulation Log")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.left_panel = left_panel
        self.right_panel = right_panel
    
    def create_control_panel(self):
        """Create control panel"""
        control_frame = ttk.LabelFrame(self.left_panel, text="Simulation Controls")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Start button
        self.start_button = ttk.Button(control_frame, text="Start Simulation", command=self.start_simulation)
        self.start_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Stop button
        self.stop_button = ttk.Button(control_frame, text="Stop Simulation", command=self.stop_simulation, state=tk.DISABLED)
        self.stop_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Number of simulations
        ttk.Label(control_frame, text="Number of Simulations:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.num_sims_var = tk.StringVar(value="1000000")
        ttk.Entry(control_frame, textvariable=self.num_sims_var).pack(fill=tk.X, padx=5, pady=5)
        
        # Speed
        ttk.Label(control_frame, text="Simulation Speed:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.speed_var = tk.StringVar(value="1x")
        speed_combo = ttk.Combobox(control_frame, textvariable=self.speed_var, values=["1x", "2x", "5x", "10x"])
        speed_combo.pack(fill=tk.X, padx=5, pady=5)
    
    def create_status_panel(self):
        """Create status panel"""
        status_frame = ttk.LabelFrame(self.left_panel, text="Status")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Current simulation
        ttk.Label(status_frame, text="Current Simulation:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.current_sim_label = ttk.Label(status_frame, text="0", font=("Arial", 12, "bold"))
        self.current_sim_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Best score
        ttk.Label(status_frame, text="Best Score:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.best_score_label = ttk.Label(status_frame, text="0.0", font=("Arial", 12, "bold"))
        self.best_score_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Best progress
        ttk.Label(status_frame, text="Best Progress:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.best_progress_label = ttk.Label(status_frame, text="0.0%", font=("Arial", 12, "bold"))
        self.best_progress_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Status
        ttk.Label(status_frame, text="Status:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.status_label = ttk.Label(status_frame, text="Idle", foreground="gray")
        self.status_label.pack(anchor=tk.W, padx=5, pady=5)
    
    def create_log_panel(self):
        """Create log panel"""
        log_frame = ttk.LabelFrame(self.right_panel, text="Simulation Log")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure tags for coloring
        self.log_text.tag_config("info", foreground="blue")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")
    
    def draw_3d_tunnel(self, obstacles=None, fly_position=None):
        """
        Draw 3D tunnel visualization on canvas
        
        Args:
            obstacles: List of obstacles to draw
            fly_position: Current fly position
        """
        self.viz_canvas.delete("all")
        
        # Canvas dimensions
        width = self.viz_canvas.winfo_width()
        height = self.viz_canvas.winfo_height()
        if width < 100:
            width = 600
        if height < 100:
            height = 400
        
        # 3D projection parameters
        scale = 20
        center_x = width / 2
        center_y = height / 2
        
        # Draw tunnel walls (cylinder)
        num_segments = 16
        for z in [-50, 0, 50]:  # Draw at different depths
            radius = 5.0
            for i in range(num_segments):
                angle = 2 * math.pi * i / num_segments
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                
                # Simple perspective projection
                proj_x = center_x + x * scale
                proj_y = center_y + y * scale + z * 0.5
                
                # Draw wall segment
                next_angle = 2 * math.pi * (i + 1) / num_segments
                next_x = radius * math.cos(next_angle)
                next_y = radius * math.sin(next_angle)
                next_proj_x = center_x + next_x * scale
                next_proj_y = center_y + next_y * scale + z * 0.5
                
                self.viz_canvas.create_line(proj_x, proj_y, next_proj_x, next_proj_y, fill="cyan", width=2)
        
        # Draw obstacles
        if obstacles:
            for obs in obstacles[:10]:  # Draw first 10 obstacles
                ox, oy, oz = obs['position']
                obs_size = obs['size']
                
                # Project obstacle position
                proj_ox = center_x + ox * scale
                proj_oy = center_y + oy * scale + oz * 0.5
                
                # Draw obstacle
                color = "red" if obs['has_hole'] else "orange"
                self.viz_canvas.create_oval(
                    proj_ox - obs_size * scale,
                    proj_oy - obs_size * scale,
                    proj_ox + obs_size * scale,
                    proj_oy + obs_size * scale,
                    fill=color, outline="white"
                )
        
        # Draw fly
        if fly_position is not None:
            fx, fy, fz = fly_position
            proj_fx = center_x + fx * scale
            proj_fy = center_y + fy * scale + fz * 0.5
            
            # Draw fly body
            self.viz_canvas.create_oval(
                proj_fx - 5, proj_fy - 5,
                proj_fx + 5, proj_fy + 5,
                fill="yellow", outline="white", width=2
            )
            
            # Draw direction indicator
            self.viz_canvas.create_line(
                proj_fx, proj_fy,
                proj_fx + 10, proj_fy,
                fill="white", width=2, arrow=tk.LAST
            )
        
        # Draw finish line
        finish_z = 50
        self.viz_canvas.create_line(
            center_x - 100, center_y + finish_z * 0.5,
            center_x + 100, center_y + finish_z * 0.5,
            fill="green", width=3
        )
        self.viz_canvas.create_text(
            center_x, center_y + finish_z * 0.5 - 10,
            text="FINISH LINE", fill="green", font=("Arial", 10, "bold")
        )
    
    def log(self, message, tag="info"):
        """
        Add message to log
        
        Args:
            message: Message to log
            tag: Tag for coloring
        """
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.log_text.update()
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete(1.0, tk.END)
    
    def start_simulation(self):
        """Start the simulation"""
        if self.simulation_running:
            self.log("Simulation already running", "warning")
            return
        
        try:
            num_sims = int(self.num_sims_var.get())
        except ValueError:
            self.log("Invalid number of simulations", "error")
            return
        
        self.simulation_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text="Running", foreground="green")
        
        self.log(f"Starting simulation: {num_sims} runs", "info")
        
        # Start simulation in background thread
        self.simulation_thread = threading.Thread(target=self.run_simulation, args=(num_sims,), daemon=True)
        self.simulation_thread.start()
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Stopping...", foreground="orange")
        self.log("Stopping simulation...", "warning")
    
    def run_simulation(self, num_sims: int):
        """
        Run the simulation (background thread)
        
        Args:
            num_sims: Number of simulations to run
        """
        try:
            # Import simulation modules
            from main_simulation import FruitFlyRacer
            
            # Create racer
            racer = FruitFlyRacer(num_simulations=num_sims)
            racer.simulation_running = True
            
            # Run simulations
            for sim_id in range(num_sims):
                if not self.simulation_running:
                    break
                
                self.current_simulation = sim_id + 1
                
                # Update GUI
                self.root.after(0, self.update_gui, self.current_simulation)
                
                # Update 3D visualization
                self.root.after(0, self.update_3d_viz, racer.environment.obstacles, results.get('position'))
                
                # Run single simulation
                results = racer.run_single_simulation()
                
                # Update neural weights
                racer.update_neural_weights(results)
                
                # Track best
                if results['total_points'] > self.best_score:
                    self.best_score = results['total_points']
                    self.root.after(0, self.update_best_score, self.best_score)
                
                if results['final_progress'] > self.best_progress:
                    self.best_progress = results['final_progress']
                    self.root.after(0, self.update_best_progress, self.best_progress)
                
                # Log progress
                if self.current_simulation % 10 == 0:
                    self.root.after(0, self.log_progress, self.current_simulation, results)
                
                # Save checkpoint
                if self.current_simulation % 100 == 0:
                    racer.sync_manager.save_checkpoint(racer.neural_weights)
                    self.root.after(0, self.log_checkpoint, self.current_simulation)
            
            # Final save
            racer.sync_manager.save_checkpoint(racer.neural_weights)
            
            # Done
            self.root.after(0, self.simulation_complete)
            
        except Exception as e:
            self.root.after(0, self.log_error, str(e))
            self.root.after(0, self.simulation_complete)
    
    def update_gui(self, current_sim: int):
        """Update GUI elements"""
        self.current_sim_label.config(text=str(current_sim))
    
    def update_best_score(self, score: float):
        """Update best score display"""
        self.best_score_label.config(text=f"{score:.1f}")
    
    def update_best_progress(self, progress: float):
        """Update best progress display"""
        self.best_progress_label.config(text=f"{progress:.2%}")
    
    def update_3d_viz(self, obstacles, position):
        """Update 3D visualization"""
        self.draw_3d_tunnel(obstacles, position)
    
    def log_progress(self, sim_id: int, results: dict):
        """Log simulation progress"""
        self.log(f"Sim {sim_id}: Progress {results['final_progress']:.2%}, Points {results['total_points']:.1f}", "info")
    
    def log_checkpoint(self, sim_id: int):
        """Log checkpoint save"""
        self.log(f"Checkpoint saved at simulation {sim_id}", "success")
    
    def log_error(self, error: str):
        """Log error"""
        self.log(f"Error: {error}", "error")
    
    def simulation_complete(self):
        """Handle simulation completion"""
        self.simulation_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Complete", foreground="green")
        self.log(f"Simulation complete! Total: {self.current_simulation}", "success")
        self.log(f"Best Score: {self.best_score:.1f}", "success")
        self.log(f"Best Progress: {self.best_progress:.2%}", "success")
    
    def reset_statistics(self):
        """Reset statistics"""
        self.current_simulation = 0
        self.best_score = 0.0
        self.best_progress = 0.0
        self.current_sim_label.config(text="0")
        self.best_score_label.config(text="0.0")
        self.best_progress_label.config(text="0.0%")
        self.log("Statistics reset", "info")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Fruit Fly Racer

3D Obstacle Course Racing Simulation

Based on MaleCNS v1.0 Fruit Fly Connectome
211,577 neurons / ~151.8M connections

Features:
- MuJoCo physics engine
- Procedural obstacle generation
- Dynamic wind fields
- Neural network learning
- Reward/penalty system
- Neural memory with cloud sync

Version 1.0"""
        messagebox.showinfo("About Fruit Fly Racer", about_text)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = FruitFlyRacerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
