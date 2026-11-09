"""Áudio espacial procedural para o Eco do Abismo (usado na fase 7).

Nenhum arquivo de som é necessário: bipes, vozes, chiado e zumbido são
sintetizados em Python na hora em que a fase começa. O som sai em estéreo,
com volume e balanço (esquerda/direita) calculados pela posição da fonte
em relação ao jogador.

Se o mixer não puder ser iniciado (sem placa de som, por exemplo),
`AudioEspacial.ativo` fica False e a fase liga uma seta visual de ajuda.
"""
import array
import math
import random

import pygame

TAXA_SINTESE = 11025      # taxa em que os sons são gerados (depois reamostrada)
LIMITE_ABAFADO = 0.55     # acima dessa fração do alcance o som sai "abafado"


# ---------------------------------------------------------------------------
# Matemática do som (sem pygame, fácil de testar)
# ---------------------------------------------------------------------------
def mixagem_estereo(origem, ouvinte, alcance, pan_erro=0.0, expoente=1.4):
    """Devolve (volume_esq, volume_dir, proximidade 0..1).

    proximidade = distancia / alcance (1.0 = fora do alcance, mudo).
    `pan_erro` desloca o balanço (usado para simular o ouvido ruim).
    """
    dx = origem[0] - ouvinte[0]
    dy = origem[1] - ouvinte[1]
    dist = math.hypot(dx, dy)
    if dist >= alcance:
        return 0.0, 0.0, 1.0
    prox = dist / alcance
    vol = (1.0 - prox) ** expoente
    pan = max(-1.0, min(1.0, dx / 400.0 + pan_erro))   # -1 esquerda ... +1 direita (400px = totalmente de um lado)
    ang = (pan + 1.0) * math.pi / 4.0
    return vol * math.cos(ang), vol * math.sin(ang), prox


# ---------------------------------------------------------------------------
# Síntese (listas de floats entre -1 e 1)
# ---------------------------------------------------------------------------
def _silencio(dur):
    return [0.0] * int(dur * TAXA_SINTESE)


def _juntar(*partes):
    saida = []
    for p in partes:
        saida.extend(p)
    return saida


def _bip(freq, dur=0.11):
    n = int(dur * TAXA_SINTESE)
    ataque = 0.004 * TAXA_SINTESE
    return [math.sin(2 * math.pi * freq * i / TAXA_SINTESE)
            * math.exp(-(i / TAXA_SINTESE) * 26)
            * min(1.0, i / ataque)
            for i in range(n)]


def _batida(freq, dur=0.22, semente=3):
    """Pancada grave com um 'clique' de ruído no início (fechadura)."""
    rng = random.Random(semente)
    n = int(dur * TAXA_SINTESE)
    saida = []
    for i in range(n):
        t = i / TAXA_SINTESE
        corpo = math.sin(2 * math.pi * freq * t) * math.exp(-t * 16)
        clique = rng.uniform(-1, 1) * math.exp(-t * 140) * 0.8
        saida.append(corpo + clique)
    return saida


def _passa_baixa(amostras, a=0.35, ganho=1.3):
    y = 0.0
    saida = []
    for x in amostras:
        y += a * (x - y)
        saida.append(y * ganho)
    return saida


def _normalizar(amostras, pico=0.85):
    maior = max((abs(s) for s in amostras), default=0.0)
    if maior <= 1e-9:
        return amostras
    k = pico / maior
    return [s * k for s in amostras]


