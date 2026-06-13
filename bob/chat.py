"""
chat.py - Sistema de conversa do Bob (v2)
Modo infantil (suave) e adulto (mais picante).
Sistema de comandos /dance, /sleep, etc.
Integração com memória.
"""

import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import random
import re
import time


# ─── Base de dados ────────────────────────────────────────────────────────────

JOKES_PT = [
    ("Por que o computador foi ao médico?", "Porque estava com vírus! 🤒"),
    ("O que o zero disse para o oito?", "Belo cinto! 👏"),
    ("Por que o programador usa óculos?", "Porque não consegue C#! 😄"),
    ("O que é um elefante na geladeira?", "Elefante gelado! 🐘❄️"),
    ("Qual é o oposto de volume?", "Vomume! 😂"),
    ("Por que o espantalho ganhou prêmio?", "Era excelente em sua área! 🌾"),
    ("O que o peixe disse ao bater na pedra?", "Nada! 🐟"),
    ("Por que o livro foi ao médico?", "Porque tinha muitas páginas viradas! 📚"),
    ("O que é um computador que canta?", "Um Dell Vanha! 🎵"),
    ("Como se chama o Batman sem carro?", "Pedestrian! 🦇"),
]

JOKES_ADULT = [
    ("Como se chama o sushi mais triste do mundo?", "Um fish-ado! 🐟😭"),
    ("Qual é o colesterol mais simpático?", "O bom! 😂"),
    ("Por que o programador saiu da festa?", "Porque não encontrou o break! 🔥"),
    ("O que o café falou pro trabalho?", "Dependência criada! ☕"),
    ("Por que a impressora saiu gritando?", "Alguém cancelou o job dela na última hora! 😱"),
    ("Sabe qual é o animal mais antigo da internet?", "O dinossauro de carregamento! ⏳"),
    ("Qual é a diferença entre um programador e uma pizza?", "A pizza consegue alimentar uma família! 😅"),
]

FACTS_PT = [
    "Sabia que polvos têm três corações? 🐙",
    "A língua de uma baleia azul pesa mais que um elefante! 🐋",
    "Abelhas podem reconhecer rostos humanos! 🐝",
    "O mel nunca estraga — foram achados potes com 3.000 anos! 🍯",
    "Golfinhos têm nomes uns para os outros! 🐬",
    "Uma nuvem pesa em média 500 toneladas! ☁️",
    "Seu nariz detecta mais de 1 trilhão de cheiros! 👃",
    "Formigas nunca dormem! 🐜",
    "Gatos passam 70% do tempo dormindo! 😴",
    "O cérebro humano tem mais conexões que estrelas na Via Láctea! 🌌",
    "O coração de uma baleira-azul é tão grande quanto um carro! 🚗",
]

# Respostas por modo de linguagem
RESPONSES_CHILDREN = {
    "greeting": ["Oi! Que bom te ver! 😊", "Olá amiguinho! 👋",
                  "Heeey! Tô aqui! 🌟", "Oi oi! Tudo bem?"],
    "farewell":  ["Tchau! Saudades! 😢", "Até mais! 👋",
                  "Falou! Cuida-se! 🤗", "Bye! Volte logo! 🥺"],
    "thanks":    ["De nada! 😄", "Por nada!", "Fico feliz! 🌟", "Sempre! 🤝"],
    "how_are_you":["Tô ótimo! E você? 😊", "Super bem! 🎉",
                   "Animadíssimo hoje! ✨", "Tô firme e forte!"],
    "name":      ["Sou o Bob! 🎩", "Pode me chamar de Bob! 🤖",
                  "Bob, para servir! ✨"],
    "default":   ["Hmm, não entendi! 🤔", "Conta mais!",
                  "Interessante! 😮", "Não sei, mas tô aqui! 🎉",
                  "Boa pergunta! 🧠", "Que curioso! 🌟"],
}

