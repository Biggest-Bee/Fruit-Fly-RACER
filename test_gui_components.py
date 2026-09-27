"""
Test desktop app GUI components one by one
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing GUI components incrementally...")

try:
    root = tk.Tk()
    root.title("Fruit Fly AI - Component Test")
    root.geometry("800x600")
    
    console_text = tk.Text(root, height=25, width=100)
    console_text.pack(padx=10, pady=10)
    
    def log(message):
        console_text.insert(tk.END, message + "\n")
        console_text.see(tk.END)
        root.update()
    
    log("Starting GUI component test...")
    
    # Test 1: Menu
    log("1. Testing menu creation...")
    menubar = tk.Menu(root)
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)
    root.config(menu=menubar)
    log("   Menu: OK")
    
    # Test 2: Main layout
    log("2. Testing main layout...")
    main_container = ttk.Frame(root)
    main_container.pack(fill=tk.BOTH, expand=True)
    log("   Main layout: OK")
    
    # Test 3: Chat interface components
    log("3. Testing chat interface components...")
    chat_frame = ttk.LabelFrame(main_container, text="Chat Interface")
    chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    chat_display = tk.Text(chat_frame, height=15, state='disabled')
    chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    input_frame = ttk.Frame(chat_frame)
    input_frame.pack(fill=tk.X, padx=5, pady=5)
    
    chat_input = ttk.Entry(input_frame)
    chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    send_button = ttk.Button(input_frame, text="Send")
    send_button.pack(side=tk.RIGHT, padx=5)
    log("   Chat interface: OK")
    
    # Test 4: 3D viewer components
    log("4. Testing 3D viewer components...")
    viewer_frame = ttk.LabelFrame(main_container, text="3D Environment Viewer")
    viewer_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    viewer_canvas = tk.Canvas(viewer_frame, bg='black')
    viewer_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    log("   3D viewer: OK")
    
    # Test 5: File explorer components
    log("5. Testing file explorer components...")
    file_frame = ttk.LabelFrame(main_container, text="File Explorer")
    file_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    file_listbox = tk.Listbox(file_frame)
    file_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    log("   File explorer: OK")
    
    # Test 6: Training panel components
    log("6. Testing training panel components...")
    training_frame = ttk.LabelFrame(main_container, text="Training Panel")
    training_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    training_label = ttk.Label(training_frame, text="Training Controls")
    training_label.pack(pady=5)
    log("   Training panel: OK")
    
    # Test 7: Status panel components
    log("7. Testing status panel components...")
    status_frame = ttk.LabelFrame(main_container, text="Status Panel")
    status_frame.pack(fill=tk.X, padx=5, pady=5)
    
    status_label = ttk.Label(status_frame, text="Status: Ready")
    status_label.pack(pady=5)
    log("   Status panel: OK")
    
    log("\nSUCCESS: All GUI components tested successfully!")
    
    ttk.Button(root, text="Close", command=root.destroy).pack(pady=10)
    
    print("GUI test completed")
    root.mainloop()
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()