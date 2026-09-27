"""
Ultra-Simple Desktop App - No Backend Loading
Just the GUI, backend loaded manually on demand
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("DEBUG: Starting Ultra-Simple App...")
print("DEBUG: Python version:", sys.version)
print("DEBUG: Tkinter available:", tk.TkVersion)

class UltraSimpleApp:
    def __init__(self, root):
        print("DEBUG: Initializing UltraSimpleApp...")
        self.root = root
        self.root.title("Fruit Fly AI - Simple")
        self.root.geometry("700x500")
        
        print("DEBUG: Setting up state variables...")
        # State
        self.chat_history = []
        self.backend_systems = {}
        
        print("DEBUG: Creating minimal GUI...")
        # Create minimal GUI
        self.create_minimal_gui()
        
        print("DEBUG: GUI creation complete")
        
    def create_minimal_gui(self):
        """Create minimal GUI without any backend loading"""
        print("DEBUG: Creating title frame...")
        # Simple title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(title_frame, text="Fruit Fly AI", font=("Arial", 16)).pack()
        ttk.Label(title_frame, text="Desktop Application").pack()
        
        print("DEBUG: Creating status label...")
        # Status
        self.status_label = ttk.Label(title_frame, text="Status: Ready - No Backend Loaded", foreground="blue")
        self.status_label.pack(pady=5)
        
        print("DEBUG: Creating chat area...")
        # Chat area
        chat_frame = ttk.LabelFrame(self.root, text="Chat")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.chat_display = tk.Text(chat_frame, height=12, state='disabled', wrap=tk.WORD)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        print("DEBUG: Creating input area...")
        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(input_frame, text="Send", command=self.send_message).pack(side=tk.RIGHT)
        
        print("DEBUG: Creating control buttons...")
        # Control buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Load Backend", command=self.load_backend).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Status", command=self.show_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_chat).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.on_exit).pack(side=tk.RIGHT, padx=5)
        
        print("DEBUG: Adding welcome message...")
        # Welcome message
        self.add_message("System", "Fruit Fly AI - Simple Mode")
        self.add_message("System", "Click 'Load Backend' to enable full features")
        
        print("DEBUG: GUI creation complete")
        
    def create_minimal_gui(self):
        """Create minimal GUI without any backend loading"""
        # Simple title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(title_frame, text="Fruit Fly AI", font=("Arial", 16)).pack()
        ttk.Label(title_frame, text="Desktop Application").pack()
        
        # Status
        self.status_label = ttk.Label(title_frame, text="Status: Ready - No Backend Loaded", foreground="blue")
        self.status_label.pack(pady=5)
        
        # Chat area
        chat_frame = ttk.LabelFrame(self.root, text="Chat")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.chat_display = tk.Text(chat_frame, height=12, state='disabled', wrap=tk.WORD)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(input_frame, text="Send", command=self.send_message).pack(side=tk.RIGHT)
        
        # Control buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Load Backend", command=self.load_backend).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Status", command=self.show_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_chat).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.on_exit).pack(side=tk.RIGHT, padx=5)
        
        # Welcome message
        self.add_message("System", "Fruit Fly AI - Simple Mode")
        self.add_message("System", "Click 'Load Backend' to enable full features")
        
    def add_message(self, sender, message):
        """Add message to chat"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        self.chat_history.append({"sender": sender, "message": message})
        
    def load_backend(self):
        """Load backend systems"""
        self.status_label.config(text="Loading backend...", foreground="orange")
        self.root.update()
        
        try:
            self.add_message("System", "Loading backend systems...")
            
            # Load training coordinator
            from training_system.training_coordinator import TrainingCoordinator
            self.backend_systems['coordinator'] = TrainingCoordinator()
            self.add_message("System", "Training Coordinator loaded")
            
            # Load advanced brain
            from brain_sim.advanced_cognitive_brain import AdvancedCognitiveBrain
            self.backend_systems['brain'] = AdvancedCognitiveBrain()
            self.add_message("System", "Advanced Cognitive Brain loaded")
            
            # Load survival system
            from training_system.survival_system import SurvivalSystem
            self.backend_systems['survival'] = SurvivalSystem()
            self.add_message("System", "Survival System loaded")
            
            self.status_label.config(text="Status: Backend Loaded", foreground="green")
            self.add_message("System", "All backend systems loaded successfully!")
            
        except Exception as e:
            self.status_label.config(text="Status: Error", foreground="red")
            self.add_message("System", f"Error loading backend: {e}")
            messagebox.showerror("Error", f"Failed to load backend: {e}")
    
    def show_status(self):
        """Show current status"""
        status = f"Backend Systems Loaded: {len(self.backend_systems)}\n"
        status += f"Chat Messages: {len(self.chat_history)}\n"
        
        if self.backend_systems:
            status += "\nLoaded Systems:\n"
            for name in self.backend_systems.keys():
                status += f"  - {name}\n"
        else:
            status += "\nNo backend systems loaded.\nClick 'Load Backend' to enable features."
        
        messagebox.showinfo("Status", status)
        
    def send_message(self):
        """Send chat message"""
        message = self.chat_input.get().strip()
        if not message:
            return
            
        self.add_message("You", message)
        self.chat_input.delete(0, tk.END)
        
        if not self.backend_systems:
            self.add_message("System", "Backend not loaded. Click 'Load Backend' first.")
            return
        
        # Simple responses
        message_lower = message.lower()
        if "hello" in message_lower or "hi" in message_lower:
            response = "Hello! I'm the Fruit Fly AI with 213,077 neurons ready to learn coding!"
        elif "backend" in message_lower:
            response = f"I have {len(self.backend_systems)} backend systems loaded and ready."
        elif "train" in message_lower:
            response = "I can train in 27 programming languages with zero-tolerance error correction!"
        else:
            response = "I understand! I'm a simulated fruit fly brain enhanced for coding and learning."
        
        self.add_message("Fly", response)
        
    def clear_chat(self):
        """Clear chat"""
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state='disabled')
        self.chat_history = []
        self.add_message("System", "Chat cleared")
        
    def on_exit(self):
        """Exit"""
        if messagebox.askokcancel("Exit", "Exit?"):
            self.root.destroy()

def main():
    print("DEBUG: Starting main function...")
    
    try:
        print("DEBUG: Creating Tk root...")
        root = tk.Tk()
        print("DEBUG: Tk root created successfully")
        
        # Set icon
        icon_path = os.path.join(os.path.dirname(__file__), "fruit fly.ico")
        if os.path.exists(icon_path):
            try:
                root.iconbitmap(icon_path)
                print("DEBUG: Icon loaded successfully")
            except Exception as e:
                print(f"DEBUG: Could not load icon: {e}")
        
        print("DEBUG: Creating UltraSimpleApp instance...")
        app = UltraSimpleApp(root)
        print("DEBUG: UltraSimpleApp created successfully")
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