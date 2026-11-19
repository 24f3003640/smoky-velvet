"""
Liquid Antique Gold reactive ripple effect.
Calculates organic expanding waves from triggered key coordinates across the 81-LED matrix.
"""
from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple
from core.color import Color, LIQUID_GOLD_GRADIENT
from core.layout import KeyboardLayout
from effects.base import Effect

class SingleRipple:
    """A single expanding ripple instance triggered by a keypress."""
    def __init__(
        self,
        origin_led: int,
        start_time: float,
        duration: float = 0.85,     # 850 ms
        expansion: float = 0.55,    # 550 ms
        fade: float = 0.30,         # 300 ms
        max_radius: float = 5.5,    # 5.5 key distances
        wave_thickness: float = 1.8 # 1.8 key distances
    ):
        self.origin_led = origin_led
        self.start_time = start_time
        self.duration = duration
        self.expansion = expansion
        self.fade = fade
        self.max_radius = max_radius
        self.wave_thickness = wave_thickness
        # Gaussian standard deviation
        self.sigma = max(0.1, wave_thickness / 2.355)
        self.two_sigma_sq = 2.0 * self.sigma * self.sigma
        self.age = 0.0

    def update(self, current_time: float) -> None:
        self.age = current_time - self.start_time

    @property
    def is_finished(self) -> bool:
        return self.age >= self.duration

    def calculate_led_contribution(self, distance: float) -> Optional[Tuple[Color, float]]:
        """
        Returns (Color, intensity) where intensity in [0.0, 1.0].
        """
        if self.age < 0 or self.age >= self.duration:
            return None

        # Current wave crest radius
        if self.age <= self.expansion:
            current_radius = self.max_radius * (self.age / self.expansion)
            fade_factor = 1.0
        else:
            current_radius = self.max_radius
            fade_progress = (self.age - self.expansion) / self.fade
            fade_factor = max(0.0, 1.0 - fade_progress)

        # Distance from wave crest
        dist_from_crest = abs(distance - current_radius)
        if dist_from_crest > self.wave_thickness * 1.8:
            return None

        # Gaussian falloff around wavefront
        gaussian = math.exp(-(dist_from_crest * dist_from_crest) / self.two_sigma_sq)
        intensity = gaussian * fade_factor

        if intensity < 0.03:
            return None

        # Progress through 4-stage Liquid Gold gradient (0.0 to 1.0)
        grad_progress = min(1.0, self.age / self.duration)
        gold_color = LIQUID_GOLD_GRADIENT.sample(grad_progress)

        return (gold_color, min(1.0, intensity))


class LiquidGoldRippleManager(Effect):
    """
    Manages active overlapping ripples triggered by user keystrokes.
    """
    def __init__(
        self,
        duration: float = 0.85,
        expansion: float = 0.55,
        fade: float = 0.30,
        max_radius: float = 5.5,
        wave_thickness: float = 1.8,
        max_concurrent: int = 16
    ):
        self.duration = duration
        self.expansion = expansion
        self.fade = fade
        self.max_radius = max_radius
        self.wave_thickness = wave_thickness
        self.max_concurrent = max_concurrent
        self.ripples: List[SingleRipple] = []

    def trigger(self, origin_led: int, timestamp: Optional[float] = None) -> None:
        """Trigger a new ripple originating from origin_led."""
        t = timestamp if timestamp is not None else time.monotonic()
        if len(self.ripples) >= self.max_concurrent:
            self.ripples.pop(0)

        ripple = SingleRipple(
            origin_led=origin_led,
            start_time=t,
            duration=self.duration,
            expansion=self.expansion,
            fade=self.fade,
            max_radius=self.max_radius,
            wave_thickness=self.wave_thickness
        )
        self.ripples.append(ripple)

    def update(self, dt: float, current_time: float) -> None:
        for r in self.ripples:
            r.update(current_time)
        self.ripples = [r for r in self.ripples if not r.is_finished]

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Tuple[Color, float]]]) -> None:
        if not self.ripples:
            return

        for ripple in self.ripples:
            for led_idx in range(layout.led_count):
                dist = layout.distance(ripple.origin_led, led_idx)
                contrib = ripple.calculate_led_contribution(dist)
                if contrib is not None:
                    color, alpha = contrib
                    existing = buffer[led_idx]
                    if existing is None:
                        buffer[led_idx] = (color, alpha)
                    else:
                        prev_col, prev_alpha = existing
                        # Combine alphas and blend colors
                        new_alpha = min(1.0, prev_alpha + alpha * (1.0 - prev_alpha))
                        blended_col = prev_col.lerp(color, alpha / max(0.001, prev_alpha + alpha))
                        buffer[led_idx] = (blended_col, new_alpha)

    def is_finished(self) -> bool:
        # The manager persists across the engine lifecycle
        return False
