# Architecture Decision Records (ADRs)

## ADR-001: Technology Stack Selection — Python 3.14 + Native Adapters
- **Status:** Accepted
- **Context:** The application requires cross-platform support (Linux and Windows), low latency for 30–60 FPS lighting frames, asynchronous event handling (evdev, Hyprland IPC, Windows RawInput), and a rapid, modular architecture.
- **Decision:** Python 3.14 with standard `asyncio` for the core engine and controller, utilizing:
  - `openrgb-python` / custom pure-Python SDK client for protocol communication.
  - `evdev` for Linux input event capture (without keylogging).
  - Modern cross-platform GUI framework (e.g. PyQt6 / PySide6 or lightweight native frontend).
- **Consequences:** Highly portable, rapid iteration, clean separation of platform adapters.

## ADR-002: Hardware Transport — ColorHoster Bridge over Raw HID
- **Status:** Accepted
- **Context:** The URX Core75 uses QMK with VIA per-key lighting. OpenRGB natively does not talk VIA direct mode out-of-the-box for all keyboards. URX officially supports and distributes ColorHoster.
- **Decision:** Use ColorHoster v0.7.2 musl binary as a localized SDK bridge running on `127.0.0.1:6742`. Smoky Velvet controls ColorHoster lifecycle.
- **Consequences:** Full per-key RGB control with no custom firmware flashing required.

## ADR-003: LED Matrix Calibration — 81 LEDs (0 to 80)
- **Status:** Accepted
- **Context:** Literature and informal guides interchangeably refer to "81" or "82" LEDs.
- **Decision:** Verified against both the official VIA layout JSON (`URX_Core75_VIA.json`) and the actual physical hardware enumeration. Exactly 81 addressable LEDs (`l0` through `l80`) are present. Matrix positions `0,14` and `0,15` correspond to the mechanical rotary encoder knob (`e0`), which does not possess an addressable RGB diode.
- **Consequences:** Accurate rendering math, zero array index out-of-bounds, accurate key mapping.

## ADR-004: Linux Non-Root Hardware Access via udev
- **Status:** Accepted
- **Context:** By default, Linux assigns `/dev/hidraw*` to `root:root 0600`, preventing non-root users from writing VIA lighting packets or reading evdev key events.
- **Decision:** Install dedicated udev rule `/etc/udev/rules.d/99-urx-core75.rules` matching VID `36b0` and PID `3130` with `MODE="0666"` and `TAG+="uaccess"`.
- **Consequences:** The application runs entirely in user-space with zero security risk and zero root requirements.
