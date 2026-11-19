"""
Layer-based lighting compositor.
Combines Base, Reactive, Indicator, and Environmental layers into a single RGB frame.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from core.color import Color, MIDNIGHT_PURPLE
from core.layout import KeyboardLayout
from effects.base import Effect

class BaseLayer:
    """Foundational underglow illumination (Layer 1)."""
    def __init__(self, led_count: int, default_color: Color = MIDNIGHT_PURPLE):
        self.led_count = led_count
        self.colors: List[Color] = [default_color] * led_count
        self.enabled = True
        self.opacity = 1.0

    def set_all(self, color: Color) -> None:
        self.colors = [color] * self.led_count

    def set_key(self, led_index: int, color: Color) -> None:
        if 0 <= led_index < self.led_count:
            self.colors[led_index] = color

    def set_keys(self, color_map: Dict[int, Color]) -> None:
        for idx, col in color_map.items():
            if 0 <= idx < self.led_count:
                self.colors[idx] = col


class ReactiveLayer:
    """Reactive keypress effects and transient animations (Layer 2)."""
    def __init__(self, led_count: int):
        self.led_count = led_count
        self.effects: List[Effect] = []
        self.enabled = True
        self.opacity = 1.0

    def add_effect(self, effect: Effect) -> None:
        self.effects.append(effect)

    def remove_effect(self, effect: Effect) -> None:
        if effect in self.effects:
            self.effects.remove(effect)

    def update(self, dt: float, current_time: float) -> None:
        for eff in self.effects:
            eff.update(dt, current_time)
        # Prune dead effects
        self.effects = [eff for eff in self.effects if not eff.is_finished()]

    def render(self, layout: KeyboardLayout) -> List[Optional[Color]]:
        buffer: List[Optional[Color]] = [None] * self.led_count
        if not self.enabled:
            return buffer

        for eff in self.effects:
            eff.render(layout, buffer)

        # Scale by layer opacity if needed
        if self.opacity < 1.0:
            for i in range(self.led_count):
                if buffer[i] is not None:
                    buffer[i] = buffer[i].scale(self.opacity) # type: ignore

        return buffer


class IndicatorLayer:
    """System status overrides e.g. Caps Lock, Mute, Volume (Layer 3)."""
    def __init__(self, led_count: int):
        self.led_count = led_count
        # Mapping: led_index -> (Color, opacity)
        self.indicators: Dict[int, Tuple[Color, float]] = {}
        self.enabled = True

    def set_indicator(self, led_index: int, color: Color, opacity: float = 1.0) -> None:
        if 0 <= led_index < self.led_count:
            self.indicators[led_index] = (color, max(0.0, min(1.0, opacity)))

    def clear_indicator(self, led_index: int) -> None:
        self.indicators.pop(led_index, None)

    def clear_all(self) -> None:
        self.indicators.clear()


class Compositor:
    """
    Composites all layers into the final 81-LED RGB output frame.
    Guarantees dirty-frame diffing to prevent redundant hardware writes.
    """
    def __init__(self, layout: KeyboardLayout, global_brightness: float = 1.0):
        self.layout = layout
        self.led_count = layout.led_count
        self.global_brightness = max(0.0, min(1.0, global_brightness))

        self.base_layer = BaseLayer(self.led_count)
        self.reactive_layer = ReactiveLayer(self.led_count)
        self.indicator_layer = IndicatorLayer(self.led_count)

        self._last_frame: Optional[List[Color]] = None

    def set_brightness(self, brightness: float) -> None:
        self.global_brightness = max(0.0, min(1.0, brightness))

    def update(self, dt: float, current_time: float) -> None:
        self.reactive_layer.update(dt, current_time)

    def render_frame(self) -> Tuple[List[Color], bool]:
        """
        Renders the active layers and returns (final_colors, is_dirty).
        is_dirty is True only if colors differ from the previous rendered frame.
        """
        # Step 1: Base Layer
        if self.base_layer.enabled:
            frame = [c for c in self.base_layer.colors]
        else:
            frame = [Color(0, 0, 0)] * self.led_count

        # Step 2: Reactive Layer (Additive blending over base)
        if self.reactive_layer.enabled and self.reactive_layer.effects:
            reactive_buf = self.reactive_layer.render(self.layout)
            for i in range(self.led_count):
                rec = reactive_buf[i]
                if rec is not None:
                    frame[i] = frame[i].blend_additive(rec)

        # Step 3: Indicator Layer (Override with alpha blend)
        if self.indicator_layer.enabled and self.indicator_layer.indicators:
            for idx, (color, opacity) in self.indicator_layer.indicators.items():
                if 0 <= idx < self.led_count:
                    frame[idx] = frame[idx].blend_alpha(color, opacity)

        # Step 4: Global Brightness Scaling
        if self.global_brightness < 1.0:
            frame = [c.scale(self.global_brightness) for c in frame]

        # Step 5: Dirty check
        is_dirty = True
        if self._last_frame is not None:
            if len(self._last_frame) == len(frame) and all(c1 == c2 for c1, c2 in zip(self._last_frame, frame)):
                is_dirty = False

        if is_dirty:
            self._last_frame = frame

        return frame, is_dirty
