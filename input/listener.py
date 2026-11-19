"""
Abstract interface for platform-specific physical keystroke listeners.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, Optional

# Callback signature: (led_index: int, timestamp: float) -> None
KeyCallback = Callable[[int, float], None]

class InputListener(ABC):
    def __init__(self):
        self._callback: Optional[KeyCallback] = None

    def set_callback(self, callback: KeyCallback) -> None:
        self._callback = callback

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
