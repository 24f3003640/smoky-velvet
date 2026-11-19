"""
Liquid Antique Gold & Watercolor reactive ripple effect for URX Core75.
Calculates organic expanding waves from triggered key coordinates across the 81-LED matrix.
Implements watercolor dispersion, smooth cosine envelope, and chromatic pigment dissolution.
"""
from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple
from core.color import Color, SMOKY_PLUM_PURPLE, MOLTEN_ANTIQUE_GOLD, DEEP_ANTIQUE_GOLD, VELVET_MAGENTA, LIQUID_GOLD_GRADIENT
from core.layout import KeyboardLayout
from effects.base import Effect

# Harmonic wave crest colors
LUMINOUS_AMETHYST = Color(255, 107, 248)  # #FF6BF8 - Radiant Electric Amethyst
ROSE_GOLD         = Color(255, 126, 101)  # #FF7E65 - Warm 18k Rose Gold
ANTIQUE_COPPER    = Color(255, 100, 24)   # #FF6418 - Burnished Antique Copper

class SingleRipple:
    """A single organic expanding ripple instance triggered by a keypress."""
    def __init__(
        self,
        origin_led: int,
        start_time: float,
        duration: float = 0.60,      # 600 ms smooth duration
        expansion: float = 0.45,     # Kept for backward compatibility
        fade: float = 0.15,          # Kept for backward compatibility
        max_radius: float = 2.6,     # 2-3 keys localized radius
        wave_thickness: float = 1.0, # 1.0 key distance
        crest_color: Optional[Color] = None,
        base_color: Optional[Color] = None,
    ):
        self.origin_led = origin_led
        self.start_time = start_time
        self.duration = duration
        self.expansion = expansion
        self.fade = fade
        self.max_radius = max_radius
        self.wave_thickness = wave_thickness
        self.crest_color = crest_color if crest_color is not None else LUMINOUS_AMETHYST
        self.base_color = base_color if base_color is not None else SMOKY_PLUM_PURPLE
        self.age = 0.0

    def update(self, current_time: float) -> None:
        self.age = current_time - self.start_time

    @property
    def is_finished(self) -> bool:
        return self.age >= self.duration

    def calculate_led_contribution(self, distance: float, base_color: Optional[Color] = None) -> Optional[Tuple[Color, float]]:
        """
        Returns (Color, intensity) where intensity in [0.0, 1.0].
        Calculates fluid dispersion and watercolor dissolution into the background pond.
        """
        if self.age < 0 or self.age >= self.duration:
            return None

        # Normalized lifecycle progress [0.0, 1.0]
        p = self.age / self.duration

        # Fluid dispersion: wave expands smoothly and naturally decelerates as radius grows
        current_radius = self.max_radius * math.sqrt(p)

        # Dynamic wavefront dispersion: wave naturally broadens slightly as it travels
        current_thickness = self.wave_thickness * (1.0 + 0.6 * p)
        sigma = max(0.1, current_thickness / 2.355)
        two_sigma_sq = 2.0 * sigma * sigma

        # Distance from wave crest
        diff = distance - current_radius
        if abs(diff) > current_thickness * 1.6:
            return None

        # Spatial Gaussian profile around wavefront
        gaussian = math.exp(-(diff * diff) / two_sigma_sq)

        # Smooth watercolor ease-out envelope: both value and derivative gently reach 0 at t=duration
        envelope = math.cos(0.5 * math.pi * p) ** 2.0
        intensity = gaussian * envelope

        if intensity < 0.015:
            return None

        # Watercolor pigment dissolution:
        # As wave travels outward, the pigment dissolves from crest_color into the resting pond color
        target_base = base_color or self.base_color
        dissolved_color = self.crest_color.lerp(target_base, p * 0.80)

        return (dissolved_color, min(1.0, intensity))


class LiquidGoldRippleManager(Effect):
    """
    Manages active overlapping ripples triggered by user keystrokes.
    """
    def __init__(
        self,
        duration: float = 0.60,
        expansion: float = 0.45,
        fade: float = 0.15,
        max_radius: float = 2.6,
        wave_thickness: float = 1.0,
        max_concurrent: int = 16,
        crest_color: Optional[Color] = None,
        base_color: Optional[Color] = None,
    ):
        self.duration = duration
        self.expansion = expansion
        self.fade = fade
        self.max_radius = max_radius
        self.wave_thickness = wave_thickness
        self.max_concurrent = max_concurrent
        self.crest_color = crest_color if crest_color is not None else LUMINOUS_AMETHYST
        self.base_color = base_color if base_color is not None else SMOKY_PLUM_PURPLE
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
            wave_thickness=self.wave_thickness,
            crest_color=self.crest_color,
            base_color=self.base_color,
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
                contrib = ripple.calculate_led_contribution(dist, self.base_color)
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
