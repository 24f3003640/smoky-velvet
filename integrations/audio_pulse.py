"""
PipeWire Audio Beat & Energy Monitor for Linux.
Spawns a low-overhead pw-record monitor stream at 1000Hz mono (only 2KB/sec) to detect musical rhythm.
"""
from __future__ import annotations
import logging
import math
import struct
import subprocess
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class AudioEnergyMonitor:
    def __init__(self, on_beat: Callable[[float], None]):
        self.on_beat = on_beat
        self._thread: Optional[threading.Thread] = None
        self._process: Optional[subprocess.Popen] = None
        self._stop_event = threading.Event()
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> bool:
        if self._is_running:
            return True

        self._stop_event.clear()
        self._is_running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="AudioBeatMonitor")
        self._thread.start()
        logger.info("Audio energy monitor started.")
        return True

    def stop(self) -> None:
        self._stop_event.set()
        self._is_running = False
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
            self._process = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
            self._thread = None
        logger.info("Audio energy monitor stopped.")

    def _monitor_loop(self) -> None:
        cmd = ["pw-record", "--rate=1000", "--channels=1", "--format=s16", "-"]
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )
        except Exception as e:
            logger.warning(f"Failed to launch pw-record for audio monitor: {e}")
            self._is_running = False
            return

        # 32 samples = 32ms at 1000Hz (64 bytes)
        chunk_size = 64
        avg_energy = 0.0
        last_beat_time = 0.0

        while not self._stop_event.is_set():
            try:
                raw_bytes = self._process.stdout.read(chunk_size)
                if not raw_bytes or len(raw_bytes) < chunk_size:
                    time.sleep(0.05)
                    continue

                # Unpack 32 signed 16-bit integers
                samples = struct.unpack("<32h", raw_bytes)
                # Compute RMS amplitude normalized to [0.0, 1.0]
                rms = math.sqrt(sum(s * s for s in samples) / len(samples)) / 32768.0

                # Adaptive EMA beat tracking
                avg_energy = 0.90 * avg_energy + 0.10 * rms

                now = time.monotonic()
                # Beat threshold: instantaneous energy spikes > 1.45x rolling average
                if rms > 0.05 and rms > (avg_energy * 1.45) and (now - last_beat_time) > 0.22:
                    beat_energy = min(1.0, (rms - avg_energy) * 3.5 + 0.3)
                    self.on_beat(beat_energy)
                    last_beat_time = now

            except Exception as e:
                logger.debug(f"Audio monitor read error: {e}")
                break

        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
            self._process = None
