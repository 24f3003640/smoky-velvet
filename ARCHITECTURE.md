# Smoky Velvet System Architecture

## 1. Architectural Philosophy
Smoky Velvet separates **hardware transmission**, **platform input**, **composited rendering**, and **user interface** into distinct, isolated subsystems. No business logic or effect rendering relies on OS-specific calls or hardware-specific wire protocols.

```
+--------------------------------------------------------------+
|                         User Interface                       |
|        (Dashboard, Lighting Studio, Effects Panel, Tray)     |
+--------------------------------------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|                     Application Controller                   |
|        (State Management, Profile Router, Lifecycle)         |
+--------------------------------------------------------------+
         |                                            |
         v                                            v
+-----------------------+                    +-----------------+
|     Input Engine      |                    | Lighting Engine |
| (evdev/RawInput hook) |                    |  (Compositor)   |
+-----------------------+                    +-----------------+
         |                                            |
         |  KeyEvent (key_id, timestamp)              v
         +---------------------------------> +-----------------+
                                             |  Layer Stack    |
                                             |  - Indicators   |
                                             |  - Reactive     |
                                             |  - Base         |
                                             +-----------------+
                                                      |
                                                      | Composited RGB Frame
                                                      v
                                             +-----------------+
                                             | Device Adapter  |
                                             |  (OpenRGB SDK)  |
                                             +-----------------+
                                                      |
                                                      | TCP :6742
                                                      v
                                             +-----------------+
                                             |   ColorHoster   |
                                             | (VIA Raw HID)   |
                                             +-----------------+
                                                      |
                                                      | USB HID /dev/hidraw1
                                                      v
                                             +-----------------+
                                             |   URX Core75    |
                                             +-----------------+
```

---

## 2. Layer-Based Rendering Pipeline
The lighting engine renders frames using a prioritized 4-layer stack:

1. **Layer 1: Base Illumination**
   - Solid, per-key, or gradient background (Default: Midnight Purple `#30183F`).
   - Constant background coverage for all 81 LEDs.
2. **Layer 2: Reactive & Dynamic Animations**
   - Liquid Antique Gold ripple, waves, reactive pulses, typing heatmaps.
   - Computes alpha-blended or additive RGB offsets based on keypress events.
3. **Layer 3: System Status Indicators**
   - High-priority state overrides (Caps Lock indicator, mic mute, volume levels, notification bursts).
   - Overrides designated LED positions with configurable priority.
4. **Layer 4: Environmental / Ambient (Future)**
   - Audio reactive visualizations and screen color ambience.

### Single Hardware Writer Guarantee
Only a single thread/worker writes to the `DeviceAdapter`. Frames are evaluated at a fixed tick rate (default: 40–60 FPS) with dirty-frame checking to avoid redundant USB bus traffic.
