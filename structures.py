import random

class StructureBuilder:
    def __init__(self, model):
        self.model = model

    def build(self, position, structure_data, materials):
        start_x, start_y, start_z = position
        
        for y, layer in enumerate(structure_data):
            # Itera sobre as linhas (profundidade Z)
            for z, row in enumerate(layer):
                # Itera sobre as colunas (largura X)
                for x, block_type in enumerate(row):
                    # Se o bloco for -1 (ou None), é ar, então pulamos
                    if block_type == -1:
                        continue
                    
                    # Pega a textura correspondente ao ID (0, 1, 2, etc)
                    if block_type in materials:
                        texture = materials[block_type]
                        # Calcula a posição real no mundo
                        world_pos = (start_x + x, start_y + y, start_z + z)
                        # Adiciona o bloco (immediate=False para ser rápido na geração inicial)
                        self.model.add_block(world_pos, texture, immediate=False)

# --- DEFINIÇÃO DAS ESTRUTURAS (BLUEPRINTS) ---
# 0: Chão (Ex: Pedra/Areia)
# 1: Parede (Ex: Tijolo)
# 2: Teto/Detalhe (Ex: Grama/Pedra)
# -1: Vazio

# Casa Simples (5x5 de largura/profundidade, 4 de altura)
SIMPLE_HOUSE = [
    # Camada 0 (Chão)
    [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ],
    # Camada 1 (Paredes + Porta)
    [
        [1, 1, 1, 1, 1],
        [1, -1, -1, -1, 1],
        [1, -1, -1, -1, 1],
        [1, -1, -1, -1, 1],
        [1, 1, -1, 1, 1], # Porta no meio
    ],
    # Camada 2 (Paredes + Janela)
    [
        [1, 1, 1, 1, 1],
        [1, -1, -1, -1, 1],
        [1, -1, -1, -1, -1], # Janela
        [1, -1, -1, -1, 1],
        [1, 1, -1, 1, 1], # Topo da porta
    ],
    # Camada 3 (Teto)
    [
        [2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2],
        [2, 2, 2, 2, 2],
    ]
]

# Farol (Pequeno)
LIGHTHOUSE = [
    # Base (Chão)
    [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
    # Corpo (Paredes) - Repetido várias vezes na lógica ou definido manualmente
    [[1, 1, 1], [1, -1, 1], [1, 1, 1]], 
    [[1, 1, 1], [1, -1, 1], [1, 1, 1]], 
    [[1, 1, 1], [1, -1, 1], [1, 1, 1]], 
    [[1, 1, 1], [1, -1, 1], [1, 1, 1]], 
    [[1, 1, 1], [1, -1, 1], [1, 1, 1]], 
    # Topo (Luz) - Usamos 2 (Areia) para simular luz amarela
    [[-1, -1, -1], [-1, 2, -1], [-1, -1, -1]],
]

# Labirinto (Pequeno 7x7)
MAZE = [
    # Chão
    [
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0],
    ],
    # Paredes (Labirinto)
    [
        [1, 1, 1, 1, 1, 1, 1],
        [1, -1, -1, -1, 1, -1, -1], # Entrada e caminho
        [1, 1, 1, -1, 1, -1, 1],
        [1, -1, -1, -1, -1, -1, 1],
        [1, -1, 1, 1, 1, 1, 1],
        [1, -1, -1, -1, -1, -1, 1],
        [1, 1, 1, 1, 1, 1, 1],
    ],
    # Paredes Altas (camada 2 do labirinto)
    [
        [1, 1, 1, 1, 1, 1, 1],
        [1, -1, -1, -1, 1, -1, -1], 
        [1, 1, 1, -1, 1, -1, 1],
        [1, -1, -1, -1, -1, -1, 1],
        [1, -1, 1, 1, 1, 1, 1],
        [1, -1, -1, -1, -1, -1, 1],
        [1, 1, 1, 1, 1, 1, 1],
    ]
]