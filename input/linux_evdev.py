"""
Linux evdev input listener for URX Core75.
Captures keydown events and rotary encoder volume knob actions across all URX input endpoints concurrently using native read_loop.
PRIVACY GUARANTEE: Zero text logging or buffering. Only transmits physical LED index and timestamp.
"""
from __future__ import annotations
import glob
import json
import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Optional
import evdev
from core.layout import EVDEV_KEY_TO_LED
from input.listener import InputListener, KeyCallback, KnobCallback

logger = logging.getLogger(__name__)

class LinuxEvdevListener(InputListener):
    def __init__(self, device_path: Optional[str] = None):
        super().__init__()
        self.device_path = device_path
        self._devices: List[evdev.InputDevice] = []
        self._threads: List[threading.Thread] = []
        self._supervisor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False
        self._last_abs_vol: Optional[int] = None
        self._active_modifiers = set()
        self._modifier_lock = threading.Lock()
        self._caps_timer: Optional[threading.Timer] = None
        self._caps_timer_lock = threading.Lock()
        self._last_synced_caps_state: Optional[bool] = None

    def _resolve_knob_turn(self, direction: str) -> str:
        """Resolve knob turn action based on active modifier keys."""
        with self._modifier_lock:
            if 'super' in self._active_modifiers:
                return "media_next" if direction == "up" else "media_prev"
            elif 'ctrl' in self._active_modifiers or 'alt' in self._active_modifiers:
                return "workspace_next" if direction == "up" else "workspace_prev"
            elif 'shift' in self._active_modifiers:
                return "led_brightness_up" if direction == "up" else "led_brightness_down"
            return "volume_up" if direction == "up" else "volume_down"

    @property
    def is_running(self) -> bool:
        return self._is_running

    def _find_device_paths(self) -> List[str]:
        if self.device_path and Path(self.device_path).exists():
            return [self.device_path]

        paths: List[str] = []
        # Check by-id symlinks for all URX event devices (excluding only joystick)
        matches = sorted(glob.glob("/dev/input/by-id/*URX*event*"))
        by_id_matches = [p for p in matches if "joystick" not in p]
        if by_id_matches:
            paths.extend(by_id_matches)

        if not paths:
            # Fallback scan across all event devices
            for dev_path in evdev.list_devices():
                try:
                    dev = evdev.InputDevice(dev_path)
                    if "URX" in dev.name:
                        caps = dev.capabilities()
                        if evdev.ecodes.EV_KEY in caps:
                            keys = caps[evdev.ecodes.EV_KEY]
                            if (evdev.ecodes.KEY_SPACE in keys and evdev.ecodes.KEY_A in keys) or \
                               (evdev.ecodes.KEY_VOLUMEUP in keys or evdev.ecodes.KEY_MUTE in keys):
                                paths.append(dev_path)
                except Exception:
                    pass

        return paths

    def _attach_devices(self, target_paths: List[str]) -> bool:
        """Attach to input device nodes and launch reader threads."""
        for dev in self._devices:
            try:
                dev.close()
            except Exception:
                pass
        self._devices.clear()
        self._threads.clear()
        self._last_synced_caps_state = None

        for p in target_paths:
            try:
                dev = evdev.InputDevice(p)
                self._devices.append(dev)
                logger.info(f"Listening for input on: {dev.path} ({dev.name})")
            except Exception as e:
                logger.warning(f"Failed to open evdev device {p}: {e}")

        if not self._devices:
            return False

        for dev in self._devices:
            t = threading.Thread(
                target=self._read_device_loop,
                args=(dev,),
                daemon=True,
                name=f"EvdevReader-{dev.path.split('/')[-1]}"
            )
            self._threads.append(t)
            t.start()
        return True

    def _schedule_caps_sync(self, delay: float = 0.08) -> None:
        """Schedules a debounced Caps Lock synchronization after physical key settling."""
        with self._caps_timer_lock:
            if self._caps_timer is not None:
                try:
                    self._caps_timer.cancel()
                except Exception:
                    pass
            self._caps_timer = threading.Timer(delay, self._sync_caps_lock)
            self._caps_timer.daemon = True
            self._caps_timer.start()

            # Schedule follow-up check to guarantee synchronization after compositor transitions
            followup = threading.Timer(delay + 0.15, self._sync_caps_lock)
            followup.daemon = True
            followup.start()

    def _query_caps_state(self) -> bool:
        """Queries current Caps Lock lock-state from Hyprland devices, with sysfs fallback."""
        try:
            res = subprocess.run(["hyprctl", "devices", "-j"], capture_output=True, text=True, timeout=0.8)
            data = json.loads(res.stdout)
            for kb in data.get("keyboards", []):
                name = kb.get("name", "").lower()
                caps = kb.get("capsLock", False)
                if "urx" in name and caps:
                    return True
            return False
        except Exception as e:
            logger.debug(f"Hyprctl Caps Lock check error: {e}")
            for p in glob.glob("/sys/class/leds/*capslock*/brightness"):
                try:
                    with open(p, "r") as f:
                        if f.read().strip() == "1":
                            return True
                except Exception:
                    pass
            return False

    def _sync_caps_lock(self, force: bool = False) -> None:
        """
        Synchronizes hardware Caps Lock LED state across all URX Core75 interfaces.
        Fixes the Linux Wayland/Hyprland dual-interface desynchronization quirk.
        NOTE: Never injects synthetic keystrokes. Only sets output LED state via dev.set_led.
        """
        caps_on = self._query_caps_state()

        if force or caps_on != self._last_synced_caps_state:
            target_val = 1 if caps_on else 0
            for dev in self._devices:
                try:
                    if evdev.ecodes.EV_LED in dev.capabilities():
                        dev.set_led(evdev.ecodes.LED_CAPSL, target_val)
                except Exception:
                    pass
            self._last_synced_caps_state = caps_on
            if self._caps_lock_callback is not None:
                try:
                    self._caps_lock_callback(caps_on)
                except Exception as e:
                    logger.debug(f"Caps lock callback error: {e}")

    def _supervisor_loop(self) -> None:
        """Monitors evdev reader threads. If keyboard resets or reconnects, reattaches automatically."""
        while not self._stop_event.wait(timeout=2.0):
            alive_threads = [t for t in self._threads if t.is_alive()]
            if not alive_threads:
                paths = self._find_device_paths()
                if paths:
                    logger.info("Auto-reconnecting to URX Core75 input devices...")
                    self._attach_devices(paths)
            self._sync_caps_lock()

    def start(self) -> None:
        if self._is_running:
            return

        self._stop_event.clear()
        self._is_running = True

        target_paths = self._find_device_paths()
        if target_paths:
            self._attach_devices(target_paths)
            self._sync_caps_lock(force=True)
        else:
            logger.warning("No URX Core75 input devices found on startup. Supervisor will auto-detect on connection.")

        self._supervisor_thread = threading.Thread(
            target=self._supervisor_loop,
            daemon=True,
            name="EvdevSupervisor"
        )
        self._supervisor_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._is_running = False

        with self._caps_timer_lock:
            if self._caps_timer is not None:
                try:
                    self._caps_timer.cancel()
                except Exception:
                    pass
                self._caps_timer = None

        if self._supervisor_thread and self._supervisor_thread.is_alive():
            self._supervisor_thread.join(timeout=0.5)
            self._supervisor_thread = None

        for dev in self._devices:
            try:
                dev.close()
            except Exception:
                pass
        self._devices.clear()

        for t in self._threads:
            if t.is_alive():
                t.join(timeout=0.5)
        self._threads.clear()

    def _read_device_loop(self, dev: evdev.InputDevice) -> None:
        logger.info(f"Started evdev read loop for {dev.path} ({dev.name})")
        mute_press_time: Optional[float] = None
        last_mute_release_time: float = 0.0

        try:
            for event in dev.read_loop():
                if self._stop_event.is_set():
                    break

                now = time.monotonic()

                # 1. Rotary encoder dial turn (EV_REL)
                if event.type == evdev.ecodes.EV_REL:
                    rel_codes = [evdev.ecodes.REL_HWHEEL, evdev.ecodes.REL_WHEEL]
                    if hasattr(evdev.ecodes, 'REL_HWHEEL_HI_RES'):
                        rel_codes.append(evdev.ecodes.REL_HWHEEL_HI_RES)
                    if hasattr(evdev.ecodes, 'REL_WHEEL_HI_RES'):
                        rel_codes.append(evdev.ecodes.REL_WHEEL_HI_RES)
                    if event.code in rel_codes:
                        direction = "up" if event.value > 0 else "down"
                        action = self._resolve_knob_turn(direction)
                        if self._knob_callback is not None:
                            self._knob_callback(action, now)

                # 2. Absolute volume axis (EV_ABS)
                elif event.type == evdev.ecodes.EV_ABS:
                    if event.code == evdev.ecodes.ABS_VOLUME:
                        if self._last_abs_vol is not None:
                            diff = event.value - self._last_abs_vol
                            if diff != 0:
                                direction = "up" if diff > 0 else "down"
                                action = self._resolve_knob_turn(direction)
                                if self._knob_callback is not None:
                                    self._knob_callback(action, now)
                        self._last_abs_vol = event.value

                # 3. Key events (EV_KEY)
                elif event.type == evdev.ecodes.EV_KEY:
                    key_code = event.code

                    # If Caps Lock pressed or released, schedule debounced sync (waits for key settling)
                    if key_code == evdev.ecodes.KEY_CAPSLOCK:
                        self._schedule_caps_sync(0.08)

                    # Track active modifiers
                    mod_map = {
                        evdev.ecodes.KEY_LEFTMETA: 'super',
                        evdev.ecodes.KEY_RIGHTMETA: 'super',
                        evdev.ecodes.KEY_LEFTCTRL: 'ctrl',
                        evdev.ecodes.KEY_RIGHTCTRL: 'ctrl',
                        evdev.ecodes.KEY_LEFTALT: 'alt',
                        evdev.ecodes.KEY_RIGHTALT: 'alt',
                        evdev.ecodes.KEY_LEFTSHIFT: 'shift',
                        evdev.ecodes.KEY_RIGHTSHIFT: 'shift',
                    }
                    if key_code in mod_map:
                        mod = mod_map[key_code]
                        with self._modifier_lock:
                            if event.value in (1, 2):
                                self._active_modifiers.add(mod)
                            elif event.value == 0:
                                self._active_modifiers.discard(mod)

                    # Knob Volume Up
                    if key_code == evdev.ecodes.KEY_VOLUMEUP:
                        if event.value in (1, 2) and self._knob_callback is not None:
                            action = self._resolve_knob_turn("up")
                            self._knob_callback(action, now)

                    # Knob Volume Down
                    elif key_code == evdev.ecodes.KEY_VOLUMEDOWN:
                        if event.value in (1, 2) and self._knob_callback is not None:
                            action = self._resolve_knob_turn("down")
                            self._knob_callback(action, now)

                    # Knob Mute / Mode Switch Click
                    elif key_code == evdev.ecodes.KEY_MUTE:
                        if event.value == 1:
                            mute_press_time = now
                        elif event.value == 0:
                            with self._modifier_lock:
                                has_ctrl_or_alt = ('ctrl' in self._active_modifiers or 'alt' in self._active_modifiers)
                            if has_ctrl_or_alt:
                                if self._knob_callback is not None:
                                    self._knob_callback("media_play_pause", now)
                            elif mute_press_time is not None:
                                duration = now - mute_press_time
                                mute_press_time = None
                                if duration >= 0.6:
                                    # Long press (>0.6s) toggles hardware/software mode
                                    if self._knob_callback is not None:
                                        self._knob_callback("knob_long_press", now)
                                else:
                                    if (now - last_mute_release_time) < 0.35:
                                        # Double click toggles hardware/software mode
                                        if self._knob_callback is not None:
                                            self._knob_callback("knob_double_click", now)
                                    else:
                                        # Standard short mute click
                                        if self._knob_callback is not None:
                                            self._knob_callback("mute_click", now)
                            last_mute_release_time = now

                    # Standard keypress down (value == 1)
                    elif event.value == 1:
                        try:
                            key_name = evdev.ecodes.KEY[key_code]
                            if isinstance(key_name, list):
                                key_name = key_name[0]
                        except (KeyError, IndexError):
                            continue

                        led_idx = EVDEV_KEY_TO_LED.get(key_name)
                        if led_idx is not None and self._callback is not None:
                            self._callback(led_idx, now)
        except Exception as e:
            if not self._stop_event.is_set():
                logger.error(f"Error in evdev read loop for {dev.path}: {e}")
        finally:
            logger.info(f"Evdev read loop terminated for {dev.path}")
