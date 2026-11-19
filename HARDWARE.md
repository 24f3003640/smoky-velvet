# Hardware Specification & Verification Report: URX Core75

## 1. Verified Device Information
- **Manufacturer:** URX
- **Product:** URX Core75 (Smoky Black)
- **USB Vendor ID (VID):** `0x36B0` (`13904`)
- **USB Product ID (PID):** `0x3130` (`12592`)
- **Firmware Base:** QMK Firmware with VIA per-key RGB support
- **Connection Mode:** Wired USB-C (Physical back toggle switch set to `OFF` / Wired)

## 2. USB Interfaces & Descriptors
The URX Core75 exposes three USB interfaces:
1. **Interface 0 (Boot Keyboard):**
   - HID Class (Subclass 1, Protocol 1)
   - EP 1 IN (8 bytes interrupt)
2. **Interface 1 (VIA Raw HID):**
   - HID Class (Subclass 0, Protocol 0)
   - EP 2 IN (32 bytes interrupt)
   - EP 3 OUT (32 bytes interrupt)
   - Used by VIA and ColorHoster for per-key RGB lighting packets
3. **Interface 2 (Consumer / Mouse / System Controls):**
   - HID Class (Consumer control, rotary encoder wheel events)
   - EP 4 IN (32 bytes interrupt)

## 3. LED Matrix Architecture
- **Verified LED Count:** 81 addressable per-key LEDs (indexed `0` to `80`).
  *(Note: While some documentation informally refers to an "82-LED matrix", the official layout file `URX_Core75_VIA.json` specifies exactly 81 RGB LEDs `l0` through `l80`. The remaining two matrix entries correspond to the rotary encoder press and rotation `e0`, which do not contain backlight LEDs.)*
- **Layout Matrix:** 6 rows × 16 columns.
- **Physical Geometry:** 75% compact ANSI layout with dedicated arrow cluster and rotary encoder knob.
  - Row 0: `Escape` (l0), `F1`–`F12` (l1–l12), `Delete` (l13), Encoder (`e0`)
  - Row 1: `` ` `` to `Backspace` (l14–l27), `Home` (l28)
  - Row 2: `Tab` to `\` (l29–l42), `End` (l43)
  - Row 3: `Caps Lock` to `Enter` (l44–l56), `Page Up` (l57)
  - Row 4: `Left Shift` to `Right Shift` (l58–l69), `Up Arrow` (l70), `Page Down` (l71)
  - Row 5: `L-Ctrl`, `L-Win`, `L-Alt`, `Space (6.25U)`, `R-Alt`, `R-Fn`, `Left`, `Down`, `Right` (l72–l80)

## 4. Linux Permissions & udev Rules
Standard Linux restricts `/dev/hidraw*` to `root:root 0600`. To allow non-root users to communicate with the keyboard and capture input events without elevated permissions, the following udev rule is installed at `/etc/udev/rules.d/99-urx-core75.rules`:

```udev
# URX Core75 Raw HID (VIA), USB and Input access for Smoky Velvet
KERNEL=="hidraw*", ATTRS{idVendor}=="36b0", ATTRS{idProduct}=="3130", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="36b0", ATTRS{idProduct}=="3130", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="input", ATTRS{idVendor}=="36b0", ATTRS{idProduct}=="3130", MODE="0666", TAG+="uaccess"
```

## 5. ColorHoster SDK Server Bridge
- **Binary:** ColorHoster v0.7.2 (Linux musl x86_64, zero external C library dependencies).
- **Execution Flags:**
  ```bash
  ColorHoster -d ./hardware/layouts -b -j ./hardware/layouts/URX_Core75_VIA.json
  ```
- **SDK Protocol Endpoint:** `127.0.0.1:6742` (OpenRGB SDK protocol).
- **Verified Status:** Connects to URX Core75 via raw HID, initiates VIA direct mode (mode 0, "Per Key RGB"), and streams per-key RGB frames.
- **Update Rate Considerations:** The QMK/VIA raw HID bridge transfers 32-byte chunks. To prevent buffer starvation or USB bus saturation, frame updates should be capped at 30–60 FPS and only dirty frames transmitted.
