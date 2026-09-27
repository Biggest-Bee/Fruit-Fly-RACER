"""
Simplified desktop app test to identify the blocking issue
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing simplified desktop app...")

try:
    root = tk.Tk()
    root.title("Fruit Fly AI - Test")
    root.geometry("800x600")
    
    # Simple interface
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Label(main_frame, text="Fruit Fly AI - Test Mode").pack(pady=20)
    
    # Try to initialize backend systems one by one
    console_text = tk.Text(main_frame, height=20, width=80)
    console_text.pack(pady=10)
    
    def test_backend():
        console_text.insert(tk.END, "Testing backend systems...\n")
        console_text.see(tk.END)
        root.update()
        
        try:
            # Test 1: Training coordinator
            console_text.insert(tk.END, "1. Loading training coordinator...\n")
            console_text.see(tk.END)
            root.update()
            
            from training_system.training_coordinator import TrainingCoordinator
            coordinator = TrainingCoordinator()
            console_text.insert(tk.END, "   Training coordinator: OK\n")
            console_text.see(tk.END)
            root.update()
            
            # Test 2: Advanced brain
            console_text.insert(tk.END, "2. Loading advanced brain...\n")
            console_text.see(tk.END)
            root.update()
            
            from brain_sim.advanced_cognitive_brain import AdvancedCognitiveBrain
            brain = AdvancedCognitiveBrain()
            console_text.insert(tk.END, "   Advanced brain: OK\n")
            console_text.see(tk.END)
            root.update()
            
            # Test 3: Survival system
            console_text.insert(tk.END, "3. Loading survival system...\n")
            console_text.see(tk.END)
            root.update()
            
            from training_system.survival_system import SurvivalSystem
            survival = SurvivalSystem()
            console_text.insert(tk.END, "   Survival system: OK\n")
            console_text.see(tk.END)
            root.update()
            
            console_text.insert(tk.END, "\nSUCCESS: All systems loaded!\n")
            console_text.see(tk.END)
            
        except Exception as e:
            console_text.insert(tk.END, f"ERROR: {e}\n")
            console_text.see(tk.END)
            import traceback
            console_text.insert(tk.END, traceback.format_exc())
            console_text.see(tk.END)
    
    ttk.Button(main_frame, text="Test Backend", command=test_backend).pack(pady=10)
    ttk.Button(main_frame, text="Close", command=root.destroy).pack(pady=5)
    
    print("Simplified GUI created")
    root.mainloop()
    print("Test completed")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()