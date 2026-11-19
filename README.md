# Smoky Velvet 🌌✨

**Smoky Velvet** is a high-performance, privacy-first desktop lighting engine and reactive physics driver built for mechanical keyboards, specifically calibrated for the **URX Core75 (Smoky Black translucent case, 81 physical LEDs)** on Linux (Hyprland + Caelestia) and Windows.

---

## 🎨 Signature Aesthetic Identity
* **Base Illumination ("The Velvet Pond"):** Deep Velvet Purple (`#FF00FE` / QMK Hue 215, Sat 255) — authentic, steady, non-flickering underglow.
* **Reactive Ripple ("The Stone"):** Electric Cobalt Sapphire (`#1E90FF`) — a cool, radiant analogous shockwave radiating outward and smoothly dissolving like watercolor into the purple pond.

---

## ⚡ Technical Highlights
* **Native Kernel-Level SignalRGB Raw HID Direct Driver:** Communicates directly with `/dev/hidraw1` using 9-LED chunks via the SignalRGB protocol extension (`0x25` enable, `0x24` stream, `0x26` disable). Achieves ~2ms latency without requiring external servers or background daemons.
* **Hardware Anti-Flicker Timing:** 1.2ms hardware inter-packet pacing delay between USB HID packets at 35 FPS, giving the IS31FL3731 LED matrix driver clean I2C cycles with zero packet drops and zero flicker.
* **Fluid Watercolor Ripple Physics Engine:**
  * Square-root fluid dispersion: $r(t) = 2.6 \cdot \sqrt{t/\text{duration}}$.
  * Wavefront broadening: $1.0 \to 1.6$ keys Gaussian width expansion.
  * Cosine ease-out envelope: $\cos^2(\frac{\pi}{2} \cdot \frac{t}{\text{duration}})$, eliminating all abrupt cutoffs.
  * Chromatic pigment dissolution: Wave hue progressively dissolves into the resting Velvet Purple pond.
* **Anti-Chaos Typing Engine:**
  * **Dynamic Cadence Detection:** Exponential Moving Average of keystroke timing automatically scales ripple duration ($0.44\text{s} \to 0.72\text{s}$) to keep rapid typing clean, crisp, and readable under your fingers.
  * **Dominant-Wave Interference Normalization:** Primary wave dictates crest sharpness; secondary waves provide a soft 20% ambient wash without blinding cluster blowouts.
  * **Per-Key Debounce ($90\text{ms}$):** Rapid duplicate keystrokes re-energize existing droplets instead of producing conflicting rings.
* **Privacy First (Zero Keystroke Logging):** Asynchronous Linux `evdev` reader maps keys directly to physical LED indices $(x,y)$ in memory and discards the keystroke. No text or key history is ever logged, buffered, or transmitted.
* **First-Class Desktop Integration:** Native UNIX socket IPC, Hyprland window/workspace listener, and systemd user service.

---

## 🕹️ CLI Quick Reference

The `smoky-velvet` CLI is installed directly in `~/.local/bin/smoky-velvet`:

```bash
# Query live engine and hardware status
smoky-velvet status

# List all available profiles
smoky-velvet list-profiles

# Switch active profile instantly
smoky-velvet profile electric_sapphire   # Signature Electric Cobalt Sapphire
smoky-velvet profile smoky_cyan          # Shimmering Cyan Synthwave
smoky-velvet profile electric_aqua       # High-Voltage Pure Aqua
smoky-velvet profile mint_jade           # Frosted Mint Jade
smoky-velvet profile sunset_peach        # Luminous Sunset Peach
smoky-velvet profile electric_ruby       # Radiant Crimson Ruby
smoky-velvet profile pearl_white         # Pure Diamond Pearl Starlight
smoky-velvet profile honey_amber         # Radiant Honey Amber
smoky-velvet profile smoky_copper        # Molten Antique Gold / Copper

# Adjust brightness (0.0 to 1.0 or 0 to 100)
smoky-velvet brightness 0.85

# Trigger a test ripple across keyboard
smoky-velvet test-ripple --key 38
```

---

## 📂 Project Organization
```
smoky-velvet/
├── cli.py                 # Desktop CLI control surface
├── main.py                # Main application runtime and background daemon
├── core/                  # Core engine systems
│   ├── color.py           # Color models, KaTeX mathematical blending, gradients
│   ├── compositor.py      # 4-layer composition stack (Base, Reactive, Indicator, Ambient)
│   ├── engine.py          # Frame coordination, IPC command dispatch, render loop
│   ├── ipc.py             # UNIX domain socket IPC server & client
│   ├── layout.py          # Physical KLE layout parser & 2D distance matrix
│   └── profile.py         # JSON Profile Manager with hot-reloading & persistence
├── effects/               # Lighting animation effects
│   ├── base.py            # Abstract Effect interface
│   └── ripple.py          # Fluid watercolor dispersion, cadence adaptation, chaos suppression
├── hardware/              # Hardware transport adapters
│   ├── adapter.py         # OpenRGB SDK client
│   ├── signalrgb_hid.py   # Direct Raw HID SignalRGB kernel driver
│   └── layouts/           # Official VIA JSON keyboard definitions
├── input/                 # Hardware input listeners
│   ├── listener.py        # Abstract InputListener interface
│   └── linux_evdev.py     # High-speed evdev physical key reader (zero text logging)
├── integrations/          # Desktop environment bridges
│   └── hyprland.py        # Hyprland IPC socket2 workspace and active window listener
├── profiles/              # JSON lighting profiles (hot-reloaded)
└── tests/                 # Comprehensive unit & integration test suites
```

---

## 🛠️ Background Service Management
Smoky Velvet runs as an automated systemd user service:

```bash
# Check service status
systemctl --user status smoky-velvet.service

# View live logs
journalctl --user -u smoky-velvet.service -f

# Restart service
systemctl --user restart smoky-velvet.service
```