def _fade(amostras, dur=0.03):
    n = len(amostras)
    f = max(1, int(dur * TAXA_SINTESE))
    for i in range(min(f, n // 2)):
        k = i / f
        amostras[i] *= k
        amostras[n - 1 - i] *= k
    return amostras


def _chiado(dur=1.0, semente=11):
    rng = random.Random(semente)
    y = 0.0
    saida = []
    for _ in range(int(dur * TAXA_SINTESE)):
        y += 0.4 * (rng.uniform(-1, 1) - y)
        saida.append(y)
    return _fade(_normalizar(saida, 0.6), 0.04)


def _zumbido(dur=1.8):
    n = int(dur * TAXA_SINTESE)
    saida = [0.6 * math.sin(2 * math.pi * 3800 * i / TAXA_SINTESE)
             + 0.25 * math.sin(2 * math.pi * 2850 * i / TAXA_SINTESE)
             for i in range(n)]
    return _fade(_normalizar(saida, 0.5), 0.25)


def _susto(dur=0.6, semente=5):
    rng = random.Random(semente)
    n = int(dur * TAXA_SINTESE)
    saida = []
    for i in range(n):
        t = i / TAXA_SINTESE
        saida.append(rng.uniform(-1, 1) * math.exp(-t * 9)
                     + math.sin(2 * math.pi * 55 * t) * math.exp(-t * 6))
    return _normalizar(saida, 0.9)


def _formante(freq, f1, f2):
    return (math.exp(-((freq - f1) / 180.0) ** 2)
            + 0.6 * math.exp(-((freq - f2) / 300.0) ** 2)
            + 0.04)


def _silaba(f0, f1, f2, dur, vibrato, ruido, rng, sussurro=False):
    n = max(8, int(dur * TAXA_SINTESE))
    if sussurro:
        y = 0.0
        saida = []
        for i in range(n):
            env = math.sin(math.pi * i / n) ** 0.7
            y += 0.55 * (rng.uniform(-1, 1) - y)
            saida.append(y * env)
        return saida

    h_max = max(1, int(min(3000, TAXA_SINTESE / 2 - 300) / f0))
    h_max = min(h_max, 14)
    amps = [_formante(f0 * h, f1, f2) / (h ** 0.7) for h in range(1, h_max + 1)]
    soma = sum(amps) or 1.0
    amps = [a / soma for a in amps]
    queda = rng.uniform(-0.06, 0.04)
    fase = 0.0
    saida = []
    for i in range(n):
        u = i / n
        t = i / TAXA_SINTESE
        f = f0 * (1 + queda * u + vibrato * math.sin(2 * math.pi * 5.5 * t))
        fase += 2 * math.pi * f / TAXA_SINTESE
        s = 0.0
        for h, a in enumerate(amps, start=1):
            s += a * math.sin(h * fase)
        s = s * (1 - ruido) + ruido * rng.uniform(-1, 1)
        saida.append(s * math.sin(math.pi * u) ** 0.6)
    return saida


def sintetizar_voz(n_silabas, f0, formantes, dur, vibrato=0.0, ruido=0.0,
                   sussurro=False, anel=0.0, semente=1):
    """Balbucio com cara de voz (sem palavras): as legendas dizem o que é."""
    rng = random.Random(semente)
    partes = []
    for k in range(n_silabas):
        f1, f2 = formantes[k % len(formantes)]
        partes.append(_silaba(f0, f1, f2, dur * rng.uniform(0.8, 1.25),
                              vibrato, ruido, rng, sussurro))
        partes.append(_silencio(rng.uniform(0.04, 0.09)))
    voz = _juntar(*partes)
    if anel > 0:
        voz = [s * ((1 - anel) + anel * math.sin(2 * math.pi * 47 * i / TAXA_SINTESE))
               for i, s in enumerate(voz)]
    return _fade(_normalizar(voz, 0.85), 0.02)


# ---------------------------------------------------------------------------
# Catálogo de sons da fase 7 (nome -> lista de variantes de amostras)
# ---------------------------------------------------------------------------
def catalogo_fase7():
    f_real = [(600, 1000), (500, 900), (700, 1100), (450, 800)]      # vogais redondas e graves
    f_agudo = [(350, 2300), (550, 1900), (300, 2600)]                # vogais finas e "erradas"
    f_grave = [(400, 700), (350, 600)]

    return {
        # --- o barulho REAL: dois bipes, mesmo tom, mesmo ritmo, sempre ---
        "bip_real": [_normalizar(_juntar(_bip(880), _silencio(0.16), _bip(880)), 0.8)],
        # --- barulhos FALSOS: tom ou ritmo diferentes, aparecem em lugares aleatórios ---
        "falso_agudo": [_normalizar(_bip(1320, 0.09), 0.7)],
        "falso_grave": [_normalizar(_juntar(_bip(520, 0.14), _silencio(0.35), _bip(520, 0.14)), 0.8)],
        "falso_triplo": [_normalizar(_juntar(_bip(880), _silencio(0.10), _bip(880),
                                             _silencio(0.22), _bip(880)), 0.8)],
        "falso_quase": [_normalizar(_juntar(_bip(940), _silencio(0.16), _bip(940)), 0.8)],
        # --- depois da chave: a fechadura da porta ---
        "tique_porta": [_normalizar(_juntar(_batida(180), _silencio(0.12), _batida(140, semente=4)), 0.9)],
        # --- ambiente ---
        "chiado": [_chiado()],
        "zumbido": [_zumbido()],
        "susto": [_susto()],
        # --- A VOZ de antes: grave, estável, centrada ---
        "voz_real": [sintetizar_voz(n, 105, f_real, 0.24, ruido=0.03, semente=s)
                     for n, s in ((5, 1), (8, 2), (11, 3))],
        # --- vozes novas: agudas/trêmulas, sussurradas ou graves e distorcidas ---
        "fv_agudo": [sintetizar_voz(n, 190, f_agudo, 0.17, vibrato=0.05, ruido=0.12, semente=s)
                     for n, s in ((6, 10), (9, 11))],
        "fv_sussurro": [sintetizar_voz(n, 100, f_agudo, 0.15, sussurro=True, semente=s)
                        for n, s in ((8, 20), (10, 21))],
        "fv_grave": [sintetizar_voz(n, 68, f_grave, 0.30, anel=0.55, ruido=0.05, semente=s)
                     for n, s in ((5, 30), (7, 31))],
    }


# ---------------------------------------------------------------------------
# Motor de áudio (pygame.mixer)
# ---------------------------------------------------------------------------
class AudioEspacial:
    def __init__(self):
        self.ativo = False
        self._cfg = None
        self._sons = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            cfg = pygame.mixer.get_init()
            if cfg and cfg[1] == -16 and cfg[2] in (1, 2):
                self._cfg = cfg
                pygame.mixer.set_num_channels(24)
                pygame.mixer.stop()          # corta o que sobrou da fase anterior
                for nome, variantes in catalogo_fase7().items():
                    self._sons[nome] = [
                        (self._para_sound(v), self._para_sound(_passa_baixa(v)))
                        for v in variantes
                    ]
                self.ativo = True
        except Exception as erro:            # sem áudio: a fase usa a seta visual
            print(f"[audio] desativado: {erro}")
            self.ativo = False

    def _para_sound(self, amostras):
        freq, _fmt, canais = self._cfg
        n_in = len(amostras)
        if freq != TAXA_SINTESE and n_in >= 2:
            n_out = max(2, int(n_in * freq / TAXA_SINTESE))
            passo = (n_in - 1) / (n_out - 1)
            novo = []
            for j in range(n_out):
                p = j * passo
                i = int(p)
                a = amostras[i]
                b = amostras[i + 1] if i + 1 < n_in else a
                novo.append(a + (b - a) * (p - i))
            amostras = novo
        buf = array.array("h")
        for s in amostras:
            v = int(max(-1.0, min(1.0, s)) * 30000)
            buf.append(v)
            if canais == 2:
                buf.append(v)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _tocar(self, nome, esq, dir_, abafado):
        variantes = self._sons.get(nome)
        if not variantes:
            return
        nitido, abafada = random.choice(variantes)
        canal = (abafada if abafado else nitido).play()
        if canal is not None:
            canal.set_volume(min(1.0, esq), min(1.0, dir_))

    def tocar_na_posicao(self, nome, origem, ouvinte, alcance, ganho=1.0, pan_erro=0.0,
                         forcar_abafado=False):
        """Toca um som vindo de `origem` (mundo) para um ouvinte em `ouvinte`."""
        if not self.ativo:
            return False
        esq, dir_, prox = mixagem_estereo(origem, ouvinte, alcance, pan_erro)
        esq *= ganho
        dir_ *= ganho
        if max(esq, dir_) < 0.01:
            return False
        self._tocar(nome, esq, dir_, forcar_abafado or prox > LIMITE_ABAFADO)
        return True

    def tocar_central(self, nome, ganho=1.0, abafado=False):
        """Som 'dentro da cabeça': sem direção (A VOZ, chiado, zumbido)."""
        if not self.ativo:
            return False
        self._tocar(nome, ganho, ganho, abafado)
        return True

    def parar(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.stop()
        except Exception:
            pass