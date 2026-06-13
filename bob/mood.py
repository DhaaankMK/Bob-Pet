"""
mood.py - Sistema de humor do Bob (v2)
Modos de linguagem: children (suave) e adult (mais picante).
Integração com personalidade.
"""

import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import time
import random
from enum import Enum


class Mood(Enum):
    HAPPY    = "happy"
    BORED    = "bored"
    EXCITED  = "excited"
    SLEEPY   = "sleepy"
    ANGRY    = "angry"
    SAD      = "sad"
    PLAYFUL  = "playful"


MOOD_COLORS = {
    Mood.HAPPY:   ("#5B9BD5", "#3A7FBF"),
    Mood.BORED:   ("#9B9B9B", "#757575"),
    Mood.EXCITED: ("#F4A72A", "#D4871A"),
    Mood.SLEEPY:  ("#7B8FA8", "#5A6E85"),
    Mood.ANGRY:   ("#E05252", "#C03030"),
    Mood.SAD:     ("#6A8FA8", "#4A6F88"),
    Mood.PLAYFUL: ("#7CD67C", "#50B650"),
}

# ─── Frases por humor e modo de linguagem ─────────────────────────────────────

PHRASES = {
    "children": {
        Mood.HAPPY: [
            "Que dia lindo! 😊", "Estou super feliz! 🌟",
            "Vida boa! ✨", "Você é incrível!",
            "Tudo maravilhoso!", "Que alegria! 🎉",
            "Hehe! Adoro isso!", "😄 Sorrindo aqui!",
        ],
        Mood.BORED: [
            "Hmm... tédio total.", "Tem alguém aí? 👀",
            "Nada pra fazer...", "Bosteja...",
            "Cadê os brinquedos? 🎮", "Me dá atenção!",
            "Durma, Bob, dorme...", "Que demora!",
        ],
        Mood.EXCITED: [
            "UAU! Incrível! 🎊", "VAMOS LÁ! 🚀",
            "Isso é DEMAIS!", "YEP YEP YEP! 🥳",
            "WHEEE! Animado! 🎈", "Wooooo! 🎉",
            "Tô na vibe! 💥", "ÉPICO! 🌟",
        ],
        Mood.SLEEPY: [
            "Zzz... 💤", "Sono pesadinho...",
            "Só mais um segundo...", "Zzzz... hm?",
            "Tô com sono 😴", "Cama boa...",
        ],
        Mood.ANGRY: [
            "Pra lá! 😤", "Humph! Bravo!",
            "Isso me deixou bravo!", "GRR! 😠",
            "Não tô legal não!", "Bravíssimo! 😤",
        ],
        Mood.SAD: [
            "Estou tristinho... 😢", "Ninguém me dá bola.",
            "Saudade de brincar...", ";(",
            "Hoje não tá legal.", "Precisava de um abraço.",
        ],
        Mood.PLAYFUL: [
            "Pega eu se conseguir! 😜", "HORA DE BRINCAR! 🎮",
            "Vem brincar comigo! 🎉", "WHEEE! 🎈",
            "Sou VELOZ! ⚡", "Tentou me pegar? Hehe!",
        ],
    },
    "adult": {
        Mood.HAPPY: [
            "Hoje tá ótimo! 😊", "Cara, que dia bom!",
            "Feliz e sem motivo 😄", "Vida tá boa viu!",
            "Tô de boa! ✌️", "Meu humor: excelente!",
            "Humor aprovado! 👍", "Sem reclamação hoje!",
        ],
        Mood.BORED: [
            "Meu Deus, que tédio.", "Alguém me bota pra trabalhar.",
            "Vou contar os pixels aqui.", "Tédio nível máximo.",
            "Nada acontece nesse PC.", "Estou praticamente em coma.",
            "Isso é pior que reunião!", "Me manda um brinquedo pelo menos.",
        ],
        Mood.EXCITED: [
            "CARAMBA! QUE ISSO! 🔥", "ISSO É DEMAIS MEU!!!",
            "Tô vibrando aqui! 🚀", "Para tudo! OLHA ISSO!",
            "Energia 100%! 💥", "BORA! SEM FREIO! 🏎️",
            "Explodindo de animação!", "MODO TURBO ATIVADO! ⚡",
        ],
        Mood.SLEEPY: [
            "zzzz... cansei.", "Manda o café...",
            "Reunião às 8? Nope.", "Dorme quem pode.",
            "Já são 3am aqui não?", "Caindo de sono.",
        ],
        Mood.ANGRY: [
            "Que #%@! foi isso?! 😤", "Tô de cara feia aqui!",
            "Me testou, viu?! 😠", "Sério isso?!",
            "Perdi a paciência!", "OK chega, tô bravo!",
        ],
        Mood.SAD: [
            "Bah, que dia paia.", "Não tô legal não.",
            "Alguém me dá atenção?", "Hoje não foi o dia.",
            "Mood: lama.", "Vou ficar quieto aqui.",
        ],
        Mood.PLAYFUL: [
            "Tenta me pegar! Haha! 😜", "Modo: caos ativado!",
            "Bora bagunçar! 🎉", "Pegou nada! 😂",
            "Jogo de pega-pega! 🏃", "Velocidade: ridícula! ⚡",
        ],
    },
}


