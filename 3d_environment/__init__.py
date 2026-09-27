"""
3D Environment Module
Simulates the virtual world where the fly can navigate
"""

from .world import World3D
from .fly_character import FlyCharacter
from .sensory_system import SensorySystem
from .food_system import FoodSystem

__all__ = ['World3D', 'FlyCharacter', 'SensorySystem', 'FoodSystem']