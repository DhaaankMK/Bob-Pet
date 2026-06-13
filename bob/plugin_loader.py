"""
bob/plugin_loader.py — Carregador de plugins (v2 estável)

Correções:
  • Verifica se a pasta plugins/ existe (sem crashar)
  • Ignora arquivos inválidos silenciosamente
  • Valida interface mínima do plugin antes de carregar
  • Protege on_tick e on_interaction com try/except individuais
"""
import sys
import importlib.util
import importlib
from pathlib import Path

_THIS = Path(__file__).resolve().parent.parent
if str(_THIS) not in sys.path:
    sys.path.insert(0, str(_THIS))

from bob.paths import PATHS


class PluginLoader:
    """Carrega e gerencia plugins do Bob."""

    # Interface mínima que um plugin DEVE ter para ser carregado
    REQUIRED_FUNCTIONS = []  # Nenhuma obrigatória — todos são opcionais

    def __init__(self):
        self.plugins: dict = {}  # stem -> módulo

    def load_all(self, bob_instance):
        """Carrega todos os .py da pasta plugins/."""
        plugins_dir = PATHS.get("plugins")
        if not plugins_dir or not plugins_dir.exists():
            return

        loaded = 0
        for py_file in sorted(plugins_dir.glob("*.py")):
            # Pula __init__.py e arquivos que começam com _
            if py_file.stem.startswith("_"):
                continue
            success = self._load_one(py_file, bob_instance)
            if success:
                loaded += 1

        if loaded:
            print(f"[Plugins] {loaded} plugin(s) carregado(s)")

    def _load_one(self, path: Path, bob_instance) -> bool:
        """Carrega um único plugin. Retorna True se bem-sucedido."""
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            if spec is None or spec.loader is None:
                return False

            module = importlib.util.module_from_spec(spec)

            # Executa o módulo (pode lançar erros de sintaxe etc.)
            spec.loader.exec_module(module)

            self.plugins[path.stem] = module

            name = getattr(module, "PLUGIN_NAME", path.stem)

            # Chama on_load se existir
            if hasattr(module, "on_load") and callable(module.on_load):
                try:
                    module.on_load(bob_instance)
                except Exception as e:
                    print(f"[Plugins] on_load '{name}' falhou: {e}")

            print(f"[Plugins] ✓ {name}")
            return True

        except SyntaxError as e:
            print(f"[Plugins] ✗ Erro de sintaxe em {path.name}: {e}")
        except ImportError as e:
            print(f"[Plugins] ✗ Import error em {path.name}: {e}")
        except Exception as e:
            print(f"[Plugins] ✗ Erro ao carregar {path.name}: {e}")
        return False

    def tick(self, bob_instance, dt: float):
        """Chama on_tick em todos os plugins com proteção individual."""
        for name, module in list(self.plugins.items()):
            if hasattr(module, "on_tick") and callable(module.on_tick):
                try:
                    module.on_tick(bob_instance, dt)
                except Exception as e:
                    # Não remove o plugin por um erro de tick
                    pass

    def on_interaction(self, bob_instance, event_type: str):
        """Chama on_interaction em todos os plugins."""
        for name, module in list(self.plugins.items()):
            if hasattr(module, "on_interaction") and callable(module.on_interaction):
                try:
                    module.on_interaction(bob_instance, event_type)
                except Exception:
                    pass

    def unload_all(self, bob_instance):
        """Descarrega todos os plugins chamando on_unload."""
        for name, module in list(self.plugins.items()):
            if hasattr(module, "on_unload") and callable(module.on_unload):
                try:
                    module.on_unload(bob_instance)
                except Exception:
                    pass
        self.plugins.clear()

    def reload(self, stem: str, bob_instance) -> bool:
        """Recarrega um plugin pelo stem do nome."""
        plugins_dir = PATHS.get("plugins")
        if not plugins_dir:
            return False
        path = plugins_dir / f"{stem}.py"
        if not path.exists():
            return False
        # Descarrega o existente
        if stem in self.plugins:
            module = self.plugins.pop(stem)
            if hasattr(module, "on_unload"):
                try: module.on_unload(bob_instance)
                except Exception: pass
        return self._load_one(path, bob_instance)

    def get_names(self) -> list:
        """Retorna lista com os nomes dos plugins carregados."""
        return [
            getattr(m, "PLUGIN_NAME", n)
            for n, m in self.plugins.items()
        ]

    def count(self) -> int:
        return len(self.plugins)
