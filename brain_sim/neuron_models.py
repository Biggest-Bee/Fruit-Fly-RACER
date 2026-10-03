"""
Neuron Models for Fruit Fly Brain Simulation
Implements simplified neuron models based on the MaleCNS connectome data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import time
import sys
import os

# Add parent directory to path for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from learning_system.memory_integrity import MemoryIntegrity
except ImportError:
    from memory_integrity import MemoryIntegrity

class Neuron:
    """
    Individual neuron model using Integrate-and-Fire dynamics
    """
    
    def __init__(self, neuron_id: int, neuron_type: str = "interneuron"):
        self.id = neuron_id
        self.type = neuron_type
        self.membrane_potential = -70.0  # Resting potential in mV
        self.threshold = -55.0  # Firing threshold in mV
        self.resting_potential = -70.0
        self.refractory_period = 2.0  # ms
        self.last_spike_time = -1000.0
        self.is_firing = False
        
        # Neuron parameters based on type
        self._set_parameters_by_type()
        
    def _set_parameters_by_type(self):
        """Set neuron parameters based on cell type"""
        type_params = {
            "sensory": {"threshold": -50.0, "refractory": 1.0},
            "motor": {"threshold": -55.0, "refractory": 2.0},
            "interneuron": {"threshold": -55.0, "refractory": 2.0},
            "modulatory": {"threshold": -60.0, "refractory": 5.0},
            # New synthetic neuron types with 100% fireability
            "prefrontal_cortex": {"threshold": -45.0, "refractory": 0.5},
            "wernicke_area": {"threshold": -45.0, "refractory": 0.5},
            "math_processor": {"threshold": -48.0, "refractory": 0.8},
            "pattern_detector": {"threshold": -48.0, "refractory": 0.8},
            "coding_processor": {"threshold": -45.0, "refractory": 0.5},
            "self_correction": {"threshold": -47.0, "refractory": 0.7},
            "arithmetic_processor": {"threshold": -48.0, "refractory": 0.8},
            "algebraic_processor": {"threshold": -48.0, "refractory": 0.8},
            "logical_processor": {"threshold": -48.0, "refractory": 0.8},
            "statistical_processor": {"threshold": -48.0, "refractory": 0.8},
            "advanced_processor": {"threshold": -48.0, "refractory": 0.8},
            "visual_pattern_detector": {"threshold": -48.0, "refractory": 0.8},
            "code_pattern_detector": {"threshold": -45.0, "refractory": 0.5},
            "sequence_pattern_detector": {"threshold": -48.0, "refractory": 0.8},
            "anomaly_detector": {"threshold": -48.0, "refractory": 0.8},
            "syntax_analyzer": {"threshold": -45.0, "refractory": 0.5},
            "semantic_analyzer": {"threshold": -45.0, "refractory": 0.5},
            "code_generator": {"threshold": -45.0, "refractory": 0.5},
            "pattern_matcher": {"threshold": -45.0, "refractory": 0.5},
            "optimizer": {"threshold": -45.0, "refractory": 0.5},
            "debugger": {"threshold": -45.0, "refractory": 0.5},
            "language_adapter": {"threshold": -45.0, "refractory": 0.5}
        }
        
        params = type_params.get(self.type, type_params["interneuron"])
        self.threshold = params["threshold"]
        self.refractory_period = params["refractory"]
    
    def update(self, input_current: float, dt: float = 0.1) -> bool:
        """
        Update neuron state for one time step
        
        Args:
            input_current: Total input current from synapses
            dt: Time step in milliseconds
            
        Returns:
            bool: True if neuron fired, False otherwise
        """
        current_time = time.time() * 1000  # Convert to ms
        
        # Check refractory period
        if current_time - self.last_spike_time < self.refractory_period:
            self.membrane_potential = self.resting_potential
            return False
        
        # Integrate input current (simplified membrane equation)
        # dV/dt = (I - V) / tau
        tau = 10.0  # Membrane time constant in ms
        dV = (input_current - self.membrane_potential) / tau * dt
        self.membrane_potential += dV
        
        # Check for firing
        if self.membrane_potential >= self.threshold:
            self.fire(current_time)
            return True
        
        # Decay towards resting potential
        self.membrane_potential += (self.resting_potential - self.membrane_potential) * 0.1 * dt
        
        return False
    
    def fire(self, current_time: float):
        """Fire the neuron"""
        self.membrane_potential = 30.0  # Spike peak
        self.last_spike_time = current_time
        self.is_firing = True
        
        # Reset after spike
        self.membrane_potential = self.resting_potential
        self.is_firing = False
    
    def reset(self):
        """Reset neuron to resting state"""
        self.membrane_potential = self.resting_potential
        self.last_spike_time = -1000.0
        self.is_firing = False


class NeuronPopulation:
    """
    Manages a population of neurons with efficient bulk operations and memory integrity
    """
    
    def __init__(self, annotations_file: str, enable_memory_integrity: bool = True):
        """
        Initialize neuron population from connectome annotations
        
        Args:
            annotations_file: Path to body annotations feather file
            enable_memory_integrity: Whether to enable memory integrity for conflict resolution
        """
        print(f"Loading neuron annotations from {annotations_file}...")
        self.annotations = pd.read_feather(annotations_file)
        print(f"Loaded {len(self.annotations)} neuron annotations")
        
        self.neurons: Dict[int, Neuron] = {}
        self._initialize_neurons()
        
        # Memory integrity for conflict resolution
        self.enable_memory_integrity = enable_memory_integrity
        if enable_memory_integrity:
            self.memory_integrity = MemoryIntegrity()
            print("Memory integrity enabled for neuron population")
        else:
            self.memory_integrity = None
        
    def _initialize_neurons(self):
        """Initialize neurons from annotations"""
        print("Initializing neuron models...")
        
        for idx, row in self.annotations.iterrows():
            neuron_id = row['bodyId']
            neuron_type = self._determine_neuron_type(row)
            
            neuron = Neuron(neuron_id, neuron_type)
            self.neurons[neuron_id] = neuron
            
            if idx % 10000 == 0:
                print(f"  Initialized {idx} neurons...")
        
        print(f"Total neurons initialized: {len(self.neurons)}")
    
    def _determine_neuron_type(self, row) -> str:
        """Determine neuron type from annotations"""
        # Use available annotations to classify neurons
        if pd.notna(row.get('class')):
            neuron_class = row['class'].lower()
            if 'sensory' in neuron_class:
                return 'sensory'
            elif 'motor' in neuron_class:
                return 'motor'
            elif 'modulatory' in neuron_class:
                return 'modulatory'
        
        return 'interneuron'  # Default
    
    def get_neuron(self, neuron_id: int) -> Optional[Neuron]:
        """Get neuron by ID"""
        return self.neurons.get(neuron_id)
    
    def get_neuron_info(self, neuron_id: int) -> Optional[dict]:
        """Get neuron annotation information"""
        neuron_data = self.annotations[self.annotations['bodyId'] == neuron_id]
        if not neuron_data.empty:
            return neuron_data.iloc[0].to_dict()
        return None
    
    def get_neurons_by_type(self, neuron_type: str) -> List[int]:
        """Get all neuron IDs of a specific type"""
        return [nid for nid, neuron in self.neurons.items() if neuron.type == neuron_type]
    
    def update_population(self, input_currents: Dict[int, float], dt: float = 0.1) -> List[int]:
        """
        Update all neurons with their input currents
        
        Args:
            input_currents: Dictionary mapping neuron_id -> input_current
            dt: Time step in milliseconds
            
        Returns:
            List of neuron IDs that fired
        """
        fired_neurons = []
        
        for neuron_id, current in input_currents.items():
            neuron = self.neurons.get(neuron_id)
            if neuron and neuron.update(current, dt):
                fired_neurons.append(neuron_id)
        
        return fired_neurons
    
    def get_population_stats(self) -> dict:
        """Get statistics about the neuron population"""
        type_counts = {}
        for neuron in self.neurons.values():
            type_counts[neuron.type] = type_counts.get(neuron.type, 0) + 1
        
        return {
            "total_neurons": len(self.neurons),
            "type_distribution": type_counts,
            "annotation_columns": self.annotations.columns.tolist()
        }


if __name__ == "__main__":
    # Test the neuron models
    print("Testing Neuron Models...")
    
    # Create a single neuron
    neuron = Neuron(12345, "sensory")
    print(f"Created neuron {neuron.id} of type {neuron.type}")
    print(f"Resting potential: {neuron.resting_potential} mV")
    print(f"Threshold: {neuron.threshold} mV")
    
    # Test neuron firing
    input_current = 20.0  # Strong input to trigger firing
    for i in range(10):
        fired = neuron.update(input_current)
        print(f"Step {i}: Potential = {neuron.membrane_potential:.2f} mV, Fired = {fired}")
    
    print("\nNeuron model test completed!")