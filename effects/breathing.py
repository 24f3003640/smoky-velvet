"""
Ambient Lockscreen & Idle Breathing Effect for URX Core75.
Renders an ultra-slow, hypnotic 4.5-second breathing wave when Hyprland locks or goes idle.
"""
from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple
from core.color import Color
from core.layout import KeyboardLayout
from effects.base import Effect

# Deep Velvet Ember Breathing Color (0% Green, safe for smoky case)
BREATHING_COLOR = Color(214, 0, 41)

class AmbientBreathingEffect(Effect):
    def __init__(self, period: float = 4.5):
        self.period = period
        self.enabled = False
        self._phase = 0.0

    def update(self, dt: float, current_time: float) -> None:
        if not self.enabled:
            return
        self._phase = (current_time % self.period) / self.period

    def is_finished(self) -> bool:
        return False

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Tuple[Color, float]]]) -> None:
        if not self.enabled:
            return

        # Smooth organic bell-shaped breathing curve [0.08 to 0.40]
        # In lock mode, keyboard operates at very low ambient intensity
        sine = math.sin(self._phase * 2.0 * math.pi)
        intensity = 0.08 + 0.32 * (0.5 + 0.5 * sine)

        for i in range(layout.led_count):
            buffer[i] = (BREATHING_COLOR, intensity)
