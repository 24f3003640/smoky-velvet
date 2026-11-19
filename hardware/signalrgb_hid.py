"""
Hardware transport adapter for communicating directly with URX Core75 via
Raw HID (SignalRGB protocol extension).

Directly streams per-key RGB frames to /dev/hidraw* without requiring OpenRGB,
ColorHoster, or any intermediate background services.
"""
from __future__ import annotations
import glob
import logging
import os
import select
import time
from pathlib import Path
from typing import List, Optional
from core.color import Color

logger = logging.getLogger(__name__)

# Protocol Command Constants
CMD_SIGNALRGB_ENABLE   = 0x25
CMD_SIGNALRGB_DISABLE  = 0x26
CMD_SIGNALRGB_STREAM   = 0x24
CMD_VIA_CUSTOM_SET_VAL = 0x07

URX_VID = "36B0"
URX_PID = "3130"
SIGNALRGB_INTERFACE_NUM = "01"
MAX_LEDS_PER_PACKET = 9
PACKET_SIZE = 32

class DeviceInfo:
    def __init__(self, name: str = "URX Core75"):
        self.name = name

class SignalRGBRawHIDAdapter:
    """
    Direct Raw HID device adapter for URX Core75 using the SignalRGB protocol extension.
    Achieves ~2ms roundtrip USB frame streaming directly in kernel space.
    """
    def __init__(
        self,
        device_path: Optional[str] = None,
        led_count: int = 82,
        min_frame_interval: float = 0.028  # ~35 FPS smooth pacing
    ):
        self.device_path = device_path
        self.led_count = led_count
        self.min_frame_interval = min_frame_interval

        self.device = DeviceInfo("URX Core75")
        self._fd: Optional[int] = None
        self._last_send_time: float = 0.0
        self._connected: bool = False
        self._paused: bool = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_connected(self) -> bool:
        return self._connected and self._fd is not None

    @classmethod
    def find_device_node(cls) -> Optional[str]:
        """
        Dynamically finds the URX Core75 Raw HID endpoint (bInterfaceNumber=01).
        """
        for p in sorted(glob.glob('/sys/class/hidraw/hidraw*')):
            dev_name = os.path.basename(p)
            dev_path = f'/dev/{dev_name}'
            try:
                device_dir = os.path.realpath(os.path.join(p, 'device'))
                uevent_path = os.path.join(device_dir, 'uevent')
                if not os.path.exists(uevent_path):
                    continue
                uevent = open(uevent_path).read()
                if URX_VID in uevent and URX_PID in uevent:
                    # Verify interface 01
                    cur = device_dir
                    for _ in range(5):
                        cur = os.path.dirname(cur)
                        intf_file = os.path.join(cur, 'bInterfaceNumber')
                        if os.path.exists(intf_file):
                            b_num = open(intf_file).read().strip()
                            if b_num == SIGNALRGB_INTERFACE_NUM:
                                return dev_path
                            break
            except Exception:
                continue

        # Fallback to standard /dev/hidraw1
        if os.path.exists('/dev/hidraw1'):
            return '/dev/hidraw1'
        return None

    def connect(self) -> bool:
        """Connect to keyboard Raw HID endpoint and enable SignalRGB stream mode."""
        if self.is_connected:
            return True

        target_path = self.device_path or self.find_device_node()
        if not target_path or not os.path.exists(target_path):
            logger.error(f"Cannot find URX Core75 Raw HID device node.")
            self._connected = False
            return False

        try:
            self._fd = os.open(target_path, os.O_RDWR)
            # Enable SignalRGB effect mode (0x25)
            enable_pkt = bytes([CMD_SIGNALRGB_ENABLE] + [0x00] * (PACKET_SIZE - 1))
            os.write(self._fd, enable_pkt)
            time.sleep(0.02)

            self.device_path = target_path
            self._connected = True
            logger.info(f"Connected to URX Core75 on {target_path} via SignalRGB Raw HID.")
            return True
        except Exception as e:
            logger.error(f"Failed to open {target_path}: {e}")
            if self._fd is not None:
                try:
                    os.close(self._fd)
                except Exception:
                    pass
                self._fd = None
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Gracefully release device, disabling SignalRGB stream mode."""
        if self._fd is not None:
            try:
                # 1. Disable SignalRGB stream mode (0x26)
                disable_pkt = bytes([CMD_SIGNALRGB_DISABLE] + [0x00] * (PACKET_SIZE - 1))
                os.write(self._fd, disable_pkt)

                # 2. Restore VIA Solid Color (Smoky Plum Velvet: Hue 215, Sat 255)
                solid_cmd = bytes([CMD_VIA_CUSTOM_SET_VAL, 3, 2, 1] + [0x00] * 28)
                color_cmd = bytes([CMD_VIA_CUSTOM_SET_VAL, 3, 4, 215, 255] + [0x00] * 27)
                os.write(self._fd, solid_cmd)
                os.write(self._fd, color_cmd)

                os.close(self._fd)
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self._fd = None

        self._connected = False
        logger.info("Disconnected from URX Core75 Raw HID.")

    def pause_streaming(self) -> bool:
        """Release keyboard from SignalRGB mode (0x26), allowing onboard preset RGB modes to run without flicker."""
        if self._fd is not None:
            try:
                disable_pkt = bytes([CMD_SIGNALRGB_DISABLE] + [0x00] * (PACKET_SIZE - 1))
                os.write(self._fd, disable_pkt)
                self._paused = True
                logger.info("Paused SignalRGB streaming. Keyboard returned to hardware preset mode.")
                return True
            except Exception as e:
                logger.warning(f"Error pausing SignalRGB stream: {e}")
        return False

    def resume_streaming(self) -> bool:
        """Re-engage SignalRGB mode (0x25) for Smoky Velvet host effects."""
        if self._fd is not None:
            try:
                enable_pkt = bytes([CMD_SIGNALRGB_ENABLE] + [0x00] * (PACKET_SIZE - 1))
                os.write(self._fd, enable_pkt)
                time.sleep(0.02)
                self._paused = False
                logger.info("Resumed SignalRGB streaming. Smoky Velvet active.")
                return True
            except Exception as e:
                logger.warning(f"Error resuming SignalRGB stream: {e}")
        return False

    def send_frame(self, colors: List[Color], force: bool = False) -> bool:
        """
        Stream full 82-LED RGB frame to hardware via 9-LED packets.
        """
        if self._paused and not force:
            return False

        if not self.is_connected:
            if not self.connect():
                return False

        now = time.monotonic()
        if not force and self.min_frame_interval > 0 and (now - self._last_send_time) < (self.min_frame_interval * 0.75):
            return False

        try:
            total_leds = min(len(colors), self.led_count)
            # Pad up to 82 LEDs if layout has 81
            rgb_tuples = [c.to_tuple() for c in colors]
            if len(rgb_tuples) < 82:
                last_color = rgb_tuples[-1] if rgb_tuples else (0, 0, 0)
                rgb_tuples.extend([last_color] * (82 - len(rgb_tuples)))

            for start_idx in range(0, 82, MAX_LEDS_PER_PACKET):
                chunk = rgb_tuples[start_idx : min(start_idx + MAX_LEDS_PER_PACKET, 82)]
                count = len(chunk)
                packet = bytearray([CMD_SIGNALRGB_STREAM, start_idx, count])
                for rgb in chunk:
                    packet.extend(rgb)
                if len(packet) < PACKET_SIZE:
                    packet.extend([0] * (PACKET_SIZE - len(packet)))

                os.write(self._fd, bytes(packet[:PACKET_SIZE]))
                time.sleep(0.0012)  # Inter-packet pacing: prevents USB FIFO overruns and LED matrix flicker

            self._last_send_time = now
            return True
        except Exception as e:
            logger.error(f"Hardware write error: {e}. Marking disconnected.")
            if self._fd is not None:
                try:
                    os.close(self._fd)
                except Exception:
                    pass
                self._fd = None
            self._connected = False
            return False
