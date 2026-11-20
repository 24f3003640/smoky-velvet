"""
Audio Beat Pulse & Orchestral Swell Effect for URX Core75.
Combines:
1. Dynamic Audio Swell: Follows orchestral crescendos, piano phrasing, and volume dynamics.
2. Melodic Note Striking: Radiates solar white ripples on piano keys, violin accents, or beat onsets.
3. Spacebar Music Heartbeat: Spacebar breathes continuously in sync with the audio loudness envelope.
Calibrated for URX Smoky Black casing (0% green contamination).
"""
from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple
from core.color import Color
from core.layout import KeyboardLayout
from effects.base import Effect

# High-luminance colors for dark smoky casing:
# Melodic Note Ripple: Brilliant Solar White (100% luminance, cuts through dark smoke)
COLOR_MELODIC_NOTE = Color(255, 255, 255)
# Dynamic Swell Color: Luminous Electric Cyan / Azure (0% green)
COLOR_SWELL        = Color(0, 220, 255)
# Spacebar Heartbeat Accent: Radiant Diamond Ice
COLOR_HEARTBEAT    = Color(220, 245, 255)

class AudioPulseEffect(Effect):
    def __init__(self, origin_led: int = 75, pulse_duration: float = 0.60):
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
        self._smooth_energy = max(0.0, min(1.0, energy))

    def trigger_beat(self, energy: float = 1.0, timestamp: Optional[float] = None) -> None:
        """Called on melodic note onsets, staccato strikes, or percussive beats."""
        if not self.enabled:
            return
        t = timestamp if timestamp is not None else time.monotonic()
        self._last_beat_time = t
        self._beat_energy = max(0.35, min(1.0, energy))

    def update(self, dt: float, current_time: float) -> None:
        pass

    def is_finished(self) -> bool:
        return False

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Tuple[Color, float]]]) -> None:
        if not self.enabled:
            return

        now = time.monotonic()

        # 1. Orchestral / Piano Volume Swell (Full Matrix Dynamics)
        # Breathes with crescendo dynamics across all keys
        if self._smooth_energy > 0.05:
            swell_intensity = self._smooth_energy * 0.60  # Up to 60% vivid overlay
            for i in range(layout.led_count):
                existing = buffer[i]
                if existing is not None:
                    ex_col, ex_a = existing
                    buffer[i] = (COLOR_SWELL.blend_alpha(ex_col, ex_a), min(1.0, swell_intensity + ex_a))
                else:
                    buffer[i] = (COLOR_SWELL, swell_intensity)

        # 2. Spacebar Real-Time Audio Heartbeat Indicator (LED 75)
        # Always illuminates proportionally to current musical loudness
        if self._smooth_energy > 0.02 and self.origin_led < layout.led_count:
            heart_intensity = min(1.0, self._smooth_energy * 0.95 + 0.15)
            existing = buffer[self.origin_led]
            if existing is not None:
                ex_col, ex_a = existing
                buffer[self.origin_led] = (COLOR_HEARTBEAT.blend_alpha(ex_col, ex_a), max(ex_a, heart_intensity))
            else:
                buffer[self.origin_led] = (COLOR_HEARTBEAT, heart_intensity)

        # 3. Melodic Note Strike / Beat Transient Ripple (Expanding wave from Spacebar)
        if self._last_beat_time > 0.0:
            elapsed = now - self._last_beat_time
            if elapsed < self.pulse_duration:
                p = elapsed / self.pulse_duration
                radius = p * 6.5  # Expands outward ~6.5 keys from Spacebar
                envelope = math.cos(0.5 * math.pi * p) ** 2.0 * self._beat_energy

                for i in range(layout.led_count):
                    dist = layout.distance(self.origin_led, i)
                    diff = abs(dist - radius)
                    if diff < 1.6:
                        intensity = max(0.0, (1.0 - (diff / 1.6)) * envelope * 0.85)
                        if intensity > 0.02:
                            existing = buffer[i]
                            if existing is not None:
                                ex_col, ex_a = existing
                                buffer[i] = (COLOR_MELODIC_NOTE.blend_alpha(ex_col, ex_a), min(1.0, intensity + ex_a))
                            else:
                                buffer[i] = (COLOR_MELODIC_NOTE, intensity)
