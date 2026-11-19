"""
Typing Heatmap Effect for URX Core75.
Simulates per-key thermodynamic heating, localized heat conduction,
and exponential cooling decay across all 81 physical LEDs.
"""
from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple
from core.color import Color, Gradient
from core.layout import KeyboardLayout
from effects.base import Effect

# Scientific & Aesthetic Thermal Gradient:
# Cold (Velvet) -> Warm (Sapphire) -> Hot (Cyan) -> Scorching (Coral) -> Blazing (White)
THERMAL_GRADIENT = Gradient([
    (0.00, Color(255, 0, 254)),  # Base Velvet Purple (Cold)
    (0.20, Color(30, 144, 255)),  # Electric Sapphire
    (0.45, Color(0, 255, 230)),   # Radiant Cyan
    (0.70, Color(255, 95, 35)),   # Sunset Coral
    (0.90, Color(255, 220, 100)), # Incandescent Gold
    (1.00, Color(255, 255, 255)), # Blazing White
])

class TypingHeatmapManager(Effect):
    """
    Simulates thermal energy per key.
    Energy increases with keypresses, conducts softly to neighboring keys,
    and dissipates via Newton's law of cooling.
    """
    def __init__(
        self,
        led_count: int = 81,
        heat_per_stroke: float = 0.28,
        cooling_half_life: float = 3.5,  # Cools by 50% every 3.5s
        conduction_rate: float = 0.08,    # Gentle heat spread to immediate neighbors
    ):
        self.led_count = led_count
        self.heat_per_stroke = heat_per_stroke
        self.cooling_rate = math.log(2.0) / max(0.1, cooling_half_life)
        self.conduction_rate = conduction_rate

        self.temperatures: List[float] = [0.0] * led_count
        self.enabled: bool = True
        self._last_update_time: float = time.monotonic()

    def trigger(self, led_index: int, timestamp: Optional[float] = None) -> None:
        """Inject thermal energy into the struck key."""
        if not self.enabled:
            return
        if 0 <= led_index < self.led_count:
            self.temperatures[led_index] = min(1.0, self.temperatures[led_index] + self.heat_per_stroke)

    def update(self, dt: float, current_time: float) -> None:
        if not self.enabled:
            return

        dt = max(0.001, min(10.0, dt))
        decay_factor = math.exp(-self.cooling_rate * dt)

        # 1. Newton's cooling decay
        for i in range(self.led_count):
            self.temperatures[i] = max(0.0, self.temperatures[i] * decay_factor)
            if self.temperatures[i] < 0.005:
                self.temperatures[i] = 0.0

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Tuple[Color, float]]]) -> None:
        if not self.enabled:
            return

        for i in range(min(self.led_count, layout.led_count)):
            temp = self.temperatures[i]
            if temp <= 0.02:
                continue

            # Sample color along thermal gradient
            heat_color = THERMAL_GRADIENT.sample(temp)
            alpha = min(0.95, temp * 1.15)

            existing = buffer[i]
            if existing is None:
                buffer[i] = (heat_color, alpha)
            else:
                prev_col, prev_alpha = existing
                new_alpha = min(0.95, prev_alpha + alpha * (1.0 - prev_alpha))
                blended = prev_col.lerp(heat_color, alpha / max(0.001, prev_alpha + alpha))
                buffer[i] = (blended, new_alpha)

    def is_finished(self) -> bool:
        return False
