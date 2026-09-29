import pygame
import sys
import random
import math

class Particula:
    def __init__(self, largura, altura):
        self.x = random.randint(0, largura)
        self.y = random.randint(0, altura)
        self.vy = random.uniform(-0.3, -1.5)
        self.tamanho = random.randint(1, 4)
        self.brilho = random.randint(100, 255)

    def atualizar(self, altura):
        self.y += self.vy
        if self.y < 0:
            self.y = altura

    def desenhar(self, tela):
        brilho_extra = min(255, int(self.brilho) + 20)
        cor = (int(self.brilho), int(self.brilho), brilho_extra)
        pygame.draw.circle(tela, cor, (int(self.x), int(self.y)), self.tamanho)

class Botao:
    def __init__(self, x, y, texto, fonte):
        self.texto = texto
        self.fonte = fonte
        self.imagem = self.fonte.render(self.texto, True, (255, 255, 255))
        self.rect = self.imagem.get_rect(center=(x, y))
        self.hover = False

    def atualizar(self, mouse_pos):
        self.hover = self.rect.inflate(60, 30).collidepoint(mouse_pos)

    def desenhar(self, tela):
        cor_fundo = (60, 120, 200) if self.hover else (40, 60, 100)
        caixa = self.rect.inflate(60, 30)
        pygame.draw.rect(tela, cor_fundo, caixa, border_radius=8)
        pygame.draw.rect(tela, (200, 220, 255), caixa, width=2, border_radius=8)
        tela.blit(self.imagem, self.rect)

    def clicado(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.rect.inflate(60, 30).collidepoint(evento.pos):
                return True
        return False

def criar_botoes(centro_x, fonte):
    return [
        Botao(centro_x, 380, "JOGAR", fonte),
        Botao(centro_x, 460, "SAIR", fonte),
    ]

def desenhar_fundo(tela, tempo, largura, altura):
    tela.fill((10, 10, 30))

def desenhar_titulo(tela, tempo, largura, fonte_titulo, fonte_sub):
    oscilacao = math.sin(tempo / 400) * 8

    txt = fonte_titulo.render("ECO DO ABISMO", True, (220, 230, 255))
    sombra = fonte_titulo.render("ECO DO ABISMO", True, (50, 50, 80))

    tela.blit(sombra, sombra.get_rect(center=(largura // 2 + 4, 150 + int(oscilacao) + 4)))
    tela.blit(txt, txt.get_rect(center=(largura // 2, 150 + int(oscilacao))))

    sub = fonte_sub.render("Tome as pílulas e mantenha sua sanidade...", True, (130, 140, 160))
    tela.blit(sub, sub.get_rect(center=(largura // 2, 230 + int(oscilacao))))

def desenhar_intro_acordar(tela, tempo_decorrido, largura, altura, fonte_sub, sprites_jogador=None,
                            duracao_total=3400):

    tela.fill((8, 8, 13))
    pygame.draw.rect(tela, (24, 22, 30), (0, 0, largura, altura))

    rect_cama = pygame.Rect(largura // 2 - 90, altura // 2 - 30, 180, 110)
    pygame.draw.rect(tela, (55, 42, 38), rect_cama, border_radius=10)
    pygame.draw.rect(tela, (85, 68, 58), rect_cama.inflate(-24, -24), border_radius=8)
    pygame.draw.rect(tela, (35, 30, 45), (rect_cama.x - 10, rect_cama.y - 6, 20, rect_cama.height + 12), border_radius=6)

    fase_texto_1 = duracao_total * 0.35
    fase_abertura_fim = duracao_total

    if sprites_jogador and tempo_decorrido >= fase_abertura_fim:
        try:
            sprite = sprites_jogador['frente']['parado']
            tela.blit(sprite, sprite.get_rect(midbottom=(rect_cama.centerx, rect_cama.top + 12)))
        except Exception:
            pass

    if tempo_decorrido < fase_texto_1:
        alpha = min(255, int(255 * (tempo_decorrido / max(1, fase_texto_1))))
        txt = fonte_sub.render('UMA VOZ: "Acorde..."', True, (205, 215, 235))
        txt.set_alpha(alpha)
        tela.blit(txt, txt.get_rect(center=(largura // 2, altura - 90)))
        raio_atual = 0
    elif tempo_decorrido < fase_abertura_fim:
        progresso = (tempo_decorrido - fase_texto_1) / max(1, (fase_abertura_fim - fase_texto_1))
        raio_atual = progresso * largura * 0.75
        txt = fonte_sub.render('UMA VOZ: "Levante-se. Você precisa fugir daqui, agora."', True, (205, 215, 235))
        tela.blit(txt, txt.get_rect(center=(largura // 2, altura - 90)))
    else:
        raio_atual = largura
        txt = fonte_sub.render("Pressione [ESPAÇO] para levantar", True, (170, 180, 205))
        tela.blit(txt, txt.get_rect(center=(largura // 2, altura - 55)))

    if tempo_decorrido < fase_abertura_fim:
        véu = pygame.Surface((largura, altura), pygame.SRCALPHA)
        véu.fill((0, 0, 0, 255))
        if raio_atual > 0:
            largura_olho = raio_atual * 2
            altura_olho = raio_atual
            pygame.draw.ellipse(véu, (0, 0, 0, 0),
                                 (largura // 2 - largura_olho / 2, altura // 2 - altura_olho / 2,
                                  largura_olho, altura_olho))
        tela.blit(véu, (0, 0))