"""
Liquid Antique Gold reactive ripple effect.
Calculates organic expanding waves from triggered key coordinates across the 81-LED matrix.
"""
from __future__ import annotations
import math
import time
from typing import List, Optional
from core.color import Color, LIQUID_GOLD_GRADIENT
from core.layout import KeyboardLayout
from effects.base import Effect

class SingleRipple:
    """A single expanding ripple instance triggered by a keypress."""
    def __init__(
        self,
        origin_led: int,
        start_time: float,
        duration: float = 0.8,      # 800 ms
        expansion: float = 0.55,    # 550 ms
        fade: float = 0.25,         # 250 ms
        max_radius: float = 5.0,    # 5 key distances
        wave_thickness: float = 1.5 # 1.5 key distances
    ):
        self.origin_led = origin_led
        self.start_time = start_time
        self.duration = duration
        self.expansion = expansion
        self.fade = fade
        self.max_radius = max_radius
        self.wave_thickness = wave_thickness
        # Gaussian standard deviation based on FWHM = wave_thickness
        self.sigma = max(0.1, wave_thickness / 2.355)
        self.two_sigma_sq = 2.0 * self.sigma * self.sigma
        self.age = 0.0

    def update(self, current_time: float) -> None:
        self.age = current_time - self.start_time

    @property
    def is_finished(self) -> bool:
        return self.age >= self.duration

    def calculate_led_contribution(self, distance: float) -> Optional[Color]:
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

        if intensity < 0.02:
            return None

        # Progress through 4-stage Liquid Gold gradient (0.0 to 1.0)
        grad_progress = min(1.0, self.age / self.duration)
        gold_color = LIQUID_GOLD_GRADIENT.sample(grad_progress)

        # Return color scaled by wave intensity
        return gold_color.scale(intensity)


class LiquidGoldRippleManager(Effect):
    """
    Manages active overlapping ripples triggered by user keystrokes.
    """
    def __init__(
        self,
        duration: float = 0.8,
        expansion: float = 0.55,
        fade: float = 0.25,
        max_radius: float = 5.0,
        wave_thickness: float = 1.5,
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
        t = timestamp if timestamp is not None else time.time()
        # Cap concurrent ripples to prevent performance degradation under rapid typing
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
        # Prune expired ripples
        self.ripples = [r for r in self.ripples if not r.is_finished]

    def render(self, layout: KeyboardLayout, buffer: List[Optional[Color]]) -> None:
        if not self.ripples:
            return

        for ripple in self.ripples:
            for led_idx in range(layout.led_count):
                dist = layout.distance(ripple.origin_led, led_idx)
                contrib = ripple.calculate_led_contribution(dist)
                if contrib is not None:
                    existing = buffer[led_idx]
                    if existing is None:
                        buffer[led_idx] = contrib
                    else:
                        # Additive composition for overlapping waves
                        buffer[led_idx] = existing.blend_additive(contrib)

    def is_finished(self) -> bool:
        return len(self.ripples) == 0
