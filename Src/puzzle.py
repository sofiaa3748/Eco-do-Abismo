import pygame
import random

CINZA_PAINEL = (25, 30, 40)
CINZA_BORDA = (70, 80, 95)
CIANO_BRILHO = (0, 220, 255)
VERDE_OK = (60, 200, 100)
VERMELHO_ERRO = (200, 60, 60)
BRANCO = (255, 255, 255)
DOURADO = (200, 160, 50)


class PuzzleRadio:
    """
    Puzzle do dial de rádio, estilo "timing" (Semana 4):
    o ponteiro se move sozinho, indo e voltando dentro da barra.
    O jogador precisa apertar R no momento exato em que o ponteiro
    estiver passando pela faixa-alvo (a "frequência certa").

    - Apertar R com o ponteiro dentro da faixa: sucesso, rádio liga.
    - Apertar R com o ponteiro fora da faixa: erro, estática, novo
      alvo é sorteado e o ponteiro continua se movendo.
    """

    def __init__(self, largura_tela, altura_tela):
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela

        self.largura_barra = 400
        self.altura_barra = 20
        self.x_barra = largura_tela // 2 - self.largura_barra // 2
        self.y_barra = altura_tela // 2

        self.resolvido = False
        self.mostrando_erro = False
        self.tempo_erro = 0
        self.duracao_msg_erro = 1000  
        self._sortear_novo_alvo()
        self.posicao_indicador = 0.0
        self.velocidade_indicador = 3.5
        self._direcao = 1 

    def _sortear_novo_alvo(self):
        largura_alvo = random.randint(40, 60)
        inicio_max = self.largura_barra - largura_alvo
        self.alvo_inicio = random.randint(0, inicio_max)
        self.alvo_fim = self.alvo_inicio + largura_alvo

    def reiniciar(self):
        """Reinicia o puzzle do zero (ex: quando o jogador volta pra sala)."""
        self.resolvido = False
        self.mostrando_erro = False
        self._sortear_novo_alvo()
        self.posicao_indicador = 0.0
        self._direcao = 1

    def processar_evento(self, evento):
        if self.resolvido:
            return

        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_r:
            self._confirmar(pygame.time.get_ticks())

    def atualizar(self, teclas=None):
        """
        O ponteiro se move sozinho, indo e voltando dentro da barra.
        'teclas' não é mais usado para mover (mantido só por compatibilidade
        de chamada), o jogador não controla a direção, apenas o timing do R.
        """
        if self.resolvido:
            return

        self.posicao_indicador += self.velocidade_indicador * self._direcao

        if self.posicao_indicador >= self.largura_barra:
            self.posicao_indicador = self.largura_barra
            self._direcao = -1
        elif self.posicao_indicador <= 0:
            self.posicao_indicador = 0
            self._direcao = 1

        if self.mostrando_erro and pygame.time.get_ticks() - self.tempo_erro > self.duracao_msg_erro:
            self.mostrando_erro = False

    def esta_na_faixa(self):
        return self.alvo_inicio <= self.posicao_indicador <= self.alvo_fim

    def _confirmar(self, tempo_atual):
        if self.esta_na_faixa():
            self.resolvido = True
            self.mostrando_erro = False
        else:
            self.mostrando_erro = True
            self.tempo_erro = tempo_atual
            self._sortear_novo_alvo()

    def desenhar(self, surf, fonte):
        largura_painel = self.largura_barra + 80
        altura_painel = 160
        x_painel = self.largura_tela // 2 - largura_painel // 2
        y_painel = self.altura_tela // 2 - altura_painel // 2

        painel_surf = pygame.Surface((largura_painel, altura_painel), pygame.SRCALPHA)
        pygame.draw.rect(painel_surf, (*CINZA_PAINEL, 230), painel_surf.get_rect(), border_radius=8)
        pygame.draw.rect(painel_surf, CIANO_BRILHO, painel_surf.get_rect(), width=2, border_radius=8)
        surf.blit(painel_surf, (x_painel, y_painel))

        titulo = fonte.render("Aperte R quando o ponteiro estiver na faixa verde", True, BRANCO)
        surf.blit(titulo, titulo.get_rect(center=(self.largura_tela // 2, y_painel + 25)))

        pygame.draw.rect(surf, CINZA_BORDA, (self.x_barra, self.y_barra,
                                              self.largura_barra, self.altura_barra), border_radius=4)

        rect_alvo = pygame.Rect(self.x_barra + self.alvo_inicio, self.y_barra,
                                 self.alvo_fim - self.alvo_inicio, self.altura_barra)
        pygame.draw.rect(surf, VERDE_OK, rect_alvo, border_radius=4)

        cor_indicador = DOURADO if self.esta_na_faixa() else CIANO_BRILHO
        x_indicador = self.x_barra + self.posicao_indicador
        pygame.draw.line(surf, cor_indicador, (x_indicador, self.y_barra - 10),
                          (x_indicador, self.y_barra + self.altura_barra + 10), 4)

        if self.mostrando_erro:
            msg = fonte.render("ESTÁTICA — frequência errada, tente de novo", True, VERMELHO_ERRO)
            surf.blit(msg, msg.get_rect(center=(self.largura_tela // 2, y_painel + altura_painel - 30)))
        elif self.resolvido:
            msg = fonte.render("SINAL CAPTURADO — rádio ligado", True, VERDE_OK)
            surf.blit(msg, msg.get_rect(center=(self.largura_tela // 2, y_painel + altura_painel - 30)))