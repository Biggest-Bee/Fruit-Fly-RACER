"""
Minimal GUI test
"""
import tkinter as tk
from tkinter import ttk

print("Testing minimal Tkinter GUI...")

try:
    root = tk.Tk()
    root.title("Test Window")
    root.geometry("400x300")
    
    label = ttk.Label(root, text="Test GUI Working")
    label.pack(pady=20)
    
    button = ttk.Button(root, text="Close", command=root.destroy)
    button.pack(pady=10)
    
    print("GUI created successfully")
    print("Waiting 2 seconds then closing...")
    root.after(2000, root.destroy)
    root.mainloop()
    
    print("GUI test completed successfully")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()