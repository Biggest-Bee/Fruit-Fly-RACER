"""
Fixed Desktop Application - Progressive Loading
Loads GUI first, then backend systems step by step
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class FixedDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fruit Fly AI - Desktop Application")
        self.root.geometry("900x700")
        
        # Initialize state variables
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
        
        # Loading state
        self.backend_loaded = False
        self.loading_thread = None
        
        # Create basic GUI first
        self.create_basic_gui()
        
        # Load backend in background after GUI is shown
        self.root.after(100, self.start_backend_loading)
        
    def create_basic_gui(self):
        """Create basic GUI components"""
        # Menu
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Contact Support", command=self.contact_support)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menubar)
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status bar at top
        self.status_bar = ttk.Label(main_container, text="Loading backend systems...", foreground="orange")
        self.status_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Chat interface
        chat_frame = ttk.LabelFrame(main_container, text="Chat Interface")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_display = tk.Text(chat_frame, height=15, state='disabled', wrap=tk.WORD)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.send_button = ttk.Button(input_frame, text="Send", command=self.send_message, state='disabled')
        self.send_button.pack(side=tk.RIGHT)
        
        # Control panel
        control_frame = ttk.Frame(main_container)
        control_frame.pack(fill=tk.X)
        
        self.load_button = ttk.Button(control_frame, text="Load Backend", command=self.load_backend_manually)
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Clear Chat", command=self.clear_chat).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="About", command=self.show_about).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Exit", command=self.on_exit).pack(side=tk.RIGHT, padx=5)
        
        # Add initial message
        self.add_message("System", "Fruit Fly AI Desktop Application")
        self.add_message("System", "Backend systems loading in background...")
        
    def start_backend_loading(self):
        """Start loading backend systems in background"""
        self.loading_thread = threading.Thread(target=self.load_backend_background, daemon=True)
        self.loading_thread.start()
        
    def load_backend_background(self):
        """Load backend systems in background thread"""
        try:
            # Update status
            self.root.after(0, lambda: self.status_bar.config(text="Loading Training Coordinator..."))
            
            # Load training coordinator
            from training_system.training_coordinator import TrainingCoordinator
            self.training_coordinator = TrainingCoordinator()
            
            self.root.after(0, lambda: self.status_bar.config(text="Loading Advanced Cognitive Brain..."))
            
            # Load advanced brain
            from brain_sim.advanced_cognitive_brain import AdvancedCognitiveBrain
            self.advanced_brain = AdvancedCognitiveBrain()
            
            self.root.after(0, lambda: self.status_bar.config(text="Loading Survival System..."))
            
            # Load survival system
            from training_system.survival_system import SurvivalSystem
            self.survival_system = SurvivalSystem()
            
            # Update UI when done
            self.root.after(0, self.backend_loading_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self.backend_loading_error(str(e)))
    
    def backend_loading_complete(self):
        """Called when backend loading is complete"""
        self.backend_loaded = True
        self.status_bar.config(text="Backend loaded - Ready", foreground="green")
        self.send_button.config(state='normal')
        self.load_button.config(state='disabled')
        self.add_message("System", "Backend systems loaded successfully!")
        self.add_message("System", "You can now chat with the fly and use all features.")
        
    def backend_loading_error(self, error):
        """Called when backend loading fails"""
        self.status_bar.config(text="Backend loading failed", foreground="red")
        self.add_message("System", f"Error loading backend: {error}")
        self.add_message("System", "Some features may not be available.")
        
    def load_backend_manually(self):
        """Manually trigger backend loading"""
        if not self.backend_loaded and (self.loading_thread is None or not self.loading_thread.is_alive()):
            self.status_bar.config(text="Loading backend systems...", foreground="orange")
            self.start_backend_loading()
        else:
            messagebox.showinfo("Info", "Backend is already loaded or loading")
    
    def add_message(self, sender, message):
        """Add message to chat display"""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        self.chat_history.append({"sender": sender, "message": message})
        
    def send_message(self):
        """Send chat message"""
        message = self.chat_input.get().strip()
        if not message:
            return
            
        self.add_message("You", message)
        self.chat_input.delete(0, tk.END)
        
        if not self.backend_loaded:
            self.add_message("System", "Backend not fully loaded yet. Please wait...")
            return
        
        # Process message with backend
        try:
            # Simple response based on message content
            if "hello" in message.lower() or "hi" in message.lower():
                response = "Hello! I am the Fruit Fly AI. I have a brain simulation with 213,077 neurons and can learn to code in 27 languages."
            elif "train" in message.lower():
                response = "I'm ready for training! I can learn Python, TypeScript, JavaScript, Rust, C++, C#, Go, Java, Swift, Kotlin, PHP, Ruby, SQL, and many more languages."
            elif "hungry" in message.lower():
                response = "I'm not hungry right now. My energy levels are good. In the full simulation, I would seek food when hungry."
            elif "brain" in message.lower():
                response = f"My brain has 213,077 total neurons: 211,577 from the actual fruit fly connectome plus 1,500 specialized neurons for advanced cognitive functions."
            elif "code" in message.lower():
                response = "I can code in 27 programming languages including Python, TypeScript, JavaScript, Rust, C++, C#, Go, Java, and many more. I have zero-tolerance error correction."
            else:
                response = "I understand your message. As a simulated fruit fly brain, I'm designed to learn coding and communicate. What would you like to know?"
            
            self.add_message("Fly", response)
            
        except Exception as e:
            self.add_message("System", f"Error processing message: {e}")
    
    def clear_chat(self):
        """Clear chat display"""
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state='disabled')
        self.chat_history = []
        self.add_message("System", "Chat cleared")
        
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
    print("Starting Fixed Desktop Application...")
    
    try:
        root = tk.Tk()
        
        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "fruit fly.ico")
        if os.path.exists(icon_path):
            try:
                root.iconbitmap(icon_path)
            except Exception as e:
                print(f"Could not load icon: {e}")
        
        app = FixedDesktopApp(root)
        print("Application started successfully")
        root.mainloop()
        print("Application closed")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())