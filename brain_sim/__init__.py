"""
Brain Simulation Module
Simulates neural activity in the MaleCNS fruit fly connectome
"""

try:
    from .neuron_models import Neuron, NeuronPopulation
    from .brain_engine import BrainEngine
    from .synapse_models import Synapse
except ImportError:
    from neuron_models import Neuron, NeuronPopulation
    from brain_engine import BrainEngine
    from synapse_models import Synapse

__all__ = ['Neuron', 'NeuronPopulation', 'BrainEngine', 'Synapse']