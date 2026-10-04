"""
Enhanced Human-Like Brain Regions
Adds 100k neurons to Prefrontal Cortex and 100k neurons to Wernicke's Area
These regions are designed to be 100% fireable and support advanced cognitive functions.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from .neuron_models import Neuron
except ImportError:
    from neuron_models import Neuron


class PrefrontalCortex:
    """
    Prefrontal Cortex - 100,000 neurons for human-like executive functions
    Supports coding, planning, decision-making, and complex problem-solving.
    All neurons are 100% fireable with optimized parameters.
    """
    
    def __init__(self, num_neurons: int = 100000):
        """
        Initialize the Prefrontal Cortex
        
        Args:
            num_neurons: Number of neurons (default 100,000)
        """
        self.num_neurons = num_neurons
        self.neurons: Dict[int, Neuron] = {}
        
        # Sub-regions of prefrontal cortex (initialize before calling _initialize_neurons)
        self.dorsolateral_pfc = set()  # Working memory, cognitive control
        self.ventromedial_pfc = set()  # Decision-making, emotion regulation
        self.orbitofrontal_pfc = set()  # Reward processing, value assessment
        self.anterior_cingulate = set()  # Error detection, conflict monitoring
        
        # Create neurons with specialized sub-regions
        self._initialize_neurons()
        
        # Cognitive state
        self.working_memory = {}  # Short-term memory for active tasks
        self.task_stack = []  # Stack of current tasks
        self.active_goals = {}  # Current goals and their priorities
        
        # Coding-specific state
        self.code_context = {}  # Current code being written
        self.language_state = {}  # State per programming language
        self.debugging_state = {}  # Active debugging sessions
        
        print(f"Prefrontal Cortex initialized with {num_neurons:,} neurons")
    
    def _initialize_neurons(self):
        """Initialize all neurons with specialized types"""
        # Distribute neurons across sub-regions
        region_size = self.num_neurons // 4
        
        start_id = 2000000  # Start IDs high to avoid conflict with connectome
        
        # Dorsolateral PFC (working memory, executive control)
        for i in range(region_size):
            neuron_id = start_id + i
            self.neurons[neuron_id] = Neuron(neuron_id, "prefrontal_cortex")
            self.dorsolateral_pfc.add(neuron_id)
        
        # Ventromedial PFC (decision-making)
        for i in range(region_size):
            neuron_id = start_id + region_size + i
            self.neurons[neuron_id] = Neuron(neuron_id, "prefrontal_cortex")
            self.ventromedial_pfc.add(neuron_id)
        
        # Orbitofrontal PFC (reward/value)
        for i in range(region_size):
            neuron_id = start_id + 2 * region_size + i
            self.neurons[neuron_id] = Neuron(neuron_id, "prefrontal_cortex")
            self.orbitofrontal_pfc.add(neuron_id)
        
        # Anterior Cingulate (error monitoring)
        for i in range(self.num_neurons - 3 * region_size):
            neuron_id = start_id + 3 * region_size + i
            self.neurons[neuron_id] = Neuron(neuron_id, "prefrontal_cortex")
            self.anterior_cingulate.add(neuron_id)
    
    def activate_coding_mode(self, language: str):
        """
        Activate coding mode for a specific programming language
        
        Args:
            language: Programming language (e.g., "python", "rust")
        """
        # Activate dorsolateral PFC for working memory
        for neuron_id in list(self.dorsolateral_pfc)[:1000]:
            neuron = self.neurons.get(neuron_id)
            if neuron:
                neuron.membrane_potential = -40.0  # High activation
        
        # Set language state
        self.language_state[language] = {
            "active": True,
            "proficiency": self.language_state.get(language, {}).get("proficiency", 0.0),
            "context": []
        }
        
        # Push coding task to stack
        self.task_stack.append({
            "type": "coding",
            "language": language,
            "priority": 1.0
        })
    
    def process_coding_task(self, task: str, context: Dict) -> Dict:
        """
        Process a coding task using executive functions
        
        Args:
            task: Description of the coding task
            context: Current context (variables, code, etc.)
            
        Returns:
            Processing result
        """
        # Use working memory to hold task
        task_id = f"task_{len(self.working_memory)}"
        self.working_memory[task_id] = {
            "task": task,
            "context": context,
            "status": "processing",
            "activation": 1.0
        }
        
        # Activate relevant neurons
        activation_count = 0
        for neuron_id in list(self.dorsolateral_pfc)[:500]:
            neuron = self.neurons.get(neuron_id)
            if neuron:
                neuron.membrane_potential = -45.0
                activation_count += 1
        
        return {
            "task_id": task_id,
            "status": "processing",
            "neurons_activated": activation_count,
            "working_memory_size": len(self.working_memory)
        }
    
    def evaluate_solution(self, solution: str, expected: str) -> Dict:
        """
        Evaluate a coding solution using error detection (anterior cingulate)
        
        Args:
            solution: Proposed solution
            expected: Expected solution
            
        Returns:
            Evaluation result
        """
        # Activate anterior cingulate for error detection
        for neuron_id in list(self.anterior_cingulate)[:200]:
            neuron = self.neurons.get(neuron_id)
            if neuron:
                neuron.membrane_potential = -42.0
        
        # Simple evaluation (would be more sophisticated in practice)
        similarity = self._calculate_similarity(solution, expected)
        
        if similarity > 0.8:
            verdict = "correct"
            confidence = similarity
        elif similarity > 0.5:
            verdict = "partially_correct"
            confidence = similarity
        else:
            verdict = "incorrect"
            confidence = 1.0 - similarity
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "similarity": similarity
        }
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        # Simple character-based similarity
        if not str1 or not str2:
            return 0.0
        
        set1 = set(str1.lower())
        set2 = set(str2.lower())
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def get_working_memory(self) -> Dict:
        """Get current working memory state"""
        return {
            "size": len(self.working_memory),
            "tasks": list(self.working_memory.keys()),
            "task_stack_depth": len(self.task_stack),
            "active_goals": list(self.active_goals.keys())
        }
    
    def reset(self):
        """Reset the prefrontal cortex state"""
        for neuron in self.neurons.values():
            neuron.reset()
        self.working_memory.clear()
        self.task_stack.clear()
        self.active_goals.clear()
        self.code_context.clear()
        self.debugging_state.clear()


class WernickeArea:
    """
    Wernicke's Area - 100,000 neurons for language comprehension and production
    Supports typing, talking with users, and language translation.
    All neurons are 100% fireable with optimized parameters.
    """
    
    def __init__(self, num_neurons: int = 100000):
        """
        Initialize Wernicke's Area
        
        Args:
            num_neurons: Number of neurons (default 100,000)
        """
        self.num_neurons = num_neurons
        self.neurons: Dict[int, Neuron] = {}
        
        # Sub-regions (initialize before _initialize_neurons)
        self.comprehension_region = set()  # Language comprehension
        self.production_region = set()  # Language production
        self.translation_region = set()  # Translation between brain activity and language
        self.semantic_network = set()  # Word meanings and concepts
        
        # Create neurons with specialized sub-regions
        self._initialize_neurons()
        
        # Language state
        self.vocabulary = {}  # Known words and their neural representations
        self.conversation_context = []  # Recent conversation history
        self.translation_buffer = {}  # Buffer for translation
        
        # Typing/talking state
        self.output_queue = []  # Queue of responses to output
        self.input_buffer = []  # Buffer of incoming text
        
        print(f"Wernicke's Area initialized with {num_neurons:,} neurons")
    
    def _initialize_neurons(self):
        """Initialize all neurons with specialized types"""
        region_size = self.num_neurons // 4
        
        start_id = 3000000  # Start IDs high to avoid conflict
        
        # Comprehension region
        for i in range(region_size):
            neuron_id = start_id + i
            self.neurons[neuron_id] = Neuron(neuron_id, "wernicke_area")
            self.comprehension_region.add(neuron_id)
        
        # Production region
        for i in range(region_size):
            neuron_id = start_id + region_size + i
            self.neurons[neuron_id] = Neuron(neuron_id, "wernicke_area")
            self.production_region.add(neuron_id)
        
        # Translation region
        for i in range(region_size):
            neuron_id = start_id + 2 * region_size + i
            self.neurons[neuron_id] = Neuron(neuron_id, "wernicke_area")
            self.translation_region.add(neuron_id)
        
        # Semantic network
        for i in range(self.num_neurons - 3 * region_size):
            neuron_id = start_id + 3 * region_size + i
            self.neurons[neuron_id] = Neuron(neuron_id, "wernicke_area")
            self.semantic_network.add(neuron_id)
    
    def comprehend_input(self, text: str) -> Dict:
        """
        Comprehend incoming text input
        
        Args:
            text: Input text to comprehend
            
        Returns:
            Comprehension result with neural activation pattern
        """
        # Activate comprehension region
        activation_pattern = {}
        
        words = text.lower().split()
        for i, word in enumerate(words[:100]):  # Limit to first 100 words
            # Map word to neurons
            neuron_id = list(self.comprehension_region)[i % len(self.comprehension_region)]
            neuron = self.neurons.get(neuron_id)
            if neuron:
                neuron.membrane_potential = -40.0
                activation_pattern[neuron_id] = 1.0
        
        # Store in conversation context
        self.conversation_context.append({
            "type": "input",
            "text": text,
            "timestamp": np.random.randint(0, 1000000)
        })
        
        if len(self.conversation_context) > 20:
            self.conversation_context.pop(0)
        
        return {
            "comprehended": True,
            "word_count": len(words),
            "activation_pattern": activation_pattern,
            "context_length": len(self.conversation_context)
        }
    
    def produce_response(self, brain_activity: Dict) -> str:
        """
        Produce a response based on brain activity
        
        Args:
            brain_activity: Dictionary of brain activation patterns
            
        Returns:
            Generated response text
        """
        # Activate production region
        for neuron_id in list(self.production_region)[:500]:
            neuron = self.neurons.get(neuron_id)
            if neuron:
                neuron.membrane_potential = -42.0
        
        # Generate response based on brain activity
        # This is a simplified generation - would be more sophisticated
        response_parts = []
        
        # Check for different activation patterns
        if "sensory" in brain_activity and brain_activity["sensory"] > 30:
            response_parts.append("I sense")
        
        if "motor" in brain_activity and brain_activity["motor"] > 25:
            response_parts.append("I want to move")
        
        if "interneuron" in brain_activity and brain_activity["interneuron"] > 20:
            response_parts.append("I'm thinking")
        
        if not response_parts:
            response_parts.append("I'm processing")
        
        response = " ".join(response_parts) + "."
        
        # Store in conversation context
        self.conversation_context.append({
            "type": "output",
            "text": response,
            "timestamp": np.random.randint(0, 1000000)
        })
        
        if len(self.conversation_context) > 20:
            self.conversation_context.pop(0)
        
        return response
    
    def translate_brain_to_english(self, brain_activity: Dict[int, float],
                                  firing_neurons: List[int]) -> str:
        """
        Translate brain activity to English text
        
        Args:
            brain_activity: Dictionary of neuron activations
            firing_neurons: List of neurons that fired
            
        Returns:
            English translation
        """
        # Activate translation region
        for neuron_id in list(self.translation_region)[:300]:
            neuron = self.neurons.get(neuron_id)
            if neuron:
                neuron.membrane_potential = -43.0
        
        # Analyze brain activity
        total_activation = sum(brain_activity.values()) if brain_activity else 0
        firing_count = len(firing_neurons)
        
        # Generate translation based on activity level
        if total_activation > 100:
            if firing_count > 50:
                translation = "I'm very active and processing a lot of information right now."
            else:
                translation = "I'm actively working on something complex."
        elif total_activation > 50:
            translation = "I'm thinking about what you said and processing it."
        else:
            translation = "I'm resting and quietly processing information."
        
        return translation
    
    def translate_english_to_brain(self, text: str) -> Dict[int, float]:
        """
        Translate English text to brain activation pattern
        
        Args:
            text: English text to translate
            
        Returns:
            Brain activation pattern
        """
        # Activate translation region
        activation = {}
        
        # Comprehend the text first
        comprehension = self.comprehend_input(text)
        
        # Map to brain regions
        words = text.lower().split()
        
        # Sensory-related words
        sensory_words = ["see", "look", "hear", "feel", "sense", "smell", "taste"]
        # Motor-related words
        motor_words = ["move", "go", "run", "fly", "walk", "type", "write"]
        # Cognitive words
        cognitive_words = ["think", "understand", "know", "learn", "remember", "plan"]
        
        for word in words:
            if word in sensory_words:
                activation["sensory"] = activation.get("sensory", 0) + 15.0
            elif word in motor_words:
                activation["motor"] = activation.get("motor", 0) + 15.0
            elif word in cognitive_words:
                activation["interneuron"] = activation.get("interneuron", 0) + 15.0
        
        # Default activation if no specific words found
        if not activation:
            activation["interneuron"] = 20.0
        
        return activation
    
    def get_conversation_context(self) -> List[Dict]:
        """Get recent conversation context"""
        return self.conversation_context.copy()
    
    def reset(self):
        """Reset Wernicke's Area state"""
        for neuron in self.neurons.values():
            neuron.reset()
        self.conversation_context.clear()
        self.output_queue.clear()
        self.input_buffer.clear()
        self.translation_buffer.clear()


