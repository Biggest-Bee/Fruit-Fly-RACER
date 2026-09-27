"""
Completely standalone GUI - no backend imports
"""
import tkinter as tk
from tkinter import ttk, messagebox

print("Creating standalone GUI...")

class StandaloneGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Fruit Fly AI - Standalone")
        self.root.geometry("600x400")
        
        self.create_interface()
        
    def create_interface(self):
        # Title
        ttk.Label(self.root, text="Fruit Fly AI", font=("Arial", 18)).pack(pady=20)
        
        # Chat area
        chat_frame = ttk.LabelFrame(self.root, text="Chat")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_display = tk.Text(chat_frame, height=10, state='disabled')
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input area
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(input_frame, text="Send", command=self.send_message).pack(side=tk.RIGHT, padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="About", command=self.show_about).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.on_exit).pack(side=tk.LEFT, padx=5)
        
        # Add welcome message
        self.add_message("System", "Fruit Fly AI - Standalone Mode (Backend disabled)")
        
    def add_message(self, sender, message):
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{sender}: {message}\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
    def send_message(self):
        message = self.chat_input.get()
        if message:
            self.add_message("You", message)
            self.chat_input.delete(0, tk.END)
            self.add_message("Fly", "This is standalone mode - backend systems are disabled.")
        
    def show_about(self):
        messagebox.showinfo("About", "Fruit Fly AI - Standalone Mode\n\nBackend systems disabled for testing.")
        
    def on_exit(self):
        if messagebox.askokcancel("Exit", "Exit?"):
            self.root.destroy()

def main():
    print("Starting standalone GUI...")
    try:
        root = tk.Tk()
        app = StandaloneGUI(root)
        print("GUI created successfully")
        root.mainloop()
        print("GUI closed")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()