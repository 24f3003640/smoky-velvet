# Smoky Velvet: Master Project Specification

*(Derived from the official specification document for Smoky Velvet.)*

## 1. Project Overview
- **Project Name:** Smoky Velvet
- **Type:** Cross-platform desktop RGB control and customization application
- **Primary Hardware:** URX Core75 — Smoky Black (81 LEDs verified, QMK/VIA-compatible)
- **Primary Development OS:** EndeavourOS Linux (Hyprland + Caelestia / Quickshell)
- **Secondary OS:** Windows
- **Core Hardware Interface:** OpenRGB SDK protocol via ColorHoster bridge (`127.0.0.1:6742`)
- **Development Approach:** Research → Hardware Validation → Polished V1 → Incremental Expansion

## 2. Core Principles
1. **Device Reusability:** Core75 is the primary target; the lighting engine must be reusable with other OpenRGB devices.
2. **First-Class Desktop Integrations without Lock-in:** Hyprland and Caelestia integrations are optional plugins; the core app runs standalone across Linux and Windows.
3. **Application-Owned Effects Engine:** The app owns all rendering, composition, layers, profiles, and reactive math; OpenRGB/ColorHoster is strictly a transport pipe.
4. **Hardware Safety:** No firmware modifications required. Rate-limited updates to prevent VIA buffer exhaustion.
