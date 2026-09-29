import pygame

class Sala:
    def __init__(self, largura_mundo, altura_mundo, ponto_entrada,
                 largura_tela=800, altura_tela=600,
                 lado_porta='direita', pos_porta=None, obstaculos=None,
                 cor_fundo=(20, 22, 28)):
        self.largura = largura_mundo
        self.altura = altura_mundo
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.ponto_entrada = ponto_entrada
        self.porta_aberta = False
        self.cor_fundo = cor_fundo

        self.espessura_parede = 40
        self.paredes = [
            pygame.Rect(0, 0, largura_mundo, self.espessura_parede),
            pygame.Rect(0, altura_mundo - self.espessura_parede, largura_mundo, self.espessura_parede),
            pygame.Rect(0, 0, self.espessura_parede, altura_mundo),
            pygame.Rect(largura_mundo - self.espessura_parede, 0, self.espessura_parede, altura_mundo),
        ]

        self.obstaculos = list(obstaculos) if obstaculos else []
        self.paredes.extend(self.obstaculos)

        if pos_porta is not None:
            self.rect_porta = pos_porta
        else:
            if lado_porta == 'direita':
                self.rect_porta = pygame.Rect(largura_mundo - self.espessura_parede, altura_mundo // 2 - 40, self.espessura_parede, 80)
            elif lado_porta == 'esquerda':
                self.rect_porta = pygame.Rect(0, altura_mundo // 2 - 40, self.espessura_parede, 80)
            elif lado_porta == 'topo':
                self.rect_porta = pygame.Rect(largura_mundo // 2 - 40, 0, 80, self.espessura_parede)
            else:
                self.rect_porta = pygame.Rect(largura_mundo // 2 - 40, altura_mundo - self.espessura_parede, 80, self.espessura_parede)

    def paredes_colisao(self):
        return self.paredes

    def calcular_camera(self, jogador):
        rect_j = jogador.get_rect()
        cam_x = rect_j.centerx - self.largura_tela // 2
        cam_y = rect_j.centery - self.altura_tela // 2

        cam_x = max(0, min(cam_x, max(0, self.largura - self.largura_tela)))
        cam_y = max(0, min(cam_y, max(0, self.altura - self.altura_tela)))
        return cam_x, cam_y

    def desenhar(self, surf):
        surf.fill(self.cor_fundo)

        for parede in self.paredes:
            pygame.draw.rect(surf, (45, 50, 60), parede)
            pygame.draw.rect(surf, (30, 35, 45), parede, width=2)

        cor_porta = (40, 150, 80) if self.porta_aberta else (150, 40, 40)
        pygame.draw.rect(surf, cor_porta, self.rect_porta)
        pygame.draw.rect(surf, (20, 20, 20), self.rect_porta, width=3)

    def jogador_na_porta(self, jogador):
        return jogador.get_rect().colliderect(self.rect_porta.inflate(10, 10))