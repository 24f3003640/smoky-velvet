"""
Color models, conversions, and gradient interpolation.
"""
from __future__ import annotations
import math
from typing import List, Tuple, Sequence

class Color:
    __slots__ = ('r', 'g', 'b')

    def __init__(self, r: int | float, g: int | float, b: int | float):
        self.r = max(0, min(255, int(round(r))))
        self.g = max(0, min(255, int(round(g))))
        self.b = max(0, min(255, int(round(b))))

    @classmethod
    def from_hex(cls, hex_str: str) -> Color:
        hex_str = hex_str.lstrip('#')
        if len(hex_str) == 3:
            hex_str = ''.join(c * 2 for c in hex_str)
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color: {hex_str}")
        return cls(
            int(hex_str[0:2], 16),
            int(hex_str[2:4], 16),
            int(hex_str[4:6], 16),
        )

    def to_hex(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    def to_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def lerp(self, other: Color, t: float) -> Color:
        t = max(0.0, min(1.0, t))
        return Color(
            self.r + (other.r - self.r) * t,
            self.g + (other.g - self.g) * t,
            self.b + (other.b - self.b) * t,
        )

    def blend_additive(self, other: Color, alpha: float = 1.0) -> Color:
        alpha = max(0.0, min(1.0, alpha))
        return Color(
            min(255, self.r + other.r * alpha),
            min(255, self.g + other.g * alpha),
            min(255, self.b + other.b * alpha),
        )

    def blend_alpha(self, other: Color, alpha: float) -> Color:
        alpha = max(0.0, min(1.0, alpha))
        return Color(
            self.r * (1.0 - alpha) + other.r * alpha,
            self.g * (1.0 - alpha) + other.g * alpha,
            self.b * (1.0 - alpha) + other.b * alpha,
        )

    def scale(self, factor: float) -> Color:
        factor = max(0.0, factor)
        return Color(self.r * factor, self.g * factor, self.b * factor)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Color):
            return (self.r, self.g, self.b) == (other.r, other.g, other.b)
        return False

    def __repr__(self) -> str:
        return f"Color(r={self.r}, g={self.g}, b={self.b}, hex='{self.to_hex()}')"


class Gradient:
    """Multi-stop color gradient interpolation."""
    def __init__(self, stops: Sequence[Tuple[float, Color]]):
        if not stops:
            raise ValueError("Gradient requires at least one stop")
        self.stops = sorted(stops, key=lambda s: s[0])

    def sample(self, t: float) -> Color:
        t = max(0.0, min(1.0, t))
        if t <= self.stops[0][0]:
            return self.stops[0][1]
        if t >= self.stops[-1][0]:
            return self.stops[-1][1]

        for i in range(len(self.stops) - 1):
            t0, c0 = self.stops[i]
            t1, c1 = self.stops[i + 1]
            if t0 <= t <= t1:
                local_t = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
                return c0.lerp(c1, local_t)

        return self.stops[-1][1]


# Signature Smoky Velvet Color Palette
# Physically calibrated for URX Core75 Smoky Black translucent casing
SMOKY_PLUM_PURPLE   = Color(255, 0, 254) # Left section: Authentic Smoky Plum Velvet (#FF00FE)
MOLTEN_ANTIQUE_GOLD = Color(255, 52, 0)  # Pure Molten Antique Gold (#FF3400)
DEEP_ANTIQUE_GOLD   = Color(255, 52, 0)  # Alias for backward compatibility
VELVET_MAGENTA      = Color(190, 0, 110) # Accent hue (#BE006E)

MIDNIGHT_PURPLE = Color.from_hex("#30183F")

# Liquid Antique Gold 4-stop palette
CHAMPAGNE_GLOW = Color.from_hex("#FFE6A3")
WARM_GOLD      = Color.from_hex("#E5C477")
ANTIQUE_GOLD    = Color.from_hex("#C49A45")
DEEP_OLD_GOLD  = Color.from_hex("#986B2D")

LIQUID_GOLD_GRADIENT = Gradient([
    (0.00, CHAMPAGNE_GLOW),
    (0.33, WARM_GOLD),
    (0.66, ANTIQUE_GOLD),
    (1.00, DEEP_OLD_GOLD),
])
