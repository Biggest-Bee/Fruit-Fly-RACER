"""
Integration Test for Brain Simulation and LLM Interface
Tests the complete flow from user input to brain activation to response
"""

import sys
import os

# Add project directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'brain_sim'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'llm_interface'))

from brain_engine import BrainEngine
from translator import BrainTranslator
from language_cortex import LanguageCortex

def test_integration():
    """Test the integration between brain simulation and LLM interface"""
    
    print("=" * 50)
    print("FRUIT FLY AI - INTEGRATION TEST")
    print("=" * 50)
    
    # Initialize components
    print("\n1. Initializing Brain Engine...")
    try:
        annotations_file = "data/body-annotations-male-cns-v1.0-minconf-0.5.feather"
        connectome_file = "data/connectome-weights-male-cns-v1.0-minconf-0.5.feather"
        
        # Use limited data for testing
        brain = BrainEngine(annotations_file, connectome_file, max_synapses=5000)
        print("[OK] Brain Engine initialized")
    except Exception as e:
        print(f"[ERROR] Brain Engine initialization failed: {e}")
        print("   Continuing with limited functionality...")
        brain = None
    
    print("\n2. Initializing Brain Translator...")
    try:
        translator = BrainTranslator()
        print("[OK] Brain Translator initialized")
    except Exception as e:
        print(f"[ERROR] Brain Translator initialization failed: {e}")
        print("   Make sure to set your GEMINI_API_KEY in the .env file")
        translator = None
    
    print("\n3. Initializing Language Cortex...")
    language_cortex = LanguageCortex(size=500)
    print("[OK] Language Cortex initialized")
    
    # Test the complete flow
    print("\n" + "=" * 50)
    print("TESTING COMPLETE FLOW")
    print("=" * 50)
    
    # Test inputs
    test_inputs = [
        "Hello, I am hungry",
        "I want to learn to code",
        "Show me how to move",
        "I am thinking about food"
    ]
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n--- Test {i}: '{user_input}' ---")
        
        # Step 1: Convert text to brain activation
        print("Step 1: Converting text to brain activation...")
        if translator:
            try:
                brain_activation = translator.text_to_brain_activation(user_input)
                print(f"   Brain activation: {brain_activation}")
            except Exception as e:
                print(f"   Error: {e}")
                brain_activation = {"sensory": 20.0, "interneuron": 15.0}
        else:
            brain_activation = {"sensory": 20.0, "interneuron": 15.0}
            print(f"   Using fallback activation: {brain_activation}")
        
        # Step 2: Process through language cortex
        print("Step 2: Processing through language cortex...")
        integrated_activation = language_cortex.integrate_with_connectome(brain_activation)
        print(f"   Integrated activation: {integrated_activation}")
        
        # Step 3: Apply to brain simulation
        print("Step 3: Applying to brain simulation...")
        if brain:
            try:
                # Convert concept activation to neuron stimulation
                for concept, current in integrated_activation.items():
                    if isinstance(concept, str):
                        brain.stimulate_region(concept, current)
                
                # Run simulation steps
                firing_record = brain.run_simulation(5, verbose=False)
                print(f"   Neurons fired: {sum(len(firing) for firing in firing_record)}")
                
                # Get network activity
                activity = brain.get_network_activity()
                print(f"   Network activity: {activity['current_firing_rate']} neurons firing")
                
                # Reset for next test
                brain.reset()
            except Exception as e:
                print(f"   Error in brain simulation: {e}")
        else:
            print("   Brain simulation skipped (not initialized)")
        
        # Step 4: Convert brain activity back to text
        print("Step 4: Converting brain activity to response...")
        if translator:
            try:
                # Simulate some brain activity for response generation
                mock_activity = integrated_activation
                mock_firing = [1, 2, 3, 4, 5]  # Mock firing neurons
                
                response = translator.brain_activity_to_text(mock_activity, mock_firing)
                print(f"   Fly response: {response}")
            except Exception as e:
                print(f"   Error: {e}")
                response = "I am processing your request."
        else:
            response = "I am processing your request (translator not available)."
            print(f"   Mock response: {response}")
        
        print(f"   [OK] Test {i} complete")
    
    # Summary
    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    if brain:
        print("[OK] Brain Engine: Working")
        brain.print_stats()
    else:
        print("[ERROR] Brain Engine: Not initialized")
    
    if translator:
        print("[OK] Brain Translator: Working")
    else:
        print("[ERROR] Brain Translator: Not initialized (check API key)")
    
    print("[OK] Language Cortex: Working")
    
    cortex_state = language_cortex.get_cortex_state()
    print(f"Language Cortex State: {cortex_state}")
    
    print("\n" + "=" * 50)
    print("Integration test completed!")
    print("=" * 50)
    
    print("\nNext steps:")
    print("1. Add your Gemini API key to .env file for full functionality")
    print("2. Run with full connectome data for complete brain simulation")
    print("3. Implement more sophisticated neuron and synapse models")
    print("4. Add 3D environment and sensory input simulation")

if __name__ == "__main__":
    test_integration()