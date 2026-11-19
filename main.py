#!/usr/bin/env python3
"""
Smoky Velvet: Core Application Entry Point & CLI Runtime.
Manages the LightingEngine, Input Engine, and Hardware Bridge.
"""
from __future__ import annotations
import argparse
import logging
import signal
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.color import Color, MIDNIGHT_PURPLE
from core.layout import KeyboardLayout
from core.engine import LightingEngine
from hardware.adapter import OpenRGBDeviceAdapter
from input.linux_evdev import LinuxEvdevListener

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SmokyVelvet")

def main():
    parser = argparse.ArgumentParser(description="Smoky Velvet: Cross-Platform RGB Customization Engine")
    parser.add_argument("--demo", action="store_true", help="Run automated ripple wave demonstration")
    parser.add_argument("--brightness", type=float, default=1.0, help="Brightness level (0.0 to 1.0)")
    parser.add_argument("--fps", type=float, default=50.0, help="Target update frequency in FPS (default: 50)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="OpenRGB / ColorHoster host")
    parser.add_argument("--port", type=int, default=6742, help="OpenRGB / ColorHoster port")
    parser.add_argument("--device-node", type=str, default=None, help="Explicit evdev input device path")
    args = parser.parse_args()

    project_root = Path(__file__).parent
    layout_path = project_root / "hardware" / "layouts" / "URX_Core75_VIA.json"

    if not layout_path.exists():
        logger.error(f"Layout definition not found at: {layout_path}")
        sys.exit(1)

    logger.info("Loading URX Core75 layout geometry...")
    layout = KeyboardLayout.load_from_via_json(layout_path)

    adapter = OpenRGBDeviceAdapter(
        host=args.host,
        port=args.port,
        min_frame_interval=1.0 / args.fps
    )

    listener = LinuxEvdevListener(device_path=args.device_node)

    engine = LightingEngine(
        layout=layout,
        adapter=adapter,
        input_listener=listener,
        target_fps=args.fps,
        enable_hyprland=True
    )
    engine.set_brightness(args.brightness)

    # Clean signal handling for Ctrl+C
    def handle_exit(sig, frame):
        logger.info("Termination signal received. Shutting down gracefully...")
        engine.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    logger.info("Starting Smoky Velvet lighting engine...")
    if not engine.start():
        logger.error("Failed to start engine. Please verify ColorHoster is running on 127.0.0.1:6742.")
        sys.exit(1)

    print("\n" + "=" * 65)
    print("  SMOKY VELVET ENGINE ACTIVE 🌌✨")
    print("  Base: Midnight Purple (#30183F)")
    print("  Reactive Effect: Liquid Antique Gold Ripple")
    print(f"  Target: URX Core75 ({layout.led_count} LEDs) @ {args.fps:.0f} FPS")
    print("=" * 65)

    if args.demo:
        print("\n[Running automated ripple demo across key anchors... Press Ctrl+C to stop]\n")
        demo_keys = [0, 15, 30, 45, 60, 75, 56, 70, 80] # Esc, 1, Q, A, Z, Space, Enter, Up, Right
        try:
            while True:
                for k in demo_keys:
                    key_def = layout.get_key(k)
                    name = key_def.name if key_def else f"Key_{k}"
                    logger.info(f"Triggering demo ripple at: {name} (LED {k})")
                    engine.trigger_key(k)
                    time.sleep(0.45)
        except KeyboardInterrupt:
            handle_exit(None, None)
    else:
        print("\n[Listening to live keyboard typing... Press any key on your Core75!]")
        print("[Press Ctrl+C to exit]\n")
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            handle_exit(None, None)

if __name__ == "__main__":
    main()
