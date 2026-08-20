import os
import pygame

PASTA_SPRITES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sprites", "operario")

_DIRECOES = ("frente", "costas", "direita", "esquerda")

_cache = None


def _carregar_imagem(nome_arquivo):
    caminho = os.path.join(PASTA_SPRITES, nome_arquivo)
    imagem = pygame.image.load(caminho).convert_alpha()
    return pygame.transform.scale(imagem, (110, 110))


def carregar_sprites_operario():
    global _cache
    if _cache is not None:
        return _cache

    sprites = {}
    for direcao in _DIRECOES:
        sprites[direcao] = {
            "parado": _carregar_imagem(f"idle_{direcao}.png"),
            "andando": [
                _carregar_imagem(f"andando_{direcao}_1.png"),
                _carregar_imagem(f"andando_{direcao}_2.png"),
            ],
        }

    _cache = sprites
    return sprites
