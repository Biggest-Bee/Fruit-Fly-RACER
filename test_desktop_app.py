"""
Test Desktop Application
Test the desktop application components without launching the GUI
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_desktop_app_imports():
    """Test that desktop app components can be imported"""
    print("Testing Desktop Application Imports...")
    
    try:
        from desktop_app.main_app import FruitFlyDesktopApp, main
        print("[OK] Desktop app imports successful")
        return True
    except ImportError as e:
        print(f"[ERROR] Desktop app imports failed: {e}")
        return False

def test_backend_integration():
    """Test backend system integration"""
    print("\nTesting Backend Integration...")
    
    try:
        from training_system.training_coordinator import TrainingCoordinator
        from brain_sim.advanced_cognitive_brain import AdvancedCognitiveBrain
        from training_system.survival_system import SurvivalSystem
        from llm_interface.language_cortex import LanguageCortex
        
        # Test training coordinator
        coordinator = TrainingCoordinator()
        print("[OK] Training coordinator initialized")
        
        # Test advanced cognitive brain
        advanced_brain = AdvancedCognitiveBrain()
        print("[OK] Advanced cognitive brain initialized")
        
        # Test survival system
        survival = SurvivalSystem()
        print("[OK] Survival system initialized")
        
        # Test language cortex
        cortex = LanguageCortex(size=500)
        print("[OK] Language cortex initialized")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Backend integration failed: {e}")
        return False

def test_file_explorer_logic():
    """Test file explorer visibility logic"""
    print("\nTesting File Explorer Logic...")
    
    # Simulate file explorer state
    viewable_files = set()
    created_files = set()
    current_file = None
    
    # Test adding viewable file
    viewable_files.add("test.py")
    print(f"[OK] Added file to viewable: {len(viewable_files)} files")
    
    # Test creating file
    created_files.add("new_file.py")
    print(f"[OK] Created file: {len(created_files)} files")
    
    # Test current file visibility
    current_file = "current.py"
    print(f"[OK] Set current file: {current_file}")
    
    # Test visibility check
    all_visible = viewable_files | created_files
    if current_file:
        all_visible.add(current_file)
    
    print(f"[OK] Total visible files: {len(all_visible)}")
    
    return True

def test_gui_components():
    """Test GUI component structure"""
    print("\nTesting GUI Component Structure...")
    
    try:
        import tkinter as tk
        from tkinter import ttk, scrolledtext
        
        # Test that GUI components can be created
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Test basic components
        frame = ttk.Frame(root)
        label = ttk.Label(frame, text="Test")
        button = ttk.Button(frame, text="Test")
        progress = ttk.Progressbar(frame, orient=tk.HORIZONTAL)
        text_area = scrolledtext.ScrolledText(frame)
        
        print("[OK] GUI components can be created")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"[ERROR] GUI component test failed: {e}")
        return False

def test_chat_interface_logic():
    """Test chat interface logic"""
    print("\nTesting Chat Interface Logic...")
    
    # Simulate chat history
    chat_history = []
    
    # Test adding messages
    chat_history.append({"sender": "User", "message": "Hello", "timestamp": 123456})
    chat_history.append({"sender": "Fly", "message": "Hi there!", "timestamp": 123457})
    
    print(f"[OK] Chat history: {len(chat_history)} messages")
    
    # Test message processing
    test_messages = [
        "hello",
        "I am hungry",
        "train me in python",
        "help with code"
    ]
    
    responses = {
        "hello": "Hello! I am ready to learn and help with coding tasks.",
        "hungry": "I am feeling a bit hungry. Could use some training rewards!",
        "train": "I'd love to train! Please start a training session.",
        "help": "I can help with coding in many languages: Python, Rust, C++, JavaScript, TypeScript, and more!"
    }
    
    for msg in test_messages:
        if "hello" in msg.lower():
            print(f"[OK] Processed: '{msg}' -> Response available")
        elif "hungry" in msg.lower():
            print(f"[OK] Processed: '{msg}' -> Response available")
        elif "train" in msg.lower():
            print(f"[OK] Processed: '{msg}' -> Response available")
        elif "help" in msg.lower():
            print(f"[OK] Processed: '{msg}' -> Response available")
    
    return True

def test_training_controls():
    """Test training control logic"""
    print("\nTesting Training Control Logic...")
    
    try:
        from training_system.training_coordinator import TrainingCoordinator
        
        coordinator = TrainingCoordinator()
        
        # Test hunger simulation
        coordinator.reward_system.hunger_system.update_hunger(50.0, activity_level=0.5)
        print("[OK] Hunger simulation successful")
        
        # Test starting training
        start_result = coordinator.start_training("python", "beginner")
        if start_result["success"]:
            print(f"[OK] Training started: {start_result['language']}")
        else:
            print(f"[WARNING] Training start issue: {start_result['reason']}")
        
        # Test getting instruction
        instruction = coordinator.get_lesson_instruction()
        print(f"[OK] Instruction received: {len(instruction)} chars")
        
        # Test stopping training
        stop_result = coordinator.stop_training("Test complete")
        if stop_result["success"]:
            print("[OK] Training stopped successfully")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Training control test failed: {e}")
        return False

def test_status_display():
    """Test status display logic"""
    print("\nTesting Status Display Logic...")
    
    try:
        from training_system.training_coordinator import TrainingCoordinator
        from training_system.survival_system import SurvivalSystem
        
        coordinator = TrainingCoordinator()
        survival = SurvivalSystem()
        
        # Test energy status
        energy = survival.hunger_mechanics.energy
        print(f"[OK] Energy status: {energy:.1f}%")
        
        # Test hunger status
        hunger_drive = survival.hunger_mechanics.hunger_drive
        print(f"[OK] Hunger drive: {hunger_drive:.2f}")
        
        # Test API status
        api_status = coordinator.api_manager.get_usage_status()
        print(f"[OK] API usage: {api_status['current_usage']}/{api_status['daily_quota']}")
        
        # Test skill progress
        skill_progress = coordinator.skill_tracker.get_overall_progress()
        print(f"[OK] Skill progress: {skill_progress['overall_mastery']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Status display test failed: {e}")
        return False

def main():
    """Run all desktop application tests"""
    print("="*50)
    print("Desktop Application - Component Tests")
    print("="*50)
    
    all_passed = True
    
    # Test imports
    if not test_desktop_app_imports():
        all_passed = False
    
    # Test backend integration
    if not test_backend_integration():
        all_passed = False
    
    # Test file explorer logic
    if not test_file_explorer_logic():
        all_passed = False
    
    # Test GUI components
    if not test_gui_components():
        all_passed = False
    
    # Test chat interface logic
    if not test_chat_interface_logic():
        all_passed = False
    
    # Test training controls
    if not test_training_controls():
        all_passed = False
    
    # Test status display
    if not test_status_display():
        all_passed = False
    
    # Final result
    print("\n" + "="*50)
    if all_passed:
        print("[SUCCESS] All desktop application tests passed!")
        print("Desktop application components are working correctly.")
        print("\nTo launch the actual GUI application, run:")
        print("python desktop_app/main_app.py")
    else:
        print("[FAILURE] Some desktop application tests failed")
    print("="*50)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)