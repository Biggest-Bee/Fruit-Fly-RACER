"""
Desktop app without backend initialization
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class NoBackendApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fruit Fly AI - No Backend")
        self.root.geometry("800x600")
        
        # Initialize attributes without backend
        self.chat_history = []
        self.viewable_files = set()
        self.created_files = set()
        self.current_file = None
        self.training_coordinator = None
        self.brain_engine = None
        self.advanced_brain = None
        self.language_cortex = None
        self.survival_system = None
        
        self.create_interface()
        
    def create_interface(self):
        # Menu
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Chat interface
        chat_frame = ttk.LabelFrame(main_container, text="Chat Interface")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.chat_display = tk.Text(chat_frame, height=15, state='disabled')
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(input_frame, text="Send", command=self.send_message).pack(side=tk.RIGHT, padx=5)
        
        # Status panel
        status_frame = ttk.LabelFrame(main_container, text="Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Backend: Disabled | Mode: Standalone")
        self.status_label.pack(pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_container)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Load Backend", command=self.load_backend).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="About", command=self.show_about).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.on_exit).pack(side=tk.LEFT, padx=5)
        
        # Add welcome message
        self.add_message("System", "Fruit Fly AI - Backend disabled for testing")
        
    def add_message(self, sender, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        self.chat_history.append({"sender": sender, "message": message})
        
    def send_message(self):
        message = self.chat_input.get()
        if message:
            self.add_message("You", message)
            self.chat_input.delete(0, tk.END)
            
            if self.training_coordinator:
                self.add_message("Fly", "Backend is loaded - processing message...")
            else:
                self.add_message("Fly", "Backend not loaded - click 'Load Backend' to enable full functionality")
        
    def load_backend(self):
        """Load backend systems"""
        self.status_label.config(text="Loading backend...", foreground="orange")
        self.root.update()
        
        try:
            from training_system.training_coordinator import TrainingCoordinator
            self.training_coordinator = TrainingCoordinator()
            
            from brain_sim.advanced_cognitive_brain import AdvancedCognitiveBrain
            self.advanced_brain = AdvancedCognitiveBrain()
            
            from training_system.survival_system import SurvivalSystem
            self.survival_system = SurvivalSystem()
            
            self.status_label.config(text="Backend: Loaded | Mode: Full", foreground="green")
            self.add_message("System", "Backend systems loaded successfully!")
            
        except Exception as e:
            self.status_label.config(text="Backend: Error", foreground="red")
            self.add_message("System", f"Error loading backend: {e}")
            messagebox.showerror("Backend Error", f"Failed to load backend: {e}")
        
    def show_about(self):
        messagebox.showinfo("About", "Fruit Fly AI - Desktop Application\n\nBackend systems can be loaded on demand.")
        
    def on_exit(self):
        if messagebox.askokcancel("Exit", "Exit application?"):
            self.root.destroy()

def main():
    print("Starting Fruit Fly AI without backend...")
    try:
        root = tk.Tk()
        app = NoBackendApp(root)
        print("Application started successfully")
        root.mainloop()
        print("Application closed")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()