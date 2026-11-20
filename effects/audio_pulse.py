"""
Audio Beat Pulse & Orchestral Swell Effect for URX Core75.
Combines:
1. Continuous dynamic breathing: Follows orchestral crescendos and piano volume swells.
2. Melodic staccato note ripples: Radiates soft watercolor pulses on piano/instrument strikes.
Calibrated for URX Smoky Black casing (0% green contamination).
"""
from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple
from core.color import Color
from core.layout import KeyboardLayout
from effects.base import Effect

# Colors:
# Dynamic Swell: Electric Sapphire / Azure
COLOR_SWELL_AZURE  = Color(0, 185, 255)
# Melodic Note Ripple: Diamond White / Ice Cyan
COLOR_MELODIC_NOTE = Color(200, 245, 255)

class AudioPulseEffect(Effect):
    def __init__(self, origin_led: int = 75, pulse_duration: float = 0.50):
        self.origin_led = origin_led
        self.pulse_duration = pulse_duration
        self.enabled = False
        self._last_beat_time: float = 0.0
        self._beat_energy: float = 0.0
        self._smooth_energy: float = 0.0

    def set_energy(self, energy: float) -> None:
        """Called continuously by audio monitor with normalized loudness envelope [0.0, 1.0]."""
        if not self.enabled:
            self._smooth_energy = 0.0
            return
        # Smooth interpolation to eliminate flicker
        self._smooth_energy = max(0.0, min(1.0, energy))

    def trigger_beat(self, energy: float = 1.0, timestamp: Optional[float] = None) -> None:
        """Called on melodic note onsets, staccato strikes, or percussive beats."""
        if not self.enabled:
            return
        t = timestamp if timestamp is not None else time.monotonic()
        self._last_beat_time = t
        self._beat_energy = max(0.25, min(1.0, energy))

    def update(self, dt: float, current_time: float) -> None:
        pass

    def is_finished(self) -> bool:
        return False

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Tuple[Color, float]]]) -> None:
        if not self.enabled:
            return

        now = time.monotonic()

        # 1. Orchestral / Piano Volume Swell (Full Matrix Breathing)
        # Gently modulates underglow intensity with crescendo dynamics
        if self._smooth_energy > 0.04:
            swell_intensity = self._smooth_energy * 0.35  # Up to 35% ambient swell
            for i in range(layout.led_count):
                existing = buffer[i]
                if existing is not None:
                    ex_col, ex_a = existing
                    buffer[i] = (COLOR_SWELL_AZURE.blend_alpha(ex_col, ex_a), min(1.0, swell_intensity + ex_a))
                else:
                    buffer[i] = (COLOR_SWELL_AZURE, swell_intensity)

        # 2. Melodic Note Strike / Beat Transient Ripple
        if self._last_beat_time > 0.0:
            elapsed = now - self._last_beat_time
            if elapsed < self.pulse_duration:
                p = elapsed / self.pulse_duration
                radius = p * 6.5  # Expands outward across ~6.5 keys from Spacebar
                envelope = math.cos(0.5 * math.pi * p) ** 2.0 * self._beat_energy

                for i in range(layout.led_count):
                    dist = layout.distance(self.origin_led, i)
                    diff = abs(dist - radius)
                    if diff < 1.5:
                        intensity = max(0.0, (1.0 - (diff / 1.5)) * envelope * 0.75)
                        if intensity > 0.02:
                            existing = buffer[i]
                            if existing is not None:
                                ex_col, ex_a = existing
                                buffer[i] = (COLOR_MELODIC_NOTE.blend_alpha(ex_col, ex_a), min(1.0, intensity + ex_a))
                            else:
                                buffer[i] = (COLOR_MELODIC_NOTE, intensity)
