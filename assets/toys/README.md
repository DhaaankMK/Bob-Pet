# assets/toys/
# Pasta para sprites de brinquedos personalizados (opcional)
#
# Brinquedos disponíveis: ball, cube, star, food, doll
# 
# Para adicionar um novo brinquedo:
# 1. Adicione o PNG aqui: ex. rocket.png (tamanho recomendado: 40x40px)
# 2. Edite bob/toys.py e adicione ao dicionário TOYS_CATALOG:
#
#   "rocket": {
#       "name": "Foguete",
#       "emoji": "🚀",
#       "description": "Um foguete veloz!",
#       "color": "#E05050",   ← Cor para desenho procedural (fallback)
#       "size": 40,
#       "bounce": 0.5,
#       "gravity": 0.4,
#   }
#
# 3. O sistema usará o PNG se disponível, senão usa o desenho procedural.
