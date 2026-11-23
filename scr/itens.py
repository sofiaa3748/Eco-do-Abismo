import math
import pygame
import random

import sprites

class FrascoSanidade:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 22)
        self.coletado = False
        self.offset_y = 0
        self.tempo = random.random() * 10

    def desenhar(self, surf):
        if not self.coletado:
            self.tempo += 0.1
            flutuacao = int(math.sin(self.tempo) * 3)
            sprites.desenhar_pilula(surf, self.rect, flutuacao)

def gerar_frascos_na_sala(nivel):
    frascos = []
    qtd = 2 if nivel == 1 else (3 if nivel == 2 else 4)

    for _ in range(qtd):
        fx = random.randint(150, 650)
        fy = random.randint(150, 450)
        frascos.append(FrascoSanidade(fx, fy))

    return frascos

class Dica:
    def __init__(self, x, y, valor, indice):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.valor = valor
        self.indice = indice
        self.coletada = False

    def desenhar(self, surf):
        # As pistas permanecem visíveis no mundo até o jogador abrir o puzzle.
        sprites.blit_centro(surf, "dica", self.rect.center)
        if not self.coletada:
            pygame.draw.circle(surf, (235, 195, 85), self.rect.center, 15, 1)


class Documento:
    def __init__(self, x, y, texto, especial=False):
        self.rect = pygame.Rect(x, y, 22, 16)
        self.texto = texto
        self.especial = especial
        self.coletado = False

    def desenhar(self, surf):
        if self.coletado:
            return
        sprites.blit_centro(surf, "documento_especial" if self.especial else "documento", self.rect.center)

class Chave:
    def __init__(self, x, y, rotulo="CHAVE"):
        self.rect = pygame.Rect(x, y, 16, 10)
        self.rotulo = rotulo
        self.coletada = False

    def desenhar(self, surf):
        if self.coletada:
            return
        sprites.blit_centro(surf, "chave", self.rect.center)


class MascaraGas:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 26, 22)
        self.coletada = False
        self.destrancado = False

    def desenhar(self, surf):
        if self.coletada:
            return
        sprites.blit_centro(surf, "mascara", self.rect.center)


class Lanterna:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 18, 14)
        self.coletada = False

    def desenhar(self, surf):
        if self.coletada:
            return
        sprites.blit_centro(surf, "lanterna", self.rect.center)
