# Plugins do Bob Desktop Mascot

Coloque arquivos .py aqui para adicionar funcionalidades extras ao Bob.

## Estrutura de um plugin

```python
# plugins/meu_plugin.py

PLUGIN_NAME = "Meu Plugin"
PLUGIN_VERSION = "1.0"
PLUGIN_AUTHOR = "Seu Nome"

def on_load(bob):
    """Chamado quando o plugin é carregado."""
    print(f"[Plugin] {PLUGIN_NAME} carregado!")

def on_tick(bob, dt):
    """Chamado a cada tick do game loop (~60fps)."""
    pass

def on_interaction(bob, event_type):
    """Chamado quando o usuário interage com o Bob."""
    # event_type: "click", "drag", "release"
    pass

def on_unload(bob):
    """Chamado quando o plugin é descarregado."""
    pass
```

## Plugins de exemplo

- `weather_plugin.py` - Mostra clima atual
- `music_plugin.py` - Reage à música tocando
- `jokes_plugin.py` - Piadas da internet
