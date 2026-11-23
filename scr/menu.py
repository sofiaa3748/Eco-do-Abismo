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
    from sprites import carregar_tela
    fundo = carregar_tela("tela_inicial")
    if fundo is not None:
        tela.blit(fundo, (0, 0))
    else:
        tela.fill((10, 10, 30))

def desenhar_titulo(tela, tempo, largura, fonte_titulo, fonte_sub):
    oscilacao = math.sin(tempo / 400) * 8

    txt = fonte_titulo.render("ECO DO ABISMO", True, (220, 230, 255))
    sombra = fonte_titulo.render("ECO DO ABISMO", True, (50, 50, 80))

    tela.blit(sombra, sombra.get_rect(center=(largura // 2 + 4, 150 + int(oscilacao) + 4)))
    tela.blit(txt, txt.get_rect(center=(largura // 2, 150 + int(oscilacao))))

    sub = fonte_sub.render("Tome as pílulas e mantenha sua sanidade...", True, (130, 140, 160))
    tela.blit(sub, sub.get_rect(center=(largura // 2, 230 + int(oscilacao))))

def _quarto_intro(largura, altura, tempo_ms):
    """Quarto de internação em pixel art: piso, parede, janela com grades e luar, lâmpada piscando."""
    s = pygame.Surface((largura, altura))
    s.fill((26, 34, 36))
    for y in range(300, altura, 40):                      # piso
        for x in range(0, largura, 40):
            c = (58, 72, 70) if ((x // 40 + y // 40) % 2 == 0) else (52, 66, 64)
            pygame.draw.rect(s, c, (x, y, 40, 40))
            pygame.draw.rect(s, (40, 52, 52), (x, y, 40, 40), 1)
    pygame.draw.rect(s, (84, 98, 96), (0, 0, largura, 300))     # parede
    for y in range(0, 300, 20):
        pygame.draw.line(s, (76, 90, 88), (0, y), (largura, y))
    pygame.draw.rect(s, (50, 60, 60), (0, 280, largura, 22))    # rodapé
    pygame.draw.rect(s, (34, 40, 40), (0, 300, largura, 3))
    for x in (130, 560):                                  # janelas com grade
        pygame.draw.rect(s, (30, 38, 52), (x, 70, 110, 100))
        pygame.draw.rect(s, (66, 88, 132), (x + 4, 74, 102, 92))
        pygame.draw.rect(s, (140, 170, 220), (x + 4, 74, 102, 8))
        for bx in range(x + 18, x + 100, 22):
            pygame.draw.rect(s, (30, 32, 38), (bx, 70, 5, 100))
        pygame.draw.rect(s, (44, 46, 54), (x, 70, 110, 100), 4)
        facho = pygame.Surface((160, 240), pygame.SRCALPHA)
        pygame.draw.polygon(facho, (150, 180, 230, 34), [(20, 0), (140, 0), (160, 240), (0, 240)])
        s.blit(facho, (x - 25, 172))
    pygame.draw.circle(s, (200, 196, 180), (400, 70), 22)   # relógio
    pygame.draw.circle(s, (50, 40, 36), (400, 70), 22, 3)
    pygame.draw.line(s, (50, 40, 36), (400, 70), (400, 54), 3)
    pygame.draw.line(s, (50, 40, 36), (400, 70), (412, 76), 3)
    return s


def _cama_intro(tela, rect_cama):
    x, y, w, h = rect_cama
    pygame.draw.rect(tela, (34, 38, 46), (x - 10, y - 14, w + 20, h + 28), border_radius=8)       # estrutura
    pygame.draw.rect(tela, (70, 78, 90), (x - 10, y - 14, w + 20, 18), border_radius=6)           # cabeceira
    pygame.draw.rect(tela, (150, 160, 168), (x, y, w, h), border_radius=8)                         # colchão
    pygame.draw.rect(tela, (200, 208, 212), (x + 10, y + 8, 54, h - 16), border_radius=10)         # travesseiro
    pygame.draw.rect(tela, (150, 160, 168), (x + 10, y + 8, 54, h - 16), 3, border_radius=10)


def _cobertor_intro(tela, rect_cama):
    x, y, w, h = rect_cama
    pygame.draw.rect(tela, (76, 98, 108), (x + 74, y - 2, w - 70, h + 4), border_radius=6)
    pygame.draw.rect(tela, (52, 70, 80), (x + 74, y - 2, w - 70, h + 4), 3, border_radius=6)
    for k in range(1, 5):
        pygame.draw.line(tela, (62, 82, 92), (x + 74 + k * 22, y + 4), (x + 74 + k * 22, y + h - 4), 2)


def desenhar_intro_acordar(tela, tempo_decorrido, largura, altura, fonte_sub, sprites_jogador=None,
                            duracao_total=3400):
    tela.blit(_quarto_intro(largura, altura, tempo_decorrido), (0, 0))

    rect_cama = pygame.Rect(largura // 2 - 130, altura // 2 - 10, 260, 90)
    _cama_intro(tela, rect_cama)

    fase_texto_1 = duracao_total * 0.35
    fase_abertura_fim = duracao_total

    if sprites_jogador:
        try:
            if tempo_decorrido >= fase_abertura_fim:
                sprite = sprites_jogador['frente']['parado']
                tela.blit(sprite, sprite.get_rect(midbottom=(rect_cama.centerx - 40, rect_cama.top + 30)))
            else:
                deitado = pygame.transform.rotate(sprites_jogador['frente']['parado'], 90)
                respira = int(2 * math.sin(tempo_decorrido / 420))
                tela.blit(deitado, deitado.get_rect(center=(rect_cama.x + 70, rect_cama.centery - 6 + respira)))
        except Exception:
            pass
    if tempo_decorrido < fase_abertura_fim:
        _cobertor_intro(tela, rect_cama)

    # lâmpada que pisca e vinheta
    pisca = 0.55 + 0.45 * (1 if (tempo_decorrido // 170) % 11 else 0.3)
    sombra = pygame.Surface((largura, altura), pygame.SRCALPHA)
    sombra.fill((0, 0, 8, int(120 * (1.2 - pisca))))
    tela.blit(sombra, (0, 0))
    for r in range(380, 120, -26):
        a = int(18 * (1 - r / 380) * 5)
        pygame.draw.circle(sombra, (0, 0, 0, 0), (largura // 2, altura // 2), r)
    vig = pygame.Surface((largura, altura), pygame.SRCALPHA)
    for k in range(10):
        pygame.draw.rect(vig, (0, 0, 0, 14 * (10 - k)), (k * 14, k * 10, largura - k * 28, altura - k * 20), 14)
    tela.blit(vig, (0, 0))

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
