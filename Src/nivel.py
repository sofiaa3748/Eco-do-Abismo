import pygame

CINZA_PAREDE = (45, 50, 60)
CINZA_PAREDE_BORDA = (70, 80, 95)
VERMELHO_PORTA = (140, 30, 30)
VERDE_PORTA = (40, 160, 90)


class Sala:
    """
    Representa uma sala do jogo: paredes (colisão), uma porta de saída
    (trancada até o puzzle ser resolvido) e ponto de entrada do jogador.
    """

    def __init__(self, largura_tela, altura_tela, ponto_entrada=(100, 300),
                 porta_rect=None, espessura_parede=24):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.ponto_entrada = ponto_entrada
        self.espessura_parede = espessura_parede

        if porta_rect is None:
            porta_rect = pygame.Rect(largura_tela - espessura_parede, altura_tela // 2 - 50,
                                      espessura_parede, 100)
        self.porta_rect = porta_rect
        self.porta_aberta = False

        self.paredes = self._gerar_paredes_perimetro()

    def _gerar_paredes_perimetro(self):
        """Cria as 4 paredes ao redor da tela, com um vão onde a porta fica."""
        e = self.espessura_parede
        paredes = []
        paredes.append(pygame.Rect(0, 0, self.largura_tela, e))
        paredes.append(pygame.Rect(0, self.altura_tela - e, self.largura_tela, e))
        paredes.append(pygame.Rect(0, 0, e, self.altura_tela))

        topo_vao = self.porta_rect.top
        base_vao = self.porta_rect.bottom
        paredes.append(pygame.Rect(self.largura_tela - e, 0, e, topo_vao))
        paredes.append(pygame.Rect(self.largura_tela - e, base_vao, e,
                                    self.altura_tela - base_vao))

        return paredes

    def paredes_colisao(self):
        """Retorna as paredes que de fato bloqueiam o jogador.
        Se a porta estiver aberta, ela não conta como obstáculo."""
        if self.porta_aberta:
            return self.paredes
        return self.paredes + [self.porta_rect]

    def jogador_na_porta(self, jogador):
        return jogador.get_rect().colliderect(self.porta_rect.inflate(10, 10))

    def desenhar(self, surf):
        for parede in self.paredes:
            pygame.draw.rect(surf, CINZA_PAREDE, parede)
            pygame.draw.rect(surf, CINZA_PAREDE_BORDA, parede, width=2)

        cor_porta = VERDE_PORTA if self.porta_aberta else VERMELHO_PORTA
        pygame.draw.rect(surf, cor_porta, self.porta_rect)
        pygame.draw.rect(surf, CINZA_PAREDE_BORDA, self.porta_rect, width=2)