class EnhancedHumanBrainIntegration:
    """
    Integrates the enhanced human-like brain regions with the existing fly brain
    """
    
    def __init__(self, prefrontal_neurons: int = 100000,
                 wernicke_neurons: int = 100000):
        """
        Initialize enhanced brain integration
        
        Args:
            prefrontal_neurons: Number of neurons in Prefrontal Cortex
            wernicke_neurons: Number of neurons in Wernicke's Area
        """
        self.prefrontal_cortex = PrefrontalCortex(prefrontal_neurons)
        self.wernicke_area = WernickeArea(wernicke_neurons)
        
        # Integration state
        self.integration_ratio = 0.0
        self.cross_region_connections = {}  # Connections between regions
        
        print(f"Enhanced Human Brain Integration initialized")
        print(f"  Prefrontal Cortex: {prefrontal_neurons:,} neurons")
        print(f"  Wernicke's Area: {wernicke_neurons:,} neurons")
        print(f"  Total enhanced neurons: {prefrontal_neurons + wernicke_neurons:,}")
    
    def integrate_with_connectome(self, brain_engine) -> Dict:
        """
        Integrate enhanced regions with the main connectome
        
        Args:
            brain_engine: Main brain engine instance
            
        Returns:
            Integration statistics
        """
        # Calculate integration ratio
        total_connectome_neurons = len(brain_engine.neuron_population.neurons)
        total_enhanced_neurons = (
            self.prefrontal_cortex.num_neurons +
            self.wernicke_area.num_neurons
        )
        
        self.integration_ratio = total_enhanced_neurons / total_connectome_neurons
        
        return {
            "connectome_neurons": total_connectome_neurons,
            "enhanced_neurons": total_enhanced_neurons,
            "integration_ratio": self.integration_ratio,
            "percentage": (self.integration_ratio * 100)
        }
    
    def process_coding_with_language(self, task: str, user_input: str) -> Dict:
        """
        Process a coding task with language comprehension
        
        Args:
            task: Coding task description
            user_input: User's input/instructions
            
        Returns:
            Processing result
        """
        # Comprehend user input
        comprehension = self.wernicke_area.comprehend_input(user_input)
        
        # Process coding task
        coding_result = self.prefrontal_cortex.process_coding_task(
            task,
            {"user_input": user_input, "comprehension": comprehension}
        )
        
        return {
            "comprehension": comprehension,
            "coding": coding_result,
            "integrated": True
        }
    
    def get_all_neurons(self) -> Dict[int, Neuron]:
        """Get all neurons from enhanced regions"""
        all_neurons = {}
        all_neurons.update(self.prefrontal_cortex.neurons)
        all_neurons.update(self.wernicke_area.neurons)
        return all_neurons
    
    def get_statistics(self) -> Dict:
        """Get statistics about enhanced regions"""
        return {
            "prefrontal_cortex": {
                "total_neurons": self.prefrontal_cortex.num_neurons,
                "working_memory_size": len(self.prefrontal_cortex.working_memory),
                "task_stack_depth": len(self.prefrontal_cortex.task_stack),
                "active_goals": len(self.prefrontal_cortex.active_goals)
            },
            "wernicke_area": {
                "total_neurons": self.wernicke_area.num_neurons,
                "conversation_context_length": len(self.wernicke_area.conversation_context),
                "vocabulary_size": len(self.wernicke_area.vocabulary)
            },
            "integration": {
                "ratio": self.integration_ratio,
                "cross_region_connections": len(self.cross_region_connections)
            }
        }
    
    def reset(self):
        """Reset all enhanced regions"""
        self.prefrontal_cortex.reset()
        self.wernicke_area.reset()


