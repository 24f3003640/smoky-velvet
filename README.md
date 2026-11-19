# Smoky Velvet 🌌✨

Smoky Velvet is a cross-platform desktop RGB control and customization application designed for mechanical keyboards, targeting the **URX Core75 (Smoky Black)** with first-class Linux (Hyprland + Caelestia) and Windows support.

---

## 🎨 Signature Identity
- **Base Illumination:** Midnight Purple (`#30183F`)
- **Reactive Ripple:** Liquid Antique Gold (`#FFE6A3` ➔ `#E5C477` ➔ `#C49A45` ➔ `#986B2D`)

---

## ⚡ Architecture Highlights
- **Layered Compositor:** Base, Reactive, Indicator, and Ambient layers composited into a single RGB frame.
- **Hardware Agnostic:** Communicates via OpenRGB SDK protocol through ColorHoster.
- **Zero Firmware Tampering:** Operates entirely over standard VIA Raw HID without altering QMK firmware or onboard settings.
- **Privacy First:** Physical coordinate mapping with zero keystroke persistence.

---

## 📂 Project Organization
```
smoky-velvet/
├── hardware/              # Layout definitions, LED matrix coordinates
│   └── layouts/           # URX_Core75_VIA.json
├── tools/                 # ColorHoster bridge and helper binaries
├── core/                  # Color models, layer compositor, animation engine
├── effects/               # Liquid Antique Gold ripple, waves, reactive pulses
├── input/                 # Linux evdev and Windows RawInput adapters
├── integrations/          # Hyprland IPC socket2, Caelestia launcher
└── tests/                 # Unit, integration, and hardware verification suites
```

---

## 🚀 Status
- **Current Milestone:** Milestone 0 (Complete) ➔ Milestone 1 (In Progress)
- **Verified Hardware:** URX Core75 — 81 LEDs addressable, rotary encoder detected, udev rules active.
