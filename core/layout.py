"""
Keyboard layout representation, LED geometry, and physical coordinate calculation.
"""
from __future__ import annotations
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

@dataclass(frozen=True)
class KeyDefinition:
    led_index: int
    matrix_coord: str  # e.g. "0,0"
    x: float          # Center X coordinate in keyboard units
    y: float          # Center Y coordinate in keyboard units
    width: float      # Key width in units
    height: float     # Key height in units
    name: str         # Human-readable key name or label

class KeyboardLayout:
    def __init__(self, keys: Dict[int, KeyDefinition]):
        self.keys = keys
        self.led_count = len(keys)
        # Precompute distance cache between all LED pairs
        self._dist_cache: Dict[Tuple[int, int], float] = {}
        for i, k1 in keys.items():
            for j, k2 in keys.items():
                d = math.hypot(k1.x - k2.x, k1.y - k2.y)
                self._dist_cache[(i, j)] = d

    def distance(self, led_a: int, led_b: int) -> float:
        return self._dist_cache.get((led_a, led_b), 0.0)

    def get_key(self, led_index: int) -> Optional[KeyDefinition]:
        return self.keys.get(led_index)

    @classmethod
    def load_from_via_json(cls, json_path: str | Path) -> KeyboardLayout:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        keymap = data['layouts']['keymap']
        keys: Dict[int, KeyDefinition] = {}

        # Standard 75% key names for URX Core75
        key_names = {
            0: "Escape", 1: "F1", 2: "F2", 3: "F3", 4: "F4", 5: "F5", 6: "F6",
            7: "F7", 8: "F8", 9: "F9", 10: "F10", 11: "F11", 12: "F12", 13: "Delete",
            14: "`", 15: "1", 16: "2", 17: "3", 18: "4", 19: "5", 20: "6",
            21: "7", 22: "8", 23: "9", 24: "0", 25: "-", 26: "=", 27: "Backspace", 28: "Home",
            29: "Tab", 30: "Q", 31: "W", 32: "E", 33: "R", 34: "T", 35: "Y",
            36: "U", 37: "I", 38: "O", 39: "P", 40: "[", 41: "]", 42: "\\", 43: "End",
            44: "Caps Lock", 45: "A", 46: "S", 47: "D", 48: "F", 49: "G", 50: "H",
            51: "J", 52: "K", 53: "L", 54: ";", 55: "'", 56: "Enter", 57: "Page Up",
            58: "Left Shift", 59: "Z", 60: "X", 61: "C", 62: "V", 63: "B", 64: "N",
            65: "M", 66: ",", 67: ".", 68: "/", 69: "Right Shift", 70: "Up Arrow", 71: "Page Down",
            72: "Left Ctrl", 73: "Left Win", 74: "Left Alt", 75: "Space",
            76: "Right Alt", 77: "Fn", 78: "Left Arrow", 79: "Down Arrow", 80: "Right Arrow"
        }

        current_y = 0.0
        for row in keymap:
            current_x = 0.0
            current_w = 1.0
            current_h = 1.0
            row_y = current_y

            for item in row:
                if isinstance(item, dict):
                    if 'y' in item:
                        row_y += item['y']
                    if 'x' in item:
                        current_x += item['x']
                    if 'w' in item:
                        current_w = item['w']
                    if 'h' in item:
                        current_h = item['h']
                elif isinstance(item, str):
                    parts = item.split('\n')
                    matrix = parts[0]
                    led_tag = parts[1] if len(parts) > 1 and parts[1].startswith('l') else None

                    cx = current_x + current_w / 2.0
                    cy = row_y + current_h / 2.0

                    if led_tag:
                        led_idx = int(led_tag[1:])
                        name = key_names.get(led_idx, f"Key_{led_idx}")
                        keys[led_idx] = KeyDefinition(
                            led_index=led_idx,
                            matrix_coord=matrix,
                            x=round(cx, 3),
                            y=round(cy, 3),
                            width=round(current_w, 2),
                            height=round(current_h, 2),
                            name=name
                        )

                    current_x += current_w
                    current_w = 1.0
                    current_h = 1.0

            current_y += 1.0

        return cls(keys)

# Predefined Linux evdev scancode name to Core75 LED index
EVDEV_KEY_TO_LED: Dict[str, int] = {
    "KEY_ESC": 0,
    "KEY_F1": 1, "KEY_F2": 2, "KEY_F3": 3, "KEY_F4": 4,
    "KEY_F5": 5, "KEY_F6": 6, "KEY_F7": 7, "KEY_F8": 8,
    "KEY_F9": 9, "KEY_F10": 10, "KEY_F11": 11, "KEY_F12": 12,
    "KEY_DELETE": 13,
    "KEY_GRAVE": 14,
    "KEY_1": 15, "KEY_2": 16, "KEY_3": 17, "KEY_4": 18, "KEY_5": 19,
    "KEY_6": 20, "KEY_7": 21, "KEY_8": 22, "KEY_9": 23, "KEY_0": 24,
    "KEY_MINUS": 25, "KEY_EQUAL": 26, "KEY_BACKSPACE": 27, "KEY_HOME": 28,
    "KEY_TAB": 29,
    "KEY_Q": 30, "KEY_W": 31, "KEY_E": 32, "KEY_R": 33, "KEY_T": 34,
    "KEY_Y": 35, "KEY_U": 36, "KEY_I": 37, "KEY_O": 38, "KEY_P": 39,
    "KEY_LEFTBRACE": 40, "KEY_RIGHTBRACE": 41, "KEY_BACKSLASH": 42, "KEY_END": 43,
    "KEY_CAPSLOCK": 44,
    "KEY_A": 45, "KEY_S": 46, "KEY_D": 47, "KEY_F": 48, "KEY_G": 49,
    "KEY_H": 50, "KEY_J": 51, "KEY_K": 52, "KEY_L": 53,
    "KEY_SEMICOLON": 54, "KEY_APOSTROPHE": 55, "KEY_ENTER": 56, "KEY_PAGEUP": 57,
    "KEY_LEFTSHIFT": 58,
    "KEY_Z": 59, "KEY_X": 60, "KEY_C": 61, "KEY_V": 62, "KEY_B": 63,
    "KEY_N": 64, "KEY_M": 65, "KEY_COMMA": 66, "KEY_DOT": 67, "KEY_SLASH": 68,
    "KEY_RIGHTSHIFT": 69, "KEY_UP": 70, "KEY_PAGEDOWN": 71,
    "KEY_LEFTCTRL": 72, "KEY_LEFTMETA": 73, "KEY_LEFTALT": 74,
    "KEY_SPACE": 75,
    "KEY_RIGHTALT": 76, "KEY_COMPOSE": 77, "KEY_FN": 77,
    "KEY_LEFT": 78, "KEY_DOWN": 79, "KEY_RIGHT": 80
}
