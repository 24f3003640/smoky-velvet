"""
Liquid Antique Gold & Watercolor reactive ripple effect for URX Core75.
Calculates organic expanding waves from triggered key coordinates across the 81-LED matrix.
Implements watercolor dispersion, smooth cosine envelope, dynamic typing-cadence adaptation,
per-key debounce, and dominant-wave interference blending to tame typing chaos.
"""
from __future__ import annotations
import math
import time
from typing import Dict, List, Optional, Tuple
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
    Manages active overlapping ripples with cadence adaptation and chaos suppression.
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

        # Anti-chaos tracking
        self._last_key_times: Dict[int, float] = {}
        self._last_keystroke_time: float = 0.0
        self._keystroke_interval_ema: float = 0.50

    def trigger(self, origin_led: int, timestamp: Optional[float] = None) -> None:
        """
        Trigger a new ripple originating from origin_led with cadence-aware adaptation
        and per-key debounce to prevent overlapping chaos.
        """
        t = timestamp if timestamp is not None else time.monotonic()

        # 1. Per-key debounce: if the exact same key was struck < 90ms ago, ignore duplicate
        if origin_led in self._last_key_times:
            if t - self._last_key_times[origin_led] < 0.09:
                return
        self._last_key_times[origin_led] = t

        # 2. Dynamic Cadence Detection:
        # Smoothly track typing speed via Exponential Moving Average of keystroke intervals
        if self._last_keystroke_time > 0:
            dt = max(0.04, min(1.0, t - self._last_keystroke_time))
            self._keystroke_interval_ema = 0.35 * dt + 0.65 * self._keystroke_interval_ema
        self._last_keystroke_time = t

        # 3. Dynamic speed-based tuning:
        # Slow typing / Pause (interval >= 0.45s) -> Full languid spread (e.g. 0.60s, 2.6 keys)
        # Rapid typing (interval <= 0.14s)      -> Tight, crisp droplet (e.g. 0.38s, 1.9 keys)
        cadence_factor = max(0.0, min(1.0, (self._keystroke_interval_ema - 0.14) / 0.31))
        dyn_duration = max(0.35, self.duration * (0.65 + 0.35 * cadence_factor))
        dyn_radius = max(1.8, self.max_radius * (0.75 + 0.25 * cadence_factor))

        if len(self.ripples) >= self.max_concurrent:
            self.ripples.pop(0)

        ripple = SingleRipple(
            origin_led=origin_led,
            start_time=t,
            duration=dyn_duration,
            expansion=self.expansion,
            fade=self.fade,
            max_radius=dyn_radius,
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
        """
        Renders ripples with dominant-wave interference blending.
        Eliminates bright white/cluster blowouts when typing fast.
        """
        if not self.ripples:
            return

        # Collect contributions per LED
        led_contributions: List[List[Tuple[Color, float]]] = [[] for _ in range(layout.led_count)]

        for ripple in self.ripples:
            for led_idx in range(layout.led_count):
                dist = layout.distance(ripple.origin_led, led_idx)
                contrib = ripple.calculate_led_contribution(dist, self.base_color)
                if contrib is not None:
                    led_contributions[led_idx].append(contrib)

        # Composite per LED using dominant-wave interference:
        # The primary wave retains full crest definition; secondary overlapping waves
        # add a soft ambient wash without blowing out the LED cluster to full saturation.
        for led_idx in range(layout.led_count):
            contribs = led_contributions[led_idx]
            if not contribs:
                continue

            if len(contribs) == 1:
                buffer[led_idx] = contribs[0]
            else:
                # Sort by intensity descending
                contribs.sort(key=lambda c: c[1], reverse=True)
                dominant_col, dominant_alpha = contribs[0]

                # Secondary waves contribute a soft 20% ambient wash
                sec_alpha_sum = sum(c[1] for c in contribs[1:]) * 0.20
                final_alpha = min(0.95, dominant_alpha + sec_alpha_sum * (1.0 - dominant_alpha))

                # Color softly blends towards secondary hues
                secondary_col = contribs[1][0]
                final_col = dominant_col.lerp(secondary_col, min(0.30, sec_alpha_sum))

                buffer[led_idx] = (final_col, final_alpha)

    def is_finished(self) -> bool:
        # The manager persists across the engine lifecycle
        return False
