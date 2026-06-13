"""
bob/system_monitor.py — Monitor de sistema para o Bob (v2 estável)

Correções:
  • Verificação de platform.system() antes de chamar APIs do Windows
  • try/except em todas as chamadas de sistema
  • Thread daemon para não bloquear encerramento
  • Sem imports condicionais no topo (evita ImportError)
"""
import sys
import time
import platform
import threading
from pathlib import Path

_THIS = Path(__file__).resolve().parent.parent
if str(_THIS) not in sys.path:
    sys.path.insert(0, str(_THIS))

# ── Verificações de disponibilidade ──────────────────────────────────────────
IS_WINDOWS = platform.system() == "Windows"

PSUTIL_OK = False
try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    pass

SOCKET_OK = False
try:
    import socket
    SOCKET_OK = True
except ImportError:
    pass

WIN32_OK = False
if IS_WINDOWS:
    try:
        import win32gui
        import win32process
        WIN32_OK = True
    except ImportError:
        pass

# ── Mapeamento de apps → reação ───────────────────────────────────────────────
APP_REACTIONS = {
    "steam":          ("🎮 Jogo detectado!",         "excited"),
    "leagueoflegends":("⚔️ LoL! Bob vai torcer!",    "excited"),
    "minecraft":      ("⛏️ Minecraft! Bob adora!",   "excited"),
    "roblox":         ("🎮 Roblox! Divertido!",       "excited"),
    "chrome":         ("🌐 Navegando na internet?",   "curious"),
    "firefox":        ("🦊 Firefox! Bom gosto!",      "curious"),
    "msedge":         ("🌐 Edge... que escolha.",     "bored"),
    "code":           ("💻 Codando! Bob respeita!",   "curious"),
    "pycharm":        ("🐍 PyCharm? Pythonista!",     "excited"),
    "notepad":        ("📝 Bloco de notas?",          "bored"),
    "excel":          ("📊 Excel... planilhas!",      "sleepy"),
    "vlc":            ("🎬 Assistindo vídeo!",        "excited"),
    "spotify":        ("🎵 Música! Bob quer dançar!", "playful"),
}


class SystemMonitor:
    """
    Monitora CPU, bateria, internet e app ativo em background.
    Roda em thread separada (daemon) para não bloquear o app.
    """

    def __init__(self, settings: dict = None):
        if settings is None:
            settings = {}
        self.enabled          = bool(settings.get("system_alerts", True))
        self.cpu_threshold    = float(settings.get("cpu_alert_threshold",    85))
        self.battery_threshold= float(settings.get("battery_alert_threshold",20))

        self.cpu_percent    : float = 0.0
        self.ram_percent    : float = 0.0
        self.battery_percent: float = -1.0
        self.is_charging    : bool  = True
        self.has_internet   : bool  = True
        self.active_app     : str   = ""
        self.active_app_name: str   = ""

        self._alerts : list          = []
        self._lock   : threading.Lock= threading.Lock()
        self._running: bool          = False
        self._thread : threading.Thread | None = None

        # Anti-spam: última vez que cada alerta foi disparado
        self._last_alert: dict = {
            "cpu": 0.0, "battery": 0.0, "net": 0.0
        }
        self._last_app: str = ""

    def start(self):
        """Inicia monitoramento em thread daemon."""
        if not PSUTIL_OK:
            return  # Sem psutil, monitoramento indisponível
        self._running = True
        self._thread  = threading.Thread(
            target=self._loop, daemon=True, name="BobSystemMonitor"
        )
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        """Loop principal de monitoramento (rodando em thread separada)."""
        while self._running:
            try:
                if self.enabled:
                    self._check_cpu()
                    self._check_battery()
                    self._check_internet()
                    if IS_WINDOWS and WIN32_OK:
                        self._check_active_app()
            except Exception as e:
                # Nunca deixa o monitor crashar silenciosamente
                pass
            time.sleep(6.0)  # Checa a cada 6 segundos

    # ── Checks individuais ────────────────────────────────────────────────────

    def _check_cpu(self):
        if not PSUTIL_OK:
            return
        try:
            self.cpu_percent = psutil.cpu_percent(interval=1)
            self.ram_percent = psutil.virtual_memory().percent
            now = time.time()
            if (self.cpu_percent > self.cpu_threshold and
                    now - self._last_alert["cpu"] > 60):
                self._last_alert["cpu"] = now
                self._push(
                    f"⚠️ CPU em {self.cpu_percent:.0f}%! Tô suando!",
                    "angry", "cpu_high"
                )
        except Exception:
            pass

    def _check_battery(self):
        if not PSUTIL_OK:
            return
        try:
            bat = psutil.sensors_battery()
            if bat is None:
                self.battery_percent = -1.0
                return
            self.battery_percent = bat.percent
            self.is_charging     = bat.power_plugged
            now = time.time()
            if (not self.is_charging and
                    self.battery_percent < self.battery_threshold and
                    now - self._last_alert["battery"] > 120):
                self._last_alert["battery"] = now
                icon = "🔋" if self.battery_percent > 10 else "🪫"
                self._push(
                    f"{icon} Bateria em {self.battery_percent:.0f}%! Carrega logo!",
                    "sad", "battery_low"
                )
        except Exception:
            pass

    def _check_internet(self):
        if not SOCKET_OK:
            return
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            was_offline = not self.has_internet
            self.has_internet = True
            now = time.time()
            if was_offline and now - self._last_alert["net"] > 30:
                self._last_alert["net"] = now
                self._push("📶 Internet voltou! Uhuuu!", "excited", "net_back")
        except OSError:
            was_online = self.has_internet
            self.has_internet = False
            now = time.time()
            if was_online and now - self._last_alert["net"] > 30:
                self._last_alert["net"] = now
                self._push("📵 Internet caiu... 😢", "sad", "net_down")
        except Exception:
            pass

    def _check_active_app(self):
        """Somente chamado quando IS_WINDOWS e WIN32_OK são True."""
        if not PSUTIL_OK:
            return
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid <= 0:
                return
            proc = psutil.Process(pid)
            app_name = proc.name().lower().replace(".exe", "")
            self.active_app_name = proc.name()

            if app_name != self._last_app:
                self._last_app  = app_name
                self.active_app = app_name
                for key, (msg, mood) in APP_REACTIONS.items():
                    if key in app_name:
                        self._push(msg, mood, f"app_{key}")
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception:
            pass

    def _push(self, message: str, mood: str, alert_id: str):
        with self._lock:
            self._alerts.append({
                "message": str(message),
                "mood":    str(mood),
                "id":      str(alert_id),
                "time":    time.time(),
            })

    def pop_alerts(self) -> list:
        """Thread-safe: retorna e limpa alertas pendentes."""
        with self._lock:
            alerts       = list(self._alerts)
            self._alerts = []
        return alerts

    def get_status(self) -> dict:
        return {
            "cpu":         self.cpu_percent,
            "ram":         self.ram_percent,
            "battery":     self.battery_percent,
            "charging":    self.is_charging,
            "internet":    self.has_internet,
            "active_app":  self.active_app_name,
            "is_windows":  IS_WINDOWS,
            "psutil_ok":   PSUTIL_OK,
        }
