"""
bob/paths.py — Gerenciamento centralizado de caminhos do projeto.

REGRA: Nenhum módulo deve usar strings literais de caminho.
Todos devem importar daqui:
    from bob.paths import PATHS, ensure_dirs, load_json_safe, save_json_safe
"""

import sys
import os
import json
import time
from pathlib import Path

# ── Raiz do projeto ───────────────────────────────────────────────────────────
# Este arquivo está em bob/paths.py → raiz = bob/../
_THIS_FILE = Path(__file__).resolve()
ROOT = _THIS_FILE.parent.parent  # .../Bob/

# Garante que a raiz está no sys.path
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── Estrutura de diretórios ───────────────────────────────────────────────────
PATHS = {
    # Raiz
    "root":          ROOT,
    # Código
    "bob":           ROOT / "bob",
    "manager":       ROOT / "manager",
    "plugins":       ROOT / "plugins",
    # Dados
    "data":          ROOT / "data",
    "config":        ROOT / "config",
    # Assets
    "assets":        ROOT / "assets",
    "assets_bob":    ROOT / "assets" / "bob",
    "assets_clothes":ROOT / "assets" / "clothes",
    "assets_toys":   ROOT / "assets" / "toys",
    "assets_sprites":ROOT / "assets" / "sprites",
    # Arquivos de dados
    "settings":      ROOT / "config" / "settings.json",
    "state":         ROOT / "data"   / "state.json",
    "commands":      ROOT / "data"   / "commands.json",
    "memory":        ROOT / "data"   / "memory.json",
    "personality":   ROOT / "data"   / "personality.json",
}

# ── Defaults para arquivos JSON ───────────────────────────────────────────────
_DEFAULTS = {
    "settings": {
        "gravity": 0.55, "volume": 0.7, "scale": 1.0,
        "bob_size": 100, "speed": 4.0,
        "spawn_auto_toys": False, "auto_behavior": True,
        "sleep_timeout_minutes": 10, "bored_timeout_minutes": 5,
        "physics_enabled": True, "always_on_top": True,
        "show_speech_bubbles": True, "bubble_duration_ms": 3500,
        "chase_cursor": False,
        "react_to_mouse_proximity": True, "mouse_proximity_radius": 150,
        "start_position": {"x": -1, "y": -1},
        "current_clothes": [], "active_toys": [],
        "current_mood": "happy", "current_animation": "idle",
        "language": "pt-BR", "show_on_taskbar": False,
        "bounce_on_edges": True, "terminal_velocity": 18.0,
        "jump_force": -14.0, "friction": 0.82,
        "language_mode": "children", "personality": "playful",
        "personality_energy": 70, "personality_curiosity": 60,
        "personality_laziness": 30, "personality_chaos": 20,
        "interact_with_windows": False, "system_alerts": True,
        "cpu_alert_threshold": 85, "battery_alert_threshold": 20,
        "user_name": "", "plugins_enabled": True,
        "walk_speed_multiplier": 1.0, "auto_jump_chance": 0.04,
        "random_walk_interval_min": 1.0,
        "random_walk_interval_max": 4.0,
        "joke_api_enabled": False, "show_system_alerts": True,
    },
    "state": {
        "running": False, "x": 100, "y": 100,
        "vx": 0.0, "vy": 0.0, "mood": "happy",
        "animation": "idle", "clothes": [], "toys_on_screen": 0,
        "is_dragging": False, "chaotic_mode": False,
        "party_mode": False, "facing": "right",
        "phrase": "", "idle_time": 0,
        "personality": "playful", "language_mode": "children",
        "user_name": "", "system": {},
    },
    "commands": [],
    "memory": {
        "user_name": "", "favorite_toy": "", "favorite_clothes": [],
        "times_interacted": 0, "times_clicked": 0, "times_dragged": 0,
        "toys_played": 0, "total_sessions": 0, "last_session": 0,
        "first_run": True, "last_mood": "happy", "conversations": [],
        "achievements": [], "total_distance_walked": 0.0,
        "times_jumped": 0, "custom_notes": "",
    },
    "personality": {
        "name": "playful",
        "energy": 70, "curiosity": 60,
        "laziness": 30, "chaos": 20,
        "saved_at": 0,
    },
}


