"""
bob/toys.py — Sistema de brinquedos (v2 estável)

Física 100% manual (sem pygame).
QTimer para o loop físico — sem travamento da UI.
try/except em todos os eventos de mouse e pintura.
"""
import sys
import math
import random
import platform
from pathlib import Path

_THIS = Path(__file__).resolve().parent.parent
if str(_THIS) not in sys.path:
    sys.path.insert(0, str(_THIS))

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore    import Qt, QTimer, QPoint
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen,
    QPainterPath, QRadialGradient, QLinearGradient
)

from PyQt6.QtCore import QPointF

from bob.paths import PATHS, asset_exists, asset_path


# ── Catálogo de brinquedos ────────────────────────────────────────────────────
TOYS_CATALOG = {
    "ball": {
        "name": "Bola", "emoji": "⚽",
        "description": "Uma bola colorida para quicar.",
        "color": "#E05050", "size": 40, "bounce": 0.68, "gravity": 0.6,
    },
    "cube": {
        "name": "Cubo", "emoji": "📦",
        "description": "Um cubo misterioso.",
        "color": "#50A0E0", "size": 40, "bounce": 0.28, "gravity": 0.72,
    },
    "star": {
        "name": "Estrela", "emoji": "⭐",
        "description": "Uma estrela brilhante.",
        "color": "#FFD700", "size": 38, "bounce": 0.52, "gravity": 0.28,
    },
    "food": {
        "name": "Pizza", "emoji": "🍕",
        "description": "Pizza! Bob vai adorar.",
        "color": "#F4A72A", "size": 36, "bounce": 0.18, "gravity": 0.82,
    },
    "doll": {
        "name": "Urso", "emoji": "🧸",
        "description": "Um ursinho fofo.",
        "color": "#D4A070", "size": 42, "bounce": 0.40, "gravity": 0.50,
    },
}


