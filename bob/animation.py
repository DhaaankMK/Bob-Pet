"""
animation.py - Sistema de animações do Bob (v2)
CORREÇÕES:
  - Texto/balão NÃO ficam invertidos (flip só afeta corpo)
  - Roupas com coordenadas corrigidas (sistema relativo consistente)
  - Animações mais detalhadas e suaves
  - Novas animações: wave, sit, spin
  - Mais itens de roupa: sunglasses, scarf, bow, tie
"""

import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import math
import random
from enum import Enum

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import (QPainter, QColor, QBrush, QPen, QPainterPath,
                         QFont, QRadialGradient, QLinearGradient, QFontMetrics)


class AnimState(Enum):
    IDLE      = "idle"
    WALK      = "walk"
    JUMP      = "jump"
    FALL      = "fall"
    SLEEP     = "sleep"
    PLAY      = "play"
    REACT     = "react"
    DANCE     = "dance"
    TRIP      = "trip"
    ANGRY     = "angry"
    DRAG      = "drag"
    CHAOTIC   = "chaotic"
    WAVE      = "wave"
    SIT       = "sit"
    SPIN      = "spin"


class AnimationSystem:
    """
    Renderiza o Bob via QPainter puro (sem sprites externos).
    
    ARQUITETURA DE DRAW (importante para entender o flip):
    
      draw()
        ├─ painter.save()
        │   ├─ [Se facing=="left": translate+scale flip]
        │   ├─ draw_fn(...)        ← corpo flippado (OK!)
        │   └─ _draw_clothes(...)  ← roupas flippadas (OK!)
        ├─ painter.restore()       ← flip desfeito aqui
        ├─ _draw_particles(...)    ← sem flip (OK!)
        └─ _draw_speech_bubble(...)← sem flip → texto sempre correto!
    """

    def __init__(self, settings: dict):
        self.state: AnimState          = AnimState.IDLE
        self.previous_state: AnimState = AnimState.IDLE
        self.tick: float               = 0.0
        self.state_tick: float         = 0.0
        self.facing: str               = "right"

        self.size: int     = int(settings.get("bob_size", 100))
        self.scale: float  = float(settings.get("scale", 1.0))

        self.primary_color: str   = "#5B9BD5"
        self.secondary_color: str = "#3A7FBF"

        self.blink_timer: float    = 0.0
        self.blink_duration: float = random.uniform(3.0, 6.0)
        self.is_blinking: bool     = False
        self.blink_frame: float    = 0.0

        self.chaotic_mode: bool = False
        self.chaotic_hue: float = 0.0

        self.particles: list    = []
        self.land_squish: float = 0.0  # efeito ao pousar

    # ─── Update ───────────────────────────────────────────────────────────────

    def update(self, dt: float):
        self.tick += dt
        self.state_tick += dt

        self.blink_timer += dt
        if self.blink_timer >= self.blink_duration:
            self.blink_timer    = 0.0
            self.blink_duration = random.uniform(2.5, 6.0)
            self.is_blinking    = True
            self.blink_frame    = 0.0

        if self.is_blinking:
            self.blink_frame += dt * 10
            if self.blink_frame > 1.0:
                self.is_blinking = False

        if self.chaotic_mode:
            self.chaotic_hue = (self.chaotic_hue + dt * 150) % 360

        if self.land_squish > 0:
            self.land_squish = max(0.0, self.land_squish - dt * 5)

        self._update_particles(dt)

    def _update_particles(self, dt: float):
        self.particles = [
            {**p,
             "life": p["life"] - dt,
             "x":    p["x"] + p["vx"] * dt,
             "y":    p["y"] + p["vy"] * dt,
             "vy":   p["vy"] + 2.8 * dt}
            for p in self.particles if p["life"] - dt > 0
        ]

    def spawn_particles(self, x: float, y: float, count: int = 8, color: str = "#FFD700"):
        for _ in range(count):
            self.particles.append({
                "x": x, "y": y,
                "vx": random.uniform(-75, 75),
                "vy": random.uniform(-140, -25),
                "life": random.uniform(0.3, 0.75),
                "max_life": 0.55,
                "color": color,
                "size": random.randint(3, 8),
            })

    def on_land(self):
        self.land_squish = 1.0

    def set_state(self, state: AnimState):
        if self.state != state:
            self.previous_state = self.state
            self.state          = state
            self.state_tick     = 0.0

    def set_state_by_name(self, name: str):
        try:
            self.set_state(AnimState(name))
        except ValueError:
            pass

    def set_colors(self, primary: str, secondary: str):
        self.primary_color   = primary
        self.secondary_color = secondary

    def _get_s(self) -> int:
        return max(40, int(self.size * self.scale))

    def _body_color(self) -> QColor:
        if self.chaotic_mode:
            return QColor.fromHsvF(self.chaotic_hue / 360, 0.88, 0.96)
        return QColor(self.primary_color)

    def _dark_color(self) -> QColor:
        if self.chaotic_mode:
            return QColor.fromHsvF(((self.chaotic_hue + 45) % 360) / 360, 0.88, 0.70)
        return QColor(self.secondary_color)

    # ─── DRAW PRINCIPAL ───────────────────────────────────────────────────────

    def draw(self, painter: QPainter, widget_w: int, widget_h: int,
             phrase: str = "", clothes: list = None, **kwargs):
        """
        Desenha o Bob completo.
        O flip de direção (esq/dir) é aplicado APENAS ao corpo e roupas.
        Balão de fala e partículas são desenhados sem flip — texto sempre legível.
        """
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        s  = self._get_s()
        cx = widget_w // 2
        cy = widget_h - int(s * 0.08)  # base dos pés

        # ── FASE 1: corpo + roupas (dentro do flip) ──────────────────────────
        painter.save()
        if self.facing == "left":
            painter.translate(float(widget_w), 0.0)
            painter.scale(-1.0, 1.0)

        draw_fn = {
            AnimState.IDLE:    self._draw_idle,
            AnimState.WALK:    self._draw_walk,
            AnimState.JUMP:    self._draw_jump,
            AnimState.FALL:    self._draw_fall,
            AnimState.SLEEP:   self._draw_sleep,
            AnimState.PLAY:    self._draw_play,
            AnimState.REACT:   self._draw_react,
            AnimState.DANCE:   self._draw_dance,
            AnimState.TRIP:    self._draw_trip,
            AnimState.ANGRY:   self._draw_angry,
            AnimState.DRAG:    self._draw_drag,
            AnimState.CHAOTIC: self._draw_chaotic,
            AnimState.WAVE:    self._draw_wave,
            AnimState.SIT:     self._draw_sit,
            AnimState.SPIN:    self._draw_spin,
        }.get(self.state, self._draw_idle)

        draw_fn(painter, cx, cy, s)

        if clothes:
            self._draw_clothes(painter, cx, cy, s, clothes)

        painter.restore()

        # ── FASE 2: partículas + balão (sem flip) ─────────────────────────────
        self._draw_particles(painter)
        if phrase:
            self._draw_speech_bubble(painter, cx, cy, s, phrase)

    # ─── Animações ────────────────────────────────────────────────────────────

    def _draw_idle(self, p, cx, cy, s):
        breath   = math.sin(self.tick * 1.8) * 2
        sq_y     = int(self.land_squish * 5)
        sq_x     = int(self.land_squish * -2)
        self._body(p, cx, cy + int(breath), s,
                   arm_l=12, arm_r=-12,
                   bew=sq_x, beh=sq_y)

    def _draw_walk(self, p, cx, cy, s):
        sp    = 8.5
        leg   = math.sin(self.tick * sp) * 24
        arm   = -leg * 0.6
        bob_y = abs(math.sin(self.tick * sp)) * 3
        self._body(p, cx, cy - int(bob_y), s,
                   arm_l=int(arm), arm_r=int(-arm),
                   leg_l=int(leg), leg_r=int(-leg))

    def _draw_jump(self, p, cx, cy, s):
        stretch = math.sin(self.state_tick * 6) * 4
        self._body(p, cx, cy, s, arm_l=-68, arm_r=68,
                   leg_l=30, leg_r=-30,
                   beh=int(stretch), expr="surprised")

    def _draw_fall(self, p, cx, cy, s):
        w = math.sin(self.tick * 14) * 5
        self._body(p, cx, cy + int(w * 0.3), s,
                   arm_l=-88, arm_r=88, expr="scared")

    def _draw_sleep(self, p, cx, cy, s):
        self._body(p, cx, cy, s, expr="sleep", arm_l=8, arm_r=-8)
        unit = s / 100.0
        for i in range(3):
            alpha = int(215 * max(0, math.sin(self.tick * 1.4 - i * 1.1)))
            if alpha > 12:
                p.setPen(QColor(120, 155, 255, alpha))
                font_size = max(6, int(s * 0.10) + i * 2)
                p.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
                zx = cx + int((35 + i * 11) * unit)
                zy = cy  - int((118 + i * 15) * unit)
                p.drawText(int(zx), int(zy), "z")

    def _draw_play(self, p, cx, cy, s):
        hop  = abs(math.sin(self.tick * 7)) * int(s * 0.10)
        spin = math.sin(self.tick * 7) * 48
        self._body(p, cx, cy - int(hop), s,
                   arm_l=int(-spin), arm_r=int(spin), expr="happy")

    def _draw_react(self, p, cx, cy, s):
        j = abs(math.sin(self.state_tick * 11)) * int(s * 0.13)
        self._body(p, cx, cy - int(j), s,
                   arm_l=-78, arm_r=78, expr="surprised")

    def _draw_dance(self, p, cx, cy, s):
        ds   = 7.0
        side = math.sin(self.tick * ds) * int(s * 0.06)
        hop  = abs(math.sin(self.tick * ds * 2)) * int(s * 0.08)
        al   = math.sin(self.tick * ds) * 68 - 22
        ar   = -math.sin(self.tick * ds) * 68 + 22
        ll   = math.sin(self.tick * ds * 2) * 30
        self._body(p, cx + int(side), cy - int(hop), s,
                   arm_l=int(al), arm_r=int(ar),
                   leg_l=int(ll), leg_r=int(-ll), expr="happy")

    def _draw_trip(self, p, cx, cy, s):
        tilt = math.sin(self.state_tick * 4) * 20
        self._body(p, cx, cy, s,
                   arm_l=52, arm_r=-105, expr="scared", tilt=tilt)

    def _draw_angry(self, p, cx, cy, s):
        shake = math.sin(self.tick * 22) * 3
        self._body(p, cx + int(shake), cy, s,
                   expr="angry", arm_l=25, arm_r=-25)

    def _draw_drag(self, p, cx, cy, s):
        spin = math.sin(self.tick * 9) * 8
        self._body(p, cx, cy, s,
                   arm_l=-95, arm_r=95, expr="scared", tilt=spin)

    def _draw_chaotic(self, p, cx, cy, s):
        ox = math.sin(self.tick * 15) * 10
        oy = math.cos(self.tick * 11) * 7
        al = math.sin(self.tick * 8) * 95
        ar = math.cos(self.tick * 13) * 95
        ll = math.sin(self.tick * 6) * 45
        self._body(p, cx + int(ox), cy + int(oy), s,
                   arm_l=int(al), arm_r=int(ar),
                   leg_l=int(ll), leg_r=int(-ll), expr="excited")

    def _draw_wave(self, p, cx, cy, s):
        wa = math.sin(self.tick * 5) * 32 - 58
        self._body(p, cx, cy, s, arm_l=int(wa), arm_r=-15, expr="happy")

    def _draw_sit(self, p, cx, cy, s):
        self._body(p, cx, cy, s, arm_l=32, arm_r=-32,
                   leg_l=85, leg_r=-85, expr="happy")

    def _draw_spin(self, p, cx, cy, s):
        spin_deg = (self.tick * 380) % 360
        p.save()
        mid_y = cy - int(s * 0.55)
        p.translate(float(cx), float(mid_y))
        p.rotate(spin_deg)
        p.translate(float(-cx), float(-mid_y))
        self._body(p, cx, cy, s, arm_l=-92, arm_r=92)
        p.restore()

    # ─── Corpo Base ───────────────────────────────────────────────────────────

    def _body(self, p: QPainter, cx: int, cy: int, s: int,
              arm_l: int = 14, arm_r: int = -14,
              leg_l: int = 0, leg_r: int = 0,
              expr: str = "normal",
              bew: int = 0, beh: int = 0,
              tilt: float = 0.0):
        """
        Desenha o Bob completo.
        (cx, cy) = base dos pés no espaço do painter.
        Internamente faz translate(cx,cy) para que tudo seja relativo à base.
        """
        p.save()
        p.translate(float(cx), float(cy))
        if tilt:
            p.rotate(tilt)

        unit = s / 100.0

        # Dimensões
        bw = int(34 * unit) + bew      # body width
        bh = int(42 * unit) + beh      # body height
        hr = int(29 * unit)            # head radius
        lw = int(11 * unit)            # leg width
        lh = int(24 * unit)            # leg height
        aw = int(10 * unit)            # arm width
        ah = int(26 * unit)            # arm height

        # Posições relativas à origem (0 = base)
        lt  = -(lh + int(3 * unit))          # leg top Y
        bt  = lt - bh + int(8 * unit)        # body top Y
        hcy = bt - hr + int(6 * unit)        # head center Y
        at  = bt + int(5 * unit)             # arm attachment Y

        # Sombra
        p.setBrush(QBrush(QColor(0, 0, 0, 32)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(-27 * unit), int(-3 * unit),
                      int(54 * unit), int(8 * unit))

        self._legs(p, unit, lt, lw, lh, leg_l, leg_r)

        # Torso
        bc = self._body_color()
        dc = self._dark_color()
        grad = QLinearGradient(
            QPointF(float(-bw // 2), float(bt)),
            QPointF(float(bw // 2),  float(bt + bh))
        )
        grad.setColorAt(0, bc.lighter(120))
        grad.setColorAt(1, dc)
        p.setBrush(QBrush(grad))
        p.setPen(QPen(dc.darker(120), max(1, int(unit * 1.1))))
        p.drawRoundedRect(-bw // 2, bt, bw, bh,
                           int(9 * unit), int(9 * unit))

        # Barriga
        belly = QColor(bc)
        belly.setAlpha(155)
        belly = belly.lighter(138)
        belly.setAlpha(155)
        p.setBrush(QBrush(belly))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(-12 * unit), bt + int(10 * unit),
                      int(24 * unit), int(22 * unit))

        self._arms(p, unit, at, aw, ah, arm_l, arm_r)

        # Cabeça
        hg = QRadialGradient(
            QPointF(float(-int(5 * unit)), float(hcy - int(6 * unit))),
            float(hr)
        )
        hg.setColorAt(0, bc.lighter(130))
        hg.setColorAt(1, dc.lighter(110))
        p.setBrush(QBrush(hg))
        p.setPen(QPen(dc.darker(130), max(1, int(unit * 1.1))))
        p.drawEllipse(-hr, hcy - hr, hr * 2, hr * 2)

        self._face(p, unit, hcy, hr, expr)

        p.restore()

    def _legs(self, p, unit, lt, lw, lh, al, ar):
        dc = self._dark_color()
        lo = int(10 * unit)
        fr, fy = int(8 * unit), int(5 * unit)
        for side, angle in [(-1, al), (1, ar)]:
            p.save()
            p.translate(float(side * lo), float(lt))
            p.rotate(float(angle))
            p.setBrush(QBrush(dc.lighter(108)))
            p.setPen(QPen(dc.darker(115), max(1, int(unit * 0.9))))
            p.drawRoundedRect(-lw // 2, 0, lw, lh, int(4 * unit), int(4 * unit))
            p.setBrush(QBrush(QColor(42, 32, 22)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(-fr, lh - fy, fr * 2 + int(4 * unit), fy * 2)
            p.restore()

    def _arms(self, p, unit, at, aw, ah, al, ar):
        bc = self._body_color()
        dc = self._dark_color()
        ao = int(19 * unit)
        hr2 = int(7 * unit)
        for side, angle in [(-1, al), (1, ar)]:
            p.save()
            p.translate(float(side * ao), float(at))
            p.rotate(float(angle))
            p.setBrush(QBrush(bc.lighter(112)))
            p.setPen(QPen(dc.darker(112), max(1, int(unit * 0.9))))
            p.drawRoundedRect(-aw // 2, 0, aw, ah, int(4 * unit), int(4 * unit))
            p.setBrush(QBrush(bc.lighter(125)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(-hr2 // 2, ah - hr2 // 2 + 2, hr2, hr2)
            p.restore()

    def _face(self, p, unit, hcy, hr, expr):
        """Rosto com expressões."""
        ey   = hcy - int(5 * unit)   # olho Y
        eox  = int(10 * unit)        # olho offset X
        er   = int(7 * unit)         # olho radius
        pr   = int(4 * unit)         # pupil radius
        ny   = hcy + int(5 * unit)   # nariz Y
        my   = hcy + int(12 * unit)  # boca Y
        mw   = int(14 * unit)        # boca width
        brow = ey - er - int(1 * unit)  # sobrancelha Y
        bw   = int(11 * unit)        # sobrancelha half-width

        # Olhos
        for side in [-1, 1]:
            ex = side * eox
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.setPen(QPen(QColor(75, 65, 55), max(1, int(unit * 0.5))))
            p.drawEllipse(ex - er // 2, ey - er // 2, er, er)

            if expr == "sleep":
                p.setPen(QPen(QColor(38, 28, 15), max(1, int(unit * 1.3))))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawLine(ex - er // 2, ey, ex + er // 2, ey)
            elif self.is_blinking:
                bh = max(1, int(er * (1 - math.sin(self.blink_frame * math.pi))))
                p.setBrush(QBrush(QColor(33, 22, 12)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(ex - pr // 2, ey - bh // 2, pr, bh)
            else:
                p.setBrush(QBrush(QColor(33, 22, 12)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(ex - pr // 2, ey - pr // 2, pr, pr)
                p.setBrush(QBrush(QColor(255, 255, 255, 215)))
                br = max(1, pr // 3)
                p.drawEllipse(ex - pr // 2 + br // 2 + 1,
                               ey - pr // 2 + br // 2, br, br)

        # Sobrancelhas
        sp = QPen(QColor(52, 33, 12), max(1, int(unit * 1.35)))
        p.setPen(sp)
        if expr == "angry":
            p.drawLine(-eox - bw, brow - int(4 * unit), -eox + bw, brow + int(1 * unit))
            p.drawLine(eox - bw, brow + int(1 * unit), eox + bw, brow - int(4 * unit))
        elif expr in ("surprised", "scared"):
            for side in [-1, 1]:
                ex = side * eox
                p.drawLine(ex - bw, brow - int(5 * unit), ex + bw, brow - int(5 * unit))
        elif expr == "sad":
            p.drawLine(-eox - bw, brow - int(1 * unit), -eox + bw, brow - int(4 * unit))
            p.drawLine(eox - bw, brow - int(4 * unit), eox + bw, brow - int(1 * unit))
        else:
            for side in [-1, 1]:
                ex = side * eox
                p.drawLine(ex - bw, brow - int(2 * unit), ex + bw, brow - int(2 * unit))

        # Bochechas
        p.setBrush(QBrush(QColor(255, 140, 140, 55)))
        p.setPen(Qt.PenStyle.NoPen)
        for side in [-1, 1]:
            p.drawEllipse(side * eox * 2 - int(5 * unit),
                           ey + int(3 * unit), int(10 * unit), int(6 * unit))

        # Nariz
        p.setBrush(QBrush(self._dark_color().darker(108)))
        p.drawEllipse(int(-3 * unit), ny, int(6 * unit), int(4 * unit))

        # Boca
        p.setPen(QPen(QColor(58, 33, 13), max(1, int(unit * 1.35))))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()

        if expr == "sleep":
            path.moveTo(int(-6 * unit), my)
            path.quadTo(0.0, float(my + int(4 * unit)), float(int(6 * unit)), float(my))
        elif expr in ("happy", "excited"):
            path.moveTo(float(-mw // 2), float(my))
            path.quadTo(0.0, float(my + int(10 * unit)), float(mw // 2), float(my))
        elif expr == "scared":
            p.setBrush(QBrush(QColor(78, 18, 18)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(-7 * unit), my - int(4 * unit),
                           int(14 * unit), int(12 * unit))
            p.setPen(QPen(QColor(58, 33, 13), max(1, int(unit * 1.35))))
            p.setBrush(Qt.BrushStyle.NoBrush)
        elif expr == "angry":
            path.moveTo(float(-mw // 2), float(my + int(5 * unit)))
            path.quadTo(0.0, float(my - int(3 * unit)), float(mw // 2), float(my + int(5 * unit)))
        elif expr == "sad":
            path.moveTo(float(-mw // 2), float(my + int(5 * unit)))
            path.quadTo(0.0, float(my - int(5 * unit)), float(mw // 2), float(my + int(5 * unit)))
        elif expr == "surprised":
            p.setBrush(QBrush(QColor(78, 38, 38)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(-6 * unit), my - int(3 * unit),
                           int(12 * unit), int(10 * unit))
            p.setPen(QPen(QColor(58, 33, 13), max(1, int(unit * 1.35))))
            p.setBrush(Qt.BrushStyle.NoBrush)
        else:
            path.moveTo(float(int(-8 * unit)), float(my + int(3 * unit)))
            path.quadTo(0.0, float(my + int(7 * unit)), float(int(8 * unit)), float(my + int(3 * unit)))

        if not path.isEmpty():
            p.drawPath(path)

    # ─── Roupas ───────────────────────────────────────────────────────────────

    def _draw_clothes(self, p: QPainter, cx: int, cy: int, s: int, clothes: list):
        """
        Desenha roupas no mesmo espaço do corpo.
        Chamado DENTRO do bloco save/restore do flip → roupas ficam corretas.
        Usa translate(cx,cy) internamente, como o _body().
        """
        unit = s / 100.0

        # Recalcula posições-chave (iguais ao _body)
        lh  = int(24 * unit)
        bh  = int(42 * unit)
        hr  = int(29 * unit)
        lt  = -(lh + int(3 * unit))
        bt  = lt - bh + int(8 * unit)
        bw  = int(34 * unit)
        hcy = bt - hr + int(6 * unit)
        ht  = hcy - hr   # head top

        for item in clothes:
            p.save()
            p.translate(float(cx), float(cy))   # mesma origem do _body

            if   item == "hat":         self._cl_hat(p, unit, ht, hr)
            elif item == "glasses":     self._cl_glasses(p, unit, hcy, hr)
            elif item == "sunglasses":  self._cl_sunglasses(p, unit, hcy, hr)
            elif item == "shirt":       self._cl_shirt(p, unit, bt, bw, bh)
            elif item == "cape":        self._cl_cape(p, unit, bt, lt)
            elif item == "crown":       self._cl_crown(p, unit, ht, hr)
            elif item == "scarf":       self._cl_scarf(p, unit, bt)
            elif item == "bow":         self._cl_bow(p, unit, ht, hr)
            elif item == "tie":         self._cl_tie(p, unit, bt, bh)

            p.restore()

    def _cl_hat(self, p, unit, ht, hr):
        hw = int(62 * unit); hh = int(36 * unit); brim = int(9 * unit)
        p.setBrush(QBrush(QColor(22, 18, 18)))
        p.setPen(QPen(QColor(55, 45, 35), max(1, int(unit))))
        p.drawRect(-hw // 2, ht - hh, hw, hh)
        p.drawRect(-int(hw * 0.72), ht - brim, int(hw * 1.44), brim)
        p.setBrush(QBrush(QColor(195, 50, 50)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(-hw // 2, ht - int(7 * unit), hw, int(7 * unit))

    def _cl_crown(self, p, unit, ht, hr):
        cw = int(52 * unit); ch = int(22 * unit)
        p.setBrush(QBrush(QColor(255, 215, 0)))
        p.setPen(QPen(QColor(200, 158, 0), max(1, int(unit))))
        path = QPainterPath()
        path.moveTo(float(-cw // 2), float(ht))
        path.lineTo(float(-cw // 2), float(ht - ch))
        path.lineTo(float(-cw // 4), float(ht - int(ch * 0.45)))
        path.lineTo(0.0,             float(ht - ch))
        path.lineTo(float( cw // 4), float(ht - int(ch * 0.45)))
        path.lineTo(float( cw // 2), float(ht - ch))
        path.lineTo(float( cw // 2), float(ht))
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(QBrush(QColor(255, 80, 80)))
        p.setPen(Qt.PenStyle.NoPen)
        for gx in [-int(cw * 0.3), 0, int(cw * 0.3)]:
            p.drawEllipse(gx - int(3 * unit), ht - int(5 * unit),
                           int(6 * unit), int(6 * unit))

    def _cl_glasses(self, p, unit, hcy, hr):
        ey = hcy - int(5 * unit); eox = int(10 * unit); gr = int(13 * unit)
        p.setPen(QPen(QColor(75, 50, 18), max(1, int(unit * 1.5))))
        p.setBrush(QBrush(QColor(145, 215, 255, 65)))
        p.drawEllipse(-eox - gr // 2, ey - gr // 2, gr, gr)
        p.drawEllipse( eox - gr // 2, ey - gr // 2, gr, gr)
        p.drawLine(-eox + gr // 2, ey, eox - gr // 2, ey)
        p.drawLine(-eox - gr // 2, ey, -eox - gr // 2 - int(9 * unit), ey - int(2 * unit))
        p.drawLine( eox + gr // 2, ey,  eox + gr // 2 + int(9 * unit), ey - int(2 * unit))

    def _cl_sunglasses(self, p, unit, hcy, hr):
        ey = hcy - int(5 * unit); eox = int(10 * unit)
        gw = int(15 * unit); gh = int(10 * unit)
        p.setBrush(QBrush(QColor(18, 18, 18, 225)))
        p.setPen(QPen(QColor(28, 28, 28), max(1, int(unit * 1.5))))
        p.drawRoundedRect(-eox - gw // 2, ey - gh // 2, gw, gh, int(3 * unit), int(3 * unit))
        p.drawRoundedRect( eox - gw // 2, ey - gh // 2, gw, gh, int(3 * unit), int(3 * unit))
        p.setPen(QPen(QColor(48, 48, 48), max(1, int(unit * 1.2))))
        p.drawLine(-eox + gw // 2, ey, eox - gw // 2, ey)
        p.drawLine(-eox - gw // 2, ey, -eox - gw // 2 - int(9 * unit), ey)
        p.drawLine( eox + gw // 2, ey,  eox + gw // 2 + int(9 * unit), ey)

    def _cl_shirt(self, p, unit, bt, bw, bh):
        sh = int(bh * 0.58)
        p.setBrush(QBrush(QColor(215, 58, 58, 200)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(-bw // 2 + 1, bt + 1, bw - 2, sh, int(6 * unit), int(6 * unit))
        p.setBrush(QBrush(QColor(255, 255, 255, 185)))
        for i in range(3):
            by2 = bt + int(6 * unit) + i * int(8 * unit)
            p.drawEllipse(int(-2 * unit), by2, int(4 * unit), int(4 * unit))

    def _cl_cape(self, p, unit, bt, lt):
        cc = QColor(178, 28, 28, 215)
        p.setBrush(QBrush(cc))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        ty = bt + int(4 * unit)
        by2 = lt + int(12 * unit)
        path.moveTo(float(-int(14 * unit)), float(ty))
        path.cubicTo(float(-int(36 * unit)), float((ty + by2) // 2),
                     float(-int(36 * unit)), float(by2), float(-int(18 * unit)), float(by2))
        path.lineTo(float( int(18 * unit)), float(by2))
        path.cubicTo(float( int(36 * unit)), float(by2),
                     float( int(36 * unit)), float((ty + by2) // 2),
                     float( int(14 * unit)), float(ty))
        path.closeSubpath()
        p.drawPath(path)

    def _cl_scarf(self, p, unit, bt):
        sy = bt - int(2 * unit)
        p.setBrush(QBrush(QColor(48, 128, 215)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(int(-19 * unit), sy, int(38 * unit), int(9 * unit),
                           int(4 * unit), int(4 * unit))
        p.setBrush(QBrush(QColor(28, 98, 195)))
        p.drawRect(int(7 * unit), sy + int(7 * unit), int(7 * unit), int(9 * unit))

    def _cl_bow(self, p, unit, ht, hr):
        by2 = ht - int(4 * unit); bx = int(13 * unit)
        p.setBrush(QBrush(QColor(255, 95, 175)))
        p.setPen(QPen(QColor(215, 55, 135), max(1, int(unit * 0.9))))
        lpath = QPainterPath()
        lpath.moveTo(0.0, float(by2))
        lpath.cubicTo(float(-bx), float(by2 - int(9 * unit)),
                      float(-bx - int(4 * unit)), float(by2 + int(7 * unit)), 0.0, float(by2))
        rpath = QPainterPath()
        rpath.moveTo(0.0, float(by2))
        rpath.cubicTo(float( bx), float(by2 - int(9 * unit)),
                      float( bx + int(4 * unit)), float(by2 + int(7 * unit)), 0.0, float(by2))
        p.drawPath(lpath)
        p.drawPath(rpath)
        p.setBrush(QBrush(QColor(255, 175, 210)))
        p.drawEllipse(int(-3 * unit), by2 - int(3 * unit), int(6 * unit), int(6 * unit))

    def _cl_tie(self, p, unit, bt, bh):
        p.setBrush(QBrush(QColor(28, 55, 160)))
        p.setPen(Qt.PenStyle.NoPen)
        tt = bt + int(4 * unit); tb = bt + int(bh * 0.65)
        p.drawRoundedRect(int(-5 * unit), tt, int(10 * unit), int(7 * unit),
                           int(2 * unit), int(2 * unit))
        path = QPainterPath()
        path.moveTo(float(-int(5 * unit)), float(tt + int(6 * unit)))
        path.lineTo(float(-int(8 * unit)), float(tb))
        path.lineTo(0.0, float(tb + int(6 * unit)))
        path.lineTo(float( int(8 * unit)), float(tb))
        path.lineTo(float( int(5 * unit)), float(tt + int(6 * unit)))
        path.closeSubpath()
        p.drawPath(path)
        p.setBrush(QBrush(QColor(75, 115, 215, 155)))
        p.drawRect(int(-3 * unit), tt + int(12 * unit), int(6 * unit), int(4 * unit))

    # ─── Partículas ───────────────────────────────────────────────────────────

    def _draw_particles(self, p: QPainter):
        for part in self.particles:
            ml = part.get("max_life", 0.55)
            alpha = int(255 * max(0.0, part["life"] / max(ml, 0.01)))
            c = QColor(part["color"])
            c.setAlpha(max(0, min(255, alpha)))
            p.setBrush(QBrush(c))
            p.setPen(Qt.PenStyle.NoPen)
            r = max(1, part["size"])
            p.drawEllipse(int(part["x"]) - r, int(part["y"]) - r, r * 2, r * 2)

    # ─── Balão de Fala ────────────────────────────────────────────────────────

    def _draw_speech_bubble(self, p: QPainter, cx: int, cy: int, s: int, phrase: str):
        """
        CORREÇÃO: Chamado APÓS restore() do flip.
        O texto NUNCA fica invertido, independente da direção do Bob.
        """
        unit = s / 100.0

        # Posição do topo da cabeça em widget coords
        lh  = int(24 * unit)
        bh  = int(42 * unit)
        hr  = int(29 * unit)
        lt  = cy - (lh + int(3 * unit))
        bt  = lt - bh + int(8 * unit)
        hcy_abs = bt - hr + int(6 * unit)
        ht_abs  = hcy_abs - hr  # topo da cabeça em widget coords

        font_size = max(9, int(s * 0.12))
        font = QFont("Segoe UI", font_size)
        font.setWeight(QFont.Weight.Medium)
        p.setFont(font)
        fm = QFontMetrics(font)

        max_chars = 36
        if len(phrase) > max_chars:
            phrase = phrase[:max_chars - 1] + "…"

        ph = int(10 * unit); pv = int(8 * unit)
        tw = fm.horizontalAdvance(phrase)
        th = fm.height()
        bw2 = tw + ph * 2
        bh2 = th + pv * 2
        tail_h = int(13 * unit)

        bx = cx - bw2 // 2
        by = ht_abs - bh2 - tail_h - int(6 * unit)

        # Sombra
        p.setBrush(QBrush(QColor(0, 0, 0, 28)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(bx + 2, by + 2, bw2, bh2, int(9 * unit), int(9 * unit))

        # Fundo
        p.setBrush(QBrush(QColor(255, 255, 255, 248)))
        p.setPen(QPen(QColor(195, 195, 210), max(1, int(unit))))
        p.drawRoundedRect(bx, by, bw2, bh2, int(9 * unit), int(9 * unit))

        # Cauda
        tail = QPainterPath()
        tail.moveTo(float(cx - int(7 * unit)), float(by + bh2))
        tail.lineTo(float(cx), float(ht_abs - int(4 * unit)))
        tail.lineTo(float(cx + int(7 * unit)), float(by + bh2))
        tail.closeSubpath()
        p.setBrush(QBrush(QColor(255, 255, 255, 248)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(tail)

        p.setPen(QPen(QColor(195, 195, 210), max(1, int(unit))))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(cx - int(7 * unit), by + bh2, cx, ht_abs - int(4 * unit))
        p.drawLine(cx, ht_abs - int(4 * unit), cx + int(7 * unit), by + bh2)

        # Texto
        p.setPen(QPen(QColor(28, 28, 38)))
        p.drawText(bx + ph, by + pv, tw + 2, th + 2,
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   phrase)
