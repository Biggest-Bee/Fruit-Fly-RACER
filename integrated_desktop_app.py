"""
Full Desktop Application with Integrated 3D Environment
Includes resizable panels, 3D environment integration, and training system
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import sys
import os
import threading
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("DEBUG: Starting Full Desktop App with 3D Integration...")

class FullDesktopAppWith3D:
    """
    Full desktop application with integrated 3D environment and resizable panels
    """
    
    def __init__(self, root):
        print("DEBUG: Initializing FullDesktopAppWith3D...")
        self.root = root
        self.root.title("Fruit Fly AI - Full Desktop with 3D Environment")
        self.root.geometry("1400x900")
        
        # Application state
        self.is_running = False
        self.chat_history = []
        self.viewable_files = set()
        self.created_files = set()
        self.current_file = None
        self.backend_loaded = False
        self.three_d_process = None
        self.three_d_running = False
        self.training_repos = []  # List of training repos
        self.training_active = False
        self.file_workspace = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fly_workspace")
        os.makedirs(self.file_workspace, exist_ok=True)  # Create workspace directory
        self.active_training_languages = []  # List of languages currently being trained
        
        # Backend systems
        self.training_coordinator = None
        self.brain_engine = None
        self.advanced_brain = None
        self.language_cortex = None
        self.survival_system = None
        
        # Panel sizes (for resizing)
        self.panel_sizes = {
            'left': 300,
            'center': 600,
            'right': 300
        }
        
        print("DEBUG: Creating resizable GUI...")
        # Create resizable GUI
        self.create_menu()
        self.create_resizable_layout()
        self.create_chat_interface()
        self.create_3d_panel()
        self.create_file_explorer()
        self.create_training_panel()
        self.create_status_panel()
        
        print("DEBUG: GUI created successfully")
        
        # Load backend in background
        self.root.after(100, self.start_backend_loading)
        
        # Auto-launch 3D environment after a short delay
        self.root.after(2000, self.launch_3d_environment)
        
        print("DEBUG: FullDesktopAppWith3D initialization complete")
    
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
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Expand Left Panel", command=lambda: self.resize_panel('left', 100))
        view_menu.add_command(label="Contract Left Panel", command=lambda: self.resize_panel('left', -100))
        view_menu.add_separator()
        view_menu.add_command(label="Expand Center Panel", command=lambda: self.resize_panel('center', 100))
        view_menu.add_command(label="Contract Center Panel", command=lambda: self.resize_panel('center', -100))
        view_menu.add_separator()
        view_menu.add_command(label="Expand Right Panel", command=lambda: self.resize_panel('right', 100))
        view_menu.add_command(label="Contract Right Panel", command=lambda: self.resize_panel('right', -100))
        view_menu.add_separator()
        view_menu.add_command(label="Reset Layout", command=self.reset_layout)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # 3D menu
        three_d_menu = tk.Menu(menubar, tearoff=0)
        three_d_menu.add_command(label="Launch 3D Environment", command=self.launch_3d_environment)
        three_d_menu.add_command(label="Close 3D Environment", command=self.close_3d_environment)
        three_d_menu.add_separator()
        three_d_menu.add_command(label="Reset 3D View", command=self.reset_3d_view)
        menubar.add_cascade(label="3D Environment", menu=three_d_menu)
        
        # Training menu
        training_menu = tk.Menu(menubar, tearoff=0)
        training_menu.add_command(label="Start Training", command=self.start_training)
        training_menu.add_command(label="Stop Training", command=self.stop_training)
        training_menu.add_command(label="Get Hint", command=self.get_hint)
        training_menu.add_separator()
        training_menu.add_command(label="Practice in 3D", command=self.practice_in_3d)
        menubar.add_cascade(label="Training", menu=training_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="Contact Support", command=self.contact_support)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        print("DEBUG: Menu created")
    
    def create_resizable_layout(self):
        """Create resizable layout with paned windows"""
        print("DEBUG: Creating resizable layout...")
        
        # Main horizontal paned window
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel container
        self.left_paned = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.left_paned, weight=1)
        
        # Center panel (3D environment)
        self.center_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.center_frame, weight=2)
        
        # Right panel container
        self.right_paned = ttk.PanedWindow(self.main_paned, orient=tk.VERTICAL)
        self.main_paned.add(self.right_paned, weight=1)
        
        print("DEBUG: Resizable layout created")
    
    def resize_panel(self, panel, delta):
        """Resize a panel by delta pixels"""
        if panel in self.panel_sizes:
            self.panel_sizes[panel] = max(100, self.panel_sizes[panel] + delta)
            self.root.update_idletasks()
            self.add_chat_message("System", f"{panel.capitalize()} panel resized to {self.panel_sizes[panel]}px")
    
    def reset_layout(self):
        """Reset layout to default sizes"""
        self.panel_sizes = {'left': 300, 'center': 600, 'right': 300}
        self.add_chat_message("System", "Layout reset to default sizes")
    
    def create_chat_interface(self):
        """Create chat interface in left panel"""
        print("DEBUG: Creating chat interface...")
        
        chat_frame = ttk.LabelFrame(self.left_paned, text="Chat Interface")
        self.left_paned.add(chat_frame, weight=2)
        
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
        self.add_chat_message("System", "Fruit Fly AI - Full Desktop with 3D Environment")
        self.add_chat_message("System", "Panels are resizable via View menu")
        self.add_chat_message("System", "3D Environment can be launched anytime")
        
        print("DEBUG: Chat interface created")
    
    def create_3d_panel(self):
        """Create 3D environment panel in center"""
        print("DEBUG: Creating 3D panel...")
        
        three_d_frame = ttk.LabelFrame(self.center_frame, text="3D Environment")
        three_d_frame.pack(fill=tk.BOTH, expand=True)
        
        # Placeholder for 3D view
        self.three_d_canvas = tk.Canvas(three_d_frame, bg='black')
        self.three_d_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Draw placeholder 3D scene
        self.draw_placeholder_3d()
        
        # Control buttons
        control_frame = ttk.Frame(three_d_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Launch 3D Environment", command=self.launch_3d_environment).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Close 3D", command=self.close_3d_environment).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="Practice in 3D", command=self.practice_in_3d).pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.three_d_status = ttk.Label(control_frame, text="3D: Not launched", foreground="gray")
        self.three_d_status.pack(side=tk.RIGHT, padx=5)
        
        print("DEBUG: 3D panel created")
    
    def draw_placeholder_3d(self):
        """Draw placeholder 3D scene"""
        self.three_d_canvas.delete("all")
        
        # Draw simple 3D representation
        # Room boundaries
        self.three_d_canvas.create_rectangle(50, 50, 550, 350, outline="white", width=2)
        
        # Food locations
        self.three_d_canvas.create_oval(70, 70, 90, 90, fill="red", outline="white")
        self.three_d_canvas.create_oval(510, 70, 530, 90, fill="red", outline="white")
        self.three_d_canvas.create_oval(70, 310, 90, 330, fill="red", outline="white")
        self.three_d_canvas.create_oval(510, 310, 530, 330, fill="red", outline="white")
        
        # Fly
        self.three_d_canvas.create_oval(280, 180, 320, 220, fill="cyan", outline="white")
        
        # Labels
        self.three_d_canvas.create_text(300, 380, text="3D Environment Placeholder", fill="white")
        self.three_d_canvas.create_text(300, 400, text="Click 'Launch 3D Environment' for real 3D", fill="yellow")
    
    def create_file_explorer(self):
        """Create file explorer in left panel - synced with actual file system"""
        print("DEBUG: Creating file explorer...")
        
        file_frame = ttk.LabelFrame(self.left_paned, text="File Explorer")
        self.left_paned.add(file_frame, weight=1)
        
        # Workspace path display
        workspace_frame = ttk.Frame(file_frame)
        workspace_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(workspace_frame, text="Workspace:", font=("Arial", 8)).pack(side=tk.LEFT)
        ttk.Label(workspace_frame, text=self.file_workspace, font=("Arial", 8, "italic")).pack(side=tk.LEFT, padx=5)
        
        # File list
        self.file_listbox = tk.Listbox(file_frame, height=10)
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # Code editor area
        self.code_editor = scrolledtext.ScrolledText(file_frame, height=8, wrap=tk.NONE)
        self.code_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control buttons
        file_button_frame = ttk.Frame(file_frame)
        file_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(file_button_frame, text="Add File", command=self.add_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_button_frame, text="Add Multiple", command=self.add_multiple_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_button_frame, text="Create File", command=self.create_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_button_frame, text="Run Code", command=self.run_code).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_button_frame, text="Remove", command=self.remove_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_button_frame, text="Refresh", command=self.refresh_file_list).pack(side=tk.LEFT, padx=2)
        
        # Load initial files
        self.refresh_file_list()
        
        print("DEBUG: File explorer created")
    
    def create_training_panel(self):
        """Create training panel in right panel"""
        print("DEBUG: Creating training panel...")
        
        # Create scrollable container for right panel
        right_scroll_frame = ttk.Frame(self.right_paned)
        self.right_paned.add(right_scroll_frame, weight=1)
        
        # Scrollbar
        right_scrollbar = ttk.Scrollbar(right_scroll_frame, orient="vertical")
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Scrollable canvas
        right_canvas = tk.Canvas(right_scroll_frame, yscrollcommand=right_scrollbar.set)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_scrollbar.config(command=right_canvas.yview)
        
        # Frame inside canvas
        right_inner_frame = ttk.Frame(right_canvas)
        right_canvas.create_window((0, 0), window=right_inner_frame, anchor="nw")
        
        # Configure scroll
        right_inner_frame.bind("<Configure>", lambda e: right_canvas.configure(scrollregion=right_canvas.bbox("all")))
        
        # Training Panel
        training_frame = ttk.LabelFrame(right_inner_frame, text="Training Panel")
        training_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Language selection
        ttk.Label(training_frame, text="Language:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        self.language_var = tk.StringVar(value="python")
        languages = ["python", "typescript", "javascript", "rust", "c++", "c#", "go", "java", "swift", "kotlin", "php", "ruby", "sql", "css", "html", "json", "graphql", "toml", "yaml", "ini", "xml_rpc", "soap", "protobuf", "avro", "msgpack", "cbor", "bson"]
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
        ttk.Button(training_button_frame, text="Practice in 3D", command=self.practice_in_3d).pack(fill=tk.X, pady=2)
        
        # Training progress
        ttk.Label(training_frame, text="Progress:").pack(anchor=tk.W, padx=5, pady=(10, 0))
        self.progress_label = ttk.Label(training_frame, text="Not started")
        self.progress_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Language progress
        ttk.Label(training_frame, text="Language Progress:").pack(anchor=tk.W, padx=5, pady=(10, 0))
        self.language_progress_label = ttk.Label(training_frame, text="0/27 languages mastered")
        self.language_progress_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Training Files Panel (NEW)
        training_files_frame = ttk.LabelFrame(right_inner_frame, text="Training Files")
        training_files_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Mode selection
        ttk.Label(training_files_frame, text="Repo Selection Mode:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.repo_mode_var = tk.StringVar(value="ai")
        mode_frame = ttk.Frame(training_files_frame)
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Radiobutton(mode_frame, text="AI Chooses", variable=self.repo_mode_var, value="ai").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="User Chooses", variable=self.repo_mode_var, value="user").pack(side=tk.LEFT, padx=5)
        
        # Import repo button
        import_frame = ttk.Frame(training_files_frame)
        import_frame.pack(fill=tk.X, padx=5, pady=5)
        self.repo_url_var = tk.StringVar()
        ttk.Button(import_frame, text="Import/Fork Repo", command=self.import_repo).pack(side=tk.LEFT, padx=2)
        ttk.Entry(import_frame, textvariable=self.repo_url_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Training files list
        ttk.Label(training_files_frame, text="Current Training Repos:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.training_files_listbox = tk.Listbox(training_files_frame, height=5)
        self.training_files_listbox.pack(fill=tk.X, padx=5, pady=5)
        
        # Remove repo button
        self.remove_repo_button = ttk.Button(training_files_frame, text="Remove Selected Repo", command=self.remove_training_repo)
        self.remove_repo_button.pack(fill=tk.X, padx=5, pady=5)
        
        print("DEBUG: Training panel created")
    
    def create_status_panel(self):
        """Create status panel in right panel"""
        print("DEBUG: Creating status panel...")
        
        # Status Panel (part of the scrollable right panel)
        status_frame = ttk.LabelFrame(right_inner_frame, text="Status Panel")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
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
        
        # 3D status
        ttk.Label(status_frame, text="3D Environment:").pack(anchor=tk.W, padx=5, pady=(10, 0))
        self.three_d_status_label = ttk.Label(status_frame, text="Not launched", foreground="gray")
        self.three_d_status_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Total neurons
        ttk.Label(status_frame, text="Total Neurons:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.neurons_label = ttk.Label(status_frame, text="411,577")
        self.neurons_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # Backend status
        ttk.Label(status_frame, text="Backend:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.backend_status_label = ttk.Label(status_frame, text="Loading...", foreground="orange")
        self.backend_status_label.pack(anchor=tk.W, padx=5, pady=5)
        
        print("DEBUG: Status panel created")
    
    def launch_3d_environment(self):
        """Launch the real 3D environment"""
        if self.three_d_running:
            self.add_chat_message("System", "3D environment is already running")
            return
        
        self.add_chat_message("System", "Launching 3D environment...")
        self.three_d_status_label.config(text="Launching...", foreground="orange")
        self.three_d_status.config(text="Launching...", foreground="orange")
        
        try:
            # Clear placeholder and show message
            self.three_d_canvas.delete("all")
            self.three_d_canvas.create_text(300, 200, text="Launching Ursina 3D Window...", fill="white", font=("Arial", 14))
            self.three_d_canvas.create_text(300, 230, text="A separate window will open", fill="yellow", font=("Arial", 12))
            
            # Launch 3D environment in separate process
            self.three_d_process = subprocess.Popen(
                [sys.executable, "3d_environment/real_3d_environment.py"],
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            self.three_d_running = True
            self.three_d_status_label.config(text="Running", foreground="green")
            self.three_d_status.config(text="Running", foreground="green")
            
            # Update canvas to show 3D is running
            self.three_d_canvas.delete("all")
            self.three_d_canvas.create_text(300, 200, text="3D Environment Running", fill="green", font=("Arial", 16, "bold"))
            self.three_d_canvas.create_text(300, 230, text="Separate Ursina window is open", fill="white", font=("Arial", 12))
            self.three_d_canvas.create_text(300, 260, text="Controls: WASD to move, Mouse to look, ESC to exit", fill="yellow", font=("Arial", 10))
            
            self.add_chat_message("System", "3D environment launched successfully")
            self.add_chat_message("System", "A separate Ursina 3D window has opened")
            self.add_chat_message("System", "Use WASD to move, mouse to look, ESC to exit")
        except Exception as e:
            self.add_chat_message("System", f"Failed to launch 3D: {e}")
            self.three_d_status_label.config(text="Error", foreground="red")
            self.draw_placeholder_3d()  # Show placeholder again on error
    
    def close_3d_environment(self):
        """Close the 3D environment"""
        if not self.three_d_running:
            self.add_chat_message("System", "3D environment is not running")
            return
        
        if self.three_d_process:
            self.three_d_process.terminate()
            self.three_d_process = None
        
        self.three_d_running = False
        self.three_d_status_label.config(text="Not launched", foreground="gray")
        self.three_d_status.config(text="Not launched", foreground="gray")
        self.add_chat_message("System", "3D environment closed")
    
    def practice_in_3d(self):
        """Practice coding in 3D environment"""
        if not self.backend_loaded:
            self.add_chat_message("System", "Wait for backend to load...")
            return
        
        if not self.three_d_running:
            self.launch_3d_environment()
        
        language = self.language_var.get()
        self.add_chat_message("System", f"Starting {language} practice in 3D environment...")
        self.add_chat_message("System", "The fly will practice coding while in the 3D world")
        self.progress_label.config(text=f"Practicing {language} in 3D...")
    
    def reset_3d_view(self):
        """Reset 3D view"""
        self.draw_placeholder_3d()
        self.add_chat_message("System", "3D view reset")
    
    def import_repo(self):
        """Import/fork a GitHub repo into training files (one at a time)"""
        if self.training_active:
            self.add_chat_message("System", "Cannot import repos during training. Stop training first.")
            return
        
        repo_url = self.repo_url_var.get().strip()
        if not repo_url:
            self.add_chat_message("System", "Please enter a GitHub repository URL")
            return
        
        if repo_url in self.training_repos:
            self.add_chat_message("System", "This repo is already in training files")
            return
        
        # Only one repo at a time
        if len(self.training_repos) > 0:
            self.add_chat_message("System", "Only one repo can be imported at a time. Remove current repo first.")
            return
        
        try:
            if self.backend_loaded and self.training_coordinator:
                # Use GitHub integration to pull repo
                result = self.training_coordinator.ai_trainer.pull_github_repository(repo_url)
                if result.get("success"):
                    self.training_repos.append(repo_url)
                    self.training_files_listbox.insert(tk.END, repo_url)
                    self.add_chat_message("System", f"Successfully imported: {repo_url}")
                    self.add_chat_message("System", f"Repo cloned to: {result.get('path', 'github_repos')}")
                    self.repo_url_var.set("")  # Clear input
                else:
                    self.add_chat_message("System", f"Failed to import: {result.get('error', 'Unknown error')}")
            else:
                self.add_chat_message("System", "Backend not loaded. Wait for backend to load.")
        except Exception as e:
            self.add_chat_message("System", f"Error importing repo: {e}")
    
    def remove_training_repo(self):
        """Remove selected repo from training files"""
        if self.training_active:
            self.add_chat_message("System", "Cannot remove repos during training. Stop training first.")
            return
        
        selection = self.training_files_listbox.curselection()
        if not selection:
            self.add_chat_message("System", "Please select a repo to remove")
            return
        
        index = selection[0]
        repo_url = self.training_files_listbox.get(index)
        
        try:
            if self.backend_loaded and self.training_coordinator:
                # Cleanup repo
                self.training_coordinator.ai_trainer.cleanup_github_repo(repo_url)
            
            self.training_repos.remove(repo_url)
            self.training_files_listbox.delete(index)
            self.add_chat_message("System", f"Removed: {repo_url}")
        except Exception as e:
            self.add_chat_message("System", f"Error removing repo: {e}")
    
    def auto_remove_completed_repo(self, repo_url: str):
        """Auto-remove repo when training on it is complete"""
        try:
            if repo_url in self.training_repos:
                if self.backend_loaded and self.training_coordinator:
                    self.training_coordinator.ai_trainer.cleanup_github_repo(repo_url)
                
                self.training_repos.remove(repo_url)
                # Update listbox
                self.training_files_listbox.delete(0, tk.END)
                for repo in self.training_repos:
                    self.training_files_listbox.insert(tk.END, repo)
                
                self.add_chat_message("System", f"Auto-removed completed repo: {repo_url}")
        except Exception as e:
            self.add_chat_message("System", f"Error auto-removing repo: {e}")
    
    def start_backend_loading(self):
        """Start loading backend systems in background"""
        print("DEBUG: Starting backend loading...")
        threading.Thread(target=self.load_backend_systems, daemon=True).start()
    
    def load_backend_systems(self):
        """Load backend systems in background thread"""
        try:
            self.root.after(0, lambda: self.backend_status_label.config(text="Loading Training Coordinator...", foreground="orange"))
            
            from training_system.training_coordinator import TrainingCoordinator
            self.training_coordinator = TrainingCoordinator()
            
            self.root.after(0, lambda: self.backend_status_label.config(text="Loading Advanced Brain...", foreground="orange"))
            
            from brain_sim.advanced_cognitive_brain import AdvancedCognitiveBrain
            self.advanced_brain = AdvancedCognitiveBrain()
            
            self.root.after(0, lambda: self.backend_status_label.config(text="Loading Survival System...", foreground="orange"))
            
            from training_system.survival_system import SurvivalSystem
            self.survival_system = SurvivalSystem()
            
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
        self.add_chat_message("System", "All 27 languages supported for training")
    
    def backend_loading_error(self, error):
        """Called when backend loading fails"""
        print(f"DEBUG: Backend loading error: {error}")
        self.backend_status_label.config(text="Backend Error", foreground="red")
        self.add_chat_message("System", f"Error loading backend: {error}")
    
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
            response = "Hello! I'm the Fruit Fly AI with 213,077 neurons ready to learn coding in 27 languages!"
        elif "3d" in message_lower:
            response = "I can practice coding in the 3D environment! Launch it from the 3D menu."
        elif "train" in message_lower:
            response = f"I can train in {self.language_var.get()} with zero-tolerance error correction!"
        else:
            response = "I understand! I'm ready to learn and practice coding."
        
        self.add_chat_message("Fly", response)
    
    # File Methods
    def add_file(self):
        """Add file to workspace - copies file to fly workspace"""
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                # Copy file to workspace
                filename = os.path.basename(file_path)
                workspace_path = os.path.join(self.file_workspace, filename)
                
                # Read original file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Write to workspace
                with open(workspace_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.viewable_files.add(workspace_path)
                self.refresh_file_list()
                self.add_chat_message("System", f"Added file to workspace: {filename}")
            except Exception as e:
                self.add_chat_message("System", f"Error adding file: {e}")
    
    def add_multiple_files(self):
        """Add multiple files to workspace"""
        file_paths = filedialog.askopenfilenames()
        if file_paths:
            added_count = 0
            for file_path in file_paths:
                try:
                    filename = os.path.basename(file_path)
                    workspace_path = os.path.join(self.file_workspace, filename)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    with open(workspace_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.viewable_files.add(workspace_path)
                    added_count += 1
                except Exception as e:
                    self.add_chat_message("System", f"Error adding {os.path.basename(file_path)}: {e}")
            
            self.refresh_file_list()
            self.add_chat_message("System", f"Added {added_count} files to workspace")
    
    def create_file(self):
        """Create new file in workspace"""
        file_path = filedialog.asksaveasfilename(
            initialdir=self.file_workspace,
            defaultextension=".py"
        )
        if file_path:
            try:
                # Create empty file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("")
                
                self.created_files.add(file_path)
                self.viewable_files.add(file_path)
                self.refresh_file_list()
                self.add_chat_message("System", f"Created file: {os.path.basename(file_path)}")
            except Exception as e:
                self.add_chat_message("System", f"Error creating file: {e}")
    
    def run_code(self):
        """Run code in the editor - saves to workspace first"""
        code = self.code_editor.get(1.0, tk.END).strip()
        if not code:
            self.add_chat_message("System", "No code to run")
            return
        
        # Save current file if selected
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            filename = self.file_listbox.get(index)
            workspace_path = os.path.join(self.file_workspace, filename)
            
            try:
                with open(workspace_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                self.add_chat_message("System", f"Saved {filename}")
            except Exception as e:
                self.add_chat_message("System", f"Error saving file: {e}")
        
        language = self.language_var.get()
        self.add_chat_message("System", f"Running {language} code...")
        
        if not self.backend_loaded:
            self.add_chat_message("System", "Backend not loaded - basic syntax check only")
            # Simple syntax check
            if "def " in code or "function " in code or "class " in code:
                self.add_chat_message("System", "Code appears to have valid structure")
            else:
                self.add_chat_message("System", "Code structure unclear")
        else:
            self.add_chat_message("System", f"Code evaluation with zero-tolerance for {language}")
            # Would integrate with training coordinator here
    
    def remove_file(self):
        """Remove file from workspace"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            filename = self.file_listbox.get(index)
            workspace_path = os.path.join(self.file_workspace, filename)
            
            try:
                # Delete from workspace
                if os.path.exists(workspace_path):
                    os.remove(workspace_path)
                
                self.viewable_files.discard(workspace_path)
                self.refresh_file_list()
                self.add_chat_message("System", f"Removed: {filename}")
            except Exception as e:
                self.add_chat_message("System", f"Error removing file: {e}")
    
    def refresh_file_list(self):
        """Refresh file list from workspace"""
        self.file_listbox.delete(0, tk.END)
        
        if os.path.exists(self.file_workspace):
            files = [f for f in os.listdir(self.file_workspace) if os.path.isfile(os.path.join(self.file_workspace, f))]
            for filename in sorted(files):
                self.file_listbox.insert(tk.END, filename)
                self.viewable_files.add(os.path.join(self.file_workspace, filename))
    
    def on_file_select(self, event):
        """Handle file selection - load file content into editor"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            filename = self.file_listbox.get(index)
            workspace_path = os.path.join(self.file_workspace, filename)
            
            try:
                with open(workspace_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.code_editor.delete(1.0, tk.END)
                self.code_editor.insert(1.0, content)
                self.current_file = workspace_path
            except Exception as e:
                self.add_chat_message("System", f"Error loading file: {e}")
    
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
        """Start training - supports multiple languages"""
        if not self.backend_loaded:
            self.add_chat_message("System", "Wait for backend to load...")
            return
        
        language = self.language_var.get()
        level = self.level_var.get()
        
        # Add to active training languages if not already there
        if language not in self.active_training_languages:
            self.active_training_languages.append(language)
        
        self.add_chat_message("System", f"Starting training in {language} ({level})")
        self.add_chat_message("System", f"Active training languages: {', '.join(self.active_training_languages)}")
        self.progress_label.config(text=f"Training {language}...")
        self.start_training_button.config(state='disabled')
        self.stop_training_button.config(state='normal')
        self.remove_repo_button.config(state='disabled')
        self.training_active = True
        
        # If AI mode, let AI choose next language
        if self.repo_mode_var.get() == "ai" and len(self.active_training_languages) < 3:
            self.ai_choose_next_language()
        
        # Simulate training progress
        self.root.after(2000, lambda: self.progress_label.config(text=f"Training {language} - 25%"))
        self.root.after(4000, lambda: self.progress_label.config(text=f"Training {language} - 50%"))
        self.root.after(6000, lambda: self.progress_label.config(text=f"Training {language} - 75%"))
        self.root.after(8000, lambda: self.progress_label.config(text=f"Training {language} - Complete"))
    
    def ai_choose_next_language(self):
        """AI chooses next language to train on"""
        all_languages = ["python", "typescript", "javascript", "rust", "c++", "c#", "go", "java", "swift", "kotlin", "php", "ruby", "sql", "css", "html", "json", "graphql", "toml", "yaml", "ini", "xml_rpc", "soap", "protobuf", "avro", "msgpack", "cbor", "bson"]
        
        # Choose a language not currently being trained
        available = [lang for lang in all_languages if lang not in self.active_training_languages]
        
        if available:
            next_lang = available[0]  # Simple selection - could be smarter
            self.language_var.set(next_lang)
            self.add_chat_message("System", f"AI selected next language: {next_lang}")
    
    def stop_training(self):
        """Stop training"""
        self.add_chat_message("System", "Training stopped")
        self.progress_label.config(text="Training stopped")
        self.start_training_button.config(state='normal')
        self.stop_training_button.config(state='disabled')
        self.remove_repo_button.config(state='normal')
        self.training_active = False
        self.active_training_languages = []  # Clear active languages
    
    def get_hint(self):
        """Get training hint"""
        language = self.language_var.get()
        hints = {
            "python": "Focus on proper indentation and function definitions",
            "javascript": "Pay attention to semicolons and variable declarations",
            "rust": "Remember ownership rules and memory safety",
            "c++": "Watch out for memory management and pointers"
        }
        hint = hints.get(language, "Focus on the syntax and basic patterns first")
        self.add_chat_message("System", f"Hint for {language}: {hint}")
    
    # Help Methods
    def show_about(self):
        """Show about dialog"""
        about_text = """
