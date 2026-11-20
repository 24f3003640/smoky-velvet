#!/usr/bin/env python3
"""
Smoky Velvet Desktop Studio — Interactive GUI Control Surface.
Visualizes the 81-LED URX Core75 layout in real-time, allowing intuitive
profile switching, live color picking, and animated ripple triggering.
"""
from __future__ import annotations
import math
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QLinearGradient, QRadialGradient, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QSlider, QFrame,
    QColorDialog, QMessageBox, QGroupBox, QListView
)

# Project root setup
sys.path.insert(0, str(Path(__file__).parent))

from core.color import Color
from core.ipc import IpcClient
from core.layout import KeyboardLayout
from core.profile import ProfileManager

DARK_BG = "#0D0A14"
PANEL_BG = "#161220"
CARD_BG = "#1F1A2C"
ACCENT_BLUE = "#1E90FF"
ACCENT_PURPLE = "#A855F7"
TEXT_COLOR = "#F3E8FF"
MUTED_TEXT = "#948B9E"
BORDER_COLOR = "#2D253D"

STYLE_SHEET = f"""
QMainWindow {{
    background-color: {DARK_BG};
}}
QWidget {{
    color: {TEXT_COLOR};
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}
QGroupBox {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    color: {ACCENT_PURPLE};
}}
QPushButton {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: bold;
    color: {TEXT_COLOR};
}}
QPushButton:hover {{
    background-color: #2A233D;
    border-color: {ACCENT_BLUE};
}}
QPushButton:pressed {{
    background-color: {ACCENT_BLUE};
    color: #FFFFFF;
}}
QComboBox {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: bold;
    color: {TEXT_COLOR};
}}
QComboBox:hover {{
    border-color: {ACCENT_PURPLE};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {ACCENT_PURPLE};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {PANEL_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 4px;
    color: {TEXT_COLOR};
    selection-background-color: {ACCENT_PURPLE};
    selection-color: #FFFFFF;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    min-height: 28px;
    padding: 6px 10px;
    border-radius: 4px;
    color: {TEXT_COLOR};
    background-color: transparent;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {CARD_BG};
    color: {ACCENT_BLUE};
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {ACCENT_PURPLE};
    color: #FFFFFF;
}}
QScrollBar:vertical {{
    background: {PANEL_BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {CARD_BG};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT_PURPLE};
}}
QSlider::groove:horizontal {{
    height: 6px;
    background: {CARD_BG};
    border-radius: 3px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT_BLUE};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: #FFFFFF;
    border: 2px solid {ACCENT_BLUE};
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}}
"""

