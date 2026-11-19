"""
Abstract base class for all lighting effects.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional
from core.color import Color
from core.layout import KeyboardLayout

class Effect(ABC):
    @abstractmethod
    def update(self, dt: float, current_time: float) -> None:
        """Update effect state by time step dt."""
        pass

    @abstractmethod
    def render(self, layout: KeyboardLayout, buffer: List[Optional[Color]]) -> None:
        """
        Render effect onto the given buffer (size = layout.led_count).
        buffer entries are None if untouched by this effect, or Color.
        """
        pass

    @abstractmethod
    def is_finished(self) -> bool:
        """Return True if the effect is complete and can be garbage collected."""
        pass
