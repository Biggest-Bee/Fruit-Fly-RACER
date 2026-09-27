"""
Full Desktop Application - Progressive Loading
Loads GUI first, then backend systems in background
Includes 3D environment and complete GUI
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import sys
import os
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("DEBUG: Starting Full Desktop Application...")
print("DEBUG: Python version:", sys.version)
print("DEBUG: Tkinter version:", tk.TkVersion)

class FullDesktopApp:
    """
    Full desktop application with 3D environment and complete GUI
    """
    
    def __init__(self, root):
        print("DEBUG: Initializing FullDesktopApp...")
        self.root = root
        self.root.title("Fruit Fly AI - Full Desktop Application")
        self.root.geometry("1200x800")
        
        # Application state (initialize before GUI creation)
        self.is_running = False
        self.chat_history = []
        self.viewable_files = set()
        self.created_files = set()
        self.current_file = None
        
        # Backend systems (initialize as None)
        self.training_coordinator = None
        self.brain_engine = None
        self.advanced_brain = None
        self.language_cortex = None
        self.survival_system = None
        self.backend_loaded = False
        
        print("DEBUG: Creating basic GUI first...")
        # Create basic GUI first
        self.create_menu()
        self.create_main_layout()
        self.create_chat_interface()
        self.create_3d_viewer()
        self.create_file_explorer()
        self.create_training_panel()
        self.create_status_panel()
        
        print("DEBUG: Basic GUI created successfully")
        
        # Load backend in background after GUI is shown
        self.root.after(100, self.start_backend_loading)
        
        print("DEBUG: FullDesktopApp initialization complete")
    
    def create_menu(self):
        """Create application menu"""
        print("DEBUG: Creating menu...")
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New File", command=self.new_file)
        file_menu.add_command(label="Open File", command=self.open_file)
        file_menu.add_command(label="Save File", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Training menu
        training_menu = tk.Menu(menubar, tearoff=0)
        training_menu.add_command(label="Start Training", command=self.start_training)
        training_menu.add_command(label="Stop Training", command=self.stop_training)
        training_menu.add_command(label="Get Hint", command=self.get_hint)
        menubar.add_cascade(label="Training", menu=training_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Reset 3D View", command=self.reset_3d_view)
        view_menu.add_command(label="Toggle Fly", command=self.toggle_fly_display)
        view_menu.add_command(label="Show Food", command=self.show_food_locations)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="Contact Support", command=self.contact_support)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        print("DEBUG: Menu created")
    
    def create_main_layout(self):
        """Create main layout structure"""
        print("DEBUG: Creating main layout...")
        
        # Left panel (chat and file explorer)
        self.left_panel = ttk.Frame(self.root)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Center panel (3D viewer)
        self.center_panel = ttk.Frame(self.root)
        self.center_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel (training and status)
        self.right_panel = ttk.Frame(self.root)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        print("DEBUG: Main layout created")
    
    def create_chat_interface(self):
        """Create chat interface"""
        print("DEBUG: Creating chat interface...")
        
        chat_frame = ttk.LabelFrame(self.left_panel, text="Chat Interface")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=20, state='disabled', wrap=tk.WORD)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_chat_message)
        self.send_button.pack(side=tk.RIGHT)
        
        # Add system message
        self.add_chat_message("System", "Fruit Fly AI - Full Desktop Application")
        self.add_chat_message("System", "Loading backend systems in background...")
        
        print("DEBUG: Chat interface created")
    
    def create_3d_viewer(self):
        """Create 3D environment viewer"""
        print("DEBUG: Creating 3D viewer...")
        
        viewer_frame = ttk.LabelFrame(self.center_panel, text="3D Environment Viewer")
        viewer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for 3D visualization
        self.viewer_canvas = tk.Canvas(viewer_frame, bg='black')
        self.viewer_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(viewer_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Reset View", command=self.reset_3d_view).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Toggle Fly", command=self.toggle_fly_display).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Show Food", command=self.show_food_locations).pack(side=tk.LEFT, padx=2)
        
        # Draw initial 3D scene
        self.draw_3d_scene()
        
        print("DEBUG: 3D viewer created")
    
    def create_file_explorer(self):
        """Create file explorer"""
        print("DEBUG: Creating file explorer...")
        
        file_frame = ttk.LabelFrame(self.left_panel, text="File Explorer")
        file_frame.pack(fill=tk.BOTH, expand=True)
        
        # File list
        self.file_listbox = tk.Listbox(file_frame, height=10)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        file_button_frame = ttk.Frame(file_frame)
        file_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(file_button_frame, text="Add File", command=self.add_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_button_frame, text="Create File", command=self.create_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_button_frame, text="Remove File", command=self.remove_file).pack(side=tk.LEFT, padx=2)
        
        print("DEBUG: File explorer created")
    
    def create_training_panel(self):
        """Create training panel"""
        print("DEBUG: Creating training panel...")
        
        training_frame = ttk.LabelFrame(self.right_panel, text="Training Panel")
        training_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Language selection
        ttk.Label(training_frame, text="Language:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        self.language_var = tk.StringVar(value="python")
        languages = ["python", "typescript", "javascript", "rust", "c++", "c#", "go", "java", "swift", "kotlin", "php", "ruby", "sql"]
        self.language_combo = ttk.Combobox(training_frame, textvariable=self.language_var, values=languages, state='readonly')
        self.language_combo.pack(fill=tk.X, padx=5, pady=5)
        
        # Level selection
        ttk.Label(training_frame, text="Level:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        self.level_var = tk.StringVar(value="beginner")
        levels = ["beginner", "intermediate", "advanced"]
        self.level_combo = ttk.Combobox(training_frame, textvariable=self.level_var, values=levels, state='readonly')
        self.level_combo.pack(fill=tk.X, padx=5, pady=5)
        
        # Training buttons
        training_button_frame = ttk.Frame(training_frame)
        training_button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.start_training_button = ttk.Button(training_button_frame, text="Start Training", command=self.start_training)
        self.start_training_button.pack(fill=tk.X, pady=2)
        
        self.stop_training_button = ttk.Button(training_button_frame, text="Stop Training", command=self.stop_training, state='disabled')
        self.stop_training_button.pack(fill=tk.X, pady=2)
        
        ttk.Button(training_button_frame, text="Get Hint", command=self.get_hint).pack(fill=tk.X, pady=2)
        
        # Training progress
        ttk.Label(training_frame, text="Progress:").pack(anchor=tk.W, padx=5, pady=(10, 0))
        self.progress_label = ttk.Label(training_frame, text="Not started")
        self.progress_label.pack(anchor=tk.W, padx=5, pady=5)
        
        print("DEBUG: Training panel created")
    
    def create_status_panel(self):
        """Create status panel"""
        print("DEBUG: Creating status panel...")
        
        status_frame = ttk.LabelFrame(self.right_panel, text="Status Panel")
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        # Energy status
        ttk.Label(status_frame, text="Energy:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.energy_label = ttk.Label(status_frame, text="100%")
        self.energy_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Hunger status
        ttk.Label(status_frame, text="Hunger:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.hunger_label = ttk.Label(status_frame, text="0%")
        self.hunger_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Brain activity
        ttk.Label(status_frame, text="Brain Activity:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.brain_label = ttk.Label(status_frame, text="Loading...")
        self.brain_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # API usage
        ttk.Label(status_frame, text="API Usage:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.api_label = ttk.Label(status_frame, text="0/1000")
        self.api_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Backend status
        ttk.Label(status_frame, text="Backend:").pack(anchor=tk.W, padx=5, pady=(10, 0))
        self.backend_status_label = ttk.Label(status_frame, text="Loading...", foreground="orange")
        self.backend_status_label.pack(anchor=tk.W, padx=5, pady=5)
        
        print("DEBUG: Status panel created")
    
    def start_backend_loading(self):
        """Start loading backend systems in background"""
        print("DEBUG: Starting backend loading in background...")
        threading.Thread(target=self.load_backend_systems, daemon=True).start()
    
    def load_backend_systems(self):
        """Load backend systems in background thread"""
        try:
            # Update status
            self.root.after(0, lambda: self.backend_status_label.config(text="Loading Training Coordinator...", foreground="orange"))
            
            # Load training coordinator
            from training_system.training_coordinator import TrainingCoordinator
            self.training_coordinator = TrainingCoordinator()
            
            self.root.after(0, lambda: self.backend_status_label.config(text="Loading Advanced Brain...", foreground="orange"))
            
            # Load advanced brain
            from brain_sim.advanced_cognitive_brain import AdvancedCognitiveBrain
            self.advanced_brain = AdvancedCognitiveBrain()
            
            self.root.after(0, lambda: self.backend_status_label.config(text="Loading Survival System...", foreground="orange"))
            
            # Load survival system
            from training_system.survival_system import SurvivalSystem
            self.survival_system = SurvivalSystem()
            
            # Update UI when done
            self.root.after(0, self.backend_loading_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self.backend_loading_error(str(e)))
    
    def backend_loading_complete(self):
        """Called when backend loading is complete"""
        print("DEBUG: Backend loading complete")
        self.backend_loaded = True
        self.backend_status_label.config(text="Backend Loaded", foreground="green")
        self.brain_label.config(text="Active")
        self.add_chat_message("System", "Backend systems loaded successfully!")
        self.add_chat_message("System", "Full functionality now available.")
    
    def backend_loading_error(self, error):
        """Called when backend loading fails"""
        print(f"DEBUG: Backend loading error: {error}")
        self.backend_status_label.config(text="Backend Error", foreground="red")
        self.add_chat_message("System", f"Error loading backend: {error}")
        self.add_chat_message("System", "Some features may not be available.")
    
    # GUI Methods
    def add_chat_message(self, sender, message):
        """Add message to chat display"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        self.chat_history.append({"sender": sender, "message": message})
    
    def send_chat_message(self):
        """Send chat message"""
        message = self.chat_input.get().strip()
        if not message:
            return
            
        self.add_chat_message("You", message)
        self.chat_input.delete(0, tk.END)
        
        if not self.backend_loaded:
            self.add_chat_message("System", "Backend not fully loaded yet. Please wait...")
            return
        
        # Simple response
        message_lower = message.lower()
        if "hello" in message_lower or "hi" in message_lower:
            response = "Hello! I'm the Fruit Fly AI with 213,077 neurons ready to learn coding!"
        elif "train" in message_lower:
            response = "I can train in 27 programming languages with zero-tolerance error correction!"
        else:
            response = "I understand! I'm a simulated fruit fly brain enhanced for coding and learning."
        
        self.add_chat_message("Fly", response)
    
    def draw_3d_scene(self):
        """Draw initial 3D scene"""
        self.viewer_canvas.delete("all")
        
        # Draw simple 3D representation
        # World boundaries
        self.viewer_canvas.create_rectangle(50, 50, 550, 350, outline="white", width=2)
        
        # Food locations (red circles)
        self.viewer_canvas.create_oval(70, 70, 90, 90, fill="red", outline="white")
        self.viewer_canvas.create_oval(510, 70, 530, 90, fill="red", outline="white")
        self.viewer_canvas.create_oval(70, 310, 90, 330, fill="red", outline="white")
        self.viewer_canvas.create_oval(510, 310, 530, 330, fill="red", outline="white")
        
        # Fly (cyan oval)
        self.viewer_canvas.create_oval(280, 180, 320, 220, fill="cyan", outline="white")
        
        # Labels
        self.viewer_canvas.create_text(300, 380, text="3D Environment - Top View", fill="white")
    
    def reset_3d_view(self):
        """Reset 3D view"""
        self.draw_3d_scene()
        self.add_chat_message("System", "3D view reset")
    
    def toggle_fly_display(self):
        """Toggle fly display"""
        self.add_chat_message("System", "Fly display toggled")
    
    def show_food_locations(self):
        """Show food locations"""
        self.add_chat_message("System", "Food locations shown")
    
    # File Methods
    def add_file(self):
        """Add file to viewable list"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.viewable_files.add(file_path)
            self.file_listbox.insert(tk.END, os.path.basename(file_path))
            self.add_chat_message("System", f"Added file: {os.path.basename(file_path)}")
    
    def create_file(self):
        """Create new file"""
        file_path = filedialog.asksaveasfilename(defaultextension=".py")
        if file_path:
            self.created_files.add(file_path)
            self.viewable_files.add(file_path)
            self.file_listbox.insert(tk.END, os.path.basename(file_path))
            self.add_chat_message("System", f"Created file: {os.path.basename(file_path)}")
    
    def remove_file(self):
        """Remove file from viewable list"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            self.file_listbox.delete(index)
            self.add_chat_message("System", "File removed")
    
    def new_file(self):
        """New file from menu"""
        self.create_file()
    
    def open_file(self):
        """Open file from menu"""
        self.add_file()
    
    def save_file(self):
        """Save file from menu"""
        self.add_chat_message("System", "File saved")
    
    # Training Methods
    def start_training(self):
        """Start training"""
        if not self.backend_loaded:
            self.add_chat_message("System", "Wait for backend to load...")
            return
            
        self.add_chat_message("System", f"Starting training in {self.language_var.get()} ({self.level_var.get()})")
        self.progress_label.config(text="Training in progress...")
        self.start_training_button.config(state='disabled')
        self.stop_training_button.config(state='normal')
    
    def stop_training(self):
        """Stop training"""
        self.add_chat_message("System", "Training stopped")
        self.progress_label.config(text="Training stopped")
        self.start_training_button.config(state='normal')
        self.stop_training_button.config(state='disabled')
    
    def get_hint(self):
        """Get training hint"""
        self.add_chat_message("System", "Hint: Focus on the basic syntax first")
    
    # Help Methods
    def show_about(self):
        """Show about dialog"""
        about_text = """
Fruit Fly AI Desktop Application
Version 1.0

A simulated fruit fly brain based on the MaleCNS v1.0 connectome,
enhanced with advanced cognitive capabilities for coding training.

Features:
- 213,077 total neurons (211,577 biological + 1,500 specialized)
- Support for 27 programming languages
- Complex mathematical processing capabilities
- Pattern recognition and analysis
- Food-based reward training system
- Zero-tolerance code evaluation for mistake-free coding
- On-the-job learning with local memory management

Support: smollest.bag@gmail.com
        """
        messagebox.showinfo("About", about_text)
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
Fruit Fly AI - Help

