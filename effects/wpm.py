"""
Live Typing Speedometer & WPM Gauge Effect for URX Core75.
Tracks physical typing cadence in real-time and renders a dynamic velocity meter across the Number Row (keys 1-0).
PRIVACY GUARANTEE: Operates purely on timestamps. Zero keystroke identity or text content logged.
"""
from __future__ import annotations
import math
import time
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple
from core.color import Color
from core.layout import KeyboardLayout
from effects.base import Effect

# Number Row LED Indices: '1' through '0' (10 keys total)
# 15: "1", 16: "2", 17: "3", 18: "4", 19: "5", 20: "6", 21: "7", 22: "8", 23: "9", 24: "0"
NUMBER_ROW_LEDS = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

# High-contrast, optical velocity palettes designed for translucent smoky polycarbonate
COLOR_SOLAR_WHITE   = Color(255, 255, 255)
# Legacy aliases for compatibility
COLOR_MOLTEN_GOLD   = Color(255, 184, 0)
COLOR_NEON_VIOLET   = Color(180, 0, 255)
COLOR_STEALTH_BLOOD = Color(255, 0, 128)

WPM_THEMES: Dict[str, List[Color]] = {
    # 1. Tachometer: F1-style 5-zone racing meter with maximum optical contrast against crimson/purple
    #    1-3: Electric Ice Cyan (#00F0FF)
    #    4-5: Electric Neon Mint (#00FFAA)
    #    6-7: Solar Amber Gold (#FFB800)
    #    8-9: Hot Neon Magenta (#FF0080)
    #    0:   Hyperdrive Solar White (#FFFFFF)
    "tachometer": [
        Color(0, 240, 255),   # 1: Electric Ice Cyan
        Color(0, 229, 255),   # 2: Electric Ice Cyan
        Color(0, 200, 255),   # 3: Vivid Sky Azure
        Color(0, 255, 170),   # 4: Electric Neon Mint
        Color(20, 245, 120),  # 5: Electric Lime Mint
        Color(255, 215, 0),   # 6: Solar Gold
        Color(255, 160, 0),   # 7: Vivid Amber
        Color(255, 0, 128),   # 8: Hot Neon Magenta
        Color(255, 20, 180),  # 9: Shocking Electric Pink
        Color(255, 255, 255), # 0: Hyperdrive Solar White
    ],
    # 2. Ice Cyan: Crisp, razor-sharp crystalline cyan directly complementary to crimson
    "ice_cyan": [
        Color(0, 240, 255),
        Color(0, 235, 255),
        Color(0, 225, 255),
        Color(20, 220, 255),
        Color(50, 225, 255),
        Color(80, 230, 255),
        Color(120, 235, 255),
        Color(160, 240, 255),
        Color(210, 250, 255),
        Color(255, 255, 255),
    ],
    # 3. Cyberpunk: Neon Cyan through Ultraviolet to Hot Magenta & Pure White
    "cyberpunk": [
        Color(0, 240, 255),   # 1: Cyan
        Color(0, 220, 255),   # 2: Azure
        Color(30, 170, 255),  # 3: Sky Blue
        Color(120, 70, 255),  # 4: Indigo
        Color(170, 0, 255),   # 5: Ultraviolet
        Color(215, 0, 235),   # 6: Neon Orchid
        Color(255, 0, 150),   # 7: Hot Pink
        Color(255, 0, 100),   # 8: Neon Rose
        Color(255, 60, 180),  # 9: Shocking Fuchsia
        Color(255, 255, 255), # 0: Solar White
    ],
    # 4. Amber Gold: Radiant molten solar amber transitioning into pure white (0% green)
    "amber_gold": [
        Color(255, 150, 0),   # 1: Deep Amber
        Color(255, 165, 0),   # 2: Amber
        Color(255, 180, 0),   # 3: Solar Gold
        Color(255, 195, 0),   # 4: Warm Gold
        Color(255, 210, 0),   # 5: Brilliant Gold
        Color(255, 220, 30),  # 6: Yellow Gold
        Color(255, 230, 70),  # 7: Light Gold
        Color(255, 240, 120), # 8: Pale Sun
        Color(255, 248, 180), # 9: Solar Ray
        Color(255, 255, 255), # 0: Solar White
    ],
    # 5. Neon Mint: Matrix-style electric mint emerald transitioning into pure white
    "neon_mint": [
        Color(0, 255, 150),   # 1: Deep Mint
        Color(0, 255, 165),   # 2: Electric Mint
        Color(0, 255, 180),   # 3: Aqua Mint
        Color(20, 255, 195),  # 4: Bright Mint
        Color(50, 255, 210),  # 5: Neon Mint
        Color(90, 255, 220),  # 6: Mint Frost
        Color(130, 255, 230), # 7: Ice Mint
        Color(170, 255, 240), # 8: Pale Mint
        Color(215, 255, 248), # 9: Glacier White
        Color(255, 255, 255), # 0: Solar White
    ],
}


class WpmGaugeEffect(Effect):
    def __init__(self, window_seconds: float = 4.0, max_scale_wpm: float = 100.0, theme: str = "tachometer"):
        self.window_seconds = window_seconds
        self.max_scale_wpm = max_scale_wpm
        self.theme = theme if theme in WPM_THEMES else "tachometer"
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

    def set_theme(self, theme_name: str) -> bool:
        if theme_name in WPM_THEMES:
            self.theme = theme_name
            return True
        return False

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
        palette = WPM_THEMES.get(self.theme, WPM_THEMES["tachometer"])
        is_overdrive = self._current_wpm >= 100.0

        for i, led_idx in enumerate(NUMBER_ROW_LEDS):
            if led_idx >= layout.led_count:
                continue

            base_color = palette[min(i, len(palette) - 1)]

            if i < int(active_keys_float):
                # Fully lit key - 100% opacity overrides base layer without muddy bleed
                key_opacity = 1.0 * self._display_opacity
                if is_overdrive:
                    key_color = base_color.lerp(COLOR_SOLAR_WHITE, 0.35)
                else:
                    key_color = base_color
            elif i == int(active_keys_float):
                # Partial leading edge key acts as luminous needle highlight
                partial = active_keys_float - int(active_keys_float)
                key_opacity = max(0.0, partial * 1.0 * self._display_opacity)
                key_color = base_color.lerp(COLOR_SOLAR_WHITE, 0.45)
            else:
                key_opacity = 0.0

            if key_opacity > 0.01:
                existing = buffer[led_idx]
                if existing is not None:
                    ex_color, ex_alpha = existing
                    buffer[led_idx] = (key_color.blend_alpha(ex_color, ex_alpha), min(1.0, key_opacity + ex_alpha))
                else:
                    buffer[led_idx] = (key_color, key_opacity)
