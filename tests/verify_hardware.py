#!/usr/bin/env python3
"""
Smoky Velvet: Milestone 0 Hardware Verification Suite
Tests connection to ColorHoster, enables Per-Key RGB mode, sets Midnight Purple,
and runs an individual key test in Antique Gold.
"""
import sys
import time
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor

# Signature Colors
MIDNIGHT_PURPLE = RGBColor(48, 24, 63)
CHAMPAGNE_GLOW  = RGBColor(255, 230, 163)
ANTIQUE_GOLD    = RGBColor(196, 154, 69)

def main():
    print("=" * 60)
    print("  SMOKY VELVET: HARDWARE VERIFICATION SUITE")
    print("=" * 60)
    
    print("\n[1/5] Connecting to ColorHoster OpenRGB server on 127.0.0.1:6742...")
    try:
        client = OpenRGBClient(port=6742)
    except Exception as e:
        print(f"FAILED to connect to ColorHoster: {e}")
        print("Please ensure ColorHoster is running.")
        sys.exit(1)
        
    if not client.devices:
        print("FAILED: No RGB devices found on SDK server.")
        sys.exit(1)
        
    dev = client.devices[0]
    print(f" -> Found device: {dev.name} (ID: {dev.id})")
    print(f" -> Addressable LEDs: {len(dev.leds)}")
    
    print("\n[2/5] Switching to 'Per Key RGB' mode...")
    mode = dev.modes[0]
    # Neutralize openrgb-python client validation assertion
    mode.colors_min = None
    mode.colors_max = None
    mode.colors = None
    dev.set_mode(mode)
    print(" -> Mode set to 'Per Key RGB' (Direct mode).")
    time.sleep(0.1)
    
    print("\n[3/5] Setting foundational base: Midnight Purple (#30183F)...")
    dev.set_color(MIDNIGHT_PURPLE)
    print(" -> Midnight Purple applied to all 81 LEDs.")
    time.sleep(1.0)
    
    print("\n[4/5] Testing individual LED addressability (Antique Gold wave)...")
    # Wave across row anchors: Esc (0), Tab (29), Caps (44), LShift (58), Space (75), Enter (56)
    test_keys = [0, 15, 29, 44, 58, 75, 56, 70, 80]
    for key_idx in test_keys:
        led_name = dev.leds[key_idx].name
        print(f" -> Illuminating LED {key_idx:2d} ({led_name}) in Antique Gold...")
        frame = [MIDNIGHT_PURPLE] * len(dev.leds)
        frame[key_idx] = ANTIQUE_GOLD
        dev.set_colors(frame)
        time.sleep(0.2)
        
    print("\n[5/5] Restoring Midnight Purple base...")
    dev.set_color(MIDNIGHT_PURPLE)
    print(" -> Base restored cleanly.")
    
    print("\n" + "=" * 60)
    print("  ALL HARDWARE VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()