class KeyboardCanvas(QWidget):
    """Interactive 2D render of the URX Core75 layout."""
    def __init__(self, layout: KeyboardLayout, parent=None):
        super().__init__(parent)
        self.layout_data = layout
        self.setMinimumSize(820, 290)
        self.key_rects: Dict[int, QRectF] = {}

        # Visual animation state
        self.base_color = QColor(255, 0, 254)
        self.crest_color = QColor(30, 144, 255)
        self.ripples: List[Dict[str, float]] = []

        # 40 FPS GUI Animation Timer
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_frame)
        self.anim_timer.start(25)

    def trigger_visual_ripple(self, led_idx: int):
        self.ripples.append({
            'led': led_idx,
            'start': time.monotonic(),
            'duration': 0.72,
            'radius': 2.6
        })
        if len(self.ripples) > 16:
            self.ripples.pop(0)

    def _animate_frame(self):
        now = time.monotonic()
        active = [r for r in self.ripples if now - r['start'] < r['duration']]
        if len(active) != len(self.ripples) or active:
            self.ripples = active
            self.update()

    def mousePressEvent(self, event):
        pos = event.position()
        for led_idx, rect in self.key_rects.items():
            if rect.contains(pos):
                self.trigger_visual_ripple(led_idx)
                # Dispatch to physical hardware via IPC
                IpcClient.send_command({"action": "trigger_ripple", "led": led_idx})
                break

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background chassis
        chassis_rect = QRectF(10, 10, self.width() - 20, self.height() - 20)
        painter.setPen(QPen(QColor(BORDER_COLOR), 2))
        painter.setBrush(QBrush(QColor("#110D1A")))
        painter.drawRoundedRect(chassis_rect, 14, 14)

        # Calculate unit scale
        unit_w = (self.width() - 50) / 16.0
        unit_h = (self.height() - 50) / 6.0
        scale = min(unit_w, unit_h)
        offset_x = 24
        offset_y = 24

        now = time.monotonic()
        self.key_rects.clear()

        for led_id, key in self.layout_data.keys.items():
            x = offset_x + (key.x - key.width / 2.0) * scale
            y = offset_y + (key.y - key.height / 2.0) * scale
            w = key.width * scale - 2.5
            h = key.height * scale - 2.5
            rect = QRectF(x, y, w, h)
            self.key_rects[led_id] = rect

            # Calculate color from ripples
            final_col = QColor(self.base_color)
            total_alpha = 0.0

            for r in self.ripples:
                age = now - r['start']
                p = age / r['duration']
                rad = r['radius'] * math.sqrt(p)
                dist = self.layout_data.distance(r['led'], led_id)
                diff = abs(dist - rad)
                if diff <= 1.5:
                    intensity = math.exp(-(diff * diff) / 0.4) * (math.cos(0.5 * math.pi * p) ** 2)
                    if intensity > 0.02:
                        total_alpha = min(0.95, total_alpha + intensity * (1.0 - total_alpha))

            if total_alpha > 0:
                # Lerp towards crest
                r_val = int(self.base_color.red() * (1 - total_alpha) + self.crest_color.red() * total_alpha)
                g_val = int(self.base_color.green() * (1 - total_alpha) + self.crest_color.green() * total_alpha)
                b_val = int(self.base_color.blue() * (1 - total_alpha) + self.crest_color.blue() * total_alpha)
                final_col = QColor(r_val, g_val, b_val)

            # Draw keycap
            painter.setPen(QPen(QColor("#2B2238"), 1))
            painter.setBrush(QBrush(final_col))
            painter.drawRoundedRect(rect, 4, 4)

            # Key label
            painter.setPen(QColor("#FFFFFF" if total_alpha > 0.4 else "#D6CEE0"))
            painter.setFont(QFont("Inter", max(7, int(scale * 0.22)), QFont.Weight.Bold))
            label = key.name.replace("KC_", "")
            if len(label) > 5:
                label = label[:4] + "."
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smoky Velvet Studio 🌌✨")
        self.setMinimumSize(920, 680)
        self.setStyleSheet(STYLE_SHEET)

        # Load layout
        layout_path = Path(__file__).parent / "hardware" / "layouts" / "URX_Core75_VIA.json"
        self.keyboard_layout = KeyboardLayout.load_from_via_json(layout_path)

        # Profile manager
        self.profile_mgr = ProfileManager()

        self._init_ui()
        self._refresh_status()

        # Polling status timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._refresh_status)
        self.status_timer.start(2000)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        title_label = QLabel("SMOKY VELVET STUDIO")
        title_label.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {ACCENT_BLUE}; letter-spacing: 1px;")

        self.status_pill = QLabel("● CONNECTED")
        self.status_pill.setStyleSheet("color: #10B981; font-weight: bold; background: #064E3B; border-radius: 6px; padding: 4px 8px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_pill)
        main_layout.addLayout(header_layout)

        # 2. Interactive Canvas
        self.canvas = KeyboardCanvas(self.keyboard_layout, self)
        main_layout.addWidget(self.canvas)

        # 3. Control Panels
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(16)

        # Left: Profiles & Presets
        profile_group = QGroupBox("Lighting Profiles")
        prof_vbox = QVBoxLayout(profile_group)
        prof_vbox.setSpacing(12)

        self.profile_combo = QComboBox()
        self.profile_combo.setView(QListView())
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)
        prof_vbox.addWidget(QLabel("Active Profile:"))
        prof_vbox.addWidget(self.profile_combo)

        btn_row = QHBoxLayout()
        self.btn_cyan = QPushButton("Cyan Synth")
        self.btn_cyan.clicked.connect(lambda: self._select_profile("smoky_cyan"))
        self.btn_sapphire = QPushButton("Electric Sapphire")
        self.btn_sapphire.clicked.connect(lambda: self._select_profile("electric_sapphire"))
        btn_row.addWidget(self.btn_sapphire)
        btn_row.addWidget(self.btn_cyan)
        prof_vbox.addLayout(btn_row)

        btn_row2 = QHBoxLayout()
        self.btn_coral = QPushButton("Hot Coral")
        self.btn_coral.clicked.connect(lambda: self._select_profile("hot_coral"))
        self.btn_amber = QPushButton("Honey Amber")
        self.btn_amber.clicked.connect(lambda: self._select_profile("honey_amber"))
        btn_row2.addWidget(self.btn_coral)
        btn_row2.addWidget(self.btn_amber)
        prof_vbox.addLayout(btn_row2)

        controls_layout.addWidget(profile_group, 1)

        # Middle: Colors
        color_group = QGroupBox("Custom Palette Tuning")
        color_vbox = QVBoxLayout(color_group)
        color_vbox.setSpacing(10)

        # Base color button
        self.btn_base_color = QPushButton("Edit Velvet Base Color")
        self.btn_base_color.clicked.connect(self._pick_base_color)
        color_vbox.addWidget(self.btn_base_color)

        # Wave crest button
        self.btn_crest_color = QPushButton("Edit Wave Crest Color")
        self.btn_crest_color.clicked.connect(self._pick_crest_color)
        color_vbox.addWidget(self.btn_crest_color)

        # Test wave button
        self.btn_test_wave = QPushButton("⚡ Trigger Keyboard Ripple")
        self.btn_test_wave.setStyleSheet(f"background-color: {ACCENT_PURPLE}; color: white;")
        self.btn_test_wave.clicked.connect(lambda: self._trigger_center_ripple())
        color_vbox.addWidget(self.btn_test_wave)

        controls_layout.addWidget(color_group, 1)

        # Right: Sliders
        slider_group = QGroupBox("Hardware Brightness & Dynamics")
        slider_vbox = QVBoxLayout(slider_group)
        slider_vbox.setSpacing(8)

        # Brightness
        slider_vbox.addWidget(QLabel("Brightness:"))
        self.slider_bright = QSlider(Qt.Orientation.Horizontal)
        self.slider_bright.setRange(5, 100)
        self.slider_bright.setValue(100)
        self.slider_bright.valueChanged.connect(self._on_brightness_changed)
        slider_vbox.addWidget(self.slider_bright)

        # Toggle reactive
        self.btn_toggle_reactive = QPushButton("Toggle Ripple Effect (ON)")
        self.btn_toggle_reactive.clicked.connect(self._toggle_reactive)
        slider_vbox.addWidget(self.btn_toggle_reactive)

        # Hardware mode toggle
        self.btn_toggle_mode = QPushButton("🎛️ Onboard RGB Presets (No Flicker)")
        self.btn_toggle_mode.clicked.connect(self._toggle_mode)
        slider_vbox.addWidget(self.btn_toggle_mode)

        # Volume HUD test
        self.btn_test_vol = QPushButton("🔊 Test F1–F12 Volume HUD")
        self.btn_test_vol.clicked.connect(self._test_volume_hud)
        slider_vbox.addWidget(self.btn_test_vol)

        controls_layout.addWidget(slider_group, 1)

        main_layout.addLayout(controls_layout)

        # Populate profile combo
        self._populate_profiles()

    def _trigger_center_ripple(self):
        self.canvas.trigger_visual_ripple(38)
        IpcClient.send_command({"action": "trigger_ripple", "led": 38})

    def _populate_profiles(self):
        resp = IpcClient.send_command({"action": "list_profiles"})
        if resp.get("status") == "ok":
            profiles = resp.get("profiles", [])
            active = resp.get("active", "electric_sapphire")
            self.profile_combo.blockSignals(True)
            self.profile_combo.clear()
            for p in profiles:
                self.profile_combo.addItem(p)
            self.profile_combo.setCurrentText(active)
            self.profile_combo.blockSignals(False)

    def _select_profile(self, name: str):
        self.profile_combo.setCurrentText(name)

    def _on_profile_selected(self, idx: int):
        name = self.profile_combo.currentText()
        if name:
            IpcClient.send_command({"action": "set_profile", "name": name})
            self._sync_canvas_colors(name)

    def _sync_canvas_colors(self, prof_name: str):
        prof = self.profile_mgr.get_profile(prof_name)
        if prof:
            self.canvas.base_color = QColor(prof.base_color.r, prof.base_color.g, prof.base_color.b)
            self.canvas.crest_color = QColor(prof.reactive_crest_color.r, prof.reactive_crest_color.g, prof.reactive_crest_color.b)
            self.canvas.update()

    def _on_brightness_changed(self, val: int):
        float_val = val / 100.0
        IpcClient.send_command({"action": "set_brightness", "value": float_val})

    def _toggle_reactive(self):
        resp = IpcClient.send_command({"action": "toggle_reactive"})
        if resp.get("status") == "ok":
            enabled = resp.get("reactive_enabled", True)
            self.btn_toggle_reactive.setText(f"Toggle Ripple Effect ({'ON' if enabled else 'OFF'})")

    def _toggle_mode(self):
        resp = IpcClient.send_command({"action": "toggle_mode"})
        self._refresh_status()

    def _test_volume_hud(self):
        IpcClient.send_command({"action": "volume"})

    def _pick_base_color(self):
        col = QColorDialog.getColor(self.canvas.base_color, self, "Select Velvet Base Color")
        if col.isValid():
            self.canvas.base_color = col
            self.canvas.update()
            # Save into current active profile
            active = self.profile_combo.currentText()
            prof = self.profile_mgr.get_profile(active)
            if prof:
                prof.base_color_hex = col.name()
                self.profile_mgr.save_profile(prof)
                IpcClient.send_command({"action": "set_profile", "name": active})

    def _pick_crest_color(self):
        col = QColorDialog.getColor(self.canvas.crest_color, self, "Select Wave Crest Color")
        if col.isValid():
            self.canvas.crest_color = col
            self.canvas.update()
            active = self.profile_combo.currentText()
            prof = self.profile_mgr.get_profile(active)
            if prof:
                prof.reactive_crest_color_hex = col.name()
                self.profile_mgr.save_profile(prof)
                IpcClient.send_command({"action": "set_profile", "name": active})

    def _refresh_status(self):
        resp = IpcClient.send_command({"action": "status"})
        if resp.get("status") == "ok":
            data = resp.get("data", {})
            hw_mode = data.get("hardware_mode", False)
            if hw_mode:
                self.status_pill.setText("● HARDWARE PRESETS (No Flicker)")
                self.status_pill.setStyleSheet("color: #F59E0B; font-weight: bold; background: #78350F; border-radius: 6px; padding: 4px 8px;")
                self.btn_toggle_mode.setText("✨ Re-engage Smoky Velvet")
            else:
                self.status_pill.setText(f"● CONNECTED ({data.get('device_name')})")
                self.status_pill.setStyleSheet("color: #10B981; font-weight: bold; background: #064E3B; border-radius: 6px; padding: 4px 8px;")
                self.btn_toggle_mode.setText("🎛️ Onboard RGB Presets (No Flicker)")

            active = data.get("active_profile", "")
            if active and self.profile_combo.currentText() != active:
                self.profile_combo.blockSignals(True)
                self.profile_combo.setCurrentText(active)
                self.profile_combo.blockSignals(False)
                self._sync_canvas_colors(active)
        else:
            self.status_pill.setText("● DISCONNECTED")
            self.status_pill.setStyleSheet("color: #EF4444; font-weight: bold; background: #450A0A; border-radius: 6px; padding: 4px 8px;")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
