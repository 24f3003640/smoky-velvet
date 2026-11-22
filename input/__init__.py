"""Smoky Velvet Input Package"""
import sys
from input.listener import InputListener

if sys.platform.startswith("win"):
    from input.windows_listener import WindowsInputListener
    __all__ = ["InputListener", "WindowsInputListener"]
else:
    from input.linux_evdev import LinuxEvdevListener
    __all__ = ["InputListener", "LinuxEvdevListener"]