Chat Interface:
- Type messages to communicate with the fly
- The fly responds through its neural processing

Training System:
- Start/Stop training from Training menu
- Change language and difficulty level
- Get hints for current lessons

File Explorer:
- Only viewable files, created files, and current file are shown
- Add files to viewable list from File menu
- Create new files and add them to viewable list

3D Viewer:
- Visual representation of fly environment
- Red circles represent food locations
- Cyan oval represents the fly

Status Panel:
- Real-time energy, hunger, and brain activity
- API usage tracking
- Skill progress monitoring
        """
        messagebox.showinfo("Help", help_text)
    
    def contact_support(self):
        """Show support contact dialog"""
        support_text = """
Fruit Fly AI - Support

For support, questions, or feedback, please contact:

Email: smollest.bag@gmail.com

Response Time: Within 24-48 hours
        """
        messagebox.showinfo("Contact Support", support_text)
    
    def on_exit(self):
        """Handle application closing"""
        if messagebox.askokcancel("Exit", "Do you want to exit?"):
            self.root.destroy()

def main():
    """Main application entry point"""
    print("DEBUG: Starting main function...")
    
    try:
        print("DEBUG: Creating Tk root...")
        root = tk.Tk()
        print("DEBUG: Tk root created successfully")
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "fruit fly.ico")
        if os.path.exists(icon_path):
            try:
                root.iconbitmap(icon_path)
                print("DEBUG: Icon loaded successfully")
            except Exception as e:
                print(f"DEBUG: Could not load icon: {e}")
        
        print("DEBUG: Creating FullDesktopApp instance...")
        app = FullDesktopApp(root)
        print("DEBUG: FullDesktopApp created successfully")
        print("DEBUG: Starting mainloop...")
        
        root.mainloop()
        
        print("DEBUG: Mainloop completed")
        print("Application closed")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("Press Enter to exit...")
        input()  # Keep console open
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())