"""
Linux evdev input listener for URX Core75.
Captures keydown events and rotary encoder volume knob actions across all URX input endpoints concurrently using native read_loop.
PRIVACY GUARANTEE: Zero text logging or buffering. Only transmits physical LED index and timestamp.
"""
from __future__ import annotations
import glob
import logging
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
        self._stop_event = threading.Event()
        self._is_running = False
        self._last_abs_vol: Optional[int] = None

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

    def start(self) -> None:
        if self._is_running:
            return

        target_paths = self._find_device_paths()
        if not target_paths:
            logger.error("Could not find any URX Core75 keyboard device nodes.")
            return

        self._devices.clear()
        for p in target_paths:
            try:
                dev = evdev.InputDevice(p)
                self._devices.append(dev)
                logger.info(f"Listening for input on: {dev.path} ({dev.name})")
            except Exception as e:
                logger.error(f"Failed to open evdev device {p}: {e}")

        if not self._devices:
            return

        self._stop_event.clear()
        self._is_running = True
        self._threads.clear()

        # Dedicated reader thread per input endpoint
        for dev in self._devices:
            t = threading.Thread(
                target=self._read_device_loop,
                args=(dev,),
                daemon=True,
                name=f"EvdevReader-{dev.path.split('/')[-1]}"
            )
            self._threads.append(t)
            t.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._is_running = False

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
                        action = "volume_up" if event.value > 0 else "volume_down"
                        if self._knob_callback is not None:
                            self._knob_callback(action, now)

                # 2. Absolute volume axis (EV_ABS)
                elif event.type == evdev.ecodes.EV_ABS:
                    if event.code == evdev.ecodes.ABS_VOLUME:
                        if self._last_abs_vol is not None:
                            diff = event.value - self._last_abs_vol
                            if diff != 0:
                                action = "volume_up" if diff > 0 else "volume_down"
                                if self._knob_callback is not None:
                                    self._knob_callback(action, now)
                        self._last_abs_vol = event.value

                # 3. Key events (EV_KEY)
                elif event.type == evdev.ecodes.EV_KEY:
                    key_code = event.code

                    # Knob Volume Up
                    if key_code == evdev.ecodes.KEY_VOLUMEUP:
                        if event.value in (1, 2) and self._knob_callback is not None:
                            self._knob_callback("volume_up", now)

                    # Knob Volume Down
                    elif key_code == evdev.ecodes.KEY_VOLUMEDOWN:
                        if event.value in (1, 2) and self._knob_callback is not None:
                            self._knob_callback("volume_down", now)

                    # Knob Mute / Mode Switch Click
                    elif key_code == evdev.ecodes.KEY_MUTE:
                        if event.value == 1:
                            mute_press_time = now
                        elif event.value == 0:
                            if mute_press_time is not None:
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
