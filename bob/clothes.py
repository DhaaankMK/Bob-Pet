"""
clothes.py - Sistema de roupas do Bob (v2)
Catálogo expandido. Renderização em animation.py.
"""

import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from typing import List


CLOTHES_CATALOG = {
    "hat": {
        "name": "Chapéu Preto",
        "description": "Um elegante chapéu-coco.",
        "emoji": "🎩",
        "slot": "head",
        "category": "classic",
    },
    "glasses": {
        "name": "Óculos",
        "description": "Óculos inteligentes com armação marrom.",
        "emoji": "👓",
        "slot": "face",
        "category": "classic",
    },
    "sunglasses": {
        "name": "Óculos de Sol",
        "description": "Óculos escuros estilosos.",
        "emoji": "🕶️",
        "slot": "face",
        "category": "cool",
    },
    "shirt": {
        "name": "Camisa Vermelha",
        "description": "Uma camisa casual com botões.",
        "emoji": "👕",
        "slot": "body",
        "category": "classic",
    },
    "cape": {
        "name": "Capa de Super-Herói",
        "description": "Para o Bob heróico!",
        "emoji": "🦸",
        "slot": "back",
        "category": "hero",
    },
    "crown": {
        "name": "Coroa",
        "description": "Bob é o rei! Coroa dourada com gemas.",
        "emoji": "👑",
        "slot": "head",
        "category": "royal",
    },
    "scarf": {
        "name": "Cachecol",
        "description": "Um cachecol azul estiloso.",
        "emoji": "🧣",
        "slot": "neck",
        "category": "classic",
    },
    "bow": {
        "name": "Laço Rosa",
        "description": "Um laço fofo e adorável!",
        "emoji": "🎀",
        "slot": "head",
        "category": "cute",
    },
    "tie": {
        "name": "Gravata",
        "description": "Bob vai a uma reunião!",
        "emoji": "👔",
        "slot": "neck",
        "category": "formal",
    },
}

SLOTS = ["head", "face", "body", "back", "neck"]

# Outfits completos pré-definidos
OUTFITS = {
    "heroi":    ["cape", "shirt"],
    "rei":      ["crown", "cape"],
    "elegante": ["hat", "glasses", "tie"],
    "casual":   ["shirt", "scarf"],
    "festeiro": ["bow", "shirt"],
    "cool":     ["sunglasses", "shirt"],
    "nu":       [],  # Remove tudo
}


class ClothesSystem:
    """Gerencia inventário e itens equipados no Bob."""

    def __init__(self, initial: List[str] = None):
        self.equipped: List[str] = list(initial or [])

    def equip(self, item_id: str) -> bool:
        if item_id not in CLOTHES_CATALOG:
            return False
        slot = CLOTHES_CATALOG[item_id]["slot"]
        # Remove itens do mesmo slot
        self.equipped = [
            e for e in self.equipped
            if CLOTHES_CATALOG.get(e, {}).get("slot") != slot
        ]
        if item_id not in self.equipped:
            self.equipped.append(item_id)
        return True

    def unequip(self, item_id: str) -> bool:
        if item_id in self.equipped:
            self.equipped.remove(item_id)
            return True
        return False

    def toggle(self, item_id: str) -> bool:
        return self.unequip(item_id) if item_id in self.equipped else self.equip(item_id)

    def clear(self):
        self.equipped.clear()

    def apply_outfit(self, outfit_name: str) -> bool:
        if outfit_name not in OUTFITS:
            return False
        self.equipped.clear()
        for item_id in OUTFITS[outfit_name]:
            self.equip(item_id)
        return True

    def is_equipped(self, item_id: str) -> bool:
        return item_id in self.equipped

    def get_equipped(self) -> List[str]:
        return list(self.equipped)

    def get_equipped_info(self) -> List[dict]:
        return [
            {"id": iid, **CLOTHES_CATALOG[iid]}
            for iid in self.equipped if iid in CLOTHES_CATALOG
        ]

    @staticmethod
    def get_catalog() -> dict:
        return CLOTHES_CATALOG

    @staticmethod
    def get_outfits() -> dict:
        return OUTFITS
