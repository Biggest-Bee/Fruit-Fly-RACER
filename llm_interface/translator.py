"""
Brain Translator
Handles translation between human language and brain activation patterns using Gemini API
"""

import os
try:
    import google.generativeai as genai
except ImportError:
    print("Warning: google.generativeai is deprecated. Please install google.genai instead.")
    # For now, we'll continue with the deprecated version
    import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, List, Optional, Tuple
import json
import numpy as np

class BrainTranslator:
    """
    Translates between human language and brain activation patterns
    """
    
    def __init__(self):
        """Initialize the brain translator with Gemini API"""
        load_dotenv()
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError("Please set your GEMINI_API_KEY in the .env file")
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Initialize language cortex mapping
        self.language_to_brain_mapping = self._initialize_language_mapping()
        
        print("Brain Translator initialized with Gemini API")
    
    def _initialize_language_mapping(self) -> Dict[str, str]:
        """
        Initialize mapping between language concepts and brain regions
        This is a simplified mapping - would be expanded with actual connectome data
        """
        return {
            # Basic concepts
            "hello": "sensory",
            "food": "sensory", 
            "hungry": "interneuron",
            "fly": "motor",
            "move": "motor",
            "look": "sensory",
            "think": "interneuron",
            "code": "interneuron",
            "learn": "interneuron",
            "help": "interneuron",
            
            # Emotions and states
            "happy": "modulatory",
            "sad": "modulatory", 
            "scared": "modulatory",
            "tired": "modulatory",
            "excited": "modulatory",
            
            # Actions
            "go": "motor",
            "stop": "motor",
            "eat": "motor",
            "write": "motor",
            "read": "sensory",
        }
    
    def text_to_brain_activation(self, text: str) -> Dict[int, float]:
        """
        Convert human text to brain activation patterns
        
        Args:
            text: Human language input
            
        Returns:
            Dictionary mapping neuron IDs to activation currents
        """
        # Use Gemini to understand the text and extract key concepts
        prompt = f"""
        Analyze this text and extract the key concepts and actions: "{text}"
        
        Return a JSON object with:
        - "concepts": list of key concepts (simple words)
        - "actions": list of actions (verbs)
        - "emotions": list of emotional states
        - "intensity": overall intensity (0.0 to 1.0)
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Parse the response (simplified - would need more robust parsing)
            try:
                # Try to extract JSON from response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    analysis = json.loads(json_str)
                else:
                    # Fallback if JSON parsing fails
                    analysis = self._fallback_analysis(text)
            except:
                analysis = self._fallback_analysis(text)
            
            # Convert concepts to brain activation
            activation_patterns = self._concepts_to_activation(analysis)
            
            return activation_patterns
            
        except Exception as e:
            print(f"Error in text_to_brain_activation: {e}")
            return self._fallback_activation(text)
    
    def _fallback_analysis(self, text: str) -> dict:
        """Fallback analysis if Gemini fails"""
        words = text.lower().split()
        return {
            "concepts": [w for w in words if w in self.language_to_brain_mapping],
            "actions": [],
            "emotions": [],
            "intensity": 0.5
        }
    
    def _concepts_to_activation(self, analysis: dict) -> Dict[int, float]:
        """
        Convert concepts and analysis to specific neuron activation patterns
        This is a simplified version - would use actual neuron IDs from connectome
        """
        activation = {}
        intensity = analysis.get("intensity", 0.5)
        
        # Map concepts to neuron types (simplified)
        concept_weights = {
            "sensory": 30.0,
            "motor": 25.0, 
            "interneuron": 20.0,
            "modulatory": 15.0
        }
        
        # Combine all concepts
        all_concepts = (analysis.get("concepts", []) + 
                       analysis.get("actions", []) + 
                       analysis.get("emotions", []))
        
        for concept in all_concepts:
            concept_lower = concept.lower()
            if concept_lower in self.language_to_brain_mapping:
                neuron_type = self.language_to_brain_mapping[concept_lower]
                base_activation = concept_weights.get(neuron_type, 10.0)
                
                # Create activation for neurons of this type
                # In real implementation, would use specific neuron IDs
                activation[neuron_type] = activation.get(neuron_type, 0.0) + base_activation * intensity
        
        return activation
    
    def _fallback_activation(self, text: str) -> Dict[int, float]:
        """Fallback activation if all else fails"""
        words = text.lower().split()
        activation = {}
        
        for word in words:
            if word in self.language_to_brain_mapping:
                neuron_type = self.language_to_brain_mapping[word]
                activation[neuron_type] = activation.get(neuron_type, 0.0) + 15.0
        
        return activation
    
    def brain_activity_to_text(self, brain_activity: Dict[int, float], 
                               firing_neurons: List[int]) -> str:
        """
        Convert brain activity back to human language
        
        Args:
            brain_activity: Dictionary of neuron activations
            firing_neurons: List of neurons that recently fired
            
        Returns:
            Human language response
        """
        # Analyze the brain activity patterns
        activity_summary = self._analyze_brain_activity(brain_activity, firing_neurons)
        
        # Use Gemini to generate natural language response
        prompt = f"""
        Based on this brain activity analysis, generate a natural language response:
        
        Activity Summary:
        - Active regions: {activity_summary['active_regions']}
        - Firing patterns: {activity_summary['firing_patterns']}
        - Overall activity level: {activity_summary['activity_level']}
        - Dominant states: {activity_summary['dominant_states']}
        
        Generate a simple, conversational response as if you are a fruit fly brain.
        Keep it brief and natural.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error in brain_activity_to_text: {e}")
            return self._fallback_response(activity_summary)
    
    def _analyze_brain_activity(self, brain_activity: Dict[int, float], 
                                firing_neurons: List[int]) -> dict:
        """Analyze brain activity patterns"""
        # Calculate activity statistics
        total_activation = sum(brain_activity.values()) if brain_activity else 0
        firing_count = len(firing_neurons)
        
        # Determine active regions
        active_regions = list(brain_activity.keys()) if brain_activity else []
        
        # Determine activity level
        if total_activation > 100:
            activity_level = "high"
        elif total_activation > 50:
            activity_level = "moderate"
        else:
            activity_level = "low"
        
        # Determine dominant states based on firing patterns
        if firing_count > 10:
            dominant_states = ["active", "processing"]
        elif firing_count > 5:
            dominant_states = ["moderately active"]
        else:
            dominant_states = ["calm", "resting"]
        
        return {
            "active_regions": active_regions,
            "firing_patterns": f"{firing_count} neurons fired",
            "activity_level": activity_level,
            "dominant_states": dominant_states,
            "total_activation": total_activation
        }
    
    def _fallback_response(self, activity_summary: dict) -> str:
        """Fallback response if Gemini fails"""
        activity_level = activity_summary["activity_level"]
        firing_count = int(activity_summary["firing_patterns"].split()[0])
        
        if activity_level == "high":
            return "I'm very active right now, processing lots of information!"
        elif activity_level == "moderate":
            return "I'm thinking about what you said."
        else:
            return "I'm resting and processing quietly."
    
    def test_connection(self) -> bool:
        """Test the connection to Gemini API"""
        try:
            response = self.model.generate_content("Hello, this is a test.")
            print(f"[OK] Gemini API connection successful!")
            print(f"   Test response: {response.text[:50]}...")
            return True
        except Exception as e:
            print(f"[ERROR] Error connecting to Gemini API: {e}")
            return False


if __name__ == "__main__":
    # Test the brain translator
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    print("Testing Brain Translator...")
    
    try:
        translator = BrainTranslator()
        
        # Test API connection
        translator.test_connection()
        
        # Test text to brain activation
        print("\nTesting text to brain activation...")
        test_text = "I am hungry and want to find food"
        activation = translator.text_to_brain_activation(test_text)
        print(f"Input: '{test_text}'")
        print(f"Brain activation: {activation}")
        
        # Test brain activity to text
        print("\nTesting brain activity to text...")
        test_activity = {"sensory": 45.0, "motor": 30.0}
        test_firing = [1, 2, 3, 4, 5]
        response = translator.brain_activity_to_text(test_activity, test_firing)
        print(f"Brain activity: {test_activity}")
        print(f"Firing neurons: {test_firing}")
        print(f"Response: {response}")
        
        print("\nBrain Translator test completed!")
        
    except Exception as e:
        print(f"Error during Brain Translator test: {e}")
        print("Make sure to set your GEMINI_API_KEY in the .env file")