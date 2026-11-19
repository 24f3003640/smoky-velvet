"""
Hardware transport adapter for communicating with OpenRGB SDK / ColorHoster.
Includes auto-reconnection, rate limiting, and dirty-frame buffering.
"""
from __future__ import annotations
import logging
import subprocess
import time
from pathlib import Path
from typing import List, Optional
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor
from core.color import Color

logger = logging.getLogger(__name__)

class OpenRGBDeviceAdapter:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 6742,
        client_name: str = "SmokyVelvet",
        min_frame_interval: float = 0.020 # Max ~50 FPS
    ):
        self.host = host
        self.port = port
        self.client_name = client_name
        self.min_frame_interval = min_frame_interval

        self.client: Optional[OpenRGBClient] = None
        self.device = None
        self.led_count: int = 0
        self._last_send_time: float = 0.0
        self._connected: bool = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self.client is not None

    def connect(self) -> bool:
        """Establish connection to ColorHoster OpenRGB SDK server."""
        try:
            self.client = OpenRGBClient(
                address=self.host,
                port=self.port,
                name=self.client_name
            )
            if not self.client.devices:
                logger.warning("Connected to SDK server but no devices reported.")
                self._connected = False
                return False

            self.device = self.client.devices[0]
            self.led_count = len(self.device.leds)

            # Switch device into Per Key RGB mode
            mode = self.device.modes[0]
            # Bypass openrgb-python validation bug for mode-specific colors
            mode.colors_min = None
            mode.colors_max = None
            mode.colors = None
            self.device.set_mode(mode)

            self._connected = True
            logger.info(f"Connected to '{self.device.name}' with {self.led_count} addressable LEDs.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ColorHoster ({self.host}:{self.port}): {e}")
            self.client = None
            self.device = None
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Gracefully disconnect from the server."""
        try:
            if self.client:
                self.client.disconnect()
        except Exception:
            pass
        finally:
            self.client = None
            self.device = None
            self._connected = False

    def send_frame(self, colors: List[Color], force: bool = False) -> bool:
        """
        Send RGB frame to hardware with rate limiting.
        """
        if not self.is_connected:
            # Attempt reconnect
            if not self.connect():
                return False

        now = time.time()
        time_since_last = now - self._last_send_time
        if not force and time_since_last < self.min_frame_interval:
            # Rate limit exceeded; caller will push on next tick
            return False

        try:
            # Convert internal Color objects to OpenRGB RGBColor
            rgb_colors = [RGBColor(c.r, c.g, c.b) for c in colors]
            self.device.set_colors(rgb_colors, fast=True)
            self._last_send_time = now
            return True
        except Exception as e:
            logger.error(f"Hardware write error: {e}. Marking disconnected.")
            self._connected = False
            return False
