"""
Linux System Telemetry Reader for URX Core75.
Reads real-time CPU usage, CPU temperature, and Memory pressure directly
from /proc and /sys without external dependencies.
"""
from __future__ import annotations
import glob
import logging
import os
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class SystemTelemetry:
    """Lightweight asynchronous hardware telemetry reader."""
    def __init__(self):
        self._prev_cpu_times: Optional[Tuple[int, int]] = None
        self._last_sample_time: float = 0.0
        self.cpu_usage_pct: float = 0.0
        self.cpu_temp_celsius: float = 40.0
        self.memory_usage_pct: float = 0.0

        # Discover primary thermal zone
        self._thermal_file: Optional[str] = self._find_thermal_file()

    def _find_thermal_file(self) -> Optional[str]:
        # Search coretemp / k10temp / thermal_zone
        for p in sorted(glob.glob("/sys/class/hwmon/hwmon*/temp*_input")):
            try:
                with open(p, "r") as f:
                    val = int(f.read().strip())
                if 20000 <= val <= 115000:
                    return p
            except Exception:
                continue

        for p in sorted(glob.glob("/sys/class/thermal/thermal_zone*/temp")):
            try:
                with open(p, "r") as f:
                    val = int(f.read().strip())
                if 20000 <= val <= 115000:
                    return p
            except Exception:
                continue
        return None

    def sample(self) -> Dict[str, float]:
        """Poll current system stats (rate limited to once per 500ms)."""
        now = time.monotonic()
        if now - self._last_sample_time < 0.50:
            return {
                "cpu_usage": self.cpu_usage_pct,
                "cpu_temp": self.cpu_temp_celsius,
                "memory_usage": self.memory_usage_pct,
            }
        self._last_sample_time = now

        # 1. CPU Usage via /proc/stat
        try:
            with open("/proc/stat", "r") as f:
                first_line = f.readline()
            parts = [int(x) for x in first_line.split()[1:8]]
            idle_time = parts[3] + parts[4] # idle + iowait
            total_time = sum(parts)

            if self._prev_cpu_times is not None:
                prev_idle, prev_total = self._prev_cpu_times
                diff_idle = idle_time - prev_idle
                diff_total = total_time - prev_total
                if diff_total > 0:
                    self.cpu_usage_pct = max(0.0, min(100.0, (1.0 - diff_idle / diff_total) * 100.0))

            self._prev_cpu_times = (idle_time, total_time)
        except Exception:
            pass

        # 2. CPU Temperature
        if self._thermal_file:
            try:
                with open(self._thermal_file, "r") as f:
                    raw_temp = int(f.read().strip())
                self.cpu_temp_celsius = max(20.0, min(110.0, raw_temp / 1000.0))
            except Exception:
                pass

        # 3. Memory Usage via /proc/meminfo
        try:
            mem_total = 0
            mem_avail = 0
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        mem_avail = int(line.split()[1])
                    if mem_total > 0 and mem_avail > 0:
                        break
            if mem_total > 0:
                self.memory_usage_pct = max(0.0, min(100.0, (1.0 - mem_avail / mem_total) * 100.0))
        except Exception:
            pass

        return {
            "cpu_usage": self.cpu_usage_pct,
            "cpu_temp": self.cpu_temp_celsius,
            "memory_usage": self.memory_usage_pct,
        }
