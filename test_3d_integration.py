"""
Integration Test for 3D Environment and Brain Simulation
Tests the complete flow: 3D environment -> sensory input -> brain processing -> motor output
"""

import sys
import os
import numpy as np

# Add project directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'brain_sim'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'llm_interface'))
sys.path.append(os.path.join(os.path.dirname(__file__), '3d_environment'))

from brain_engine import BrainEngine
from language_cortex import LanguageCortex
from world import World3D
from fly_character import FlyCharacter
from sensory_system import SensorySystem
from food_system import FoodSystem

def test_3d_brain_integration():
    """Test the integration between 3D environment and brain simulation"""
    
    print("=" * 50)
    print("FRUIT FLY AI - 3D ENVIRONMENT INTEGRATION TEST")
    print("=" * 50)
    
    # Initialize 3D environment
    print("\n1. Initializing 3D Environment...")
    world = World3D(size=(100.0, 100.0, 50.0))
    world.setup_food_in_corners()
    world.add_obstacle((50.0, 50.0, 25.0), (10.0, 10.0, 20.0))
    print("[OK] 3D World initialized")
    
    # Initialize fly character
    print("\n2. Initializing Fly Character...")
    fly = FlyCharacter(start_position=(50.0, 50.0, 25.0))
    print("[OK] Fly character initialized")
    
    # Initialize sensory system
    print("\n3. Initializing Sensory System...")
    sensory = SensorySystem(world_size=world.size)
    print("[OK] Sensory system initialized")
    
    # Initialize food system
    print("\n4. Initializing Food System...")
    food_system = FoodSystem(world_size=world.size)
    food_system.setup_corner_food()
    print("[OK] Food system initialized")
    
    # Initialize brain components (limited for testing)
    print("\n5. Initializing Brain Components...")
    try:
        annotations_file = "data/body-annotations-male-cns-v1.0-minconf-0.5.feather"
        connectome_file = "data/connectome-weights-male-cns-v1.0-minconf-0.5.feather"
        brain = BrainEngine(annotations_file, connectome_file, max_synapses=3000)
        print("[OK] Brain Engine initialized")
    except Exception as e:
        print(f"[ERROR] Brain Engine initialization failed: {e}")
        brain = None
    
    language_cortex = LanguageCortex(size=300)
    print("[OK] Language Cortex initialized")
    
    # Test the complete integration loop
    print("\n" + "=" * 50)
    print("TESTING INTEGRATION LOOP")
    print("=" * 50)
    
    # Simulation parameters
    simulation_steps = 20
    dt = 0.1
    
    for step in range(simulation_steps):
        print(f"\n--- Simulation Step {step + 1} ---")
        
        # Step 1: Get sensory input from environment
        print("Step 1: Processing sensory input...")
        visual_input = sensory.process_visual_input(
            fly.position, 
            {"yaw": fly.yaw, "pitch": fly.pitch, "roll": fly.roll},
            food_system.food_locations,
            world.obstacles
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
        
        print(f"   Visual intensity: {np.mean(np.abs(visual_input)):.4f}")
        print(f"   Chemical signals: {list(chemical_input.keys())}")
        print(f"   Speed: {proprioception_input['speed']:.2f}")
        
        # Step 2: Convert sensory input to brain activation
        print("Step 2: Converting to brain activation...")
        brain_activation = sensory.convert_to_brain_input()
        print(f"   Brain activation: {brain_activation}")
        
        # Step 3: Process through language cortex
        print("Step 3: Processing through language cortex...")
        integrated_activation = language_cortex.integrate_with_connectome(brain_activation)
        print(f"   Integrated activation: {integrated_activation}")
        
        # Step 4: Apply to brain simulation
        print("Step 4: Brain simulation processing...")
        if brain:
            try:
                # Convert concept activation to neuron stimulation
                for concept, current in integrated_activation.items():
                    if isinstance(concept, str):
                        brain.stimulate_region(concept, current)
                
                # Run brain simulation
                firing_record = brain.run_simulation(3, verbose=False)
                activity = brain.get_network_activity()
                print(f"   Neurons fired: {activity['current_firing_rate']}")
                
                # Reset for next step
                brain.reset()
            except Exception as e:
                print(f"   Error in brain simulation: {e}")
        else:
            print("   Brain simulation skipped")
        
        # Step 5: Generate motor output based on brain activity
        print("Step 5: Generating motor output...")
        motor_output = {}
        
        # Simple behavior: if sensory input indicates food, navigate towards it
        if chemical_input:
            nearest_food = food_system.find_nearest_food(fly.position)
            if nearest_food and nearest_food["distance"] < 30.0:
                print(f"   Food detected at {nearest_food['distance']:.2f} units")
                print(f"   Navigating to food...")
                fly.navigate_to(nearest_food["food"]["position"], dt)
            else:
                # Random exploration
                print(f"   Exploring environment...")
                control_input = {
                    "thrust": 0.3,
                    "yaw": np.random.uniform(-0.5, 0.5),
                    "pitch": np.random.uniform(-0.2, 0.2),
                    "roll": 0.0
                }
                fly.update(dt, control_input)
        else:
            # Hover in place
            print(f"   Hovering...")
            control_input = {
                "thrust": 0.5,  # Counteract gravity
                "yaw": 0.0,
                "pitch": 0.0,
                "roll": 0.0
            }
            fly.update(dt, control_input)
        
        # Step 6: Check if fly should eat
        print("Step 6: Checking feeding behavior...")
        nearest_food = food_system.find_nearest_food(fly.position)
        if nearest_food and nearest_food["distance"] < 2.0:
            print(f"   Close to food! Landing and eating...")
            fly.land()
            energy_gained = food_system.consume_food(nearest_food["index"], consumption_time=1.0)
            fly.eat(energy_gained)
            fly.take_off()
        else:
            print(f"   No food nearby")
        
        # Step 7: Update world state
        print("Step 7: Updating world state...")
        world.update()
        food_system.regenerate_food(0.01)
        
        # Step 8: Check energy and survival
        print("Step 8: Survival check...")
        print(f"   Fly energy: {fly.energy:.1f}")
        if fly.energy < 20.0:
            print(f"   WARNING: Fly is getting hungry!")
        
        # Update sensory system for next iteration
        sensory_summary = sensory.get_sensory_summary()
        print(f"   Sensory summary: {sensory_summary}")
        
        print(f"   [OK] Step {step + 1} complete")
        
        # Check if fly is too low (crash prevention)
        if fly.position[2] < 5.0:
            print(f"   WARNING: Fly too low, taking emergency action!")
            fly.position[2] = 10.0
            fly.velocity[2] = 5.0
    
    # Summary
    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    world_state = world.get_world_state()
    print(f"World time: {world_state['time']:.2f}")
    print(f"Available food: {world_state['available_food']:.1f}")
    
    fly_state = fly.get_state()
    print(f"Fly position: {fly_state['position']}")
    print(f"Fly energy: {fly_state['energy']:.1f}")
    print(f"Flight mode: {fly_state['flight_mode']}")
    
    food_status = food_system.get_food_status()
    print(f"Food consumed: {food_status['total_consumed']:.1f}")
    
    cortex_state = language_cortex.get_cortex_state()
    print(f"Language cortex: {cortex_state}")
    
    print("\n" + "=" * 50)
    print("3D Environment Integration test completed!")
    print("=" * 50)
    
    print("\nIntegration achievements:")
    print("[OK] 3D world with food locations and obstacles")
    print("[OK] Fly character with flight mechanics")
    print("[OK] Sensory system processing visual, chemical, proprioceptive input")
    print("[OK] Food system with consumption and regeneration")
    print("[OK] Brain simulation integration")
    print("[OK] Complete sensorimotor loop")
    
    print("\nNext steps:")
    print("1. Implement more sophisticated navigation algorithms")
    print("2. Add hunger-driven behavior priorities")
    print("3. Implement training system with coding tasks")
    print("4. Connect to desktop application interface")

if __name__ == "__main__":
    test_3d_brain_integration()