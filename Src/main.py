import pygame
import sys
import math
import random
from personagem import Jogador, CameraSeguranca
from nivel import Sala
from puzzle import PuzzleRadio
from interface_usuario import desenhar_hud, desenhar_mensagem_contextual, desenhar_flash_detectado

pygame.init()

LARGURA, ALTURA = 900, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Eco do Abismo")

PRETO          = (0, 0, 0)
BRANCO         = (255, 255, 255)
AZUL_ABISMO    = (10, 20, 45)
AZUL_ESCURO    = (5, 10, 30)
CIANO_BRILHO   = (0, 220, 255)
CIANO_SUAVE    = (0, 150, 180)
CINZA_NÉVOA    = (40, 60, 90)
DOURADO        = (200, 160, 50)
DOURADO_BRILHO = (255, 210, 80)
VERMELHO_SANGUE = (180, 20, 20)
AMARELO_ALERTA = (230, 200, 60)

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


class FrascoPilula:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 25)
        self.coletado = False

    def desenhar(self, surf):
        if not self.coletado:
            pygame.draw.rect(surf, DOURADO, self.rect, border_radius=3)
            pygame.draw.rect(surf, BRANCO, (self.rect.x + 4, self.rect.y - 4, 12, 5))


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

        cor_fundo = (int(5 + self.brilho * 0), int(25 + self.brilho * 30), int(55 + self.brilho * 30))
        pygame.draw.rect(surf, cor_fundo, r, border_radius=8)

        alfa_borda = int(120 + self.brilho * 135)
        borda_surf = pygame.Surface((larg, alt), pygame.SRCALPHA)
        pygame.draw.rect(borda_surf, (*CIANO_BRILHO, alfa_borda), borda_surf.get_rect(), width=2, border_radius=8)
        surf.blit(borda_surf, (rx, ry))

        linha_cor = (*CIANO_BRILHO, int(80 + self.brilho * 175))
        linha_surf = pygame.Surface((4, alt - 16), pygame.SRCALPHA)
        pygame.draw.rect(linha_surf, linha_cor, linha_surf.get_rect(), border_radius=2)
        surf.blit(linha_surf, (rx + 10, ry + 8))

        cor_texto = (int(180 + self.brilho * 75), int(220 + self.brilho * 35), int(240 + self.brilho * 15))
        txt = fonte_botao.render(self.texto, True, cor_texto)
        surf.blit(txt, txt.get_rect(center=r.center))

    def clicado(self, evento):
        return evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.rect.collidepoint(evento.pos)


particulas = [Particula() for _ in range(90)]
cx_botoes = LARGURA // 2
botoes = [
    Botao("JOGAR",    cx_botoes, 340),
    Botao("CRÉDITOS", cx_botoes, 410),
    Botao("SAIR",     cx_botoes, 480),
]


