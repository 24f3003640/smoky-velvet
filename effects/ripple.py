"""
Liquid Antique Gold reactive ripple effect.
Calculates organic expanding waves from triggered key coordinates across the 81-LED matrix.
"""
from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple
from core.color import Color, MOLTEN_ANTIQUE_GOLD, DEEP_ANTIQUE_GOLD, VELVET_MAGENTA, LIQUID_GOLD_GRADIENT
from core.layout import KeyboardLayout
from effects.base import Effect

class SingleRipple:
    """A single expanding ripple instance triggered by a keypress."""
    def __init__(
        self,
        origin_led: int,
        start_time: float,
        duration: float = 0.55,      # 550 ms
        expansion: float = 0.40,     # 400 ms expanding
        fade: float = 0.15,          # 150 ms fading out
        max_radius: float = 2.6,     # 2.6 key distances (2-3 keys localized)
        wave_thickness: float = 1.1  # 1.1 key distances
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
        Pure Molten Antique Gold (Color(255, 52, 0)) wave radiating across 4.2 keys.
        """
        if self.age < 0 or self.age >= self.duration:
            return None

        # Strictly contain wave within max_radius
        if distance > self.max_radius + 0.5:
            return None

        # Calculate current wave crest radius and fading envelope
        if self.expansion > 0 and self.age <= self.expansion:
            current_radius = self.max_radius * (self.age / self.expansion)
            envelope = 1.0 - (self.age / self.duration) * 0.4
        else:
            current_radius = self.max_radius
            fade_progress = (self.age - self.expansion) / max(0.001, self.fade)
            envelope = max(0.0, 1.0 - fade_progress)

        # Distance from wave crest
        diff = distance - current_radius
        if abs(diff) > self.wave_thickness:
            return None

        # Gaussian falloff around wavefront
        gaussian = math.exp(-(diff * diff) / self.two_sigma_sq)
        intensity = gaussian * envelope

        if intensity < 0.03:
            return None

        return (MOLTEN_ANTIQUE_GOLD, min(1.0, intensity))


class LiquidGoldRippleManager(Effect):
    """
    Manages active overlapping ripples triggered by user keystrokes.
    """
    def __init__(
        self,
        duration: float = 0.55,
        expansion: float = 0.40,
        fade: float = 0.15,
        max_radius: float = 2.6,
        wave_thickness: float = 1.1,
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
