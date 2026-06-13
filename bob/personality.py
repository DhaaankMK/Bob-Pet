"""
bob/personality.py — Sistema de personalidade do Bob (v2 estável)
Persiste em data/personality.json.
"""
import sys
import random
import time
from pathlib import Path

_THIS = Path(__file__).resolve().parent.parent
if str(_THIS) not in sys.path:
    sys.path.insert(0, str(_THIS))

from bob.paths import load_json_safe, save_json_safe


class Personality:
    """Personalidade configurável do Bob, com persistência em arquivo."""

    PERSONALITIES = {
        "playful": {
            "label": "😜 Brincalhão",
            "description": "Sempre animado e pronto para brincar!",
            "energy": 85, "curiosity": 70, "laziness": 15, "chaos": 40,
            "jump_chance_mult": 1.8, "walk_speed_mult": 1.3,
            "toy_seek_mult": 1.5, "phrase_interval_mult": 0.7,
        },
        "lazy": {
            "label": "😴 Preguiçoso",
            "description": "Prefere ficar parado e sonhar...",
            "energy": 25, "curiosity": 30, "laziness": 90, "chaos": 10,
            "jump_chance_mult": 0.3, "walk_speed_mult": 0.6,
            "toy_seek_mult": 0.4, "phrase_interval_mult": 1.8,
        },
        "curious": {
            "label": "🔍 Curioso",
            "description": "Sempre explorando e fazendo perguntas!",
            "energy": 65, "curiosity": 95, "laziness": 20, "chaos": 30,
            "jump_chance_mult": 1.0, "walk_speed_mult": 1.1,
            "toy_seek_mult": 2.0, "phrase_interval_mult": 0.8,
        },
        "chaotic": {
            "label": "🌀 Caótico",
            "description": "Totalmente imprevisível e louco!",
            "energy": 90, "curiosity": 80, "laziness": 5, "chaos": 95,
            "jump_chance_mult": 2.5, "walk_speed_mult": 1.6,
            "toy_seek_mult": 1.2, "phrase_interval_mult": 0.5,
        },
        "calm": {
            "label": "😌 Calmo",
            "description": "Tranquilo e ponderado.",
            "energy": 50, "curiosity": 50, "laziness": 50, "chaos": 10,
            "jump_chance_mult": 0.6, "walk_speed_mult": 0.9,
            "toy_seek_mult": 0.8, "phrase_interval_mult": 1.2,
        },
    }

    def __init__(self, settings: dict = None):
        if settings is None:
            settings = {}

        # Carrega do arquivo persistido
        saved = load_json_safe("personality")

        # Settings tem prioridade sobre o arquivo salvo
        p_name = settings.get("personality") or saved.get("name", "playful")
        self.set_personality(p_name)

        self.energy    = int(settings.get("personality_energy")    or saved.get("energy",    self._preset["energy"]))
        self.curiosity = int(settings.get("personality_curiosity") or saved.get("curiosity", self._preset["curiosity"]))
        self.laziness  = int(settings.get("personality_laziness")  or saved.get("laziness",  self._preset["laziness"]))
        self.chaos     = int(settings.get("personality_chaos")     or saved.get("chaos",     self._preset["chaos"]))

        self._last_save = 0.0

    def set_personality(self, name: str):
        """Define o preset de personalidade."""
        self.name     = name if name in self.PERSONALITIES else "playful"
        self._preset  = self.PERSONALITIES[self.name]

    def save(self):
        """Persiste a personalidade em data/personality.json."""
        try:
            save_json_safe("personality", {
                "name":      self.name,
                "energy":    self.energy,
                "curiosity": self.curiosity,
                "laziness":  self.laziness,
                "chaos":     self.chaos,
                "saved_at":  int(time.time()),
            })
        except Exception as e:
            print(f"[Personality] Erro ao salvar: {e}")

    def auto_save(self):
        """Salva a cada 10 segundos se houver mudanças."""
        now = time.time()
        if now - self._last_save > 10.0:
            self._last_save = now
            self.save()

    # ── Multiplicadores ───────────────────────────────────────────────────────

    @property
    def jump_chance_mult(self) -> float:
        try:
            return max(0.1, self._preset["jump_chance_mult"] * (self.energy / 70.0))
        except Exception:
            return 1.0

    @property
    def walk_speed_mult(self) -> float:
        try:
            base = self._preset["walk_speed_mult"]
            return max(0.2, base * (1.0 - self.laziness / 200.0))
        except Exception:
            return 1.0

    @property
    def toy_seek_mult(self) -> float:
        try:
            return max(0.1, self._preset["toy_seek_mult"] * (self.curiosity / 60.0))
        except Exception:
            return 1.0

    @property
    def phrase_interval_mult(self) -> float:
        try:
            return max(0.2, self._preset["phrase_interval_mult"])
        except Exception:
            return 1.0

    @property
    def random_action_chance(self) -> float:
        try:
            return max(0.0, (self.energy * 0.0003) * (1.0 - self.laziness / 150.0))
        except Exception:
            return 0.001

    def should_sleep_early(self) -> bool:
        try:
            return self.laziness > 70 and random.random() < 0.003
        except Exception:
            return False

    def should_do_random_action(self) -> bool:
        try:
            return random.random() < self.random_action_chance
        except Exception:
            return False

    def get_random_action(self) -> str:
        try:
            actions = []
            if self.energy > 50:     actions += ["jump", "walk_random", "spin"]
            if self.curiosity > 50:  actions += ["seek_toy", "look_around"]
            if self.chaos > 60:      actions += ["jump", "spin", "bounce"]
            if self.laziness > 60:   actions += ["idle", "yawn", "stretch"]
            return random.choice(actions) if actions else "idle"
        except Exception:
            return "idle"

    def update_from_settings(self, settings: dict):
        """Atualiza a partir de um dicionário de configurações."""
        try:
            if "personality" in settings:
                self.set_personality(settings["personality"])
            if "personality_energy"    in settings: self.energy    = int(settings["personality_energy"])
            if "personality_curiosity" in settings: self.curiosity = int(settings["personality_curiosity"])
            if "personality_laziness"  in settings: self.laziness  = int(settings["personality_laziness"])
            if "personality_chaos"     in settings: self.chaos     = int(settings["personality_chaos"])
        except Exception as e:
            print(f"[Personality] Erro ao atualizar: {e}")

    @staticmethod
    def get_all() -> dict:
        return Personality.PERSONALITIES
