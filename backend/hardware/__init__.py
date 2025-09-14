"""
Hardware control modules for radio functionality.

This package contains hardware abstraction layers:
- AudioPlayer: MPV-based audio streaming and playback control
- GPIOController: Physical button and rotary encoder control

All hardware components support mock mode for development on non-Pi systems.
"""

from .audio_player import AudioPlayer
from .gpio_controller import GPIOController

__all__ = [
    "AudioPlayer",
    "GPIOController"
]
