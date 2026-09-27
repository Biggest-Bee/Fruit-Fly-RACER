"""
Synapse Models for Fruit Fly Brain Simulation
Implements synaptic connections and dynamics based on connectome weights
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import scipy.sparse as sp
import sys
import os

# Add parent directory to path for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class Synapse:
    """
    Individual synapse model with plasticity
    """
    
    def __init__(self, pre_neuron_id: int, post_neuron_id: int, weight: float):
        self.pre_neuron_id = pre_neuron_id
        self.post_neuron_id = post_neuron_id
        self.weight = weight
        self.base_weight = weight
        self.last_activation = 0.0
        
        # Synaptic parameters
        self.depression = 0.1  # Short-term depression
        self.facilitation = 0.02  # Short-term facilitation
        self.depression_factor = 1.0
        self.facilitation_factor = 1.0
    
    def get_effective_weight(self) -> float:
        """Get current effective weight with short-term plasticity"""
        return self.weight * self.depression_factor * self.facilitation_factor
    
    def activate(self):
        """Activate synapse and update plasticity"""
        self.last_activation = 1.0
        
        # Short-term depression
        self.depression_factor *= (1 - self.depression)
        
        # Short-term facilitation
        self.facilitation_factor += self.facilitation
    
    def deactivate(self):
        """Deactivate synapse and recover plasticity"""
        self.last_activation = 0.0
        
        # Recovery from depression
        self.depression_factor += (1 - self.depression_factor) * 0.1
        
        # Recovery from facilitation
        self.facilitation_factor -= (self.facilitation_factor - 1) * 0.1
        
        # Clamp factors
        self.depression_factor = np.clip(self.depression_factor, 0.1, 1.0)
        self.facilitation_factor = np.clip(self.facilitation_factor, 1.0, 2.0)


class SynapticConnectivity:
    """
    Manages the synaptic connectivity matrix from the connectome data
    """
    
    def __init__(self, connectome_file: str, max_synapses: Optional[int] = None):
        """
        Initialize synaptic connectivity from connectome weights file
        
        Args:
            connectome_file: Path to connectome weights feather file
            max_synapses: Maximum number of synapses to load (for testing)
        """
        print(f"Loading connectome data from {connectome_file}...")
        
        # Load the connectivity data
        self.connectome = pd.read_feather(connectome_file)
        
        if max_synapses:
            self.connectome = self.connectome.head(max_synapses)
        
        print(f"Loaded {len(self.connectome)} synaptic connections")
        
        # Build sparse adjacency matrix for efficient computation
        self._build_connectivity_matrix()
        
        # Build synapse objects for detailed simulation
        self.synapses: Dict[Tuple[int, int], Synapse] = {}
        self._build_synapse_objects()
        
    def _build_connectivity_matrix(self):
        """Build sparse adjacency matrix for efficient connectivity queries"""
        print("Building connectivity matrix...")
        
        # Get unique neuron IDs
        self.neuron_ids = set(self.connectome['body_pre'].unique()) | set(self.connectome['body_post'].unique())
        self.neuron_ids = sorted(list(self.neuron_ids))
        
        # Create mapping from neuron ID to matrix index
        self.neuron_to_index = {nid: idx for idx, nid in enumerate(self.neuron_ids)}
        self.index_to_neuron = {idx: nid for nid, idx in self.neuron_to_index.items()}
        
        # Build sparse matrix
        n_neurons = len(self.neuron_ids)
        row_indices = [self.neuron_to_index[nid] for nid in self.connectome['body_pre']]
        col_indices = [self.neuron_to_index[nid] for nid in self.connectome['body_post']]
        weights = self.connectome['weight'].values
        
        self.adjacency_matrix = sp.csr_matrix((weights, (row_indices, col_indices)), 
                                              shape=(n_neurons, n_neurons))
        
        print(f"Built adjacency matrix: {n_neurons} neurons, {self.adjacency_matrix.nnz} connections")
    
    def _build_synapse_objects(self):
        """Build synapse objects for detailed simulation"""
        print("Building synapse objects...")
        
        # Build a subset of synapses for detailed simulation
        # For full simulation, we'd use the matrix approach
        sample_size = min(10000, len(self.connectome))
        sample_connections = self.connectome.head(sample_size)
        
        for _, row in sample_connections.iterrows():
            pre_id = int(row['body_pre'])
            post_id = int(row['body_post'])
            weight = float(row['weight'])
            
            synapse = Synapse(pre_id, post_id, weight)
            self.synapses[(pre_id, post_id)] = synapse
        
        print(f"Created {len(self.synapses)} detailed synapse objects")
    
    def get_inputs_for_neuron(self, neuron_id: int) -> List[Tuple[int, float]]:
        """
        Get all input connections for a specific neuron
        
        Args:
            neuron_id: ID of the neuron
            
        Returns:
            List of (pre_neuron_id, weight) tuples
        """
        if neuron_id not in self.neuron_to_index:
            return []
        
        idx = self.neuron_to_index[neuron_id]
        
        # Get column from sparse matrix (inputs to this neuron)
        column = self.adjacency_matrix[:, idx]
        inputs = column.nonzero()
        
        result = []
        for row_idx in inputs[0]:
            pre_neuron_id = self.index_to_neuron[row_idx]
            weight = column[row_idx, 0]
            result.append((pre_neuron_id, weight))
        
        return result
    
    def get_outputs_for_neuron(self, neuron_id: int) -> List[Tuple[int, float]]:
        """
        Get all output connections for a specific neuron
        
        Args:
            neuron_id: ID of the neuron
            
        Returns:
            List of (post_neuron_id, weight) tuples
        """
        if neuron_id not in self.neuron_to_index:
            return []
        
        idx = self.neuron_to_index[neuron_id]
        
        # Get row from sparse matrix (outputs from this neuron)
        row = self.adjacency_matrix[idx, :]
        outputs = row.nonzero()
        
        result = []
        for col_idx in outputs[1]:
            post_neuron_id = self.index_to_neuron[col_idx]
            weight = row[0, col_idx]
            result.append((post_neuron_id, weight))
        
        return result
    
    def get_synapse(self, pre_neuron_id: int, post_neuron_id: int) -> Optional[Synapse]:
        """Get detailed synapse object if available"""
        return self.synapses.get((pre_neuron_id, post_neuron_id))
    
    def propagate_activity(self, firing_neurons: List[int]) -> Dict[int, float]:
        """
        Propagate activity from firing neurons to their postsynaptic targets
        
        Args:
            firing_neurons: List of neuron IDs that fired
            
        Returns:
            Dictionary mapping post_neuron_id -> total_input_current
        """
        input_currents = {}
        
        for neuron_id in firing_neurons:
            outputs = self.get_outputs_for_neuron(neuron_id)
            
            for post_neuron_id, weight in outputs:
                # Add weighted input to postsynaptic neuron
                if post_neuron_id not in input_currents:
                    input_currents[post_neuron_id] = 0.0
                input_currents[post_neuron_id] += weight
                
                # Update detailed synapse if available
                synapse = self.get_synapse(neuron_id, post_neuron_id)
                if synapse:
                    synapse.activate()
        
        return input_currents
    
    def update_synapses(self):
        """Update all synapses (recovery from plasticity)"""
        for synapse in self.synapses.values():
            synapse.deactivate()
    
    def get_connectivity_stats(self) -> dict:
        """Get statistics about the connectivity"""
        n_neurons = len(self.neuron_ids)
        n_connections = self.adjacency_matrix.nnz
        
        # Calculate connection statistics
        weight_stats = {
            "min": float(self.connectome['weight'].min()),
            "max": float(self.connectome['weight'].max()),
            "mean": float(self.connectome['weight'].mean()),
            "median": float(self.connectome['weight'].median())
        }
        
        return {
            "total_neurons": n_neurons,
            "total_connections": n_connections,
            "average_connections_per_neuron": n_connections / n_neurons if n_neurons > 0 else 0,
            "weight_statistics": weight_stats,
            "sparsity": n_connections / (n_neurons * n_neurons) if n_neurons > 0 else 0
        }


if __name__ == "__main__":
    # Test the synapse models
    print("Testing Synapse Models...")
    
    # Create a single synapse
    synapse = Synapse(100, 200, 5.0)
    print(f"Created synapse from neuron {synapse.pre_neuron_id} to {synapse.post_neuron_id}")
    print(f"Base weight: {synapse.base_weight}")
    
    # Test synapse activation
    print("\nTesting synapse activation:")
    for i in range(5):
        effective_weight = synapse.get_effective_weight()
        print(f"Step {i}: Effective weight = {effective_weight:.3f}")
        synapse.activate()
    
    print("\nSynapse model test completed!")