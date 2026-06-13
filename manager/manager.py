"""
manager/manager.py  —  Painel Gerenciador do Bob  (v3 — Revisão de Estabilidade)

Correções aplicadas:
  1. sys.path via bob.paths no topo
  2. Todos os caminhos via PATHS (sem strings literais)
  3. QPointF em todos os gradientes
  4. Validação de comandos antes de enviar
  5. try/except em todas as operações críticas
  6. Verificação de plataforma antes de APIs Windows
  7. Timers em vez de operações bloqueantes
  8. API de piadas com fallback (try/except + resposta local)
  9. Status bar atualizada via QTimer (não bloqueia UI)
"""

import sys
import os
import time
import platform
import subprocess
from pathlib import Path

# ── sys.path PRIMEIRÍSSIMO ────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# ─────────────────────────────────────────────────────────────────────────────

import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QComboBox, QCheckBox, QGroupBox,
    QGridLayout, QScrollArea, QFrame, QLineEdit, QTextEdit,
    QTabWidget, QSpinBox, QDoubleSpinBox, QMessageBox,
    QStatusBar, QSizePolicy, QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui  import (QColor, QFont, QPainter, QLinearGradient,
                           QBrush, QPen, QPainterPath)

from bob.paths      import PATHS, load_json_safe, save_json_safe, ensure_dirs
from bob.clothes    import CLOTHES_CATALOG, OUTFITS
from bob.toys       import TOYS_CATALOG
from bob.personality import Personality

ensure_dirs()
IS_WINDOWS = platform.system() == "Windows"

# ── Conjunto de ações válidas (para validação antes de enviar) ────────────────
VALID_ACTIONS = {
    "set_mood","set_gravity","set_speed","set_physics","teleport",
    "spawn_toy","remove_toys","equip_clothes","unequip_clothes","clear_clothes",
    "apply_outfit","set_animation","set_chaotic","party_mode","dance","jump",
    "say","set_size","reload_settings","restart","set_language","set_personality",
    "set_interact_windows","push_window","set_user_name",
}


