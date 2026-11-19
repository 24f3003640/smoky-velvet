# Smoky Velvet Development Roadmap & Task Tracker

## Milestones Overview
- [x] **Milestone 0: Research & Hardware Verification** (Completed)
- [x] **Milestone 1: RGB Communication Prototype & Device Adapter** (Completed)
- [x] **Milestone 2: Layered Lighting Engine & Compositor** (Completed)
- [x] **Milestone 3: Reactive Effects & Input Engine (Liquid Gold Ripple)** (Completed)
- [x] **Milestone 4: Profile Management & CLI Controls** (Completed)
- [x] **Milestone 5: Linux Desktop Integrations (Hyprland + Caelestia)** (Completed)
- [ ] **Milestone 6: Windows Platform Compatibility** (Planned)
- [ ] **Milestone 7: Desktop GUI Studio (V1.0 Polish & Packaging)** (Planned)
- [ ] **Milestone 8: V1.1 Smart Profiles & Typing Heatmap** (Planned)
- [ ] **Milestone 9: V1.2 Audio/Screen Reactive & V2.0 Creator Studio** (Planned)

---

## Detailed Task Tracker

| Task ID | Description | Milestone | Status | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **M0-1** | Inspect Core75 USB descriptors and interface mapping | M0 | **Complete** | Vendor `0x36B0`, Product `0x3130`, Interface 1 VIA Raw HID verified |
| **M0-2** | Obtain official VIA JSON layout definition | M0 | **Complete** | Official `URX_Core75_VIA.json` acquired and verified |
| **M0-3** | Verify LED count and physical 2D layout geometry | M0 | **Complete** | 81 LEDs (`l0`–`l80`) mapped with exact 2D $(x,y)$ coordinates |
| **M0-4** | Deploy ColorHoster OpenRGB SDK bridge on Linux | M0 | **Complete** | ColorHoster running at `127.0.0.1:6742`, zero crashes |
| **M0-5** | Configure Linux udev rules for non-root hardware access | M0 | **Complete** | Rule active in `/etc/udev/rules.d/99-urx-core75.rules`, `hidraw` and `input` accessible |
| **M0-6** | Verify per-key hardware lighting control via OpenRGB | M0 | **Complete** | Successfully set Midnight Purple and highlighted individual keys in Antique Gold |
| **M1-1** | Implement robust standalone OpenRGB SDK Client / DeviceAdapter | M1 | **Complete** | Reconnect logic, clean protocol handshake, dirty-frame caching |
| **M1-2** | Implement ColorHoster process supervisor / health watchdog | M1 | **Complete** | Systemd user unit + background service verified |
| **M1-3** | Direct SignalRGB Raw HID Adapter (`hardware/signalrgb_hid.py`) | M1 | **Complete** | Direct `/dev/hidraw1` 9-LED packet streaming, bypassing OpenRGB with ~2ms latency |
| **M2-1** | Core Color and Gradient library with KaTeX math models | M2 | **Complete** | Linear, sRGB, multi-stop gradient interpolation, additive/alpha blending |
| **M2-2** | Layer Compositor (Base, Reactive, Indicator, Ambient) | M2 | **Complete** | 4-layer stack with dirty diffing, opacity, and Caps Lock override |
| **M3-1** | Linux evdev input hook with zero keystroke persistence | M3 | **Complete** | Multi-device select loop on `/dev/input/by-id/*URX*`, converts to LED index |
| **M3-2** | Liquid Antique Gold ripple physics engine | M3 | **Complete** | Multi-keypress overlapping ripples with 4-stop gold dissipation |
| **M3-3** | Custom 50 FPS Water Ripple Wave & Physical Calibration | M3 | **Complete** | Isotropic circular wave, 4.2-key localized radius, Smoky Plum Velvet base + Antique Gold crest |
| **M4-1** | Portable Profile Manager (JSON profiles) | M4 | **Complete** | Shipped with 5 default profiles (`smoky_velvet`, `coding`, `study`, `gaming`, `night`) |
| **M4-2** | Fast UNIX Socket IPC Server & `smoky-velvet` CLI | M4 | **Complete** | Instant CLI commands for profile, brightness, and status control |
| **M5-1** | Hyprland IPC adapter for active window / workspace sync | M5 | **Complete** | Auto-switches profile on workspace change (e.g. WS 1 ➔ coding, WS 4 ➔ gaming) |
| **M5-2** | Caelestia launcher integration | M5 | **Complete** | Installed `smoky-velvet` into `~/.local/bin/` and `.desktop` entry |
