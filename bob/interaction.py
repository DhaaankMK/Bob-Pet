"""
interaction.py - Gerenciador de interações do Bob (v2)
Mouse tracking melhorado, chase configurável, interação com janelas (opcional).
"""

import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import math
import time
from PyQt6.QtCore import QPoint

# Interação com janelas do Windows (opcional)
WIN32_OK = False
if sys.platform == "win32":
    try:
        import win32gui
        import win32con
        import win32api
        WIN32_OK = True
    except ImportError:
        pass


class InteractionHandler:
    """
    Centraliza interações do Bob com mouse e sistema operacional.
    """

    def __init__(self, settings: dict):
        self.chase_cursor: bool      = bool(settings.get("chase_cursor", False))
        self.react_to_proximity: bool= bool(settings.get("react_to_mouse_proximity", True))
        self.proximity_radius: float = float(settings.get("mouse_proximity_radius", 150))
        self.interact_with_windows: bool = bool(settings.get("interact_with_windows", False))

        # Estado de arrastar
        self.is_dragging: bool     = False
        self.drag_offset: QPoint   = QPoint(0, 0)
        self.last_drag_pos: QPoint = QPoint(0, 0)
        self.drag_vx: float        = 0.0
        self.drag_vy: float        = 0.0
        self._prev_time: float     = time.time()

        # Cursor
        self.cursor_x: float = 0.0
        self.cursor_y: float = 0.0
        self.near_cursor: bool = False

        # Callbacks
        self.on_click_callback     = None
        self.on_drag_start_callback= None
        self.on_drag_end_callback  = None
        self.on_proximity_callback = None

        # Estado de interação com janelas
        self._window_interact_timer: float = 0.0
        self._sitting_on_hwnd: int         = 0

    def update_cursor(self, cx: float, cy: float,
                      bx: float, by: float, bw: float, bh: float):
        """Atualiza posição do cursor e checa proximidade."""
        self.cursor_x = cx
        self.cursor_y = cy

        bob_cx = bx + bw / 2
        bob_cy = by + bh / 2
        dist   = math.hypot(cx - bob_cx, cy - bob_cy)

        was_near       = self.near_cursor
        self.near_cursor = (dist < self.proximity_radius)

        if self.near_cursor and not was_near and self.on_proximity_callback:
            self.on_proximity_callback(dist)

    def get_chase_direction(self, bx: float, by: float,
                             bw: float, bh: float) -> tuple:
        """Direção normalizada para perseguir o cursor."""
        bob_cx = bx + bw / 2
        bob_cy = by + bh / 2
        dx     = self.cursor_x - bob_cx
        dy     = self.cursor_y - bob_cy
        dist   = math.hypot(dx, dy)
        if dist < 8:
            return 0.0, 0.0
        return dx / dist, dy / dist

    # ── Eventos de Mouse ──────────────────────────────────────────────────────

    def on_mouse_press(self, event_pos: QPoint, global_pos: QPoint) -> bool:
        self.is_dragging   = True
        self.drag_offset   = event_pos
        self.last_drag_pos = global_pos
        self.drag_vx       = 0.0
        self.drag_vy       = 0.0
        self._prev_time    = time.time()
        if self.on_drag_start_callback:
            self.on_drag_start_callback()
        return True

    def on_mouse_move(self, global_pos: QPoint) -> QPoint:
        if not self.is_dragging:
            return global_pos
        now = time.time()
        dt  = now - self._prev_time
        if dt > 0.001:
            dx = global_pos.x() - self.last_drag_pos.x()
            dy = global_pos.y() - self.last_drag_pos.y()
            alpha         = 0.38
            self.drag_vx  = self.drag_vx * (1 - alpha) + (dx / dt) * alpha
            self.drag_vy  = self.drag_vy * (1 - alpha) + (dy / dt) * alpha
        self.last_drag_pos = global_pos
        self._prev_time    = now
        return QPoint(
            global_pos.x() - self.drag_offset.x(),
            global_pos.y() - self.drag_offset.y(),
        )

    def on_mouse_release(self, global_pos: QPoint) -> tuple:
        if not self.is_dragging:
            return 0.0, 0.0
        self.is_dragging = False
        scale   = 0.075
        max_v   = 20.0
        vx = max(-max_v, min(max_v, self.drag_vx * scale))
        vy = max(-max_v, min(max_v, self.drag_vy * scale))
        if self.on_drag_end_callback:
            self.on_drag_end_callback(vx, vy)
        return vx, vy

    # ── Interação com Janelas (Windows) ───────────────────────────────────────

    def get_window_under_bob(self, bx: float, by: float, bw: float) -> int:
        """
        Retorna o HWND da janela que está logo abaixo do Bob.
        Retorna 0 se não encontrar ou se a funcionalidade estiver desativada.
        """
        if not WIN32_OK or not self.interact_with_windows:
            return 0
        try:
            # Ponto central abaixo do Bob
            px = int(bx + bw / 2)
            py = int(by + 5)  # alguns pixels abaixo do Bob
            hwnd = win32gui.WindowFromPoint((px, py))
            if hwnd and win32gui.IsWindowVisible(hwnd):
                return hwnd
        except Exception:
            pass
        return 0

    def try_sit_on_window(self, bx: float, by: float, bh: float) -> tuple:
        """
        Tenta sentar Bob no topo de uma janela.
        Retorna (new_y, hwnd) ou (None, 0) se não encontrar.
        """
        if not WIN32_OK or not self.interact_with_windows:
            return None, 0
        try:
            px = int(bx + 50)
            py = int(by + bh + 10)
            hwnd = win32gui.WindowFromPoint((px, py))
            if hwnd and hwnd != win32gui.GetDesktopWindow():
                rect = win32gui.GetWindowRect(hwnd)
                window_top = rect[1]
                new_y = window_top - bh
                return float(new_y), hwnd
        except Exception:
            pass
        return None, 0

    def push_window(self, hwnd: int, dx: int):
        """Empurra uma janela para o lado (para diversão)."""
        if not WIN32_OK or not hwnd:
            return
        try:
            rect = win32gui.GetWindowRect(hwnd)
            new_x = rect[0] + dx
            win32gui.MoveWindow(hwnd, new_x, rect[1],
                                 rect[2] - rect[0], rect[3] - rect[1], True)
        except Exception:
            pass

    def update_settings(self, settings: dict):
        self.chase_cursor         = bool(settings.get("chase_cursor", self.chase_cursor))
        self.react_to_proximity   = bool(settings.get("react_to_mouse_proximity", self.react_to_proximity))
        self.proximity_radius     = float(settings.get("mouse_proximity_radius", self.proximity_radius))
        self.interact_with_windows= bool(settings.get("interact_with_windows", self.interact_with_windows))
