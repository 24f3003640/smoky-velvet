"""
Windows input listener for URX Core75.
Captures keydown events and multimedia volume actions across Windows using pynput,
and queries Caps Lock hardware state directly using the Win32 GetKeyState API.
PRIVACY GUARANTEE: Zero text logging or buffering. Only transmits physical LED index and timestamp.
"""
from __future__ import annotations
import ctypes
import logging
import threading
import time
from typing import Optional
from core.layout import EVDEV_KEY_TO_LED
from input.listener import InputListener, KeyCallback, KnobCallback, CapsLockCallback

logger = logging.getLogger(__name__)

# Map pynput special key names to standard EVDEV_KEY_TO_LED names
SPECIAL_KEY_MAP = {
    "esc": "KEY_ESC",
    "f1": "KEY_F1", "f2": "KEY_F2", "f3": "KEY_F3", "f4": "KEY_F4",
    "f5": "KEY_F5", "f6": "KEY_F6", "f7": "KEY_F7", "f8": "KEY_F8",
    "f9": "KEY_F9", "f10": "KEY_F10", "f11": "KEY_F11", "f12": "KEY_F12",
    "delete": "KEY_DELETE",
    "backspace": "KEY_BACKSPACE",
    "tab": "KEY_TAB",
    "caps_lock": "KEY_CAPSLOCK",
    "enter": "KEY_ENTER",
    "shift": "KEY_LEFTSHIFT", "shift_l": "KEY_LEFTSHIFT", "shift_r": "KEY_RIGHTSHIFT",
    "ctrl": "KEY_LEFTCTRL", "ctrl_l": "KEY_LEFTCTRL", "ctrl_r": "KEY_RIGHTCTRL",
    "alt": "KEY_LEFTALT", "alt_l": "KEY_LEFTALT", "alt_r": "KEY_RIGHTALT", "alt_gr": "KEY_RIGHTALT",
    "cmd": "KEY_LEFTMETA", "cmd_l": "KEY_LEFTMETA", "cmd_r": "KEY_RIGHTMETA",
    "space": "KEY_SPACE",
    "up": "KEY_UP", "down": "KEY_DOWN", "left": "KEY_LEFT", "right": "KEY_RIGHT",
    "home": "KEY_HOME", "end": "KEY_END",
    "page_up": "KEY_PAGEUP", "page_down": "KEY_PAGEDOWN",
}

# Map punctuation / symbols to standard names
CHAR_SYMBOL_MAP = {
    "`": "KEY_GRAVE", "~": "KEY_GRAVE",
    "-": "KEY_MINUS", "_": "KEY_MINUS",
    "=": "KEY_EQUAL", "+": "KEY_EQUAL",
    "[": "KEY_LEFTBRACE", "{": "KEY_LEFTBRACE",
    "]": "KEY_RIGHTBRACE", "}": "KEY_RIGHTBRACE",
    "\\": "KEY_BACKSLASH", "|": "KEY_BACKSLASH",
    ";": "KEY_SEMICOLON", ":": "KEY_SEMICOLON",
    "'": "KEY_APOSTROPHE", '"': "KEY_APOSTROPHE",
    ",": "KEY_COMMA", "<": "KEY_COMMA",
    ".": "KEY_DOT", ">": "KEY_DOT",
    "/": "KEY_SLASH", "?": "KEY_SLASH",
}

def query_windows_caps_lock() -> bool:
    """Returns True if Caps Lock is physically toggled ON on Windows."""
    try:
        # VK_CAPITAL = 0x14. Low-order bit is set if the key is toggled on.
        return bool(ctypes.windll.user32.GetKeyState(0x14) & 1)
    except Exception:
        return False

class WindowsInputListener(InputListener):
    """
    Windows input listener using pynput for global keystrokes and Win32 API for Caps Lock.
    """
    def __init__(self):
        super().__init__()
        self._listener = None
        self._is_running = False
        self._stop_event = threading.Event()
        self._supervisor_thread: Optional[threading.Thread] = None
        self._last_caps_state: Optional[bool] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def _sync_caps_lock(self) -> None:
        """Query Windows Caps Lock state and notify callback if state changed."""
        is_caps = query_windows_caps_lock()
        if is_caps != self._last_caps_state:
            self._last_caps_state = is_caps
            if self._caps_lock_callback is not None:
                try:
                    self._caps_lock_callback(is_caps)
                except Exception as e:
                    logger.debug(f"Caps lock callback error: {e}")

    def _supervisor_loop(self) -> None:
        """Periodic background check for Windows Caps Lock state."""
        while not self._stop_event.wait(timeout=1.0):
            self._sync_caps_lock()

    def _resolve_key_name(self, key) -> Optional[str]:
        """Translates a pynput key object into standard EVDEV_KEY_TO_LED identifier."""
        # 1. Alphanumeric / symbol character
        if hasattr(key, "char") and key.char:
            ch = key.char.lower()
            if ch.isalnum():
                return f"KEY_{ch.upper()}"
            if ch in CHAR_SYMBOL_MAP:
                return CHAR_SYMBOL_MAP[ch]

        # 2. Named special key (Key.space, Key.enter, etc.)
        if hasattr(key, "name") and key.name:
            k_name = key.name.lower()
            return SPECIAL_KEY_MAP.get(k_name)

        # 3. Fallback string representation
        s = str(key).replace("Key.", "").lower()
        return SPECIAL_KEY_MAP.get(s)

    def _on_press(self, key):
        now = time.monotonic()

        # Check for volume knob / multimedia keys
        if hasattr(key, "name") and key.name:
            k_name = key.name.lower()
            if k_name == "media_volume_up":
                if self._knob_callback is not None:
                    self._knob_callback("volume_up", now)
                return
            elif k_name == "media_volume_down":
                if self._knob_callback is not None:
                    self._knob_callback("volume_down", now)
                return
            elif k_name == "media_volume_mute":
                if self._knob_callback is not None:
                    self._knob_callback("mute_click", now)
                return
            elif k_name == "media_play_pause":
                if self._knob_callback is not None:
                    self._knob_callback("media_play_pause", now)
                return

        # Check for Caps Lock toggle
        if hasattr(key, "name") and key.name == "caps_lock":
            # Small 30ms sleep allows OS state to settle before reading
            threading.Thread(target=lambda: (time.sleep(0.03), self._sync_caps_lock()), daemon=True).start()

        key_name = self._resolve_key_name(key)
        if not key_name:
            return

        led_idx = EVDEV_KEY_TO_LED.get(key_name)
        if led_idx is not None and self._callback is not None:
            self._callback(led_idx, now)

    def start(self) -> None:
        """Start global keyboard hook and Caps Lock supervisor."""
        if self._is_running:
            return

        try:
            from pynput import keyboard
        except ImportError:
            logger.error("The 'pynput' library is required on Windows. Install via: pip install pynput")
            return

        self._stop_event.clear()
        self._is_running = True

        # Initial Caps Lock sync
        self._sync_caps_lock()

        # Start pynput listener
        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True
        self._listener.start()

        # Start supervisor thread
        self._supervisor_thread = threading.Thread(
            target=self._supervisor_loop,
            daemon=True,
            name="WindowsInputSupervisor"
        )
        self._supervisor_thread.start()
        logger.info("Windows keyboard listener started via pynput.")

    def stop(self) -> None:
        """Stop keyboard hook and supervisor."""
        self._stop_event.set()
        self._is_running = False

        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

        if self._supervisor_thread and self._supervisor_thread.is_alive():
            self._supervisor_thread.join(timeout=0.5)
            self._supervisor_thread = None

        logger.info("Windows keyboard listener stopped.")
