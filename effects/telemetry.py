"""
Hardware Telemetry Indicator Effect for URX Core75.
Visualizes real-time CPU load and RAM pressure across the F1-F12 function row segments.
"""
from __future__ import annotations
import math
from typing import List, Optional, Tuple
from core.color import Color, Gradient
from core.layout import KeyboardLayout
from effects.base import Effect
from integrations.system_stats import SystemTelemetry

SEGMENT_GRADIENT = Gradient([
    (0.00, Color(30, 144, 255)),  # 0% - Calm Sapphire
    (0.35, Color(0, 255, 230)),   # 35% - Radiant Aqua
    (0.65, Color(255, 180, 0)),   # 65% - Warm Amber
    (0.85, Color(255, 60, 20)),   # 85% - Hot Orange-Red
    (1.00, Color(255, 0, 80)),    # 100% - Critical Crimson
])

class TelemetryRowEffect(Effect):
    """
    Overlays CPU load on F1-F6 (LEDs 1..6) and RAM usage on F7-F12 (LEDs 7..12).
    """
    def __init__(self):
        self.telemetry = SystemTelemetry()
        self.enabled: bool = False
        self.cpu_leds = [1, 2, 3, 4, 5, 6]       # F1 to F6
        self.ram_leds = [7, 8, 9, 10, 11, 12]    # F7 to F12

    def update(self, dt: float, current_time: float) -> None:
        if self.enabled:
            self.telemetry.sample()

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Tuple[Color, float]]]) -> None:
        if not self.enabled:
            return

        cpu_ratio = self.telemetry.cpu_usage_pct / 100.0
        ram_ratio = self.telemetry.memory_usage_pct / 100.0

        # Render CPU Meter on F1-F6
        cpu_segments = min(6, int(math.ceil(cpu_ratio * 6.0)))
        for i, led_idx in enumerate(self.cpu_leds):
            if i < cpu_segments:
                seg_ratio = (i + 1) / 6.0
                col = SEGMENT_GRADIENT.sample(seg_ratio)
                buffer[led_idx] = (col, 0.90)

        # Render RAM Meter on F7-F12
        ram_segments = min(6, int(math.ceil(ram_ratio * 6.0)))
        for i, led_idx in enumerate(self.ram_leds):
            if i < ram_segments:
                seg_ratio = (i + 1) / 6.0
                col = SEGMENT_GRADIENT.sample(seg_ratio)
                buffer[led_idx] = (col, 0.85)

    def is_finished(self) -> bool:
        return False
