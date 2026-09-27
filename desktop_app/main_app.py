"""
Desktop Application - Main Window
Main desktop application interface for the Fruit Fly AI project
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import sys
import os
import threading
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from training_system.training_coordinator import TrainingCoordinator
    from brain_sim.brain_engine import BrainEngine
    from llm_interface.translator import BrainTranslator
    from llm_interface.language_cortex import LanguageCortex
    from brain_sim.advanced_cognitive_brain import AdvancedCognitiveBrain
    from training_system.survival_system import SurvivalSystem
except ImportError as e:
    print(f"Import error: {e}")
    # Set defaults for testing without full backend
    TrainingCoordinator = None
    BrainEngine = None
    BrainTranslator = None
    LanguageCortex = None
    AdvancedCognitiveBrain = None
    SurvivalSystem = None

class FruitFlyDesktopApp:
    """
    Main desktop application for the Fruit Fly AI
    """
    
    def __init__(self, root):
        """
        Initialize the desktop application
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Fruit Fly AI - Desktop Application")
        self.root.geometry("1200x800")
        
        # Application state (initialize before GUI creation)
        self.is_running = False
        self.chat_history = []
        self.viewable_files = set()
        self.created_files = set()
        self.current_file = None
        
        # Initialize backend systems
        self.init_backend_systems()
        
        # Create GUI components
        self.create_menu()
        self.create_main_layout()
        self.create_chat_interface()
        self.create_3d_viewer()
        self.create_file_explorer()
        self.create_training_panel()
        self.create_status_panel()
        
        print("Desktop application initialized")
    
    def init_backend_systems(self):
        """Initialize all backend systems"""
        print("Initializing backend systems...")
        
        try:
            # Initialize training coordinator
            print("Loading training coordinator...")
            self.training_coordinator = TrainingCoordinator()
            print("Training coordinator loaded")
            
            # Skip brain engine for faster startup (it's very large)
            print("Skipping brain engine for faster startup")
            self.brain_engine = None
            
            # Initialize advanced cognitive brain
            print("Loading advanced cognitive brain...")
            self.advanced_brain = AdvancedCognitiveBrain()
            print("Advanced cognitive brain loaded")
            
            # Initialize language cortex
            print("Loading language cortex...")
            self.language_cortex = LanguageCortex(size=500)
            print("Language cortex loaded")
            
            # Initialize survival system
            print("Loading survival system...")
            self.survival_system = SurvivalSystem()
            print("Survival system loaded")
            
            print("Backend systems initialized successfully")
            
        except Exception as e:
            print(f"Error initializing backend systems: {e}")
            self.training_coordinator = None
            self.brain_engine = None
            self.advanced_brain = None
            self.language_cortex = None
            self.survival_system = None
    
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Add to Viewable Files", command=self.add_viewable_file)
        file_menu.add_command(label="Remove from Viewable Files", command=self.remove_viewable_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save Chat History", command=self.save_chat_history)
        file_menu.add_command(label="Load Chat History", command=self.load_chat_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Training menu
        training_menu = tk.Menu(menubar, tearoff=0)
        training_menu.add_command(label="Start Training", command=self.start_training)
        training_menu.add_command(label="Stop Training", command=self.stop_training)
        training_menu.add_command(label="Take Break", command=self.take_break)
        training_menu.add_separator()
        training_menu.add_command(label="Change Language", command=self.change_language)
        training_menu.add_command(label="Change Level", command=self.change_level)
        menubar.add_cascade(label="Training", menu=training_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Toggle 3D Viewer", command=self.toggle_3d_viewer)
        view_menu.add_command(label="Toggle File Explorer", command=self.toggle_file_explorer)
        view_menu.add_command(label="Toggle Training Panel", command=self.toggle_training_panel)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="Contact Support", command=self.contact_support)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_main_layout(self):
        """Create main application layout"""
        # Main container with paned windows
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel (Chat + File Explorer)
        self.left_panel = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.left_panel, weight=1)
        
        # Center panel (3D Viewer)
        self.center_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.center_panel, weight=2)
        
        # Right panel (Training + Status)
        self.right_panel = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.right_panel, weight=1)
    
    def create_chat_interface(self):
        """Create chat interface for user-fly communication"""
        chat_frame = ttk.LabelFrame(self.left_panel, text="Chat Interface")
        self.left_panel.add(chat_frame, weight=2)
        
        # Chat history display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, state='disabled')
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.chat_input.bind("<Return>", self.send_message)
        
        send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
        send_button.pack(side=tk.RIGHT)
        
        # Add system message
        self.add_chat_message("System", "Fruit Fly AI initialized. Ready for communication.")
    
    def create_3d_viewer(self):
        """Create 3D viewer for fly environment"""
        viewer_frame = ttk.LabelFrame(self.center_panel, text="3D Environment Viewer")
        viewer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for 3D visualization
        self.viewer_canvas = tk.Canvas(viewer_frame, bg='black')
        self.viewer_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(viewer_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Reset View", command=self.reset_3d_view).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Toggle Fly", command=self.toggle_fly_display).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Show Food", command=self.show_food_locations).pack(side=tk.LEFT, padx=2)
        
        # Status labels
        self.fly_position_label = ttk.Label(control_frame, text="Fly Position: (0, 0, 0)")
        self.fly_position_label.pack(side=tk.RIGHT, padx=5)
        
        # Draw initial 3D scene
        self.draw_3d_scene()
    
    def create_file_explorer(self):
        """Create controlled file explorer with visibility restrictions"""
        explorer_frame = ttk.LabelFrame(self.left_panel, text="File Explorer (Restricted)")
        self.left_panel.add(explorer_frame, weight=1)
        
        # File list
        self.file_listbox = tk.Listbox(explorer_frame, selectmode=tk.SINGLE)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.file_listbox.bind("<Double-Button-1>", self.open_file)
        
        # Control buttons
        button_frame = ttk.Frame(explorer_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Create File", command=self.create_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Add to Viewable", command=self.add_current_viewable).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Refresh", command=self.refresh_file_list).pack(side=tk.LEFT, padx=2)
        
        # Status
        self.file_status_label = ttk.Label(explorer_frame, text="Viewable files: 0 | Created files: 0")
        self.file_status_label.pack(fill=tk.X, padx=5, pady=2)
        
        # Initialize with current directory
        self.refresh_file_list()
    
    def create_training_panel(self):
        """Create training controls and progress display"""
        training_frame = ttk.LabelFrame(self.right_panel, text="Training System")
        self.right_panel.add(training_frame, weight=2)
        
        # Training status
        status_frame = ttk.Frame(training_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.training_status_label = ttk.Label(status_frame, text="Status: Not Training")
        self.training_status_label.pack(anchor=tk.W)
        
        self.current_lesson_label = ttk.Label(status_frame, text="Lesson: None")
        self.current_lesson_label.pack(anchor=tk.W)
        
        self.language_label = ttk.Label(status_frame, text="Language: Python")
        self.language_label.pack(anchor=tk.W)
        
        self.level_label = ttk.Label(status_frame, text="Level: Beginner")
        self.level_label.pack(anchor=tk.W)
        
        # Progress bar
        ttk.Label(training_frame, text="Training Progress:").pack(anchor=tk.W, padx=5)
        self.progress_bar = ttk.Progressbar(training_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Skill progress
        skill_frame = ttk.LabelFrame(training_frame, text="Skill Progress")
        skill_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.skill_progress_text = scrolledtext.ScrolledText(skill_frame, height=8, state='disabled')
        self.skill_progress_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        control_frame = ttk.Frame(training_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Start Training", command=self.start_training).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Stop Training", command=self.stop_training).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Get Hint", command=self.get_hint).pack(side=tk.LEFT, padx=2)
    
    def create_status_panel(self):
        """Create real-time fly state visualization"""
        status_frame = ttk.LabelFrame(self.right_panel, text="Fly Status")
        self.right_panel.add(status_frame, weight=1)
        
        # Energy display
        energy_frame = ttk.Frame(status_frame)
        energy_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(energy_frame, text="Energy:").pack(side=tk.LEFT)
        self.energy_bar = ttk.Progressbar(energy_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.energy_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.energy_label = ttk.Label(energy_frame, text="100%")
        self.energy_label.pack(side=tk.LEFT)
        
        # Hunger drive
        hunger_frame = ttk.Frame(status_frame)
        hunger_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(hunger_frame, text="Hunger:").pack(side=tk.LEFT)
        self.hunger_bar = ttk.Progressbar(hunger_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.hunger_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.hunger_label = ttk.Label(hunger_frame, text="0%")
        self.hunger_label.pack(side=tk.LEFT)
        
        # Brain activity
        brain_frame = ttk.Frame(status_frame)
        brain_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(brain_frame, text="Brain Activity:").pack(side=tk.LEFT)
        self.brain_bar = ttk.Progressbar(brain_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.brain_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.brain_label = ttk.Label(brain_frame, text="0%")
        self.brain_label.pack(side=tk.LEFT)
        
        # Current behavior
        self.behavior_label = ttk.Label(status_frame, text="Behavior: Resting")
        self.behavior_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Survival status
        self.survival_label = ttk.Label(status_frame, text="Survival: Normal")
        self.survival_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # API usage
        api_frame = ttk.Frame(status_frame)
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(api_frame, text="API Usage:").pack(side=tk.LEFT)
        self.api_bar = ttk.Progressbar(api_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.api_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.api_label = ttk.Label(api_frame, text="0/1000")
        self.api_label.pack(side=tk.LEFT)
        
        # Start status update timer
        self.update_status_display()
    
    def add_chat_message(self, sender, message):
        """Add message to chat display"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        
        self.chat_history.append({"sender": sender, "message": message, "timestamp": time.time()})
    
    def send_message(self, event=None):
        """Send message to fly"""
        message = self.chat_input.get().strip()
        if not message:
            return
        
        # Add user message
        self.add_chat_message("User", message)
        self.chat_input.delete(0, tk.END)
        
        # Process through fly brain
        self.process_user_message(message)
    
    def process_user_message(self, message):
        """Process user message through fly brain systems"""
        # This would integrate with the translator and language cortex
        # For now, provide a simulated response
        
        if self.language_cortex:
            # Process through language cortex
            activation = self.language_cortex.process_input({"user_input": 0.8, "text": 0.6})
            brain_activity = (activation.sum() / len(activation)) * 100
        else:
            brain_activity = 50.0
        
        # Generate response based on message content
        response = self.generate_fly_response(message)
        
        # Add delay to simulate processing
        self.root.after(500, lambda: self.add_chat_message("Fly", response))
    
    def generate_fly_response(self, message):
        """Generate fly response based on message content"""
        message_lower = message.lower()
        
        if "hello" in message_lower or "hi" in message_lower:
            return "Hello! I am ready to learn and help with coding tasks."
        elif "hungry" in message_lower:
            return "I am feeling a bit hungry. Could use some training rewards!"
        elif "code" in message_lower or "program" in message_lower:
            return "I'm ready to code! Let me show you what I've learned."
        elif "train" in message_lower:
            return "I'd love to train! Please start a training session."
        elif "food" in message_lower:
            return "Food sounds good! I need energy to learn effectively."
        elif "help" in message_lower:
            return "I can help with coding in many languages: Python, Rust, C++, JavaScript, TypeScript, and more!"
        else:
            return "I understand you're communicating with me. I'm processing your input through my neural networks."
    
    def draw_3d_scene(self):
        """Draw simplified 3D scene on canvas"""
        self.viewer_canvas.delete("all")
        
        # Draw ground plane
        self.viewer_canvas.create_rectangle(50, 400, 750, 450, fill='#2d5a27', outline='#1a3d17')
        
        # Draw food locations (corners)
        food_locations = [
            (60, 390),  # Top-left
            (740, 390), # Top-right
            (60, 440),  # Bottom-left
            (740, 440)  # Bottom-right
        ]
        
        for x, y in food_locations:
            self.viewer_canvas.create_oval(x-10, y-10, x+10, y+10, fill='#ff6b6b', outline='#c92a2a')
        
        # Draw fly (center)
        fly_x, fly_y = 400, 425
        self.viewer_canvas.create_oval(fly_x-15, fly_y-8, fly_x+15, fly_y+8, fill='#4ecdc4', outline='#2a9d8f')
        self.viewer_canvas.create_oval(fly_x-20, fly_y-3, fly_x-15, fly_y+3, fill='#4ecdc4', outline='#2a9d8f')  # Left wing
        self.viewer_canvas.create_oval(fly_x+15, fly_y-3, fly_x+20, fly_y+3, fill='#4ecdc4', outline='#2a9d8f')  # Right wing
        
        # Draw walls
        self.viewer_canvas.create_line(50, 100, 50, 450, fill='#666', width=3)  # Left wall
        self.viewer_canvas.create_line(750, 100, 750, 450, fill='#666', width=3)  # Right wall
        self.viewer_canvas.create_line(50, 100, 750, 100, fill='#666', width=3)  # Back wall
        
        # Add labels
        self.viewer_canvas.create_text(400, 50, text="3D Environment - 100x100x50 units", fill='white')
        self.viewer_canvas.create_text(60, 370, text="Food", fill='#ff6b6b', font=('Arial', 8))
    
    def reset_3d_view(self):
        """Reset 3D view to default"""
        self.draw_3d_scene()
    
    def toggle_fly_display(self):
        """Toggle fly display in 3D viewer"""
        # Toggle fly visibility (simplified)
        pass
    
    def show_food_locations(self):
        """Highlight food locations in 3D viewer"""
        # Highlight food (simplified)
        self.draw_3d_scene()
    
    def refresh_file_list(self):
        """Refresh file explorer list"""
        self.file_listbox.delete(0, tk.END)
        
        # Only show viewable files, created files, and current file
        files_to_show = set()
        files_to_show.update(self.viewable_files)
        files_to_show.update(self.created_files)
        if self.current_file:
            files_to_show.add(self.current_file)
        
        if files_to_show:
            for file in sorted(files_to_show):
                self.file_listbox.insert(tk.END, file)
        else:
            self.file_listbox.insert(tk.END, "(No viewable files)")
        
        self.update_file_status()
    
    def update_file_status(self):
        """Update file status label"""
        self.file_status_label.config(
            text=f"Viewable files: {len(self.viewable_files)} | Created files: {len(self.created_files)}"
        )
    
    def add_viewable_file(self):
        """Add file to viewable list"""
        file_path = filedialog.askopenfilename(
            title="Select file to add to viewable list",
            filetypes=[("All files", "*.*")]
        )
        
        if file_path:
            # Convert to relative path if possible
            if file_path.startswith(os.getcwd()):
                file_path = os.path.relpath(file_path, os.getcwd())
            
            self.viewable_files.add(file_path)
            self.refresh_file_list()
            self.add_chat_message("System", f"Added {file_path} to viewable files")
    
    def remove_viewable_file(self):
        """Remove file from viewable list"""
        selection = self.file_listbox.curselection()
        if selection:
            file_name = self.file_listbox.get(selection[0])
            if file_name in self.viewable_files:
                self.viewable_files.remove(file_name)
                self.refresh_file_list()
                self.add_chat_message("System", f"Removed {file_name} from viewable files")
    
    def add_current_viewable(self):
        """Add currently selected file to viewable list"""
        selection = self.file_listbox.curselection()
        if selection:
            file_name = self.file_listbox.get(selection[0])
            self.viewable_files.add(file_name)
            self.update_file_status()
            self.add_chat_message("System", f"Added {file_name} to viewable files")
    
    def create_file(self):
        """Create new file"""
        file_path = filedialog.asksaveasfilename(
            title="Create new file",
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        if file_path:
            # Convert to relative path if possible
            if file_path.startswith(os.getcwd()):
                file_path = os.path.relpath(file_path, os.getcwd())
            
            # Create empty file
            try:
                with open(file_path, 'w') as f:
                    f.write("# New file created by Fruit Fly AI\n")
                
                self.created_files.add(file_path)
                self.current_file = file_path
                self.refresh_file_list()
                self.add_chat_message("System", f"Created new file: {file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create file: {e}")
    
    def open_file(self, event):
        """Open selected file"""
        selection = self.file_listbox.curselection()
        if selection:
            file_name = self.file_listbox.get(selection[0])
            
            # Check if file is viewable
            is_viewable = (file_name in self.viewable_files or 
                          file_name in self.created_files or 
                          file_name == self.current_file)
            
            if not is_viewable:
                messagebox.showwarning("Access Denied", "This file is not in your viewable list.")
                return
            
            self.current_file = file_name
            self.add_chat_message("System", f"Opened file: {file_name}")
    
    def start_training(self):
        """Start training session"""
        if not self.training_coordinator:
            messagebox.showerror("Error", "Training system not available")
            return
        
        # Simulate hunger first
        if self.survival_system:
            self.survival_system.hunger_mechanics.update_hunger(50.0, activity_level=0.5)
        
        result = self.training_coordinator.start_training("python", "beginner")
        
        if result["success"]:
            self.training_status_label.config(text="Status: Training")
            self.current_lesson_label.config(text=f"Lesson: {result['lesson']}")
            self.language_label.config(text=f"Language: {result['language']}")
            self.level_label.config(text=f"Level: {result['level']}")
            self.add_chat_message("System", f"Training started: {result['language']} - {result['level']}")
        else:
            messagebox.showerror("Error", f"Failed to start training: {result['reason']}")
    
    def stop_training(self):
        """Stop training session"""
        if not self.training_coordinator:
            return
        
        result = self.training_coordinator.stop_training("User stopped")
        
        if result["success"]:
            self.training_status_label.config(text="Status: Not Training")
            self.add_chat_message("System", "Training stopped")
    
    def take_break(self):
        """Take a break from training"""
        if not self.training_coordinator:
            return
        
        result = self.training_coordinator.take_break(60.0)
        
        if result["success"]:
            self.add_chat_message("System", f"Took a {result['duration']}s break. Energy: {result['new_energy']:.1f}")
    
    def change_language(self):
        """Change training language"""
        if not self.training_coordinator:
            return
        
        # Simple dialog for language selection
        languages = ["python", "typescript", "javascript", "rust", "c++", "c#", "go", "java"]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Language")
        dialog.geometry("300x400")
        
        ttk.Label(dialog, text="Select Programming Language:").pack(pady=10)
        
        for lang in languages:
            ttk.Button(dialog, text=lang.capitalize(), 
                      command=lambda l=lang: self._set_language(l, dialog)).pack(pady=2)
    
    def _set_language(self, language, dialog):
        """Set the training language"""
        result = self.training_coordinator.change_language(language)
        
        if result["success"]:
            self.language_label.config(text=f"Language: {result['language']}")
            self.current_lesson_label.config(text=f"Lesson: {result['lesson']}")
            self.add_chat_message("System", f"Changed language to {result['language']}")
        
        dialog.destroy()
    
    def change_level(self):
        """Change training level"""
        if not self.training_coordinator:
            return
        
        levels = ["beginner", "intermediate", "advanced"]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Level")
        dialog.geometry("300x200")
        
        ttk.Label(dialog, text="Select Difficulty Level:").pack(pady=10)
        
        for level in levels:
            ttk.Button(dialog, text=level.capitalize(), 
                      command=lambda l=level: self._set_level(l, dialog)).pack(pady=2)
    
    def _set_level(self, level, dialog):
        """Set the training level"""
        result = self.training_coordinator.change_level(level)
        
        if result["success"]:
            self.level_label.config(text=f"Level: {result['level']}")
            self.current_lesson_label.config(text=f"Lesson: {result['lesson']}")
            self.add_chat_message("System", f"Changed level to {result['level']}")
        
        dialog.destroy()
    
    def get_hint(self):
        """Get hint for current lesson"""
        if not self.training_coordinator:
            return
        
        hint = self.training_coordinator.get_hint()
        self.add_chat_message("System", f"Hint: {hint}")
    
    def update_status_display(self):
        """Update real-time status display"""
        # Update energy bar
        if self.survival_system:
            energy = self.survival_system.hunger_mechanics.energy
            self.energy_bar['value'] = energy
            self.energy_label.config(text=f"{energy:.0f}%")
            
            hunger_drive = self.survival_system.hunger_mechanics.hunger_drive * 100
            self.hunger_bar['value'] = hunger_drive
            self.hunger_label.config(text=f"{hunger_drive:.0f}%")
            
            if self.survival_system.hunger_mechanics.is_starving:
                self.survival_label.config(text="Survival: STARVING", foreground='red')
            else:
                self.survival_label.config(text="Survival: Normal", foreground='black')
        
        # Update brain activity
        if self.language_cortex:
            # Simulate brain activity
            activity = 30 + (time.time() % 30)  # Oscillating between 30-60%
            self.brain_bar['value'] = activity
            self.brain_label.config(text=f"{activity:.0f}%")
        
        # Update API usage
        if self.training_coordinator:
            api_status = self.training_coordinator.api_manager.get_usage_status()
            usage = api_status['current_usage']
            quota = api_status['daily_quota']
            percentage = (usage / quota) * 100
            self.api_bar['value'] = percentage
            self.api_label.config(text=f"{usage}/{quota}")
        
        # Update skill progress
        if self.training_coordinator:
            progress = self.training_coordinator.skill_tracker.get_overall_progress()
            self.skill_progress_text.config(state='normal')
            self.skill_progress_text.delete(1.0, tk.END)
            self.skill_progress_text.insert(tk.END, f"Overall Mastery: {progress['overall_mastery']:.1%}\n")
            self.skill_progress_text.insert(tk.END, f"Languages in Progress: {progress['languages_in_progress']}\n")
            self.skill_progress_text.insert(tk.END, f"Current Streak: {progress['current_streak']}\n")
            self.skill_progress_text.insert(tk.END, f"Best Streak: {progress['best_streak']}\n")
            self.skill_progress_text.config(state='disabled')
        
        # Schedule next update
        self.root.after(1000, self.update_status_display)
    
    def toggle_3d_viewer(self):
        """Toggle 3D viewer visibility"""
        # Simplified toggle
        pass
    
    def toggle_file_explorer(self):
        """Toggle file explorer visibility"""
        # Simplified toggle
        pass
    
    def toggle_training_panel(self):
        """Toggle training panel visibility"""
        # Simplified toggle
        pass
    
    def save_chat_history(self):
        """Save chat history to file"""
        file_path = filedialog.asksaveasfilename(
            title="Save Chat History",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    for msg in self.chat_history:
                        f.write(f"{msg['sender']}: {msg['message']}\n")
                
                messagebox.showinfo("Success", "Chat history saved successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save chat history: {e}")
    
    def load_chat_history(self):
        """Load chat history from file"""
        file_path = filedialog.askopenfilename(
            title="Load Chat History",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                self.chat_display.config(state='normal')
                self.chat_display.delete(1.0, tk.END)
                self.chat_display.insert(tk.END, content)
                self.chat_display.config(state='disabled')
                
                messagebox.showinfo("Success", "Chat history loaded successfully")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load chat history: {e}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
Fruit Fly AI Desktop Application
Version 1.0

A simulated fruit fly brain based on the MaleCNS v1.0 connectome,
enhanced with advanced cognitive capabilities for coding training.

Features:
- 213,077 biological neurons + 1,500 specialized neurons
- Support for 27 programming languages
- Complex mathematical processing capabilities
- Pattern recognition and analysis
- Food-based reward training system
- Controlled file explorer with visibility restrictions
- Real-time 3D environment simulation
- Desktop application with chat interface
- On-the-job learning with local memory management
- Zero-tolerance code evaluation for mistake-free coding

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
        support_email = "smollest.bag@gmail.com"
        
        support_text = f"""
Fruit Fly AI - Support

For support, questions, or feedback, please contact:

Email: {support_email}

When contacting support, please include:
- Description of the issue
- Steps to reproduce the problem
- Your system information
- Screenshots if applicable

Support Hours: 
Monday - Friday: 9:00 AM - 5:00 PM (UTC)
Saturday - Sunday: 10:00 AM - 2:00 PM (UTC)

Response Time: 
Within 24-48 hours for all inquiries
        """
        
        messagebox.showinfo("Contact Support", support_text)
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Stop training if active
            if self.training_coordinator:
                self.training_coordinator.stop_training("Application closing")
            
            self.root.destroy()
            sys.exit(0)


def main():
    """Main application entry point"""
    root = tk.Tk()
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fruit fly.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not load icon: {e}")
    
    app = FruitFlyDesktopApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()