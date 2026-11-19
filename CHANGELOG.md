# Changelog

All notable changes to Smoky Velvet will be documented in this file.

## [1.0.0] - 2026-11-19 (Linux V1.0 Release - The Velvet Engine & Electric Sapphire)
### Added
- **Signature Palette: Electric Sapphire on Velvet Purple**:
  - Resting Base: Deep Velvet Purple (`#FF00FE` / QMK Hue 215, Sat 255).
  - Wave Crest: Electric Cobalt Sapphire (`#1E90FF`).
  - Automatic persistence of active profile in `.active_profile` across reboots.
- **Fluid Watercolor Ripple Physics Engine**:
  - Square-root fluid dispersion: Wave naturally decelerates as it expands ($r(t) = 2.6 \cdot \sqrt{t/\text{duration}}$).
  - Wavefront broadening: Dynamic Gaussian width expansion ($1.0 \to 1.6$ keys) eliminating harsh ring borders.
  - Cosine ease-out envelope: $\cos^2(\frac{\pi}{2} \cdot \frac{t}{\text{duration}})$ ensuring both intensity and derivative smoothly reach zero with zero snap.
  - Chromatic pigment dissolution: The ripple hue progressively dissolves into the resting Velvet Purple pond.
- **Anti-Chaos Typing Engine**:
  - Dynamic Cadence Detection: Exponential Moving Average of keystroke timing automatically scales ripple duration ($0.44\text{s} \to 0.72\text{s}$) to keep rapid typing clean, crisp, and readable.
  - Dominant-Wave Interference Normalization: Primary wave dictates crest sharpness; secondary waves provide a soft 20% ambient wash without blinding cluster blowouts.
  - Per-Key Debounce ($90\text{ms}$): Rapid duplicate keystrokes re-energize existing droplets instead of producing conflicting rings.
- **Hardware Anti-Flicker Timing**:
  - 1.2ms hardware pacing delay between 9-LED USB Raw HID packets.
  - 35 FPS rock-solid frame rate preventing IS31FL3731 LED matrix I2C bus collision.
- **Expanded Harmonic Color Profiles**:
  - `electric_sapphire` (Signature active)
  - `smoky_cyan` (Shimmering Cyan Synthwave)
  - `electric_aqua` (High-Voltage Pure Cyan)
  - `mint_jade` (Frosted Mint Jade)
  - `hot_coral` (Sunset Coral Flamingo)
  - `pearl_white` (Diamond Pearl Starlight)
  - `honey_amber` (Radiant Honey Citrine)
  - `smoky_rosegold` (Warm 18k Rose Gold)
  - `smoky_copper` (Molten Antique Gold)

## [0.3.0] - 2026-11-19 (Native SignalRGB Raw HID Engine & Custom Water Ripple Wave)
### Added
- **Direct SignalRGB Raw HID Driver (`hardware/signalrgb_hid.py`)**: Direct kernel-level Raw HID streaming over `/dev/hidraw1` using the native SignalRGB protocol extension (`0x25` enable, `0x24` stream in 9-LED packets, `0x26` disable). Eliminates all external server/SDK dependencies with ~2ms frame delivery.
- **Dynamic Device Auto-Discovery**: Automatically enumerates `/sys/class/hidraw` to locate URX Core75 interface `01` with graceful fallback.
- **Unit Test Suite Expansion**: Added `tests/test_signalrgb_hid.py` and `tests/test_ripple.py`, bringing the automated test suite to 24 tests passing 100%.
- **Live User Systemd Daemon**: Configured and enabled `smoky-velvet.service` as an auto-starting user service.

## [0.2.0] - 2026-11-19 (Milestones 1–5: Core Engine, Ripple, Profiles, Hyprland & Caelestia)
### Added
- **Device Adapter (`hardware/adapter.py`)**: Resilient OpenRGB SDK bridge client with auto-reconnection and dirty-frame buffering.
- **Color & Math Engine (`core/color.py`)**: High-performance RGB models, sRGB lerp, and multi-stop gradient interpolation.
- **Layout Geometry (`core/layout.py`)**: Precise KLE parser extracting centers $(x, y)$ in keyboard units and distance matrix for all 81 LEDs.
- **Layer Compositor (`core/compositor.py`)**: 4-layer composition stack (`Base`, `Reactive`, `Indicator`, `Environmental`) with dirty diffing and alpha/additive blend modes.
- **Evdev Input Listener (`input/linux_evdev.py`)**: Multi-endpoint asynchronous reader for URX Core75 with zero keylogging.
- **Profile Manager (`core/profile.py`)**: Portable JSON configuration with default profiles.
- **UNIX Domain Socket IPC & CLI (`core/ipc.py`, `cli.py`)**: Fast local IPC interface supporting status queries, profile switching, and brightness adjustments.
- **Hyprland IPC Integration (`integrations/hyprland.py`)**: Live listener on `.socket2.sock` supporting workspace-bound and active-window profile triggers.
- **Desktop Environment Integration**: Installed `smoky-velvet` CLI into `~/.local/bin/` and created `.desktop` launcher entry.
