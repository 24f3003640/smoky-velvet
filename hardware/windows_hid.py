"""
Hardware transport adapter for communicating directly with URX Core75 on Windows
via Raw HID (SignalRGB protocol extension) using hidapi.
"""
from __future__ import annotations
import logging
import time
from typing import List, Optional
from core.color import Color

logger = logging.getLogger(__name__)

# Protocol Command Constants (Identical to Linux hardware protocol)
CMD_SIGNALRGB_ENABLE   = 0x25
CMD_SIGNALRGB_DISABLE  = 0x26
CMD_SIGNALRGB_STREAM   = 0x24
CMD_VIA_CUSTOM_SET_VAL = 0x07

URX_VID = 0x36B0
URX_PID = 0x3130
SIGNALRGB_INTERFACE_NUM = 1
MAX_LEDS_PER_PACKET = 9
PACKET_SIZE = 32

class DeviceInfo:
    def __init__(self, name: str = "URX Core75 (Windows HID)"):
        self.name = name

class WindowsSignalRGBAdapter:
    """
    Direct Raw HID device adapter for URX Core75 on Windows using hidapi.
    Streams per-key RGB frames directly to the keyboard hardware.
    """
    def __init__(
        self,
        device_path: Optional[str] = None,
        led_count: int = 82,
        min_frame_interval: float = 0.033  # ~30 FPS
    ):
        self.device_path = device_path
        self.led_count = led_count
        self.min_frame_interval = min_frame_interval
        self._dev = None
        self._connected = False
        self._paused = False
        self._last_send_time = 0.0
        self.device = DeviceInfo()

    @property
    def is_connected(self) -> bool:
        return self._connected and self._dev is not None

    @property
    def is_paused(self) -> bool:
        return self._paused

    def connect(self) -> bool:
        """Connect to URX Core75 Raw HID endpoint and enable SignalRGB stream mode."""
        if self.is_connected:
            return True

        try:
            import hid
        except ImportError:
            logger.error("The 'hidapi' library is required on Windows. Install via: pip install hidapi")
            self._connected = False
            return False

        try:
            target_path = self.device_path
            if not target_path:
                # Enumerate all URX Core75 interfaces to find Interface 1
                for dev_info in hid.enumerate(URX_VID, URX_PID):
                    intf = dev_info.get("interface_number")
                    usage_page = dev_info.get("usage_page")
                    # Interface 1 or VIA/SignalRGB Usage Page 0xFFA0
                    if intf == SIGNALRGB_INTERFACE_NUM or usage_page == 0xFFA0:
                        target_path = dev_info.get("path")
                        break

            self._dev = hid.device()
            if target_path:
                self._dev.open_path(target_path)
            else:
                self._dev.open(URX_VID, URX_PID)

            self._dev.set_nonblocking(True)

            # On Windows hidapi, write expects Report ID as byte 0 (0x00 for unnumbered reports)
            enable_pkt = bytes([0x00, CMD_SIGNALRGB_ENABLE] + [0x00] * (PACKET_SIZE - 1))
            try:
                self._dev.write(enable_pkt)
            except Exception:
                # Fallback if device driver strips report ID
                self._dev.write(enable_pkt[1:])

            time.sleep(0.02)
            self._connected = True
            logger.info("Connected to URX Core75 on Windows via hidapi.")
            return True
        except Exception as e:
            logger.error(f"Failed to open URX Core75 on Windows: {e}")
            self._connected = False
            if self._dev is not None:
                try:
                    self._dev.close()
                except Exception:
                    pass
                self._dev = None
            return False

    def disconnect(self) -> None:
        """Gracefully release device, returning keyboard to onboard firmware RGB mode."""
        if self._dev is not None:
            try:
                disable_pkt = bytes([0x00, CMD_SIGNALRGB_DISABLE] + [0x00] * (PACKET_SIZE - 1))
                try:
                    self._dev.write(disable_pkt)
                except Exception:
                    self._dev.write(disable_pkt[1:])
                self._dev.close()
            except Exception as e:
                logger.warning(f"Error during Windows disconnect: {e}")
            finally:
                self._dev = None

        self._connected = False
        logger.info("Disconnected from URX Core75 Windows Raw HID.")

    def pause_streaming(self) -> bool:
        """Release keyboard from SignalRGB mode (0x26), allowing onboard preset modes."""
        if self._dev is not None:
            try:
                disable_pkt = bytes([0x00, CMD_SIGNALRGB_DISABLE] + [0x00] * (PACKET_SIZE - 1))
                try:
                    self._dev.write(disable_pkt)
                except Exception:
                    self._dev.write(disable_pkt[1:])
                self._paused = True
                logger.info("Paused SignalRGB streaming. Keyboard returned to hardware preset mode.")
                return True
            except Exception as e:
                logger.warning(f"Error pausing stream: {e}")
        return False

    def resume_streaming(self) -> bool:
        """Re-engage SignalRGB mode (0x25) for host effects."""
        if self._dev is not None:
            try:
                enable_pkt = bytes([0x00, CMD_SIGNALRGB_ENABLE] + [0x00] * (PACKET_SIZE - 1))
                try:
                    self._dev.write(enable_pkt)
                except Exception:
                    self._dev.write(enable_pkt[1:])
                time.sleep(0.02)
                self._paused = False
                logger.info("Resumed SignalRGB streaming. Smoky Velvet active.")
                return True
            except Exception as e:
                logger.warning(f"Error resuming stream: {e}")
        return False

    def send_frame(self, colors: List[Color], force: bool = False) -> bool:
        """Stream full 82-LED RGB frame to hardware via 9-LED packets."""
        if self._paused and not force:
            return False

        if not self.is_connected:
            if not self.connect():
                return False

        now = time.monotonic()
        if not force and self.min_frame_interval > 0 and (now - self._last_send_time) < (self.min_frame_interval * 0.75):
            return False

        try:
            rgb_tuples = [c.to_tuple() for c in colors]
            if len(rgb_tuples) < 82:
                last_color = rgb_tuples[-1] if rgb_tuples else (0, 0, 0)
                rgb_tuples.extend([last_color] * (82 - len(rgb_tuples)))

            for start_idx in range(0, 82, MAX_LEDS_PER_PACKET):
                chunk = rgb_tuples[start_idx : min(start_idx + MAX_LEDS_PER_PACKET, 82)]
                count = len(chunk)
                # Prepend 0x00 Report ID for Windows hidapi
                packet = bytearray([0x00, CMD_SIGNALRGB_STREAM, start_idx, count])
                for rgb in chunk:
                    packet.extend(rgb)
                if len(packet) < (PACKET_SIZE + 1):
                    packet.extend([0] * (PACKET_SIZE + 1 - len(packet)))

                try:
                    self._dev.write(bytes(packet[:PACKET_SIZE + 1]))
                except Exception:
                    self._dev.write(bytes(packet[1:PACKET_SIZE + 1]))

                time.sleep(0.0022)  # Inter-packet pacing: 2.2ms guarantees separate USB frames

            self._last_send_time = now
            return True
        except Exception as e:
            logger.error(f"Windows hardware write error: {e}. Marking disconnected.")
            if self._dev is not None:
                try:
                    self._dev.close()
                except Exception:
                    pass
                self._dev = None
            self._connected = False
            return False
