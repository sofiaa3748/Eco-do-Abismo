import math
import os
import random

import pygame

W, H = 800, 600
BAIXA = (200, 150)          # arte em baixa resolução, ampliada 4x (pixel art)


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _poco(cor_anel, cor_fundo, centro, rng, olhos=False):
    s = pygame.Surface(BAIXA)
    for y in range(BAIXA[1]):
        t = y / BAIXA[1]
        s.fill(_mix(cor_fundo[0], cor_fundo[1], t), (0, y, BAIXA[0], 1))
    cx, cy = centro
    # paredes do poço: anéis de perspectiva
    for k in range(16):
        f = 0.80 ** k
        rx, ry = int(118 * f), int(58 * f)
        brilho = (k / 15) ** 1.4
        cor = _mix(_mix(cor_anel, (0, 0, 0), 0.65), cor_anel, brilho)
        pygame.draw.ellipse(s, cor, (cx - rx, cy - ry + int(k * 1.2), rx * 2, ry * 2), 1 if k > 1 else 2)
        if k % 2 == 0:
            for a in range(0, 360, 30):
                ang = math.radians(a + k * 9)
                x = cx + int(math.cos(ang) * rx)
                y = cy + int(math.sin(ang) * ry) - ry + ry + int(k * 1.2) - ry + ry
                if 0 <= x < BAIXA[0] and 0 <= y < BAIXA[1]:
                    s.set_at((x, y), _mix(cor, (255, 255, 255), 0.15))
    # fundo escuro do poço
    pygame.draw.ellipse(s, (2, 3, 8), (cx - 6, cy + 12, 12, 6))
    # reflexos de eco: arcos que sobem
    for k in range(4):
        r = 14 + k * 12
        pygame.draw.arc(s, _mix(cor_anel, (0, 0, 0), 0.5 + k * 0.12), (cx - r, cy + 10 - r // 2, r * 2, r), math.pi * 1.1, math.pi * 1.9, 1)
    # partículas
    for _ in range(70):
        x, y = rng.randint(0, BAIXA[0] - 1), rng.randint(0, BAIXA[1] - 1)
        s.set_at((x, y), _mix(cor_fundo[0], cor_anel, rng.uniform(0.2, 0.9)))
    if olhos:
        for _ in range(26):
            x, y = rng.randint(6, BAIXA[0] - 8), rng.randint(4, 70)
            if abs(x - cx) < 20 and y > 40:
                continue
            c = (230, 40, 40) if rng.random() < 0.8 else (255, 140, 60)
            s.set_at((x, y), c)
            s.set_at((x + 3, y), c)
    return pygame.transform.scale(s, (W, H))


def _carregar_operario(caminho, altura):
    img = pygame.image.load(caminho).convert_alpha()
    img = img.subsurface(img.get_bounding_rect()).copy()
    return pygame.transform.scale(img, (img.get_width() * altura // img.get_height(), altura))


def _vinheta(img, forca=0.85):
    v = pygame.Surface((W, H), pygame.SRCALPHA)
    for r in range(0, 360, 6):
        a = int(255 * forca * (r / 360) ** 2.2)
        pygame.draw.ellipse(v, (0, 0, 0, min(255, a)), (-r, -r + 0, W + 2 * r, H + 2 * r), 8)
    img.blit(v, (0, 0))


def _plataforma(img, x0, y, largura, cor):
    pygame.draw.rect(img, _mix(cor, (0, 0, 0), 0.6), (x0, y, largura, H - y))
    pygame.draw.rect(img, cor, (x0, y, largura, 8))
    pygame.draw.rect(img, _mix(cor, (255, 255, 255), 0.18), (x0, y, largura, 2))
    rng = random.Random(4)
    for _ in range(40):
        px, py = rng.randint(x0, x0 + largura - 4), rng.randint(y + 10, H - 4)
        pygame.draw.rect(img, _mix(cor, (0, 0, 0), 0.8), (px, py, rng.randint(6, 18), 3))


def _brilho(img, pos, raio, cor, forca=90):
    halo = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
    for r in range(raio, 0, -4):
        pygame.draw.circle(halo, (*cor, int(forca * (1 - r / raio) ** 2)), (raio, raio), r)
    img.blit(halo, (pos[0] - raio, pos[1] - raio))


def _fundo_simples(topo, base, brilho, cor_brilho):
    img = pygame.Surface((W, H))
    for y in range(H):
        img.fill(_mix(topo, base, y / H), (0, y, W, 1))
    _brilho(img, (W // 2, H // 2), 260, cor_brilho, brilho)
    return img


def tela_inicial(pasta_sprites, saida):
    img = _fundo_simples((8, 12, 28), (2, 4, 10), 55, (0, 190, 230))
    op = _carregar_operario(os.path.join(pasta_sprites, "..", "base", "frente.png"), 104)
    sombra = pygame.Surface((90, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (0, 0, 0, 120), (0, 0, 90, 14))
    img.blit(sombra, sombra.get_rect(center=(W // 2, 352)))
    img.blit(op, (W // 2 - op.get_width() // 2, 250))
    _vinheta(img, 0.7)
    pygame.image.save(img, saida)


def game_over(pasta_sprites, saida):
    img = _fundo_simples((18, 4, 8), (4, 0, 2), 45, (200, 30, 40))
    op = _carregar_operario(os.path.join(pasta_sprites, "dano_3.png"), 180)
    op = pygame.transform.rotate(op, 90)
    sombra = pygame.Surface((220, 22), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (0, 0, 0, 130), (0, 0, 220, 22))
    img.blit(sombra, sombra.get_rect(center=(W // 2, 372)))
    img.blit(op, (W // 2 - op.get_width() // 2, 372 - op.get_height() + 6))
    _vinheta(img, 0.7)
    pygame.image.save(img, saida)


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((1, 1))
    base = os.path.dirname(os.path.abspath(__file__))
    spr = os.path.join(base, "assets", "sprites", "operario")
    pasta = os.path.join(base, "assets", "telas")
    os.makedirs(pasta, exist_ok=True)
    tela_inicial(spr, os.path.join(pasta, "tela_inicial.png"))
    game_over(spr, os.path.join(pasta, "game_over.png"))
    print("Telas geradas em", pasta)
