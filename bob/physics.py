"""
physics.py - Motor de física do Bob (v2)
Gravidade, colisão com bordas, pulo, queda, velocidade ajustável.
"""

import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import math
from PyQt6.QtWidgets import QApplication


class PhysicsEngine:
    """Motor de física 2D para o Bob."""

    def __init__(self, settings: dict):
        self.x: float = 100.0
        self.y: float = 100.0
        self.vx: float = 0.0
        self.vy: float = 0.0

        self.gravity: float          = float(settings.get("gravity", 0.55))
        self.terminal_velocity: float= float(settings.get("terminal_velocity", 18.0))
        self.jump_force: float       = float(settings.get("jump_force", -14.0))
        self.friction: float         = float(settings.get("friction", 0.82))
        self.speed: float            = float(settings.get("speed", 4.0))
        self.bounce_on_edges: bool   = bool(settings.get("bounce_on_edges", True))
        self.physics_enabled: bool   = bool(settings.get("physics_enabled", True))

        self.on_ground: bool    = False
        self.is_dragging: bool  = False
        self.bob_width: int     = int(settings.get("bob_size", 100) * 1.8)
        self.bob_height: int    = int(settings.get("bob_size", 100) * 2.5)

        self._update_screen_bounds()

    def _update_screen_bounds(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.screen_w = geo.width()
            self.screen_h = geo.height()
            self.screen_x = geo.x()
            self.screen_y = geo.y()
        else:
            self.screen_w = 1920
            self.screen_h = 1080
            self.screen_x = 0
            self.screen_y = 0

    def update(self, dt: float = 1.0):
        if not self.physics_enabled or self.is_dragging:
            return

        self.vy += self.gravity * dt
        self.vy = min(self.vy, self.terminal_velocity)

        self.x += self.vx * dt
        self.y += self.vy * dt

        self.vx *= self.friction

        if abs(self.vx) < 0.08:
            self.vx = 0.0

        self._handle_collisions()

    def _handle_collisions(self):
        self._update_screen_bounds()

        ground_y = float(self.screen_y + self.screen_h - self.bob_height)
        if self.y >= ground_y:
            self.y = ground_y
            if self.bounce_on_edges and abs(self.vy) > 2.5:
                self.vy *= -0.38
            else:
                self.vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

        if self.y < float(self.screen_y):
            self.y = float(self.screen_y)
            self.vy = abs(self.vy) * 0.3

        if self.x < float(self.screen_x):
            self.x = float(self.screen_x)
            self.vx = abs(self.vx) * (0.5 if self.bounce_on_edges else 0.0)

        right_limit = float(self.screen_x + self.screen_w - self.bob_width)
        if self.x > right_limit:
            self.x = right_limit
            self.vx = -abs(self.vx) * (0.5 if self.bounce_on_edges else 0.0)

    def jump(self):
        if self.on_ground:
            self.vy = self.jump_force
            self.on_ground = False
            return True
        return False

    def walk_left(self):
        self.vx = -self.speed

    def walk_right(self):
        self.vx = self.speed

    def throw(self, vx: float, vy: float):
        self.vx = max(-22.0, min(22.0, vx))
        self.vy = max(-22.0, min(22.0, vy))

    def teleport(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0

    def apply_force(self, fx: float, fy: float):
        self.vx += fx
        self.vy += fy

    def set_gravity(self, v: float):
        self.gravity = max(0.0, float(v))

    def set_speed(self, v: float):
        self.speed = max(0.5, float(v))

    def set_physics_enabled(self, e: bool):
        self.physics_enabled = bool(e)
        if not e:
            self.vx = 0.0
            self.vy = 0.0

    def update_settings(self, s: dict):
        self.gravity          = float(s.get("gravity", self.gravity))
        self.terminal_velocity= float(s.get("terminal_velocity", self.terminal_velocity))
        self.jump_force       = float(s.get("jump_force", self.jump_force))
        self.friction         = float(s.get("friction", self.friction))
        self.speed            = float(s.get("speed", self.speed))
        self.bounce_on_edges  = bool(s.get("bounce_on_edges", self.bounce_on_edges))
        self.physics_enabled  = bool(s.get("physics_enabled", self.physics_enabled))

    def get_state(self) -> dict:
        return {
            "x": self.x, "y": self.y,
            "vx": self.vx, "vy": self.vy,
            "on_ground": self.on_ground,
            "is_dragging": self.is_dragging,
        }