def ensure_dirs():
    """
    Cria todas as pastas necessárias do projeto.
    Deve ser chamada na inicialização de bob.py e manager.py.
    """
    dirs = [
        PATHS["data"], PATHS["config"], PATHS["plugins"],
        PATHS["assets"], PATHS["assets_bob"],
        PATHS["assets_clothes"], PATHS["assets_toys"],
        PATHS["assets_sprites"],
    ]
    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[Paths] Aviso: não foi possível criar {d}: {e}")

    # Cria __init__.py nos pacotes que podem não ter
    for pkg_dir in [PATHS["bob"], PATHS["manager"], PATHS["plugins"]]:
        init = pkg_dir / "__init__.py"
        if not init.exists():
            try:
                init.write_text(f"# {pkg_dir.name} package\n", encoding="utf-8")
            except Exception:
                pass


def load_json_safe(path_key: str) -> dict:
    """
    Carrega um arquivo JSON de forma segura.
    - Cria o arquivo com valores padrão se não existir.
    - Garante que todas as chaves padrão existam.
    - Trata JSON inválido/vazio sem crash.
    
    Args:
        path_key: chave em PATHS (ex: "settings", "memory")
    Returns:
        dict com os dados carregados
    """
    path   = PATHS.get(path_key)
    if path is None:
        print(f"[Paths] Chave desconhecida: {path_key}")
        return {}

    default = _DEFAULTS.get(path_key, {} if path_key != "commands" else [])

    # Garante que a pasta existe
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # Se o arquivo não existe, cria com defaults
    if not path.exists():
        save_json_safe(path_key, default)
        return _deep_copy(default)

    # Lê o arquivo
    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            save_json_safe(path_key, default)
            return _deep_copy(default)
        data = json.loads(content)
    except (json.JSONDecodeError, OSError, PermissionError) as e:
        print(f"[Paths] Erro ao ler {path.name}: {e}. Usando padrões.")
        save_json_safe(path_key, default)
        return _deep_copy(default)

    # Para dicionários: garante que todas as chaves padrão existem
    if isinstance(data, dict) and isinstance(default, dict):
        _fill_defaults(data, default)

    return data


def save_json_safe(path_key: str, data) -> bool:
    """
    Salva dados em JSON de forma segura.
    Returns: True se salvou com sucesso.
    """
    path = PATHS.get(path_key)
    if path is None:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Escreve em arquivo temporário e depois rename (atômico)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        tmp.replace(path)
        return True
    except Exception as e:
        print(f"[Paths] Erro ao salvar {path_key}: {e}")
        return False


def asset_path(subfolder: str, filename: str) -> Path:
    """
    Retorna o caminho absoluto de um asset.
    Usa os.path.join internamente para garantir portabilidade.
    Exemplo: asset_path("clothes", "hat.png")
    """
    base = PATHS.get(f"assets_{subfolder}", PATHS["assets"])
    return Path(os.path.join(str(base), filename))


def asset_exists(subfolder: str, filename: str) -> bool:
    """Verifica se um asset existe."""
    return asset_path(subfolder, filename).exists()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _deep_copy(obj):
    """Cópia profunda simples via JSON."""
    try:
        return json.loads(json.dumps(obj))
    except Exception:
        return obj


def _fill_defaults(data: dict, defaults: dict):
    """Preenche recursivamente chaves ausentes com os valores padrão."""
    for k, v in defaults.items():
        if k not in data:
            data[k] = _deep_copy(v)
        elif isinstance(v, dict) and isinstance(data.get(k), dict):
            _fill_defaults(data[k], v)


# Executa ao importar — garante que as pastas existem
ensure_dirs()
