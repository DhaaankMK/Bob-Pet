# 🤖 Bob Desktop Mascot

Um mascote virtual completo para o Windows Desktop, construído em **Python + PyQt6**.
Bob vive na sua área de trabalho, tem física real, humor, roupas, brinquedos e muito mais!

---

## 📁 Estrutura do Projeto

```
Scripts/
├── launcher.py              ← Ponto de entrada principal
├── requirements.txt         ← Dependências Python
├── install.bat              ← Instalador automático (Windows)
│
├── bob/                     ← Pacote principal do mascote
│   ├── bob.py               ← Janela do mascote (roda separado)
│   ├── physics.py           ← Motor de física (gravidade, colisão)
│   ├── animation.py         ← Sistema de animações (QPainter)
│   ├── mood.py              ← Sistema de humor e estados
│   ├── chat.py              ← Chatbot local do Bob
│   ├── clothes.py           ← Sistema de roupas
│   ├── toys.py              ← Sistema de brinquedos com física
│   └── interaction.py       ← Gerenciador de interações (mouse)
│
├── manager/
│   └── manager.py           ← Painel gerenciador completo
│
├── config/
│   └── settings.json        ← Configurações persistentes
│
├── data/
│   ├── state.json           ← Estado atual do Bob (lido pelo Manager)
│   └── commands.json        ← Fila de comandos Manager → Bob
│
└── assets/
    ├── sprites/             ← Sprites PNG opcionais do Bob
    ├── toys/                ← Sprites PNG opcionais dos brinquedos
    └── clothes/             ← Sprites PNG opcionais das roupas
```

---

## ⚡ Como Executar

### 1. Instalar dependências

**Opção A — Batch (Windows):**
```
Clique duas vezes em install.bat
```

**Opção B — Manual:**
```bash
pip install -r requirements.txt
```

### 2. Iniciar o Launcher
```bash
cd Scripts
python launcher.py
```

No Launcher você pode:
- **▶ Iniciar Bob** — Abre só o mascote
- **⚙️ Abrir Gerenciador** — Abre só o painel de controle
- **✨ Iniciar Tudo** — Abre Bob + Gerenciador juntos

### 3. Iniciar diretamente (sem Launcher)

**Só o Bob:**
```bash
python bob/bob.py
```

**Só o Gerenciador:**
```bash
python manager/manager.py
```

---

## 🎮 Interações com o Bob

| Ação | Efeito |
|------|--------|
| **Clique esquerdo** | Bob reage e fala |
| **Arrastar** | Segura e arremessa o Bob |
| **Duplo clique** | Abre o chat de conversa |
| **Clique direito** | Mini-menu de opções rápidas |
| **Mouse próximo** | Bob acorda se estiver dormindo |

---

## 😊 Estados de Humor

| Humor | Trigger | Comportamento |
|-------|---------|---------------|
| Feliz | Padrão | Passeia, sorri, frases animadas |
| Animado | Interação + sorte | Dança, pula, frases energéticas |
| Entediado | 5 min sem interação | Fica parado, reclama |
| Com Sono | 10 min sem interação | Dorme, Zzz flutuantes |
| Bravo | Contexto / comando | Treme, expressão carrancuda |
| Triste | Contexto | Expressão cabisbaixa |
| Brincalhão | Brincar com toy | Pula, sorri, busca brinquedos |

---

## 🎬 Animações Disponíveis

`idle` · `walk` · `jump` · `fall` · `sleep` · `play` · `react` · `dance` · `trip` · `angry` · `drag` · `chaotic`

---

## 👕 Roupas Disponíveis

| ID | Nome | Slot |
|----|------|------|
| `hat` | 🎩 Chapéu Preto | Cabeça |
| `glasses` | 🕶️ Óculos | Rosto |
| `shirt` | 👕 Camisa Vermelha | Corpo |
| `cape` | 🦸 Capa de Super-Herói | Costas |
| `crown` | 👑 Coroa | Cabeça |

### Como adicionar uma nova roupa

1. **Defina no catálogo** — `bob/clothes.py`, dicionário `CLOTHES_CATALOG`:
```python
"scarf": {
    "name": "Cachecol",
    "description": "Um cachecol estiloso.",
    "emoji": "🧣",
    "slot": "neck",
}
```

2. **Implemente o desenho** — `bob/animation.py`, método `_draw_clothes()`:
```python
elif item == "scarf":
    self._draw_scarf(p, cx, cy, unit)
```

3. **Crie o método de desenho** na classe `AnimationSystem`:
```python
def _draw_scarf(self, p, cx, cy, unit):
    p.setBrush(QBrush(QColor(220, 50, 50)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(cx - int(20*unit), cy - int(60*unit), int(40*unit), int(8*unit))
```

