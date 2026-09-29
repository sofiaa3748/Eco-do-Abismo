import pygame
import random

class FrascoSanidade:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 22)
        self.coletado = False
        self.offset_y = 0
        self.tempo = random.random() * 10

    def desenhar(self, surf):
        if not self.coletado:
            self.tempo += 0.1
            import math
            flutuacao = math.sin(self.tempo) * 3

            rect_animado = pygame.Rect(self.rect.x, self.rect.y + flutuacao, self.rect.width, self.rect.height)

            pygame.draw.rect(surf, (50, 200, 255), rect_animado, border_radius=4) # Líquido
            pygame.draw.rect(surf, (200, 255, 255), rect_animado, width=2, border_radius=4) # Vidro
            pygame.draw.rect(surf, (150, 100, 50), (rect_animado.x + 4, rect_animado.y - 4, 8, 4)) # Rolha

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
        if self.coletada:
            return
        pygame.draw.rect(surf, (230, 200, 60), self.rect, border_radius=4)
        pygame.draw.rect(surf, (120, 100, 20), self.rect, width=2, border_radius=4)


class Documento:
    def __init__(self, x, y, texto, especial=False):
        self.rect = pygame.Rect(x, y, 22, 16)
        self.texto = texto
        self.especial = especial
        self.coletado = False

    def desenhar(self, surf):
        if self.coletado:
            return
        cor = (220, 190, 90) if self.especial else (200, 200, 200)
        pygame.draw.rect(surf, cor, self.rect)
        pygame.draw.rect(surf, (80, 80, 80), self.rect, width=1)

class Chave:
    def __init__(self, x, y, rotulo="CHAVE"):
        self.rect = pygame.Rect(x, y, 16, 10)
        self.rotulo = rotulo
        self.coletada = False

    def desenhar(self, surf):
        if self.coletada:
            return
        pygame.draw.rect(surf, (255, 210, 60), self.rect, border_radius=2)
        pygame.draw.circle(surf, (255, 210, 60), (self.rect.left, self.rect.centery), 5)


class MascaraGas:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 26, 22)
        self.coletada = False
        self.destrancado = False

    def desenhar(self, surf):
        if self.coletada:
            return
        cor = (120, 150, 130) if self.destrancado else (70, 60, 55)
        pygame.draw.rect(surf, cor, self.rect, border_radius=6)
        pygame.draw.rect(surf, (30, 30, 30), self.rect, width=2, border_radius=6)


class Lanterna:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 18, 14)
        self.coletada = False

    def desenhar(self, surf):
        if self.coletada:
            return
        pygame.draw.rect(surf, (200, 200, 60), self.rect, border_radius=3)
        pygame.draw.rect(surf, (60, 60, 20), self.rect, width=2, border_radius=3)