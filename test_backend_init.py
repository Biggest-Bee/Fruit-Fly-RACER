"""
Test backend initialization separately
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing backend initialization...")

try:
    # Test training coordinator
    print("1. Testing training coordinator...")
    from training_system.training_coordinator import TrainingCoordinator
    coordinator = TrainingCoordinator()
    print("   Training coordinator: OK")
    
    # Test advanced brain
    print("2. Testing advanced brain...")
    from brain_sim.advanced_cognitive_brain import AdvancedCognitiveBrain
    brain = AdvancedCognitiveBrain()
    print("   Advanced brain: OK")
    
    # Test survival system
    print("3. Testing survival system...")
    from training_system.survival_system import SurvivalSystem
    survival = SurvivalSystem()
    print("   Survival system: OK")
    
    print("SUCCESS: All backend systems initialized")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()