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