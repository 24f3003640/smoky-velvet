# Smoky Velvet Development Roadmap & Task Tracker

## Milestones Overview
- [x] **Milestone 0: Research & Hardware Verification** (Completed)
- [x] **Milestone 1: RGB Communication Prototype & Device Adapter** (Completed)
- [x] **Milestone 2: Layered Lighting Engine & Compositor** (Completed)
- [x] **Milestone 3: Reactive Effects & Input Engine (Fluid Watercolor Ripple)** (Completed)
- [x] **Milestone 4: Profile Management & CLI Controls** (Completed)
- [x] **Milestone 5: Linux Desktop Integrations (Hyprland + Caelestia)** (Completed)
- [x] **Milestone 7: Desktop GUI Studio (V1.0 Polish & Packaging)** (Completed)
- [x] **Milestone 8: V1.1 Smart Profiles & Typing Heatmap** (Completed)
- [ ] **Milestone 6: Windows Platform Compatibility** (Planned)
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
| **M1-4** | Hardware Inter-Packet Pacing & Anti-Flicker Timing | M1 | **Complete** | 1.2ms pacing delay between chunk packets, rock-solid 35 FPS, zero matrix flicker |
| **M2-1** | Core Color and Gradient library with KaTeX math models | M2 | **Complete** | Linear, sRGB, multi-stop gradient interpolation, additive/alpha blending |
| **M2-2** | Layer Compositor (Base, Reactive, Indicator, Ambient) | M2 | **Complete** | 4-layer stack with dirty diffing, opacity, and Caps Lock override |
| **M3-1** | Linux evdev input hook with zero keystroke persistence | M3 | **Complete** | Multi-device select loop on `/dev/input/by-id/*URX*`, converts to LED index |
| **M3-2** | Fluid Watercolor Ripple Physics Engine | M3 | **Complete** | Square-root dispersion ($r = 2.6 \sqrt{p}$), wavefront broadening ($1.0 \to 1.6$), cosine ease-out envelope |
| **M3-3** | Chromatic Pigment Dissolution | M3 | **Complete** | Wave crest lerps directly into Velvet Purple pond, eliminating abrupt visual cutoffs |
| **M3-4** | Anti-Chaos Typing Cadence Engine | M3 | **Complete** | EMA typing cadence detection; scales wave duration ($0.44\text{s} \to 0.72\text{s}$) to keep rapid typing clean |
| **M3-5** | Dominant-Wave Interference Normalization | M3 | **Complete** | Primary wave preserves crest sharpness; secondary waves provide soft 20% wash with zero cluster blowout |
| **M3-6** | Signature Aesthetic Calibration | M3 | **Complete** | User-selected **Electric Sapphire** (`#1E90FF`) over **Deep Velvet Purple** (`#FF00FE`) |
| **M4-1** | Portable Profile Manager (JSON profiles) | M4 | **Complete** | Hot-reloading, dynamic profile scanning, and reboot persistence |
| **M4-2** | Fast UNIX Socket IPC Server & `smoky-velvet` CLI | M4 | **Complete** | Instant CLI commands for profile, brightness, ripple testing, and status control |
| **M5-1** | Hyprland IPC adapter for active window / workspace sync | M5 | **Complete** | Config-driven workspace and window rules over Hyprland `.socket2.sock` |
| **M5-2** | Caelestia launcher integration | M5 | **Complete** | Installed `smoky-velvet` into `~/.local/bin/` and `.desktop` entry |
| **M7-1** | PyQt6 Desktop Studio GUI (`gui.py`) | M7 | **Complete** | Real-time 2D 81-LED keyboard visualizer, interactive color pickers, and live ripple testing |
