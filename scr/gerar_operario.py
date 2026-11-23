import os
import numpy as np
from PIL import Image

PAL = {'H': (76, 34, 0), 'h': (66, 29, 0), 'S': (201, 155, 121), 's': (196, 148, 113), 'e': (180, 126, 85),
       'A': (168, 96, 3), 'B': (152, 87, 3), 'C': (138, 79, 2), 'K': (53, 31, 0), 'k': (62, 36, 18),
       'W': (255, 255, 255), 'w': (228, 228, 228),
       # só para brilhos de dano e pílula
       'R': (214, 52, 60), 'U': (70, 110, 220), 'O': (255, 140, 40), 'Y': (255, 215, 90)}
LET = [c for c in PAL if c not in "RUOY"]
COL = np.array([PAL[c] for c in LET])
AQUI = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(AQUI, "assets", "sprites", "base")
SAIDA = os.path.join(AQUI, "assets", "sprites", "operario")
TELA = 600


def ler(nome, u):
    a = np.array(Image.open(os.path.join(BASE, nome)).convert("RGBA"))
    n = 1200 // u
    g = []
    for y in range(n):
        linha = []
        for x in range(n):
            p = a[y * u + u // 2, x * u + u // 2]
            if p[3] < 128:
                linha.append('.')
            else:
                linha.append(LET[int(((COL - p[:3].astype(int)) ** 2).sum(1).argmin())])
        g.append(linha)
    return g


def vazia(n):
    return [['.'] * n for _ in range(n)]


def linhas(g, a, b):
    return [r[:] for r in g[a:b + 1]]


def empilhar(blocos, n, y0=0):
    """Empilha blocos de linhas (cada um é lista de linhas)."""
    g = vazia(n)
    y = y0
    for bloco in blocos:
        for r in bloco:
            g[y] = r[:]
            y += 1
    return g, y


def encostar_embaixo(g, folga=1):
    """Desce o desenho até os pés ficarem na mesma altura das sprites originais."""
    n = len(g)
    ult = max(i for i, r in enumerate(g) if any(c != '.' for c in r))
    alvo = n - 1 - folga
    dy = alvo - ult
    if dy > 0:
        g = [['.'] * n for _ in range(dy)] + g[:n - dy]
    return g


def pintar(g, x, y, bloco):
    """Cola um bloco de texto em (x,y). '.' apaga, ' ' mantém."""
    for j, linha in enumerate(bloco):
        for i, c in enumerate(linha):
            if c == ' ':
                continue
            if 0 <= y + j < len(g) and 0 <= x + i < len(g[0]):
                g[y + j][x + i] = c


def deslocar(g, dx, y0, y1):
    """Desloca as linhas y0..y1 dx colunas."""
    n = len(g[0])
    for y in range(y0, y1 + 1):
        r = g[y]
        if dx > 0:
            g[y] = ['.'] * dx + r[:n - dx]
        elif dx < 0:
            g[y] = r[-dx:] + ['.'] * (-dx)


def salvar(g, u, nome):
    n = len(g)
    img = Image.new("RGBA", (n * u, n * u), (0, 0, 0, 0))
    px = img.load()
    for y, r in enumerate(g):
        for x, c in enumerate(r):
            if c != '.':
                cor = PAL[c] + (255,)
                for j in range(u):
                    for i in range(u):
                        px[x * u + i, y * u + j] = cor
    # canvas final TELA x TELA (mesma proporção das originais 1200x1200)
    img = img.resize((TELA, TELA), Image.NEAREST) if n * u != TELA else img
    img.save(os.path.join(SAIDA, nome))
    return img


def ux(n):
    return TELA // n


# =========================================================================== AGACHADO
def agachar_frente(f, passo=0):
    cab = linhas(f, 5, 34)
    tor = linhas(f, 35, 39) + linhas(f, 46, 47)
    quad = linhas(f, 48, 48)
    pernas = linhas(f, 49, 50) + linhas(f, 54, 54)
    botas = linhas(f, 55, 58)
    g, _ = empilhar([cab, tor, quad, pernas, botas], 60, 3)
    g = encostar_embaixo(g, 1)
    n = len(g)
    ult = max(i for i, r in enumerate(g) if any(c != '.' for c in r))
    if passo:                                        # passo: um pé sobe 1 linha
        for x in (range(21, 30) if passo > 0 else range(31, 40)):
            for y in range(ult, ult - 3, -1):
                if g[y][x] != '.':
                    g[y][x] = '.'
    return g


def agachar_costas(c, passo=0):
    cab = linhas(c, 6, 25)
    tor = linhas(c, 26, 29) + linhas(c, 36, 38)
    quad = linhas(c, 39, 40)
    pernas = linhas(c, 44, 45)
    botas = linhas(c, 46, 48)
    g, _ = empilhar([cab, tor, quad, pernas, botas], 50, 3)
    g = encostar_embaixo(g, 1)
    ult = max(i for i, r in enumerate(g) if any(ch != '.' for ch in r))
    if passo:
        xs = range(18, 24) if passo > 0 else range(25, 31)
        for x in xs:
            for y in range(ult, ult - 2, -1):
                g[y][x] = '.'
    return g


def agachar_lado(s, passo=0):
    cab = linhas(s, 1, 24)
    tor = linhas(s, 25, 28) + linhas(s, 35, 38)
    pernas = linhas(s, 39, 40) + linhas(s, 45, 46)
    botas = linhas(s, 47, 49)
    g, _ = empilhar([cab, tor, pernas, botas], 50, 0)
    g = encostar_embaixo(g, 0)
    ult = max(i for i, r in enumerate(g) if any(ch != '.' for ch in r))
    # a cabeça se projeta 2 colunas à frente para parecer curvado
    if passo:
        deslocar(g, 1 if passo > 0 else -1, ult - 3, ult)
    return g


# =========================================================================== PÍLULA e DANO (de frente)
def reta(g, p0, p1, esp=3, cor='A', borda='C'):
    """Braço/antebraço: faixa de 'esp' pixels com contorno, no estilo das mangas."""
    (x0, y0), (x1, y1) = p0, p1
    passos = max(abs(x1 - x0), abs(y1 - y0), 1)
    pts = [(round(x0 + (x1 - x0) * i / passos), round(y0 + (y1 - y0) * i / passos)) for i in range(passos + 1)]
    for (x, y) in pts:
        for j in range(-esp // 2 - 1, esp // 2 + 2):
            for i in range(-esp // 2 - 1, esp // 2 + 2):
                if g[y + j][x + i] == '.' or g[y + j][x + i] in 'ABC':
                    g[y + j][x + i] = borda
    for (x, y) in pts:
        for j in range(-esp // 2, esp // 2 + 1):
            for i in range(-esp // 2, esp // 2 + 1):
                g[y + j][x + i] = cor
    for (x, y) in pts:                               # sombra à direita, como nas suas mangas
        if g[y][x + esp // 2] == cor:
            g[y][x + esp // 2] = 'B'


def mao(g, x, y, w=5, h=4):
    pintar(g, x, y, [' ' + 'e' * (w - 2) + ' '] + ['e' + 'S' * (w - 2) + 'e'] * (h - 1) + [' ' + 'e' * (w - 2) + ' '])


def sem_maos(g):
    for (x0, x1) in ((16, 21), (37, 43)):
        for y in (46, 47, 48):
            for x in range(x0, x1 + 1):
                if g[y][x] in 'Se':
                    g[y][x] = '.'


def olhos_fechados(g):
    for x0 in (23, 34):
        for y in range(26, 30):
            for x in (x0, x0 + 1):
                g[y][x] = 'S'
    for x0 in (22, 33):
        pintar(g, x0, 28, ['kkkk'])


def olhos_dor(g):
    for x0 in (23, 34):
        for y in range(26, 30):
            for x in (x0, x0 + 1):
                g[y][x] = 'S'
    pintar(g, 22, 26, ['kk']); pintar(g, 24, 27, ['kk']); pintar(g, 25, 28, ['k'])
    pintar(g, 36, 26, ['kk']); pintar(g, 34, 27, ['kk']); pintar(g, 34, 28, ['k'])


def pilula_quadro(F, q):
    g = [r[:] for r in F]
    sem_maos(g)
    if q == 1:                                       # segura a pílula ao lado do peito
        reta(g, (19, 44), (13, 43), 3)
        mao(g, 9, 41)
        pintar(g, 10, 39, ["RRUU", "RRUU"])
    elif q == 2:                                     # leva o punho à boca
        reta(g, (19, 44), (25, 38), 3)
        pintar(g, 29, 30, ["RU"])
        mao(g, 26, 33, 7, 5)
    elif q == 3:                                     # pílula na boca
        reta(g, (19, 44), (25, 38), 3)
        pintar(g, 28, 30, ["kkkk", "kRUk"])
        mao(g, 26, 33, 7, 5)
    elif q == 4:                                     # engole de olhos fechados
        olhos_fechados(g)
        pintar(g, 28, 31, ["kkkk"])
        reta(g, (19, 44), (24, 41), 3)
        mao(g, 24, 37, 7, 5)
    else:                                            # alívio
        olhos_fechados(g)
        pintar(g, 27, 30, ["k    k", " kkkk "])
        pintar(g, 16, 46, ["SSSS"]); pintar(g, 38, 46, ["SSSS"])
        pintar(g, 16, 46, ["eSSSS"]); pintar(g, 15, 47, ["eSSSSe"])
    return g


def dano_quadro(F, q):
    g = [r[:] for r in F]
    olhos_dor(g)
    pintar(g, 27, 31, ["kkkkkk", "k    k"])
    if q == 1:                                       # leva o golpe no peito
        for (x, y, c) in ((27, 38, 'O'), (29, 41, 'Y'), (32, 43, 'O'), (26, 43, 'Y'), (34, 38, 'Y'), (31, 36, 'O')):
            g[y][x] = c
        deslocar(g, -1, 5, 47)
    elif q == 2:                                     # jogado para trás, braços abertos
        sem_maos(g)
        deslocar(g, 2, 5, 47)
        reta(g, (21, 40), (11, 33), 3)
        mao(g, 6, 30)
        reta(g, (40, 40), (48, 33), 3)
        mao(g, 47, 30)
    else:                                            # curvado de dor
        sem_maos(g)
        g = g[:35] + g[38:] + [['.'] * 60] * 3
        deslocar(g, -2, 5, 47)
        reta(g, (20, 42), (25, 45), 3)
        mao(g, 25, 44)
        reta(g, (40, 42), (35, 45), 3)
        mao(g, 31, 44)
        olhos_dor(g)
    return encostar_embaixo(g, 1) if q == 3 else g



# =========================================================================== GUARDAS (suas sprites recoloridas)
def recolorir(g, mapa):
    return [[mapa.get(c, c) for c in r] for r in g]


def gerar_guardas():
    pasta = os.path.join(AQUI, "assets", "sprites", "inimigos")
    os.makedirs(pasta, exist_ok=True)
    fontes = {"frente": ("frente.png", 20), "costas": ("costas.png", 24),
              "direita": ("lado_direita.png", 24), "esquerda": ("lado_esquerda.png", 24)}
    extra = {'1': (84, 104, 168), '2': (72, 90, 148), '3': (56, 70, 118), '4': (40, 48, 86), '5': (28, 34, 64),
             '6': (230, 190, 70), '7': (200, 160, 50),
             '8': (150, 60, 60), '9': (132, 50, 50), 'a': (100, 36, 36), 'b': (56, 32, 32), 'c': (38, 22, 22)}
    PAL.update(extra)
    tipos = {"prisao": {'A': '1', 'B': '2', 'C': '3', 'H': '4', 'h': '5', 'W': '6', 'w': '7'},
             "perseguidor": {'A': '8', 'B': '9', 'C': 'a', 'H': 'b', 'h': 'c', 'W': '6', 'w': '7'}}
    for tipo, mapa in tipos.items():
        for d, (arq, u) in fontes.items():
            g = recolorir(ler(arq, u), mapa)
            xs = [x for r in g for x, c in enumerate(r) if c != '.']
            ys = [y for y, r in enumerate(g) if any(c != '.' for c in r)]
            x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
            cel = 4
            img = Image.new("RGBA", ((x1 - x0 + 1) * cel, (y1 - y0 + 1) * cel), (0, 0, 0, 0))
            px = img.load()
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    c = g[y][x]
                    if c != '.':
                        for j in range(cel):
                            for i in range(cel):
                                px[(x - x0) * cel + i, (y - y0) * cel + j] = PAL[c] + (255,)
            img.save(os.path.join(pasta, f"guarda_{tipo}_{d}.png"))



def gerar():
    os.makedirs(SAIDA, exist_ok=True)
    F = ler("frente.png", 20)
    C = ler("costas.png", 24)
    SD = ler("lado_direita.png", 24)
    SE = ler("lado_esquerda.png", 24)
    for p, nome in ((0, "parado"), (1, "andando_1"), (-1, "andando_2")):
        salvar(agachar_frente(F, p), 20, f"agachado_frente_{nome}.png")
        salvar(agachar_costas(C, p), 24, f"agachado_costas_{nome}.png")
        salvar(agachar_lado(SD, p), 24, f"agachado_direita_{nome}.png")
        salvar(agachar_lado(SE, p), 24, f"agachado_esquerda_{nome}.png")
    for q in range(1, 6):
        salvar(pilula_quadro(F, q), 20, f"pilula_{q}.png")
    for q in range(1, 4):
        salvar(dano_quadro(F, q), 20, f"dano_{q}.png")


if __name__ == "__main__":
    gerar()
    print("Poses geradas em", SAIDA)
