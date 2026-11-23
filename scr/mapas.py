import math
import random

import pygame

TEMA_POR_NIVEL = {
    1: "dormitorio", 2: "deposito", 3: "escritorio", 4: "corredor", "4B": "duto", 5: "manutencao", 6: "abandonado",
    7: "hospital", 8: "prisao", 9: "geradores", 10: "patio", 11: "seguranca", 12: "biblioteca",
}

def _mix(a, b, t):
    return tuple(max(0, min(255, int(a[i] + (b[i] - a[i]) * t))) for i in range(3))


def _esc(c, k=0.78):
    return tuple(int(v * k) for v in c)


def _luz(c, k=1.18):
    return tuple(min(255, int(v * k + 4)) for v in c)


def _alfa(w, h):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def _sujeira(surf, rng, cor, dens=2500, escuro=(-12, -4), tam=(2, 7)):
    w, h = surf.get_size()
    for _ in range((w * h) // dens):
        x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
        d = rng.randint(*escuro)
        surf.fill(_mix(cor, (0, 0, 0) if d < 0 else (255, 255, 255), abs(d) / 100),
                  (x, y, rng.randint(*tam), rng.randint(1, 3)))


def _manchas(surf, rng, n, cor, alfa=34, rx=(20, 60), ry=(10, 30)):
    w, h = surf.get_size()
    for _ in range(n):
        a, b = rng.randint(*rx), rng.randint(*ry)
        m = _alfa(a * 2, b * 2)
        pygame.draw.ellipse(m, (*cor, alfa), (0, 0, a * 2, b * 2))
        surf.blit(m, (rng.randint(40, w - 40 - a), rng.randint(40, h - 40 - b)))


def _rachaduras(surf, rng, n, cor, comp=(60, 160)):
    w, h = surf.get_size()
    for _ in range(n):
        x, y = rng.randint(60, w - 60), rng.randint(60, h - 60)
        ang = rng.uniform(0, 6.28)
        for _ in range(rng.randint(*comp) // 8):
            nx, ny = x + math.cos(ang) * 8, y + math.sin(ang) * 8
            pygame.draw.line(surf, cor, (x, y), (nx, ny), 1)
            if rng.random() < 0.18:
                pygame.draw.line(surf, cor, (nx, ny), (nx + math.cos(ang + 1) * 10, ny + math.sin(ang + 1) * 10), 1)
            x, y, ang = nx, ny, ang + rng.uniform(-0.6, 0.6)

def _piso_xadrez(surf, rng, c1, c2, junta, t=40):
    w, h = surf.get_size()
    for ty in range(0, h, t):
        for tx in range(0, w, t):
            pygame.draw.rect(surf, c1 if (tx // t + ty // t) % 2 == 0 else c2, (tx, ty, t, t))
    for x in range(0, w, t):
        pygame.draw.line(surf, junta, (x, 0), (x, h))
    for y in range(0, h, t):
        pygame.draw.line(surf, junta, (0, y), (w, y))


def _piso_concreto(surf, rng, base, lajes=80):
    w, h = surf.get_size()
    surf.fill(base)
    for ty in range(0, h, lajes):
        for tx in range(0, w, lajes):
            d = rng.randint(-5, 5)
            pygame.draw.rect(surf, _mix(base, (255, 255, 255) if d > 0 else (0, 0, 0), abs(d) / 100), (tx, ty, lajes, lajes))
            pygame.draw.rect(surf, _esc(base, 0.82), (tx, ty, lajes, lajes), 1)


def _piso_grade(surf, rng, base):
    w, h = surf.get_size()
    surf.fill(base)
    escuro, claro = _esc(base, 0.6), _luz(base, 1.25)
    for y in range(0, h, 16):
        for x in range((y // 16 % 2) * 8, w, 16):
            pygame.draw.rect(surf, escuro, (x + 2, y + 2, 10, 4), border_radius=2)
            pygame.draw.line(surf, claro, (x + 2, y + 1), (x + 11, y + 1))
    for x in range(0, w, 80):
        pygame.draw.line(surf, _esc(base, 0.5), (x, 0), (x, h), 2)
    for y in range(0, h, 80):
        pygame.draw.line(surf, _esc(base, 0.5), (0, y), (w, y), 2)


def _piso_madeira(surf, rng, base, larg=22):
    w, h = surf.get_size()
    for y in range(0, h, larg):
        deslocamento = rng.randint(0, 120)
        x = -deslocamento
        while x < w:
            comp = rng.randint(120, 220)
            d = rng.randint(-6, 6)
            pygame.draw.rect(surf, _mix(base, (255, 255, 255) if d > 0 else (0, 0, 0), abs(d) / 100), (x, y, comp, larg))
            pygame.draw.rect(surf, _esc(base, 0.7), (x, y, comp, larg), 1)
            if rng.random() < 0.5:
                pygame.draw.line(surf, _esc(base, 0.85), (x + 8, y + larg // 2), (x + comp - 12, y + larg // 2))
            x += comp


def _piso_pedra(surf, rng, base):
    w, h = surf.get_size()
    surf.fill(base)
    y = 0
    while y < h:
        alt = rng.choice((40, 50, 60))
        x = -rng.randint(0, 80)
        while x < w:
            larg = rng.choice((60, 80, 100))
            d = rng.randint(-6, 6)
            pygame.draw.rect(surf, _mix(base, (255, 255, 255) if d > 0 else (0, 0, 0), abs(d) / 100), (x, y, larg, alt))
            pygame.draw.rect(surf, _esc(base, 0.7), (x, y, larg, alt), 2)
            pygame.draw.line(surf, _luz(base, 1.15), (x + 2, y + 2), (x + larg - 3, y + 2))
            x += larg
        y += alt


def _piso_carpete(surf, rng, base):
    surf.fill(base)
    w, h = surf.get_size()
    for y in range(0, h, 6):
        for x in range(((y // 6) % 2) * 3, w, 6):
            surf.set_at((x, y), _esc(base, 0.88))
    _sujeira(surf, rng, base, 4000, (-10, 6), (3, 9))


class _Clip:
    def __init__(self, surf, r):
        self.s, self.r = surf, r

    def __enter__(self):
        self.old = self.s.get_clip()
        self.s.set_clip(self.r)

    def __exit__(self, *a):
        self.s.set_clip(self.old)


def _parede_tijolo(surf, r, rng, base, junta, alt=20, larg=40):
    with _Clip(surf, r):
        pygame.draw.rect(surf, base, r)
        linhas = 0
        for y in range(r.y, r.bottom, alt):
            pygame.draw.line(surf, junta, (r.x, y), (r.right, y))
            for x in range(r.x + (larg // 2 if linhas % 2 else 0), r.right, larg):
                pygame.draw.line(surf, junta, (x, y), (x, y + alt))
                if rng.random() < 0.25:
                    pygame.draw.rect(surf, _mix(base, (0, 0, 0), 0.12), (x + 1, y + 1, larg - 2, alt - 2))
            linhas += 1
        pygame.draw.line(surf, _luz(base, 1.25), (r.x, r.y), (r.right, r.y), 2)
        pygame.draw.line(surf, _esc(base, 0.6), (r.x, r.bottom - 1), (r.right, r.bottom - 1), 2)
    pygame.draw.rect(surf, _esc(base, 0.6), r, 2)


def _parede_painel(surf, r, rng, base, rebite, larg=60):
    with _Clip(surf, r):
        pygame.draw.rect(surf, base, r)
        for x in range(r.x, r.right, larg):
            pygame.draw.line(surf, _esc(base, 0.65), (x, r.y), (x, r.bottom), 2)
            pygame.draw.line(surf, _luz(base, 1.2), (x + 2, r.y), (x + 2, r.bottom))
            for y in range(r.y + 6, r.bottom - 4, 22):
                pygame.draw.circle(surf, rebite, (x + 8, y), 2)
                pygame.draw.circle(surf, rebite, (x + larg - 8, y), 2)
        pygame.draw.line(surf, _luz(base, 1.3), (r.x, r.y), (r.right, r.y), 2)
        pygame.draw.line(surf, _esc(base, 0.5), (r.x, r.bottom - 1), (r.right, r.bottom - 1), 2)
    pygame.draw.rect(surf, _esc(base, 0.55), r, 2)


def _parede_pintada(surf, r, rng, base, rodape):
    with _Clip(surf, r):
        pygame.draw.rect(surf, base, r)
        for _ in range(max(2, r.width * r.height // 4000)):
            x, y = rng.randint(r.x, r.right), rng.randint(r.y, r.bottom)
            pygame.draw.rect(surf, _esc(base, 0.9), (x, y, rng.randint(6, 30), rng.randint(2, 12)))
        if r.height <= 60:
            pygame.draw.rect(surf, rodape, (r.x, r.bottom - 10, r.width, 10))
        pygame.draw.line(surf, _luz(base, 1.2), (r.x, r.y), (r.right, r.y), 2)
    pygame.draw.rect(surf, _esc(base, 0.6), r, 2)


def _parede_lambril(surf, r, rng, base):
    with _Clip(surf, r):
        pygame.draw.rect(surf, base, r)
        for x in range(r.x, r.right, 24):
            pygame.draw.line(surf, _esc(base, 0.75), (x, r.y), (x, r.bottom), 2)
            pygame.draw.line(surf, _luz(base, 1.15), (x + 3, r.y), (x + 3, r.bottom))
        pygame.draw.rect(surf, _esc(base, 0.65), (r.x, r.y + r.height // 2 - 2, r.width, 4))
    pygame.draw.rect(surf, _esc(base, 0.55), r, 2)


def _parede_azulejo(surf, r, rng, base, faixa):
    with _Clip(surf, r):
        pygame.draw.rect(surf, base, r)
        for x in range(r.x, r.right, 20):
            pygame.draw.line(surf, _esc(base, 0.82), (x, r.y), (x, r.bottom))
        for y in range(r.y, r.bottom, 20):
            pygame.draw.line(surf, _esc(base, 0.82), (r.x, y), (r.right, y))
        pygame.draw.rect(surf, faixa, (r.x, r.y + r.height // 2 - 3, r.width, 6))
        pygame.draw.line(surf, _luz(base, 1.25), (r.x, r.y), (r.right, r.y), 2)
    pygame.draw.rect(surf, _esc(base, 0.55), r, 2)


def _parede_cerca(surf, r, rng, base, arame):
    with _Clip(surf, r):
        pygame.draw.rect(surf, base, r)
        for x in range(r.x - r.height, r.right + r.height, 10):
            pygame.draw.line(surf, arame, (x, r.y), (x + r.height, r.bottom))
            pygame.draw.line(surf, arame, (x + r.height, r.y), (x, r.bottom))
        for x in range(r.x, r.right, 120):
            pygame.draw.rect(surf, _esc(base, 0.6), (x, r.y, 6, r.height))
        pygame.draw.line(surf, (60, 62, 66), (r.x, r.y + 5), (r.right, r.y + 5), 2)
        for x in range(r.x, r.right, 14):
            pygame.draw.line(surf, (60, 62, 66), (x, r.y + 2), (x + 5, r.y + 8))
    pygame.draw.rect(surf, _esc(base, 0.5), r, 2)


def _parede_estante(surf, r, rng, base):
    cores = [(120, 52, 48), (66, 92, 120), (110, 96, 50), (70, 110, 80), (96, 66, 110), (140, 100, 60), (80, 60, 50)]
    with _Clip(surf, r):
        pygame.draw.rect(surf, _esc(base, 0.7), r)
        horizontal = r.width >= r.height
        if horizontal:
            for niv in range(r.y + 2, r.bottom, max(14, r.height // 2)):
                x = r.x
                while x < r.right:
                    l = rng.randint(4, 8)
                    a = rng.randint(r.height // 2 - 8, r.height // 2 - 2)
                    c = rng.choice(cores)
                    pygame.draw.rect(surf, c, (x, niv + (max(14, r.height // 2) - 4 - a), l, a))
                    pygame.draw.line(surf, _esc(c, 0.7), (x, niv + 2), (x, niv + max(14, r.height // 2) - 4))
                    x += l + 1
                pygame.draw.rect(surf, base, (r.x, niv + max(14, r.height // 2) - 3, r.width, 3))
        else:
            for niv in range(r.x + 2, r.right, 14):
                y = r.y
                while y < r.bottom:
                    l = rng.randint(4, 8)
                    c = rng.choice(cores)
                    pygame.draw.rect(surf, c, (niv, y, 10, l))
                    y += l + 1
        pygame.draw.line(surf, _luz(base, 1.3), (r.x, r.y), (r.right, r.y), 2)
    pygame.draw.rect(surf, _esc(base, 0.45), r, 2)


def _parede_pedra(surf, r, rng, base):
    with _Clip(surf, r):
        pygame.draw.rect(surf, base, r)
        y = r.y
        while y < r.bottom:
            alt = rng.choice((18, 22, 26))
            x = r.x - rng.randint(0, 40)
            while x < r.right:
                larg = rng.choice((30, 40, 52))
                d = rng.randint(-7, 7)
                pygame.draw.rect(surf, _mix(base, (255, 255, 255) if d > 0 else (0, 0, 0), abs(d) / 100), (x, y, larg, alt))
                pygame.draw.rect(surf, _esc(base, 0.62), (x, y, larg, alt), 1)
                if rng.random() < 0.12:
                    pygame.draw.rect(surf, (52, 74, 52), (x + 2, y + alt - 6, larg - 4, 4))
                x += larg
            y += alt
    pygame.draw.rect(surf, _esc(base, 0.5), r, 2)


def _janela_grade(surf, x, y, w=60, h=26, luar=True):
    pygame.draw.rect(surf, (20, 28, 48), (x, y, w, h))
    if luar:
        pygame.draw.rect(surf, (60, 80, 120), (x + 2, y + 2, w - 4, h - 4))
        pygame.draw.rect(surf, (130, 160, 210), (x + 2, y + 2, w - 4, 3))
    for bx in range(x + 8, x + w - 4, 10):
        pygame.draw.rect(surf, (30, 32, 38), (bx, y, 3, h))
    pygame.draw.rect(surf, (36, 38, 46), (x, y, w, h), 2)


def _facho_janela(surf, x, y, w=60, comprimento=120, cor=(120, 150, 210), alfa=26):
    f = _alfa(w + 40, comprimento)
    pygame.draw.polygon(f, (*cor, alfa), [(10, 0), (w + 30, 0), (w + 36, comprimento), (0, comprimento)])
    surf.blit(f, (x - 18, y))


def _relogio(surf, x, y):
    pygame.draw.circle(surf, (36, 34, 36), (x, y), 12)
    pygame.draw.circle(surf, (200, 196, 180), (x, y), 10)
    pygame.draw.line(surf, (50, 40, 36), (x, y), (x, y - 7), 2)
    pygame.draw.line(surf, (50, 40, 36), (x, y), (x + 5, y + 2), 2)


def _cama(surf, x, y):
    pygame.draw.rect(surf, (52, 54, 62), (x, y, 120, 76), border_radius=4)
    pygame.draw.rect(surf, (96, 104, 112), (x + 6, y + 6, 108, 64), border_radius=3)
    pygame.draw.rect(surf, (150, 160, 166), (x + 10, y + 10, 30, 56), border_radius=6)
    pygame.draw.rect(surf, (78, 96, 104), (x + 44, y + 8, 66, 60), border_radius=3)
    pygame.draw.line(surf, (60, 76, 84), (x + 44, y + 34), (x + 108, y + 34), 2)
    pygame.draw.rect(surf, (34, 36, 42), (x, y, 120, 76), 3, border_radius=4)


def _prateleira_caixas(surf, rng, x, y, w):
    pygame.draw.rect(surf, (58, 62, 72), (x, y + 24, w, 8))
    cx = x + 4
    while cx < x + w - 24:
        cw, ch = rng.randint(14, 26), rng.randint(12, 22)
        pygame.draw.rect(surf, (138, 96, 56), (cx, y + 24 - ch, cw, ch))
        pygame.draw.rect(surf, (96, 64, 36), (cx, y + 24 - ch, cw, ch), 2)
        cx += cw + rng.randint(2, 8)


def _cano_horizontal(surf, x, y, w, cor=(96, 100, 108), esp=10):
    pygame.draw.rect(surf, _esc(cor, 0.6), (x, y, w, esp))
    pygame.draw.rect(surf, cor, (x, y + 1, w, esp - 4))
    pygame.draw.rect(surf, _luz(cor, 1.3), (x, y + 1, w, 2))
    for jx in range(x + 40, x + w - 10, 120):
        pygame.draw.rect(surf, _esc(cor, 0.7), (jx, y - 2, 8, esp + 4))
        pygame.draw.circle(surf, _luz(cor, 1.2), (jx + 4, y + esp // 2), 2)


def _valvula_parede(surf, x, y, cor=(190, 60, 52)):
    pygame.draw.rect(surf, (60, 64, 72), (x - 2, y + 8, 4, 8))
    pygame.draw.circle(surf, _esc(cor, 0.6), (x, y), 9, 3)
    pygame.draw.line(surf, cor, (x - 8, y), (x + 8, y), 2)
    pygame.draw.line(surf, cor, (x, y - 8), (x, y + 8), 2)


def _quadro(surf, x, y, w=26, h=20, rng=None):
    pygame.draw.rect(surf, (84, 56, 34), (x, y, w, h))
    pygame.draw.rect(surf, (150, 140, 110), (x + 3, y + 3, w - 6, h - 6))
    pygame.draw.polygon(surf, (90, 110, 90), [(x + 3, y + h - 3), (x + w // 2, y + 6), (x + w - 3, y + h - 3)])


def _venezianas(surf, x, y, w=70, h=28):
    pygame.draw.rect(surf, (40, 30, 24), (x, y, w, h))
    for yy in range(y + 3, y + h - 2, 5):
        pygame.draw.rect(surf, (168, 150, 112), (x + 3, yy, w - 6, 3))
    pygame.draw.rect(surf, (60, 44, 32), (x, y, w, h), 2)


def _papeis(surf, rng, n):
    w, h = surf.get_size()
    for _ in range(n):
        x, y = rng.randint(60, w - 90), rng.randint(60, h - 90)
        p = _alfa(22, 18)
        pygame.draw.rect(p, (214, 206, 184), (0, 0, 20, 16))
        pygame.draw.rect(p, (150, 140, 120), (0, 0, 20, 16), 1)
        for ly in (4, 8, 12):
            pygame.draw.line(p, (150, 140, 120), (3, ly), (16, ly))
        surf.blit(pygame.transform.rotate(p, rng.randint(-40, 40)), (x, y))


def _faixa_perigo(surf, r, vertical=False):
    with _Clip(surf, r):
        pygame.draw.rect(surf, (210, 170, 40), r)
        passo = 14
        rng_ = range(r.x - r.height, r.right + r.height, passo * 2) if not vertical else range(r.y - r.width, r.bottom + r.width, passo * 2)
        for k in rng_:
            if not vertical:
                pygame.draw.polygon(surf, (40, 36, 30), [(k, r.bottom), (k + passo, r.bottom), (k + passo + r.height, r.y), (k + r.height, r.y)])
            else:
                pygame.draw.polygon(surf, (40, 36, 30), [(r.x, k), (r.x, k + passo), (r.right, k + passo + r.width), (r.right, k + r.width)])


def _luz_emergencia_fixa(surf, x, y):
    pygame.draw.rect(surf, (40, 40, 46), (x - 8, y - 5, 16, 10), border_radius=3)
    pygame.draw.rect(surf, (200, 60, 50), (x - 5, y - 3, 10, 6), border_radius=2)


def _camera(surf, x, y, cor=(200, 60, 50)):
    pygame.draw.rect(surf, (52, 54, 62), (x - 10, y - 12, 20, 8))
    pygame.draw.polygon(surf, (82, 86, 98), [(x - 8, y - 6), (x + 8, y - 6), (x + 5, y + 6), (x - 5, y + 6)])
    pygame.draw.circle(surf, (20, 22, 28), (x, y + 6), 5)
    pygame.draw.circle(surf, cor, (x, y + 6), 2)


def _seta_chao(surf, x, y, cor=(214, 170, 50)):
    pygame.draw.polygon(surf, cor, [(x, y - 14), (x + 22, y), (x, y + 14), (x + 6, y)])
    pygame.draw.polygon(surf, _esc(cor, 0.6), [(x, y - 14), (x + 22, y), (x, y + 14), (x + 6, y)], 2)


def _tampa_esgoto(surf, x, y):
    pygame.draw.circle(surf, (36, 38, 42), (x, y), 26)
    pygame.draw.circle(surf, (70, 74, 80), (x, y), 23)
    for k in range(-3, 4):
        pygame.draw.line(surf, (40, 42, 48), (x - 20, y + k * 6), (x + 20, y + k * 6), 2)


def _bordas(sala):
    return sala.paredes[:4], sala.paredes[4:]


def _tema_dormitorio(surf, sala, rng):
    base = (70, 86, 84)
    _piso_xadrez(surf, rng, base, (64, 80, 78), (46, 58, 58))
    _sujeira(surf, rng, base, 2200)
    _manchas(surf, rng, 10, (20, 24, 24), 40)
    _rachaduras(surf, rng, 4, (40, 52, 52))
    w, h = sala.largura, sala.altura
    # cama onde o operário acordou, ao lado da porta de entrada
    _cama(surf, 46, sala.ponto_entrada[1] - 150)
    # marca de luar no chão
    for x in (260, 760, 1100):
        _facho_janela(surf, x, 40, 60, 150)
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_pintada(surf, r, rng, (92, 104, 102), (56, 66, 66))
    for r in obs:
        _parede_pintada(surf, r, rng, (100, 112, 110), (60, 70, 70))
    for x in (260, 760, 1100):
        _janela_grade(surf, x, 7, 60, 26)
    _relogio(surf, 520, 20)
    pygame.draw.rect(surf, (60, 66, 70), (900, 8, 50, 24))
    pygame.draw.rect(surf, (150, 40, 40), (922, 12, 6, 16))
    pygame.draw.rect(surf, (150, 40, 40), (914, 18, 22, 4))


def _tema_deposito(surf, sala, rng):
    base = (60, 60, 66)
    _piso_concreto(surf, rng, base, 80)
    _sujeira(surf, rng, base, 2000)
    _manchas(surf, rng, 14, (10, 10, 14), 50)
    _manchas(surf, rng, 6, (70, 50, 20), 38, (14, 30), (8, 18))
    _rachaduras(surf, rng, 6, (36, 36, 42))
    w, h = sala.largura, sala.altura
    for (x, y) in ((200, 560), (800, 180), (500, 380)):          # pallets de madeira
        for k in range(5):
            pygame.draw.rect(surf, (112, 80, 48), (x, y + k * 11, 90, 8))
            pygame.draw.rect(surf, (70, 48, 28), (x, y + k * 11, 90, 8), 1)
    _faixa_perigo(surf, pygame.Rect(40, h // 2 - 5, 90, 8))
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_painel(surf, r, rng, (72, 76, 88), (110, 114, 124))
    for r in obs:
        _parede_painel(surf, r, rng, (82, 86, 98), (120, 124, 134))
    for x in range(120, w - 220, 330):
        _prateleira_caixas(surf, rng, x, 8, 240)
    _cano_horizontal(surf, 60, h - 28, w - 120, (92, 96, 104), 8)


def _tema_escritorio(surf, sala, rng):
    base = (74, 50, 52)
    _piso_carpete(surf, rng, base)
    w, h = sala.largura, sala.altura
    tapete = pygame.Rect(w // 2 - 260, h // 2 - 150, 520, 300)
    pygame.draw.rect(surf, (96, 40, 44), tapete)
    pygame.draw.rect(surf, (140, 100, 60), tapete, 4)
    pygame.draw.rect(surf, (140, 100, 60), tapete.inflate(-28, -28), 2)
    _manchas(surf, rng, 8, (20, 10, 10), 40)
    _papeis(surf, rng, 28)
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_lambril(surf, r, rng, (98, 68, 44))
    for r in obs:
        _parede_lambril(surf, r, rng, (110, 78, 52))
    for x in (180, 520, 900):
        _venezianas(surf, x, 6, 70, 28)
        _facho_janela(surf, x, 40, 70, 110, (200, 170, 110), 18)
    for x in (360, 700, 1060):
        _quadro(surf, x, 9)
    for x in range(200, w - 200, 300):
        pygame.draw.rect(surf, (60, 66, 76), (x, h - 34, 40, 28))          # arquivos junto à parede de baixo
        pygame.draw.rect(surf, (36, 40, 48), (x, h - 34, 40, 28), 2)
        for yy in (h - 28, h - 20):
            pygame.draw.rect(surf, (140, 144, 152), (x + 14, yy, 12, 3))


def _tema_corredor(surf, sala, rng):
    base = (46, 50, 58)
    _piso_grade(surf, rng, base)
    w, h = sala.largura, sala.altura
    _faixa_perigo(surf, pygame.Rect(40, 40, w - 80, 8))
    _faixa_perigo(surf, pygame.Rect(40, h - 48, w - 80, 8))
    _manchas(surf, rng, 8, (10, 10, 14), 50)
    for x in range(200, w - 200, 400):
        _tampa_esgoto(surf, x, h // 2 + 120)
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_painel(surf, r, rng, (60, 66, 78), (108, 112, 122))
    for r in obs:
        _parede_painel(surf, r, rng, (70, 76, 88), (116, 120, 130))
    _cano_horizontal(surf, 60, 12, w - 120, (96, 100, 110), 9)
    for x in range(260, w - 200, 380):
        _luz_emergencia_fixa(surf, x, 26)
    pygame.draw.rect(surf, (40, 120, 70), (w - 220, h - 36, 70, 24))
    pygame.draw.rect(surf, (200, 240, 210), (w - 214, h - 30, 58, 12))


def _tema_duto(surf, sala, rng):
    base = (58, 62, 72)
    _piso_grade(surf, rng, base)
    _manchas(surf, rng, 10, (14, 14, 18), 40)
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_painel(surf, r, rng, (50, 54, 64), (100, 104, 116))
    for r in obs:
        _parede_painel(surf, r, rng, (74, 78, 90), (120, 124, 136))
        # nervuras metálicas do duto
        for x in range(r.x + 40, r.right - 20, 70):
            pygame.draw.rect(surf, (52, 56, 66), (x, r.y, 4, r.height))


def _tema_manutencao(surf, sala, rng):
    base = (74, 60, 46)
    _piso_grade(surf, rng, base)
    _manchas(surf, rng, 10, (30, 110, 60), 46, (26, 60), (14, 34))
    _manchas(surf, rng, 8, (20, 12, 8), 50)
    w, h = sala.largura, sala.altura
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_painel(surf, r, rng, (62, 54, 48), (130, 100, 70), 50)
    for r in obs:
        _parede_painel(surf, r, rng, (78, 68, 60), (130, 100, 70), 50)
    _cano_horizontal(surf, 50, 8, w - 100, (130, 88, 56), 11)
    _cano_horizontal(surf, 50, 24, w - 100, (96, 104, 112), 8)
    _cano_horizontal(surf, 50, h - 30, w - 100, (110, 80, 56), 10)
    for x in range(180, w - 150, 260):
        _valvula_parede(surf, x, 18, (196, 70, 60))
    pygame.draw.rect(surf, (210, 170, 40), (w - 300, h - 30, 80, 20))
    pygame.draw.polygon(surf, (30, 28, 24), [(w - 280, h - 12), (w - 260, h - 28), (w - 240, h - 12)])


def _tema_abandonado(surf, sala, rng):
    base = (50, 50, 52)
    _piso_concreto(surf, rng, base, 80)
    _sujeira(surf, rng, base, 1600, (-14, 6))
    _rachaduras(surf, rng, 18, (26, 26, 30), (80, 220))
    _manchas(surf, rng, 12, (8, 8, 10), 60)
    w, h = sala.largura, sala.altura
    for _ in range(40):                                                 # entulho miúdo
        x, y = rng.randint(60, w - 80), rng.randint(60, h - 80)
        c = rng.choice(((66, 62, 58), (80, 72, 64), (44, 44, 48)))
        pygame.draw.polygon(surf, c, [(x, y), (x + rng.randint(6, 16), y - rng.randint(2, 6)), (x + rng.randint(10, 20), y + rng.randint(4, 10)), (x + 2, y + 8)])
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_tijolo(surf, r, rng, (62, 52, 50), (36, 30, 30))
    for r in obs:
        _parede_tijolo(surf, r, rng, (72, 60, 56), (40, 34, 34))
    for _ in range(6):                                                  # buracos nas paredes
        x = rng.randint(80, w - 120)
        pygame.draw.rect(surf, (18, 16, 18), (x, 6, rng.randint(14, 26), rng.randint(10, 24)))
    for (x, y) in ((44, 44), (w - 76, 44)):                             # teias de aranha nos cantos
        for k in range(1, 5):
            pygame.draw.line(surf, (110, 110, 114), (x, y), (x + k * 6, y + 4 * k - 2))
            pygame.draw.line(surf, (110, 110, 114), (x, y), (x + 4 * k - 2, y + k * 6))


def _tema_hospital(surf, sala, rng):
    base = (96, 108, 108)
    _piso_xadrez(surf, rng, base, (88, 100, 100), (62, 72, 72))
    _sujeira(surf, rng, base, 2400)
    _manchas(surf, rng, 10, (110, 20, 24), 58, (10, 30), (6, 16))
    _manchas(surf, rng, 8, (30, 40, 40), 40)
    w, h = sala.largura, sala.altura
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_azulejo(surf, r, rng, (86, 124, 122), (56, 90, 88))
    for r in obs:
        _parede_azulejo(surf, r, rng, (100, 138, 136), (64, 98, 96))
    pygame.draw.rect(surf, (200, 200, 196), (w // 2 - 14, 8, 28, 24))              # cruz vermelha
    pygame.draw.rect(surf, (180, 40, 44), (w // 2 - 3, 11, 6, 18))
    pygame.draw.rect(surf, (180, 40, 44), (w // 2 - 9, 17, 18, 6))
    for x in (260, 760, 1260):                                                     # monitores e armários
        pygame.draw.rect(surf, (36, 40, 46), (x, 9, 36, 22), border_radius=2)
        pygame.draw.rect(surf, (20, 70, 50), (x + 3, 12, 30, 14))
        pygame.draw.lines(surf, (90, 230, 140), False, [(x + 5, 20), (x + 12, 20), (x + 16, 14), (x + 21, 25), (x + 25, 20), (x + 31, 20)], 1)
    for x in range(160, w - 160, 340):
        pygame.draw.rect(surf, (200, 200, 204), (x, h - 34, 44, 28))
        pygame.draw.rect(surf, (110, 116, 120), (x, h - 34, 44, 28), 2)
        pygame.draw.line(surf, (110, 116, 120), (x + 22, h - 34), (x + 22, h - 6), 2)


def _tema_prisao(surf, sala, rng):
    base = (44, 44, 52)
    _piso_pedra(surf, rng, base)
    _manchas(surf, rng, 18, (6, 6, 10), 56, (20, 70), (10, 36))
    _manchas(surf, rng, 6, (40, 70, 44), 40, (16, 40), (8, 20))
    w, h = sala.largura, sala.altura
    _rachaduras(surf, rng, 10, (22, 22, 28))
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_pedra(surf, r, rng, (62, 64, 76))
    for r in obs:
        _parede_pedra(surf, r, rng, (70, 72, 86))
    for x in range(160, w - 400, 380):
        pygame.draw.rect(surf, (20, 22, 30), (x, 8, 34, 24))
        for bx in range(x + 6, x + 30, 8):
            pygame.draw.rect(surf, (80, 84, 96), (bx, 8, 3, 24))


def _tema_geradores(surf, sala, rng):
    base = (52, 54, 52)
    _piso_concreto(surf, rng, base, 100)
    w, h = sala.largura, sala.altura
    _manchas(surf, rng, 12, (8, 8, 8), 56)
    _manchas(surf, rng, 6, (60, 50, 20), 44, (12, 30), (6, 16))
    _faixa_perigo(surf, pygame.Rect(200, 60, w - 400, 8))
    for x in range(200, w - 200, 300):                                  # cabos no chão
        pts = [(x, 240), (x + 60, 250), (x + 130, 232), (x + 210, 252)]
        pygame.draw.lines(surf, (20, 20, 24), False, pts, 5)
        pygame.draw.lines(surf, (60, 60, 70), False, pts, 2)
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_painel(surf, r, rng, (50, 54, 62), (96, 100, 110), 80)
    for r in obs:
        _parede_painel(surf, r, rng, (62, 66, 74), (104, 108, 118), 80)
    # porta do elevador (aberta e parada) na parede da esquerda, onde o operário entra
    ey = sala.ponto_entrada[1]
    pygame.draw.rect(surf, (26, 28, 34), (2, ey - 70, 36, 150))
    pygame.draw.rect(surf, (90, 96, 108), (2, ey - 70, 8, 150))
    pygame.draw.rect(surf, (90, 96, 108), (30, ey - 70, 8, 150))
    pygame.draw.rect(surf, (140, 40, 36), (14, ey - 84, 12, 8))
    for x in range(360, w - 360, 280):                                  # painéis elétricos
        pygame.draw.rect(surf, (76, 82, 92), (x, 7, 54, 28))
        pygame.draw.rect(surf, (30, 32, 38), (x, 7, 54, 28), 2)
        for k in range(4):
            pygame.draw.rect(surf, (200, 200, 60) if k % 2 else (60, 200, 90), (x + 6 + k * 11, 12, 6, 6))
        pygame.draw.rect(surf, (36, 38, 44), (x + 6, 22, 42, 8))


def _tema_patio(surf, sala, rng):
    base = (92, 96, 94)
    _piso_concreto(surf, rng, base, 100)
    w, h = sala.largura, sala.altura
    for _ in range(26):                                                 # mato nas frestas
        x, y = rng.randint(60, w - 100), rng.randint(60, h - 100)
        for k in range(rng.randint(8, 16)):
            pygame.draw.line(surf, rng.choice(((58, 90, 52), (72, 108, 60), (44, 70, 44))),
                             (x + rng.randint(-10, 10), y + rng.randint(-4, 4)),
                             (x + rng.randint(-12, 12), y - rng.randint(4, 12)), 2)
    _manchas(surf, rng, 10, (50, 64, 80), 60, (30, 70), (12, 30))       # poças
    _manchas(surf, rng, 8, (20, 22, 22), 44)
    _rachaduras(surf, rng, 10, (50, 52, 52))
    for (x, y) in ((380, 180), (900, 700), (1300, 300)):                # lonas e materiais
        pygame.draw.polygon(surf, (62, 92, 112), [(x, y), (x + 70, y - 6), (x + 86, y + 40), (x + 10, y + 52)])
        pygame.draw.polygon(surf, (38, 60, 78), [(x, y), (x + 70, y - 6), (x + 86, y + 40), (x + 10, y + 52)], 2)
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_cerca(surf, r, rng, (50, 54, 58), (124, 132, 140))
    for r in obs:
        _parede_cerca(surf, r, rng, (60, 64, 68), (130, 138, 146))
    for x in range(200, w - 200, 420):                                  # postes de luz
        halo = _alfa(120, 120)
        for rr in range(60, 4, -6):
            pygame.draw.circle(halo, (255, 230, 150, int(34 * (1 - rr / 60) ** 1.5)), (60, 60), rr)
        surf.blit(halo, (x - 60, 60))
        pygame.draw.rect(surf, (30, 30, 34), (x - 3, 30, 6, 14))
        pygame.draw.circle(surf, (255, 232, 160), (x, 44), 5)


def _tema_seguranca(surf, sala, rng):
    base = (40, 44, 56)
    _piso_xadrez(surf, rng, base, (36, 40, 52), (24, 28, 38), 60)
    w, h = sala.largura, sala.altura
    for x in range(120, w - 120, 150):                                  # setas de emergência
        _seta_chao(surf, x, h // 2, (200, 160, 50))
    _faixa_perigo(surf, pygame.Rect(40, 60, w - 80, 8))
    _faixa_perigo(surf, pygame.Rect(40, h - 68, w - 80, 8))
    _manchas(surf, rng, 8, (8, 8, 12), 54)
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_painel(surf, r, rng, (54, 58, 70), (100, 104, 116))
    for r in obs:
        _parede_painel(surf, r, rng, (66, 70, 84), (110, 114, 126))
    for x in (250, 700, 1150, 1600):
        _camera(surf, x, 20)
    # portões de segurança (as portas que vão fechando)
    for x in (560, 1010, 1460):
        pygame.draw.rect(surf, (34, 36, 44), (x, 40, 18, 90))
        for yy in range(46, 124, 10):
            pygame.draw.rect(surf, (110, 114, 124), (x + 2, yy, 14, 4))
        pygame.draw.rect(surf, (34, 36, 44), (x, h - 130, 18, 90))
        for yy in range(h - 124, h - 46, 10):
            pygame.draw.rect(surf, (110, 114, 124), (x + 2, yy, 14, 4))


def _tema_biblioteca(surf, sala, rng):
    base = (96, 66, 42)
    _piso_madeira(surf, rng, base)
    w, h = sala.largura, sala.altura
    pygame.draw.rect(surf, (110, 40, 44), (80, h // 2 - 50, w - 260, 100))               # tapete corrido
    pygame.draw.rect(surf, (170, 130, 70), (80, h // 2 - 50, w - 260, 100), 4)
    pygame.draw.rect(surf, (170, 130, 70), (96, h // 2 - 34, w - 292, 68), 2)
    _manchas(surf, rng, 8, (20, 10, 6), 44)
    _papeis(surf, rng, 40)
    bord, obs = _bordas(sala)
    for r in bord:
        _parede_estante(surf, r, rng, (84, 54, 34))
    for r in obs:
        _parede_estante(surf, r, rng, (96, 62, 40))
    # luar da janela da direita (onde o operário pula)
    _facho_janela(surf, w - 230, h // 2 - 60, 140, 120, (150, 180, 230), 22)


TEMAS = {
    "dormitorio": _tema_dormitorio, "deposito": _tema_deposito, "escritorio": _tema_escritorio,
    "corredor": _tema_corredor, "manutencao": _tema_manutencao, "abandonado": _tema_abandonado,
    "hospital": _tema_hospital, "prisao": _tema_prisao, "geradores": _tema_geradores,
    "patio": _tema_patio, "seguranca": _tema_seguranca, "biblioteca": _tema_biblioteca,
    "duto": _tema_duto,
}


def _acabamento_cinematico(surf, tema, rng):
    """Camada de arte procedural: desgaste, luz localizada e objetos de cena."""
    w, h = surf.get_size()
    cores = {"dormitorio": (130, 178, 166), "deposito": (202, 153, 95),
             "escritorio": (158, 178, 194), "corredor": (135, 166, 190),
             "duto": (160, 192, 165), "manutencao": (215, 164, 92),
             "abandonado": (159, 135, 124), "hospital": (150, 205, 190),
             "prisao": (140, 164, 191), "geradores": (231, 160, 85),
             "patio": (155, 177, 198), "seguranca": (199, 93, 89),
             "biblioteca": (210, 176, 117)}
    cor = cores.get(tema, (170, 180, 180))
    # Patina de piso com marcas finas e riscos de arrasto, deterministica.
    marcas = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(max(25, (w * h) // 12500)):
        x, y = rng.randrange(30, max(31, w-30)), rng.randrange(40, max(41, h-40))
        comprimento = rng.randrange(12, 55)
        pygame.draw.line(marcas, (8, 12, 16, rng.randrange(12, 30)),
                         (x, y), (min(w-1, x+comprimento), y+rng.randrange(-4, 5)), 1)
        if i % 5 == 0:
            pygame.draw.line(marcas, (*cor, 23), (x, y+3), (min(w-1,x+comprimento//2), y+3), 1)
    # Pequenas luminarias e halos suaves para leitura espacial.
    for x in range(165, w-80, 390):
        for y in (90, h-90):
            halo = pygame.Surface((220, 220), pygame.SRCALPHA)
            for r in range(105, 10, -10):
                pygame.draw.circle(halo, (*cor, max(1, int(9*(1-r/115)))), (110,110), r)
            marcas.blit(halo, (x-110, y-110))
            pygame.draw.circle(marcas, (16, 20, 24, 210), (x,y), 12)
            pygame.draw.circle(marcas, (*cor, 185), (x,y), 6)
            pygame.draw.circle(marcas, (240, 232, 201, 205), (x-2,y-2), 2)
    # Objetos ambientais: documentos, latas, parafusos, marcas de aviso.
    for i in range(max(12, (w*h)//52000)):
        x, y = rng.randrange(65,max(66,w-65)), rng.randrange(65,max(66,h-65))
        if i % 3 == 0:
            pygame.draw.polygon(marcas, (186,174,144,135), [(x,y),(x+17,y-3),(x+21,y+9),(x+3,y+13)])
            pygame.draw.line(marcas, (66,67,67,120), (x+4,y+4), (x+14,y+2), 1)
        elif i % 3 == 1:
            pygame.draw.ellipse(marcas, (15,20,23,115), (x-3,y+5,20,8))
            pygame.draw.rect(marcas, (82,92,96,170), (x,y,13,9), border_radius=2)
            pygame.draw.line(marcas, (171,174,164,160), (x+2,y+2),(x+10,y+2),1)
        else:
            pygame.draw.circle(marcas, (20,24,28,125), (x,y), 5)
            pygame.draw.circle(marcas, (154,154,142,160), (x,y), 3,1)
    surf.blit(marcas, (0,0))
    # Vinheta sutil, pré-calculada apenas na construção do mapa.
    vinheta = pygame.Surface((w,h),pygame.SRCALPHA)
    for k in range(9):
        margem = k*11
        pygame.draw.rect(vinheta,(3,7,11,4+k), (margem,margem,w-2*margem,h-2*margem), max(1, 12-k))
    surf.blit(vinheta,(0,0))


def fundo_tema(sala, tema):
    surf = pygame.Surface((sala.largura, sala.altura))
    rng = random.Random(sala.largura * 17 + sala.altura * 3 + hash(tema) % 1000)
    TEMAS[tema](surf, sala, rng)
    _acabamento_cinematico(surf, tema, rng)
    return surf


_cache_anim = {}


def animar_tema(sala, surf, tempo_ms):
    tema = getattr(sala, "tema", None)
    w, h = sala.largura, sala.altura
    if tema in ("seguranca", "geradores"):
        pulso = 0.5 + 0.5 * math.sin(tempo_ms / (260 if tema == "seguranca" else 700))
        chave = (id(sala), "luz")
        luz = _cache_anim.get(chave)
        if luz is None:
            luz = _alfa(w, h)
            for x in range(160, w - 120, 280):
                for y in (46, h - 46):
                    for rr in range(70, 6, -8):
                        pygame.draw.circle(luz, (230, 30, 30, int(40 * (1 - rr / 70) ** 1.6)), (x, y), rr)
            _cache_anim[chave] = luz
        luz.set_alpha(int(60 + 190 * pulso) if tema == "seguranca" else int(30 + 120 * pulso))
        surf.blit(luz, (0, 0))
    elif tema == "manutencao":
        for i, x in enumerate(range(200, w - 200, 260)):
            for k in range(4):
                fase = ((tempo_ms / 900) + i * 0.37 + k * 0.25) % 1.0
                a = int(70 * (1 - fase))
                r = 6 + int(fase * 22)
                p = _alfa(r * 2, r * 2)
                pygame.draw.circle(p, (150, 220, 170, a), (r, r), r)
                surf.blit(p, (x - r + int(math.sin(fase * 6 + i) * 8), 36 + int(fase * 90) - r))
    elif tema == "hospital":
        if (tempo_ms // 140) % 17 == 0:
            pass


def desenhar_estante(surf, rect):
    """Estante de livros (usada na biblioteca da sala 12)."""
    _parede_estante(surf, rect, random.Random(rect.x * 7 + rect.y), (84, 54, 34))
    pygame.draw.rect(surf, (52, 34, 22), rect, 3)


def desenhar_duto(surf, duto):
    """Duto de ventilação da sala 4 (corredor, grades e portinholas)."""
    c = duto["corredor"]
    pygame.draw.rect(surf, (36, 38, 44), c.inflate(8, 8))
    pygame.draw.rect(surf, (78, 82, 92), c)
    pygame.draw.rect(surf, (112, 116, 128), (c.x, c.y, c.width, 4))
    for x in range(c.x + 30, c.right - 20, 60):
        pygame.draw.rect(surf, (54, 58, 68), (x, c.y, 4, c.height))
    for x in range(c.x + 50, c.right - 40, 120):
        for k in range(5):
            pygame.draw.rect(surf, (44, 46, 54), (x, c.y + 14 + k * 8, 30, 3))
    for chave, aberta in (("rect_entrada", duto["porta_entrada_aberta"]), ("rect_saida", duto["porta_saida_aberta"])):
        r = duto[chave]
        if not aberta:
            pygame.draw.rect(surf, (150, 154, 166), r)
            pygame.draw.rect(surf, (80, 84, 96), r, 2)
            for yy in range(r.y + 6, r.bottom - 4, 10):
                pygame.draw.line(surf, (96, 100, 112), (r.x + 2, yy), (r.right - 3, yy))
