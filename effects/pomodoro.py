"""
Pomodoro & Focus Countdown Timer Effect for URX Core75.
Visualizes remaining focus time across the 12-segment F-Row (F1-F12).
Upon completion, emits a calming ambient celebration wave across the keyboard.
"""
from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple
from core.color import Color
from core.layout import KeyboardLayout
from effects.base import Effect

# F-Row LED Indices: F1 through F12 (12 keys)
FROW_LEDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# Colors:
# Focus active: Soothing Emerald Cyan / Azure
COLOR_FOCUS_ACTIVE = Color(0, 210, 255)
# Sub-key tick pulse
COLOR_TICK_PULSE   = Color(255, 255, 255)
# Celebration finish: Radiant Pure White
COLOR_CELEBRATION  = Color(255, 255, 255)

class PomodoroTimerEffect(Effect):
    def __init__(self):
        self.enabled = False
        self.start_time: float = 0.0
        self.duration_seconds: float = 0.0
        self.is_active: bool = False
        self._celebration_start: float = 0.0
        self._celebration_duration: float = 3.5

    def start_timer(self, minutes: float) -> None:
        """Start a new Pomodoro focus timer."""
        self.duration_seconds = max(60.0, minutes * 60.0)
        self.start_time = time.monotonic()
        self.is_active = True
        self.enabled = True
        self._celebration_start = 0.0

    def cancel(self) -> None:
        """Cancel the active timer."""
        self.is_active = False
        self.enabled = False
        self._celebration_start = 0.0

    @property
    def remaining_seconds(self) -> float:
        if not self.is_active:
            return 0.0
        elapsed = time.monotonic() - self.start_time
        return max(0.0, self.duration_seconds - elapsed)

    @property
    def remaining_minutes_str(self) -> str:
        rem = self.remaining_seconds
        mins = int(rem // 60)
        secs = int(rem % 60)
        return f"{mins:02d}:{secs:02d}"

    def update(self, dt: float, current_time: float) -> None:
        if not self.enabled:
            return

        if self.is_active:
            elapsed = current_time - self.start_time
            if elapsed >= self.duration_seconds:
                # Timer finished! Transition to celebration wave
                self.is_active = False
                self._celebration_start = current_time

        if self._celebration_start > 0.0:
            if current_time - self._celebration_start >= self._celebration_duration:
                self.enabled = False
                self._celebration_start = 0.0

    def is_finished(self) -> bool:
        return False

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Tuple[Color, float]]]) -> None:
        if not self.enabled:
            return

        now = time.monotonic()

        # 1. Timer Active State: F1-F12 countdown
        if self.is_active:
            elapsed = now - self.start_time
            fraction_remaining = max(0.0, min(1.0, 1.0 - (elapsed / self.duration_seconds)))
            active_keys_float = fraction_remaining * len(FROW_LEDS)

            # Breathing pulse on the currently expiring minute key
            pulse = 0.5 + 0.5 * math.sin(now * 3.0)

            for i, led_idx in enumerate(FROW_LEDS):
                if led_idx >= layout.led_count:
                    continue

                if i < int(active_keys_float):
                    # Solid key remaining
                    buffer[led_idx] = (COLOR_FOCUS_ACTIVE, 0.85)
                elif i == int(active_keys_float):
                    # Partial / current minute key
                    col = COLOR_FOCUS_ACTIVE.lerp(COLOR_TICK_PULSE, pulse * 0.7)
                    buffer[led_idx] = (col, 0.90)

        # 2. Celebration State: 3 gentle harmonic breathing waves
        elif self._celebration_start > 0.0:
            p = (now - self._celebration_start) / self._celebration_duration
            if p < 1.0:
                # 3 harmonic sine pulses
                wave = math.sin(p * math.pi * 3.0) ** 2.0
                fade = 1.0 - p
                intensity = wave * fade * 0.80

                for i in range(layout.led_count):
                    existing = buffer[i]
                    if existing is not None:
                        ex_col, ex_a = existing
                        buffer[i] = (COLOR_CELEBRATION.blend_alpha(ex_col, ex_a), min(1.0, intensity + ex_a))
                    else:
                        buffer[i] = (COLOR_CELEBRATION, intensity)
