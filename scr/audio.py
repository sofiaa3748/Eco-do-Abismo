import array
import math
import random

import pygame

TAXA_SINTESE = 11025      # taxa em que os sons são gerados (depois reamostrada)
LIMITE_ABAFADO = 0.55     # acima dessa fração do alcance o som sai "abafado"

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

import os
import tempfile
import wave


def _ruido(dur, semente=1, a=1.0):
    """Ruído branco filtrado (a=1 sem filtro; menor = mais grave/abafado)."""
    rng = random.Random(semente)
    y = 0.0
    saida = []
    for _ in range(int(dur * TAXA_SINTESE)):
        y += a * (rng.uniform(-1, 1) - y)
        saida.append(y)
    return saida


def _env(amostras, queda=0.0, ataque=0.0, sino=False):
    """Aplica envelope: ataque linear, queda exponencial ou 'sino' (sobe e desce)."""
    n = len(amostras)
    saida = []
    for i, s in enumerate(amostras):
        t = i / TAXA_SINTESE
        k = 1.0
        if ataque > 0:
            k *= min(1.0, t / ataque)
        if queda > 0:
            k *= math.exp(-t * queda)
        if sino:
            k *= math.sin(math.pi * i / max(1, n)) ** 1.2
        saida.append(s * k)
    return saida


def _varredura(f0, f1, dur, harmonicos=1):
    """Tom que vai de f0 a f1 (Hz)."""
    n = int(dur * TAXA_SINTESE)
    fase = 0.0
    saida = []
    for i in range(n):
        f = f0 + (f1 - f0) * i / max(1, n - 1)
        fase += 2 * math.pi * f / TAXA_SINTESE
        s = 0.0
        for h in range(1, harmonicos + 1):
            s += math.sin(h * fase) / h
        saida.append(s)
    return saida


def _tom(freq, dur, queda=0.0):
    n = int(dur * TAXA_SINTESE)
    return _env([math.sin(2 * math.pi * freq * i / TAXA_SINTESE) for i in range(n)], queda=queda, ataque=0.004)


def _somar(*partes):
    """partes = (inicio_s, amostras, ganho)."""
    total = max(int(o * TAXA_SINTESE) + len(l) for o, l, g in partes)
    saida = [0.0] * total
    for o, l, g in partes:
        i0 = int(o * TAXA_SINTESE)
        for k, v in enumerate(l):
            saida[i0 + k] += v * g
    return saida


def _sino(freqs, dur, queda=9.0):
    """Metal batido: soma de parciais inarmônicas."""
    n = int(dur * TAXA_SINTESE)
    saida = [0.0] * n
    for k, f in enumerate(freqs):
        q = queda * (1 + 0.5 * k)
        for i in range(n):
            t = i / TAXA_SINTESE
            saida[i] += math.sin(2 * math.pi * f * t) * math.exp(-t * q) / (k + 1)
    return saida


def _som_passo(semente, grave=70, a=0.28):
    return _normalizar(_somar(
        (0.0, _env(_ruido(0.10, semente, a), queda=48), 1.0),
        (0.0, _env(_tom(grave, 0.10), queda=40), 0.9)), 0.7)


def _som_pilula():
    chocalho = _somar(*[(0.05 * k, _env(_ruido(0.03, 40 + k, 0.9), queda=120), 0.35) for k in range(4)])
    engolir = _env(_varredura(340, 130, 0.22), sino=True)
    alivio = _somar((0.0, _tom(520, 0.18, 9), 0.45), (0.12, _tom(780, 0.30, 7), 0.45))
    return _normalizar(_somar((0.0, chocalho, 0.7), (0.30, engolir, 0.8), (0.58, alivio, 0.7)), 0.8)


def _som_dano():
    soco = _env(_varredura(150, 45, 0.30), queda=9)
    estalo = _env(_ruido(0.25, 9, 0.8), queda=22)
    disson = _env(_somar((0.0, _tom(233, 0.5), 1.0), (0.0, _tom(247, 0.5), 1.0)), queda=6)
    return _normalizar(_somar((0.0, soco, 1.0), (0.0, estalo, 0.7), (0.02, disson, 0.35)), 0.9)