class ToyWidget(QWidget):
    """
    Widget de brinquedo individual.
    Física implementada manualmente — sem pygame, sem conflito de event loop.
    Loop físico via QTimer (não bloqueia a UI).
    """

    def __init__(self, toy_type: str, x: int, y: int, gravity: float = 0.55):
        super().__init__()
        self.toy_type = toy_type if toy_type in TOYS_CATALOG else "ball"
        self.cfg      = TOYS_CATALOG[self.toy_type]

        sz = self.cfg["size"]
        self.setFixedSize(sz + 12, sz + 12)

        # ── Estado físico ──
        self.px: float = float(x)
        self.py: float = float(y)
        self.vx: float = random.uniform(-3.5, 3.5)
        self.vy: float = random.uniform(-6.0, -1.5)

        self.gravity: float      = float(self.cfg.get("gravity", gravity))
        self.bounce_coef: float  = float(self.cfg.get("bounce", 0.5))
        self.friction: float     = 0.87
        self.rotation: float     = 0.0
        self.on_ground: bool     = False

        # ── Arrasto ──
        self.is_dragging: bool   = False
        self.drag_offset: QPoint = QPoint(0, 0)

        # ── Flags Qt ──
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.move(int(self.px), int(self.py))
        self.show()

        # ── Timer físico (~60fps via QTimer — não bloqueia UI) ──
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._physics_step)
        self._timer.start(16)

    # ── Física Manual ─────────────────────────────────────────────────────────

    def _physics_step(self):
        """
        Um tick de física.
        Chamado pelo QTimer a ~60fps sem travar a interface.
        Física completamente manual — sem pygame.
        """
        if self.is_dragging:
            return

        try:
            # ── Limites da tela ──
            screen = QApplication.primaryScreen()
            if screen is None:
                return
            geo = screen.availableGeometry()
            sw, sh = geo.width(), geo.height()
            sx, sy = geo.x(),    geo.y()

            # Gravidade (manual — velocity_y += gravity)
            self.vy += self.gravity
            self.vy  = min(self.vy, 22.0)  # terminal velocity

            # Atualiza posição (manual — pos += velocity)
            self.px += self.vx
            self.py += self.vy

            # Rotação visual
            self.rotation = (self.rotation + self.vx * 2.5) % 360

            # ── Colisão com chão ──
            bottom = float(sy + sh - self.height())
            if self.py >= bottom:
                self.py = bottom
                if abs(self.vy) > 1.5:
                    self.vy *= -self.bounce_coef
                else:
                    self.vy = 0.0
                self.vx *= self.friction
                self.on_ground = True
            else:
                self.on_ground = False

            # ── Colisão com topo ──
            if self.py < float(sy):
                self.py  = float(sy)
                self.vy  = abs(self.vy) * 0.3

            # ── Colisão com laterais ──
            if self.px < float(sx):
                self.px  = float(sx)
                self.vx  = abs(self.vx) * 0.55
            right = float(sx + sw - self.width())
            if self.px > right:
                self.px  = right
                self.vx  = -abs(self.vx) * 0.55

            # Para velocidades insignificantes
            if abs(self.vx) < 0.06:
                self.vx = 0.0

            self.move(int(self.px), int(self.py))
            self.update()

        except Exception as e:
            # Nunca deixa o timer crashar — silencia erros
            pass

    # ── Eventos de Mouse ──────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_dragging = True
                self.drag_offset = event.pos()
                self.vx = 0.0
                self.vy = 0.0
        except Exception:
            pass

    def mouseMoveEvent(self, event):
        try:
            if self.is_dragging:
                new_pos = event.globalPosition().toPoint() - self.drag_offset
                self.px = float(new_pos.x())
                self.py = float(new_pos.y())
                self.move(new_pos)
        except Exception:
            pass

    def mouseReleaseEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.is_dragging = False
                self.vx = random.uniform(-4, 4)
                self.vy = random.uniform(-8, -3)
        except Exception:
            pass

    # ── Pintura ───────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            s  = self.cfg["size"]
            cx = self.width()  // 2
            cy = self.height() // 2
            color = QColor(self.cfg["color"])

            p.translate(float(cx), float(cy))

            # Rotação apenas para ball e star
            if self.toy_type in ("ball", "star"):
                p.rotate(self.rotation)

            if   self.toy_type == "ball":  self._draw_ball(p, s, color)
            elif self.toy_type == "cube":  self._draw_cube(p, s, color)
            elif self.toy_type == "star":  self._draw_star(p, s, color)
            elif self.toy_type == "food":  self._draw_pizza(p, s, color)
            elif self.toy_type == "doll":  self._draw_doll(p, s, color)
            else:                          self._draw_ball(p, s, color)

        except Exception:
            pass
        finally:
            try:
                p.end()
            except Exception:
                pass

    def _draw_ball(self, p, s, color):
        r = s // 2
        g = QRadialGradient(QPointF(float(-r//4), float(-r//4)), float(r))
        g.setColorAt(0, color.lighter(155))
        g.setColorAt(1, color.darker(130))
        p.setBrush(QBrush(g))
        p.setPen(QPen(color.darker(150), 1))
        p.drawEllipse(-r, -r, s, s)
        p.setBrush(QBrush(QColor(255,255,255,75)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(-r//2, -r//2, r//2, r//2)

    def _draw_cube(self, p, s, color):
        h = s // 2
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(130), 1))
        p.drawRect(-h, -h, s, s)
        top = QPainterPath()
        top.moveTo(-h, -h); top.lineTo(-h+9, -h-9)
        top.lineTo(h+9, -h-9); top.lineTo(h, -h)
        p.setBrush(QBrush(color.lighter(125)))
        p.drawPath(top)

    def _draw_star(self, p, s, color):
        ro, ri = s//2, s//4
        path = QPainterPath()
        for i in range(10):
            import math
            r  = ro if i%2==0 else ri
            a  = math.radians(i*36 - 90)
            x  = r * math.cos(a)
            y  = r * math.sin(a)
            if i == 0: path.moveTo(x, y)
            else:      path.lineTo(x, y)
        path.closeSubpath()
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(130), 1))
        p.drawPath(path)

    def _draw_pizza(self, p, s, color):
        r = s // 2
        p.setBrush(QBrush(QColor(220,180,80)))
        p.setPen(QPen(QColor(180,130,40), 1))
        p.drawEllipse(-r, -r, s, s)
        p.setBrush(QBrush(QColor(235,100,50)))
        p.drawPie(-r+4, -r+4, s-8, s-8, 30*16, 60*16)
        p.setBrush(QBrush(QColor(255,230,100)))
        p.setPen(Qt.PenStyle.NoPen)
        for dx,dy in [(-8,-5),(5,-8),(0,5),(-5,8)]:
            p.drawEllipse(dx-3, dy-3, 6, 6)

    def _draw_doll(self, p, s, color):
        r = s // 3
        p.setBrush(QBrush(color))
        p.setPen(QPen(color.darker(130), 1))
        p.drawEllipse(-r, -s//2, r*2, r*2)
        er = r // 2
        for sx in [-1, 1]:
            p.drawEllipse(sx*r - er + 4, -s//2, er*2, er*2)
        p.drawEllipse(-int(r*1.2), 0, int(r*2.4), int(s*0.6))
        p.setBrush(QBrush(QColor(30,30,30)))
        p.setPen(Qt.PenStyle.NoPen)
        ey = -s//2 + r//2 + 4
        for ex in [-r//2-2, r//2-2]:
            p.drawEllipse(ex, ey, 5, 5)

    # ── API pública ───────────────────────────────────────────────────────────

    def apply_force(self, fx: float, fy: float):
        """Aplica força (Bob brincando com o brinquedo)."""
        try:
            self.vx += float(fx)
            self.vy += float(fy)
        except Exception:
            pass

    def destroy(self):
        """Remove o brinquedo da tela de forma segura."""
        try:
            self._timer.stop()
        except Exception:
            pass
        try:
            self.close()
        except Exception:
            pass


class ToyManager:
    """Gerencia todos os brinquedos na área de trabalho."""

    def __init__(self):
        self.toys: list[ToyWidget] = []

    def spawn(self, toy_type: str, x: int = None, y: int = None,
              gravity: float = 0.55) -> ToyWidget | None:
        """Cria um brinquedo na tela. Retorna o widget criado ou None."""
        # Valida tipo
        if toy_type not in TOYS_CATALOG:
            print(f"[Toys] Tipo desconhecido: '{toy_type}'. Usando 'ball'.")
            toy_type = "ball"

        try:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                if x is None: x = random.randint(geo.x()+100, geo.x()+geo.width()-100)
                if y is None: y = geo.y() + 80
            else:
                if x is None: x = 200
                if y is None: y = 100

            toy = ToyWidget(toy_type, x, y, gravity)
            self.toys.append(toy)
            return toy
        except Exception as e:
            print(f"[Toys] Erro ao criar brinquedo: {e}")
            return None

    def remove_all(self):
        for toy in list(self.toys):
            try: toy.destroy()
            except Exception: pass
        self.toys.clear()

    def remove(self, toy: ToyWidget):
        if toy in self.toys:
            try: toy.destroy()
            except Exception: pass
            self.toys.remove(toy)

    def get_nearest(self, bx: float, by: float) -> tuple:
        """Retorna (brinquedo mais próximo, distância) ou (None, inf)."""
        if not self.toys:
            return None, float("inf")
        try:
            nearest = min(self.toys, key=lambda t: math.hypot(t.px-bx, t.py-by))
            dist    = math.hypot(nearest.px - bx, nearest.py - by)
            return nearest, dist
        except Exception:
            return None, float("inf")

    def count(self) -> int:
        return len(self.toys)

    def cleanup_dead(self):
        """Remove widgets que foram fechados externamente."""
        self.toys = [t for t in self.toys if t.isVisible()]