def _send(action: str, params: dict = None) -> bool:
    """
    Envia um comando para o Bob via commands.json.
    Valida o action antes de enviar.
    Retorna True se enviado, False se inválido ou erro.
    """
    # Validação
    if action not in VALID_ACTIONS:
        print(f"[Manager] Ação inválida ignorada: '{action}'")
        return False

    try:
        cmd_path = PATHS["commands"]
        cmd_path.parent.mkdir(parents=True, exist_ok=True)

        cmds = []
        if cmd_path.exists():
            try:
                raw = cmd_path.read_text(encoding="utf-8").strip()
                if raw:
                    cmds = json.loads(raw)
                    if not isinstance(cmds, list):
                        cmds = []
            except (json.JSONDecodeError, Exception):
                cmds = []

        cmds.append({
            "action": action,
            "params": params if isinstance(params, dict) else {},
            "time":   time.time(),
        })

        cmd_path.write_text(
            json.dumps(cmds, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return True
    except Exception as e:
        print(f"[Manager] Erro ao enviar '{action}': {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  TEMA
# ═══════════════════════════════════════════════════════════════════════════════

STYLE = """
QMainWindow,QWidget{background:#0d0d1e;color:#dde0f0;
    font-family:'Segoe UI',Arial;font-size:13px;}
QTabWidget::pane{border:1px solid #1e1e42;border-radius:6px;background:#111128;}
QTabBar::tab{background:#161630;color:#666;padding:9px 22px;
    border-radius:6px 6px 0 0;margin-right:3px;font-size:12px;}
QTabBar::tab:selected{background:#5B9BD5;color:#fff;font-weight:bold;}
QTabBar::tab:hover:!selected{background:#1e1e3e;color:#aaa;}
QGroupBox{border:1px solid #1e1e42;border-radius:8px;margin-top:14px;
    padding:12px 8px 8px 8px;background:#111128;font-weight:bold;color:#5B9BD5;}
QGroupBox::title{subcontrol-origin:margin;left:14px;padding:0 6px;}
QPushButton{background:#1a1a38;color:#bbb;border:1px solid #2e2e5e;
    border-radius:8px;padding:8px 14px;}
QPushButton:hover{background:#232350;border-color:#5B9BD5;color:#fff;}
QPushButton:pressed{background:#5B9BD5;color:#fff;border:none;}
QSlider::groove:horizontal{height:6px;background:#1a1a38;border-radius:3px;}
QSlider::handle:horizontal{background:#5B9BD5;width:16px;height:16px;
    margin:-5px 0;border-radius:8px;}
QSlider::sub-page:horizontal{background:#5B9BD5;border-radius:3px;}
QComboBox{background:#1a1a38;border:1px solid #2e2e5e;
    border-radius:6px;padding:6px 10px;color:#ddd;}
QComboBox:hover{border-color:#5B9BD5;}
QComboBox QAbstractItemView{background:#1a1a38;border:1px solid #5B9BD5;
    color:#ddd;selection-background-color:#5B9BD5;}
QCheckBox{color:#ccc;spacing:8px;}
QCheckBox::indicator{width:16px;height:16px;border:1px solid #5B9BD5;
    border-radius:4px;background:#1a1a38;}
QCheckBox::indicator:checked{background:#5B9BD5;}
QLineEdit,QTextEdit,QSpinBox,QDoubleSpinBox{background:#1a1a38;
    border:1px solid #2e2e5e;border-radius:6px;padding:6px;color:#ddd;}
QLineEdit:focus,QTextEdit:focus{border-color:#5B9BD5;}
QScrollBar:vertical{background:#111128;width:8px;border-radius:4px;}
QScrollBar::handle:vertical{background:#2e2e5e;border-radius:4px;min-height:20px;}
QScrollBar::handle:vertical:hover{background:#5B9BD5;}
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}
QStatusBar{background:#080818;color:#555;border-top:1px solid #1e1e42;}
QProgressBar{background:#1a1a38;border:1px solid #2e2e5e;border-radius:4px;
    text-align:center;color:#fff;height:12px;}
QProgressBar::chunk{background:#5B9BD5;border-radius:4px;}
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  Status Widget
# ═══════════════════════════════════════════════════════════════════════════════

class StatusWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame{background:#111128;border:1px solid #1e1e42;border-radius:10px;padding:4px;}")
        lay = QHBoxLayout(self); lay.setSpacing(16)

        self.dot = QLabel("●"); self.dot.setStyleSheet("font-size:20px;color:#555;")
        lay.addWidget(self.dot)

        col = QVBoxLayout(); col.setSpacing(2)
        self.lbl_status = QLabel("Bob: Offline")
        self.lbl_status.setStyleSheet("font-weight:bold;color:#555;")
        col.addWidget(self.lbl_status)
        self.lbl_mood = QLabel("Humor: --")
        self.lbl_mood.setStyleSheet("color:#888;font-size:12px;")
        col.addWidget(self.lbl_mood)
        self.lbl_anim = QLabel("Animação: --")
        self.lbl_anim.setStyleSheet("color:#888;font-size:12px;")
        col.addWidget(self.lbl_anim)
        lay.addLayout(col)
        lay.addStretch()

        col2 = QVBoxLayout(); col2.setSpacing(2)
        self.lbl_pos  = QLabel("Pos: --")
        self.lbl_idle = QLabel("Ocioso: --")
        self.lbl_toys = QLabel("Brinquedos: --")
        self.lbl_lang = QLabel("Linguagem: --")
        self.lbl_pers = QLabel("Pers: --")
        for lb in (self.lbl_pos,self.lbl_idle,self.lbl_toys,self.lbl_lang,self.lbl_pers):
            lb.setStyleSheet("color:#555;font-size:11px;"); col2.addWidget(lb)
        lay.addLayout(col2)

        col3 = QVBoxLayout(); col3.setSpacing(4)
        row_cpu = QHBoxLayout()
        lbl_c = QLabel("CPU:"); lbl_c.setStyleSheet("color:#555;font-size:11px;"); lbl_c.setFixedWidth(32)
        self.pb_cpu = QProgressBar(); self.pb_cpu.setFixedWidth(90); self.pb_cpu.setRange(0,100); self.pb_cpu.setTextVisible(False)
        row_cpu.addWidget(lbl_c); row_cpu.addWidget(self.pb_cpu)
        row_ram = QHBoxLayout()
        lbl_r = QLabel("RAM:"); lbl_r.setStyleSheet("color:#555;font-size:11px;"); lbl_r.setFixedWidth(32)
        self.pb_ram = QProgressBar(); self.pb_ram.setFixedWidth(90); self.pb_ram.setRange(0,100); self.pb_ram.setTextVisible(False)
        row_ram.addWidget(lbl_r); row_ram.addWidget(self.pb_ram)
        col3.addLayout(row_cpu); col3.addLayout(row_ram)
        lay.addLayout(col3)

    def refresh(self):
        """Atualiza via QTimer — não bloqueia UI."""
        try:
            state = load_json_safe("state")
            online = state.get("running", False)
            self.dot.setStyleSheet(f"font-size:20px;color:{'#2ecc71' if online else '#e74c3c'};")
            self.lbl_status.setText(f"Bob: {'Online ✓' if online else 'Offline ✗'}")
            self.lbl_status.setStyleSheet(f"font-weight:bold;color:{'#2ecc71' if online else '#e74c3c'};")
            icons = {"happy":"😊","bored":"😑","excited":"🎉","sleepy":"😴",
                     "angry":"😠","sad":"😢","playful":"😜"}
            mood = state.get("mood","--")
            self.lbl_mood.setText(f"Humor: {icons.get(mood,'')} {mood}")
            self.lbl_anim.setText(f"Animação: {state.get('animation','--')}")
            self.lbl_pos.setText(f"Pos: ({state.get('x','?')}, {state.get('y','?')})")
            self.lbl_idle.setText(f"Ocioso: {int(state.get('idle_time',0))}s")
            self.lbl_toys.setText(f"Brinquedos: {state.get('toys_on_screen',0)}")
            self.lbl_lang.setText(f"Lang: {state.get('language_mode','--')}")
            self.lbl_pers.setText(f"Pers: {state.get('personality','--')}")
            sys_info = state.get("system", {})
            self.pb_cpu.setValue(int(sys_info.get("cpu",0)))
            self.pb_ram.setValue(int(sys_info.get("ram",0)))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
#  Console
# ═══════════════════════════════════════════════════════════════════════════════

class ConsoleWidget(QWidget):
    HELP = """╔═════════════════════════════════════════════╗
║       CONSOLE DO BOB  v3  (estável)          ║
╠═════════════════════════════════════════════╣
║  mood <happy|bored|excited|sleepy|          ║
║       angry|playful|sad>                    ║
║  gravity <0.0-3.0>  speed <0.5-15.0>        ║
║  jump  dance  wave  spin  sit               ║
║  party   chaos on|off                       ║
║  say <texto>                                ║
║  spawn <ball|cube|star|food|doll>           ║
║  teleport <x> <y>   size <40-300>           ║
║  restart  anim <nome>  toys remove          ║
║  outfit <heroi|rei|elegante|cool|casual>    ║
║  lang children|adult                        ║
║  pers <playful|lazy|curious|chaotic|calm>   ║
║  push_window  name <nome>  status           ║
╚═════════════════════════════════════════════╝"""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)

        self.out = QTextEdit(); self.out.setReadOnly(True)
        self.out.setStyleSheet("""
            QTextEdit{background:#050510;color:#00e87a;
                font-family:'Consolas','Courier New',monospace;font-size:12px;
                border:1px solid #0a2a1a;border-radius:6px;}
        """)
        lay.addWidget(self.out)

        row = QHBoxLayout()
        pl = QLabel(">"); pl.setStyleSheet("color:#00e87a;font-family:monospace;font-size:15px;font-weight:bold;")
        row.addWidget(pl)
        self.inp = QLineEdit()
        self.inp.setStyleSheet("""
            QLineEdit{background:#050510;color:#00e87a;font-family:monospace;
                border:1px solid #0a2a1a;border-radius:4px;padding:5px 8px;}
        """)
        self.inp.setPlaceholderText("Digite um comando (help para ajuda)...")
        self.inp.returnPressed.connect(self._run)
        row.addWidget(self.inp)
        btn = QPushButton("▶"); btn.setFixedWidth(36); btn.clicked.connect(self._run)
        row.addWidget(btn)
        lay.addLayout(row)

        self._log("[Console] Pronto! Digite 'help'.", "#5B9BD5")

    def _log(self, text: str, color: str = "#00e87a"):
        try:
            safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            self.out.append(f'<span style="color:{color}">{safe}</span>')
        except Exception:
            pass

    def _run(self):
        try:
            raw = self.inp.text().strip()
            if not raw: return
            self.inp.clear()
            self._log(f"> {raw}", "#ffffff")
            self._parse(raw)
        except Exception as e:
            self._log(f"✗ Erro: {e}", "#ff6666")

    def _parse(self, raw: str):
        try:
            parts = raw.split()
            cmd   = parts[0].lower()

            if cmd == "help":
                self._log(self.HELP.replace("\n","<br>"), "#aaaaff"); return

            if cmd == "status":
                state = load_json_safe("state")
                for k,v in state.items():
                    if k != "system":
                        self._log(f"  {k}: {v}", "#aaffaa")
                return

            # Mapa simples
            simple = {
                "jump":    ("jump",  {},                    "⬆️ Bob pulou!"),
                "dance":   ("dance", {},                    "💃 Dançando!"),
                "wave":    ("set_animation",{"anim":"wave"},"👋 Acenando!"),
                "spin":    ("set_animation",{"anim":"spin"},"🌀 Girando!"),
                "sit":     ("set_animation",{"anim":"sit"}, "🪑 Sentado!"),
                "party":   ("party_mode",{},               "🎉 MODO FESTA!"),
                "restart": ("restart",{},                  "↺ Reiniciado!"),
                "push_window":("push_window",{},           "💪 Empurrou!"),
            }
            if cmd in simple:
                action,params,msg = simple[cmd]
                ok = _send(action, params)
                self._log(f"{'✓' if ok else '✗'} {msg}", "#ffdd44" if ok else "#ff6666")
                return

            if cmd == "mood" and len(parts) > 1:
                _send("set_mood",{"mood":parts[1]}); self._log(f"✓ Humor → {parts[1]}", "#ffdd44"); return

            if cmd == "gravity" and len(parts) > 1:
                try:
                    v = float(parts[1])
                    if 0 <= v <= 5:
                        _send("set_gravity",{"value":v}); self._log(f"✓ Gravidade → {v}", "#ffdd44")
                    else:
                        self._log("✗ Valor deve ser entre 0 e 5", "#ff6666")
                except ValueError:
                    self._log("✗ Valor inválido", "#ff6666")
                return

            if cmd == "speed" and len(parts) > 1:
                try:
                    v = float(parts[1])
                    if 0.1 <= v <= 20:
                        _send("set_speed",{"value":v}); self._log(f"✓ Velocidade → {v}", "#ffdd44")
                    else:
                        self._log("✗ Valor deve ser entre 0.1 e 20", "#ff6666")
                except ValueError:
                    self._log("✗ Valor inválido", "#ff6666")
                return

            if cmd == "chaos" and len(parts) > 1:
                on = parts[1].lower() in ("on","1","true","yes")
                _send("set_chaotic",{"enabled":on})
                self._log(f"✓ Caos: {'ON 🌀' if on else 'OFF 😌'}", "#ffdd44"); return

            if cmd == "say" and len(parts) > 1:
                msg = " ".join(parts[1:])
                _send("say",{"text":msg,"duration":4.5})
                self._log(f"✓ Bob diz: '{msg}'", "#ffdd44"); return

            if cmd == "spawn" and len(parts) > 1:
                toy = parts[1]
                if toy not in TOYS_CATALOG:
                    self._log(f"✗ Brinquedo inválido. Use: {list(TOYS_CATALOG.keys())}", "#ff6666"); return
                _send("spawn_toy",{"type":toy}); self._log(f"✓ Spawn: {toy}", "#ffdd44"); return

            if cmd == "teleport" and len(parts) >= 3:
                try:
                    x,y = float(parts[1]),float(parts[2])
                    _send("teleport",{"x":x,"y":y}); self._log(f"✓ Teleporte → ({x},{y})", "#ffdd44")
                except ValueError:
                    self._log("✗ Coordenadas inválidas", "#ff6666")
                return

            if cmd == "size" and len(parts) > 1:
                try:
                    sz = int(parts[1])
                    if 40 <= sz <= 300:
                        _send("set_size",{"size":sz}); self._log(f"✓ Tamanho → {sz}px", "#ffdd44")
                    else:
                        self._log("✗ Tamanho deve ser entre 40 e 300", "#ff6666")
                except ValueError:
                    self._log("✗ Valor inválido", "#ff6666")
                return

            if cmd == "anim" and len(parts) > 1:
                _send("set_animation",{"anim":parts[1]}); self._log(f"✓ Animação → {parts[1]}", "#ffdd44"); return

            if cmd == "toys" and len(parts) > 1 and parts[1] == "remove":
                _send("remove_toys"); self._log("✓ Brinquedos removidos", "#ffdd44"); return

            if cmd == "outfit" and len(parts) > 1:
                _send("apply_outfit",{"outfit":parts[1]}); self._log(f"✓ Outfit → {parts[1]}", "#ffdd44"); return

            if cmd == "lang" and len(parts) > 1:
                mode = parts[1]
                if mode not in ("children","adult"):
                    self._log("✗ Use: lang children  ou  lang adult", "#ff6666"); return
                _send("set_language",{"mode":mode}); self._log(f"✓ Linguagem → {mode}", "#ffdd44"); return

            if cmd == "pers" and len(parts) > 1:
                name = parts[1]
                if name not in Personality.PERSONALITIES:
                    self._log(f"✗ Use: {list(Personality.PERSONALITIES.keys())}", "#ff6666"); return
                _send("set_personality",{"name":name}); self._log(f"✓ Personalidade → {name}", "#ffdd44"); return

            if cmd == "name" and len(parts) > 1:
                name = " ".join(parts[1:])
                _send("set_user_name",{"name":name}); self._log(f"✓ Nome → {name}", "#ffdd44"); return

            self._log(f"✗ Desconhecido: '{cmd}'. Digite help.", "#ff6666")

        except Exception as e:
            self._log(f"✗ Erro interno: {e}", "#ff6666")


# ═══════════════════════════════════════════════════════════════════════════════
#  Manager Window
# ═══════════════════════════════════════════════════════════════════════════════

class ManagerWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚙️ Bob Manager  v3  —  Painel de Controle")
        self.setMinimumSize(820, 680); self.resize(900, 760)
        self.setStyleSheet(STYLE)

        self.cfg = load_json_safe("settings")
        self._bob_proc = None

        self._build()

        # Status atualizado via QTimer — não bloqueia a UI
        self._poll = QTimer(self)
        self._poll.timeout.connect(self._refresh_status)
        self._poll.start(1000)

        self._status("Gerenciador v3 iniciado.")

    # ─── Build ────────────────────────────────────────────────────────────────

    def _build(self):
        central = QWidget(); self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(12,12,12,12); root.setSpacing(10)

        root.addWidget(self._header())
        self.status_w = StatusWidget()
        root.addWidget(self.status_w)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)
        self.tabs.addTab(self._tab_control(),     "🎮 Controle")
        self.tabs.addTab(self._tab_appearance(),  "👕 Aparência")
        self.tabs.addTab(self._tab_toys(),        "🎯 Brinquedos")
        self.tabs.addTab(self._tab_physics(),     "⚙️ Física")
        self.tabs.addTab(self._tab_personality(), "🧠 Personalidade")
        self.tabs.addTab(self._tab_settings(),    "🔧 Configurações")
        self.tabs.addTab(self._tab_memory(),      "💾 Memória")
        self.tabs.addTab(ConsoleWidget(),         "💻 Console")

        self.setStatusBar(QStatusBar())

    def _header(self):
        f = QFrame()
        f.setStyleSheet("QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #141428,stop:1 #0a1428);border-radius:10px;padding:8px;}")
        lay = QHBoxLayout(f)
        col = QVBoxLayout()
        t = QLabel("⚙️  Bob Manager"); t.setStyleSheet("font-size:20px;font-weight:bold;color:#5B9BD5;")
        col.addWidget(t)
        s = QLabel("Painel de controle — v3 Estável"); s.setStyleSheet("color:#666;font-size:12px;")
        col.addWidget(s); lay.addLayout(col); lay.addStretch()

        for label, fn, color in [
            ("▶ Iniciar Bob",   self._start_bob,     "#1a6630"),
            ("■ Parar Bob",     self._stop_bob,      "#8B2020"),
            ("✨ Iniciar Tudo", self._start_all,     "#4a1a8a"),
            ("↺ Reiniciar",     lambda: _send("restart"), "#2a2a5e"),
        ]:
            b = QPushButton(label)
            b.setStyleSheet(f"QPushButton{{background:{color};color:#fff;border:none;border-radius:8px;padding:9px 16px;font-weight:bold;}}QPushButton:hover{{opacity:0.85;}}")
            b.clicked.connect(fn); lay.addWidget(b)
        return f

    def _scroll(self):
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
        cnt = QWidget(); sc.setWidget(cnt)
        lay = QVBoxLayout(cnt); lay.setSpacing(12)
        return sc, lay

    # ── Controle ──────────────────────────────────────────────────────────────

    def _tab_control(self):
        sc, lay = self._scroll()

        g = QGroupBox("😊 Humor do Bob"); gl = QGridLayout(g)
        for i,(lbl,mid) in enumerate([("😊 Feliz","happy"),("🎉 Animado","excited"),("😑 Entediado","bored"),
                                       ("😴 Com Sono","sleepy"),("😠 Bravo","angry"),("😜 Brincalhão","playful"),("😢 Triste","sad")]):
            b = QPushButton(lbl); b.clicked.connect(lambda _,m=mid: _send("set_mood",{"mood":m}))
            gl.addWidget(b, i//3, i%3)
        lay.addWidget(g)

        g2 = QGroupBox("🎬 Animações"); gl2 = QGridLayout(g2)
        for i,(lbl,anim) in enumerate([("🧍 Idle","idle"),("🚶 Andar","walk"),("⬆️ Pular","jump"),("⬇️ Cair","fall"),
                                        ("😴 Dormir","sleep"),("🎮 Brincar","play"),("😱 Reagir","react"),("💃 Dançar","dance"),
                                        ("🤕 Tropeçar","trip"),("😠 Bravo","angry"),("👋 Acenar","wave"),("🌀 Girar","spin"),
                                        ("🪑 Sentar","sit"),("🌀 Caótico","chaotic")]):
            b = QPushButton(lbl); b.clicked.connect(lambda _,a=anim: _send("set_animation",{"anim":a}))
            gl2.addWidget(b, i//4, i%4)
        lay.addWidget(g2)

        g3 = QGroupBox("⚡ Ações Rápidas"); gl3 = QGridLayout(g3)
        for i,(lbl,action,params) in enumerate([
            ("⬆️ Pular","jump",{}),("💃 Dançar","dance",{}),
            ("🎉 Modo Festa","party_mode",{}),("🌀 Modo Caos","set_chaotic",{"enabled":True}),
            ("😌 Normal","set_chaotic",{"enabled":False}),("↺ Reiniciar","restart",{}),
            ("👋 Acenar","set_animation",{"anim":"wave"}),("🌀 Girar","set_animation",{"anim":"spin"}),
        ]):
            b = QPushButton(lbl); b.clicked.connect(lambda _,a=action,p=params: _send(a,p))
            gl3.addWidget(b, i//3, i%3)

        # Push window só no Windows
        if IS_WINDOWS:
            b = QPushButton("💪 Empurrar Janela")
            b.clicked.connect(lambda: _send("push_window"))
            gl3.addWidget(b, len([])//3, len([])%3)
        lay.addWidget(g3)

        # Teleporte
        g4 = QGroupBox("📍 Teletransporte"); g4l = QHBoxLayout(g4)
        g4l.addWidget(QLabel("X:"))
        self.tp_x = QSpinBox(); self.tp_x.setRange(0,3840); self.tp_x.setValue(500)
        g4l.addWidget(self.tp_x)
        g4l.addWidget(QLabel("Y:"))
        self.tp_y = QSpinBox(); self.tp_y.setRange(0,2160); self.tp_y.setValue(300)
        g4l.addWidget(self.tp_y)
        tb = QPushButton("📍 Teletransportar")
        tb.clicked.connect(lambda: _send("teleport",{"x":self.tp_x.value(),"y":self.tp_y.value()}))
        g4l.addWidget(tb); lay.addWidget(g4)

        # Falar
        g5 = QGroupBox("💬 Fazer Bob Falar"); g5l = QHBoxLayout(g5)
        self.say_in = QLineEdit(); self.say_in.setPlaceholderText("Frase para o Bob dizer...")
        self.say_in.returnPressed.connect(self._do_say)
        g5l.addWidget(self.say_in)
        sb = QPushButton("💬 Falar"); sb.clicked.connect(self._do_say)
        g5l.addWidget(sb); lay.addWidget(g5)

        lay.addStretch(); return sc

    # ── Aparência ─────────────────────────────────────────────────────────────

    def _tab_appearance(self):
        sc, lay = self._scroll()

        g = QGroupBox("📏 Tamanho do Bob"); gl = QHBoxLayout(g)
        self.sz_sl = QSlider(Qt.Orientation.Horizontal)
        self.sz_sl.setRange(40,250); self.sz_sl.setValue(self.cfg.get("bob_size",100))
        self.sz_lbl = QLabel(f"{self.cfg.get('bob_size',100)}px")
        self.sz_lbl.setStyleSheet("color:#FFD700;font-weight:bold;min-width:50px;")
        self.sz_sl.valueChanged.connect(lambda v: (
            self.sz_lbl.setText(f"{v}px"),
            _send("set_size",{"size":v}),
            self._save_k("bob_size",v),
        ))
        gl.addWidget(QLabel("Pequeno")); gl.addWidget(self.sz_sl)
        gl.addWidget(QLabel("Grande"));  gl.addWidget(self.sz_lbl)
        lay.addWidget(g)

        cg = QGroupBox("👕 Roupas Individuais"); cgl = QGridLayout(cg)
        for i,(iid,info) in enumerate(CLOTHES_CATALOG.items()):
            b = QPushButton(f"{info['emoji']} {info['name']}")
            b.setToolTip(info.get("description",""))
            b.setCheckable(True)
            b.toggled.connect(lambda chk,ii=iid: _send("equip_clothes" if chk else "unequip_clothes",{"item":ii}))
            cgl.addWidget(b, i//2, i%2)
        clr = QPushButton("❌ Tirar tudo")
        clr.setStyleSheet("background:#5a1a1a;color:#ff8888;")
        clr.clicked.connect(lambda: _send("clear_clothes"))
        cgl.addWidget(clr, (len(CLOTHES_CATALOG)+1)//2+1, 0, 1, 2)
        lay.addWidget(cg)

        og = QGroupBox("🎭 Outfits Completos"); ogl = QGridLayout(og)
        outfits = [(o,o.capitalize()) for o in OUTFITS if o != "nu"]
        for i,(oid,oname) in enumerate(outfits):
            b = QPushButton(f"🎭 {oname}")
            b.clicked.connect(lambda _,o=oid: _send("apply_outfit",{"outfit":o}))
            ogl.addWidget(b, i//3, i%3)
        nude = QPushButton("🚫 Remover Tudo")
        nude.setStyleSheet("background:#2a1a1a;color:#ff9999;")
        nude.clicked.connect(lambda: _send("clear_clothes"))
        ogl.addWidget(nude, (len(outfits)//3)+1, 0, 1, 3)
        lay.addWidget(og)

        lay.addStretch(); return sc

    # ── Brinquedos ────────────────────────────────────────────────────────────

    def _tab_toys(self):
        sc, lay = self._scroll()

        g = QGroupBox("🎯 Spawnar Brinquedos"); gl = QGridLayout(g)
        for i,(tid,info) in enumerate(TOYS_CATALOG.items()):
            b = QPushButton(f"{info['emoji']} {info['name']}")
            b.setToolTip(info.get("description",""))
            b.clicked.connect(lambda _,t=tid: _send("spawn_toy",{"type":t}))
            gl.addWidget(b, i//2, i%2)
        lay.addWidget(g)

        g2 = QGroupBox("🗑️ Controle"); g2l = QHBoxLayout(g2)
        rb = QPushButton("🗑️ Remover Todos os Brinquedos")
        rb.setStyleSheet("background:#5a1a1a;color:#ff8888;border:none;border-radius:8px;padding:10px;")
        rb.clicked.connect(lambda: _send("remove_toys"))
        g2l.addWidget(rb); lay.addWidget(g2)
        lay.addStretch(); return sc

    # ── Física ────────────────────────────────────────────────────────────────

    def _tab_physics(self):
        sc, lay = self._scroll()

        sliders = [
            ("🌍 Gravidade",           "gravity",           0,   300,  55, 100, "set_gravity"),
            ("💨 Velocidade",          "speed",            50,  1500, 400, 100, "set_speed"),
            ("⬇️ Vel. Terminal",       "terminal_velocity",500, 3000,1800, 100, None),
            ("🏀 Atrito",              "friction",          50,   100,  82, 100, None),
        ]
        for label,key,lo,hi,default,scale,cmd in sliders:
            g = QGroupBox(label); gl = QHBoxLayout(g)
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setRange(lo,hi)
            cur = int(float(self.cfg.get(key, default/scale)) * scale)
            sl.setValue(max(lo, min(hi, cur)))
            vl = QLabel(f"{cur/scale:.2f}"); vl.setStyleSheet("color:#FFD700;font-weight:bold;min-width:55px;")
            def on_change(v, k=key, sc=scale, lb=vl, c=cmd):
                real = v/sc
                lb.setText(f"{real:.2f}"); self._save_k(k,real)
                if c: _send(c,{"value":real})
                else: _send("reload_settings")
            sl.valueChanged.connect(on_change)
            gl.addWidget(sl); gl.addWidget(vl); lay.addWidget(g)

        og = QGroupBox("⚙️ Opções"); ogl = QVBoxLayout(og)
        for lbl,key,default,cb in [
            ("Física Ativada","physics_enabled",True,lambda v: _send("set_physics",{"enabled":v})),
            ("Quicar nas Bordas","bounce_on_edges",True,None),
            ("Perseguir Cursor (gradual)","chase_cursor",False,None),
            ("Reagir à Proximidade","react_to_mouse_proximity",True,None),
            ("Interagir com Janelas (Windows)","interact_with_windows",False,
             lambda v: _send("set_interact_windows",{"enabled":v}) if IS_WINDOWS else None),
        ]:
            c = QCheckBox(lbl); c.setChecked(self.cfg.get(key,default))
            def make(k,extra):
                def fn(v):
                    self._save_k(k,v)
                    if extra: extra(v)
                return fn
            c.toggled.connect(make(key,cb))
            ogl.addWidget(c)
        lay.addWidget(og)

        br = QHBoxLayout()
        sb = QPushButton("💾 Salvar e Aplicar")
        sb.setStyleSheet("background:#1a4a2a;color:#80ff80;border:none;border-radius:8px;padding:10px 20px;font-weight:bold;")
        sb.clicked.connect(self._save_all)
        br.addWidget(sb)
        lay.addLayout(br)
        lay.addStretch(); return sc

    # ── Personalidade ─────────────────────────────────────────────────────────

    def _tab_personality(self):
        sc, lay = self._scroll()

        pg = QGroupBox("🎭 Preset"); pgl = QGridLayout(pg)
        for i,(pname,info) in enumerate(Personality.PERSONALITIES.items()):
            b = QPushButton(info["label"]); b.setToolTip(info["description"])
            b.clicked.connect(lambda _,n=pname: (_send("set_personality",{"name":n}), self._save_k("personality",n)))
            pgl.addWidget(b, i//2, i%2)
        lay.addWidget(pg)

        for label,key,default in [("⚡ Energia","personality_energy",70),
                                   ("🔍 Curiosidade","personality_curiosity",60),
                                   ("😴 Preguiça","personality_laziness",30),
                                   ("🌀 Caos","personality_chaos",20)]:
            g = QGroupBox(label); gl = QHBoxLayout(g)
            sl = QSlider(Qt.Orientation.Horizontal); sl.setRange(0,100); sl.setValue(self.cfg.get(key,default))
            vl = QLabel(f"{sl.value()}%"); vl.setStyleSheet("color:#FFD700;font-weight:bold;min-width:45px;")
            sl.valueChanged.connect(lambda v,k=key,lb=vl: (lb.setText(f"{v}%"), self._save_k(k,v)))
            gl.addWidget(sl); gl.addWidget(vl); lay.addWidget(g)

        lg = QGroupBox("💬 Modo de Linguagem"); lgl = QHBoxLayout(lg)
        for lbl,mode in [("👶 Crianças","children"),("🔞 Adultos","adult")]:
            b = QPushButton(lbl)
            b.clicked.connect(lambda _,m=mode: (_send("set_language",{"mode":m}), self._save_k("language_mode",m)))
            lgl.addWidget(b)
        lay.addWidget(lg)

        ab = QPushButton("✅ Aplicar ao Bob")
        ab.setStyleSheet("background:#1a3a5a;color:#88ccff;border:none;border-radius:8px;padding:10px;")
        ab.clicked.connect(lambda: (_send("reload_settings"), self._save_all()))
        lay.addWidget(ab)
        lay.addStretch(); return sc

    # ── Configurações ─────────────────────────────────────────────────────────

    def _tab_settings(self):
        sc, lay = self._scroll()

        bg = QGroupBox("🤖 Comportamento"); bgl = QVBoxLayout(bg)
        for lbl,key,default in [("Comportamento Automático","auto_behavior",True),
                                  ("Reagir à Proximidade","react_to_mouse_proximity",True),
                                  ("Mostrar Balões de Fala","show_speech_bubbles",True),
                                  ("Quicar nas Bordas","bounce_on_edges",True)]:
            c = QCheckBox(lbl); c.setChecked(self.cfg.get(key,default))
            c.toggled.connect(lambda v,k=key: self._save_k(k,v)); bgl.addWidget(c)
        tr = QHBoxLayout()
        tr.addWidget(QLabel("Entediar (min):"))
        bs = QSpinBox(); bs.setRange(1,60); bs.setValue(self.cfg.get("bored_timeout_minutes",5))
        bs.valueChanged.connect(lambda v: self._save_k("bored_timeout_minutes",v)); tr.addWidget(bs)
        tr.addWidget(QLabel("Dormir (min):"))
        ss = QSpinBox(); ss.setRange(1,120); ss.setValue(self.cfg.get("sleep_timeout_minutes",10))
        ss.valueChanged.connect(lambda v: self._save_k("sleep_timeout_minutes",v)); tr.addWidget(ss)
        bgl.addLayout(tr); lay.addWidget(bg)

        sysg = QGroupBox("🖥️ Alertas de Sistema"); sysgl = QVBoxLayout(sysg)
        c_sys = QCheckBox("Ativar alertas (CPU, bateria, internet)")
        c_sys.setChecked(self.cfg.get("system_alerts",True))
        c_sys.toggled.connect(lambda v: self._save_k("system_alerts",v)); sysgl.addWidget(c_sys)
        row_cpu = QHBoxLayout(); row_cpu.addWidget(QLabel("Alerta CPU (%):"))
        cpu_sp = QSpinBox(); cpu_sp.setRange(50,100); cpu_sp.setValue(self.cfg.get("cpu_alert_threshold",85))
        cpu_sp.valueChanged.connect(lambda v: self._save_k("cpu_alert_threshold",v))
        row_cpu.addWidget(cpu_sp); row_cpu.addStretch(); sysgl.addLayout(row_cpu); lay.addWidget(sysg)

        plg = QGroupBox("🔌 Plugins"); plgl = QVBoxLayout(plg)
        c_pl = QCheckBox("Ativar plugins da pasta /plugins")
        c_pl.setChecked(self.cfg.get("plugins_enabled",True))
        c_pl.toggled.connect(lambda v: self._save_k("plugins_enabled",v)); plgl.addWidget(c_pl)
        if IS_WINDOWS:
            pdir = QPushButton("📁 Abrir pasta de plugins")
            pdir.clicked.connect(lambda: os.startfile(str(PATHS["plugins"])))
            plgl.addWidget(pdir)
        lay.addWidget(plg)

        br = QHBoxLayout()
        svb = QPushButton("💾 Salvar Configurações")
        svb.setStyleSheet("background:#1a4a2a;color:#80ff80;border:none;border-radius:8px;padding:10px 20px;font-weight:bold;")
        svb.clicked.connect(self._save_all)
        rlb = QPushButton("🔄 Recarregar no Bob"); rlb.clicked.connect(lambda: _send("reload_settings"))
        br.addWidget(svb); br.addWidget(rlb); lay.addLayout(br)
        lay.addStretch(); return sc

    # ── Memória ───────────────────────────────────────────────────────────────

    def _tab_memory(self):
        sc, lay = self._scroll()

        ug = QGroupBox("👤 Usuário"); ugl = QHBoxLayout(ug)
        ugl.addWidget(QLabel("Nome:"))
        self.name_in = QLineEdit()
        mem = load_json_safe("memory")
        self.name_in.setText(mem.get("user_name",""))
        self.name_in.setPlaceholderText("Como Bob deve te chamar?")
        ugl.addWidget(self.name_in)
        sb = QPushButton("✅ Salvar")
        sb.clicked.connect(lambda: _send("set_user_name",{"name":self.name_in.text()}))
        ugl.addWidget(sb); lay.addWidget(ug)

        sg = QGroupBox("📊 Estatísticas"); sgl = QGridLayout(sg)
        self.mem_labels = {}
        for i,(key,label) in enumerate([
            ("times_interacted","Total Interações"),("times_clicked","Cliques"),
            ("times_dragged","Arrastos"),("toys_played","Brinquedos Usados"),
            ("times_jumped","Pulos"),("total_sessions","Sessões"),
            ("total_distance_walked","Distância (px)"),
        ]):
            sgl.addWidget(QLabel(f"{label}:"), i, 0)
            vl = QLabel(str(mem.get(key,0))); vl.setStyleSheet("color:#FFD700;font-weight:bold;")
            sgl.addWidget(vl, i, 1); self.mem_labels[key] = vl
        lay.addWidget(sg)

        ach = mem.get("achievements",[])
        if ach:
            ag = QGroupBox("🏆 Conquistas"); agl = QVBoxLayout(ag)
            for a in ach:
                agl.addWidget(QLabel(f"🏅 {a}"))
            lay.addWidget(ag)

        rb = QPushButton("🔄 Atualizar"); rb.clicked.connect(self._refresh_memory)
        lay.addWidget(rb); lay.addStretch(); return sc

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _do_say(self):
        try:
            txt = self.say_in.text().strip()
            if txt:
                _send("say",{"text":txt,"duration":4.5})
                self.say_in.clear()
        except Exception: pass

    def _save_k(self, key, val):
        self.cfg[key] = val

    def _save_all(self):
        try:
            save_json_safe("settings", self.cfg)
            _send("reload_settings")
            self._status("✅ Configurações salvas e aplicadas!")
        except Exception as e:
            self._status(f"❌ Erro ao salvar: {e}")

    def _refresh_status(self):
        try:
            self.status_w.refresh()
        except Exception:
            pass

    def _refresh_memory(self):
        try:
            mem = load_json_safe("memory")
            for key,lbl in self.mem_labels.items():
                val = mem.get(key,0)
                lbl.setText(f"{val:.1f}" if isinstance(val,float) else str(val))
        except Exception:
            pass

    def _status(self, msg: str):
        try:
            self.statusBar().showMessage(f"[{time.strftime('%H:%M:%S')}]  {msg}")
        except Exception:
            pass

    # ─── Bob Control ──────────────────────────────────────────────────────────

    def _start_bob(self):
        bob_script = PATHS["bob"] / "bob.py"
        if not bob_script.exists():
            QMessageBox.critical(self, "Erro", f"bob.py não encontrado:\n{bob_script}")
            return
        try:
            flags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
            self._bob_proc = subprocess.Popen([sys.executable, str(bob_script)], creationflags=flags)
            self._status("▶ Bob iniciado!")
        except TypeError:
            try:
                self._bob_proc = subprocess.Popen([sys.executable, str(bob_script)])
                self._status("▶ Bob iniciado!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível iniciar o Bob:\n{e}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível iniciar o Bob:\n{e}")

    def _stop_bob(self):
        try:
            if self._bob_proc and self._bob_proc.poll() is None:
                self._bob_proc.terminate()
                self._status("■ Bob encerrado.")
            else:
                self._status("ℹ️ Nenhuma instância gerenciada ativa.")
        except Exception as e:
            self._status(f"Aviso: {e}")

    def _start_all(self):
        self._start_bob()
        QTimer.singleShot(500, lambda: self._status("✨ Bob + Gerenciador rodando!"))


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Bob Manager")
    win = ManagerWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
