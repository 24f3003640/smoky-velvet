"""
Fluid LED Volume Gauge & Mute Indicator Effect for URX Core75.
Visualizes system PipeWire audio levels across the F1-F12 function row in real time,
with automatic watercolor dissolution when inactive and hardware mute indication.
"""
from __future__ import annotations
import math
import subprocess
import time
from typing import List, Optional, Tuple
from core.color import Color, Gradient
from core.layout import KeyboardLayout
from effects.base import Effect

# Scientific & Aesthetic Volume Gradient:
# Low: Electric Sapphire (#1E90FF) -> Mid: Radiant Cyan (#00FFE6) -> High: Sunset Amber (#FFB400) -> Peak: Crimson Flame (#FF1450)
VOLUME_GRADIENT = Gradient([
    (0.00, Color(30, 144, 255)),  # Calm Electric Sapphire
    (0.35, Color(0, 255, 230)),   # Radiant Cyan
    (0.65, Color(255, 180, 0)),   # Sunset Amber
    (0.85, Color(255, 60, 20)),   # Vivid Coral-Red
    (1.00, Color(255, 20, 80)),   # Crimson Flame
])

MUTED_COLOR = Color(220, 20, 60)       # Soft Crimson Amber
UNLIT_TRACK_COLOR = Color(40, 20, 60)  # Very subtle backdrop dot for unlit segments

class VolumeGaugeEffect(Effect):
    """
    Overlays live volume level on F1-F12 when volume changes or knob turns.
    Fades out gently after 1.5s of inactivity.
    """
    def __init__(self, fade_timeout: float = 1.5, fade_duration: float = 0.45):
        self.fade_timeout = fade_timeout
        self.fade_duration = fade_duration
        self.f_keys = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # F1 to F12 LEDs
        self.delete_key = 13  # Key right next to physical knob

        self.current_volume: float = 0.50
        self.is_muted: bool = False
        self.last_active_time: float = 0.0
        self._last_poll_time: float = 0.0

    def trigger_activity(self) -> None:
        """Called whenever volume knob turns, clicks, or volume changes."""
        self.last_active_time = time.monotonic()
        self._query_system_volume()

    def set_volume_state(self, volume: float, muted: bool = False) -> None:
        """Manually update volume level and mute state (useful for tests and IPC overrides)."""
        self.current_volume = max(0.0, volume)
        self.is_muted = muted
        self.last_active_time = time.monotonic()

    def _query_system_volume(self) -> None:
        try:
            out = subprocess.check_output(
                ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                timeout=0.08,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            # Format: "Volume: 0.60" or "Volume: 0.60 [MUTED]"
            parts = out.split()
            if len(parts) >= 2:
                self.current_volume = max(0.0, float(parts[1]))
                self.is_muted = "[MUTED]" in out
        except Exception:
            pass

    def update(self, dt: float, current_time: float) -> None:
        # Periodically poll volume while active (every 80ms)
        if current_time - self.last_active_time < self.fade_timeout + self.fade_duration:
            if current_time - self._last_poll_time > 0.08:
                self._query_system_volume()
                self._last_poll_time = current_time

    def _blend(self, buffer: List[Optional[Tuple[Color, float]]], idx: int, color: Color, alpha: float) -> None:
        if 0 <= idx < len(buffer):
            existing = buffer[idx]
            if existing is None:
                buffer[idx] = (color, alpha)
            else:
                prev_col, prev_alpha = existing
                new_alpha = min(0.98, prev_alpha + alpha * (1.0 - prev_alpha))
                ratio = alpha / max(0.001, prev_alpha + alpha)
                blended = prev_col.lerp(color, ratio)
                buffer[idx] = (blended, new_alpha)

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Tuple[Color, float]]]) -> None:
        now = time.monotonic()
        time_since_active = now - self.last_active_time

        # Persistent hardware mute indicator on Delete key (next to knob)
        if self.is_muted:
            self._blend(buffer, self.delete_key, MUTED_COLOR, 0.85)

        if time_since_active >= self.fade_timeout + self.fade_duration:
            return

        # Calculate cosine smooth dissolution envelope
        if time_since_active <= self.fade_timeout:
            envelope = 1.0
        else:
            fade_p = (time_since_active - self.fade_timeout) / self.fade_duration
            envelope = math.cos(0.5 * math.pi * min(1.0, fade_p)) ** 2.0

        if envelope <= 0.01:
            return

        if self.is_muted:
            # Muted breathing pulse across entire F-row
            pulse = 0.40 + 0.35 * math.sin(now * 4.0)
            alpha = pulse * envelope
            for led_idx in self.f_keys:
                self._blend(buffer, led_idx, MUTED_COLOR, alpha)
            return

        # Active volume bar: 12 segments
        total_segments = len(self.f_keys)
        norm_vol = min(1.0, self.current_volume)
        lit_count = min(total_segments, int(math.ceil(norm_vol * total_segments)))

        for i, led_idx in enumerate(self.f_keys):
            if i < lit_count:
                seg_ratio = (i + 1) / total_segments
                col = VOLUME_GRADIENT.sample(seg_ratio)
                alpha = 0.95 * envelope
                self._blend(buffer, led_idx, col, alpha)
            else:
                # Dim background track for unlit keys during HUD display
                self._blend(buffer, led_idx, UNLIT_TRACK_COLOR, 0.20 * envelope)

    def is_finished(self) -> bool:
        return False
