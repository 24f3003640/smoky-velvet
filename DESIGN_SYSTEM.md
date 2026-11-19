# Smoky Velvet Design System & Color Identity

## 1. Visual Identity
Smoky Velvet is designed around the translucent smoky-black chassis and dark charcoal keycaps of the URX Core75. The aesthetic prioritizes refined, atmospheric luxury over aggressive RGB gaming presets.

---

## 2. Signature Color Palette

### Base Illumination: Midnight Purple
- **HEX:** `#30183F`
- **RGB:** `(48, 24, 63)`
- **KaTeX / Normalized:** `(0.188, 0.094, 0.247)`
- **Behavior:** The foundational static underglow. Maintained continuously when idle and restored seamlessly after transient animations conclude.

### Signature Reactive Sequence: Liquid Antique Gold
The reactive ripple transitions organically through four warm gold stops:

| Stage | Name | HEX | RGB | Normalized | Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0** | **Champagne Glow** | `#FFE6A3` | `(255, 230, 163)` | `(1.00, 0.902, 0.639)` | Intense impact epicenter |
| **1** | **Warm Gold** | `#E5C477` | `(229, 196, 119)` | `(0.898, 0.769, 0.467)` | Inner crest transition |
| **2** | **Antique Gold** | `#C49A45` | `(196, 154, 69)` | `(0.769, 0.604, 0.271)` | Main expanding wave body |
| **3** | **Deep Old Gold** | `#986B2D` | `(152, 107, 45)` | `(0.596, 0.420, 0.176)` | Trailing dissipated edge |

---

## 3. Liquid Gold Ripple Physics
The signature ripple is calculated using Euclidean distance from the triggering key $(x_0, y_0)$ to all keyboard LEDs $(x_i, y_i)$:

$$d_i = \sqrt{(x_i - x_0)^2 + (y_i - y_0)^2}$$

### Dynamic Parameters
- **Total Duration ($T$):** 800 ms
- **Expansion Phase ($T_{\text{exp}}$):** 550 ms
- **Dissipation Phase ($T_{\text{fade}}$):** 250 ms
- **Maximum Ripple Radius ($R_{\text{max}}$):** 5.0 key units
- **Wavefront Thickness ($W$):** 1.5 key units
- **Wave Velocity ($v$):** $R_{\text{max}} / T_{\text{exp}}$

### Blending Model
At any timestamp $t \in [0, T]$, the intensity contribution $I_i(t)$ of key $i$ is evaluated by Gaussian falloff around the propagating radius $r(t) = v \cdot t$:

$$I_i(t) = \exp\left(-\frac{(d_i - r(t))^2}{2\sigma^2}\right) \cdot \left(1 - \frac{t}{T}\right)$$

Multiple keypresses produce independent ripple instances which are composited additively or via maximum luminance blending onto the base layer before clipping to $[0, 255]$.
