"""
Reward System
Manages food-based rewards for coding training performance
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from .hunger_mechanics import HungerMechanics
    from .behavior_priorities import BehaviorPriorities
except ImportError:
    from training_system.hunger_mechanics import HungerMechanics
    from training_system.behavior_priorities import BehaviorPriorities

class RewardSystem:
    """
    Reward system that provides food motivation for coding training
    """
    
    def __init__(self, hunger_system: HungerMechanics = None):
        """
        Initialize the reward system
        
        Args:
            hunger_system: Optional hunger mechanics instance
        """
        self.hunger_system = hunger_system or HungerMechanics()
        self.behavior_priorities = BehaviorPriorities()
        
        # Reward configuration
        self.base_food_reward = 25.0  # Base energy gain for correct answer
        self.quality_multiplier = 1.5  # Multiplier for high-quality answers
        self.language_bonus = {}  # Language-specific bonuses
        self.streak_bonus = 0.0  # Current streak bonus
        
        # Training mode settings
        self.training_mode = False
        self.training_reward_only = True  # Only feed during training if correct
        
        # Performance tracking
        self.performance_history = []
        self.correct_streak = 0
        self.total_correct = 0
        self.total_attempts = 0
        
        print("Reward system initialized with food motivation")
    
    def calculate_reward(self, evaluation: Dict, language: str) -> Dict:
        """
        Calculate food reward based on code evaluation
        
        Args:
            evaluation: Code evaluation results
            language: Programming language
            
        Returns:
            Reward details
        """
        if not evaluation.get("correct", False):
            # No reward for incorrect answers during training
            self.correct_streak = 0
            self.total_attempts += 1
            
            return {
                "reward": 0.0,
                "fed": False,
                "reason": "Incorrect answer - no food reward",
                "quality": evaluation.get("quality", 0.0),
                "streak": 0
            }
        
        # Calculate base reward
        quality = evaluation.get("quality", 0.0)
        base_reward = self.base_food_reward * quality
        
        # Apply quality multiplier for high-quality answers
        if quality >= 0.8:
            base_reward *= self.quality_multiplier
        
        # Apply language bonus
        language_bonus = self.language_bonus.get(language, 0.0)
        base_reward += language_bonus
        
        # Apply streak bonus
        self.correct_streak += 1
        streak_bonus = min(10.0, self.correct_streak * 2.0)
        base_reward += streak_bonus
        
        # Cap maximum reward
        max_reward = 50.0
        final_reward = min(max_reward, base_reward)
        
        # Update tracking
        self.total_correct += 1
        self.total_attempts += 1
        
        reward_details = {
            "reward": final_reward,
            "fed": True,
            "reason": "Correct answer - food reward granted",
            "quality": quality,
            "streak": self.correct_streak,
            "language_bonus": language_bonus,
            "streak_bonus": streak_bonus
        }
        
        self.performance_history.append(reward_details)
        
        return reward_details
    
    def grant_reward(self, reward: Dict) -> bool:
        """
        Grant the food reward to the fly
        
        Args:
            reward: Reward details from calculate_reward
            
        Returns:
            Whether reward was successfully granted
        """
        if not reward.get("fed", False):
            return False
        
        energy_gain = reward["reward"]
        
        # Update hunger system to ensure drives are calculated
        self.hunger_system.update_hunger(0.0, 0.0)
        
        # Apply energy gain through hunger system
        self.hunger_system.consume_food(energy_gain)
        current_energy = self.hunger_system.energy
        
        print(f"Reward granted: +{energy_gain:.1f} energy (Current: {current_energy:.1f})")
        
        return True
    
    def get_training_mode_status(self) -> Dict:
        """
        Get current training mode status
        
        Returns:
            Training mode status information
        """
        if not self.training_mode:
            return {
                "training_mode": False,
                "can_eat": True,
                "reason": "Not in training mode - free feeding available"
            }
        
        return {
            "training_mode": True,
            "can_eat": self.training_reward_only,
            "reason": "Training mode - food only when correct" if self.training_reward_only else "Training mode - free feeding"
        }
    
    def set_training_mode(self, enabled: bool, reward_only: bool = True):
        """
        Set training mode
        
        Args:
            enabled: Whether training mode is active
            reward_only: Whether food is only granted for correct answers
        """
        self.training_mode = enabled
        self.training_reward_only = reward_only
        
        if enabled:
            print(f"Training mode enabled (reward only: {reward_only})")
        else:
            print("Training mode disabled - free feeding available")
    
    def get_performance_stats(self) -> Dict:
        """
        Get performance statistics
        
        Returns:
            Performance statistics
        """
        if self.total_attempts == 0:
            return {
                "total_attempts": 0,
                "total_correct": 0,
                "success_rate": 0.0,
                "current_streak": 0,
                "best_streak": 0,
                "average_reward": 0.0
            }
        
        success_rate = self.total_correct / self.total_attempts
        best_streak = max(0, max([r.get("streak", 0) for r in self.performance_history]))
        average_reward = sum([r.get("reward", 0.0) for r in self.performance_history]) / len(self.performance_history) if self.performance_history else 0.0
        
        return {
            "total_attempts": self.total_attempts,
            "total_correct": self.total_correct,
            "success_rate": success_rate,
            "current_streak": self.correct_streak,
            "best_streak": best_streak,
            "average_reward": average_reward,
            "total_energy_gained": sum([r.get("reward", 0.0) for r in self.performance_history])
        }
    
    def set_language_bonus(self, language: str, bonus: float):
        """
        Set a language-specific bonus
        
        Args:
            language: Programming language
            bonus: Bonus amount to add to rewards
        """
        self.language_bonus[language] = bonus
        print(f"Language bonus set: {language} +{bonus:.1f}")
    
    def check_hunger_can_train(self) -> Dict:
        """
        Check if the fly is hungry enough to train
        
        Returns:
            Whether the fly can train based on hunger
        """
        energy = self.hunger_system.energy
        hunger_drive = self.hunger_system.hunger_drive
        
        # Fly should be somewhat hungry to be motivated for training
        # But not starving (too hungry to focus)
        can_train = energy > 20.0 and energy < 80.0
        
        return {
            "can_train": can_train,
            "energy": energy,
            "hunger_drive": hunger_drive,
            "reason": "Optimal hunger for training" if can_train else 
                     "Too hungry to focus" if energy <= 20.0 else "Not hungry enough for motivation"
        }
    
    def reset_performance(self):
        """Reset performance tracking"""
        self.performance_history = []
        self.correct_streak = 0
        self.total_correct = 0
        self.total_attempts = 0
        print("Performance tracking reset")
    
    def get_hunger_status(self) -> Dict:
        """
        Get current hunger status
        
        Returns:
            Hunger status information
        """
        return {
            "energy": self.hunger_system.energy,
            "hunger_drive": self.hunger_system.hunger_drive,
            "survival_drive": self.hunger_system.survival_drive,
            "is_starving": self.hunger_system.is_starving,
            "is_critical": self.hunger_system.is_critical,
            "death_imminent": self.hunger_system.death_imminent
        }


if __name__ == "__main__":
    # Test the reward system
    print("Testing Reward System...")
    
    try:
        from hunger_mechanics import HungerMechanics
        from behavior_priorities import BehaviorPriorities
    except ImportError:
        from training_system.hunger_mechanics import HungerMechanics
        from training_system.behavior_priorities import BehaviorPriorities
    
    reward_system = RewardSystem()
    
    # Test reward calculation for correct answer
    print("\nTesting reward calculation for correct answer...")
    evaluation_correct = {
        "correct": True,
        "quality": 0.9,
        "feedback": "Excellent code"
    }
    reward = reward_system.calculate_reward(evaluation_correct, "python")
    print(f"Reward for correct answer: {reward}")
    
    # Test reward calculation for incorrect answer
    print("\nTesting reward calculation for incorrect answer...")
    evaluation_incorrect = {
        "correct": False,
        "quality": 0.0,
        "feedback": "Syntax error"
    }
    reward = reward_system.calculate_reward(evaluation_incorrect, "python")
    print(f"Reward for incorrect answer: {reward}")
    
    # Test reward granting
    print("\nTesting reward granting...")
    reward_system.grant_reward({
        "reward": 25.0,
        "fed": True,
        "quality": 0.9,
        "streak": 1
    })
    
    # Test performance stats
    print("\nTesting performance stats...")
    stats = reward_system.get_performance_stats()
    print(f"Performance stats: {stats}")
    
    # Test hunger status
    print("\nTesting hunger status...")
    hunger_status = reward_system.get_hunger_status()
    print(f"Hunger status: {hunger_status}")
    
    # Test training mode
    print("\nTesting training mode...")
    reward_system.set_training_mode(True, True)
    training_status = reward_system.get_training_mode_status()
    print(f"Training mode status: {training_status}")
    
    print("Reward system test completed!")