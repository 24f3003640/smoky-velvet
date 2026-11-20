"""
Audio Beat Pulse & Visualizer Effect for URX Core75.
Renders rhythmic expanding bass pulses radiating from the Spacebar outward across the matrix.
"""
from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple
from core.color import Color
from core.layout import KeyboardLayout
from effects.base import Effect

# Pulse color: Deep Electric Cyan & Royal Sapphire
PULSE_COLOR = Color(0, 240, 255)

class AudioPulseEffect(Effect):
    def __init__(self, origin_led: int = 75, pulse_duration: float = 0.45):
        self.origin_led = origin_led
        self.pulse_duration = pulse_duration
        self.enabled = False
        self._last_beat_time: float = 0.0
        self._energy: float = 0.0

    def trigger_beat(self, energy: float = 1.0, timestamp: Optional[float] = None) -> None:
        if not self.enabled:
            return
        t = timestamp if timestamp is not None else time.monotonic()
        self._last_beat_time = t
        self._energy = max(0.2, min(1.0, energy))

    def update(self, dt: float, current_time: float) -> None:
        pass

    def is_finished(self) -> bool:
        return False

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Tuple[Color, float]]]) -> None:
        if not self.enabled or self._last_beat_time == 0.0:
            return

        now = time.monotonic()
        elapsed = now - self._last_beat_time
        if elapsed >= self.pulse_duration:
            return

        # Progress [0.0, 1.0]
        p = elapsed / self.pulse_duration
        radius = p * 6.0  # Expands outward ~6 keys from Spacebar
        envelope = math.cos(0.5 * math.pi * p) ** 2.0 * self._energy

        for i in range(layout.led_count):
            dist = layout.distance(self.origin_led, i)
            diff = abs(dist - radius)
            if diff < 1.4:
                intensity = max(0.0, (1.0 - (diff / 1.4)) * envelope * 0.70)
                if intensity > 0.02:
                    existing = buffer[i]
                    if existing is not None:
                        ex_col, ex_a = existing
                        buffer[i] = (PULSE_COLOR.blend_alpha(ex_col, ex_a), min(1.0, intensity + ex_a))
                    else:
                        buffer[i] = (PULSE_COLOR, intensity)
