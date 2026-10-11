"""
Brain Engine for Fruit Fly Brain Simulation
Main simulation engine that coordinates neurons and synapses
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import time
from collections import deque
import sys
import os

# Add parent directory to path for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from .neuron_models import NeuronPopulation
    from .synapse_models import SynapticConnectivity
except ImportError:
    from neuron_models import NeuronPopulation
    from synapse_models import SynapticConnectivity

# Enhanced regions are optional (removed in racing simulation)
try:
    from .enhanced_human_regions import EnhancedHumanBrainIntegration
except ImportError:
    EnhancedHumanBrainIntegration = None

# Translator is optional (removed in racing simulation)
try:
    from llm_interface.translator import BrainTranslator
except ImportError:
    BrainTranslator = None


class BrainEngine:
    """
    Main brain simulation engine
    Coordinates neural activity and synaptic transmission
    """
    
    def __init__(self, annotations_file: str = None, connectome_file: str = None, 
                 max_neurons: Optional[int] = None, max_synapses: Optional[int] = None,
                 enable_enhanced_regions: bool = False,
                 prefrontal_neurons: int = 100000,
                 wernicke_neurons: int = 100000):
        """
        Initialize the brain simulation engine
        
        Args:
            annotations_file: Path to neuron annotations file (optional)
            connectome_file: Path to connectome weights file (optional)
            max_neurons: Maximum number of neurons to load (for testing)
            max_synapses: Maximum number of synapses to load (for testing)
            enable_enhanced_regions: Whether to enable enhanced human-like brain regions
            prefrontal_neurons: Number of neurons in Prefrontal Cortex
            wernicke_neurons: Number of neurons in Wernicke's Area
        """
        print("Initializing Brain Engine...")
        self.start_time = time.time()
        
        # Load neuron population (if files provided)
        if annotations_file and os.path.exists(annotations_file):
            self.neuron_population = NeuronPopulation(annotations_file, max_neurons=max_neurons)
        else:
            print("No annotations file provided, using empty neuron population")
            self.neuron_population = None
        
        # Load synaptic connectivity (if files provided)
        if connectome_file and os.path.exists(connectome_file):
            self.synaptic_connectivity = SynapticConnectivity(connectome_file, max_synapses)
        else:
            print("No connectome file provided, using empty synaptic connectivity")
            self.synaptic_connectivity = None
        
        # Initialize enhanced human-like brain regions (optional)
        self.enable_enhanced_regions = enable_enhanced_regions
        if enable_enhanced_regions and EnhancedHumanBrainIntegration:
            self.enhanced_brain = EnhancedHumanBrainIntegration(
                prefrontal_neurons=prefrontal_neurons,
                wernicke_neurons=wernicke_neurons
            )
            # Integrate with connectome
            integration_stats = self.enhanced_brain.integrate_with_connectome(self)
            print(f"Enhanced regions integrated: {integration_stats['percentage']:.2f}% additional neurons")
        else:
            self.enhanced_brain = None
        
        # Initialize brain translator (optional, removed in racing simulation)
        self.brain_translator = None
        if BrainTranslator:
            try:
                self.brain_translator = BrainTranslator(enable_wernicke=enable_enhanced_regions)
                print("Brain translator connected to brain engine")
            except Exception as e:
                print(f"Brain translator not available: {e}")
        
        # Simulation state
        self.current_time = 0.0
        self.dt = 0.1  # Time step in milliseconds
        self.firing_history = deque(maxlen=1000)  # Keep track of recent firing
        
        # Input/output buffers
        self.external_inputs: Dict[int, float] = {}
        self.external_outputs: Dict[int, float] = {}
        
        # Performance tracking
        self.simulation_steps = 0
        self.total_fired_neurons = 0
        
        print("Brain Engine initialized successfully!")
        self.print_stats()
    
    def print_stats(self):
        """Print brain engine statistics"""
        neuron_stats = self.neuron_population.get_population_stats()
        synapse_stats = self.synaptic_connectivity.get_connectivity_stats()
        
        print("\n=== Brain Engine Statistics ===")
        print(f"Connectome Neurons: {neuron_stats['total_neurons']}")
        print(f"Neuron types: {neuron_stats['type_distribution']}")
        print(f"Synaptic connections: {synapse_stats['total_connections']}")
        print(f"Average connections per neuron: {synapse_stats['average_connections_per_neuron']:.2f}")
        print(f"Network sparsity: {synapse_stats['sparsity']:.6f}")
        print(f"Weight range: {synapse_stats['weight_statistics']['min']:.2f} to {synapse_stats['weight_statistics']['max']:.2f}")
        
        if self.enable_enhanced_regions and self.enhanced_brain:
            enhanced_stats = self.enhanced_brain.get_statistics()
            print(f"\nEnhanced Regions:")
            print(f"  Prefrontal Cortex: {enhanced_stats['prefrontal_cortex']['total_neurons']:,} neurons")
            print(f"  Wernicke's Area: {enhanced_stats['wernicke_area']['total_neurons']:,} neurons")
            print(f"  Integration ratio: {enhanced_stats['integration']['ratio']:.4f}")
        
        print("=" * 30 + "\n")
    
    def step(self) -> Dict[int, float]:
        """
        Advance the simulation by one time step
        
        Returns:
            Dictionary of neuron IDs that fired in this step
        """
        self.simulation_steps += 1
        self.current_time += self.dt
        
        # Start with external inputs
        input_currents = self.external_inputs.copy()
        
        # Add propagated activity from previous step
        if hasattr(self, 'last_fired_neurons'):
            propagated_inputs = self.synaptic_connectivity.propagate_activity(self.last_fired_neurons)
            for neuron_id, current in propagated_inputs.items():
                input_currents[neuron_id] = input_currents.get(neuron_id, 0.0) + current
        
        # Update all neurons
        fired_neurons = self.neuron_population.update_population(input_currents, self.dt)
        
        # Store firing for next step
        self.last_fired_neurons = fired_neurons
        self.firing_history.append(fired_neurons)
        self.total_fired_neurons += len(fired_neurons)
        
        # Update synapses (recovery)
        self.synaptic_connectivity.update_synapses()
        
        # Clear external inputs (they're one-time)
        self.external_inputs.clear()
        
        return fired_neurons
    
    def stimulate_neuron(self, neuron_id: int, current: float):
        """
        Apply external stimulation to a specific neuron
        
        Args:
            neuron_id: ID of neuron to stimulate
            current: Current to apply (in arbitrary units)
        """
        self.external_inputs[neuron_id] = self.external_inputs.get(neuron_id, 0.0) + current
    
    def stimulate_region(self, neuron_type: str, current: float):
        """
        Stimulate all neurons of a specific type
        
        Args:
            neuron_type: Type of neurons to stimulate
            current: Current to apply to each neuron
        """
        neuron_ids = self.neuron_population.get_neurons_by_type(neuron_type)
        for neuron_id in neuron_ids:
            self.stimulate_neuron(neuron_id, current)
    
    def run_simulation(self, steps: int, verbose: bool = True) -> List[List[int]]:
        """
        Run simulation for multiple steps
        
        Args:
            steps: Number of simulation steps
            verbose: Whether to print progress
            
        Returns:
            List of firing neuron lists for each step
        """
        if verbose:
            print(f"Running simulation for {steps} steps...")
        
        firing_record = []
        
        for step in range(steps):
            fired = self.step()
            firing_record.append(fired)
            
            if verbose and step % 100 == 0:
                print(f"  Step {step}: {len(fired)} neurons fired")
        
        if verbose:
            print(f"Simulation complete. Total neurons fired: {self.total_fired_neurons}")
        
        return firing_record
    
    def get_neuron_activity(self, neuron_id: int) -> dict:
        """
        Get current activity state of a specific neuron
        
        Args:
            neuron_id: ID of neuron
            
        Returns:
            Dictionary with neuron state information
        """
        neuron = self.neuron_population.get_neuron(neuron_id)
        if not neuron:
            return None
        
        return {
            "id": neuron.id,
            "type": neuron.type,
            "membrane_potential": neuron.membrane_potential,
            "threshold": neuron.threshold,
            "is_firing": neuron.is_firing,
            "last_spike_time": neuron.last_spike_time
        }
    
    def get_network_activity(self) -> dict:
        """
        Get overall network activity statistics
        
        Returns:
            Dictionary with network activity metrics
        """
        recent_firing = list(self.firing_history)
        
        if not recent_firing:
            return {
                "current_firing_rate": 0.0,
                "average_firing_rate": 0.0,
                "active_neurons": 0
            }
        
        # Calculate firing rates
        current_firing = len(recent_firing[-1]) if recent_firing else 0
        avg_firing = sum(len(firing) for firing in recent_firing) / len(recent_firing)
        
        return {
            "simulation_time": self.current_time,
            "simulation_steps": self.simulation_steps,
            "current_firing_rate": current_firing,
            "average_firing_rate": avg_firing,
            "total_fired_neurons": self.total_fired_neurons,
            "active_neurons": len(recent_firing[-1]) if recent_firing else 0
        }
    
    def reset(self):
        """Reset the simulation to initial state"""
        self.current_time = 0.0
        self.simulation_steps = 0
        self.total_fired_neurons = 0
        self.firing_history.clear()
        self.external_inputs.clear()
        self.external_outputs.clear()
        
        # Reset all neurons
        for neuron in self.neuron_population.neurons.values():
            neuron.reset()
        
        print("Brain simulation reset to initial state")


if __name__ == "__main__":
    # Test the brain engine
    print("Testing Brain Engine...")
    
    try:
        from neuron_models import NeuronPopulation
        from synapse_models import SynapticConnectivity
    except ImportError:
        from brain_sim.neuron_models import NeuronPopulation
        from brain_sim.synapse_models import SynapticConnectivity
    
    # Use smaller datasets for testing
    annotations_file = "../data/body-annotations-male-cns-v1.0-minconf-0.5.feather"
    connectome_file = "../data/connectome-weights-male-cns-v1.0-minconf-0.5.feather"
    
    try:
        # Initialize brain engine with limited data for testing
        brain = BrainEngine(annotations_file, connectome_file, max_synapses=10000)
        
        # Test basic stimulation
        print("\nTesting neuron stimulation...")
        sensory_neurons = brain.neuron_population.get_neurons_by_type("sensory")
        if sensory_neurons:
            test_neuron = sensory_neurons[0]
            brain.stimulate_neuron(test_neuron, 50.0)
            print(f"Stimulated sensory neuron {test_neuron}")
        
        # Run a short simulation
        print("\nRunning short simulation...")
        firing_record = brain.run_simulation(10, verbose=True)
        
        # Check network activity
        activity = brain.get_network_activity()
        print(f"\nNetwork activity: {activity}")
        
        print("\nBrain engine test completed!")
        
    except Exception as e:
        print(f"Error during brain engine test: {e}")
        print("This is expected if the data files are not in the correct location.")