def gerar_frascos_na_sala():
    """Lógica de Spawn Aleatório (Semana 3), evitando posições muito perto da porta."""
    posicoes_possiveis = [
        (220, 150), (450, 120), (720, 180),
        (150, 420), (520, 310),
        (330, 490), (610, 240)
    ]
    quantidade_para_spawnar = random.randint(3, 5)
    posicoes_escolhidas = random.sample(posicoes_possiveis, quantidade_para_spawnar)
    return [FrascoPilula(pos[0], pos[1]) for pos in posicoes_escolhidas]


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
    pygame.draw.ellipse(nevoa, (0, 100, 150, 18), (LARGURA // 2 - raio, ALTURA // 2 - 120, raio * 2, 280))
    surf.blit(nevoa, (0, 0))


def desenhar_titulo(surf, tempo):
    pulso = math.sin(tempo * 0.002) * 0.5 + 0.5
    sombra = fonte_titulo.render("ECO DO ABISMO", True, (0, 40, 80))
    surf.blit(sombra, sombra.get_rect(center=(LARGURA // 2 + 3, 165)))

    for offset, alfa_base in [(6, 18), (3, 35)]:
        glow_surf = pygame.Surface((LARGURA, 120), pygame.SRCALPHA)
        txt_g     = fonte_titulo.render("ECO DO ABISMO", True, (*CIANO_BRILHO, int(alfa_base + pulso * 20)))
        glow_surf.blit(txt_g, txt_g.get_rect(center=(LARGURA // 2, 60)))
        for dx in range(-offset, offset + 1, 2):
            surf.blit(glow_surf, (dx, 105))

    r_ = int(100 + pulso * 80)
    g_ = int(200 + pulso * 55)
    b_ = int(240 + pulso * 15)
    txt_main = fonte_titulo.render("ECO DO ABISMO", True, (r_, g_, b_))
    surf.blit(txt_main, txt_main.get_rect(center=(LARGURA // 2, 165)))

    linha_w, ly = 340, 200
    linha_s = pygame.Surface((linha_w, 2), pygame.SRCALPHA)
    linha_s.fill((*CIANO_BRILHO, int(80 + pulso * 120)))
    surf.blit(linha_s, (LARGURA // 2 - linha_w // 2, ly))

    sub = fonte_subtitulo.render("— Desça. Ouça. Sobreviva. —", True, (int(80 + pulso * 40), int(160 + pulso * 40), int(200 + pulso * 30)))
    surf.blit(sub, sub.get_rect(center=(LARGURA // 2, 218)))


def iniciar_sala(jogador):
    """Reseta o estado da sala atual: posição do jogador, frascos, câmera e puzzle."""
    jogador.sanidade = 100
    jogador.quantidade_pilulas = 0
    jogador.efeito_pilula_ativo = False

    sala = Sala(LARGURA, ALTURA, ponto_entrada=(60, ALTURA // 2 - 16))
    jogador.x, jogador.y = sala.ponto_entrada

    frascos = gerar_frascos_na_sala()
    
    camera = CameraSeguranca(x=LARGURA - 40, y=40, angulo_inicial=135,
                              alcance=260, abertura_graus=50,
                              velocidade_giro=0.5, arco_max=35)

    puzzle = PuzzleRadio(LARGURA, ALTURA)

    return sala, frascos, camera, puzzle


def main():
    rodando = True
    estado = "MENU"

    jogador = Jogador(100, 300, "Operário 724")
    sala, frascos, camera, puzzle = iniciar_sala(jogador)

    puzzle_aberto = False
    offset_tremor_x = 0
    offset_tremor_y = 0
    mensagem_flash_ativo = False
    tempo_flash = 0

    while rodando:
        tempo = pygame.time.get_ticks()
        mouse = pygame.mouse.get_pos()
        teclas = pygame.key.get_pressed()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            if estado == "MENU":
                for botao in botoes:
                    if botao.clicado(evento):
                        if botao.texto.endswith("JOGAR"):
                            estado = "JOGANDO"
                            sala, frascos, camera, puzzle = iniciar_sala(jogador)
                            puzzle_aberto = False
                        elif botao.texto.endswith("SAIR"):
                            rodando = False

            elif estado == "JOGANDO":
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        if puzzle_aberto:
                            puzzle_aberto = False
                        else:
                            estado = "MENU"

                    if evento.key == pygame.K_e and not puzzle_aberto:
                        acao_realizada = False

                        for f in frascos:
                            if not f.coletado and jogador.get_rect().colliderect(f.rect):
                                f.coletado = True
                                jogador.quantidade_pilulas += 1
                                acao_realizada = True
                                break

                        if not acao_realizada and not sala.porta_aberta and sala.jogador_na_porta(jogador):
                            puzzle_aberto = True
                            acao_realizada = True
                            
                        if not acao_realizada:
                            jogador.tentar_tomar_pilula(tempo)

                if puzzle_aberto:
                    puzzle.processar_evento(evento)

        if estado == "MENU":
            for p in particulas:
                p.atualizar()
            for botao in botoes:
                botao.atualizar(mouse)

        elif estado == "JOGANDO":
            if puzzle_aberto:
                puzzle.atualizar(teclas)
                if puzzle.resolvido:
                    sala.porta_aberta = True
            else:
                jogador.andar_teclas(teclas, LARGURA, ALTURA, paredes=sala.paredes_colisao())
                jogador.dano_sanidade(0.03)
                jogador.atualizar_efeito_pilula(tempo)
                camera.atualizar()

                if camera.detecta(jogador):
                    mensagem_flash_ativo = True
                    tempo_flash = tempo
                    jogador.x, jogador.y = sala.ponto_entrada

                if mensagem_flash_ativo and tempo - tempo_flash > 250:
                    mensagem_flash_ativo = False

                if sala.porta_aberta and sala.jogador_na_porta(jogador):
                    sala, frascos, camera, puzzle = iniciar_sala(jogador)
                    puzzle_aberto = False

                if jogador.sanidade <= 0:
                    sala, frascos, camera, puzzle = iniciar_sala(jogador)
                    puzzle_aberto = False

            if jogador.sanidade < 30:
                offset_tremor_x = random.randint(-3, 3)
                offset_tremor_y = random.randint(-3, 3)
            else:
                offset_tremor_x, offset_tremor_y = 0, 0

        if estado == "MENU":
            desenhar_fundo(tela, tempo)
            for p in particulas:
                p.desenhar(tela)
            desenhar_titulo(tela, tempo)
            for botao in botoes:
                botao.desenhar(tela)

            rodape = fonte_subtitulo.render("© 2026  Eco do Abismo  —  Todos os direitos reservados", True, (40, 70, 100))
            tela.blit(rodape, rodape.get_rect(center=(LARGURA // 2, ALTURA - 20)))

        elif estado == "JOGANDO":
            superficie_fase = pygame.Surface((LARGURA, ALTURA))
            superficie_fase.fill(AZUL_ESCURO)

            sala.desenhar(superficie_fase)

            for f in frascos:
                f.desenhar(superficie_fase)

            cone_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            cor_cone = (*VERMELHO_SANGUE, 70) if camera.detecta(jogador) else (*AMARELO_ALERTA, 45)
            pygame.draw.polygon(cone_surf, cor_cone, camera.pontos_do_cone())
            superficie_fase.blit(cone_surf, (0, 0))

            cor_lente = VERMELHO_SANGUE if camera.detecta(jogador) else (200, 200, 210)
            pygame.draw.rect(superficie_fase, (30, 30, 35), (camera.x - 12, camera.y - 12, 24, 24), border_radius=3)
            dir_x = math.cos(math.radians(camera.angulo))
            dir_y = math.sin(math.radians(camera.angulo))
            ponta_lente = (camera.x + dir_x * 16, camera.y + dir_y * 16)
            pygame.draw.circle(superficie_fase, cor_lente, ponta_lente, 6)

            cor_player = CIANO_BRILHO if jogador.efeito_pilula_ativo else BRANCO
            pygame.draw.rect(superficie_fase, cor_player, jogador.get_rect(), border_radius=4)

            tela.blit(superficie_fase, (offset_tremor_x, offset_tremor_y))

            desenhar_hud(tela, jogador, fonte_subtitulo)

            if not sala.porta_aberta and sala.jogador_na_porta(jogador) and not puzzle_aberto:
                desenhar_mensagem_contextual(tela, "Pressione E para acessar o painel de rádio",
                                              LARGURA, ALTURA, fonte_subtitulo)
            elif sala.porta_aberta and sala.jogador_na_porta(jogador):
                desenhar_mensagem_contextual(tela, "Porta liberada — siga em frente",
                                              LARGURA, ALTURA, fonte_subtitulo)

            if puzzle_aberto:
                puzzle.desenhar(tela, fonte_subtitulo)

            if mensagem_flash_ativo:
                desenhar_flash_detectado(tela, LARGURA, ALTURA)

        pygame.display.flip()
        relogio.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()