"""
Dictate - Push-to-Talk Voice Dictation for macOS

A local, privacy-first voice dictation app using Apple Silicon MLX models.
"""

__version__ = "1.0.0"
__author__ = "Piotr Rasala"

from dictate.app import DictationApp
from dictate.config import Config

__all__ = ["DictationApp", "Config", "__version__"]
