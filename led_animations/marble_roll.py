"""
MarbleRollAnimation - Physics-based marble rolling animation reactive to accelerometer.

This module provides a custom animation that simulates a marble rolling inside
an acrylic tube (the LED strip), reacting to the accelerometer to determine
gravity along the strip. The animation exposes a `lightsaber_state` property
which must be set by the caller before each draw.
"""

import math
from lib.adafruit_led_animation.animation import Animation
from lib.adafruit_led_animation.color import BLACK
from lib.adafruit_led_animation import monotonic_ms


class MarbleRollAnimation(Animation):
    """
    Simulate a marble rolling along the LED strip under gravity, with wall bounces.

    Parameters:
    - pixel_object: Initialized LED object
    - float speed: Animation update period in seconds (how often draw runs)
    - background_color: Background color (r, g, b) or 0xRRGGBB, defaults to BLACK
    - marble_color: Marble color (r, g, b) or 0xRRGGBB
    - float marble_diameter_mm: Diameter of the marble in millimeters
    - float pixel_width_mm: Physical spacing of LEDs in millimeters
    - float gravity: Gravitational acceleration magnitude (e.g. 9.81)
    - float floor_friction: Linear damping factor (N·s/m) for rolling friction
    - float mass: Mass of the marble in kilograms

    Notes:
    - The caller must set `animation.lightsaber_state = LightsaberState` before each draw.
      The state should provide `cached_acceleration` as a tuple (ax, ay, az) in m/s^2.
    - Gravity along the strip is derived from the accelerometer Z-axis by default.
      If your strip is aligned with a different axis, set `axis_index` accordingly
      after construction (0 for X, 1 for Y, 2 for Z).
    """

    def __init__(
        self,
        pixel_object,
        speed,
        marble_color,
        marble_diameter_mm,
        pixel_width_mm,
        gravity,
        floor_friction,
        mass,
        background_color=BLACK,
        name=None,
    ):
        # The base Animation accepts a color; we use marble_color as the primary color.
        super().__init__(pixel_object, speed, marble_color, name=name)

        # Rendering parameters
        self.background_color = background_color
        self.marble_color = self._color

        # Physical parameters
        self.pixel_width_mm = float(pixel_width_mm)
        self.marble_diameter_mm = float(marble_diameter_mm)
        self.gravity = float(gravity)
        self.floor_friction = float(floor_friction)
        self.mass = float(mass) if mass > 0 else 1.0

        # Strip geometry
        self._num_pixels = len(pixel_object)
        self._strip_length_mm = self._num_pixels * self.pixel_width_mm

        # State that caller must set prior to draw
        self.lightsaber_state = None

        # Motion state (1D along strip)
        self._position_mm = 0.5 * self._strip_length_mm
        self._velocity_mm_s = 0.0
        self._last_time_ms = None
        # High-pass filter state (implemented via low-pass baseline)
        self._axis_lowpass_m_s2 = 0.0
        self._hp_time_constant_s = 0.15  # Tunable: higher = slower baseline, more relative response

        # Tube axis direction in device coordinates as a unit vector (defaults to +Y).
        # This defines which way along the pixels is considered "down the tube" when tilted.
        self.tube_axis_unit = (0.0, 1.0, 0.0)

        # Coefficient for bounce energy loss derived from friction (clamped)
        # 0 → perfectly inelastic, 1 → perfectly elastic
        self._bounce_restitution = max(0.0, min(1.0, 1.0 - (self.floor_friction / (self.floor_friction + 1.0))))

    def _now_ms(self):
        return monotonic_ms()

    def _get_accel_vector(self):
        """
        Obtain 3D acceleration vector (ax, ay, az) in m/s^2.
        Returns a tuple; if unavailable, returns (0.0, 0.0, 0.0).
        """
        if self.lightsaber_state is None:
            return 0.0, 0.0, 0.0
        acceleration = getattr(self.lightsaber_state, "cached_acceleration", None)
        if not acceleration:
            return 0.0, 0.0, 0.0
        try:
            ax = float(acceleration[0])
            ay = float(acceleration[1])
            az = float(acceleration[2])
            return ax, ay, az
        except Exception:
            return 0.0, 0.0, 0.0

    def _integrate_motion(self, dt_s):
        """
        Semi-implicit Euler integration for position and velocity in mm/s and mm.
        Forces: gravity component along strip + linear velocity damping (friction).
        """
        # Component of acceleration along strip (m/s^2).
        # Use low-pass gravity estimate to compute tilt along tube and high-pass for responsiveness.
        ax, ay, az = self._get_accel_vector()

        # Low-pass of each axis to estimate gravity direction/magnitude
        tau = max(1e-3, self._hp_time_constant_s)
        alpha = 1.0 - pow(2.718281828, -dt_s / tau)

        if not hasattr(self, '_g_lp'):
            self._g_lp = [ax, ay, az]
        else:
            self._g_lp[0] += alpha * (ax - self._g_lp[0])
            self._g_lp[1] += alpha * (ay - self._g_lp[1])
            self._g_lp[2] += alpha * (az - self._g_lp[2])

        # High-pass (delta) for quick changes
        if not hasattr(self, '_g_prev'):
            self._g_prev = [ax, ay, az]
        gx_hp = ax - self._g_prev[0]
        gy_hp = ay - self._g_prev[1]
        gz_hp = az - self._g_prev[2]
        self._g_prev = [ax, ay, az]

        # Normalize tube axis to a unit vector
        ux, uy, uz = self.tube_axis_unit
        norm_u = max(1e-6, math.sqrt(ux*ux + uy*uy + uz*uz))
        ux /= norm_u
        uy /= norm_u
        uz /= norm_u

        # Project gravity low-pass onto tube axis (positive meaning accelerating towards +axis)
        a_lp_along = -(self._g_lp[0] * ux + self._g_lp[1] * uy + self._g_lp[2] * uz)

        # Add a small portion of high-pass projection to improve responsiveness
        a_hp_along = -(gx_hp * ux + gy_hp * uy + gz_hp * uz)

        # Deadzone for hp noise
        if -0.05 < a_hp_along < 0.05:
            a_hp_along = 0.0

        # Combine: dominant low-pass (tilt gravity) + scaled high-pass
        a_axis_m_s2 = a_lp_along + 0.5 * a_hp_along

        # Convert to mm/s^2
        a_axis_mm_s2 = a_axis_m_s2 * 1000.0

        # Linear damping force proportional to velocity (N·s/m). Convert velocity to m/s first.
        v_m_s = self._velocity_mm_s / 1000.0
        damping_accel_m_s2 = -(self.floor_friction / max(self.mass, 1e-6)) * v_m_s
        damping_accel_mm_s2 = damping_accel_m_s2 * 1000.0

        # Net acceleration (mm/s^2)
        a_net_mm_s2 = a_axis_mm_s2 + damping_accel_mm_s2

        # Integrate velocity then position (semi-implicit Euler)
        self._velocity_mm_s += a_net_mm_s2 * dt_s
        self._position_mm += self._velocity_mm_s * dt_s

        # Marble boundaries based on center position and radius
        radius = 0.5 * self.marble_diameter_mm
        min_pos = radius
        max_pos = max(min_pos, self._strip_length_mm - radius)

        # Handle bounces against the ends (with restitution)
        if self._position_mm <= min_pos:
            self._position_mm = min_pos
            if self._velocity_mm_s < 0:
                self._velocity_mm_s = -self._velocity_mm_s * self._bounce_restitution
        elif self._position_mm >= max_pos:
            self._position_mm = max_pos
            if self._velocity_mm_s > 0:
                self._velocity_mm_s = -self._velocity_mm_s * self._bounce_restitution

    def _render(self):
        """
        Render the marble as a solid cylinder with sub-pixel blending at edges.
        """
        pixels = self.pixel_object
        num = self._num_pixels

        # Fill background
        pixels.fill(self.background_color)

        # Marble span in pixels
        center_px = self._position_mm / self.pixel_width_mm
        radius_px = max(0.0, 0.5 * (self.marble_diameter_mm / self.pixel_width_mm))
        start_px = center_px - radius_px
        end_px = center_px + radius_px

        # Draw with coverage-based blending
        r_m, g_m, b_m = self.marble_color
        r_b, g_b, b_b = self.background_color

        def blend(c_bg, c_fg, alpha):
            return int(c_bg + (c_fg - c_bg) * alpha)

        # The marble covers pixels from floor(start_px) to ceil(end_px)-1
        i_start = max(0, int(math.floor(start_px)))
        i_end = min(num - 1, int(math.ceil(end_px)) - 1)

        for i in range(i_start, i_end + 1):
            # Pixel coverage from [i, i+1) intersect [start_px, end_px)
            left = max(i, start_px)
            right = min(i + 1, end_px)
            coverage = max(0.0, right - left)
            if coverage <= 0:
                continue
            # Normalize coverage to [0..1] by pixel width of 1 px
            alpha = max(0.0, min(1.0, coverage))
            r = blend(r_b, r_m, alpha)
            g = blend(g_b, g_m, alpha)
            b = blend(b_b, b_m, alpha)
            if 0 <= i < num:
                pixels[i] = (r, g, b)

    def draw(self):
        # Require caller to set lightsaber_state each frame
        now = self._now_ms()
        if self._last_time_ms is None:
            self._last_time_ms = now
            dt_s = 0.0
        else:
            dt_s = max(0.0, (now - self._last_time_ms) / 1000.0)
            self._last_time_ms = now

        # Integrate physics
        self._integrate_motion(dt_s)

        # Clamp position every frame to ensure visibility
        radius = 0.5 * self.marble_diameter_mm
        min_pos = radius
        max_pos = max(min_pos, self._strip_length_mm - radius)
        if self._position_mm < min_pos:
            self._position_mm = min_pos
        elif self._position_mm > max_pos:
            self._position_mm = max_pos

        # Render
        self._render()

    def reset(self):
        # Reset motion and timing
        self._last_time_ms = None
        self._velocity_mm_s = 0.0
        self._position_mm = 0.5 * self._strip_length_mm


