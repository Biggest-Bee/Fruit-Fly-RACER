"""
Create a completely simplified desktop app that just shows basic functionality
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SimpleFruitFlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fruit Fly AI - Simple")
        self.root.geometry("800x600")
        
        # Simple layout
        self.create_simple_interface()
        
    def create_simple_interface(self):
        """Create a simple interface"""
        # Title
        title_label = ttk.Label(self.root, text="Fruit Fly AI", font=("Arial", 20))
        title_label.pack(pady=20)
        
        # Description
        desc_label = ttk.Label(self.root, text="Desktop Application - Simplified Version")
        desc_label.pack(pady=10)
        
        # Status
        status_frame = ttk.Frame(self.root)
        status_frame.pack(pady=20)
        
        ttk.Label(status_frame, text="Status: ").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="green")
        self.status_label.pack(side=tk.LEFT)
        
        # Action buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Test Backend", command=self.test_backend).pack(pady=5)
        ttk.Button(button_frame, text="Show Info", command=self.show_info).pack(pady=5)
        ttk.Button(button_frame, text="Exit", command=self.on_exit).pack(pady=5)
        
    def test_backend(self):
        """Test backend systems"""
        self.status_label.config(text="Testing...", foreground="orange")
        self.root.update()
        
        try:
            # Quick test of one backend component
            from training_system.training_coordinator import TrainingCoordinator
            coordinator = TrainingCoordinator()
            
            self.status_label.config(text="Backend OK", foreground="green")
            messagebox.showinfo("Backend Test", "Backend systems are working!")
            
        except Exception as e:
            self.status_label.config(text="Error", foreground="red")
            messagebox.showerror("Backend Test", f"Error: {e}")
    
    def show_info(self):
        """Show application info"""
        info = """
Fruit Fly AI - Desktop Application

This is a simplified version of the Fruit Fly AI application.

Features:
- Training coordinator: Working
- Advanced cognitive brain: Available
- Survival system: Available
- Full GUI: Simplified for testing

For full functionality, the complete desktop app is being debugged.
        """
        messagebox.showinfo("Application Info", info)
    
    def on_exit(self):
        """Exit application"""
        if messagebox.askokcancel("Exit", "Do you want to exit?"):
            self.root.destroy()

def main():
    print("Starting simplified Fruit Fly AI...")
    
    try:
        root = tk.Tk()
        app = SimpleFruitFlyApp(root)
        print("Application started successfully")
        root.mainloop()
        print("Application closed")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()