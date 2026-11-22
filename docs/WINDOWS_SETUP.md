# Smoky Velvet on Windows (URX Core75 Setup Guide)

This guide walks you through running the native **Smoky Velvet** RGB lighting engine and Desktop Studio GUI on Windows 10 or 11.

---

## 1. Prerequisites

1. **Python 3.11 or 3.12:**
   - Download the official installer from [python.org](https://www.python.org/downloads/).
   - ⚠️ **IMPORTANT:** During installation, ensure you check the box:  
     **`☑ Add python.exe to PATH`**
2. **URX Core75 Keyboard:**
   - Connect via USB-C cable (ensure physical switch on back is set to **Wired / OFF**).
   - *No third-party drivers or Zadig installs required!* Windows uses the built-in standard USB HID driver.

---

## 2. Installation (PowerShell or Command Prompt)

Open **PowerShell** or **Command Prompt** and run:

```powershell
# 1. Clone the repository
git clone https://github.com/24f3003640/smoky-velvet.git
cd smoky-velvet

# 2. Create and activate a Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install Windows dependencies
pip install -r requirements-windows.txt
```

*(If PowerShell blocks running scripts, run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once).*

---

## 3. Running Smoky Velvet

### Method A: One-Click Launchers (Easiest)
Simply double-click the included batch scripts:
* **`run_smoky_velvet.bat`** — Starts the background engine (30 FPS, active profiles, WPM gauge, ripples).
* **`run_gui.bat`** — Launches the interactive Desktop Studio GUI.

### Method B: Command Line (CLI)
From your active virtual environment:

```powershell
# Start the background lighting engine
python main.py

# Switch active profile
python cli.py profile stealth_crimson
python cli.py profile smoky_velvet
python cli.py profile tokyo_night

# Change WPM theme
python cli.py wpm amber_gold

# Query engine status
python cli.py status

# Launch the visual GUI
python gui.py
```

---

## 4. Run Automatically on Windows Startup (Optional)

To have Smoky Velvet automatically launch when Windows boots:

1. Press `Win + R`, type **`shell:startup`**, and press Enter. This opens your Windows Startup folder.
2. Right-click inside the folder $\rightarrow$ **New** $\rightarrow$ **Shortcut**.
3. In the location field, browse to your `run_smoky_velvet.bat` file (or type `wscript.exe` / Python background runner if you want it completely headless without a visible console window).
4. Click **Next** and **Finish**.

Now Smoky Velvet will illuminate your URX Core75 as soon as you log in!

---

## 5. Windows Hardware Architecture

| Subsystem | Linux Implementation | Windows Implementation |
| :--- | :--- | :--- |
| **Transport** | `/dev/hidraw*` direct kernel driver | `hidapi` (VID `0x36B0`, PID `0x3130`, Interface 1) |
| **Keystroke Input** | Linux `evdev` reader loops | Global keyboard hook via `pynput` |
| **Caps Lock Sync** | Hyprland IPC query + debounce | Win32 API `GetKeyState(VK_CAPITAL)` (instant, 0ms) |
| **Volume Knob** | Linux `wpctl` / PipeWire | Windows Multimedia HID (native volume & mute keys) |
| **Local IPC** | User UNIX Domain Socket | High-speed Localhost Loopback (`127.0.0.1:49753`) |
| **Desktop Studio GUI** | PyQt6 / PySide6 | PyQt6 / PySide6 (100% native Windows styling) |
