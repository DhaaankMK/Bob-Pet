# assets/clothes/
# Pasta para sprites de roupas personalizadas (opcional)
#
# Roupas disponíveis: hat, glasses, shirt, cape, crown
#
# Para adicionar uma nova roupa:
# 1. Adicione o PNG aqui: ex. scarf.png (fundo transparente, 100x130px)
# 2. Edite bob/clothes.py e adicione ao dicionário CLOTHES_CATALOG:
#
#   "scarf": {
#       "name": "Cachecol",
#       "description": "Um cachecol estiloso.",
#       "emoji": "🧣",
#       "slot": "neck",       ← Slot único (head, face, body, back, neck...)
#   }
#
# 3. Edite animation.py → método _draw_clothes() e adicione o elif:
#
#   elif item == "scarf":
#       self._draw_scarf(p, cx, cy, unit)
#
# 4. Implemente o método _draw_scarf() na classe AnimationSystem.