def _som_coletar():
    return _normalizar(_juntar(_bip(660, 0.09), _bip(990, 0.14)), 0.7)


def _som_chave():
    t = [(0.0, _sino([2400, 3100, 4100], 0.35, 14), 0.8), (0.11, _sino([2700, 3500], 0.3, 16), 0.6),
         (0.20, _sino([2200, 3000, 3900], 0.4, 12), 0.7)]
    return _normalizar(_somar(*t), 0.7)


def _som_papel():
    base = _ruido(0.28, 17, 0.75)
    rng = random.Random(5)
    return _normalizar(_env([s * (0.4 + 0.6 * abs(math.sin(i / 90 + rng.random() * 0.05)))
                             for i, s in enumerate(base)], sino=True), 0.5)


def _som_porta_abrir():
    chiado = _env(_ruido(0.55, 23, 0.32), sino=True)
    motor = _env(_varredura(110, 190, 0.55), sino=True)
    return _normalizar(_somar((0.0, _batida(105, 0.25, 6), 0.9), (0.05, chiado, 0.8),
                              (0.05, motor, 0.4), (0.52, _batida(80, 0.25, 8), 0.8)), 0.85)


def _som_porta_trancada():
    partes = [(0.0, _batida(300, 0.07, 2), 0.8), (0.09, _batida(260, 0.07, 3), 0.8),
              (0.20, _batida(320, 0.09, 4), 0.9)]
    return _normalizar(_somar(*partes), 0.7)


def _som_valvula():
    guincho = _env(_varredura(700, 1350, 0.38), ataque=0.03, sino=True)
    vib = [s * (0.7 + 0.3 * math.sin(i / 40)) for i, s in enumerate(guincho)]
    return _normalizar(_somar((0.0, vib, 0.6), (0.0, _env(_ruido(0.38, 31, 0.4), sino=True), 0.5),
                              (0.36, _sino([900, 1500], 0.2, 20), 0.5)), 0.8)


def _som_disjuntor_ok():
    estalo = _env(_ruido(0.04, 51, 1.0), queda=90)
    zumbido = _env(_varredura(110, 260, 0.35, 3), ataque=0.02, queda=3)
    fagulha = _somar(*[(0.04 * k, _env(_ruido(0.02, 60 + k, 1.0), queda=150), 0.3) for k in range(5)])
    return _normalizar(_somar((0.0, estalo, 1.0), (0.03, zumbido, 0.5), (0.1, fagulha, 0.6)), 0.8)


def _som_disjuntor_erro():
    buz = _env(_varredura(130, 70, 0.5, 6), ataque=0.01, queda=3)
    buz = [s * (0.6 + 0.4 * math.copysign(1, math.sin(i / 90))) for i, s in enumerate(buz)]
    return _normalizar(_somar((0.0, buz, 0.8), (0.0, _env(_ruido(0.5, 61, 0.5), queda=5), 0.3)), 0.8)


def _som_golpe():
    return _normalizar(_somar((0.0, _sino([520, 1130, 1870], 0.45, 10), 0.8),
                              (0.0, _env(_ruido(0.05, 71, 1.0), queda=80), 0.9),
                              (0.05, _env(_ruido(0.45, 72, 0.5), sino=True), 0.25)), 0.9)


def _som_arrombar():
    estalo = _env(_ruido(0.12, 81, 1.0), queda=50)
    madeira = _env(_varredura(180, 90, 0.2), queda=14)
    metal = _env(_varredura(1800, 600, 0.3, 2), queda=9)
    return _normalizar(_somar((0.0, estalo, 1.0), (0.0, madeira, 0.9), (0.03, metal, 0.35),
                              (0.18, _batida(90, 0.3, 9), 0.7)), 0.9)


def _som_arremesso():
    return _normalizar(_env(_ruido(0.35, 91, 0.22), ataque=0.12, sino=True), 0.5)


def _som_clang():
    return _normalizar(_somar((0.0, _sino([780, 1580, 2330, 3100], 0.9, 6), 0.8),
                              (0.0, _env(_ruido(0.04, 92, 1.0), queda=100), 0.8)), 0.9)


