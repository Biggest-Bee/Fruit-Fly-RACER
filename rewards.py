"""
Rewards Module - Reward and Penalty System
Calculates rewards based on progress and penalties for collisions.
"""

import numpy as np
from typing import Dict


class RewardSystem:
    """
    Reward and penalty system for the racing simulation
    """
    
    def __init__(self):
        """
        Initialize reward system
        """
        self.total_points = 0.0
        self.max_points = 1000.0
        self.penalty_per_collision = -50.0
        self.progress_reward_multiplier = 100.0
        
        self.collision_count = 0
        self.best_progress = 0.0
        
        print("Reward System initialized")
    
    def calculate_progress_reward(self, progress: float) -> float:
        """
        Calculate reward based on progress to finish line
        
        Args:
            progress: Progress value (0 to 1)
            
        Returns:
            Reward value
        """
        # Dense distance-based progression shaping
        reward = progress * self.progress_reward_multiplier
        
        # Bonus for exceeding best progress
        if progress > self.best_progress:
            bonus = (progress - self.best_progress) * 20.0
            reward += bonus
            self.best_progress = progress
        
        return reward
    
    def calculate_collision_penalty(self) -> float:
        """
        Calculate penalty for collision
        
        Returns:
            Penalty value
        """
        self.collision_count += 1
        return self.penalty_per_collision
    
    def update_total_points(self, reward: float = 0.0, penalty: float = 0.0):
        """
        Update total points with reward and penalty
        
        Args:
            reward: Reward to add
            penalty: Penalty to subtract
        """
        self.total_points += reward + penalty
        self.total_points = np.clip(self.total_points, 0.0, self.max_points)
    
    def get_current_score(self) -> Dict:
        """
        Get current score statistics
        
        Returns:
            Dictionary with score information
        """
        return {
            'total_points': self.total_points,
            'collision_count': self.collision_count,
            'best_progress': self.best_progress,
            'score_percentage': self.total_points / self.max_points * 100
        }
    
    def reset(self):
        """Reset reward system for new simulation"""
        self.total_points = 0.0
        self.collision_count = 0
        self.best_progress = 0.0
        # Only print on first reset
        if not hasattr(self, '_reset_count'):
            self._reset_count = 0
        self._reset_count += 1
        if self._reset_count == 1:
            print("Reward system reset")


if __name__ == "__main__":
    reward_system = RewardSystem()
    print("Rewards module loaded")
