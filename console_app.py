"""
Console-only version of Fruit Fly AI
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Fruit Fly AI - Console Version")
print("=" * 40)
print()

def main():
    print("Starting Fruit Fly AI Console Application...")
    print()
    
    try:
        # Test backend systems
        print("1. Testing Training Coordinator...")
        from training_system.training_coordinator import TrainingCoordinator
        coordinator = TrainingCoordinator()
        print("   Training Coordinator: OK")
        
        print()
        print("2. Testing Advanced Cognitive Brain...")
        from brain_sim.advanced_cognitive_brain import AdvancedCognitiveBrain
        brain = AdvancedCognitiveBrain()
        print("   Advanced Cognitive Brain: OK")
        
        print()
        print("3. Testing Survival System...")
        from training_system.survival_system import SurvivalSystem
        survival = SurvivalSystem()
        print("   Survival System: OK")
        
        print()
        print("=" * 40)
        print("SUCCESS: All backend systems are working!")
        print("=" * 40)
        print()
        print("Available commands:")
        print("  chat    - Start chat interface")
        print("  train   - Start training mode")
        print("  status  - Show system status")
        print("  exit    - Exit application")
        print()
        
        while True:
            try:
                command = input("fruit-ai> ").strip().lower()
                
                if command == "exit":
                    print("Exiting Fruit Fly AI...")
                    break
                elif command == "status":
                    print("System Status:")
                    print(f"  Training Coordinator: {'Active' if coordinator else 'Inactive'}")
                    print(f"  Advanced Brain: {'Active' if brain else 'Inactive'}")
                    print(f"  Survival System: {'Active' if survival else 'Inactive'}")
                elif command == "chat":
                    print("Chat interface (console mode):")
                    print("Type 'quit' to return to main menu")
                    while True:
                        user_input = input("You> ")
                        if user_input.lower() == "quit":
                            break
                        print("Fly> This is console mode - full chat requires GUI")
                elif command == "train":
                    print("Training mode (console mode):")
                    print("Type 'quit' to return to main menu")
                    while True:
                        user_input = input("train> ")
                        if user_input.lower() == "quit":
                            break
                        print("System: Training commands require GUI interface")
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'exit' to quit")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' command to quit")
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())