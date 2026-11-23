import math
import os
import random

import pygame

from configuracoes import VERMELHO_ALARME
from personagem import Inimigo, GuardaPrisao

_AQUI = os.path.dirname(os.path.abspath(__file__))


def _achar_pasta():
    for base in (_AQUI, os.path.join(_AQUI, "..")):
        caminho = os.path.normpath(os.path.join(base, "assets", "sprites", "operario"))
        if os.path.isdir(caminho):
            return caminho
    return os.path.join(_AQUI, "assets", "sprites", "operario")


PASTA_SPRITES = _achar_pasta()
_DIRECOES = ("frente", "costas", "direita", "esquerda")
TAMANHO = 110

_cache = None
_arte = {}


def _carregar_imagem(nome_arquivo, obrigatoria=True):
    caminho = os.path.join(PASTA_SPRITES, nome_arquivo)
    if not obrigatoria and not os.path.exists(caminho):
        return None
    imagem = pygame.image.load(caminho).convert_alpha()
    return pygame.transform.scale(imagem, (TAMANHO, TAMANHO))


def carregar_sprites_operario():
    """Devolve o dicionário de sprites.

    sprites[direcao]['parado'] / ['andando'][0..1]   -> como antes
    sprites['agachado'][direcao]['parado'/'andando'] -> só 'direita'/'esquerda'
    sprites['pilula'][0..4]                          -> animação de tomar a pílula
    sprites['dano'][0..2]                            -> animação de levar dano
    Os arquivos novos são opcionais: se faltarem, o jogo usa o desenho antigo.
    """
    global _cache
    if _cache is not None:
        return _cache

    sprites = {}
    for direcao in _DIRECOES:
        sprites[direcao] = {
            "parado": _carregar_imagem(f"idle_{direcao}.png"),
            "andando": [
                _carregar_imagem(f"andando_{direcao}_1.png"),
                _carregar_imagem(f"andando_{direcao}_2.png"),
            ],
        }

    agachado = {}
    for lado in _DIRECOES:
        parado = _carregar_imagem(f"agachado_{lado}_parado.png", False)
        a1 = _carregar_imagem(f"agachado_{lado}_andando_1.png", False)
        a2 = _carregar_imagem(f"agachado_{lado}_andando_2.png", False)
        if parado and a1 and a2:
            agachado[lado] = {"parado": parado, "andando": [a1, a2]}
    if "direita" in agachado and "esquerda" not in agachado:
        agachado["esquerda"] = {
            "parado": pygame.transform.flip(agachado["direita"]["parado"], True, False),
            "andando": [pygame.transform.flip(i, True, False) for i in agachado["direita"]["andando"]],
        }
    sprites["agachado"] = agachado

    sprites["pilula"] = [i for i in (_carregar_imagem(f"pilula_{n}.png", False) for n in range(1, 6)) if i]
    sprites["dano"] = [i for i in (_carregar_imagem(f"dano_{n}.png", False) for n in range(1, 4)) if i]

    _cache = sprites
    return sprites


_telas = {}


def carregar_tela(nome):
    """Carrega assets/telas/<nome>.png (800x600). Devolve None se não existir."""
    if nome in _telas:
        return _telas[nome]
    img = None
    for base in (_AQUI, os.path.join(_AQUI, "..")):
        caminho = os.path.normpath(os.path.join(base, "assets", "telas", nome + ".png"))
        if os.path.exists(caminho):
            try:
                img = pygame.image.load(caminho).convert()
            except Exception:
                img = None
            break
    _telas[nome] = img
    return img


DURACAO_PILULA_MS = 750      # 5 quadros de 150 ms
DURACAO_DANO_MS = 520
LIMIAR_DANO = 1.0            # queda de sanidade (em um quadro) que conta como "levou dano"


def iniciar_animacao_pilula(jogador, tempo_ms):
    jogador.pilula_inicio = tempo_ms


def _sombra():
    s = _arte.get("sombra_jogador")
    if s is None:
        s = pygame.Surface((70, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, 90), (0, 0, 70, 18))
        _arte["sombra_jogador"] = s
    return s


