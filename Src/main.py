import pygame
import sys
import math
import random

pygame.init()

LARGURA, ALTURA = 900, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Eco do Abismo")

PRETO        = (0, 0, 0)
BRANCO       = (255, 255, 255)
AZUL_ABISMO  = (10, 20, 45)
AZUL_ESCURO  = (5, 10, 30)
CIANO_BRILHO = (0, 220, 255)
CIANO_SUAVE  = (0, 150, 180)
CINZA_NÉVOA  = (40, 60, 90)
DOURADO      = (200, 160, 50)
DOURADO_BRILHO = (255, 210, 80)

try:
    fonte_titulo   = pygame.font.SysFont("consolas", 64, bold=True)
    fonte_subtitulo = pygame.font.SysFont("consolas", 20)
    fonte_botao    = pygame.font.SysFont("consolas", 26, bold=True)
except:
    fonte_titulo   = pygame.font.SysFont(None, 64)
    fonte_subtitulo = pygame.font.SysFont(None, 20)
    fonte_botao    = pygame.font.SysFont(None, 26)

relogio = pygame.time.Clock()

class Particula:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x     = random.uniform(0, LARGURA)
        self.y     = random.uniform(0, ALTURA)
        self.vy    = random.uniform(-0.3, -0.08)
        self.vx    = random.uniform(-0.15, 0.15)
        self.raio  = random.uniform(1, 3)
        self.alfa  = random.randint(40, 180)
        self.cor   = random.choice([CIANO_BRILHO, CIANO_SUAVE, (100, 200, 255)])

    def atualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.alfa -= 0.4
        if self.alfa <= 0 or self.y < -5:
            self.reset()
            self.y = ALTURA + 5

    def desenhar(self, surf):
        s = pygame.Surface((self.raio * 2 + 2, self.raio * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.cor, int(self.alfa)), (int(self.raio) + 1, int(self.raio) + 1), int(self.raio))
        surf.blit(s, (int(self.x), int(self.y)))


particulas = [Particula() for _ in range(90)]

