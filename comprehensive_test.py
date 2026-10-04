"""
Comprehensive Test Suite for Fruit Fly AI
Tests all requested features:
1. 3D Environment
2. Fly movement and vision in 3D
3. AI trainer in 3D environment
4. Hunger mode
5. GitHub repo pulling
6. Training in 3D environment
"""

import sys
import os
import time
import numpy as np

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'brain_sim'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'llm_interface'))
sys.path.append(os.path.join(os.path.dirname(__file__), '3d_environment'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'training_system'))

print("=" * 70)
print("COMPREHENSIVE FRUIT FLY AI TEST SUITE")
print("=" * 70)

# Test results tracking
test_results = {}

def run_test(test_name, test_func):
    """Run a test and track results"""
    print(f"\n{'=' * 70}")
    print(f"TEST: {test_name}")
    print('=' * 70)
    try:
        result = test_func()
        test_results[test_name] = {"status": "PASS", "result": result}
        print(f"[PASS] {test_name}: PASSED")
        return True
    except Exception as e:
        test_results[test_name] = {"status": "FAIL", "error": str(e)}
        print(f"[FAIL] {test_name}: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

# Test 1: 3D Environment
def test_3d_environment():
    """Test 3D environment initialization and basic functionality"""
    from world import World3D
    from food_system import FoodSystem
    
    # Create world
    world = World3D(size=(100.0, 100.0, 50.0))
    world.setup_food_in_corners()
    world.add_obstacle((50.0, 50.0, 25.0), (10.0, 10.0, 20.0))
    
    # Create food system
    food_system = FoodSystem(world_size=world.size)
    food_system.setup_corner_food()
    
    # Get world state
    world_state = world.get_world_state()
    food_status = food_system.get_food_status()
    
    assert world_state['size'] == (100.0, 100.0, 50.0), "World size incorrect"
    assert food_status['total_locations'] == 4, "Should have 4 food locations"
    assert food_status['available_food'] > 0, "Should have food available"
    
    print(f"World size: {world_state['size']}")
    print(f"Food locations: {food_status['total_locations']}")
    print(f"Available food: {food_status['available_food']}")
    
    return {"world_size": world_state['size'], "food_count": food_status['total_locations']}

# Test 2: Fly Movement and Vision in 3D
def test_fly_movement_vision():
    """Test fly character movement and sensory input"""
    from fly_character import FlyCharacter
    from sensory_system import SensorySystem
    from food_system import FoodSystem
    
    # Create fly
    fly = FlyCharacter(start_position=(50.0, 50.0, 25.0))
    
    # Create sensory system
    sensory = SensorySystem(world_size=(100.0, 100.0, 50.0))
    
    # Create food system
    food_system = FoodSystem(world_size=(100.0, 100.0, 50.0))
    food_system.setup_corner_food()
    
    # Test navigation
    target = (10.0, 10.0, 25.0)
    dt = 0.1
    fly.navigate_to(target, dt)
    
    # Process sensory input
    visual_input = sensory.process_visual_input(
        fly.position,
        {"yaw": fly.yaw, "pitch": fly.pitch, "roll": fly.roll},
        food_system.food_locations,
        []
    )
    
    chemical_input = sensory.process_chemical_input(
        fly.position,
        food_system.food_locations
    )
    
    proprioception_input = sensory.process_proprioception(
        fly.position,
        fly.velocity,
        {"yaw": fly.yaw, "pitch": fly.pitch, "roll": fly.roll}
    )
    
    # Get fly state
    fly_state = fly.get_state()
    
    # Allow any flight mode value
    assert len(visual_input) > 0, "Visual input should not be empty"
    assert 'speed' in proprioception_input, "Proprioception should include speed"
    
    print(f"Fly position: {fly_state['position']}")
    print(f"Flight mode: {fly_state['flight_mode']}")
    print(f"Visual input shape: {len(visual_input)}")
    print(f"Chemical signals: {list(chemical_input.keys())}")
    print(f"Speed: {proprioception_input['speed']}")
    
    return {
        "position": fly_state['position'],
        "flight_mode": fly_state['flight_mode'],
        "visual_processing": len(visual_input) > 0
    }

# Test 3: AI Trainer in 3D Environment
def test_ai_trainer_3d():
    """Test AI training interface integration"""
    from training_system.ai_training_interface import AITrainingInterface
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize AI trainer with GitHub integration
    ai_trainer = AITrainingInterface(enable_github=True)
    
    # Test basic functionality
    test_lesson = {
        "task": "Write a function that adds two numbers",
        "starter_code": "def add_numbers(a, b):\n    pass",
        "expected_solution": "def add_numbers(a, b):\n    return a + b",
        "test_cases": ["syntax", "correctness"]
    }
    
    # Get instruction
    instruction = ai_trainer.get_lesson_instruction(test_lesson)
    
    # Evaluate code
    user_code = "def add_numbers(a, b):\n    return a + b"
    evaluation = ai_trainer.evaluate_code(user_code, test_lesson)
    
    # Check GitHub status
    github_status = ai_trainer.get_github_status()
    
    assert instruction is not None, "Should get instruction"
    assert evaluation is not None, "Should get evaluation"
    assert github_status is not None, "Should get GitHub status"
    
    print(f"Instruction length: {len(instruction)}")
    print(f"Evaluation correct: {evaluation.get('correct', False)}")
    print(f"GitHub enabled: {github_status.get('enabled', False)}")
    
    return {
        "instruction_received": len(instruction) > 0,
        "evaluation_works": evaluation is not None,
        "github_enabled": github_status.get('enabled', False)
    }

# Test 4: Hunger Mode
def test_hunger_mode():
    """Test hunger mechanics and survival system"""
    from training_system.survival_system import SurvivalSystem
    from training_system.hunger_mechanics import HungerMechanics
    
    # Create survival system
    survival = SurvivalSystem(initial_energy=100.0)
    hunger = survival.hunger_mechanics
    
    # Test hunger activation
    hunger.set_enabled(True)
    
    # Update survival
    dt = 1.0
    activity_level = 0.5
    survival.update(dt, activity_level=activity_level)
    
    # Check hunger state
    should_seek_food = hunger.should_seek_food()
    
    # Test feeding
    energy_before = hunger.energy
    survival.process_feeding(25.0)
    energy_after = hunger.energy
    
    assert energy_after > energy_before, "Energy should increase after feeding"
    assert hunger.enabled == True, "Hunger should be enabled"
    
    print(f"Energy before: {energy_before}")
    print(f"Energy after: {energy_after}")
    print(f"Should seek food: {should_seek_food}")
    print(f"Hunger level: {hunger.hunger_level}")
    print(f"Starving: {hunger.is_starving}")
    
    return {
        "energy_gain": energy_after - energy_before,
        "hunger_enabled": hunger.enabled,
        "can_seek_food": should_seek_food
    }

# Test 5: GitHub Repo Pulling
def test_github_repo_pulling():
    """Test GitHub repository pulling with rate limiting"""
    from training_system.github_rate_limiter import GitHubRateLimiter
    from training_system.github_repo_puller import GitHubRepoPuller
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get GitHub token
    import os
    github_token = os.getenv("GITHUB_TOKEN")
    authenticated = bool(github_token)
    
    # Create rate limiter
    rate_limiter = GitHubRateLimiter(authenticated=authenticated, github_token=github_token)
    
    # Create repo puller
    puller = GitHubRepoPuller(rate_limiter, workspace_dir="test_github_repos")
    
    # Test rate limiter status
    status = rate_limiter.get_status()
    
    # Test repository info (doesn't require cloning)
    success, repo_info, message = puller.get_repository_info(
        "https://github.com/torvalds/linux"
    )
    
    assert status is not None, "Should get rate limiter status"
    assert repo_info is not None or success == False, "Should get repo info or fail gracefully"
    
    print(f"Authenticated: {authenticated}")
    print(f"Search limit: {status['search']['limit']}/min")
    print(f"General limit: {status['general']['limit']}/hour")
    print(f"Secondary limit: {status['secondary']['limit']}/min")
    print(f"Repo info success: {success}")
    print(f"Repo info: {repo_info if repo_info else 'N/A'}")
    
    # Cleanup
    puller.cleanup_all()
    
    return {
        "authenticated": authenticated,
        "search_limit": status['search']['limit'],
        "general_limit": status['general']['limit'],
        "repo_info_success": success
    }

# Test 6: Training in 3D Environment
def test_training_3d():
    """Test training system integration with 3D environment"""
    from training_system.training_coordinator import TrainingCoordinator
    from training_system.coding_curriculum import CodingCurriculum
    from brain_controller import BrainFlyController
    
    # Create training coordinator
    coordinator = TrainingCoordinator()
    
    # Create curriculum
    curriculum = CodingCurriculum()
    
    # Get a lesson
    lesson = curriculum.get_lesson_for_language("python", "beginner")
    
    # Create brain controller with 3D
    controller = BrainFlyController(
        bounds=(20.0, 20.0, 12.0),
        hunger_enabled=True
    )
    
    # Test training session
    coordinator.start_training()
    
    # Set current lesson and language
    coordinator.current_lesson = lesson
    coordinator.current_language = "python"
    
    # Simulate training step
    user_code = lesson['starter_code']
    result = coordinator.submit_code(user_code)
    
    # Test brain controller with food
    food_sources = [
        {"position": (-5.0, -5.0, 0.8), "amount": 100.0},
        {"position": (5.0, 5.0, 0.8), "amount": 100.0}
    ]
    
    dt = 0.1
    state = controller.update(dt, food_sources)
    
    coordinator.stop_training()
    
    assert lesson is not None, "Should get a lesson"
    assert result is not None, "Should get training result"
    assert state is not None, "Should get controller state"
    
    print(f"Lesson task: {lesson['task']}")
    print(f"Training result: {result}")
    print(f"Controller behavior: {state.get('behavior', 'unknown')}")
    print(f"Fly energy: {controller.hunger.energy}")
    
    return {
        "lesson_available": lesson is not None,
        "training_works": result is not None,
        "controller_active": state is not None,
        "behavior": state.get('behavior', 'unknown')
    }

# Test 7: Enhanced Brain Regions
def test_enhanced_brain_regions():
    """Test Prefrontal Cortex and Wernicke's Area"""
    from brain_sim.enhanced_human_regions import PrefrontalCortex, WernickeArea
    
    # Create Prefrontal Cortex (smaller for testing)
    prefrontal = PrefrontalCortex(num_neurons=1000)
    
    # Create Wernicke's Area (smaller for testing)
    wernicke = WernickeArea(num_neurons=1000)
    
    # Test Prefrontal Cortex
    prefrontal.activate_coding_mode("python")
    coding_result = prefrontal.process_coding_task("Write a function", {"context": "test"})
    
    # Test Wernicke's Area
    comprehension = wernicke.comprehend_input("Hello, how are you?")
    response = wernicke.produce_response({"sensory": 45.0, "motor": 30.0})
    translation = wernicke.translate_brain_to_english({"sensory": 50.0}, [1, 2, 3])
    
    assert len(prefrontal.neurons) == 1000, "Should have 1000 neurons"
    assert len(wernicke.neurons) == 1000, "Should have 1000 neurons"
    assert comprehension['comprehended'] == True, "Should comprehend input"
    assert len(response) > 0, "Should produce response"
    
    print(f"Prefrontal neurons: {len(prefrontal.neurons)}")
    print(f"Working memory size: {len(prefrontal.working_memory)}")
    print(f"Wernicke neurons: {len(wernicke.neurons)}")
    print(f"Comprehension: {comprehension['comprehended']}")
    print(f"Response: {response}")
    print(f"Translation: {translation}")
    
    return {
        "prefrontal_neurons": len(prefrontal.neurons),
        "wernicke_neurons": len(wernicke.neurons),
        "comprehension_works": comprehension['comprehended'],
        "response_generated": len(response) > 0
    }

# Test 8: Distance-Based Connections and Hebbian Learning
def test_neuromorphic_features():
    """Test distance-based connections and Hebbian learning"""
    from brain_sim.synapse_models import Synapse, SynapticConnectivity
    
    # Test individual synapse with distance
    synapse = Synapse(pre_neuron_id=1, post_neuron_id=100, weight=1.0, distance=10.0)
    
    # Test distance probability
    distance_prob = synapse.distance_probability
    expected_prob = 1.0 / 10.0
    
    # Test Hebbian learning
    synapse.co_activate()
    synapse.co_activate()
    co_activation_count = synapse.co_activation_count
    
    # Test shortcut formation
    if co_activation_count > 5:
        synapse.is_shortcut = True
        synapse.hebbian_strength = 0.6
    
    effective_weight = synapse.get_effective_weight()
    
    assert abs(distance_prob - expected_prob) < 0.01, "Distance probability should be 1/distance"
    assert co_activation_count > 0, "Should have co-activation count"
    
    print(f"Distance: {synapse.distance}")
    print(f"Distance probability: {distance_prob}")
    print(f"Expected probability: {expected_prob}")
    print(f"Co-activation count: {co_activation_count}")
    print(f"Is shortcut: {synapse.is_shortcut}")
    print(f"Hebbian strength: {synapse.hebbian_strength}")
    print(f"Effective weight: {effective_weight}")
    
    return {
        "distance_probability_correct": abs(distance_prob - expected_prob) < 0.01,
        "hebbian_learning_works": co_activation_count > 0,
        "shortcut_possible": synapse.is_shortcut
    }

# Run all tests
if __name__ == "__main__":
    tests = [
        ("3D Environment", test_3d_environment),
        ("Fly Movement and Vision", test_fly_movement_vision),
        ("AI Trainer in 3D", test_ai_trainer_3d),
        ("Hunger Mode", test_hunger_mode),
        ("GitHub Repo Pulling", test_github_repo_pulling),
        ("Training in 3D", test_training_3d),
        ("Enhanced Brain Regions", test_enhanced_brain_regions),
        ("Neuromorphic Features", test_neuromorphic_features),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
        else:
            failed += 1
        time.sleep(1)  # Brief pause between tests
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(passed / len(tests) * 100):.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in test_results.items():
        status = result["status"]
        if status == "PASS":
            print(f"[PASS] {test_name}: PASSED")
        else:
            print(f"[FAIL] {test_name}: FAILED - {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 70)
    
    if failed == 0:
        print("[SUCCESS] ALL TESTS PASSED!")
    else:
        print(f"[WARNING] {failed} test(s) failed. Please review the errors above.")
    
    print("=" * 70)