def desenhar_jogador(superficie, jogador, sprites, tempo_ms):
    """Escolhe o quadro certo (dano > pílula > agachado > normal) e desenha o jogador."""
    # detecta dano pela queda brusca de sanidade (a queda passiva é minúscula)
    ant = getattr(jogador, "_sanidade_ant", jogador.sanidade)
    if ant - jogador.sanidade >= LIMIAR_DANO:
        jogador.dano_inicio = tempo_ms
    jogador._sanidade_ant = jogador.sanidade

    rect = jogador.get_rect()
    pes = (rect.centerx, rect.bottom + 2)
    sombra = _sombra()
    superficie.blit(sombra, sombra.get_rect(center=(rect.centerx, rect.bottom - 2)))

    imagem = None
    tingir = False

    dano_dec = tempo_ms - getattr(jogador, "dano_inicio", -10 ** 9)
    pil_dec = tempo_ms - getattr(jogador, "pilula_inicio", -10 ** 9)

    if 0 <= dano_dec < DURACAO_DANO_MS and sprites.get("dano"):
        quadros = sprites["dano"]
        ordem = [0, 1, 2, 1] if len(quadros) >= 3 else [0]
        imagem = quadros[ordem[min(len(ordem) - 1, dano_dec * len(ordem) // DURACAO_DANO_MS)] % len(quadros)]
        tingir = dano_dec < 260
    elif 0 <= pil_dec < DURACAO_PILULA_MS and sprites.get("pilula") and not jogador.agachado:
        quadros = sprites["pilula"]
        imagem = quadros[min(len(quadros) - 1, pil_dec * len(quadros) // DURACAO_PILULA_MS)]
    elif jogador.agachado and sprites.get("agachado", {}).get(jogador.direcao):
        grupo = sprites["agachado"][jogador.direcao]
        imagem = grupo["andando"][jogador.frame_index] if jogador.andando else grupo["parado"]

    if imagem is None:
        jogador.desenhar(superficie, sprites)
        return

    if tingir:
        imagem = imagem.copy()
        imagem.fill((90, 0, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
    superficie.blit(imagem, imagem.get_rect(midbottom=pes))


def _px(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _x(surf, f):
    return pygame.transform.scale(surf, (surf.get_width() * f, surf.get_height() * f))


def arte(nome):
    """Sprite procedural em cache (itens)."""
    s = _arte.get(nome)
    if s is None:
        # se existir assets/sprites/objetos/<nome>.png, ele substitui o desenho por código
        for base in (_AQUI, os.path.join(_AQUI, "..")):
            caminho = os.path.normpath(os.path.join(base, "assets", "sprites", "objetos", nome + ".png"))
            if os.path.exists(caminho):
                s = pygame.image.load(caminho).convert_alpha()
                break
        if s is None:
            s = _CONSTRUTORES[nome]()
        _arte[nome] = s
    return s


def blit_centro(surf, nome, centro, deslocamento=(0, 0)):
    img = arte(nome)
    surf.blit(img, img.get_rect(center=(centro[0] + deslocamento[0], centro[1] + deslocamento[1])))


P_A, P_B, P_C = (168, 96, 3), (152, 87, 3), (138, 79, 2)
P_ESC, P_K = (76, 34, 0), (53, 31, 0)
M1, M2, M3 = (170, 176, 188), (126, 132, 146), (84, 90, 106)
OURO, OURO_B, OURO_L = (222, 168, 36), (150, 100, 10), (248, 214, 100)


def _pilula():
    s = _px(14, 8)
    pygame.draw.rect(s, (110, 30, 50), (0, 0, 14, 8), border_radius=4)
    pygame.draw.rect(s, (226, 56, 66), (1, 1, 6, 6), border_top_left_radius=3, border_bottom_left_radius=3)
    pygame.draw.rect(s, (70, 116, 236), (7, 1, 6, 6), border_top_right_radius=3, border_bottom_right_radius=3)
    pygame.draw.line(s, (255, 190, 190), (2, 2), (5, 2))
    pygame.draw.line(s, (190, 214, 255), (8, 2), (11, 2))
    return pygame.transform.rotate(_x(s, 2), 35)


def _chave():
    s = _px(14, 7)
    pygame.draw.circle(s, OURO_B, (3, 3), 3)
    pygame.draw.circle(s, OURO, (3, 3), 2)
    pygame.draw.circle(s, (0, 0, 0, 0), (3, 3), 1)
    pygame.draw.rect(s, OURO, (5, 2, 8, 2))
    pygame.draw.rect(s, OURO_B, (5, 4, 8, 1))
    pygame.draw.rect(s, OURO, (10, 4, 2, 3))
    pygame.draw.rect(s, OURO, (12, 4, 2, 2))
    s.set_at((2, 1), OURO_L)
    return _x(s, 2)


def _documento():
    s = _px(11, 8)
    pygame.draw.rect(s, (150, 120, 84), (0, 0, 11, 8))
    pygame.draw.rect(s, (226, 212, 180), (1, 1, 9, 6))
    for y in (2, 4):
        pygame.draw.line(s, (170, 140, 100), (2, y), (8, y))
    pygame.draw.line(s, (150, 120, 84), (2, 6), (5, 6))
    return _x(s, 2)


def _documento_especial():
    s = _px(11, 8)
    pygame.draw.rect(s, P_C, (0, 0, 11, 8))
    pygame.draw.rect(s, (232, 186, 96), (1, 1, 9, 6))
    pygame.draw.line(s, (190, 140, 60), (4, 1), (4, 6))
    pygame.draw.line(s, (190, 140, 60), (7, 1), (7, 6))
    for p in ((8, 2), (9, 3), (9, 2), (8, 3)):
        s.set_at(p, (200, 50, 50))
    return _x(s, 2)


def _dica():
    s = _px(10, 10)
    pygame.draw.rect(s, OURO_B, (0, 0, 10, 10))
    pygame.draw.rect(s, (240, 206, 84), (1, 1, 8, 8))
    pygame.draw.polygon(s, (206, 164, 50), [(6, 9), (9, 6), (9, 9)])
    for y in (3, 5):
        pygame.draw.line(s, OURO_B, (2, y), (6, y))
    return _x(s, 2)


def _mascara():
    s = _px(13, 11)
    pygame.draw.rect(s, (52, 68, 56), (1, 0, 11, 10), border_radius=4)
    pygame.draw.rect(s, (112, 138, 116), (2, 1, 9, 8), border_radius=3)
    for cx in (4, 9):
        pygame.draw.circle(s, (52, 68, 56), (cx, 4), 2)
        pygame.draw.circle(s, (130, 224, 196), (cx, 4), 1)
    pygame.draw.rect(s, M3, (5, 7, 3, 4))
    pygame.draw.line(s, M1, (5, 8), (7, 8))
    return _x(s, 2)


def _lanterna():
    s = _px(10, 7)
    pygame.draw.rect(s, P_C, (0, 1, 7, 5))
    pygame.draw.rect(s, OURO, (1, 2, 5, 3))
    pygame.draw.rect(s, P_C, (7, 0, 3, 7))
    pygame.draw.rect(s, (255, 244, 190), (8, 1, 2, 5))
    return _x(s, 2)


def _pe_de_cabra():
    s = _px(18, 8)
    pygame.draw.line(s, M3, (2, 6), (15, 2), 3)
    pygame.draw.line(s, M1, (2, 5), (15, 1), 1)
    pygame.draw.line(s, M3, (15, 2), (17, 5), 3)
    pygame.draw.line(s, M3, (0, 6), (2, 7), 2)
    return _x(s, 2)


def _caixa_base():
    s = _px(24, 24)
    pygame.draw.rect(s, P_A, (0, 0, 24, 24))
    for y in range(5, 24, 6):
        pygame.draw.line(s, P_B, (0, y), (23, y))
        pygame.draw.line(s, P_C, (0, y + 1), (23, y + 1))
    for (a, b) in (((1, 1), (22, 22)), ((22, 1), (1, 22))):
        pygame.draw.line(s, P_C, a, b, 2)
    pygame.draw.rect(s, P_C, (0, 0, 24, 24), 2)
    pygame.draw.line(s, P_B, (2, 2), (21, 2))
    for c in ((3, 3), (20, 3), (3, 20), (20, 20)):
        pygame.draw.rect(s, M2, (c[0] - 1, c[1] - 1, 3, 3))
        s.set_at((c[0] - 1, c[1] - 1), M1)
    return s


_CONSTRUTORES = {
    "pilula": _pilula, "chave": _chave, "documento": _documento,
    "documento_especial": _documento_especial, "dica": _dica, "mascara": _mascara,
    "lanterna": _lanterna, "pe_de_cabra": _pe_de_cabra, "caixa_base": _caixa_base,
}


def desenhar_caixa(surf, rect):
    """Caixa de madeira de qualquer tamanho (caixas empurráveis, obstáculos, entulho)."""
    chave = ("caixa", rect.width, rect.height)
    img = _arte.get(chave)
    if img is None:
        img = pygame.transform.scale(arte("caixa_base"), (max(4, rect.width), max(4, rect.height)))
        _arte[chave] = img
    surf.blit(img, rect.topleft)


def desenhar_pilula(surf, rect, flutuacao, brilho=1.0):
    cx, cy = rect.centerx, rect.centery + flutuacao
    halo = _arte.get("halo_pilula")
    if halo is None:
        halo = _px(60, 60)
        for r in range(28, 4, -4):
            pygame.draw.circle(halo, (90, 200, 255, int(34 * (1 - r / 28))), (30, 30), r)
        _arte["halo_pilula"] = halo
    surf.blit(halo, halo.get_rect(center=(cx, cy)))
    img = arte("pilula")
    surf.blit(img, img.get_rect(center=(cx, cy)))


def desenhar_valvula(surf, pos, girada, tempo_ms=0):
    x, y = pos
    cano = (70, 76, 88)
    pygame.draw.rect(surf, (40, 44, 54), (x - 22, y - 5, 44, 10))
    pygame.draw.rect(surf, cano, (x - 22, y - 3, 44, 6))
    pygame.draw.rect(surf, (95, 100, 112), (x - 22, y - 3, 44, 2))
    pygame.draw.rect(surf, (45, 48, 56), (x - 4, y - 14, 8, 12))
    cor = (70, 200, 110) if girada else (205, 70, 60)
    escuro = (25, 80, 45) if girada else (90, 25, 22)
    ang = math.radians(45 if girada else 0)
    for k in range(4):
        a = ang + k * math.pi / 2
        ex, ey = x + math.cos(a) * 15, y - 16 + math.sin(a) * 15
        pygame.draw.line(surf, escuro, (x, y - 16), (ex, ey), 5)
        pygame.draw.line(surf, cor, (x, y - 16), (ex, ey), 3)
    pygame.draw.circle(surf, escuro, (x, y - 16), 15, 4)
    pygame.draw.circle(surf, cor, (x, y - 16), 15, 2)
    pygame.draw.circle(surf, (230, 230, 235), (x, y - 16), 3)
    if not girada and (tempo_ms // 500) % 2 == 0:
        pygame.draw.circle(surf, (255, 90, 70), (x + 18, y - 28), 3)


def desenhar_disjuntor(surf, pos, ligado, tempo_ms=0):
    x, y = pos
    caixa = pygame.Rect(x - 14, y - 22, 28, 44)
    pygame.draw.rect(surf, (66, 29, 0), caixa.inflate(4, 4), border_radius=3)
    pygame.draw.rect(surf, (88, 94, 106), caixa, border_radius=3)
    pygame.draw.rect(surf, (60, 64, 74), caixa.inflate(-8, -8), border_radius=2)
    for py in (caixa.y + 4, caixa.bottom - 5):
        pygame.draw.circle(surf, (150, 150, 158), (caixa.x + 3, py), 1)
        pygame.draw.circle(surf, (150, 150, 158), (caixa.right - 4, py), 1)
    pygame.draw.rect(surf, (53, 31, 0), (x - 5, y - 12, 10, 24))
    ponta = y - 10 if ligado else y + 4
    pygame.draw.rect(surf, (225, 225, 230) if ligado else (150, 150, 158), (x - 4, ponta, 8, 8))
    pygame.draw.rect(surf, (53, 31, 0), (x - 4, ponta, 8, 8), 1)
    cor = (60, 235, 120) if ligado else ((235, 70, 60) if (tempo_ms // 600) % 2 == 0 else (110, 35, 32))
    pygame.draw.circle(surf, cor, (x, y - 17), 3)


def desenhar_cofre(surf, rect, aberto, fonte=None):
    pygame.draw.rect(surf, (66, 29, 0), rect, border_radius=5)
    corpo = rect.inflate(-6, -6)
    pygame.draw.rect(surf, (88, 92, 104), corpo, border_radius=4)
    porta = corpo.inflate(-14, -14)
    if aberto:
        pygame.draw.rect(surf, (53, 31, 0), porta, border_radius=3)
        pygame.draw.polygon(surf, (120, 126, 140),
                            [(porta.x, porta.y), (porta.x - 14, porta.y + 8),
                             (porta.x - 14, porta.bottom - 4), (porta.x, porta.bottom)])
        pygame.draw.circle(surf, (60, 235, 120), (corpo.right - 8, corpo.y + 8), 4)
    else:
        pygame.draw.rect(surf, (112, 118, 132), porta, border_radius=3)
        pygame.draw.rect(surf, (60, 64, 74), porta, 2, border_radius=3)
        c = porta.center
        pygame.draw.circle(surf, (45, 48, 58), c, 15)
        pygame.draw.circle(surf, (200, 160, 50), c, 12)
        pygame.draw.circle(surf, (120, 95, 25), c, 12, 2)
        for k in range(8):
            a = k * math.pi / 4
            pygame.draw.line(surf, (60, 45, 15), c, (c[0] + math.cos(a) * 11, c[1] + math.sin(a) * 11), 1)
        pygame.draw.rect(surf, (45, 48, 58), (porta.right - 8, porta.centery - 10, 5, 20))
        pygame.draw.circle(surf, (235, 70, 60), (corpo.right - 8, corpo.y + 8), 4)
    rotulo = "ABERTO" if aberto else "COFRE"
    if fonte is not None:
        txt = fonte.render(rotulo, True, (230, 230, 235))
        surf.blit(txt, txt.get_rect(midtop=(rect.centerx, rect.bottom + 4)))


def desenhar_reparo(surf, pos, consertado, tempo_ms=0):
    """Cano/vazamento do puzzle do fuzil (3 golpes)."""
    x, y = pos
    pygame.draw.rect(surf, (66, 29, 0), (x - 24, y - 10, 48, 20), border_radius=4)
    pygame.draw.rect(surf, (100, 106, 118), (x - 22, y - 8, 44, 16), border_radius=3)
    pygame.draw.rect(surf, (140, 146, 158), (x - 22, y - 8, 44, 4), border_radius=3)
    for bx in (x - 18, x + 18):
        pygame.draw.circle(surf, (50, 54, 62), (bx, y), 4)
        pygame.draw.circle(surf, (170, 174, 184), (bx, y), 2)
    if consertado:
        pygame.draw.rect(surf, (70, 190, 110), (x - 8, y - 9, 16, 18), border_radius=2)
        pygame.draw.rect(surf, (25, 80, 45), (x - 8, y - 9, 16, 18), 2, border_radius=2)
        pygame.draw.line(surf, (200, 255, 215), (x - 5, y - 4), (x + 4, y - 4))
    else:
        pygame.draw.line(surf, (53, 31, 0), (x - 6, y - 8), (x + 2, y), 2)
        pygame.draw.line(surf, (53, 31, 0), (x + 2, y), (x - 3, y + 8), 2)
        ferrugem = [(x - 12, y - 6, 5, 4), (x + 8, y + 2, 6, 4), (x - 2, y + 4, 4, 3)]
        for r in ferrugem:
            pygame.draw.rect(surf, (140, 80, 40), r)
        for i in range(3):
            fase = ((tempo_ms // 90) + i * 3) % 9
            pygame.draw.circle(surf, (200, 220, 215), (x - 2 + i * 3, y - 12 - fase * 2), 2 + fase // 4)


def desenhar_fonte_som(surf, pos, real, tempo_ms):
    x, y = pos
    pygame.draw.rect(surf, (66, 29, 0), (x - 12, y - 10, 24, 20), border_radius=3)
    pygame.draw.rect(surf, (80, 84, 96), (x - 10, y - 8, 20, 16), border_radius=2)
    cor = (170, 170, 255) if real else ((200, 60, 220) if (tempo_ms // 180) % 2 == 0 else (90, 20, 110))
    pygame.draw.circle(surf, cor, (x, y), 5)


# ---------------------------------------------------------------------------
# Mapa: chão, paredes, portas
# ---------------------------------------------------------------------------
def _pintar_chao(surf, cor, semente):
    rng = random.Random(semente)
    w, h = surf.get_size()
    r0, g0, b0 = cor
    for ty in range(0, h, 40):
        for tx in range(0, w, 40):
            d = rng.randint(-4, 4)
            c = (max(0, min(255, r0 + d)), max(0, min(255, g0 + d)), max(0, min(255, b0 + d)))
            pygame.draw.rect(surf, c, (tx, ty, 40, 40))
            escuro = (max(0, r0 - 8), max(0, g0 - 8), max(0, b0 - 8))
            pygame.draw.line(surf, escuro, (tx, ty), (tx + 39, ty))
            pygame.draw.line(surf, escuro, (tx, ty), (tx, ty + 39))
            claro = (min(255, r0 + 6), min(255, g0 + 6), min(255, b0 + 6))
            pygame.draw.line(surf, claro, (tx + 1, ty + 1), (tx + 38, ty + 1))
    for _ in range((w * h) // 2500):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        d = rng.randint(-10, -4)
        surf.fill((max(0, r0 + d), max(0, g0 + d), max(0, b0 + d)), (x, y, rng.randint(2, 6), rng.randint(1, 3)))
    for _ in range((w * h) // 60000 + 2):
        x, y = rng.randint(40, w - 40), rng.randint(40, h - 40)
        mancha = _px(50, 30)
        pygame.draw.ellipse(mancha, (0, 0, 0, 28), (0, 0, 50, 30))
        surf.blit(mancha, (x, y))


def _pintar_parede(surf, r):
    clip_antigo = surf.get_clip()
    surf.set_clip(r)
    pygame.draw.rect(surf, (46, 51, 62), r)
    linha, junta = (30, 34, 44), (36, 41, 51)
    linhas = 0
    for y in range(r.y, r.bottom, 20):
        pygame.draw.line(surf, linha, (r.x, y), (r.right, y))
        desloc = 20 if linhas % 2 else 0
        for x in range(r.x + desloc, r.right, 40):
            pygame.draw.line(surf, junta, (x, y), (x, min(y + 20, r.bottom)))
        linhas += 1
    pygame.draw.line(surf, (70, 77, 92), (r.x, r.y), (r.right, r.y), 2)
    pygame.draw.line(surf, (22, 25, 33), (r.x, r.bottom - 1), (r.right, r.bottom - 1), 2)
    pygame.draw.line(surf, (22, 25, 33), (r.right - 1, r.y), (r.right - 1, r.bottom), 2)
    surf.set_clip(clip_antigo)
    pygame.draw.rect(surf, (28, 32, 42), r, 2)


def fundo_sala(sala):
    """Chão ladrilhado + paredes de tijolo/metal pré-renderizados (uma vez por sala)."""
    import mapas
    if getattr(sala, "tema", None) in mapas.TEMAS:
        return mapas.fundo_tema(sala, sala.tema)
    surf = pygame.Surface((sala.largura, sala.altura))
    _pintar_chao(surf, sala.cor_fundo, sala.largura * 31 + sala.altura)
    for parede in sala.paredes:
        _pintar_parede(surf, parede)
    return surf


def desenhar_porta(surf, rect, aberta, tempo_ms=0):
    pygame.draw.rect(surf, (53, 31, 0), rect.inflate(6, 6))
    if aberta:
        pygame.draw.rect(surf, (53, 31, 0), rect)
        brilho = 55 + int(25 * math.sin(tempo_ms / 300))
        halo = _px(rect.width, rect.height)
        halo.fill((60, 230, 130, brilho))
        surf.blit(halo, rect.topleft)
        cx, cy = rect.center
        pygame.draw.polygon(surf, (110, 255, 170), [(cx - 6, cy - 8), (cx + 6, cy), (cx - 6, cy + 8)])
        pygame.draw.rect(surf, (40, 150, 80), rect, 3)
    else:
        pygame.draw.rect(surf, (120, 36, 36), rect)
        pygame.draw.rect(surf, (150, 48, 48), rect.inflate(-8, -8))
        for y in range(rect.y + 8, rect.bottom - 6, 16):
            pygame.draw.line(surf, (95, 28, 28), (rect.x + 4, y), (rect.right - 5, y), 2)
        pygame.draw.rect(surf, (200, 160, 50), (rect.centerx - 5, rect.centery - 5, 10, 10), border_radius=2)
        pygame.draw.circle(surf, (66, 29, 0), rect.center, 2)
        cor = (255, 80, 60) if (tempo_ms // 500) % 2 == 0 else (110, 30, 25)
        pygame.draw.circle(surf, cor, (rect.centerx, rect.y + 7), 3)
        pygame.draw.rect(surf, (60, 16, 16), rect, 3)

_ROXO, _ROXO_CLARO = (22, 12, 34), (95, 48, 140)


def _vulto_img(quadro):
    chave = ("vulto", quadro)
    img = _arte.get(chave)
    if img is not None:
        return img
    s = _px(35, 48)
    pts = [(17, 2), (24, 9), (28, 24), (31, 44)]
    for i in range(8):
        x = 31 - i * 4
        y = 44 + (2 if (i + quadro) % 2 else -1)
        pts.append((x, y))
    pts += [(3, 30), (6, 9)]
    pygame.draw.polygon(s, _ROXO, pts)
    pygame.draw.polygon(s, _ROXO_CLARO, pts, 1)
    pygame.draw.ellipse(s, (4, 2, 8), (11, 7, 13, 14))
    for lado in (-1, 1):
        base = (17 + lado * 9, 24)
        ponta = (17 + lado * 15, 34 + (quadro % 2) * 2)
        pygame.draw.line(s, _ROXO_CLARO, base, ponta, 2)
        for d in (-2, 0, 2):
            pygame.draw.line(s, _ROXO_CLARO, ponta, (ponta[0] + lado * 2 + d, ponta[1] + 4))
    img = _x(s, 2)
    _arte[chave] = img
    return img


class VultoSprite(Inimigo):
    """Mesmo comportamento do Inimigo; só o desenho muda (vulto encapuzado com garras)."""

    def desenhar_corpo(self, surf, tempo_ms):
        prog = self.progresso_surgimento(tempo_ms)
        if prog <= 0:
            return
        rect = self.get_rect()
        a = int(255 * prog)
        flutua = int(3 * math.sin(tempo_ms / 260 + self.semente))
        quadro = int(tempo_ms / 220 + self.semente) % 4
        aura = _px(100, 110)
        pygame.draw.ellipse(aura, (120, 60, 180, a // 7), (0, 10, 100, 100))
        surf.blit(aura, (rect.centerx - 50, rect.bottom - 100 + flutua))
        img = _vulto_img(quadro)
        img.set_alpha(int(a * 0.95))
        surf.blit(img, (rect.centerx - 35, rect.bottom - 92 + flutua))

    def desenhar_olhos(self, surf, tempo_ms):
        prog = self.progresso_surgimento(tempo_ms)
        if prog <= 0:
            return
        a = int(255 * prog)
        rect = self.get_rect()
        atacando = tempo_ms - self.ultimo_ataque < 250
        cor = VERMELHO_ALARME if atacando else (200, 120, 255)
        pulso = 3 + int(1.5 * math.sin(tempo_ms / 120 + self.semente))
        flutua = int(3 * math.sin(tempo_ms / 260 + self.semente))
        brilho = _px(70, 30)
        for ox in (-8, 8):
            pygame.draw.circle(brilho, (*cor, a // 4), (35 + ox, 15), pulso + 6)
            pygame.draw.circle(brilho, (*cor, a), (35 + ox, 15), pulso)
        surf.blit(brilho, (rect.centerx - 35, rect.bottom - 92 + 15 + flutua))

    def desenhar(self, surf, tempo_ms):
        self.desenhar_corpo(surf, tempo_ms)
        self.desenhar_olhos(surf, tempo_ms)


def _guarda_png(direcao, tipo):
    chave = ("guarda_png", direcao, tipo)
    if chave in _arte:
        return _arte[chave]
    img = None
    for base in (_AQUI, os.path.join(_AQUI, "..")):
        caminho = os.path.normpath(os.path.join(base, "assets", "sprites", "inimigos", f"guarda_{tipo}_{direcao}.png"))
        if os.path.exists(caminho):
            img = pygame.image.load(caminho).convert_alpha()
            break
    if img is not None:
        h = 66
        img = pygame.transform.scale(img, (max(1, img.get_width() * h // img.get_height()), h))
    _arte[chave] = img
    return img


def _guarda_img(direcao, passo, uniforme=(58, 70, 108), atacando=False):
    return _guarda_img_codigo(direcao, passo, uniforme, atacando)
    tipo = "prisao"
    chave = None
    base = None
    img = base
    if passo:                                      
        img = pygame.transform.scale(base, (base.get_width(), base.get_height() - 2))
        fundo = _px(base.get_width(), base.get_height())
        fundo.blit(img, (0, 2))
        img = fundo
    if atacando:
        img = img.copy()
        img.fill((90, 0, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
    _arte[chave] = img
    return img


def _guarda_img_codigo(direcao, passo, uniforme=(58, 70, 108), atacando=False):
    """Guarda em pixel art (24x28 nativo, ampliado 2x). direcao: frente/costas/direita/esquerda."""
    chave = ("guarda_codigo", direcao, passo, uniforme, atacando)
    img = _arte.get(chave)
    if img is not None:
        return img
    lado = "direita" if direcao == "esquerda" else direcao
    s = _px(24, 28)
    esc = tuple(max(0, c - 28) for c in uniforme)
    pele, bota, cinto = (205, 175, 145), (28, 28, 34), (30, 34, 50)
    cap, visor = (30, 36, 60), (18, 22, 38)
    b = 1 if passo else 0

    if lado in ("frente", "costas"):
        pygame.draw.rect(s, bota, (7, 24 + b, 4, 3))
        pygame.draw.rect(s, bota, (13, 25 - b, 4, 3))
        pygame.draw.rect(s, esc, (7, 20, 4, 5 + b))
        pygame.draw.rect(s, esc, (13, 20, 4, 5 - b))
        pygame.draw.rect(s, uniforme, (6, 13, 12, 8))
        pygame.draw.rect(s, cinto, (6, 19, 12, 2))
        pygame.draw.rect(s, uniforme, (3, 14, 3, 7))
        pygame.draw.rect(s, uniforme, (18, 14, 3, 7))
        pygame.draw.rect(s, pele, (3, 20, 3, 2))
        pygame.draw.rect(s, pele, (18, 20, 3, 2))
        pygame.draw.rect(s, (255, 235, 140), (21, 19, 2, 3))
        pygame.draw.rect(s, pele, (8, 5, 8, 8))
        pygame.draw.rect(s, cap, (7, 3, 10, 4))
        if lado == "frente":
            pygame.draw.rect(s, visor, (8, 6, 8, 1))
            ol = (255, 80, 70) if atacando else (30, 30, 40)
            pygame.draw.rect(s, ol, (9, 9, 2, 2))
            pygame.draw.rect(s, ol, (13, 9, 2, 2))
            pygame.draw.rect(s, (255, 210, 80), (14, 15, 2, 2))
        else:
            pygame.draw.rect(s, cap, (8, 5, 8, 7))
    else:
        pygame.draw.rect(s, bota, (9 + b, 24, 5, 3))
        pygame.draw.rect(s, bota, (10 - b, 25, 5, 3))
        pygame.draw.rect(s, esc, (10 + b, 20, 4, 5))
        pygame.draw.rect(s, esc, (10 - b, 20, 4, 5))
        pygame.draw.rect(s, uniforme, (8, 13, 8, 8))
        pygame.draw.rect(s, cinto, (8, 19, 8, 2))
        pygame.draw.rect(s, esc, (6, 14, 3, 6))
        pygame.draw.rect(s, uniforme, (13, 15, 7, 3))
        pygame.draw.rect(s, pele, (19, 15, 2, 3))
        pygame.draw.rect(s, (255, 235, 140), (21, 14, 2, 4))
        pygame.draw.rect(s, pele, (9, 5, 8, 8))
        pygame.draw.rect(s, cap, (8, 3, 9, 4))
        pygame.draw.rect(s, visor, (14, 6, 5, 1))
        pygame.draw.rect(s, (255, 80, 70) if atacando else (30, 30, 40), (14, 9, 2, 2))
    img = _x(s, 2)
    if direcao == "esquerda":
        img = pygame.transform.flip(img, True, False)
    _arte[chave] = img
    return img


class GuardaSprite(Inimigo):
    """Guarda perseguidor (Sala 11): mesmo comportamento do Inimigo, sprite de guarda."""

    def desenhar(self, surf, tempo_ms):
        prog = self.progresso_surgimento(tempo_ms)
        if prog <= 0:
            return
        x_ant = getattr(self, "_x_ant", self.x)
        y_ant = getattr(self, "_y_ant", self.y)
        dx, dy = self.x - x_ant, self.y - y_ant
        self._x_ant, self._y_ant = self.x, self.y
        if abs(dx) > 0.2 or abs(dy) > 0.2:
            if abs(dx) >= abs(dy):
                self._dir = "direita" if dx > 0 else "esquerda"
            else:
                self._dir = "frente" if dy > 0 else "costas"
        direcao = getattr(self, "_dir", "frente")
        atacando = tempo_ms - self.ultimo_ataque < 250
        img = _guarda_img(direcao, (tempo_ms // 170) % 2, uniforme=(96, 52, 52), atacando=atacando)
        rect = self.get_rect()
        sombra = _px(48, 12)
        pygame.draw.ellipse(sombra, (0, 0, 0, 90), (0, 0, 48, 12))
        surf.blit(sombra, sombra.get_rect(center=(rect.centerx, rect.bottom - 2)))
        img.set_alpha(int(255 * prog))
        surf.blit(img, img.get_rect(midbottom=(rect.centerx, rect.bottom + 2)))


class GuardaPrisaoSprite(GuardaPrisao):
    """Guarda da prisão (Sala 8) com sprite de 4 lados; cone de visão e barra de suspeita iguais."""

    def _direcao_visual(self):
        a = self.angulo % 360
        if a < 45 or a >= 315:
            return "direita"
        if a < 135:
            return "frente"
        if a < 225:
            return "esquerda"
        return "costas"

    def desenhar(self, surf_base, cone_surf, jogador):
        tempo_ms = pygame.time.get_ticks()
        cx, cy = int(self.x), int(self.y)

        if abs(jogador.get_rect().centerx - cx) < 900:
            if self.viu or self.suspeita >= 0.7:
                cor_cone = (255, 50, 50, 80)
            elif self.suspeita > 0.15 or self.estado == "investigando":
                cor_cone = (255, 170, 40, 65)
            else:
                cor_cone = (255, 255, 120, 45)
            pygame.draw.polygon(cone_surf, cor_cone, self._pontos_do_cone())

        parado = self.estado == "posto" or (self.estado == "patrulha" and tempo_ms < self.espera_ate)
        passo = 0 if parado else (tempo_ms // 220) % 2
        img = _guarda_img(self._direcao_visual(), passo, atacando=self.suspeita >= 0.7)
        sombra = _px(48, 12)
        pygame.draw.ellipse(sombra, (0, 0, 0, 90), (0, 0, 48, 12))
        surf_base.blit(sombra, sombra.get_rect(center=(cx, cy + 24)))
        surf_base.blit(img, img.get_rect(midbottom=(cx, cy + 28)))

        if self.suspeita > 0.04:
            if GuardaPrisao._fonte is None:
                GuardaPrisao._fonte = pygame.font.SysFont(None, 30, bold=True)
            largura = 44
            barra = pygame.Rect(cx - largura // 2, cy - 48, largura, 6)
            pygame.draw.rect(surf_base, (30, 30, 35), barra)
            cor = (255, 70, 60) if self.suspeita >= 0.7 else (255, 200, 60)
            pygame.draw.rect(surf_base, cor, (barra.x, barra.y, int(largura * self.suspeita), 6))
            pygame.draw.rect(surf_base, (210, 210, 210), barra, width=1)
            marca = GuardaPrisao._fonte.render("!" if self.suspeita >= 0.7 else "?", True, cor)
            surf_base.blit(marca, marca.get_rect(midbottom=(cx, cy - 50)))
        elif self.estado == "investigando":
            if GuardaPrisao._fonte is None:
                GuardaPrisao._fonte = pygame.font.SysFont(None, 30, bold=True)
            marca = GuardaPrisao._fonte.render("?", True, (255, 200, 60))
            surf_base.blit(marca, marca.get_rect(midbottom=(cx, cy - 34)))
