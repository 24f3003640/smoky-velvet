# Changelog

All notable changes to Smoky Velvet will be documented in this file.

## [0.3.0] - 2026-11-19 (Native SignalRGB Raw HID Engine & Custom Water Ripple Wave)
### Added
- **Direct SignalRGB Raw HID Driver (`hardware/signalrgb_hid.py`)**: Direct kernel-level Raw HID streaming over `/dev/hidraw1` using the native SignalRGB protocol extension (`0x25` enable, `0x24` stream in 9-LED packets, `0x26` disable). Eliminates all external server/SDK dependencies (ColorHoster/OpenRGB) with ~2ms frame delivery.
- **Dynamic Device Auto-Discovery**: Automatically enumerates `/sys/class/hidraw` to locate URX Core75 interface `01` (`0003:36B0:3130`) with graceful fallback.
- **Physical Optical Color Calibration**:
  - Base: Smoky Plum Velvet (`#8200A0` / RGB `[130, 0, 160]` / `Hue: 215, Sat: 255`).
  - Ripple Crest: Deep Antique Gold (`#FF2400` / RGB `[255, 36, 0]` / `Hue: 6, Sat: 255`).
  - Wave Trailing Wake: Velvet Magenta (`#BE006E` / RGB `[190, 0, 110]`).
- **Custom Mathematical Water Ripple Physics (`effects/ripple.py`)**: Replaced firmware built-ins with a bespoke isotropic circular wave engine running at 50 FPS. Radiates outward from key $(x_0, y_0)$ with a tight 4.2-key localized radius, Gaussian wavefront falloff, and smooth alpha blending into the resting purple pond.
- **Unit Test Suite Expansion**: Added `tests/test_signalrgb_hid.py`, bringing the automated test suite to 23 tests passing 100%.
- **Live User Systemd Daemon**: Configured and enabled `smoky-velvet.service` as an auto-starting user service.

## [0.2.0] - 2026-11-19 (Milestones 1–5: Core Engine, Ripple, Profiles, Hyprland & Caelestia)
### Added
- **Device Adapter (`hardware/adapter.py`)**: Resilient OpenRGB SDK bridge client with auto-reconnection and dirty-frame buffering.
- **Color & Math Engine (`core/color.py`)**: High-performance RGB models, sRGB lerp, and multi-stop gradient interpolation (`LIQUID_GOLD_GRADIENT`).
- **Layout Geometry (`core/layout.py`)**: Precise KLE parser extracting centers $(x, y)$ in keyboard units and distance matrix for all 81 LEDs.
- **Layer Compositor (`core/compositor.py`)**: 4-layer composition stack (`Base`, `Reactive`, `Indicator`, `Environmental`) with dirty diffing and alpha/additive blend modes.
- **Liquid Antique Gold Ripple (`effects/ripple.py`)**: Physics-based expanding wavefront with 4-stage color dissipation and overlapping multi-keypress ripples.
- **Evdev Input Listener (`input/linux_evdev.py`)**: Multi-endpoint asynchronous reader for URX Core75 with zero keylogging.
- **Profile Manager (`core/profile.py`)**: Portable JSON configuration with 5 default profiles (`smoky_velvet`, `coding`, `study`, `gaming`, `night`).
- **UNIX Domain Socket IPC & CLI (`core/ipc.py`, `cli.py`)**: Fast local IPC interface supporting status queries, profile switching, and brightness adjustments.
- **Hyprland IPC Integration (`integrations/hyprland.py`)**: Live listener on `.socket2.sock` supporting workspace-bound and active-window profile triggers.
- **Desktop Environment Integration**: Installed `smoky-velvet` CLI into `~/.local/bin/` and created `.desktop` launcher entry.
- **Automated Test Suite**: 20 comprehensive unit tests passing with 100% success rate.
- **Systemd User Units**: Created `smoky-velvet.service` and `colorhoster.service` in `~/.config/systemd/user/`.
### Added
- Official VIA layout definition downloaded (`URX_Core75_VIA.json`, `URX_Core75_VIA_24G.json`).
- ColorHoster v0.7.2 musl x86_64 server deployed in `smoky-velvet/tools/colorhoster/`.
- Linux udev rules installed at `/etc/udev/rules.d/99-urx-core75.rules` for non-root `/dev/hidraw*` and `/dev/input/*` access.
- Python virtual environment with `openrgb-python` and `evdev`.
- Complete hardware verification suite proving per-key addressability across all 81 LEDs.
- Verified rotary encoder event stream on Interface 2 (`REL_HWHEEL`).
- Master documentation suite (`PROJECT_SPEC.md`, `HARDWARE.md`, `DESIGN_SYSTEM.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `FEATURES.md`, `TESTING.md`, `DECISIONS.md`).
