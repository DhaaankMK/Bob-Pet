"""
bob/bob.py  —  Bob Desktop Mascot  (v3 — Revisão de Estabilidade)

Correções aplicadas:
  1. sys.path via bob.paths no topo
  2. Pasta data/ auto-criada via ensure_dirs()
  3. Todos os caminhos de arquivo via PATHS (sem strings literais)
  4. QTimer para comportamento automático (sem loop infinito)
  5. Tarefas pesadas (monitor de sistema) em threads separadas
  6. Verificação de platform antes de APIs Windows
  7. try/except em TODOS os eventos críticos
  8. Perseguição ao mouse: movimento gradual (dx * 0.05), não teleporte
  9. Validação de comandos antes de executar
  10. Fallback para assets inexistentes
"""

import sys
import os
from pathlib import Path

# ── sys.path PRIMEIRÍSSIMO — antes de qualquer import local ──────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# ─────────────────────────────────────────────────────────────────────────────

import json
import math
import random
import time
import platform
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QWidget, QMenu, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui  import QPainter, QColor, QCursor, QAction, QFont, QMouseEvent

# ── Caminhos centralizados ────────────────────────────────────────────────────
from bob.paths import PATHS, load_json_safe, save_json_safe, ensure_dirs

# ── Subsistemas ───────────────────────────────────────────────────────────────
from bob.physics        import PhysicsEngine
from bob.animation      import AnimationSystem, AnimState
from bob.mood           import MoodSystem, Mood
from bob.chat           import ChatSystem
from bob.clothes        import ClothesSystem, CLOTHES_CATALOG, OUTFITS
from bob.toys           import ToyManager, TOYS_CATALOG
from bob.interaction    import InteractionHandler
from bob.memory         import MemorySystem
from bob.personality    import Personality
from bob.system_monitor import SystemMonitor
from bob.plugin_loader  import PluginLoader

# ── Garante estrutura de pastas ───────────────────────────────────────────────
ensure_dirs()

IS_WINDOWS = platform.system() == "Windows"


# ═══════════════════════════════════════════════════════════════════════════════
#  Chat Dialog
# ═══════════════════════════════════════════════════════════════════════════════