def _som_preso():
    return _normalizar(_somar((0.0, _batida(65, 0.5, 10), 1.0), (0.0, _sino([310, 640, 1010], 0.8, 7), 0.6),
                              (0.35, _sino([300, 620], 0.6, 9), 0.3)), 0.95)


def _som_tabua():
    ranger = _env(_varredura(160, 320, 0.28, 4), ataque=0.02, sino=True)
    ranger = [s * (0.7 + 0.3 * math.sin(i / 25)) for i, s in enumerate(ranger)]
    return _normalizar(_somar((0.0, ranger, 0.8), (0.0, _env(_ruido(0.28, 95, 0.3), sino=True), 0.3)), 0.7)


def _som_alarme():
    n = int(1.4 * TAXA_SINTESE)
    fase = 0.0
    saida = []
    for i in range(n):
        t = i / TAXA_SINTESE
        f = 620 + 280 * (0.5 - 0.5 * math.cos(2 * math.pi * t / 0.7))
        fase += 2 * math.pi * f / TAXA_SINTESE
        saida.append(math.sin(fase) + 0.4 * math.sin(2 * fase) + 0.2 * math.sin(3 * fase))
    return _fade(_normalizar(saida, 0.6), 0.03)


def _som_alarme_bip():
    return _normalizar(_juntar(_bip(1000, 0.12), _silencio(0.06), _bip(1000, 0.12)), 0.55)


def _som_sucesso():
    notas = [(0.0, 523.3), (0.14, 659.3), (0.28, 784.0), (0.42, 1046.5)]
    return _normalizar(_somar(*[(o, _tom(f, 0.5, 5), 0.7) for o, f in notas]), 0.7)


def _som_fase_completa():
    notas = [(0.0, 392.0), (0.16, 523.3), (0.32, 659.3), (0.48, 784.0)]
    partes = [(o, _sino([f, f * 2.01, f * 3.0], 0.9, 5), 0.6) for o, f in notas]
    return _normalizar(_somar(*partes), 0.7)


def _som_game_over():
    queda = _env(_varredura(300, 45, 1.3, 3), ataque=0.02, queda=1.5)
    return _normalizar(_somar((0.0, queda, 0.9), (0.0, _env(_ruido(1.3, 99, 0.2), queda=2.5), 0.4),
                              (0.0, _batida(55, 0.5, 3), 0.8)), 0.9)


def _som_clique():
    return _normalizar(_bip(1300, 0.05), 0.5)


def _som_final():
    acorde = [(0.0, f, 1.0) for f in (220.0, 261.6, 329.6)]
    return _fade(_normalizar(_somar(*[(o, _env(_tom(f, 3.2), ataque=0.5, sino=True), g) for o, f, g in acorde]), 0.6), 0.2)


def _som_coracao():
    lub = _batida(58, 0.14, 12)
    dub = _batida(50, 0.12, 13)
    return _normalizar(_passa_baixa(_somar((0.0, lub, 1.0), (0.17, dub, 0.7)), 0.25, 1.4), 0.9)


def _som_vulto():
    n = int(0.9 * TAXA_SINTESE)
    grave = [math.sin(2 * math.pi * 62 * i / TAXA_SINTESE) * (0.55 + 0.45 * math.sin(2 * math.pi * 23 * i / TAXA_SINTESE))
             for i in range(n)]
    return _normalizar(_somar((0.0, _env(grave, sino=True), 1.0), (0.0, _env(_ruido(0.9, 101, 0.12), sino=True), 0.9)), 0.8)


def _som_arrastar():
    n = int(0.25 * TAXA_SINTESE)
    base = _ruido(0.25, 103, 0.13)
    return _normalizar(_env([s * (0.6 + 0.4 * math.sin(2 * math.pi * 28 * i / TAXA_SINTESE)) for i, s in enumerate(base[:n])],
                            sino=True), 0.55)


def _som_voz(n_silabas):
    f = [(600, 1000), (500, 900), (700, 1100), (450, 800)]
    return [sintetizar_voz(n, 105, f, 0.24, ruido=0.03, semente=s) for n, s in n_silabas]


