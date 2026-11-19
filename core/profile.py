"""
Profile models and configuration manager.
Handles profile serialization, JSON loading/saving, and OS-portable configuration.
"""
from __future__ import annotations
import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.color import Color, MIDNIGHT_PURPLE

logger = logging.getLogger(__name__)

CURRENT_PROFILE_VERSION = 1

@dataclass
class Profile:
    name: str
    description: str
    version: int = CURRENT_PROFILE_VERSION
    base_color_hex: str = "#30183F"
    brightness: float = 1.0
    reactive_enabled: bool = True
    reactive_duration: float = 0.8
    reactive_max_radius: float = 5.0
    reactive_wave_thickness: float = 1.5
    custom_key_colors: Dict[str, str] = field(default_factory=dict)
    workspace_bindings: Dict[str, str] = field(default_factory=dict)
    app_rules: Dict[str, str] = field(default_factory=dict)

    @property
    def base_color(self) -> Color:
        return Color.from_hex(self.base_color_hex)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Profile:
        return cls(
            name=data.get("name", "Custom"),
            description=data.get("description", ""),
            version=data.get("version", CURRENT_PROFILE_VERSION),
            base_color_hex=data.get("base_color_hex", "#30183F"),
            brightness=float(data.get("brightness", 1.0)),
            reactive_enabled=bool(data.get("reactive_enabled", True)),
            reactive_duration=float(data.get("reactive_duration", 0.8)),
            reactive_max_radius=float(data.get("reactive_max_radius", 5.0)),
            reactive_wave_thickness=float(data.get("reactive_wave_thickness", 1.5)),
            custom_key_colors=data.get("custom_key_colors", {}),
            workspace_bindings=data.get("workspace_bindings", {}),
            app_rules=data.get("app_rules", {})
        )


class ProfileManager:
    def __init__(self, profiles_dir: Optional[Path] = None):
        if profiles_dir is None:
            self.profiles_dir = Path(__file__).parent.parent / "profiles"
        else:
            self.profiles_dir = Path(profiles_dir)

        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, Profile] = {}
        self.active_profile_name: str = "smoky_velvet"
        self._ensure_default_profiles()
        self.load_all()

    def _ensure_default_profiles(self) -> None:
        defaults = {
            "smoky_velvet": Profile(
                name="smoky_velvet",
                description="Signature Velvet profile with Midnight Purple and Liquid Antique Gold ripple.",
                base_color_hex="#30183F",
                brightness=1.0,
                reactive_enabled=True,
                reactive_duration=0.8,
                reactive_max_radius=5.0
            ),
            "coding": Profile(
                name="coding",
                description="Refined dark violet underglow with fast, localized gold ripples.",
                base_color_hex="#220D30",
                brightness=0.85,
                reactive_enabled=True,
                reactive_duration=0.5,
                reactive_max_radius=3.5
            ),
            "study": Profile(
                name="study",
                description="Distraction-free static velvet illumination with animations disabled.",
                base_color_hex="#1E1026",
                brightness=0.6,
                reactive_enabled=False
            ),
            "gaming": Profile(
                name="gaming",
                description="High intensity purple base with large high-velocity splash waves.",
                base_color_hex="#481861",
                brightness=1.0,
                reactive_enabled=True,
                reactive_duration=0.6,
                reactive_max_radius=7.0
            ),
            "night": Profile(
                name="night",
                description="Subtle ultra-low brightness ambient underglow for dark environments.",
                base_color_hex="#1A0C22",
                brightness=0.25,
                reactive_enabled=False
            )
        }

        for name, prof in defaults.items():
            path = self.profiles_dir / f"{name}.json"
            if not path.exists():
                self.save_profile(prof)

    def load_all(self) -> None:
        self.profiles.clear()
        for p in self.profiles_dir.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    prof = Profile.from_dict(data)
                    self.profiles[prof.name] = prof
            except Exception as e:
                logger.error(f"Error loading profile {p.name}: {e}")

    def get_profile(self, name: str) -> Optional[Profile]:
        return self.profiles.get(name)

    def get_active_profile(self) -> Profile:
        return self.profiles.get(self.active_profile_name, self.profiles.get("smoky_velvet")) # type: ignore

    def save_profile(self, profile: Profile) -> None:
        self.profiles[profile.name] = profile
        path = self.profiles_dir / f"{profile.name}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2)

    def set_active(self, name: str) -> bool:
        if name in self.profiles:
            self.active_profile_name = name
            return True
        return False