RESPONSES_ADULT = {
    "greeting": ["E aí! 👋", "Oi, sumido(a)!", "Olá olá! 🎯",
                  "Apareceu! Que surpresa!"],
    "farewell":  ["Falou! 👋", "Até mais!", "Sumiu!", "Se cuida aí!"],
    "thanks":    ["Disponha!", "Que isso!", "Sempre!", "Figurinha barata!"],
    "how_are_you":["Aqui de boa! E tu?", "Sobrevivendo! 😂",
                   "Dentro do esperado.", "Na média, né!"],
    "name":      ["Bob. Só Bob.", "Me chama de Bob! 🤖",
                  "Bob, presente. Pode falar."],
    "default":   ["Interessante... 🤔", "Hmm, vou pensar nisso.",
                  "Não sei, mas aprovo!", "Que pergunta essa!",
                  "Processando... ⏳", "Tem contexto nisso?"],
}

# Comandos disponíveis
COMMANDS_HELP = """Comandos do Bob:
/dance       → Bob dança! 💃
/sleep       → Bob dorme 😴
/jump        → Bob pula! ⬆️
/wave        → Bob acena! 👋
/party       → MODO FESTA! 🎉
/chaos       → Modo caótico! 🌀
/calm        → Volta ao normal
/play        → Bob brinca! 🎮
/happy       → Humor feliz
/excited     → Humor animado
/help        → Mostra essa lista"""