def _som_zumbido_eletrico():
    n = int(1.6 * TAXA_SINTESE)
    s = [math.sin(2 * math.pi * 120 * i / TAXA_SINTESE) + 0.5 * math.sin(2 * math.pi * 240 * i / TAXA_SINTESE)
         + 0.2 * math.sin(2 * math.pi * 360 * i / TAXA_SINTESE) for i in range(n)]
    return _fade(_normalizar(s, 0.4), 0.25)


def _som_alerta():
    sub = _env(_varredura(180, 420, 0.35, 3), ataque=0.01, queda=3)
    return _normalizar(_somar((0.0, sub, 0.8), (0.0, _env(_somar((0.0, _tom(466, 0.5), 1.0), (0.0, _tom(494, 0.5), 1.0)), queda=4), 0.5),
                              (0.0, _env(_ruido(0.1, 111, 0.9), queda=40), 0.6)), 0.85)


def _som_gotejar():
    return _normalizar(_somar((0.0, _env(_varredura(1400, 700, 0.09), queda=40), 1.0),
                              (0.12, _env(_varredura(900, 500, 0.12), queda=30), 0.35)), 0.45)


def _som_revelacao():
    acorde = [(0.0, f) for f in (110.0, 130.8, 164.8, 220.0)]
    pad = _somar(*[(o, _env(_tom(f, 3.0), ataque=0.8, sino=True), 0.7) for o, f in acorde])
    return _fade(_normalizar(_somar((0.0, pad, 1.0), (0.0, _batida(50, 0.6, 14), 0.8)), 0.8), 0.2)


def _som_levantar():
    return _normalizar(_somar((0.0, _env(_ruido(0.5, 121, 0.3), sino=True), 0.7),
                              (0.4, _som_passo(7, 66, 0.3), 0.7)), 0.6)


def _som_iniciar():
    return _normalizar(_somar((0.0, _batida(60, 0.6, 15), 1.0), (0.0, _sino([220, 330, 440], 1.0, 4), 0.4)), 0.9)


def _som_sussurro():
    return [sintetizar_voz(n, 100, [(350, 2300), (550, 1900), (300, 2600)], 0.15, sussurro=True, semente=s)
            for n, s in ((8, 20), (10, 21))]


_BUILDERS = {
    "alerta": lambda: [_som_alerta()],
    "gotejar": lambda: [_som_gotejar()],
    "revelacao": lambda: [_som_revelacao()],
    "levantar": lambda: [_som_levantar()],
    "iniciar": lambda: [_som_iniciar()],
    "sussurro": _som_sussurro,
    "guarda_passo": lambda: [_normalizar(_som_passo(s, 48, 0.2), 0.8) for s in (8, 9)],
    "passo": lambda: [_som_passo(s, g, a) for s, g, a in ((1, 70, 0.28), (2, 62, 0.24), (3, 78, 0.32))],
    "passo_furtivo": lambda: [_normalizar(_som_passo(s, 55, 0.14), 0.35) for s in (4, 5)],
    "agachar": lambda: [_normalizar(_env(_ruido(0.14, 7, 0.5), sino=True), 0.4)],
    "pilula": lambda: [_som_pilula()],
    "dano": lambda: [_som_dano()],
    "coletar": lambda: [_som_coletar()],
    "chave": lambda: [_som_chave()],
    "papel": lambda: [_som_papel()],
    "porta_abrir": lambda: [_som_porta_abrir()],
    "porta_trancada": lambda: [_som_porta_trancada()],
    "valvula": lambda: [_som_valvula()],
    "disjuntor_ok": lambda: [_som_disjuntor_ok()],
    "disjuntor_erro": lambda: [_som_disjuntor_erro()],
    "golpe": lambda: [_som_golpe()],
    "arrombar": lambda: [_som_arrombar()],
    "arremesso": lambda: [_som_arremesso()],
    "clang": lambda: [_som_clang()],
    "preso": lambda: [_som_preso()],
    "tabua": lambda: [_som_tabua()],
    "alarme": lambda: [_som_alarme()],
    "alarme_bip": lambda: [_som_alarme_bip()],
    "sucesso": lambda: [_som_sucesso()],
    "fase_completa": lambda: [_som_fase_completa()],
    "game_over": lambda: [_som_game_over()],
    "clique": lambda: [_som_clique()],
    "final": lambda: [_som_final()],
    "coracao": lambda: [_som_coracao()],
    "vulto": lambda: [_som_vulto()],
    "arrastar": lambda: [_som_arrastar()],
    "voz": lambda: _som_voz(((4, 1), (6, 2), (8, 3))),
    "chiado_gas": lambda: [_chiado(1.0, 21)],
    "zumbido_eletrico": lambda: [_som_zumbido_eletrico()],
}