if __name__ == "__main__":
    # Test the enhanced human brain regions
    print("Testing Enhanced Human Brain Regions...")
    
    # Create regions
    prefrontal = PrefrontalCortex(num_neurons=1000)  # Smaller for testing
    wernicke = WernickeArea(num_neurons=1000)  # Smaller for testing
    
    # Test prefrontal cortex
    print("\nTesting Prefrontal Cortex...")
    prefrontal.activate_coding_mode("python")
    result = prefrontal.process_coding_task("Write a function", {"context": "test"})
    print(f"  Coding task result: {result}")
    
    # Test Wernicke's area
    print("\nTesting Wernicke's Area...")
    comprehension = wernicke.comprehend_input("Hello, how are you?")
    print(f"  Comprehension: {comprehension}")
    
    response = wernicke.produce_response({"sensory": 45.0, "motor": 30.0})
    print(f"  Response: {response}")
    
    translation = wernicke.translate_brain_to_english({"sensory": 50.0}, [1, 2, 3])
    print(f"  Translation: {translation}")
    
    # Test integration
    print("\nTesting Integration...")
    integration = EnhancedHumanBrainIntegration(prefrontal_neurons=1000, wernicke_neurons=1000)
    stats = integration.get_statistics()
    print(f"  Statistics: {stats}")
    
    print("\nEnhanced Human Brain Regions test completed!")
