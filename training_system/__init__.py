"""
Training System Module
Handles survival behaviors, hunger mechanics, and training systems
"""

from .survival_system import SurvivalSystem
from .hunger_mechanics import HungerMechanics
from .behavior_priorities import BehaviorPriorities

__all__ = ['SurvivalSystem', 'HungerMechanics', 'BehaviorPriorities']