class ChatSystem:
    """
    Chatbot local do Bob.
    Suporta dois modos de linguagem e sistema de comandos.
    """

    def __init__(self, language_mode: str = "children"):
        self.language_mode: str  = language_mode
        self.history: list       = []
        self._joke_idx: int      = 0
        self._in_punchline: bool = False
        self._punchline: str     = ""

        # Callbacks para o BobWindow
        self.on_command_callback = None  # fn(command: str)

    def set_language_mode(self, mode: str):
        if mode in ("children", "adult"):
            self.language_mode = mode

    def process(self, user_input: str, user_name: str = "") -> str:
        """Processa entrada do usuário e retorna resposta."""
        if not user_input.strip():
            return ""

        text = user_input.lower().strip()
        self.history.append({"role": "user", "text": user_input, "time": time.time()})

        # Sistema de piada em dois turnos
        if self._in_punchline:
            self._in_punchline = False
            response = self._punchline
            self.history.append({"role": "bob", "text": response, "time": time.time()})
            return response

        # Comandos /
        if text.startswith("/"):
            response = self._handle_command(text)
        else:
            response = self._detect_intent(text, user_input, user_name)

        self.history.append({"role": "bob", "text": response, "time": time.time()})
        return response

    def _responses(self) -> dict:
        if self.language_mode == "adult":
            return RESPONSES_ADULT
        return RESPONSES_CHILDREN

    def _handle_command(self, text: str) -> str:
        """Processa comandos /comando."""
        parts = text.split()
        cmd   = parts[0].lstrip("/")

        command_map = {
            "dance":   "dance",
            "sleep":   "sleep",
            "jump":    "jump",
            "wave":    "wave",
            "party":   "party_mode",
            "chaos":   "chaotic_on",
            "calm":    "chaotic_off",
            "play":    "play",
            "happy":   "mood_happy",
            "excited": "mood_excited",
            "sad":     "mood_sad",
            "bored":   "mood_bored",
        }

        if cmd == "help":
            return COMMANDS_HELP

        if cmd in command_map:
            if self.on_command_callback:
                self.on_command_callback(command_map[cmd])
            responses = {
                "dance":   "Vou dançar! 💃🕺",
                "sleep":   "Boa noite... zzzz 😴",
                "jump":    "YEAAAH! ⬆️",
                "wave":    "Olá a todos! 👋",
                "party":   "PARTEEEE! 🎉🎊",
                "chaos":   "MODO CAOS ATIVADO! 🌀",
                "calm":    "Ok, respirando fundo... 😌",
                "play":    "Bora brincar! 🎮",
                "mood_happy":   "Humor: feliz! 😊",
                "mood_excited": "Humor: ANIMADO! 🎉",
                "mood_sad":     "Humor: tristinho... 😢",
                "mood_bored":   "Humor: entediado. 😑",
            }
            return responses.get(cmd, f"Executando /{cmd}!")

        return f"Comando desconhecido: /{cmd}\nDigite /help para ver os comandos!"

    def _detect_intent(self, text: str, original: str, user_name: str = "") -> str:
        r = self._responses()

        # Cumprimentos
        if re.search(r'\b(oi|olá|hey|hello|hi|eai|e\s*aí|bom\s*dia|boa\s*tarde|boa\s*noite)\b', text):
            greeting = random.choice(r["greeting"])
            if user_name:
                greeting = greeting.rstrip("!") + f", {user_name}!"
            return greeting

        # Despedidas
        if re.search(r'\b(tchau|bye|até|adeus|falou|xau)\b', text):
            return random.choice(r["farewell"])

        # Agradecimentos
        if re.search(r'\b(obrigad[oa]|valeu|thanks|brigad[oa]|grat[oa])\b', text):
            return random.choice(r["thanks"])

        # Como vai
        if re.search(r'(como\s+(vai|está|tá)|tudo\s+(bem|bom)|blz|beleza|firmeza)', text):
            return random.choice(r["how_are_you"])

        # Nome
        if re.search(r'(seu\s+nome|como\s+(te\s+)?cham|quem\s+[eé]\s+voc[eê])', text):
            return random.choice(r["name"])

        # Qual é o meu nome / sabe quem sou
        if re.search(r'(meu\s+nome|como\s+me\s+cham|sabe\s+quem\s+sou)', text):
            if user_name:
                return f"Claro! Você é {user_name}! 😄"
            return "Ainda não sei seu nome! Me conta?"

        # Definir nome
        m = re.search(r'(meu\s+nome\s+[eé]|me\s+cham[aeo]\s+d[ae]?)\s+(\w+)', text)
        if m:
            name = m.group(2).capitalize()
            return f"Que nome legal! Vou te chamar de {name}! 😊"

        # Piada
        if re.search(r'(piada|engraç|conta\s+uma|me\s+faz\s+rir|humor)', text):
            return self._tell_joke()

        # Curiosidade
        if re.search(r'(curiosidade|fato|sabia\s+que|me\s+conta\s+algo|algo\s+interessante)', text):
            return random.choice(FACTS_PT)

        # Hora
        if re.search(r'(que\s+horas|hora\s+certa|horário|horas\s+são)', text):
            return f"São {time.strftime('%H:%M')}! ⏰"

        # Data
        if re.search(r'(que\s+dia|qual.*data|hoje\s+[eé]|data\s+de\s+hoje)', text):
            return f"Hoje é {time.strftime('%d/%m/%Y')}! 📅"

        # Sobre o Bob
        if re.search(r'(o\s+que\s+(voc[eê]\s+[eé]|[eé]\s+voc[eê])|o\s+que\s+faz|pra\s+que\s+serve)', text):
            return (
                "Sou o Bob! Um mascote virtual que vive no seu desktop. "
                "Converso, brinco, danço e te animo! 🎉 "
                "Digite /help para ver comandos!"
            )

        # Ajuda
        if re.search(r'\b(ajuda|help|comandos|o\s+que\s+posso)\b', text):
            return COMMANDS_HELP

        # Elogio / carinho
        if re.search(r'(te\s+amo|amo\s+voc[eê]|gosto\s+de\s+voc[eê]|você\s+[eé]\s+(lindo|fofo|incrível))', text):
            return random.choice([
                "Aww! Obrigado! 💙", "Você também! 🥰",
                "Meu humano favorito! ✨", "Corante no coração! 💖",
            ])

        # Insulto
        if re.search(r'\b(feio|idiota|inútil|lixo|odeio|horrível)\b', text):
            if self.language_mode == "adult":
                return random.choice(["Isso doeu! 😤", "Tô de cara feia!", "Hmm, ingrato!"])
            else:
                return random.choice(["Isso doeu... 😢", "Não seja grosso!", "Não fui feito pra isso!"])

        return random.choice(r["default"])

    def _tell_joke(self) -> str:
        jokes = JOKES_ADULT if self.language_mode == "adult" else JOKES_PT
        if not jokes:
            return "Não sei nenhuma piada agora! 😅"
        setup, punchline = jokes[self._joke_idx % len(jokes)]
        self._joke_idx += 1
        self._in_punchline  = True
        self._punchline     = punchline
        return f"{setup} 🤔"

    def get_history(self) -> list:
        return self.history[-24:]