---

## 🎯 Brinquedos Disponíveis

| ID | Nome | Física |
|----|------|--------|
| `ball` | ⚽ Bola | Alta elasticidade |
| `cube` | 📦 Cubo | Baixa elasticidade |
| `star` | ⭐ Estrela | Flutuante |
| `food` | 🍕 Pizza | Pesada |
| `doll` | 🧸 Urso | Média |

### Como adicionar um novo brinquedo

1. **Defina no catálogo** — `bob/toys.py`, dicionário `TOYS_CATALOG`:
```python
"rocket": {
    "name": "Foguete",
    "emoji": "🚀",
    "description": "Um foguete veloz!",
    "color": "#FF6644",
    "size": 40,
    "bounce": 0.6,
    "gravity": 0.3,
}
```

2. **Implemente o desenho** — `bob/toys.py`, método `paintEvent()` da `ToyWidget`:
```python
elif self.toy_type == "rocket":
    self._draw_rocket(p, s, color)
```

3. **Crie o método `_draw_rocket()`** na classe `ToyWidget`.

---

## 🎬 Como adicionar novas animações

1. **Registre o estado** — `bob/animation.py`, enum `AnimState`:
```python
class AnimState(Enum):
    ...
    WAVE = "wave"   ← novo estado
```

2. **Mapeie a função de desenho** no dicionário `draw_fn` dentro de `draw()`:
```python
AnimState.WAVE: self._draw_wave,
```

3. **Implemente o método:**
```python
def _draw_wave(self, p, cx, cy, s):
    wave_offset = math.sin(self.tick * 4) * 10
    self._draw_body(p, cx, cy + int(wave_offset), s, arm_angle_l=-60)
```

---

## ⚙️ Configurações (settings.json)

| Chave | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `gravity` | float | 0.5 | Força da gravidade |
| `speed` | float | 2.5 | Velocidade de caminhada |
| `bob_size` | int | 100 | Tamanho do Bob em pixels |
| `scale` | float | 1.0 | Escala geral |
| `physics_enabled` | bool | true | Ativa/desativa física |
| `bounce_on_edges` | bool | true | Quica nas bordas |
| `chase_cursor` | bool | false | Persegue o cursor |
| `auto_behavior` | bool | true | Comportamento automático |
| `spawn_auto_toys` | bool | false | Spawn automático de toys |
| `bored_timeout_minutes` | int | 5 | Minutos até ficar entediado |
| `sleep_timeout_minutes` | int | 10 | Minutos até dormir |
| `show_speech_bubbles` | bool | true | Mostra balões de fala |
| `react_to_mouse_proximity` | bool | true | Reage ao cursor próximo |
| `mouse_proximity_radius` | int | 150 | Raio de proximidade (px) |

---

## 💻 Console de Comandos (Manager)

O Gerenciador possui um console integrado. Comandos disponíveis:

```
mood <happy|bored|excited|sleepy|angry|playful|sad>
gravity <valor>         → Ex: gravity 1.5
speed <valor>           → Ex: speed 4.0
jump
dance
party
chaos <on|off>
say <mensagem>          → Ex: say Olá mundo!
spawn <ball|cube|star|food|doll>
teleport <x> <y>        → Ex: teleport 500 300
size <valor>            → Ex: size 150
restart
anim <nome>             → Ex: anim dance
toys remove
help
```

---

## 🏗️ Arquitetura de Comunicação

```
Manager (manager.py)
    │
    │ Escreve em data/commands.json
    ▼
Bob (bob.py) — lê a cada 200ms e processa os comandos
    │
    │ Escreve em data/state.json (a cada 1s)
    ▼
Manager — lê state.json e atualiza a UI de status
```

---

## 📦 Dependências

| Biblioteca | Versão | Uso |
|-----------|--------|-----|
| PyQt6 | ≥ 6.4 | Interface, animações, janela |
| pywin32 | ≥ 305 | Integração Windows (opcional) |
| psutil | ≥ 5.9 | Monitoramento do sistema |

---

## 🚀 Roadmap / Futuras Expansões

- [ ] Integração com Claude API para chat avançado
- [ ] Sistema de sprites PNG customizados
- [ ] Múltiplos monitores (andar entre telas)
- [ ] Minijogos (pular obstáculos, pegar itens)
- [ ] Sons e efeitos de áudio
- [ ] Sistema de XP e evolução do Bob
- [ ] Temas visuais (dark Bob, neon Bob, pixel Bob)
- [ ] Hot-reload de configurações sem reiniciar
- [ ] Notificações do sistema integradas

---

*Bob Desktop Mascot — Feito com ❤️ em Python + PyQt6*
