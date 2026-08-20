import pygame

class Sala:
    def __init__(self, largura, altura, ponto_entrada):
        self.largura = largura
        self.altura = altura
        self.ponto_entrada = ponto_entrada
        self.porta_aberta = False
        
        self.espessura_parede = 40
        self.paredes = [
            pygame.Rect(0, 0, largura, self.espessura_parede), # Parede Topo
            pygame.Rect(0, altura - self.espessura_parede, largura, self.espessura_parede), # Fundo
            pygame.Rect(0, 0, self.espessura_parede, altura), # Esquerda
            pygame.Rect(largura - self.espessura_parede, 0, self.espessura_parede, altura) # Direita
        ]
        
        self.rect_porta = pygame.Rect(largura - self.espessura_parede, altura // 2 - 40, self.espessura_parede, 80)

    def paredes_colisao(self):
        return self.paredes

    def desenhar(self, surf):
        surf.fill((20, 22, 28))
        
        for parede in self.paredes:
            pygame.draw.rect(surf, (45, 50, 60), parede)
            pygame.draw.rect(surf, (30, 35, 45), parede, width=2)
        
        cor_porta = (40, 150, 80) if self.porta_aberta else (150, 40, 40)
        pygame.draw.rect(surf, cor_porta, self.rect_porta)
        pygame.draw.rect(surf, (20, 20, 20), self.rect_porta, width=3)

    def jogador_na_porta(self, jogador):
        return jogador.get_rect().colliderect(self.rect_porta.inflate(10, 10))