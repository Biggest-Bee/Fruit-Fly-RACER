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
    Individual synapse model with plasticity and Hebbian learning
    """
    
    def __init__(self, pre_neuron_id: int, post_neuron_id: int, weight: float,
                 distance: float = 1.0):
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
        
        # Distance-based properties
        self.distance = distance
        self.distance_probability = 1.0 / max(distance, 0.1)  # 1/distance
        
        # Hebbian learning properties
        self.activation_count = 0
        self.co_activation_count = 0  # Both pre and post active together
        self.hebbian_strength = 0.0  # Learned shortcut strength
        self.is_shortcut = False  # Whether this is a learned shortcut connection
        self.usage_frequency = 0.0  # How often this path is used
    
    def get_effective_weight(self) -> float:
        """Get current effective weight with short-term plasticity and Hebbian learning"""
        base_weight = self.weight * self.depression_factor * self.facilitation_factor
        
        # Add Hebbian shortcut strength if this is a shortcut
        if self.is_shortcut:
            base_weight += self.hebbian_strength
        
        return base_weight
    
    def activate(self):
        """Activate synapse and update plasticity"""
        self.last_activation = 1.0
        self.activation_count += 1
        
        # Short-term depression
        self.depression_factor *= (1 - self.depression)
        
        # Short-term facilitation
        self.facilitation_factor += self.facilitation
    
    def co_activate(self):
        """
        Record co-activation of pre and post synaptic neurons
        This is used for Hebbian learning of shortcuts
        """
        self.co_activation_count += 1
        self.usage_frequency += 1.0
        
        # Hebbian learning: strengthen connection if frequently co-activated
        if self.co_activation_count > 10:
            # Strengthen based on co-activation frequency
            self.hebbian_strength = min(2.0, self.hebbian_strength + 0.1)
            
            # If this connection is strong enough, mark as shortcut
            if self.hebbian_strength > 0.5 and not self.is_shortcut:
                self.is_shortcut = True
                print(f"Shortcut formed: {self.pre_neuron_id} -> {self.post_neuron_id}")
    
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
        """Build synapse objects for detailed simulation with distance-based probability"""
        print("Building synapse objects with distance-based connections...")
        
        # Build a subset of synapses for detailed simulation
        # For full simulation, we'd use the matrix approach
        sample_size = min(10000, len(self.connectome))
        sample_connections = self.connectome.head(sample_size)
        
        for _, row in sample_connections.iterrows():
            pre_id = int(row['body_pre'])
            post_id = int(row['body_post'])
            weight = float(row['weight'])
            
            # Calculate distance (simplified - in real implementation would use spatial coordinates)
            distance = self._calculate_neuron_distance(pre_id, post_id)
            
            # Calculate connection probability based on distance
            connection_prob = 1.0 / max(distance, 0.1)
            
            # Only create synapse if probability check passes (for long-distance shortcuts)
            # Always create for existing connectome connections
            synapse = Synapse(pre_id, post_id, weight, distance)
            self.synapses[(pre_id, post_id)] = synapse
        
        print(f"Created {len(self.synapses)} detailed synapse objects")
    
    def _calculate_neuron_distance(self, neuron_id1: int, neuron_id2: int) -> float:
        """
        Calculate distance between two neurons.
        This is a simplified calculation - in a real implementation would use
        spatial coordinates from the connectome data.
        """
        # Simple ID-based distance as proxy for spatial distance
        # In real implementation, would use actual 3D coordinates
        return abs(neuron_id1 - neuron_id2) / 1000.0  # Normalize to reasonable range
    
    def create_shortcut_connection(self, pre_neuron_id: int, post_neuron_id: int,
                                   weight: float = 1.0) -> bool:
        """
        Create a shortcut connection between two neurons that are frequently used together.
        This bypasses the normal multi-hop path.
        
        Args:
            pre_neuron_id: Presynaptic neuron ID
            post_neuron_id: Postsynaptic neuron ID
            weight: Connection weight
            
        Returns:
            True if shortcut was created
        """
        # Check if connection already exists
        if (pre_neuron_id, post_neuron_id) in self.synapses:
            existing = self.synapses[(pre_neuron_id, post_neuron_id)]
            existing.is_shortcut = True
            existing.hebbian_strength = max(existing.hebbian_strength, weight)
            return True
        
        # Calculate distance
        distance = self._calculate_neuron_distance(pre_neuron_id, post_neuron_id)
        
        # Create new shortcut synapse
        synapse = Synapse(pre_neuron_id, post_neuron_id, weight, distance)
        synapse.is_shortcut = True
        synapse.hebbian_strength = weight
        
        self.synapses[(pre_neuron_id, post_neuron_id)] = synapse
        
        print(f"Created shortcut: {pre_neuron_id} -> {post_neuron_id} (distance: {distance:.2f})")
        return True
    
    def detect_frequent_path(self, path: List[int], threshold: int = 10) -> bool:
        """
        Detect if a path is frequently used and should have a shortcut.
        
        Args:
            path: List of neuron IDs in the path
            threshold: Usage threshold for shortcut formation
            
        Returns:
            True if shortcut should be created
        """
        if len(path) < 2:
            return False
        
        # Check if the direct connections in the path are frequently co-activated
        total_co_activation = 0
        
        for i in range(len(path) - 1):
            pre = path[i]
            post = path[i + 1]
            synapse = self.get_synapse(pre, post)
            if synapse:
                total_co_activation += synapse.co_activation_count
        
        # If path is frequently used, create shortcut from start to end
        if total_co_activation > threshold:
            self.create_shortcut_connection(path[0], path[-1])
            return True
        
        return False
    
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