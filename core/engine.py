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
from effects.heatmap import TypingHeatmapManager
from effects.telemetry import TelemetryRowEffect
from effects.volume_gauge import VolumeGaugeEffect
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
        target_fps: float = 35.0,
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

        self.heatmap_manager = TypingHeatmapManager(led_count=self.layout.led_count)
        self.heatmap_manager.enabled = False
        self.compositor.reactive_layer.add_effect(self.heatmap_manager)

        self.telemetry_effect = TelemetryRowEffect()
        self.telemetry_effect.enabled = False
        self.compositor.reactive_layer.add_effect(self.telemetry_effect)

        self.volume_gauge = VolumeGaugeEffect()
        self.compositor.reactive_layer.add_effect(self.volume_gauge)

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
        self._last_heartbeat_time: float = 0.0

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
        self.ripple_manager.crest_color = profile.reactive_crest_color
        self.ripple_manager.base_color = profile.base_color
        self.heatmap_manager.enabled = profile.heatmap_enabled
        self.telemetry_effect.enabled = profile.telemetry_enabled

        # Apply per-key overrides if any
        if profile.custom_key_colors:
            for key_str, hex_val in profile.custom_key_colors.items():
                try:
                    led_idx = int(key_str)
                    self.compositor.base_layer.set_key(led_idx, Color.from_hex(hex_val))
                except Exception:
                    pass

        self.profile_manager.set_active(profile.name)
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
        """Called whenever a key is pressed to trigger reactive ripple and heatmap."""
        if self.compositor.reactive_layer.enabled:
            logger.debug(f"Triggering ripple at LED {led_index} (active ripples before: {len(self.ripple_manager.ripples)})")
            self.ripple_manager.trigger(led_index, timestamp)
            if self.heatmap_manager.enabled:
                self.heatmap_manager.trigger(led_index, timestamp)

    def set_caps_lock(self, is_active: bool, color: Optional[Color] = None) -> None:
        """Indicator for Caps Lock (LED index 44)."""
        if is_active:
            ind_color = color if color is not None else Color(255, 255, 255)
            self.compositor.indicator_layer.set_indicator(44, ind_color, opacity=1.0)
        else:
            self.compositor.indicator_layer.clear_indicator(44)

    def _on_knob_action(self, action: str, timestamp: float) -> None:
        """Called when rotary encoder volume knob turns, clicks, or triggers gestures."""
        logger.info(f"Rotary knob action detected: {action}")
        if action in ("volume_up", "volume_down", "mute_click"):
            self.volume_gauge.trigger_activity()
        elif action in ("knob_long_press", "knob_double_click"):
            logger.info("Knob gesture detected: toggling hardware preset vs software mode!")
            self._handle_ipc_command({"action": "toggle_mode"})

    def _on_workspace_change(self, workspace_name: str) -> None:
        logger.debug(f"Hyprland workspace changed to: {workspace_name}")
        prof = self.profile_manager.get_active_profile()
        if prof and prof.workspace_bindings and workspace_name in prof.workspace_bindings:
            target = prof.workspace_bindings[workspace_name]
            if target != self.profile_manager.active_profile_name:
                self.switch_profile(target)

    def _on_active_window(self, win_class: str, win_title: str) -> None:
        logger.debug(f"Hyprland active window: {win_class}")
        prof = self.profile_manager.get_active_profile()
        if prof and prof.app_rules:
            for pattern, target in prof.app_rules.items():
                if pattern.lower() in win_class.lower():
                    if target != self.profile_manager.active_profile_name:
                        self.switch_profile(target)
                    break

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
                    "heatmap_enabled": self.heatmap_manager.enabled,
                    "telemetry_enabled": self.telemetry_effect.enabled,
                    "hardware_mode": getattr(self.adapter, "is_paused", False),
                    "volume": int(self.volume_gauge.current_volume * 100),
                    "muted": self.volume_gauge.is_muted,
                    "fps": self.target_fps
                }
            }

        elif action == "list_profiles":
            self.profile_manager.load_all()
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

        elif action == "pause" or action == "hardware_mode":
            if hasattr(self.adapter, "pause_streaming"):
                self.adapter.pause_streaming()
            return {"status": "ok", "mode": "hardware_preset"}

        elif action == "resume" or action == "software_mode":
            if hasattr(self.adapter, "resume_streaming"):
                self.adapter.resume_streaming()
                self.trigger_key(13)  # Sapphire ripple confirmation from Delete key
            return {"status": "ok", "mode": "smoky_velvet"}

        elif action == "toggle_mode":
            if hasattr(self.adapter, "is_paused") and self.adapter.is_paused:
                self.adapter.resume_streaming()
                self.trigger_key(13)
                return {"status": "ok", "mode": "smoky_velvet"}
            else:
                if hasattr(self.adapter, "pause_streaming"):
                    self.adapter.pause_streaming()
                return {"status": "ok", "mode": "hardware_preset"}

        elif action == "volume":
            import subprocess
            sub = req.get("subaction")
            if sub == "up":
                step = req.get("step", 5)
                subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{step}%+"], check=False)
            elif sub == "down":
                step = req.get("step", 5)
                subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{step}%-"], check=False)
            elif sub == "mute":
                subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], check=False)
            self.volume_gauge.trigger_activity()
            return {
                "status": "ok",
                "volume": int(self.volume_gauge.current_volume * 100),
                "muted": self.volume_gauge.is_muted
            }

        elif action == "toggle_heatmap":
            self.heatmap_manager.enabled = not self.heatmap_manager.enabled
            return {"status": "ok", "heatmap_enabled": self.heatmap_manager.enabled}

        elif action == "toggle_telemetry":
            self.telemetry_effect.enabled = not self.telemetry_effect.enabled
            return {"status": "ok", "telemetry_enabled": self.telemetry_effect.enabled}

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
            self.input_listener.set_knob_callback(self._on_knob_action)
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
        # Dirty-frame diffing: only transmit to hardware if frame changed or on 2.5s keepalive heartbeat
        if is_dirty or (now - self._last_heartbeat_time) >= 2.5:
            self.adapter.send_frame(frame)
            self._last_heartbeat_time = now

    def _render_loop(self) -> None:
        last_time = time.monotonic()
        initial_frame, _ = self.compositor.render_frame()
        self.adapter.send_frame(initial_frame, force=True)

        while not self._stop_event.is_set():
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            self.tick(dt, now)

            elapsed = time.monotonic() - now
            sleep_time = self.frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