class ChatDialog(QDialog):
    """Janela de chat com o Bob."""

    def __init__(self, chat: ChatSystem, memory: MemorySystem, parent=None):
        super().__init__(parent)
        self.chat   = chat
        self.memory = memory
        self.setWindowTitle("💬 Conversar com Bob")
        self.setMinimumSize(380, 500)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self._build()
        self._load_history()

    def _build(self):
        self.setStyleSheet("""
            QDialog{background:#12122a;color:#e0e0e0;font-family:'Segoe UI',Arial;}
            QScrollArea{background:#12122a;border:none;}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12,12,12,12); lay.setSpacing(8)

        t = QLabel("💬 Chat com Bob")
        t.setStyleSheet("font-size:15px;font-weight:bold;color:#5B9BD5;padding:4px;")
        lay.addWidget(t)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.msg_w  = QWidget()
        self.msg_l  = QVBoxLayout(self.msg_w)
        self.msg_l.setSpacing(6); self.msg_l.addStretch()
        self.scroll.setWidget(self.msg_w)
        lay.addWidget(self.scroll)

        hint = QLabel("💡 /help para ver os comandos")
        hint.setStyleSheet("color:#445;font-size:11px;")
        lay.addWidget(hint)

        row = QHBoxLayout()
        self.inp = QLineEdit()
        self.inp.setPlaceholderText("Fale com Bob ou use /help...")
        self.inp.setStyleSheet("""
            QLineEdit{background:#1c1c38;color:#eee;font-size:13px;
                      border:2px solid #5B9BD5;border-radius:8px;padding:8px 12px;}
        """)
        self.inp.returnPressed.connect(self._send)
        row.addWidget(self.inp)

        btn = QPushButton("➤"); btn.setFixedSize(44,44)
        btn.setStyleSheet("""
            QPushButton{background:#5B9BD5;color:#fff;border-radius:8px;font-size:18px;}
            QPushButton:hover{background:#3A7FBF;}
        """)
        btn.clicked.connect(self._send); row.addWidget(btn)
        lay.addLayout(row)

    def _load_history(self):
        try:
            for msg in self.chat.get_history():
                self._add_msg(msg.get("text",""), msg.get("role") == "user")
        except Exception:
            pass

    def _add_msg(self, text: str, is_user: bool):
        try:
            lbl = QLabel(str(text))
            lbl.setWordWrap(True); lbl.setMaximumWidth(300)
            lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            bg = "#5B9BD5" if is_user else "#22224a"
            lbl.setStyleSheet(f"QLabel{{background:{bg};color:#fff;border-radius:12px;padding:8px 12px;font-size:13px;}}")
            row = QHBoxLayout(); row.setContentsMargins(0,0,0,0)
            if is_user: row.addStretch(); row.addWidget(lbl)
            else:       row.addWidget(lbl); row.addStretch()
            cnt = self.msg_l.count()
            if cnt > 0:
                it = self.msg_l.itemAt(cnt-1)
                if it and it.spacerItem():
                    self.msg_l.removeItem(it)
            self.msg_l.addLayout(row)
            self.msg_l.addStretch()
            QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
                self.scroll.verticalScrollBar().maximum()))
        except Exception:
            pass

    def _send(self):
        try:
            text = self.inp.text().strip()
            if not text: return
            self.inp.clear()
            self._add_msg(text, is_user=True)
            name     = self.memory.user_name
            response = self.chat.process(text, name)
            if response:
                QTimer.singleShot(380, lambda: self._add_msg(response, is_user=False))
        except Exception as e:
            print(f"[Chat] Erro ao enviar: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Bob Window
# ═══════════════════════════════════════════════════════════════════════════════

class BobWindow(QWidget):
    """Janela principal do mascote Bob."""

    def __init__(self):
        super().__init__()
        print("[Bob] 🎉 Iniciando v3...")

        # ── Carrega configurações ─────────────────────────────────────────────
        self.cfg = load_json_safe("settings")

        # ── Subsistemas ───────────────────────────────────────────────────────
        try:
            self.physics     = PhysicsEngine(self.cfg)
            self.anim        = AnimationSystem(self.cfg)
            self.mood        = MoodSystem(self.cfg)
            self.memory      = MemorySystem()
            self.personality = Personality(self.cfg)
            self.chat        = ChatSystem(self.cfg.get("language_mode","children"))
            self.clothes     = ClothesSystem(self.cfg.get("current_clothes",[]))
            self.toys        = ToyManager()
            self.interact    = InteractionHandler(self.cfg)
            self.sys_monitor = SystemMonitor(self.cfg)
            self.plugins     = PluginLoader()
        except Exception as e:
            print(f"[Bob] CRÍTICO ao iniciar subsistemas: {e}")
            raise

        # ── Chat: callback de comandos ─────────────────────────────────────
        self.chat.on_command_callback = self._handle_chat_command

        # ── Dimensões ─────────────────────────────────────────────────────────
        self._recalc_size()

        # ── Estado interno ────────────────────────────────────────────────────
        self._chaotic_mode  = False
        self._party_mode    = False
        self._party_timer   = 0.0
        self._paused        = False

        # Auto-comportamento
        self._walk_timer    = 0.0
        self._walk_dur      = 0.0
        self._walk_dir      = 0
        self._toy_timer     = 0.0
        self._action_timer  = 0.0

        # Perseguição ao mouse (movimento GRADUAL, não teleporte)
        self._chase_smooth_vx = 0.0
        self._chase_smooth_vy = 0.0

        # ── Janela ────────────────────────────────────────────────────────────
        self._setup_window()

        # ── Posição inicial ───────────────────────────────────────────────────
        try:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                sx  = self.cfg.get("start_position",{}).get("x",-1)
                sy  = self.cfg.get("start_position",{}).get("y",-1)
                if sx == -1 or sy == -1:
                    sx = geo.x() + geo.width()  - self._ww - 60
                    sy = geo.y() + geo.height() - self._wh - 60
                self.physics.x = float(sx)
                self.physics.y = float(sy)
            self.move(int(self.physics.x), int(self.physics.y))
        except Exception as e:
            print(f"[Bob] Aviso na posição inicial: {e}")
            self.move(200, 200)

        # ── Callbacks de interação ─────────────────────────────────────────
        self.interact.on_drag_start_callback = self._cb_drag_start
        self.interact.on_drag_end_callback   = self._cb_drag_end
        self.interact.on_click_callback      = self._cb_click
        self.interact.on_proximity_callback  = self._cb_proximity

        # ── Inicia subsistemas de background ──────────────────────────────
        try:
            self.sys_monitor.start()
        except Exception as e:
            print(f"[Bob] Aviso: monitor de sistema não iniciou: {e}")

        if self.cfg.get("plugins_enabled", True):
            try:
                self.plugins.load_all(self)
            except Exception as e:
                print(f"[Bob] Aviso: plugins não carregaram: {e}")

        # ── Timers ────────────────────────────────────────────────────────
        # Game loop ~60fps
        self._gt = QTimer(self)
        self._gt.timeout.connect(self._tick)
        self._gt.start(16)

        # Comportamento de IA a cada 4s (QTimer — nunca loop infinito)
        self._ai_timer = QTimer(self)
        self._ai_timer.timeout.connect(self._ai_step)
        self._ai_timer.start(4000)

        # Lê comandos do manager (5x/s)
        self._ct = QTimer(self)
        self._ct.timeout.connect(self._read_cmds)
        self._ct.start(200)

        # Salva estado 1x/s
        self._st = QTimer(self)
        self._st.timeout.connect(self._save_state)
        self._st.start(1000)

        # Personalidade auto-save
        self._pt = QTimer(self)
        self._pt.timeout.connect(self.personality.auto_save)
        self._pt.start(10000)

        # ── Saudação inicial ──────────────────────────────────────────────
        QTimer.singleShot(1400, self._greet)

        self._chat_dialog = None
        print("[Bob] ✅ Pronto!")

    # ─── Tamanho ──────────────────────────────────────────────────────────────

    def _recalc_size(self):
        try:
            s = int(self.cfg.get("bob_size",100) * self.cfg.get("scale",1.0))
            s = max(40, min(300, s))
            self._ww = int(s * 1.85)
            self._wh = int(s * 2.55)
            self.physics.bob_width  = self._ww
            self.physics.bob_height = self._wh
            self.anim.size  = self.cfg.get("bob_size",100)
            self.anim.scale = self.cfg.get("scale",1.0)
        except Exception as e:
            print(f"[Bob] Aviso ao calcular tamanho: {e}")
            self._ww = 185; self._wh = 255

    def _setup_window(self):
        try:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
            if not self.cfg.get("show_on_taskbar", False):
                self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, True)
            self.setFixedSize(self._ww, self._wh)
        except Exception as e:
            print(f"[Bob] Aviso ao configurar janela: {e}")

    # ─── Saudação ─────────────────────────────────────────────────────────────

    def _greet(self):
        try:
            msg = self.memory.get_greeting()
            self.mood.say(msg, 5.0)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════════
    #  Game Loop (~60fps)
    # ═══════════════════════════════════════════════════════════════════════════

    def _tick(self):
        if self._paused:
            return
        try:
            dt = 1.0 / 60.0

            # Cursor
            cur = QCursor.pos()
            self.interact.update_cursor(
                float(cur.x()), float(cur.y()),
                self.physics.x, self.physics.y,
                float(self._ww), float(self._wh)
            )

            # Alertas do sistema (não bloqueia UI — lê de lista thread-safe)
            for alert in self.sys_monitor.pop_alerts():
                try:
                    self.mood.on_system_alert(alert["message"], alert["mood"])
                except Exception:
                    pass

            # Física
            prev_ground = self.physics.on_ground
            self.physics.is_dragging = self.interact.is_dragging
            self.physics.update(dt)

            # Efeito de pouso
            if not prev_ground and self.physics.on_ground:
                self.anim.on_land()
                if abs(self.physics.vy) > 1.5:
                    try:
                        self.anim.spawn_particles(
                            self.physics.x + self._ww/2,
                            self.physics.y + self._wh - 4,
                            count=5, color="#A0C8FF"
                        )
                    except Exception:
                        pass

            # Comportamento contínuo (leve, a cada frame)
            if self.cfg.get("auto_behavior",True) and not self.interact.is_dragging:
                self._frame_behavior(dt)

            # Animação
            self.anim.update(dt)
            self._sync_anim()
            try:
                c1, c2 = self.mood.get_colors()
                self.anim.set_colors(c1, c2)
            except Exception:
                pass
            self.anim.chaotic_mode = self._chaotic_mode

            # Humor
            self.mood.update(dt)

            # Plugins (cada um protegido individualmente em plugin_loader)
            self.plugins.tick(self, dt)

            # Memória (auto-save)
            self.memory.update()
            try:
                if abs(self.physics.vx) > 0.5:
                    self.memory.add_walk_distance(abs(self.physics.vx) * dt)
            except Exception:
                pass

            # Party timer
            if self._party_mode:
                self._party_timer += dt
                if self._party_timer > 35.0:
                    self._party_mode  = False
                    self._party_timer = 0.0

            # Move widget
            self.move(int(self.physics.x), int(self.physics.y))
            self.update()

        except Exception as e:
            # O game loop NUNCA pode crashar
            print(f"[Bob] Aviso no tick: {e}")

    # ─── Comportamento por Frame (leve) ───────────────────────────────────────

    def _frame_behavior(self, dt: float):
        """
        Comportamento contínuo a cada frame.
        Leve — apenas perseguição ao mouse e caminhada.
        Ações espontâneas ficam no _ai_step() (QTimer 4s).
        """
        try:
            if self.mood.current_mood == Mood.SLEEPY:
                self.anim.set_state(AnimState.SLEEP); return

            if self._chaotic_mode:
                self.anim.set_state(AnimState.CHAOTIC)
                if random.random() < 0.02:
                    self.physics.apply_force(random.uniform(-6,6), random.uniform(-9,-2))
                return

            # Perseguição ao mouse — MOVIMENTO GRADUAL (não teleporte)
            if self.interact.chase_cursor:
                try:
                    dx, dy = self.interact.get_chase_direction(
                        self.physics.x, self.physics.y, float(self._ww), float(self._wh)
                    )
                    # Lerp suave: velocidade += (alvo - vel_atual) * 0.05
                    target_vx = dx * self.physics.speed * 1.2
                    self.physics.vx += (target_vx - self.physics.vx) * 0.05
                    if abs(dx) > 0.1:
                        self.anim.facing = "right" if dx > 0 else "left"
                        self.anim.set_state(AnimState.WALK)
                except Exception:
                    pass
                return

            # Caminhada aleatória
            self._walk_timer += dt
            if self._walk_timer >= self._walk_dur:
                self._walk_timer = 0.0
                mn = self.cfg.get("random_walk_interval_min", 1.0)
                mx = self.cfg.get("random_walk_interval_max", 4.0)
                self._walk_dur = random.uniform(mn, mx)
                lazy = max(0, min(100, self.personality.laziness)) / 100.0
                choices = [-1] + [0]*int(1 + lazy*3) + [1]
                self._walk_dir = random.choice(choices)

            eff = self.physics.speed * self.personality.walk_speed_mult
            if self._walk_dir == -1:
                self.physics.vx = -eff
                self.anim.facing = "left"
                self.anim.set_state(AnimState.WALK)
            elif self._walk_dir == 1:
                self.physics.vx = eff
                self.anim.facing = "right"
                self.anim.set_state(AnimState.WALK)
            else:
                self.anim.set_state(AnimState.IDLE)

        except Exception as e:
            print(f"[Bob] Aviso em _frame_behavior: {e}")

    # ─── IA Step (QTimer 4s — sem loop infinito) ──────────────────────────────

    def _ai_step(self):
        """
        Ações espontâneas do Bob.
        Chamado pelo QTimer a cada 4 segundos.
        NÃO usa loop — nunca trava a interface.
        """
        try:
            if self._paused or self.interact.is_dragging:
                return
            if self.mood.current_mood == Mood.SLEEPY:
                return

            # Pulo ocasional
            jump_ch = self.cfg.get("auto_jump_chance", 0.04) * self.personality.jump_chance_mult
            if random.random() < jump_ch and self.physics.on_ground:
                self.physics.jump()
                self.memory.on_jump()

            # Personalidade preguiçosa dorme mais cedo
            if self.personality.should_sleep_early():
                self.mood.set_mood(Mood.SLEEPY)
                return

            # Ação aleatória da personalidade
            if self.personality.should_do_random_action():
                self._do_personality_action(self.personality.get_random_action())

            # Busca brinquedo próximo
            self._toy_timer += 4.0
            seek_interval = max(2.0, 8.0 / self.personality.toy_seek_mult)
            if self._toy_timer >= seek_interval and self.toys.count() > 0:
                self._toy_timer = 0.0
                toy, dist = self.toys.get_nearest(self.physics.x, self.physics.y)
                if toy and dist < 260:
                    dx = toy.px - self.physics.x
                    if abs(dx) > 24:
                        self.physics.vx = (1 if dx > 0 else -1) * self.physics.speed * 0.9
                        self.anim.facing = "right" if dx > 0 else "left"
                        self.anim.set_state(AnimState.WALK)
                    else:
                        toy.apply_force(random.uniform(-4,4), random.uniform(-7,-2))
                        self.mood.on_toy_play(toy.toy_type)
                        self.memory.on_toy_play(toy.toy_type)
                        self.anim.set_state(AnimState.PLAY)
                        try:
                            self.anim.spawn_particles(
                                self.physics.x+self._ww/2, self.physics.y+self._wh/2,
                                count=8, color="#FFD700"
                            )
                        except Exception:
                            pass

            # Limpa brinquedos que foram fechados
            self.toys.cleanup_dead()

        except Exception as e:
            print(f"[Bob] Aviso em _ai_step: {e}")

    def _do_personality_action(self, action: str):
        """Executa uma ação espontânea de personalidade."""
        try:
            actions = {
                "jump":        lambda: self.physics.jump() if self.physics.on_ground else None,
                "spin":        lambda: self.anim.set_state(AnimState.SPIN),
                "walk_random": lambda: setattr(self, "_walk_dir", random.choice([-1,1])),
                "seek_toy":    lambda: setattr(self, "_toy_timer", 999.0),
                "yawn":        lambda: self.mood.say("Bosteja... 😪", 2.5),
                "stretch":     lambda: (self.anim.set_state(AnimState.WAVE),
                                         self.mood.say("Espreguiça... 😌", 2.0)),
                "bounce":      lambda: self.physics.apply_force(random.uniform(-3,3), -7.5),
                "look_around": lambda: self.anim.set_state(AnimState.WAVE),
                "idle":        lambda: self.anim.set_state(AnimState.IDLE),
            }
            fn = actions.get(str(action))
            if fn:
                fn()
        except Exception:
            pass

    def _sync_anim(self):
        try:
            if self.interact.is_dragging:
                self.anim.set_state(AnimState.DRAG); return
            if self._paused or self._chaotic_mode or self._party_mode: return
            if self.mood.current_mood == Mood.SLEEPY: return
            if not self.physics.on_ground:
                if self.physics.vy > 2.5:
                    self.anim.set_state(AnimState.FALL)
                elif self.physics.vy < -2.5:
                    self.anim.set_state(AnimState.JUMP)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════════════════
    #  Eventos de Mouse
    # ═══════════════════════════════════════════════════════════════════════════

    def mousePressEvent(self, event: QMouseEvent):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                self.interact.on_mouse_press(event.pos(), event.globalPosition().toPoint())
                self.mood.on_click()
                self.memory.on_click()
                self.plugins.on_interaction(self, "click")
            elif event.button() == Qt.MouseButton.RightButton:
                self._context_menu(event.globalPosition().toPoint())
        except Exception as e:
            print(f"[Bob] Aviso em mousePressEvent: {e}")

    def mouseMoveEvent(self, event: QMouseEvent):
        try:
            if self.interact.is_dragging:
                new_pos = self.interact.on_mouse_move(event.globalPosition().toPoint())
                self.move(new_pos)
                self.physics.x  = float(new_pos.x())
                self.physics.y  = float(new_pos.y())
                self.physics.vx = 0.0
                self.physics.vy = 0.0
        except Exception as e:
            print(f"[Bob] Aviso em mouseMoveEvent: {e}")

    def mouseReleaseEvent(self, event: QMouseEvent):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                vx, vy = self.interact.on_mouse_release(event.globalPosition().toPoint())
                self.physics.throw(vx, vy)
                self.memory.on_drag()
                self.plugins.on_interaction(self, "release")
        except Exception as e:
            print(f"[Bob] Aviso em mouseReleaseEvent: {e}")

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        try:
            self._open_chat()
        except Exception:
            pass

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _cb_drag_start(self):
        try:
            self.mood.on_drag(); self.anim.set_state(AnimState.DRAG)
        except Exception: pass

    def _cb_drag_end(self, vx, vy):
        try:
            self.anim.set_state(AnimState.FALL if vy > 0 else AnimState.JUMP)
            self.anim.spawn_particles(
                self.physics.x+self._ww/2, self.physics.y,
                count=7, color="#A0C8FF")
        except Exception: pass

    def _cb_click(self):
        try: self.mood.on_click()
        except Exception: pass

    def _cb_proximity(self, dist: float):
        try:
            if self.mood.current_mood == Mood.SLEEPY:
                self.mood.set_mood(Mood.HAPPY)
                self.mood.say("Hm? Acordei! 👀", 2.5)
        except Exception: pass

    # ═══════════════════════════════════════════════════════════════════════════
    #  Menu de Contexto
    # ═══════════════════════════════════════════════════════════════════════════

    def _context_menu(self, pos: QPoint):
        try:
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu{background:#16162e;color:#e0e0e0;border:1px solid #5B9BD5;
                      border-radius:8px;padding:4px;}
                QMenu::item{padding:7px 20px;border-radius:4px;}
                QMenu::item:selected{background:#5B9BD5;color:#fff;}
                QMenu::separator{background:#2a2a5a;height:1px;margin:4px 8px;}
            """)

            def add(label, fn):
                a = QAction(label, self); a.triggered.connect(fn); menu.addAction(a)

            add("💬 Conversar com Bob", self._open_chat)
            menu.addSeparator()

            # Humores
            mm = menu.addMenu("😊 Humor")
            for mid, lbl in [("happy","😊 Feliz"),("excited","🎉 Animado"),
                              ("bored","😑 Entediado"),("sleepy","😴 Com Sono"),
                              ("angry","😠 Bravo"),("playful","😜 Brincalhão"),("sad","😢 Triste")]:
                a = QAction(lbl,self); a.triggered.connect(lambda _,m=mid: self.mood.set_mood_by_name(m))
                mm.addAction(a)

            # Roupas
            cm = menu.addMenu("👕 Roupas")
            for iid, info in CLOTHES_CATALOG.items():
                chk = "✓ " if self.clothes.is_equipped(iid) else "   "
                a = QAction(f"{chk}{info['emoji']} {info['name']}", self)
                a.triggered.connect(lambda _,i=iid: self.clothes.toggle(i))
                cm.addAction(a)
            cm.addSeparator()
            for oname in OUTFITS:
                if oname == "nu": continue
                a = QAction(f"🎭 {oname.capitalize()}", self)
                a.triggered.connect(lambda _,o=oname: self.clothes.apply_outfit(o))
                cm.addAction(a)
            a = QAction("❌ Tirar tudo", self); a.triggered.connect(self.clothes.clear)
            cm.addAction(a)

            # Brinquedos
            tm = menu.addMenu("🎯 Brinquedos")
            for tid, info in TOYS_CATALOG.items():
                a = QAction(f"{info['emoji']} {info['name']}", self)
                a.triggered.connect(lambda _,t=tid: self.toys.spawn(
                    t, gravity=float(self.cfg.get("gravity",0.55))))
                tm.addAction(a)
            tm.addSeparator()
            a = QAction("🗑️ Remover todos", self); a.triggered.connect(self.toys.remove_all)
            tm.addAction(a)

            menu.addSeparator()

            for aname, lbl in [("dance","💃 Dançar"),("wave","👋 Acenar"),
                                ("spin","🌀 Girar"),("sit","🪑 Sentar")]:
                add(lbl, lambda _=None, an=aname: self.anim.set_state_by_name(an))

            add("🎉 Modo Festa", self._party_start)
            lbl_chaos = "🔴 Desativar Caos" if self._chaotic_mode else "🌀 Modo Caótico"
            add(lbl_chaos, self._toggle_chaos)
            add("⬆️ Pular", self.physics.jump)
            menu.addSeparator()
            add("⚙️ Abrir Gerenciador", self._open_manager)
            add("❌ Fechar Bob", self.close)

            menu.exec(pos)
        except Exception as e:
            print(f"[Bob] Aviso no menu de contexto: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    #  Ações
    # ═══════════════════════════════════════════════════════════════════════════

    def _open_chat(self):
        try:
            if self._chat_dialog is None or not self._chat_dialog.isVisible():
                self._chat_dialog = ChatDialog(self.chat, self.memory, self)
            self._chat_dialog.show()
            self._chat_dialog.raise_()
            self._chat_dialog.activateWindow()
            self.mood.on_interaction()
        except Exception as e:
            print(f"[Bob] Aviso ao abrir chat: {e}")

    def _open_manager(self):
        mgr = PATHS.get("manager_py") or (_ROOT / "manager" / "manager.py")
        if not mgr.exists():
            mgr = _ROOT / "manager" / "manager.py"
        if not mgr.exists():
            print("[Bob] manager.py não encontrado")
            return
        try:
            flags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
            subprocess.Popen([sys.executable, str(mgr)], creationflags=flags)
        except TypeError:
            subprocess.Popen([sys.executable, str(mgr)])
        except Exception as e:
            print(f"[Bob] Erro ao abrir manager: {e}")

    def _toggle_chaos(self):
        try:
            self._chaotic_mode = not self._chaotic_mode
            if self._chaotic_mode:
                self.mood.say("CAOS TOTAL! 🌀😱", 3.0)
            else:
                self.mood.set_mood(Mood.HAPPY)
                self.mood.say("Ufa! Normal de volta! 😅", 3.0)
        except Exception: pass

    def _party_start(self):
        try:
            self._party_mode  = True
            self._party_timer = 0.0
            self.mood.set_mood(Mood.EXCITED)
            self.mood.say("PARTEEEE! 🎉🎊🎈", 4.0)
            self.anim.set_state(AnimState.DANCE)
            for tt in ["ball","star","star"]:
                self.toys.spawn(tt, gravity=float(self.cfg.get("gravity",0.55)))
            try:
                cx = self.physics.x + self._ww/2
                cy = self.physics.y + self._wh/2
                for _ in range(4):
                    self.anim.spawn_particles(cx, cy, count=14,
                        color=random.choice(["#FF6B6B","#FFD700","#7CD67C","#5B9BD5","#FF69B4"]))
            except Exception:
                pass
        except Exception as e:
            print(f"[Bob] Aviso em party_start: {e}")

    def _handle_chat_command(self, cmd: str):
        """Executa comandos vindos do chat. Valida antes de executar."""
        try:
            VALID_CMDS = {
                "dance":        lambda: self.anim.set_state(AnimState.DANCE),
                "sleep":        lambda: self.mood.set_mood(Mood.SLEEPY),
                "jump":         lambda: self.physics.jump(),
                "wave":         lambda: self.anim.set_state(AnimState.WAVE),
                "party_mode":   lambda: self._party_start(),
                "chaotic_on":   lambda: setattr(self,"_chaotic_mode",True),
                "chaotic_off":  lambda: setattr(self,"_chaotic_mode",False),
                "play":         lambda: self.anim.set_state(AnimState.PLAY),
                "mood_happy":   lambda: self.mood.set_mood(Mood.HAPPY),
                "mood_excited": lambda: self.mood.set_mood(Mood.EXCITED),
                "mood_sad":     lambda: self.mood.set_mood(Mood.SAD),
                "mood_bored":   lambda: self.mood.set_mood(Mood.BORED),
            }
            fn = VALID_CMDS.get(str(cmd))
            if fn:
                fn()
            # else: comando desconhecido — ignora silenciosamente
        except Exception as e:
            print(f"[Bob] Aviso ao executar comando de chat '{cmd}': {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    #  Comandos do Manager (via commands.json)
    # ═══════════════════════════════════════════════════════════════════════════

    # Tabela de comandos válidos para validação
    _VALID_ACTIONS = {
        "set_mood", "set_gravity", "set_speed", "set_physics", "teleport",
        "spawn_toy", "remove_toys", "equip_clothes", "unequip_clothes",
        "clear_clothes", "apply_outfit", "set_animation", "set_chaotic",
        "party_mode", "dance", "jump", "say", "set_size", "reload_settings",
        "restart", "set_language", "set_personality", "set_interact_windows",
        "push_window", "set_user_name",
    }

    def _read_cmds(self):
        try:
            cmd_path = PATHS["commands"]
            if not cmd_path.exists():
                return
            with open(cmd_path, encoding="utf-8") as f:
                raw = f.read().strip()
            if not raw:
                return
            cmds = json.loads(raw)
            if not isinstance(cmds, list) or not cmds:
                return
            for cmd in cmds:
                if isinstance(cmd, dict):
                    self._exec_cmd(cmd)
            # Limpa o arquivo
            with open(cmd_path, "w", encoding="utf-8") as f:
                json.dump([], f)
        except json.JSONDecodeError:
            # JSON inválido — limpa o arquivo
            try:
                with open(PATHS["commands"], "w", encoding="utf-8") as f:
                    json.dump([], f)
            except Exception:
                pass
        except Exception:
            pass

    def _exec_cmd(self, cmd: dict):
        """Valida e executa um comando. Nunca crasha."""
        try:
            action = str(cmd.get("action",""))
            # ── Validação ──
            if action not in self._VALID_ACTIONS:
                print(f"[Bob] Comando desconhecido ignorado: '{action}'")
                return
            p = cmd.get("params", {})
            if not isinstance(p, dict):
                p = {}

            # ── Executores ──
            def _mood():       self.mood.set_mood_by_name(str(p.get("mood","happy")))
            def _gravity():    self.physics.set_gravity(float(p.get("value",0.55)))
            def _speed():      self.physics.set_speed(float(p.get("value",4.0)))
            def _physics():    self.physics.set_physics_enabled(bool(p.get("enabled",True)))
            def _teleport():   self.physics.teleport(float(p.get("x",100)),float(p.get("y",100)))
            def _spawn_toy():  self.toys.spawn(str(p.get("type","ball")), gravity=float(p.get("gravity",0.55)))
            def _rm_toys():    self.toys.remove_all()
            def _equip():      self.clothes.equip(str(p.get("item","")))
            def _unequip():    self.clothes.unequip(str(p.get("item","")))
            def _clear_cl():   self.clothes.clear()
            def _outfit():     self.clothes.apply_outfit(str(p.get("outfit","")))
            def _anim():       self.anim.set_state_by_name(str(p.get("anim","idle")))
            def _chaotic():    setattr(self,"_chaotic_mode",bool(p.get("enabled",False)))
            def _party():      self._party_start()
            def _dance():      self.anim.set_state(AnimState.DANCE)
            def _jump():       self.physics.jump()
            def _say():        self.mood.say(str(p.get("text","")), float(p.get("duration",3.5)))
            def _size():       self._cmd_set_size(int(p.get("size",100)))
            def _reload():     self._reload_cfg()
            def _restart():    self._restart()
            def _lang():       self._set_language(str(p.get("mode","children")))
            def _pers():       self._set_personality(str(p.get("name","playful")))
            def _win_int():    setattr(self,"_interact_windows",bool(p.get("enabled",False)))
            def _push_win():   self._do_push_window()
            def _uname():      self.memory.set_user_name(str(p.get("name","")))

            handlers = {
                "set_mood": _mood, "set_gravity": _gravity, "set_speed": _speed,
                "set_physics": _physics, "teleport": _teleport, "spawn_toy": _spawn_toy,
                "remove_toys": _rm_toys, "equip_clothes": _equip, "unequip_clothes": _unequip,
                "clear_clothes": _clear_cl, "apply_outfit": _outfit, "set_animation": _anim,
                "set_chaotic": _chaotic, "party_mode": _party, "dance": _dance,
                "jump": _jump, "say": _say, "set_size": _size, "reload_settings": _reload,
                "restart": _restart, "set_language": _lang, "set_personality": _pers,
                "set_interact_windows": _win_int, "push_window": _push_win, "set_user_name": _uname,
            }
            fn = handlers.get(action)
            if fn:
                fn()
        except Exception as e:
            print(f"[Bob] Aviso ao executar '{cmd.get('action','')}': {e}")

    def _cmd_set_size(self, sz: int):
        try:
            self.cfg["bob_size"] = max(40, min(300, sz))
            self._recalc_size()
            self.setFixedSize(self._ww, self._wh)
        except Exception as e:
            print(f"[Bob] Aviso em set_size: {e}")

    def _set_language(self, mode: str):
        try:
            if mode not in ("children","adult"):
                mode = "children"
            self.cfg["language_mode"] = mode
            self.mood.set_language_mode(mode)
            self.chat.set_language_mode(mode)
        except Exception: pass

    def _set_personality(self, name: str):
        try:
            self.cfg["personality"] = name
            self.personality.set_personality(name)
            self.personality.save()
        except Exception: pass

    def _do_push_window(self):
        """Empurra a janela abaixo do Bob (apenas Windows)."""
        if not IS_WINDOWS:
            return
        try:
            hwnd = self.interact.get_window_under_bob(
                self.physics.x, self.physics.y, float(self._ww))
            if hwnd:
                self.interact.push_window(hwnd, random.choice([-30,30]))
                self.mood.say("Empurrei a janela! 💪", 2.5)
        except Exception: pass

    def _reload_cfg(self):
        try:
            self.cfg = load_json_safe("settings")
            self.physics.update_settings(self.cfg)
            self.interact.update_settings(self.cfg)
            self.mood.update_settings(self.cfg)
            self.personality.update_from_settings(self.cfg)
            self.physics.speed = float(self.cfg.get("speed",4.0)) * self.personality.walk_speed_mult
        except Exception as e:
            print(f"[Bob] Aviso ao recarregar cfg: {e}")

    def _restart(self):
        try:
            self.physics.teleport(200.0, 200.0)
            self.mood.set_mood(Mood.HAPPY)
            self.anim.set_state(AnimState.IDLE)
            self._chaotic_mode = False
            self._party_mode   = False
            self.mood.say("Reiniciei! Estou de volta! 🎉", 4.0)
        except Exception: pass

    # ═══════════════════════════════════════════════════════════════════════════
    #  Estado
    # ═══════════════════════════════════════════════════════════════════════════

    def _save_state(self):
        try:
            state = {
                "running":       True,
                "x":             int(self.physics.x),
                "y":             int(self.physics.y),
                "vx":            round(self.physics.vx, 2),
                "vy":            round(self.physics.vy, 2),
                "mood":          self.mood.current_mood.value,
                "animation":     self.anim.state.value,
                "clothes":       self.clothes.get_equipped(),
                "toys_on_screen":self.toys.count(),
                "is_dragging":   self.interact.is_dragging,
                "chaotic_mode":  self._chaotic_mode,
                "party_mode":    self._party_mode,
                "facing":        self.anim.facing,
                "phrase":        self.mood.current_phrase,
                "idle_time":     round(self.mood.idle_time, 1),
                "personality":   self.personality.name,
                "language_mode": self.cfg.get("language_mode","children"),
                "user_name":     self.memory.user_name,
                "system":        self.sys_monitor.get_status(),
            }
            save_json_safe("state", state)
        except Exception as e:
            print(f"[Bob] Aviso ao salvar state: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    #  Render
    # ═══════════════════════════════════════════════════════════════════════════

    def paintEvent(self, _):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            phrase = ""
            if self.cfg.get("show_speech_bubbles", True):
                phrase = self.mood.current_phrase or ""
            self.anim.draw(
                p, self._ww, self._wh,
                phrase=phrase,
                clothes=self.clothes.get_equipped(),
            )
        except Exception as e:
            print(f"[Bob] Aviso em paintEvent: {e}")
        finally:
            try:
                p.end()
            except Exception:
                pass

    def closeEvent(self, ev):
        print("[Bob] Encerrando...")
        try:
            # Timers
            for timer in [self._gt, self._ai_timer, self._ct, self._st, self._pt]:
                try: timer.stop()
                except Exception: pass
            # Salva estado offline
            save_json_safe("state", {"running": False})
            self.sys_monitor.stop()
            self.memory.force_save()
            self.personality.save()
            self.plugins.unload_all(self)
            self.toys.remove_all()
        except Exception as e:
            print(f"[Bob] Aviso ao encerrar: {e}")
        finally:
            ev.accept()


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    # Handler global de exceções não capturadas
    def global_exception_handler(exc_type, exc_value, exc_tb):
        import traceback
        print(f"[Bob] ERRO NÃO CAPTURADO: {exc_type.__name__}: {exc_value}")
        traceback.print_tb(exc_tb)
        # Não encerra o app — apenas loga

    sys.excepthook = global_exception_handler

    app = QApplication(sys.argv)
    app.setApplicationName("Bob Desktop Mascot")
    app.setQuitOnLastWindowClosed(True)
    bob = BobWindow()
    bob.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
