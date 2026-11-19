# Contributing to Smoky Velvet

## Development Guidelines
1. **Hardware Safety First:** Never alter keyboard firmware or flash hex/bin files.
2. **Platform Independence:** The core lighting engine, animation physics, and profile storage must remain 100% agnostic to Linux or Windows.
3. **No Keylogging:** Keystroke input modules must only extract physical scancodes/coordinates $(x, y)$ for reactive lighting. Never store, buffer, or transmit typed characters.
4. **Clean Abstractions:** Hardware communication is strictly isolated inside `hardware/device_manager/`. No effect or UI code should directly touch raw sockets or USB descriptors.
5. **Compositor Integrity:** All effects must participate in the layer stack (`Base`, `Reactive`, `Indicator`, `Ambient`) rather than directly writing to the device.