class Botao:
    def __init__(self, texto, cx, cy, largura=260, altura=52):
        self.texto   = texto
        self.rect    = pygame.Rect(cx - largura // 2, cy - altura // 2, largura, altura)
        self.hovered = False
        self.escala  = 1.0
        self.brilho  = 0.0

    def atualizar(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        alvo_escala  = 1.06 if self.hovered else 1.0
        alvo_brilho  = 1.0  if self.hovered else 0.0
        self.escala  += (alvo_escala - self.escala)  * 0.15
        self.brilho  += (alvo_brilho - self.brilho)  * 0.12

    def desenhar(self, surf):
        larg = int(self.rect.width  * self.escala)
        alt  = int(self.rect.height * self.escala)
        rx   = self.rect.centerx - larg // 2
        ry   = self.rect.centery - alt  // 2
        r    = pygame.Rect(rx, ry, larg, alt)

        sombra = pygame.Surface((larg + 10, alt + 10), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 180, 220, 40), sombra.get_rect(), border_radius=8)
        surf.blit(sombra, (rx - 5, ry + 6))

        cor_fundo = (
            int(5  + self.brilho * 0),
            int(25 + self.brilho * 30),
            int(55 + self.brilho * 30),
        )
        pygame.draw.rect(surf, cor_fundo, r, border_radius=8)

        # Borda
        alfa_borda = int(120 + self.brilho * 135)
        borda_surf = pygame.Surface((larg, alt), pygame.SRCALPHA)
        pygame.draw.rect(borda_surf, (*CIANO_BRILHO, alfa_borda), borda_surf.get_rect(), width=2, border_radius=8)
        surf.blit(borda_surf, (rx, ry))

        linha_cor = (*CIANO_BRILHO, int(80 + self.brilho * 175))
        linha_surf = pygame.Surface((4, alt - 16), pygame.SRCALPHA)
        pygame.draw.rect(linha_surf, linha_cor, linha_surf.get_rect(), border_radius=2)
        surf.blit(linha_surf, (rx + 10, ry + 8))

        cor_texto = (
            int(180 + self.brilho * 75),
            int(220 + self.brilho * 35),
            int(240 + self.brilho * 15),
        )
        txt = fonte_botao.render(self.texto, True, cor_texto)
        surf.blit(txt, txt.get_rect(center=r.center))

    def clicado(self, evento):
        return evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.rect.collidepoint(evento.pos)

cx_botoes = LARGURA // 2
botoes = [
    Botao("▶  JOGAR",    cx_botoes, 340),
    Botao("★  CRÉDITOS", cx_botoes, 410),
    Botao("✕  SAIR",     cx_botoes, 480),
]

def desenhar_fundo(surf, tempo):
    for y in range(ALTURA):
        t   = y / ALTURA
        r   = int(AZUL_ESCURO[0] + t * (AZUL_ABISMO[0] - AZUL_ESCURO[0]))
        g   = int(AZUL_ESCURO[1] + t * (AZUL_ABISMO[1] - AZUL_ESCURO[1]))
        b   = int(AZUL_ESCURO[2] + t * (AZUL_ABISMO[2] - AZUL_ESCURO[2]))
        pygame.draw.line(surf, (r, g, b), (0, y), (LARGURA, y))

    for i in range(6):
        fase = tempo * 0.0008 + i * 0.9
        alfa = int(abs(math.sin(fase)) * 18 + 4)
        y_   = int(ALTURA * 0.55 + i * 28)
        hl   = pygame.Surface((LARGURA, 1), pygame.SRCALPHA)
        hl.fill((0, 180, 220, alfa))
        surf.blit(hl, (0, y_))

    nevoa = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    raio  = int(260 + math.sin(tempo * 0.001) * 20)
    pygame.draw.ellipse(nevoa, (0, 100, 150, 18),
                        (LARGURA // 2 - raio, ALTURA // 2 - 120, raio * 2, 280))
    surf.blit(nevoa, (0, 0))

def desenhar_titulo(surf, tempo):
    pulso = math.sin(tempo * 0.002) * 0.5 + 0.5   # 0 → 1

    sombra = fonte_titulo.render("ECO DO ABISMO", True, (0, 40, 80))
    pos_s  = sombra.get_rect(center=(LARGURA // 2 + 3, 165))
    surf.blit(sombra, pos_s)

    for offset, alfa_base in [(6, 18), (3, 35)]:
        glow_surf = pygame.Surface((LARGURA, 120), pygame.SRCALPHA)
        txt_g     = fonte_titulo.render("ECO DO ABISMO", True,
                                        (*CIANO_BRILHO, int(alfa_base + pulso * 20)))
        glow_surf.blit(txt_g, txt_g.get_rect(center=(LARGURA // 2, 60)))
        for dx in range(-offset, offset + 1, 2):
            surf.blit(glow_surf, (dx, 105))

    r_ = int(100 + pulso * 80)
    g_ = int(200 + pulso * 55)
    b_ = int(240 + pulso * 15)
    txt_main = fonte_titulo.render("ECO DO ABISMO", True, (r_, g_, b_))
    surf.blit(txt_main, txt_main.get_rect(center=(LARGURA // 2, 165)))

    linha_w = 340
    lx = LARGURA // 2 - linha_w // 2
    ly = 200
    cor_linha = (*CIANO_BRILHO, int(80 + pulso * 120))
    linha_s = pygame.Surface((linha_w, 2), pygame.SRCALPHA)
    linha_s.fill(cor_linha)
    surf.blit(linha_s, (lx, ly))

    sub = fonte_subtitulo.render("— Desça. Ouça. Sobreviva. —", True,
                                  (int(80 + pulso * 40), int(160 + pulso * 40), int(200 + pulso * 30)))
    surf.blit(sub, sub.get_rect(center=(LARGURA // 2, 218)))

def main():
    rodando = True
    while rodando:
        tempo = pygame.time.get_ticks()
        mouse = pygame.mouse.get_pos()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            for botao in botoes:
                if botao.clicado(evento):
                    if botao.texto.endswith("SAIR"):
                        rodando = False

        for p in particulas:
            p.atualizar()
        for botao in botoes:
            botao.atualizar(mouse)

        desenhar_fundo(tela, tempo)
        for p in particulas:
            p.desenhar(tela)
        desenhar_titulo(tela, tempo)
        for botao in botoes:
            botao.desenhar(tela)
       
        rodape = fonte_subtitulo.render("© 2026  Eco do Abismo  —  Todos os direitos reservados", True, (40, 70, 100))
        tela.blit(rodape, rodape.get_rect(center=(LARGURA // 2, ALTURA - 20)))

        pygame.display.flip()
        relogio.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":

