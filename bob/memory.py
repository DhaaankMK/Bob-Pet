"""
bob/memory.py — Sistema de memória persistente do Bob (v2 estável)
Auto-cria data/memory.json se não existir.
Trata todos os erros de I/O sem crash.
"""
import sys
import time
from pathlib import Path

_THIS = Path(__file__).resolve().parent.parent
if str(_THIS) not in sys.path:
    sys.path.insert(0, str(_THIS))

from bob.paths import load_json_safe, save_json_safe


class MemorySystem:
    """Memória persistente do Bob entre sessões."""

    def __init__(self):
        self._data      = load_json_safe("memory")
        self._dirty     = False
        self._last_save = time.time()

        # Incrementa sessão
        try:
            self._data["total_sessions"] = self._data.get("total_sessions", 0) + 1
            self._data["last_session"]   = int(time.time())
            if self._data.get("first_run", True):
                self._data["first_run"] = False
            self._dirty = True
        except Exception as e:
            print(f"[Memory] Aviso na init: {e}")

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def user_name(self) -> str:
        return self._data.get("user_name", "")

    @property
    def is_first_run(self) -> bool:
        return self._data.get("first_run", False)

    @property
    def times_interacted(self) -> int:
        return self._data.get("times_interacted", 0)

    @property
    def favorite_toy(self) -> str:
        return self._data.get("favorite_toy", "")

    @property
    def total_sessions(self) -> int:
        return self._data.get("total_sessions", 1)

    # ── Setters ───────────────────────────────────────────────────────────────

    def set_user_name(self, name: str):
        try:
            self._data["user_name"] = str(name).strip()[:64]
            self._dirty = True
        except Exception:
            pass

    def set_favorite_toy(self, toy: str):
        try:
            self._data["favorite_toy"] = str(toy)
            self._dirty = True
        except Exception:
            pass

    # ── Eventos ───────────────────────────────────────────────────────────────

    def on_click(self):
        try:
            self._data["times_clicked"]    = self._data.get("times_clicked", 0) + 1
            self._data["times_interacted"] = self._data.get("times_interacted", 0) + 1
            self._dirty = True
        except Exception:
            pass

    def on_drag(self):
        try:
            self._data["times_dragged"]    = self._data.get("times_dragged", 0) + 1
            self._data["times_interacted"] = self._data.get("times_interacted", 0) + 1
            self._dirty = True
        except Exception:
            pass

    def on_toy_play(self, toy_type: str):
        try:
            self._data["toys_played"]   = self._data.get("toys_played", 0) + 1
            self._data["favorite_toy"]  = str(toy_type)
            self._dirty = True
        except Exception:
            pass

    def on_jump(self):
        try:
            self._data["times_jumped"] = self._data.get("times_jumped", 0) + 1
            self._dirty = True
        except Exception:
            pass

    def add_walk_distance(self, dist: float):
        try:
            if dist > 0:
                self._data["total_distance_walked"] = (
                    self._data.get("total_distance_walked", 0.0) + float(dist)
                )
                self._dirty = True
        except Exception:
            pass

    def add_conversation(self, user_text: str, bob_reply: str):
        try:
            convs = self._data.get("conversations", [])
            convs.append({
                "time": int(time.time()),
                "user": str(user_text)[:100],
                "bob":  str(bob_reply)[:100],
            })
            self._data["conversations"] = convs[-50:]
            self._dirty = True
        except Exception:
            pass

    def unlock_achievement(self, name: str) -> bool:
        try:
            ach = self._data.get("achievements", [])
            if name not in ach:
                ach.append(str(name))
                self._data["achievements"] = ach
                self._dirty = True
                return True
        except Exception:
            pass
        return False

    def get_all(self) -> dict:
        try:
            return dict(self._data)
        except Exception:
            return {}

    def get_greeting(self) -> str:
        try:
            name     = self.user_name
            sessions = self.total_sessions
            intrs    = self.times_interacted
            if name:
                if sessions <= 1:
                    return f"Oi {name}! Primeira vez? 😊"
                elif intrs > 100:
                    return f"Oi {name}! Saudades! 💙"
                else:
                    return f"Olá de novo, {name}! 👋"
            else:
                if sessions <= 1:
                    return "Oi! Sou o Bob! 😊 Como posso te chamar?"
                return "Olá! Que bom te ver! 👋"
        except Exception:
            return "Oi! 😊"

    # ── Persistência ──────────────────────────────────────────────────────────

    def update(self):
        """Salva se houver mudanças e 5s tiverem passado."""
        try:
            if self._dirty and time.time() - self._last_save > 5.0:
                self.force_save()
        except Exception:
            pass

    def force_save(self):
        try:
            save_json_safe("memory", self._data)
            self._dirty     = False
            self._last_save = time.time()
        except Exception as e:
            print(f"[Memory] Erro ao salvar: {e}")
