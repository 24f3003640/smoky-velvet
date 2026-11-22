"""Smoky Velvet Hardware Package"""
import sys
from hardware.adapter import OpenRGBDeviceAdapter

if sys.platform.startswith("win"):
    from hardware.windows_hid import WindowsSignalRGBAdapter
    __all__ = ["OpenRGBDeviceAdapter", "WindowsSignalRGBAdapter"]
else:
    from hardware.signalrgb_hid import SignalRGBRawHIDAdapter
    __all__ = ["OpenRGBDeviceAdapter", "SignalRGBRawHIDAdapter"]
