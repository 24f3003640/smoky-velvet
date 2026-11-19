"""
Abstract interface for platform-specific physical keystroke listeners.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Optional

# Key Callback signature: (led_index: int, timestamp: float) -> None
KeyCallback = Callable[[int, float], None]

# Knob/Volume Callback signature: (action: str, timestamp: float) -> None
# action can be: "volume_up", "volume_down", "mute_click", "knob_long_press", "knob_double_click"
KnobCallback = Callable[[str, float], None]

class InputListener(ABC):
    def __init__(self):
        self._callback: Optional[KeyCallback] = None
        self._knob_callback: Optional[KnobCallback] = None

    def set_callback(self, callback: KeyCallback) -> None:
        self._callback = callback

    def set_knob_callback(self, callback: KnobCallback) -> None:
        self._knob_callback = callback

    @abstractmethod
    def start(self) -> None:
        """Start listening for physical keypresses."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop listening and release handles."""
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Check if listener is actively reading events."""
        pass
