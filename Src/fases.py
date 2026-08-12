import pygame
import random
from configuracoes import LARGURA, ALTURA, AZUL_ESCURO, BRANCO, CINZA_BORDA
from nivel import Sala
from personagem import CameraSeguranca, Inimigo
from itens import gerar_frascos_na_sala
from interface_usuario import desenhar_hud, desenhar_mensagem_contextual, desenhar_flash_detectado
from puzzle import CaixaArrastavel, PuzzleCaixaFerramentas, PuzzleRadio


def nivel_1(jogador, resetar_jogador=False):
    jogador.sanidade = 100
    jogador.tem_pe_de_cabra = False
    jogador.agachado = False

    sala = Sala(LARGURA, ALTURA, ponto_entrada=(60, ALTURA // 2 - 16))
    jogador.x, jogador.y = sala.ponto_entrada

    cameras = [
        CameraSeguranca(x=LARGURA - 40, y=40, angulo_inicial=135,
                         alcance=260, abertura_graus=50,
                         velocidade_giro=0.5, arco_max=35)
    ]
    caixas = []
    caixa_ferramentas = None
    duto_dados = None

    frascos = gerar_frascos_na_sala(1)
    puzzle = PuzzleRadio(LARGURA, ALTURA)
    puzzle_caixa = PuzzleCaixaFerramentas(LARGURA, ALTURA)

    inimigos = []
    return sala, frascos, cameras, puzzle, caixa_ferramentas, caixas, duto_dados, puzzle_caixa, inimigos


def nivel_2(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.tem_pe_de_cabra = False
        jogador.agachado = False

    sala = Sala(LARGURA, ALTURA, ponto_entrada=(60, ALTURA // 2 - 16))
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = False

    cameras = [
        CameraSeguranca(x=430, y=40, angulo_inicial=90, alcance=500,
                         abertura_graus=32, velocidade_giro=0.0, arco_max=0)
    ]

    caixas = [
        CaixaArrastavel(70, ALTURA - 90),
        CaixaArrastavel(70, ALTURA - 145),
    ]
    caixa_ferramentas = pygame.Rect(75, ALTURA - 85, 30, 20)

    duto_dados = {
        "corredor": pygame.Rect(280, 45, 260, 45),
        "porta_entrada_aberta": False,
        "porta_saida_aberta": False,
        "rect_entrada": pygame.Rect(280, 45, 15, 45),
        "rect_saida": pygame.Rect(525, 45, 15, 45),
    }

    frascos = gerar_frascos_na_sala(2)
    puzzle = PuzzleRadio(LARGURA, ALTURA)
    puzzle_caixa = PuzzleCaixaFerramentas(LARGURA, ALTURA)
    inimigos = []
    return sala, frascos, cameras, puzzle, caixa_ferramentas, caixas, duto_dados, puzzle_caixa, inimigos


def nivel_3(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.tem_pe_de_cabra = False
        jogador.agachado = False

    sala = Sala(LARGURA, ALTURA, ponto_entrada=(60, ALTURA // 2 - 16))
    jogador.x, jogador.y = sala.ponto_entrada

    cameras = [
        CameraSeguranca(x=40, y=40, angulo_inicial=45, alcance=220,
                         abertura_graus=50, velocidade_giro=1.3, arco_max=40),
        CameraSeguranca(x=LARGURA - 40, y=40, angulo_inicial=135, alcance=220,
                         abertura_graus=50, velocidade_giro=1.3, arco_max=40),
    ]

    inimigos = [Inimigo(x=400, y=300, nome='inimigo_1', largura_tela=LARGURA, altura_tela=ALTURA)]

    caixas = []
    caixa_ferramentas = None
    duto_dados = None

    frascos = gerar_frascos_na_sala(3)
    puzzle = PuzzleRadio(LARGURA, ALTURA)
    puzzle_caixa = PuzzleCaixaFerramentas(LARGURA, ALTURA)

    return sala, frascos, cameras, puzzle, caixa_ferramentas, caixas, duto_dados, puzzle_caixa, inimigos

NIVEIS = {
    1: nivel_1,
    2: nivel_2,
    3: nivel_3,
}

def iniciar_sala(jogador, nivel, resetar_jogador=False):
    fn = NIVEIS.get(nivel, nivel_2)
    return fn(jogador, resetar_jogador=resetar_jogador)


def renderizar_jogo(tela, jogador, sala, frascos, cameras, puzzle, puzzle_aberto, nivel_atual, offset_x, offset_y, flash_ativo, LARGURA, ALTURA, fonte_sub, caixa_ferramentas=None, caixas=None, duto_dados=None, puzzle_caixa=None, inimigos=None):

    inimigos = inimigos if not None else []
    caixas = caixas if not None else []
    superficie_fase = pygame.Surface((LARGURA, ALTURA))
    superficie_fase.fill(AZUL_ESCURO)
    cone_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

    if nivel_atual == 2:
        sala.porta_aberta = False
        
    sala.desenhar(superficie_fase)
    
    for f in frascos:
        f.desenhar(superficie_fase)

    if nivel_atual == 2 and duto_dados:
        pygame.draw.rect(superficie_fase, (50, 50, 55), duto_dados["corredor"])
        pygame.draw.rect(superficie_fase, (80, 80, 85), duto_dados["corredor"], width=2)
        
        if not duto_dados["porta_entrada_aberta"]:
            pygame.draw.rect(superficie_fase, (140, 140, 150), duto_dados["rect_entrada"])
        if not duto_dados["porta_saida_aberta"]:
            pygame.draw.rect(superficie_fase, (140, 140, 150), duto_dados["rect_saida"])

    if nivel_atual == 2 and caixa_ferramentas:
        caixa_coberta = False
        for cx in caixas:
            if cx.rect.colliderect(caixa_ferramentas):
                caixa_coberta = True
        if not caixa_coberta:
            pygame.draw.rect(superficie_fase, (150, 35, 35), caixa_ferramentas, border_radius=3)
            pygame.draw.rect(superficie_fase, (220, 200, 50), (caixa_ferramentas.x+10, caixa_ferramentas.y, 10, 4))

    for cx in caixas:
        cx.desenhar(superficie_fase)

    for inimigo in inimigos:
        inimigo.desenhar(superficie_fase)

    for camera in cameras:
        camera.desenhar(superficie_fase, cone_surf, jogador)
        
    superficie_fase.blit(cone_surf, (0, 0))
    
    cor_player = (180, 220, 255) if getattr(jogador, 'agachado', False) else BRANCO
    pygame.draw.rect(superficie_fase, cor_player, jogador.get_rect(), border_radius=4)
    
    tela.blit(superficie_fase, (offset_x, offset_y))

    desenhar_hud(tela, jogador, fonte_sub)
    texto_nivel = fonte_sub.render(f"SALA {nivel_atual}", True, CINZA_BORDA)
    tela.blit(texto_nivel, (LARGURA - texto_nivel.get_width() - 20, 20))

    if nivel_atual == 2 and duto_dados:
        rect_player = jogador.get_rect()
        
        if rect_player.colliderect(duto_dados["rect_entrada"].inflate(20, 20)):
            if not duto_dados["porta_entrada_aberta"]:
                desenhar_mensagem_contextual(tela, "Pressione E com o Pé de Cabra para arrancar a grade", LARGURA, ALTURA, fonte_sub)
            elif not getattr(jogador, 'agachado', False):
                desenhar_mensagem_contextual(tela, "O duto é muito estreito. Pressione Q para agachar", LARGURA, ALTURA, fonte_sub)
        
        elif rect_player.colliderect(duto_dados["rect_saida"].inflate(20, 20)) and not duto_dados["porta_saida_aberta"]:
            desenhar_mensagem_contextual(tela, "Grade de saída trancada! Pressione E para quebrar", LARGURA, ALTURA, fonte_sub)

        if caixa_ferramentas and rect_player.colliderect(caixa_ferramentas.inflate(15, 15)) and not getattr(jogador, 'tem_pe_de_cabra', False):
            caixa_coberta = False
            for cx in caixas:
                if cx.rect.colliderect(caixa_ferramentas): caixa_coberta = True
            if not caixa_coberta:
                desenhar_mensagem_contextual(tela, "Pressione E para revirar a Caixa de Ferramentas", LARGURA, ALTURA, fonte_sub)

        for cx in caixas:
            if rect_player.inflate(15, 15).colliderect(cx.rect):
                desenhar_mensagem_contextual(tela, "Segure [R] + Direcionais para mover a caixa de madeira", LARGURA, ALTURA, fonte_sub, y=ALTURA - 90)

    if puzzle_aberto:
        puzzle.desenhar(tela, fonte_sub)
    if puzzle_caixa and puzzle_caixa.ativo:
        puzzle_caixa.desenhar(tela, fonte_sub)
    if flash_ativo:
        desenhar_flash_detectado(tela, LARGURA, ALTURA)