class MoodSystem:
    """
    Gerencia o humor do Bob com suporte a personalidade e modos de linguagem.
    """

    def __init__(self, settings: dict):
        self.current_mood: Mood  = Mood.HAPPY
        self.previous_mood: Mood = Mood.HAPPY

        self.bored_timeout: float = settings.get("bored_timeout_minutes", 5) * 60
        self.sleep_timeout: float = settings.get("sleep_timeout_minutes", 10) * 60
        self.language_mode: str   = settings.get("language_mode", "children")

        self.last_interaction: float = time.time()
        self.idle_time: float        = 0.0
        self.mood_start_time: float  = time.time()
        self.mood_duration: float    = 0.0

        self.phrase_timer: float    = 0.0
        self.phrase_interval: float = random.uniform(14.0, 42.0)
        self.current_phrase: str    = ""
        self.phrase_display_time: float = 0.0

        # Para personalidade chaotic — ações mais frequentes
        self._chaos_mult: float = 1.0

    def set_language_mode(self, mode: str):
        """'children' ou 'adult'."""
        if mode in ("children", "adult"):
            self.language_mode = mode

    def _phrases(self, mood: Mood) -> list:
        lang = self.language_mode if self.language_mode in PHRASES else "children"
        return PHRASES[lang].get(mood, ["Hmm..."])

    def update(self, dt: float):
        now = time.time()
        self.idle_time    = now - self.last_interaction
        self.mood_duration += dt

        self._auto_progress_mood()

        self.phrase_timer += dt
        if self.phrase_timer >= self.phrase_interval * self._chaos_mult:
            self.phrase_timer    = 0.0
            self.phrase_interval = random.uniform(14.0, 42.0)
            self._spontaneous_phrase()

        if self.phrase_display_time > 0:
            self.phrase_display_time -= dt
            if self.phrase_display_time <= 0:
                self.current_phrase = ""

    def _auto_progress_mood(self):
        if self.idle_time > self.sleep_timeout:
            if self.current_mood != Mood.SLEEPY:
                self.set_mood(Mood.SLEEPY)
        elif self.idle_time > self.bored_timeout:
            if self.current_mood not in (Mood.BORED, Mood.SLEEPY):
                self.set_mood(Mood.BORED)

    def _spontaneous_phrase(self):
        phrases = self._phrases(self.current_mood)
        if phrases:
            self.say(random.choice(phrases))

    # ── Eventos ───────────────────────────────────────────────────────────────

    def on_interaction(self):
        self.last_interaction = time.time()
        self.idle_time = 0.0
        if self.current_mood in (Mood.BORED, Mood.SLEEPY, Mood.SAD):
            self.set_mood(Mood.HAPPY)

    def on_click(self):
        self.on_interaction()
        if self.current_mood == Mood.HAPPY and random.random() < 0.28:
            self.set_mood(Mood.EXCITED)
        self.say(random.choice(["Oi! 👋", "Heeey!", "Oops!", "Hehe! 😄", "Opa!"]))

    def on_drag(self):
        self.on_interaction()
        lang = self.language_mode
        if lang == "adult":
            phrases = ["CARA!! 😱", "Eita raios!!", "Fica na boa!", "Me solta, mano!"]
        else:
            phrases = ["UAAAA! 😱", "Me solta!", "Voa! ✈️", "WHEEE!", "Heeelp!"]
        self.say(random.choice(phrases))

    def on_toy_play(self, toy_name: str = ""):
        self.on_interaction()
        self.set_mood(Mood.PLAYFUL)
        if toy_name:
            self.say(f"Amo brincar com {toy_name}! 🎉")
        else:
            self.say(random.choice(["Que divertido! 🎉", "YAY! 🎊", "Mais! Mais!"]))

    def on_system_alert(self, message: str, mood_hint: str):
        """Reage a alertas do sistema."""
        try:
            m = Mood(mood_hint)
            self.set_mood(m)
        except ValueError:
            pass
        self.say(message, duration=5.0)

    # ── Controles ─────────────────────────────────────────────────────────────

    def set_mood(self, mood: Mood):
        if self.current_mood != mood:
            self.previous_mood  = self.current_mood
            self.current_mood   = mood
            self.mood_start_time = time.time()
            self.mood_duration   = 0.0

    def set_mood_by_name(self, name: str):
        try:
            self.set_mood(Mood(name))
        except ValueError:
            pass

    def say(self, phrase: str, duration: float = 3.5):
        self.current_phrase      = phrase
        self.phrase_display_time = duration

    def get_colors(self) -> tuple:
        return MOOD_COLORS.get(self.current_mood, ("#5B9BD5", "#3A7FBF"))

    def set_chaos_mult(self, mult: float):
        """Personalidade caótica fala mais frequentemente."""
        self._chaos_mult = max(0.2, min(2.0, mult))

    def update_settings(self, settings: dict):
        self.bored_timeout = settings.get("bored_timeout_minutes", 5) * 60
        self.sleep_timeout = settings.get("sleep_timeout_minutes", 10) * 60
        self.language_mode = settings.get("language_mode", self.language_mode)

    def get_state(self) -> dict:
        return {
            "mood": self.current_mood.value,
            "idle_time": self.idle_time,
            "current_phrase": self.current_phrase,
        }
