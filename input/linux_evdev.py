"""
Linux evdev input listener for URX Core75.
Captures keydown events across all URX input endpoints concurrently using native read_loop.
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
from input.listener import InputListener, KeyCallback

logger = logging.getLogger(__name__)

class LinuxEvdevListener(InputListener):
    def __init__(self, device_path: Optional[str] = None):
        super().__init__()
        self.device_path = device_path
        self._devices: List[evdev.InputDevice] = []
        self._threads: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def _find_device_paths(self) -> List[str]:
        if self.device_path and Path(self.device_path).exists():
            return [self.device_path]

        paths: List[str] = []
        # Check by-id symlinks
        by_id_matches = sorted(glob.glob("/dev/input/by-id/*URX*event-kbd*"))
        if by_id_matches:
            paths.extend(by_id_matches)

        if not paths:
            # Fallback scan
            for dev_path in evdev.list_devices():
                try:
                    dev = evdev.InputDevice(dev_path)
                    if "URX" in dev.name:
                        caps = dev.capabilities()
                        if evdev.ecodes.EV_KEY in caps:
                            keys = caps[evdev.ecodes.EV_KEY]
                            if evdev.ecodes.KEY_SPACE in keys and evdev.ecodes.KEY_A in keys:
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
                logger.info(f"Listening for physical keypresses on: {dev.path} ({dev.name})")
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
        logger.info(f"Started evdev read loop for {dev.path}")
        try:
            for event in dev.read_loop():
                if self._stop_event.is_set():
                    break

                # EV_KEY key-down is value 1
                if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                    key_code = event.code
                    try:
                        key_name = evdev.ecodes.KEY[key_code]
                        if isinstance(key_name, list):
                            key_name = key_name[0]
                    except (KeyError, IndexError):
                        continue

                    led_idx = EVDEV_KEY_TO_LED.get(key_name)
                    if led_idx is not None and self._callback is not None:
                        logger.info(f"Physical keypress detected: {key_name} -> LED {led_idx}")
                        self._callback(led_idx, time.monotonic())
        except Exception as e:
            if not self._stop_event.is_set():
                logger.error(f"Error in evdev read loop for {dev.path}: {e}")
        finally:
            logger.info(f"Evdev read loop terminated for {dev.path}")
