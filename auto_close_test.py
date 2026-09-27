"""
Auto-closing GUI test
"""
import tkinter as tk

print("Creating auto-closing GUI...")
root = tk.Tk()
root.title("Auto-Close Test")
root.geometry("300x200")

label = tk.Label(root, text="This will close in 2 seconds")
label.pack(pady=50)

print("Window created, scheduling close...")
root.after(2000, root.destroy)

print("Starting mainloop...")
root.mainloop()

print("Window closed successfully")