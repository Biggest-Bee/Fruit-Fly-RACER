"""
Language Cortex
Synthetic brain extension for language processing capabilities
"""

import numpy as np
from typing import Dict, List, Optional
import json

class LanguageCortex:
    """
    Synthetic language processing cortex
    Extends the fly brain with language capabilities
    """
    
    def __init__(self, size: int = 1000):
        """
        Initialize the language cortex
        
        Args:
            size: Number of synthetic neurons in the language cortex
        """
        self.size = size
        self.neurons = np.zeros(size)
        self.weights = np.random.randn(size, size) * 0.1
        
        # Language regions (scaled to actual size)
        region_size = size // 4
        self.semantic_region = slice(0, region_size)    # Word meanings
        self.syntactic_region = slice(region_size, region_size * 2) # Grammar
        self.pragmatic_region = slice(region_size * 2, region_size * 3) # Context/use
        self.output_region = slice(region_size * 3, size)   # Response generation
        
        # Language state
        self.context_window = []
        self.max_context = 5
        
        print(f"Language Cortex initialized with {size} synthetic neurons")
    
    def process_input(self, language_activation: Dict[str, float]) -> np.ndarray:
        """
        Process language input and generate cortex activation
        
        Args:
            language_activation: Dictionary of language concepts to activation levels
            
        Returns:
            Activation pattern across the language cortex
        """
        # Reset cortex state
        self.neurons = np.zeros(self.size)
        
        # Map language concepts to cortex regions
        for concept, activation in language_activation.items():
            self._map_concept_to_cortex(concept, activation)
        
        # Propagate activity through cortex
        self._propagate_activity()
        
        # Update context
        self._update_context(language_activation)
        
        return self.neurons.copy()
    
    def _map_concept_to_cortex(self, concept: str, activation: float):
        """Map a language concept to specific cortex regions"""
        # This is a simplified mapping - would be more sophisticated in real implementation
        concept_lower = concept.lower()
        
        # Map to different regions based on concept type
        if concept in ["sensory", "look", "see", "hear"]:
            # Semantic processing
            start, end = self.semantic_region.start, self.semantic_region.stop
            # Ensure indices are within bounds
            indices = np.random.randint(start, min(end, self.size), size=10)
            self.neurons[indices] += activation * 0.5
            
        elif concept in ["motor", "move", "go", "fly"]:
            # Semantic + syntactic
            for region in [self.semantic_region, self.syntactic_region]:
                start, end = region.start, region.stop
                indices = np.random.randint(start, min(end, self.size), size=5)
                self.neurons[indices] += activation * 0.3
                
        elif concept in ["think", "understand", "learn"]:
            # Higher-level processing
            start, end = self.pragmatic_region.start, self.pragmatic_region.stop
            indices = np.random.randint(start, min(end, self.size), size=8)
            self.neurons[indices] += activation * 0.7
            
        else:
            # General semantic processing
            start, end = self.semantic_region.start, self.semantic_region.stop
            indices = np.random.randint(start, min(end, self.size), size=5)
            self.neurons[indices] += activation * 0.4
    
    def _propagate_activity(self):
        """Propagate activity through the cortex network"""
        # Simple propagation: neurons influence each other based on weights
        activation = np.dot(self.weights, self.neurons)
        
        # Apply activation function (tanh for bounded output)
        self.neurons = np.tanh(activation + self.neurons)
        
        # Normalize to prevent explosion
        max_activation = np.max(np.abs(self.neurons))
        if max_activation > 1.0:
            self.neurons = self.neurons / max_activation
    
    def _update_context(self, language_activation: Dict[str, float]):
        """Update the context window with current input"""
        self.context_window.append(language_activation.copy())
        if len(self.context_window) > self.max_context:
            self.context_window.pop(0)
    
    def generate_response(self, cortex_activation: np.ndarray) -> Dict[str, float]:
        """
        Generate response based on cortex activation
        
        Args:
            cortex_activation: Current activation pattern in the cortex
            
        Returns:
            Dictionary of response concepts with activation levels
        """
        # Extract output from output region
        output_activation = cortex_activation[self.output_region]
        
        # Generate response concepts based on output pattern
        response_concepts = {}
        
        # This is a simplified response generation
        # In real implementation, would use more sophisticated decoding
        if np.mean(output_activation) > 0.3:
            response_concepts["sensory"] = np.mean(output_activation) * 20
            response_concepts["interneuron"] = np.mean(output_activation) * 15
        
        # Incorporate context into response
        if self.context_window:
            context_influence = sum(ctx.get("interneuron", 0) for ctx in self.context_window)
            if "interneuron" in response_concepts:
                response_concepts["interneuron"] += context_influence * 0.3
            else:
                response_concepts["interneuron"] = context_influence * 0.3
        
        return response_concepts
    
    def integrate_with_connectome(self, brain_activation: Dict[int, float]) -> Dict[int, float]:
        """
        Integrate language cortex with the main connectome
        
        Args:
            brain_activation: Activation from the main brain
            
        Returns:
            Combined activation pattern
        """
        # Process any language concepts in brain activation
        language_concepts = {k: v for k, v in brain_activation.items() 
                           if isinstance(k, str)}
        
        if language_concepts:
            cortex_activation = self.process_input(language_concepts)
            response_concepts = self.generate_response(cortex_activation)
            
            # Merge response concepts back into brain activation
            combined = brain_activation.copy()
            for concept, activation in response_concepts.items():
                combined[concept] = combined.get(concept, 0.0) + activation
            
            return combined
        
        return brain_activation
    
    def reset(self):
        """Reset the language cortex state"""
        self.neurons = np.zeros(self.size)
        self.context_window = []
    
    def get_cortex_state(self) -> dict:
        """Get current state of the language cortex"""
        return {
            "size": self.size,
            "active_neurons": int(np.sum(self.neurons > 0.1)),
            "mean_activation": float(np.mean(self.neurons)),
            "max_activation": float(np.max(self.neurons)),
            "context_length": len(self.context_window)
        }


if __name__ == "__main__":
    # Test the language cortex
    print("Testing Language Cortex...")
    
    cortex = LanguageCortex(size=500)
    
    # Test input processing
    print("\nTesting input processing...")
    test_input = {"sensory": 30.0, "motor": 25.0, "interneuron": 20.0}
    activation = cortex.process_input(test_input)
    print(f"Input: {test_input}")
    print(f"Cortex activation shape: {activation.shape}")
    print(f"Active neurons: {np.sum(activation > 0.1)}")
    
    # Test response generation
    print("\nTesting response generation...")
    response = cortex.generate_response(activation)
    print(f"Response concepts: {response}")
    
    # Test integration
    print("\nTesting integration with connectome...")
    brain_activation = {"sensory": 30.0, "motor": 25.0, "interneuron": 20.0}
    integrated = cortex.integrate_with_connectome(brain_activation)
    print(f"Original activation: {brain_activation}")
    print(f"Integrated activation: {integrated}")
    
    # Test cortex state
    print("\nCortex state:")
    state = cortex.get_cortex_state()
    print(state)
    
    print("\nLanguage Cortex test completed!")