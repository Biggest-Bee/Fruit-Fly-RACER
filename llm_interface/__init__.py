"""
LLM Interface Module
Handles translation between human language and brain activation patterns
"""

from .translator import BrainTranslator
from .language_cortex import LanguageCortex

__all__ = ['BrainTranslator', 'LanguageCortex']