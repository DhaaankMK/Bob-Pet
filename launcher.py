"""
launcher.py  —  Bob Desktop Mascot  (v2)

Correções:
  • QPointF em todos os gradientes → sem TypeError Qt6
  • sys.path configurado no topo
  • Interface mais polida e animada
  • Preview do Bob atualizado com coordenadas corretas
  • Status lê state.json corretamente
  • Import de QRectF adicionado para corrigir NameError
"""

import sys
import os
from pathlib import Path

# ── sys.path PRIMEIRO ─────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# ─────────────────────────────────────────────────────────────────────────────

import json
import math
import random
import subprocess
import time

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QSizePolicy,
)
# IMPORT CORRIGIDO ABAIXO:
from PyQt6.QtCore  import Qt, QTimer, QPoint, QPointF, QRectF
from PyQt6.QtGui   import (QPainter, QColor, QBrush, QPen, QFont,
                            QLinearGradient, QRadialGradient,
                            QPainterPath, QFontMetrics)

VERSION      = "2.0.0"
BOB_SCRIPT   = _ROOT / "bob"     / "bob.py"
MGR_SCRIPT   = _ROOT / "manager" / "manager.py"
STATE_FILE   = _ROOT / "data"    / "state.json"

def _read_state() -> dict:
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════════
#  Preview animada do Bob
# ═══════════════════════════════════════════════════════════════════════════════

