#!/usr/bin/env python3
"""
Smoky Velvet CLI — Desktop Control Surface and Caelestia Launcher Interface.
Allows instantaneous switching of profiles, brightness, and effects from the shell or launcher.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.ipc import IpcClient

def main():
    parser = argparse.ArgumentParser(description="Smoky Velvet Desktop Control CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status
    subparsers.add_parser("status", help="Query engine state and hardware status")

    # list-profiles
    subparsers.add_parser("list-profiles", help="List all saved profiles")

    # profile <name>
    prof_parser = subparsers.add_parser("profile", help="Switch active profile")
    prof_parser.add_argument("name", type=str, help="Name of profile (e.g. smoky_velvet, coding, study, gaming, night)")

    # brightness <val>
    bright_parser = subparsers.add_parser("brightness", help="Set brightness level")
    bright_parser.add_argument("value", type=float, help="Brightness value (0.0 to 1.0, or 0 to 100)")

    # toggle-ripple
    subparsers.add_parser("toggle-ripple", help="Toggle reactive ripple effect on or off")

    # night
    subparsers.add_parser("night", help="Quickly switch to Night Mode")

    # test-ripple
    ripple_parser = subparsers.add_parser("test-ripple", help="Trigger a test ripple on keyboard")
    ripple_parser.add_argument("--key", type=int, default=75, help="LED index to trigger (default: 75 / Space)")

    # gui
    subparsers.add_parser("gui", help="Launch the Smoky Velvet Desktop Studio GUI")

    args = parser.parse_args()

    if args.command == "gui":
        import subprocess
        gui_path = Path(__file__).parent / "gui.py"
        python_bin = Path(__file__).parent / ".venv" / "bin" / "python3"
        subprocess.Popen([str(python_bin), str(gui_path)])
        print("🌌 Launched Smoky Velvet Desktop Studio GUI!")
        return

    if not args.command or args.command == "status":
        resp = IpcClient.send_command({"action": "status"})
        if resp.get("status") == "error":
            print(f"❌ {resp.get('message')}")
            sys.exit(1)
        data = resp.get("data", {})
        print("🌌 SMOKY VELVET STATUS:")
        print(f"  • Hardware:        {data.get('device_name', 'Unknown')} ({data.get('led_count', 0)} LEDs)")
        print(f"  • Active Profile:  {data.get('active_profile')}")
        print(f"  • Base Color:      {data.get('base_color_hex')}")
        print(f"  • Brightness:      {int(data.get('brightness', 1.0) * 100)}%")
        print(f"  • Reactive Ripple: {'Enabled' if data.get('reactive_enabled') else 'Disabled'}")
        print(f"  • Frame Rate:      {data.get('fps', 50):.0f} FPS")
        return

    if args.command == "profile":
        resp = IpcClient.send_command({"action": "set_profile", "name": args.name})
        if resp.get("status") == "ok":
            print(f"✨ Switched to profile: {args.name}")
        else:
            print(f"❌ Error: {resp.get('message')}")
            sys.exit(1)
        return

    if args.command == "list-profiles":
        resp = IpcClient.send_command({"action": "list_profiles"})
        if resp.get("status") == "ok":
            profiles = resp.get("profiles", [])
            active = resp.get("active")
            print("📁 Available Profiles:")
            for p in profiles:
                mark = "👉" if p == active else "  "
                print(f"  {mark} {p}")
        else:
            print(f"❌ Error: {resp.get('message')}")
        return

    if args.command == "brightness":
        val = args.value
        if val > 1.0:
            val = val / 100.0
        val = max(0.0, min(1.0, val))
        resp = IpcClient.send_command({"action": "set_brightness", "value": val})
        if resp.get("status") == "ok":
            print(f"☀️ Brightness set to {int(val * 100)}%")
        else:
            print(f"❌ Error: {resp.get('message')}")
        return

    if args.command == "toggle-ripple":
        resp = IpcClient.send_command({"action": "toggle_reactive"})
        if resp.get("status") == "ok":
            state = "Enabled" if resp.get("reactive_enabled") else "Disabled"
            print(f"🌊 Reactive Ripple: {state}")
        else:
            print(f"❌ Error: {resp.get('message')}")
        return

    if args.command == "night":
        resp = IpcClient.send_command({"action": "set_profile", "name": "night"})
        if resp.get("status") == "ok":
            print("🌙 Night Mode activated (low intensity velvet)")
        else:
            print(f"❌ Error: {resp.get('message')}")
        return

    if args.command == "test-ripple":
        resp = IpcClient.send_command({"action": "trigger_ripple", "led": args.key})
        if resp.get("status") == "ok":
            print(f"⚡ Test ripple dispatched to LED {args.key}")
        else:
            print(f"❌ Error: {resp.get('message')}")
        return

if __name__ == "__main__":
    main()