def _gerar_musica(caminho, dur=16, taxa=11025):
    """Drone sombrio em loop perfeito (frequências com número inteiro de ciclos em `dur`)."""
    n = dur * taxa

    def f_inteira(f):
        return round(f * dur) / dur

    camadas = [(55.0, 0.50), (82.4, 0.30), (110.0, 0.22), (164.8, 0.10), (165.6, 0.10)]
    lfo1, lfo2 = 1 / dur, 2 / dur
    rng = random.Random(8)
    ruido, y = [], 0.0
    for _ in range(n):
        y += 0.02 * (rng.uniform(-1, 1) - y)
        ruido.append(y)
    pings = [(3.0, 880.0), (7.5, 622.3), (11.0, 740.0), (13.6, 466.2)]
    amostras = array.array("h")
    for i in range(n):
        t = i / taxa
        s = 0.0
        for f, g in camadas:
            s += g * math.sin(2 * math.pi * f_inteira(f) * t)
        s *= 0.75 + 0.25 * math.sin(2 * math.pi * lfo1 * t) + 0.1 * math.sin(2 * math.pi * lfo2 * t + 1.3)
        s += ruido[i] * 6.0 * (0.6 + 0.4 * math.sin(2 * math.pi * lfo2 * t))
        for p0, pf in pings:
            dt = t - p0
            if 0 <= dt < 2.2:
                s += 0.07 * math.sin(2 * math.pi * pf * dt) * math.exp(-dt * 2.6)
        amostras.append(int(max(-1.0, min(1.0, s * 0.45)) * 30000))
    with wave.open(caminho, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes(amostras.tobytes())


def _som_para_sound(amostras, cfg):
    freq, _fmt, canais = cfg
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


def _achar_pasta_sons():
    aqui = os.path.dirname(os.path.abspath(__file__))
    for base in (aqui, os.path.join(aqui, "..")):
        p = os.path.normpath(os.path.join(base, "assets", "sons"))
        if os.path.isdir(p):
            return p
    return None


def exportar_wavs(pasta, taxa=22050):
    """Grava todos os sons do jogo como .wav (python audio.py exportar). Edite/troque à vontade."""
    os.makedirs(pasta, exist_ok=True)
    nomes = []
    for nome, construtor in _BUILDERS.items():
        for i, amostras in enumerate(construtor()):
            n_in = len(amostras)
            n_out = max(2, int(n_in * taxa / TAXA_SINTESE))
            passo = (n_in - 1) / (n_out - 1)
            dados = array.array("h")
            for j in range(n_out):
                p = j * passo
                k = int(p)
                a = amostras[k]
                b = amostras[k + 1] if k + 1 < n_in else a
                dados.append(int(max(-1.0, min(1.0, a + (b - a) * (p - k))) * 30000))
            arquivo = nome + ("" if i == 0 else f"_{i + 1}") + ".wav"
            with wave.open(os.path.join(pasta, arquivo), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(taxa)
                w.writeframes(dados.tobytes())
            nomes.append(arquivo)
    _gerar_musica(os.path.join(pasta, "musica_ambiente.wav"), taxa=22050)
    return nomes


class SomJogo:
    """Efeitos e música do jogo. Se não houver áudio no computador, tudo vira silêncio sem erro."""

    VOLUME_MUSICA = 0.32

    def __init__(self):
        self.ativo = False
        self._cfg = None
        self._cache = {}
        self._prox = {}
        self._musica_tocando = False
        self._sanidade_ant = None
        self._intro_tocada = set()
        self._msg_ant = None
        self._susp = {}

    def iniciar(self):
        if self.ativo:
            return True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            cfg = pygame.mixer.get_init()
            if cfg and cfg[1] == -16 and cfg[2] in (1, 2):
                self._cfg = cfg
                pygame.mixer.set_num_channels(max(16, pygame.mixer.get_num_channels()))
                self.ativo = True
        except Exception as erro:
            print(f"[sons] desativado: {erro}")
            self.ativo = False
        return self.ativo

    def _variantes(self, nome):
        v = self._cache.get(nome)
        if v is None:
            v = []
            pasta = _achar_pasta_sons()
            if pasta:   # arquivos em assets/sons têm prioridade: nome.wav, nome_2.wav, nome_3.wav...
                for sufixo in ("", "_2", "_3", "_4"):
                    for ext in (".wav", ".ogg"):
                        caminho = os.path.join(pasta, nome + sufixo + ext)
                        if os.path.exists(caminho):
                            try:
                                v.append(pygame.mixer.Sound(caminho))
                            except Exception as erro:
                                print(f"[sons] não carregou {caminho}: {erro}")
            if not v:
                v = [_som_para_sound(a, self._cfg) for a in _BUILDERS[nome]()]
            self._cache[nome] = v
        return v

    def pre_carregar(self, nomes=("passo", "passo_furtivo", "coletar", "pilula", "dano", "porta_abrir")):
        if not self.ativo:
            return
        for n in nomes:
            try:
                self._variantes(n)
            except Exception as erro:
                print(f"[sons] falhou ao gerar '{n}': {erro}")

    # ---- efeitos -----------------------------------------------------------
    def tocar(self, nome, ganho=1.0, esq=None, dir_=None):
        if not self.ativo:
            return None
        try:
            canal = random.choice(self._variantes(nome)).play()
        except Exception as erro:
            print(f"[sons] erro em '{nome}': {erro}")
            return None
        if canal is not None:
            e = ganho if esq is None else esq
            d = ganho if dir_ is None else dir_
            canal.set_volume(min(1.0, e), min(1.0, d))
        return canal

    def tocar_pos(self, nome, origem, ouvinte, alcance, ganho=1.0):
        """Som com direção e distância (esquerda/direita + volume)."""
        if not self.ativo:
            return None
        esq, dir_, _prox = mixagem_estereo(origem, ouvinte, alcance)
        esq *= ganho
        dir_ *= ganho
        if max(esq, dir_) < 0.02:
            return None
        return self.tocar(nome, esq=esq, dir_=dir_)

    def _a_cada(self, chave, tempo_ms, intervalo_ms):
        if tempo_ms >= self._prox.get(chave, 0):
            self._prox[chave] = tempo_ms + intervalo_ms
            return True
        return False

    def cada(self, chave, tempo_ms, intervalo_ms):
        """True no máximo uma vez por `intervalo_ms` para a mesma `chave`."""
        return self._a_cada(chave, tempo_ms, intervalo_ms)

    def musica(self, ligada=True, volume=None):
        if not self.ativo:
            return
        try:
            if ligada and not self._musica_tocando:
                pasta = _achar_pasta_sons()
                caminho = os.path.join(pasta, "musica_ambiente.wav") if pasta else ""
                if not (caminho and os.path.exists(caminho)):
                    caminho = os.path.join(tempfile.gettempdir(), "eco_do_abismo_ambiente_v1.wav")
                    if not os.path.exists(caminho):
                        _gerar_musica(caminho)
                pygame.mixer.music.load(caminho)
                pygame.mixer.music.play(-1)
                self._musica_tocando = True
            elif not ligada and self._musica_tocando:
                pygame.mixer.music.fadeout(600)
                self._musica_tocando = False
            if volume is not None:
                pygame.mixer.music.set_volume(volume)
        except Exception as erro:
            print(f"[sons] música indisponível: {erro}")

    def parar_tudo(self):
        if not self.ativo:
            return
        try:
            pygame.mixer.stop()
            self.musica(False)
        except Exception:
            pass

    def atualizar(self, nivel, contexto, jogador, tempo_ms):
        if not self.ativo:
            return
        self.musica(True, 0.0 if nivel == 7 else self.VOLUME_MUSICA)

        # passos
        if getattr(jogador, "andando", False):
            if jogador.agachado:
                if self._a_cada("passo", tempo_ms, 520):
                    self.tocar("passo_furtivo", 0.35)
            elif self._a_cada("passo", tempo_ms, 330):
                self.tocar("passo", 0.35 if nivel == 7 else 0.55)

        # levou dano (queda brusca de sanidade: vulto, susto, guarda...)
        san = getattr(jogador, "sanidade", 100)
        if self._sanidade_ant is not None and self._sanidade_ant - san >= 1.0:
            self.tocar("dano", 0.9)

        # coração acelerado com a sanidade baixa
        if san < 30 and self._a_cada("coracao", tempo_ms, 700 + int(san * 20)):
            self.tocar("coracao", 0.5 + 0.5 * (1 - san / 30))

        # clima de cada sala
        if nivel == 5 and contexto.get("tint_gas") and self._a_cada("gas", tempo_ms, 1100):
            self.tocar("chiado_gas", 0.25)
        elif nivel == 9 and self._a_cada("zumbido_eletrico", tempo_ms, 3000):
            ligado = contexto.get("puzzle_disjuntores") is not None and not contexto["puzzle_disjuntores"].resolvido
            if ligado:
                self.tocar("zumbido_eletrico", 0.18)
        elif nivel == 10:
            fuzil = contexto.get("puzzle_fuzil")
            if fuzil is not None and fuzil.consertado and self._a_cada("alarme", tempo_ms, 1450):
                self.tocar("alarme", 0.45)
        elif nivel == 11 and self._a_cada("alarme_bip", tempo_ms, 600):
            self.tocar("alarme_bip", 0.35)

        # a VOZ narra (menos na sala 7, que tem as vozes próprias)
        if nivel != 7:
            if id(contexto) not in self._intro_tocada:
                self._intro_tocada.add(id(contexto))
                intro = contexto.get("mensagem_intro") or ""
                if intro.startswith("A VOZ"):
                    self.tocar("voz", 0.8)
            msg = contexto.get("mensagem_temporaria")
            if msg != self._msg_ant and msg and tempo_ms < contexto.get("mensagem_temporaria_expira", 0):
                if str(msg).startswith("A VOZ"):
                    self.tocar("voz", 0.8)
            self._msg_ant = msg

        if nivel == 12 and contexto.get("voz_revelada") and self.cada("revelacao", tempo_ms, 10 ** 9):
            self.tocar("revelacao", 0.9)

        # prisão: guardas, goteiras e sussurros das celas
        if nivel == 8:
            centro = jogador.get_rect().center
            for g in contexto.get("guardas", []):
                if g.suspeita >= 0.7 and self._susp.get(id(g), 0) < 0.7:
                    self.tocar("alerta", 0.9)
                self._susp[id(g)] = g.suspeita
                movendo = g.estado in ("patrulha", "investigando", "voltando")
                if movendo and self._a_cada(("gp", id(g)), tempo_ms, 480):
                    self.tocar_pos("guarda_passo", (g.x, g.y), centro, 700, 0.8)
            if self._a_cada("gota", tempo_ms, random.randint(2500, 6000)):
                self.tocar("gotejar", 0.4)
            if jogador.x < 1700 and self._a_cada("sussurro", tempo_ms, random.randint(14000, 24000)):
                self.tocar("sussurro", 0.25)

        # vultos por perto
        if nivel in (6, 9):
            centro = jogador.get_rect().center
            for v in contexto.get("vultos", []):
                if v.ativo(tempo_ms) and self._a_cada(("vulto", id(v)), tempo_ms, 3800):
                    self.tocar_pos("vulto", v.get_rect().center, centro, 650, 0.9)

        self._sanidade_ant = san


sons = SomJogo()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "exportar":
        pygame.init()
        destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sons")
        lista = exportar_wavs(destino)
        print(f"{len(lista)} sons + música gravados em {destino}")
