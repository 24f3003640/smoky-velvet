"""
Live Typing Speedometer & WPM Gauge Effect for URX Core75.
Tracks physical typing cadence in real-time and renders a dynamic velocity meter across the Number Row (keys 1-0).
PRIVACY GUARANTEE: Operates purely on timestamps. Zero keystroke identity or text content logged.
"""
from __future__ import annotations
import math
import time
from collections import deque
from typing import Deque, List, Optional, Tuple
from core.color import Color
from core.layout import KeyboardLayout
from effects.base import Effect

# Number Row LED Indices: '1' through '0' (10 keys total)
# 15: "1", 16: "2", 17: "3", 18: "4", 19: "5", 20: "6", 21: "7", 22: "8", 23: "9", 24: "0"
NUMBER_ROW_LEDS = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

# Color velocity thresholds:
# 20-40 WPM: Warm Molten Gold
# 50-70 WPM: Electric Neon Violet
# 80-100 WPM: Deep Stealth Crimson
# 100+ WPM: Hyperdrive Solar White Overdrive
COLOR_MOLTEN_GOLD   = Color(255, 160, 20)
COLOR_NEON_VIOLET   = Color(160, 0, 255)
COLOR_STEALTH_BLOOD = Color(214, 0, 41)
COLOR_SOLAR_WHITE   = Color(255, 255, 255)

class WpmGaugeEffect(Effect):
    def __init__(self, window_seconds: float = 4.0, max_scale_wpm: float = 100.0):
        self.window_seconds = window_seconds
        self.max_scale_wpm = max_scale_wpm
        self.enabled = True

        self._keystroke_timestamps: Deque[float] = deque()
        self._current_wpm: float = 0.0
        self._last_typing_time: float = 0.0
        self._display_opacity: float = 0.0
        self._peak_wpm: float = 0.0

    @property
    def current_wpm(self) -> float:
        return self._current_wpm

    @property
    def peak_wpm(self) -> float:
        return self._peak_wpm

    def register_keystroke(self, timestamp: Optional[float] = None) -> None:
        """Called on physical keydown event."""
        t = timestamp if timestamp is not None else time.monotonic()
        self._keystroke_timestamps.append(t)
        self._last_typing_time = t

    def update(self, dt: float, current_time: float) -> None:
        if not self.enabled:
            self._display_opacity = max(0.0, self._display_opacity - dt * 2.5)
            return

        # Purge timestamps outside the rolling window
        cutoff = current_time - self.window_seconds
        while self._keystroke_timestamps and self._keystroke_timestamps[0] < cutoff:
            self._keystroke_timestamps.popleft()

        # Calculate instantaneous raw WPM: (keystrokes / 5) * (60 / window_seconds)
        # Standard typographical metric: 5 keystrokes = 1 word
        count = len(self._keystroke_timestamps)
        raw_wpm = (count / 5.0) * (60.0 / self.window_seconds)

        # Smooth EMA filtering
        alpha = min(1.0, dt * 5.0)
        self._current_wpm = (1.0 - alpha) * self._current_wpm + alpha * raw_wpm
        if self._current_wpm > self._peak_wpm:
            self._peak_wpm = self._current_wpm

        # Fade in when actively typing, smoothly fade out 1.2s after typing pauses
        time_since_typing = current_time - self._last_typing_time
        if time_since_typing < 1.2 and self._current_wpm > 8.0:
            self._display_opacity = min(1.0, self._display_opacity + dt * 4.0)
        else:
            self._display_opacity = max(0.0, self._display_opacity - dt * 1.5)

    def is_finished(self) -> bool:
        return False

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Tuple[Color, float]]]) -> None:
        if not self.enabled or self._display_opacity <= 0.01:
            return

        # Fraction of meter filled [0.0, 1.0]
        fraction = max(0.0, min(1.0, self._current_wpm / self.max_scale_wpm))
        total_keys = len(NUMBER_ROW_LEDS)
        active_keys_float = fraction * total_keys

        # Determine velocity color based on current speed
        if self._current_wpm < 45.0:
            p = max(0.0, min(1.0, self._current_wpm / 45.0))
            color = COLOR_MOLTEN_GOLD.lerp(COLOR_NEON_VIOLET, p)
        elif self._current_wpm < 85.0:
            p = max(0.0, min(1.0, (self._current_wpm - 45.0) / 40.0))
            color = COLOR_NEON_VIOLET.lerp(COLOR_STEALTH_BLOOD, p)
        else:
            p = max(0.0, min(1.0, (self._current_wpm - 85.0) / 25.0))
            color = COLOR_STEALTH_BLOOD.lerp(COLOR_SOLAR_WHITE, p)

        for i, led_idx in enumerate(NUMBER_ROW_LEDS):
            if led_idx >= layout.led_count:
                continue

            if i < int(active_keys_float):
                # Fully lit key
                key_opacity = 0.95 * self._display_opacity
            elif i == int(active_keys_float):
                # Partial leading edge key
                partial = active_keys_float - int(active_keys_float)
                key_opacity = max(0.0, partial * 0.95 * self._display_opacity)
            else:
                key_opacity = 0.0

            if key_opacity > 0.01:
                existing = buffer[led_idx]
                if existing is not None:
                    ex_color, ex_alpha = existing
                    buffer[led_idx] = (color.blend_alpha(ex_color, ex_alpha), min(1.0, key_opacity + ex_alpha))
                else:
                    buffer[led_idx] = (color, key_opacity)
