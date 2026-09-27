"""
Ultra-minimal desktop app test - no backend systems
"""
import tkinter as tk
from tkinter import ttk

print("Creating ultra-minimal GUI...")

try:
    root = tk.Tk()
    root.title("Fruit Fly AI - Minimal Test")
    root.geometry("600x400")
    
    main_frame = ttk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    ttk.Label(main_frame, text="Fruit Fly AI - Minimal Test", font=("Arial", 16)).pack(pady=20)
    ttk.Label(main_frame, text="This is a minimal test without backend systems").pack(pady=10)
    
    close_button = ttk.Button(main_frame, text="Close", command=root.destroy)
    close_button.pack(pady=20)
    
    print("GUI created successfully")
    print("Window will close automatically in 3 seconds...")
    
    root.after(3000, root.destroy)
    root.mainloop()
    
    print("GUI test completed successfully")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()