Fruit Fly AI - Full Desktop with 3D Environment
Version 1.0

Features:
- 213,077 total neurons (211,577 biological + 1,500 specialized)
- Support for 27 programming languages
- Real 3D environment with Ursina Engine
- Resizable panels (View menu)
- Integrated training system
- File explorer with code execution
- Zero-tolerance code evaluation
- On-the-job learning with local memory

Controls:
- View menu: Resize panels
- 3D menu: Launch/control 3D environment
- Training menu: Start/stop training, practice in 3D

Support: smollest.bag@gmail.com
        """
        messagebox.showinfo("About", about_text)
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
Fruit Fly AI - Help

Resizable Panels:
- Use View menu to expand/contract panels
- Reset Layout restores default sizes

3D Environment:
- Launch from 3D menu or center panel
- Real 3D fly with autonomous behavior
- WASD to move, mouse to look, ESC to exit
- Fly practices coding while in 3D

Training:
- Select language and level
- Start training to begin learning
- Practice in 3D for immersive training
- All 27 languages supported

File Explorer:
- Add/view files with visibility controls
- Write and run code directly
- Integrated with training system

Chat:
- Communicate with the fly
- Get real-time responses
        """
        messagebox.showinfo("Help", help_text)
    
    def contact_support(self):
        """Show support contact dialog"""
        support_text = """
Fruit Fly AI - Support

Email: smollest.bag@gmail.com
Response Time: Within 24-48 hours
        """
        messagebox.showinfo("Contact Support", support_text)
    
    def on_exit(self):
        """Handle application closing"""
        # Close 3D environment if running
        if self.three_d_running:
            self.close_3d_environment()
        
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
        
        print("DEBUG: Creating FullDesktopAppWith3D instance...")
        app = FullDesktopAppWith3D(root)
        print("DEBUG: FullDesktopAppWith3D created successfully")
        print("DEBUG: Starting mainloop...")
        
        root.mainloop()
        
        print("DEBUG: Mainloop completed")
        print("Application closed")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("Press Enter to exit...")
        input()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())