class BobPreview(QWidget):
    """Mini Bob procedural animado no launcher."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(170, 210)
        self._tick    = 0.0
        self._blink   = False
        self._blink_t = 0.0
        self._color   = QColor("#5B9BD5")
        self._dark    = QColor("#3A7FBF")
        t = QTimer(self); t.timeout.connect(self._step); t.start(16)

    def _step(self):
        self._tick += 0.016
        self._blink_t += 0.016
        if self._blink_t > 3.8:
            self._blink_t = 0.0
            self._blink   = True
            QTimer.singleShot(110, lambda: setattr(self, "_blink", False))
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s   = 82
        cx  = self.width() // 2
        cy  = self.height() - 18
        u   = s / 100.0
        bc  = self._color
        dc  = self._dark

        breath   = math.sin(self._tick * 1.9) * 2.2
        arm_sw   = math.sin(self._tick * 2.1) * 18

        # Dimensões
        bw = int(34 * u); bh = int(42 * u)
        hr = int(29 * u); lh = int(24 * u)
        aw = int(10 * u); ah = int(26 * u)
        lt  = cy - (lh + int(3 * u))
        bt  = lt - bh + int(8 * u) + int(breath)
        hcy = bt - hr + int(6 * u)
        at  = bt + int(5 * u)

        # Sombra
        p.setBrush(QBrush(QColor(0,0,0,30)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx-26, cy-3, 52, 8)

        # Pernas
        lo = int(10*u)
        for side in [-1,1]:
            p.save(); p.translate(float(cx+side*lo), float(lt))
            p.setBrush(QBrush(dc.lighter(108)))
            p.setPen(QPen(dc.darker(115),1))
            p.drawRoundedRect(-int(11*u//2), 0, int(11*u), lh, int(4*u),int(4*u))
            p.setBrush(QBrush(QColor(42,32,22)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(-int(8*u), lh-int(5*u), int(20*u), int(10*u))
            p.restore()

        # Torso
        grad = QLinearGradient(QPointF(float(-bw//2), float(bt)),
                                QPointF(float( bw//2), float(bt+bh)))
        grad.setColorAt(0, bc.lighter(120))
        grad.setColorAt(1, dc)
        p.setBrush(QBrush(grad))
        p.setPen(QPen(dc.darker(120),1))
        p.drawRoundedRect(cx-bw//2, bt, bw, bh, int(9*u),int(9*u))

        # Barriga
        bly = QColor(bc); bly.setAlpha(150); bly=bly.lighter(138); bly.setAlpha(150)
        p.setBrush(QBrush(bly)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx-int(12*u), bt+int(10*u), int(24*u),int(22*u))

        # Braços
        ao = int(19*u)
        for side,angle in [(-1,arm_sw),(1,-arm_sw)]:
            p.save(); p.translate(float(cx+side*ao), float(at))
            p.rotate(angle)
            p.setBrush(QBrush(bc.lighter(112)))
            p.setPen(QPen(dc.darker(112),1))
            p.drawRoundedRect(-aw//2,0,aw,ah,int(4*u),int(4*u))
            p.setBrush(QBrush(bc.lighter(125))); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(-int(7*u)//2, ah-int(7*u)//2+2, int(7*u),int(7*u))
            p.restore()

        # Cabeça
        hg = QRadialGradient(QPointF(float(cx-int(5*u)), float(hcy-int(6*u))), float(hr))
        hg.setColorAt(0, bc.lighter(130))
        hg.setColorAt(1, dc.lighter(110))
        p.setBrush(QBrush(hg)); p.setPen(QPen(dc.darker(130),1))
        p.drawEllipse(cx-hr, hcy-hr, hr*2, hr*2)

        # Olhos
        eox = int(10*u); er = int(7*u); pr = int(4*u); ey = hcy-int(5*u)
        for side in [-1,1]:
            ex = cx+side*eox
            p.setBrush(QBrush(QColor(255,255,255)))
            p.setPen(QPen(QColor(75,65,55),1))
            p.drawEllipse(ex-er//2, ey-er//2, er, er)
            if self._blink:
                p.setPen(QPen(QColor(35,25,12),max(1,int(u*1.3))))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawLine(ex-er//2, ey, ex+er//2, ey)
            else:
                p.setBrush(QBrush(QColor(33,22,12)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(ex-pr//2, ey-pr//2, pr, pr)
                p.setBrush(QBrush(QColor(255,255,255,210)))
                br2=max(1,pr//3)
                p.drawEllipse(ex-pr//2+br2//2+1, ey-pr//2+br2//2, br2,br2)

        # Nariz
        p.setBrush(QBrush(dc.darker(108))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx-int(3*u), hcy+int(5*u), int(6*u),int(4*u))

        # Bochechas
        p.setBrush(QBrush(QColor(255,140,140,55)))
        for side in [-1,1]:
            p.drawEllipse(cx+side*eox*2-int(5*u), ey+int(3*u), int(10*u),int(6*u))

        # Sorriso
        p.setPen(QPen(QColor(58,33,13),max(1,int(u*1.3))))
        p.setBrush(Qt.BrushStyle.NoBrush)
        my = hcy+int(12*u); mw = int(14*u)
        path = QPainterPath()
        path.moveTo(float(cx-mw//2), float(my))
        path.quadTo(float(cx), float(my+int(9*u)), float(cx+mw//2), float(my))
        p.drawPath(path)


# ═══════════════════════════════════════════════════════════════════════════════
#  Botão estilizado
# ═══════════════════════════════════════════════════════════════════════════════

class FancyButton(QPushButton):
    def __init__(self, icon: str, title: str, sub: str = "",
                 color: str = "#5B9BD5", parent=None):
        super().__init__(parent)
        self._color  = QColor(color)
        self._hover  = False
        self._sub    = sub
        self.setFixedHeight(68)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 8, 16, 8)

        ic = QLabel(icon)
        ic.setStyleSheet("font-size:26px; background:transparent;")
        ic.setFixedWidth(40)
        lay.addWidget(ic)

        col = QVBoxLayout(); col.setSpacing(2)
        ml = QLabel(title)
        ml.setStyleSheet("font-size:14px; font-weight:bold; color:#fff; background:transparent;")
        col.addWidget(ml)
        if sub:
            sl = QLabel(sub)
            sl.setStyleSheet("font-size:11px; color:rgba(255,255,255,0.6); background:transparent;")
            col.addWidget(sl)
        lay.addLayout(col)
        lay.addStretch()

        ar = QLabel("›")
        ar.setStyleSheet("font-size:20px; color:rgba(255,255,255,0.4); background:transparent;")
        lay.addWidget(ar)

        self.setStyleSheet("QPushButton{border:none; background:transparent;}")

    def enterEvent(self, e): self._hover=True;  self.update(); super().enterEvent(e)
    def leaveEvent(self, e): self._hover=False; self.update(); super().leaveEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r  = self.rect()
        c  = self._color
        g  = QLinearGradient(QPointF(r.topLeft()), QPointF(r.topRight()))
        g.setColorAt(0, c.lighter(115) if self._hover else c)
        g.setColorAt(1, c.lighter(105) if self._hover else c.darker(115))
        p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, 12, 12)
        bc = c.lighter(130); bc.setAlpha(80)
        p.setPen(QPen(bc, 1)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r.adjusted(0,0,-1,-1), 12, 12)
        super().paintEvent(_)


# ═══════════════════════════════════════════════════════════════════════════════
#  Fundo animado
# ═══════════════════════════════════════════════════════════════════════════════

class AnimBG(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tick = 0.0
        self._pts  = [
            {"x": random.uniform(0,600), "y": random.uniform(0,700),
             "vx": random.uniform(-22,22), "vy": random.uniform(-32,-8),
             "r":  random.uniform(2,5), "a": random.uniform(0.15,0.55)}
            for _ in range(28)
        ]
        t = QTimer(self); t.timeout.connect(self._step); t.start(30)

    def _step(self):
        self._tick += 0.03
        w,h = self.width(), self.height()
        for pt in self._pts:
            pt["x"] += pt["vx"]*0.03
            pt["y"] += pt["vy"]*0.03
            if pt["y"]<-12 or pt["x"]<-12 or pt["x"]>w+12:
                pt["x"] = random.uniform(0,w)
                pt["y"] = h+10
                pt["vx"]= random.uniform(-22,22)
                pt["vy"]= random.uniform(-32,-8)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h = self.width(), self.height()

        # Gradiente de fundo
        g = QLinearGradient(QPointF(0,0), QPointF(0,float(h)))
        g.setColorAt(0, QColor(8,8,28))
        g.setColorAt(0.5, QColor(12,12,38))
        g.setColorAt(1,   QColor(6,6,22))
        p.fillRect(self.rect(), QBrush(g))

        # Glow central pulsante
        pulse = 0.68 + math.sin(self._tick*1.4)*0.32
        cx,cy = w//2, h//2
        glow = QRadialGradient(QPointF(float(cx), float(cy)), 220*pulse)
        glow.setColorAt(0, QColor(91,155,213, int(28*pulse)))
        glow.setColorAt(1, QColor(91,155,213,0))
        p.setBrush(QBrush(glow)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx-220, cy-220, 440, 440)

        # Partículas
        for pt in self._pts:
            alpha = int(pt["a"]*200)
            c = QColor(91,155,213,alpha)
            p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
            r = int(pt["r"])
            p.drawEllipse(int(pt["x"])-r, int(pt["y"])-r, r*2, r*2)


# ═══════════════════════════════════════════════════════════════════════════════
#  Launcher Window
# ═══════════════════════════════════════════════════════════════════════════════

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Bob Desktop Mascot  v{VERSION}")
        self.setFixedSize(540, 640)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._bob_proc = None
        self._drag_pos = QPoint()

        self._build()

        # Status timer
        t = QTimer(self); t.timeout.connect(self._refresh); t.start(1600)

        # Centraliza
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.x() + (geo.width()  - self.width())  // 2,
                geo.y() + (geo.height() - self.height()) // 2,
            )

    def _build(self):
        # Fundo animado
        self.bg = AnimBG(self)
        self.bg.setGeometry(self.rect())

        # Container principal
        cnt = QWidget(self)
        cnt.setGeometry(self.rect())
        cnt.setStyleSheet("QWidget{background:transparent; color:#e0e0e0; font-family:'Segoe UI',Arial;}")

        lay = QVBoxLayout(cnt)
        lay.setContentsMargins(24, 0, 24, 24)
        lay.setSpacing(0)

        # ── Barra de título ──
        tbar = QWidget(); tbar.setFixedHeight(46); tbar.setStyleSheet("background:transparent;")
        tblay = QHBoxLayout(tbar); tblay.setContentsMargins(0,10,0,0)
        tl = QLabel(f"Bob Desktop Mascot   v{VERSION}")
        tl.setStyleSheet("color:#5B9BD5; font-size:12px; font-weight:bold;")
        tblay.addWidget(tl); tblay.addStretch()
        xb = QPushButton("✕"); xb.setFixedSize(30,30)
        xb.setStyleSheet("""
            QPushButton{background:#2a2a3a;color:#888;border:none;border-radius:15px;font-size:12px;}
            QPushButton:hover{background:#c0392b;color:#fff;}
        """)
        xb.clicked.connect(self.close)
        tblay.addWidget(xb)
        lay.addWidget(tbar)

        # ── Hero ──
        hero = QWidget(); hero.setStyleSheet("background:transparent;")
        hlay = QHBoxLayout(hero); hlay.setContentsMargins(0,12,0,8)
        self.preview = BobPreview()
        hlay.addWidget(self.preview)

        tcol = QVBoxLayout(); tcol.setSpacing(6)
        big = QLabel("Bob")
        big.setStyleSheet("font-size:54px; font-weight:bold; color:#fff; letter-spacing:-2px;")
        tcol.addWidget(big)
        tag = QLabel("Seu mascote virtual\npara o Windows Desktop")
        tag.setStyleSheet("font-size:15px; color:rgba(255,255,255,0.68); line-height:145%;")
        tcol.addWidget(tag)
        tcol.addSpacing(10)
        self.status_lbl = QLabel("○  Verificando...")
        self.status_lbl.setStyleSheet("""
            color:#666; font-size:12px; background:rgba(255,255,255,0.06);
            border-radius:10px; padding:4px 12px;
        """)
        tcol.addWidget(self.status_lbl)
        hlay.addLayout(tcol)
        lay.addWidget(hero)

        # ── Divisor ──
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background:rgba(91,155,213,0.18); border:none; max-height:1px;")
        lay.addWidget(div); lay.addSpacing(16)

        # ── Botões principais ──
        for icon, title, sub, color, fn in [
            ("🚀", "Iniciar Bob",      "Abre o mascote na área de trabalho", "#2e7d32", self._start_bob),
            ("⚙️", "Abrir Gerenciador","Controle total do mascote",          "#1565c0", self._open_mgr),
            ("✨", "Iniciar Tudo",     "Bob + Gerenciador juntos",           "#6a1b9a", self._start_all),
        ]:
            b = FancyButton(icon, title, sub, color)
            b.clicked.connect(fn)
            lay.addWidget(b)
            lay.addSpacing(8)

        lay.addSpacing(10)
        div2 = QFrame(); div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet("background:rgba(255,255,255,0.04); border:none; max-height:1px;")
        lay.addWidget(div2); lay.addSpacing(12)

        # ── Botões secundários ──
        row2 = QHBoxLayout()
        for lbl, fn, col in [
            ("■ Parar Bob",  self._stop_bob, "rgba(139,32,32,0.45)"),
            ("📖 README",    self._open_readme, "rgba(255,255,255,0.06)"),
        ]:
            b = QPushButton(lbl)
            b.setStyleSheet(f"""
                QPushButton{{background:{col};color:#ccc;border:1px solid rgba(255,255,255,0.08);
                              border-radius:8px;padding:8px 16px;}}
                QPushButton:hover{{color:#fff;border-color:rgba(255,255,255,0.25);}}
            """)
            b.clicked.connect(fn)
            row2.addWidget(b)
        lay.addLayout(row2)

        lay.addStretch()

        foot = QLabel("Bob Desktop Mascot  •  Python + PyQt6  •  Feito com ❤️")
        foot.setStyleSheet("color:rgba(255,255,255,0.2); font-size:11px;")
        foot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(foot)

    # ── Borda arredondada (Corrigido) ──────────────────────────────────────────

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        
        # AQUI FOI FEITA A CORREÇÃO:
        # Passamos um QRectF diretamente ao invés de um QPointF
        path.addRoundedRect(QRectF(0.0, 0.0, float(self.width()), float(self.height())), 16.0, 16.0)
        
        p.setClipPath(path)
        p.fillPath(path, QBrush(QColor(10,10,30,248)))
        p.setPen(QPen(QColor(91,155,213,55),1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(0, 0, self.width()-1, self.height()-1, 16, 16)

    # ── Arrastar janela ───────────────────────────────────────────────────────

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    # ── Ações ─────────────────────────────────────────────────────────────────

    def _start_bob(self):
        if not BOB_SCRIPT.exists():
            self._set_status("❌ bob.py não encontrado!", "#ff6b6b"); return
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            self._bob_proc = subprocess.Popen(
                [sys.executable, str(BOB_SCRIPT)], creationflags=flags)
            self._set_status("✅ Bob iniciado!", "#2ecc71")
        except Exception as e:
            self._set_status(f"❌ Erro: {e}", "#ff6b6b")

    def _open_mgr(self):
        if not MGR_SCRIPT.exists():
            self._set_status("❌ manager.py não encontrado!", "#ff6b6b"); return
        try:
            subprocess.Popen([sys.executable, str(MGR_SCRIPT)])
            self._set_status("⚙️ Gerenciador aberto!", "#5B9BD5")
        except Exception as e:
            self._set_status(f"❌ Erro: {e}", "#ff6b6b")

    def _start_all(self):
        self._start_bob()
        QTimer.singleShot(400, self._open_mgr)

    def _stop_bob(self):
        if self._bob_proc and self._bob_proc.poll() is None:
            self._bob_proc.terminate()
            self._set_status("■ Bob encerrado.", "#e74c3c")
        else:
            self._set_status("ℹ️ Bob não está rodando.", "#888")

    def _open_readme(self):
        readme = _ROOT / "README.md"
        if readme.exists() and sys.platform == "win32":
            try: os.startfile(str(readme))
            except Exception: pass

    def _refresh(self):
        state = _read_state()
        if state.get("running", False):
            mood  = state.get("mood", "?")
            name  = state.get("user_name", "")
            icons = {"happy":"😊","bored":"😑","excited":"🎉",
                     "sleepy":"😴","angry":"😠","playful":"😜","sad":"😢"}
            ic = icons.get(mood,"")
            txt = f"● Bob Online  {ic}  {mood}"
            if name:
                txt += f"  |  Olá, {name}!"
            self._set_status(txt, "#2ecc71")
        else:
            self._set_status("○  Bob Offline", "#555")

    def _set_status(self, text: str, color: str = "#888"):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"""
            color:{color}; font-size:12px;
            background:rgba(255,255,255,0.05);
            border-radius:10px; padding:4px 12px;
        """)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Bob Desktop Mascot")
    win = Launcher()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()