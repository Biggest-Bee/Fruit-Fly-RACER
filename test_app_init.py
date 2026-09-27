"""
Test desktop app initialization without launching GUI
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from desktop_app.main_app import FruitFlyDesktopApp
    import tkinter as tk
    
    print("Testing desktop app initialization...")
    
    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    # Initialize app
    app = FruitFlyDesktopApp(root)
    
    print("SUCCESS: Desktop app initialized without errors")
    print(f"Chat history length: {len(app.chat_history)}")
    print(f"Viewable files: {len(app.viewable_files)}")
    print(f"Created files: {len(app.created_files)}")
    
    # Clean up
    root.destroy()
    
    print("Test completed successfully!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()