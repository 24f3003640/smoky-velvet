# Smoky Velvet Testing Strategy & Verification Suite

## 1. Automated Testing Strategy
Smoky Velvet incorporates tests across 4 domains:
1. **Unit Tests (`tests/unit/`):**
   - Color math (sRGB, hex conversion, gamma correction, gradient interpolation).
   - Ripple physics (wavefront radius, Gaussian attenuation, multi-ripple summation).
   - Layer compositor (layer blending, alpha mask calculation, dirty state tracking).
2. **Hardware Mock Tests (`tests/mocks/`):**
   - Mock OpenRGB server emulating the 81-LED Core75 matrix for CI environments.
   - Mock evdev input feeder simulating typing sequences.
3. **Integration Tests (`tests/integration/`):**
   - DeviceAdapter connection lifecycle, auto-reconnection on socket disconnect.
   - Profile serialization / deserialization roundtrip.
4. **Physical Hardware Verification Suite (`tests/hardware/`):**
   - Direct interactive scripts testing the physical keyboard LEDs, measuring frame update rates, and checking latency.

## 2. Milestone 0 Physical Hardware Test Results
- **Test Date:** 2026-11-19
- **Device Tested:** URX Core75 (Wired Mode, VID `0x36B0`, PID `0x3130`)
- **Bridge Tested:** ColorHoster v0.7.2 on port 6742
- **Results:**
  - Connection to SDK Server: **PASS** (Latency < 2 ms)
  - Device identification: **PASS** ("URX Core75", 81 LEDs)
  - Mode switch to "Per Key RGB": **PASS**
  - Full-board solid color application (Midnight Purple `#30183F`): **PASS**
  - Individual key selective targeting (Esc, Space, Enter, Caps Lock): **PASS**
  - Linux evdev device accessibility: **PASS** (`/dev/input/event3`, `event6`, `event7`)
  - Rotary encoder event detection: **PASS** (`REL_HWHEEL` on consumer control interface)
