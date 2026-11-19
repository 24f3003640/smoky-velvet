"""
Main Smoky Velvet lighting engine.
Coordinates layout, input listening, layer composition, profile management,
Hyprland IPC events, and hardware frame delivery.
"""
from __future__ import annotations
import logging
import threading
import time
from typing import Any, Dict, Optional
from core.color import Color, MIDNIGHT_PURPLE
from core.compositor import Compositor
from core.ipc import IpcServer
from core.layout import KeyboardLayout
from core.profile import Profile, ProfileManager
from effects.ripple import LiquidGoldRippleManager
from hardware.adapter import OpenRGBDeviceAdapter
from input.listener import InputListener
from integrations.hyprland import HyprlandEventListener

logger = logging.getLogger(__name__)

class LightingEngine:
    def __init__(
        self,
        layout: KeyboardLayout,
        adapter: OpenRGBDeviceAdapter,
        input_listener: Optional[InputListener] = None,
        target_fps: float = 50.0,
        enable_hyprland: bool = True
    ):
        self.layout = layout
        self.adapter = adapter
        self.input_listener = input_listener
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps

        self.compositor = Compositor(layout)
        self.profile_manager = ProfileManager()

        self.ripple_manager = LiquidGoldRippleManager()
        self.compositor.reactive_layer.add_effect(self.ripple_manager)

        # Apply initial active profile
        initial_profile = self.profile_manager.get_active_profile()
        self.apply_profile(initial_profile)

        # IPC Server for CLI & Caelestia integration
        self.ipc_server = IpcServer(self._handle_ipc_command)

        # Hyprland IPC listener
        self.hyprland: Optional[HyprlandEventListener] = None
        if enable_hyprland:
            self.hyprland = HyprlandEventListener(
                on_active_window=self._on_active_window,
                on_workspace_change=self._on_workspace_change,
                on_fullscreen=self._on_fullscreen
            )

        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._is_running

    def apply_profile(self, profile: Profile) -> None:
        """Applies all parameters from a Profile object to the engine layers."""
        self.compositor.base_layer.set_all(profile.base_color)
        self.compositor.set_brightness(profile.brightness)
        self.compositor.reactive_layer.enabled = profile.reactive_enabled

        self.ripple_manager.duration = profile.reactive_duration
        self.ripple_manager.max_radius = profile.reactive_max_radius
        self.ripple_manager.wave_thickness = profile.reactive_wave_thickness

        # Apply per-key overrides if any
        if profile.custom_key_colors:
            for key_str, hex_val in profile.custom_key_colors.items():
                try:
                    led_idx = int(key_str)
                    self.compositor.base_layer.set_key(led_idx, Color.from_hex(hex_val))
                except Exception:
                    pass

        self.profile_manager.active_profile_name = profile.name
        logger.info(f"Applied profile: '{profile.name}' (Base: {profile.base_color_hex}, Brightness: {profile.brightness})")

    def switch_profile(self, name: str) -> bool:
        prof = self.profile_manager.get_profile(name)
        if not prof:
            return False
        self.apply_profile(prof)
        return True

    def set_brightness(self, brightness: float) -> None:
        self.compositor.set_brightness(brightness)

    def set_base_color(self, color: Color) -> None:
        self.compositor.base_layer.set_all(color)

    def trigger_key(self, led_index: int, timestamp: Optional[float] = None) -> None:
        """Called whenever a key is pressed to trigger reactive ripple."""
        if self.compositor.reactive_layer.enabled:
            self.ripple_manager.trigger(led_index, timestamp)

    def set_caps_lock(self, is_active: bool, color: Optional[Color] = None) -> None:
        """Indicator for Caps Lock (LED index 44)."""
        if is_active:
            ind_color = color if color is not None else Color(255, 255, 255)
            self.compositor.indicator_layer.set_indicator(44, ind_color, opacity=1.0)
        else:
            self.compositor.indicator_layer.clear_indicator(44)

    def _on_workspace_change(self, workspace_name: str) -> None:
        logger.debug(f"Hyprland workspace changed to: {workspace_name}")
        # Default mapping example: workspace 4 -> gaming, workspace 1 -> coding, etc.
        mappings = {
            "1": "coding",
            "4": "gaming",
            "5": "study"
        }
        target_profile = mappings.get(workspace_name)
        if target_profile and target_profile != self.profile_manager.active_profile_name:
            self.switch_profile(target_profile)

    def _on_active_window(self, win_class: str, win_title: str) -> None:
        logger.debug(f"Hyprland active window: {win_class}")
        class_lower = win_class.lower()
        if "steam" in class_lower or "game" in class_lower:
            if self.profile_manager.active_profile_name != "gaming":
                self.switch_profile("gaming")
        elif "code" in class_lower or "zed" in class_lower or "cursor" in class_lower:
            if self.profile_manager.active_profile_name != "coding":
                self.switch_profile("coding")

    def _on_fullscreen(self, is_fullscreen: bool) -> None:
        logger.debug(f"Hyprland fullscreen state: {is_fullscreen}")

    def _handle_ipc_command(self, req: Dict[str, Any]) -> Dict[str, Any]:
        action = req.get("action")

        if action == "status":
            prof = self.profile_manager.get_active_profile()
            return {
                "status": "ok",
                "data": {
                    "is_running": self._is_running,
                    "device_name": self.adapter.device.name if self.adapter.device else "URX Core75",
                    "led_count": self.layout.led_count,
                    "active_profile": prof.name,
                    "base_color_hex": prof.base_color_hex,
                    "brightness": self.compositor.global_brightness,
                    "reactive_enabled": self.compositor.reactive_layer.enabled,
                    "fps": self.target_fps
                }
            }

        elif action == "list_profiles":
            return {
                "status": "ok",
                "profiles": list(self.profile_manager.profiles.keys()),
                "active": self.profile_manager.active_profile_name
            }

        elif action == "set_profile":
            name = req.get("name")
            if not name or not self.switch_profile(name):
                return {"status": "error", "message": f"Profile '{name}' not found."}
            return {"status": "ok", "active_profile": name}

        elif action == "set_brightness":
            val = float(req.get("value", 1.0))
            self.compositor.set_brightness(val)
            return {"status": "ok", "brightness": self.compositor.global_brightness}

        elif action == "toggle_reactive":
            self.compositor.reactive_layer.enabled = not self.compositor.reactive_layer.enabled
            return {"status": "ok", "reactive_enabled": self.compositor.reactive_layer.enabled}

        elif action == "trigger_ripple":
            led = int(req.get("led", 75))
            self.trigger_key(led)
            return {"status": "ok", "led": led}

        return {"status": "error", "message": f"Unknown action '{action}'"}

    def start(self) -> bool:
        if self._is_running:
            return True

        # 1. Connect hardware
        if not self.adapter.connect():
            logger.error("Failed to connect to hardware device adapter.")
            return False

        # 2. Start input listener
        if self.input_listener:
            self.input_listener.set_callback(self.trigger_key)
            self.input_listener.start()

        # 3. Start IPC server
        self.ipc_server.start()

        # 4. Start Hyprland listener if available
        if self.hyprland and self.hyprland.is_available:
            self.hyprland.start()

        # 5. Start render loop thread
        self._stop_event.clear()
        self._is_running = True
        self._thread = threading.Thread(target=self._render_loop, daemon=True, name="LightingEngineLoop")
        self._thread.start()
        logger.info(f"Smoky Velvet lighting engine started at {self.target_fps:.0f} FPS.")
        return True

    def stop(self) -> None:
        if not self._is_running:
            return

        self._stop_event.set()
        self._is_running = False

        if self.hyprland:
            self.hyprland.stop()

        self.ipc_server.stop()

        if self.input_listener:
            self.input_listener.stop()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            self._thread = None

        # Clean restoration of base layer
        try:
            if self.adapter.is_connected:
                clean_frame = [c for c in self.compositor.base_layer.colors]
                self.adapter.send_frame(clean_frame, force=True)
                time.sleep(0.05)
                self.adapter.disconnect()
        except Exception as e:
            logger.warning(f"Error restoring base state on shutdown: {e}")

        logger.info("Smoky Velvet lighting engine stopped cleanly.")

    def tick(self, dt: float, now: float) -> None:
        """Perform one animation update and composite."""
        self.compositor.update(dt, now)
        frame, is_dirty = self.compositor.render_frame()
        if is_dirty:
            self.adapter.send_frame(frame)

    def _render_loop(self) -> None:
        last_time = time.time()
        initial_frame, _ = self.compositor.render_frame()
        self.adapter.send_frame(initial_frame, force=True)

        while not self._stop_event.is_set():
            now = time.time()
            dt = now - last_time
            last_time = now

            self.tick(dt, now)

            elapsed = time.time() - now
            sleep_time = self.frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
