"""
PipeWire Audio Beat, Melodic Onset & Dynamic Energy Monitor for Linux.
Connects directly to @DEFAULT_SINK@.monitor via parec (1000Hz mono, 2KB/sec).
Adaptive dynamic range auto-calibrates to all volume levels and musical genres:
Classical piano, orchestral symphonies, jazz, ambient, and EDM beats.
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
    def __init__(
        self,
        on_beat: Callable[[float], None],
        on_energy: Optional[Callable[[float], None]] = None
    ):
        self.on_beat = on_beat
        self.on_energy = on_energy
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
        logger.info("Adaptive audio energy monitor started on @DEFAULT_SINK@.monitor.")
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
        # Use parec with @DEFAULT_SINK@.monitor to record exactly what user is hearing
        cmd = ["parec", "-d", "@DEFAULT_SINK@.monitor", "--rate=1000", "--channels=1", "--format=s16le"]
        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=0
            )
        except Exception as e:
            logger.warning(f"Failed to launch parec for audio monitor: {e}")
            self._is_running = False
            return

        # 32 samples = 32ms at 1000Hz (64 bytes)
        chunk_size = 64
        noise_floor = 0.003
        peak_rms = 0.025
        smooth_energy = 0.0
        last_rms = 0.0
        last_accent_time = 0.0

        while not self._stop_event.is_set():
            try:
                raw_bytes = self._process.stdout.read(chunk_size)
                if not raw_bytes or len(raw_bytes) < chunk_size:
                    time.sleep(0.04)
                    continue

                # Unpack 32 signed 16-bit integers
                samples = struct.unpack("<32h", raw_bytes)
                # Compute RMS amplitude normalized to [0.0, 1.0]
                rms = math.sqrt(sum(s * s for s in samples) / len(samples)) / 32768.0

                now = time.monotonic()

                # Dynamic Auto-Calibration:
                # Slowly track ambient noise floor and signal ceiling
                noise_floor = min(noise_floor * 0.999 + 0.001 * rms, rms)
                peak_rms = max(peak_rms * 0.996, rms, noise_floor + 0.008)
                dynamic_range = max(0.006, peak_rms - noise_floor)

                # 1. Continuous Loudness Envelope (Orchestral / Piano Crescendo Swell)
                instant_loudness = max(0.0, min(1.0, (rms - noise_floor) / dynamic_range))
                smooth_energy = 0.80 * smooth_energy + 0.20 * instant_loudness
                if self.on_energy:
                    self.on_energy(smooth_energy)

                # 2. Melodic Note Strike & Transient Onset Detection (Piano/Violin/Beats)
                delta = rms - last_rms
                last_rms = rms

                # Relative contrast trigger: works at any volume level
                if delta > (dynamic_range * 0.16) and (now - last_accent_time) > 0.16:
                    accent_intensity = min(1.0, (delta / dynamic_range) * 2.5 + 0.35)
                    self.on_beat(accent_intensity)
                    last_accent_time = now

            except Exception as e:
                logger.debug(f"Audio monitor read error: {e}")
                break

        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass
            self._process = None
