import pygame
import random
import math

from configuracoes import LARGURA, ALTURA, AZUL_ESCURO, BRANCO, CINZA_BORDA, VERDE_GAS, VERMELHO_ALARME
from nivel import Sala
from personagem import Inimigo, GuardaPrisao
from itens import gerar_frascos_na_sala, Dica, Documento, Chave, MascaraGas
from interface_usuario import (desenhar_hud, desenhar_mensagem_contextual, desenhar_flash_detectado,
                                desenhar_barra_oxigenio, desenhar_overlay_gas,
                                desenhar_escuridao_com_lanterna)
from configuracoes import CIANO_BRILHO
from itens import FrascoSanidade
from audio import AudioEspacial
from puzzle import (CaixaArrastavel, PuzzleCaixaFerramentas, PuzzlePainelSenha, PuzzleCofre,
                    PuzzleValvulas, PuzzleFuzil, PuzzleDisjuntores)

def _transicao_padrao(contexto, jogador):
    sala = contexto["sala"]
    return sala.porta_aberta and sala.jogador_na_porta(jogador)


def _estado_base(sala, nivel, **kwargs):
    contexto = {
        "sala": sala,
        "nivel": nivel,
        "frascos": [],
        "cameras": [],
        "guardas": [],
        "vultos": [],
        "caixas": [],
        "objetos": [],
        "duto": None,
        "puzzle_modal": None,
        "taxa_dano_sanidade": 0.008,
        "mensagem_intro": None,
        "duracao_intro": 4500,
        "tempo_inicio": pygame.time.get_ticks(),
        "final": False,
        "mensagem_final": "Fim da demonstração.",
        "usa_oxigenio": False,
        "usa_lanterna": False,
        "tint_gas": False,
        "mensagem_temporaria": None,
        "mensagem_temporaria_expira": 0,
        "ao_interagir": None,
        "ao_atualizar": None,
        "ao_desenhar_extra": None,
        "ao_tecla_down": None,
        "texto_status": None,
        "condicao_transicao": _transicao_padrao,
    }
    contexto.update(kwargs)
    return contexto


def _definir_mensagem(contexto, texto, tempo_ms, duracao_ms=3000):
    contexto["mensagem_temporaria"] = texto
    contexto["mensagem_temporaria_expira"] = tempo_ms + duracao_ms


def _perto(jogador, pos, raio):
    centro = jogador.get_rect().center
    return math.hypot(centro[0] - pos[0], centro[1] - pos[1]) <= raio

def nivel_1(jogador, resetar_jogador=False):
    jogador.sanidade = 100
    jogador.tem_pe_de_cabra = False
    jogador.agachado = False

    sala = Sala(1400, 900, ponto_entrada=(90, 430), largura_tela=LARGURA, altura_tela=ALTURA)
    jogador.x, jogador.y = sala.ponto_entrada

    frascos = gerar_frascos_na_sala(1)

    senha = ['7', '3', '9', '1']
    posicoes = [(340, 160), (1120, 220), (1180, 740), (420, 780)]
    dicas = [Dica(x, y, senha[i], i) for i, (x, y) in enumerate(posicoes)]
    puzzle_senha = PuzzlePainelSenha(senha)

    contexto = _estado_base(
        sala, 1,
        frascos=frascos,
        objetos=dicas,
        taxa_dano_sanidade=0.004,
        mensagem_intro="Sua sanidade cai com o tempo. Tome as pílulas espalhadas pela sala "
                        "para recuperá-la — aqui ela ainda cai bem devagar.",
    )
    contexto["puzzle_senha"] = puzzle_senha

    def ao_interagir(contexto, jogador):
        for dica in contexto["objetos"]:
            if not dica.coletada and jogador.get_rect().colliderect(dica.rect.inflate(16, 16)):
                dica.coletada = True
                contexto["puzzle_senha"].registrar_pista(dica.indice, dica.valor)

        sala = contexto["sala"]
        if not sala.porta_aberta and sala.jogador_na_porta(jogador):
            if contexto["puzzle_senha"].tentar_abrir():
                sala.porta_aberta = True

    def texto_status(contexto):
        return f'SENHA DA PORTA: {contexto["puzzle_senha"].texto_progresso()}'

    contexto["ao_interagir"] = ao_interagir
    contexto["texto_status"] = texto_status
    return contexto


def nivel_2(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.tem_pe_de_cabra = False
    jogador.agachado = False

    sala = Sala(1300, 850, ponto_entrada=(90, 405), largura_tela=LARGURA, altura_tela=ALTURA)
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = False

    caixas = [
        CaixaArrastavel(1080, 560),
        CaixaArrastavel(1080, 615),
    ]
    rect_placa = pygame.Rect(1075, 545, 90, 90)
    cofre = PuzzleCofre(rect_placa, palavra_chave="ABISMO")

    bilhete = Documento(300, 700, 'Um bilhete rasgado: "...a senha do cofre é ABISMO."')
    chave = Chave(1100, 590, rotulo="Chave da Porta")

    contexto = _estado_base(
        sala, 2,
        caixas=caixas,
        objetos=[bilhete],
        mensagem_intro='A VOZ: "A saída está trancada. Procure a chave nesta sala."',
    )
    contexto["cofre"] = cofre
    contexto["chave"] = chave
    contexto["sabe_palavra_chave"] = False
    contexto["tem_chave"] = False

    def ao_interagir(contexto, jogador):
        if not bilhete.coletado and jogador.get_rect().colliderect(bilhete.rect.inflate(16, 16)):
            bilhete.coletado = True
            contexto["sabe_palavra_chave"] = True
            _definir_mensagem(contexto, bilhete.texto, pygame.time.get_ticks(), 4000)

        cofre = contexto["cofre"]
        cofre.checar_revelado(contexto["caixas"])
        if cofre.revelado and not cofre.aberto and jogador.get_rect().colliderect(cofre.rect_placa.inflate(20, 20)):
            if cofre.tentar_abrir(contexto["sabe_palavra_chave"]):
                contexto["tem_chave"] = True
                chave.coletada = True
            elif not contexto["sabe_palavra_chave"]:
                _definir_mensagem(contexto, "O cofre pede uma palavra-chave que você ainda não sabe.", pygame.time.get_ticks())

        sala = contexto["sala"]
        if contexto["tem_chave"] and not sala.porta_aberta and sala.jogador_na_porta(jogador):
            sala.porta_aberta = True

    def ao_desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        contexto["cofre"].checar_revelado(contexto["caixas"])
        contexto["cofre"].desenhar(surf, fonte)
        if not contexto["chave"].coletada:
            contexto["chave"].desenhar(surf)

    def texto_status(contexto):
        if contexto["tem_chave"]:
            return "VOCÊ TEM: Chave da Porta"
        return None

    contexto["ao_interagir"] = ao_interagir
    contexto["ao_desenhar_extra"] = ao_desenhar_extra
    contexto["texto_status"] = texto_status
    return contexto


def nivel_3(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.tem_pe_de_cabra = False
    jogador.agachado = False

    sala = Sala(1300, 850, ponto_entrada=(90, 405), largura_tela=LARGURA, altura_tela=ALTURA)
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = False

    documentos = [
        Documento(300, 220, 'Relatório: "Paciente 724 segue instável. Monitorar a Voz."'),
        Documento(950, 260, 'Ficha rasgada: "...não é a primeira vez que ele foge."'),
        Documento(650, 700, 'Anotação: "Se ele perguntar quem fala com ele, não responda."'),
        Documento(1150, 650, "Um mapa antigo da instalação, com a saída marcada.", especial=True),
    ]

    contexto = _estado_base(
        sala, 3,
        objetos=documentos,
        mensagem_intro='A VOZ: "Continue procurando. A saída está em algum lugar aqui."',
    )
    contexto["tem_mapa"] = False

    def ao_interagir(contexto, jogador):
        for doc in contexto["objetos"]:
            if not doc.coletado and jogador.get_rect().colliderect(doc.rect.inflate(16, 16)):
                doc.coletado = True
                _definir_mensagem(contexto, doc.texto, pygame.time.get_ticks(), 4000)
                if doc.especial:
                    contexto["tem_mapa"] = True
                    contexto["sala"].porta_aberta = True

    def texto_status(contexto):
        if contexto["tem_mapa"]:
            return "VOCÊ TEM: Mapa da instalação (a saída foi liberada)"
        lidos = sum(1 for d in contexto["objetos"] if d.coletado)
        return f"Documentos lidos: {lidos}/{len(contexto['objetos'])}"

    contexto["ao_interagir"] = ao_interagir
    contexto["texto_status"] = texto_status
    return contexto

def nivel_4(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.tem_pe_de_cabra = False
    jogador.agachado = False

    sala = Sala(1500, 950, ponto_entrada=(90, 470), largura_tela=LARGURA, altura_tela=ALTURA)
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = True  

    caixas = [
        CaixaArrastavel(760, 700),
        CaixaArrastavel(760, 755),
    ]
    caixa_ferramentas = pygame.Rect(770, 640, 30, 20)
    puzzle_caixa = PuzzleCaixaFerramentas(LARGURA, ALTURA)

    duto = {
        "corredor": pygame.Rect(1050, 90, 380, 60),
        "porta_entrada_aberta": False,
        "porta_saida_aberta": False,
        "rect_entrada": pygame.Rect(1050, 90, 15, 60),
        "rect_saida": pygame.Rect(1415, 90, 15, 60),
    }

    contexto = _estado_base(
        sala, 4,
        caixas=caixas,
        duto=duto,
        mensagem_intro='A VOZ: "Depressa! Siga o corredor"',
    )
    contexto["puzzle_modal"] = puzzle_caixa
    contexto["caixa_ferramentas"] = caixa_ferramentas
    contexto["saiu_do_duto"] = False

    def ao_interagir(contexto, jogador):
        rect_p = jogador.get_rect()
        duto = contexto["duto"]
        pf = contexto["puzzle_modal"]

        if rect_p.colliderect(duto["rect_entrada"].inflate(25, 25)):
            if jogador.tem_pe_de_cabra and not duto["porta_entrada_aberta"]:
                duto["porta_entrada_aberta"] = True
        elif rect_p.colliderect(duto["rect_saida"].inflate(25, 25)):
            if jogador.tem_pe_de_cabra and not duto["porta_saida_aberta"]:
                duto["porta_saida_aberta"] = True
        elif rect_p.colliderect(contexto["caixa_ferramentas"].inflate(15, 15)) and not jogador.tem_pe_de_cabra:
            coberta = any(c.rect.colliderect(contexto["caixa_ferramentas"]) for c in contexto["caixas"])
            if not coberta and not pf.ativo and not pf.resolvido:
                pf.ativo = True

    def ao_atualizar(contexto, jogador, teclas, tempo_ms):
        duto = contexto["duto"]

        dentro_do_duto = duto["corredor"].contains(jogador.get_rect())

        if contexto["puzzle_modal"].resolvido and not jogador.tem_pe_de_cabra:
            jogador.tem_pe_de_cabra = True

        if (not contexto["saiu_do_duto"] and duto["porta_saida_aberta"]
                and jogador.x > duto["rect_saida"].x):
            contexto["saiu_do_duto"] = True
            contexto["final"] = True

    contexto["ao_interagir"] = ao_interagir
    contexto["ao_atualizar"] = ao_atualizar
    return contexto


def _desenhar_armario(surf, rect, destrancado, mascara, fonte):
    pygame.draw.rect(surf, (60, 66, 78), rect, border_radius=4)
    pygame.draw.rect(surf, (30, 35, 45), rect, width=3, border_radius=4)
    if destrancado:
        pygame.draw.rect(surf, (18, 22, 30), rect.inflate(-24, -20), border_radius=3)
        mascara.desenhar(surf)
    else:
        pygame.draw.line(surf, (30, 35, 45), (rect.centerx, rect.y + 4), (rect.centerx, rect.bottom - 4), 3)
        pygame.draw.rect(surf, (150, 150, 160), (rect.centerx - 12, rect.centery - 8, 5, 16))
        pygame.draw.rect(surf, (150, 150, 160), (rect.centerx + 7, rect.centery - 8, 5, 16))
    cor_luz = VERDE_GAS if destrancado else VERMELHO_ALARME
    pygame.draw.circle(surf, cor_luz, (rect.right - 12, rect.y + 12), 5)
    txt = fonte.render("ARMÁRIO", True, CINZA_BORDA)
    surf.blit(txt, txt.get_rect(midbottom=(rect.centerx, rect.y - 6)))


def _desenhar_vazamento(surf, vazamento, tempo_ms, fonte):
    x, y = vazamento.pos
    pygame.draw.rect(surf, (80, 85, 95), (x - 80, y - 8, 150, 16))
    pygame.draw.rect(surf, (40, 45, 55), (x - 80, y - 8, 150, 16), width=2)
    if not vazamento.consertado:
        nuvem = pygame.Surface((220, 220), pygame.SRCALPHA)
        for i in range(3):
            raio = 40 + int(14 * math.sin(tempo_ms / 300 + i * 2))
            pygame.draw.circle(nuvem, (*VERDE_GAS, 55), (110 + (i - 1) * 25, 110 - i * 8), raio)
        surf.blit(nuvem, (x - 110, y - 110))
    vazamento.desenhar(surf, fonte)


def nivel_5(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.tem_pe_de_cabra = False
    jogador.agachado = False
    jogador.oxigenio = 100.0

    TAXA_OXIGENIO = 2.5          # pontos por segundo enquanto as válvulas não foram giradas
    RECUPERA_OXIGENIO = 12.0     # pontos por segundo depois que o ar volta
    DANO_SEM_OXIGENIO = 5.0      # sanidade perdida por segundo com oxigênio zerado

    rect_armario = pygame.Rect(980, 780, 120, 80)
    sala = Sala(1400, 900, ponto_entrada=(90, 430), largura_tela=LARGURA, altura_tela=ALTURA,
                obstaculos=[rect_armario])
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = False

    valvulas = PuzzleValvulas([(300, 190), (1000, 230), (560, 700)])
    valvulas.raio_interacao = 80
    mascara = MascaraGas(rect_armario.centerx - 13, rect_armario.y + 30)
    vazamento = PuzzleFuzil((1290, 250), golpes_necessarios=3)
    vazamento.raio_interacao = 90

    contexto = _estado_base(
        sala, 5,
        mensagem_intro='A VOZ: "O ar está acabando. Ache as três válvulas."',
        usa_oxigenio=True,
        tint_gas=True,
    )
    contexto["valvulas"] = valvulas
    contexto["mascara"] = mascara
    contexto["vazamento"] = vazamento
    contexto["rect_armario"] = rect_armario
    contexto["tem_mascara"] = False
    contexto["_ultimo_tempo"] = pygame.time.get_ticks()

    def ao_interagir(contexto, jogador):
        agora = pygame.time.get_ticks()
        valvulas = contexto["valvulas"]

        valvula = valvulas.valvula_proxima(jogador)
        if valvula:
            valvulas.girar(valvula)
            if valvulas.todas_giradas():
                contexto["mascara"].destrancado = True
                _definir_mensagem(contexto, "Você ouviu um estalo. O armário foi destrancado.", agora)
            else:
                giradas = sum(1 for v in valvulas.valvulas if v["girada"])
                _definir_mensagem(contexto, f"Válvula girada! ({giradas}/{len(valvulas.valvulas)})", agora)
            return

        if jogador.get_rect().colliderect(contexto["rect_armario"].inflate(30, 30)):
            if not contexto["mascara"].destrancado:
                _definir_mensagem(contexto, "O armário está trancado. Gire as 3 válvulas.", agora)
            elif not contexto["tem_mascara"]:
                contexto["tem_mascara"] = True
                contexto["mascara"].coletada = True
                _definir_mensagem(contexto, "Você pegou a máscara de gás!", agora)
            else:
                _definir_mensagem(contexto, "O armário está vazio.", agora)
            return

        vazamento = contexto["vazamento"]
        if vazamento.perto(jogador) and not vazamento.consertado:
            if not contexto["tem_mascara"]:
                _definir_mensagem(contexto, "O gás é denso demais. Você precisa da máscara.", agora)
            elif vazamento.golpear():
                contexto["sala"].porta_aberta = True
                contexto["tint_gas"] = False
                _definir_mensagem(contexto, "Vazamento consertado! A saída foi liberada.", agora, 4000)

    def ao_atualizar(contexto, jogador, teclas, tempo_ms):
        dt = min((tempo_ms - contexto["_ultimo_tempo"]) / 1000, 0.1)
        contexto["_ultimo_tempo"] = tempo_ms

        if contexto["valvulas"].todas_giradas():
            jogador.oxigenio = min(100.0, jogador.oxigenio + RECUPERA_OXIGENIO * dt)
        else:
            jogador.oxigenio = max(0.0, jogador.oxigenio - TAXA_OXIGENIO * dt)

        if jogador.oxigenio <= 0:
            jogador.dano_sanidade(DANO_SEM_OXIGENIO * dt)

        sala = contexto["sala"]
        if sala.porta_aberta and sala.jogador_na_porta(jogador):
            contexto["final"] = True

    def ao_desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        _desenhar_vazamento(surf, contexto["vazamento"], tempo_ms, fonte)
        contexto["valvulas"].desenhar(surf)
        _desenhar_armario(surf, contexto["rect_armario"], contexto["mascara"].destrancado,
                          contexto["mascara"], fonte)

    def texto_status(contexto):
        if contexto["vazamento"].consertado:
            return "Vazamento consertado (a saída foi liberada)"
        if contexto["tem_mascara"]:
            return "VOCÊ TEM: Máscara de gás (conserte o vazamento)"
        giradas = sum(1 for v in contexto["valvulas"].valvulas if v["girada"])
        return f"Válvulas giradas: {giradas}/{len(contexto['valvulas'].valvulas)}"

    contexto["ao_interagir"] = ao_interagir
    contexto["ao_atualizar"] = ao_atualizar
    contexto["ao_desenhar_extra"] = ao_desenhar_extra
    contexto["texto_status"] = texto_status
    return contexto


def _desenhar_entulho(surf, entulho, detritos):
    for r in entulho:
        pygame.draw.rect(surf, (105, 70, 45), r, border_radius=4)
        for x in range(r.x + 40, r.right - 10, 40):
            pygame.draw.line(surf, (65, 40, 25), (x, r.y + 3), (x, r.bottom - 3), 2)
        pygame.draw.rect(surf, (65, 40, 25), r, width=3, border_radius=4)
    for (x, y, w, h) in detritos:
        pygame.draw.rect(surf, (60, 64, 74), (x, y, w, h))


def _desenhar_escuridao_corredor(surf, sala, jogador, tempo_ms):
    """Escuridão desenhada dentro do mundo, para o HUD continuar legível por cima dela."""
    cam_x, cam_y = sala.calcular_camera(jogador)
    centro = jogador.get_rect().center
    escuro = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    raio = 175 + int(5 * math.sin(tempo_ms / 160))
    desenhar_escuridao_com_lanterna(escuro, (centro[0] - cam_x, centro[1] - cam_y),
                                    LARGURA, ALTURA, ligada=True, raio=raio)
    surf.blit(escuro, (cam_x, cam_y))


def nivel_6(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.tem_pe_de_cabra = False
    jogador.agachado = False

    # corredor (x 40..1100, y 340..560) seguido de uma área aberta e abandonada
    paredes_corredor = [
        pygame.Rect(40, 40, 1060, 300),
        pygame.Rect(40, 560, 1060, 300),
    ]
    entulho = [
        pygame.Rect(1400, 200, 160, 100),
        pygame.Rect(1450, 580, 100, 120),
        pygame.Rect(1750, 320, 100, 220),
        pygame.Rect(1950, 180, 160, 110),
        pygame.Rect(1980, 600, 160, 110),
    ]
    sala = Sala(2400, 900, ponto_entrada=(90, 400), largura_tela=LARGURA, altura_tela=ALTURA,
                obstaculos=paredes_corredor + entulho)
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = True

    rng = random.Random(6)
    detritos = []
    for _ in range(45):
        d = (rng.randint(1130, 2330), rng.randint(60, 830), rng.randint(6, 18), rng.randint(4, 10))
        if not any(pygame.Rect(d).colliderect(r) for r in entulho):
            detritos.append(d)

    vultos = [
        Inimigo(1650, 120, velocidade=2.6, atraso_ms=0, lado_desvio=1),
        Inimigo(1650, 740, velocidade=2.9, atraso_ms=600, lado_desvio=-1),
        Inimigo(2050, 440, velocidade=2.3, atraso_ms=1200, lado_desvio=1),
    ]

    contexto = _estado_base(
        sala, 6,
        vultos=vultos,
        mensagem_intro="Você tira a máscara de gás. O corredor está escuro.",
        condicao_transicao=lambda contexto, jogador: False,
    )
    contexto["entulho"] = entulho
    contexto["detritos"] = detritos
    contexto["vultos_surgiram"] = False
    contexto["ultimo_dano"] = -10 ** 9

    def ao_atualizar(contexto, jogador, teclas, tempo_ms):
        sala = contexto["sala"]
        vultos = contexto["vultos"]

        if not contexto["vultos_surgiram"] and jogador.get_rect().centerx > 1250:
            contexto["vultos_surgiram"] = True
            for v in vultos:
                v.surgir(tempo_ms)
            _definir_mensagem(contexto, 'A VOZ: "Eles acordaram! Corra para a porta!"', tempo_ms, 4000)

        paredes = sala.paredes_colisao()
        for v in vultos:
            v.perseguir(jogador, paredes, tempo_ms, vultos)
            if v.tentar_atacar(jogador, tempo_ms):
                contexto["ultimo_dano"] = tempo_ms

        if sala.jogador_na_porta(jogador):
            contexto["final"] = True

    def ao_desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        sala = contexto["sala"]
        _desenhar_entulho(surf, contexto["entulho"], contexto["detritos"])
        for v in contexto["vultos"]:
            v.desenhar_corpo(surf, tempo_ms)

        _desenhar_escuridao_corredor(surf, sala, jogador, tempo_ms)

        for v in contexto["vultos"]:
            v.desenhar_olhos(surf, tempo_ms)

        porta = sala.rect_porta
        luz = pygame.Surface((160, 160), pygame.SRCALPHA)
        pulso = 55 + int(20 * math.sin(tempo_ms / 300))
        pygame.draw.circle(luz, (*VERDE_GAS, pulso), (80, 80), 78)
        pygame.draw.circle(luz, (*VERDE_GAS, pulso + 40), (80, 80), 36)
        surf.blit(luz, (porta.centerx - 80, porta.centery - 80))

        decorrido = tempo_ms - contexto["ultimo_dano"]
        if decorrido < 250:
            cx, cy = jogador.get_rect().center
            marca = pygame.Surface((170, 170), pygame.SRCALPHA)
            pygame.draw.circle(marca, (*VERMELHO_ALARME, int(140 * (1 - decorrido / 250))), (85, 85), 85)
            surf.blit(marca, (cx - 85, cy - 85))

    def texto_status(contexto):
        if contexto["vultos_surgiram"]:
            return "Alcance a porta de saída!"
        return None

    contexto["ao_atualizar"] = ao_atualizar
    contexto["ao_desenhar_extra"] = ao_desenhar_extra
    contexto["texto_status"] = texto_status
    return contexto


F7_RAIO_VISAO = 120            # px de visão ao redor do jogador (curto de propósito)
F7_ESCURIDAO_ALPHA = 250       # 255 = breu total; menos que isso deixa o cenário um pouco visível
F7_ALCANCE_BIP_REAL = 1000     # até onde o bip real é ouvido
F7_ALCANCE_BIP_FALSO = 800
F7_ALCANCE_VOZ_FALSA = 900
F7_PERIODO_BIP_MS = 2400       # intervalo do bip real (sempre igual: é o que o denuncia)
F7_PERIODO_FECHADURA_MS = 1800
F7_CUSTO_FOCO_SANIDADE = 0.8   # sanidade por segundo enquanto segura F (escutar parado)
F7_DANO_SUSTO = 10             # sanidade perdida ao ir até uma voz falsa
F7_RAIO_SUSTO = 120

F7_POS_CHAVE = (748, 881)      # centro da chave (e do monitor que bipa)
F7_POS_PORTA = (1780, 500)

F7_FALAS_REAIS_SEQ = [
    "Ainda sou eu. Não responda às outras vozes.",
    "Escute o monitor: dois bipes, sempre no mesmo ritmo.",
]
F7_FALAS_REAIS_POOL = [
    "Só o som que se repete no mesmo lugar é real.",
    "Fique quieto e ouça. Segure F.",
    "As outras vozes mudam de lugar. O bip não.",
    "A chave está onde alguém velava os doentes.",
    "Não vá até onde elas chamam.",
]
F7_FALA_PERTO = "Está perto... continue ouvindo."
F7_FALA_CHAVE = "Você pegou! Agora ouça a fechadura da ala médica."

F7_FALAS_FALSAS = [
    "A chave está aqui... venha.",
    "Eu sou a voz de verdade. A outra mente.",
    "Não escute o bip... é ele que te prende.",
    "Operário 724... você já esteve nesta cama.",
    "Por aqui. Por aqui. Por aqui.",
    "Vire à esquerda... não, à direita...",
    "A VOZ: não confie em mim.",
    "Tire a máscara... respire fundo...",
]


def _f7_pontos_de_chamado():
    # centros dos corredores entre as fileiras de macas (o jogador cabe ali)
    return [(x, y) for y in (285, 545, 835) for x in (130, 400, 700, 1000, 1300, 1600)]


def _f7_desenhar_maca(surf, r):
    pygame.draw.rect(surf, (88, 94, 104), r.inflate(8, 8), border_radius=6)
    pygame.draw.rect(surf, (176, 184, 190), r, border_radius=5)
    pygame.draw.rect(surf, (214, 220, 224), (r.x + 8, r.y + 10, 34, r.height - 20), border_radius=6)
    pygame.draw.rect(surf, (130, 150, 160), (r.x + 52, r.y + 6, r.width - 60, r.height - 12), border_radius=4)
    pygame.draw.rect(surf, (60, 65, 72), r.inflate(8, 8), width=2, border_radius=6)


def _f7_desenhar_silhueta(surf, r, tempo_ms, indice):
    """Pacientes alucinados: aparecem e somem nas macas (só enfeite, não machucam)."""
    onda = math.sin(tempo_ms / 1900 + indice * 2.3)
    if onda < 0.45:
        return
    a = int(150 * (onda - 0.45) / 0.55)
    fig = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
    pygame.draw.ellipse(fig, (20, 14, 30, a), (10, 12, 34, r.height - 24))
    pygame.draw.polygon(fig, (20, 14, 30, a),
                        [(44, 16), (r.width - 8, 24), (r.width - 8, r.height - 24), (44, r.height - 16)])
    surf.blit(fig, r.topleft)


def _f7_desenhar_remedios(surf, remedios):
    for (x, y, cor, tipo) in remedios:
        if tipo == 0:
            pygame.draw.circle(surf, cor, (x, y), 4)
        elif tipo == 1:
            pygame.draw.rect(surf, cor, (x, y, 10, 5), border_radius=2)
        else:
            pygame.draw.rect(surf, (200, 200, 205), (x, y, 18, 12))
            pygame.draw.circle(surf, cor, (x + 5, y + 6), 3)
            pygame.draw.circle(surf, cor, (x + 13, y + 6), 3)


def _f7_desenhar_posto(surf, balcao, chave, tem_chave, batida):
    pygame.draw.rect(surf, (70, 60, 52), balcao, border_radius=4)
    pygame.draw.rect(surf, (35, 30, 26), balcao, width=3, border_radius=4)
    tela = pygame.Rect(balcao.x + 150, balcao.y - 34, 52, 34)
    pygame.draw.rect(surf, (25, 28, 32), tela, border_radius=3)
    cor = (80, 255, 140) if (batida and not tem_chave) else (20, 70, 40)
    pontos = [(tela.x + 4, tela.centery), (tela.x + 16, tela.centery), (tela.x + 21, tela.y + 6),
              (tela.x + 27, tela.bottom - 5), (tela.x + 32, tela.centery), (tela.right - 4, tela.centery)]
    pygame.draw.lines(surf, cor, False, pontos, 2)
    if not chave.coletada:
        chave.desenhar(surf)


def _f7_glitch(texto, tempo_ms, semente):
    rng = random.Random(semente * 7919 + tempo_ms // 130)
    return "".join(rng.choice("#%&?*/~") if (c != " " and rng.random() < 0.07) else c for c in texto)


def _f7_desenhar_escuridao(surf, sala, jogador, tempo_ms, piscada):
    cam_x, cam_y = sala.calcular_camera(jogador)
    cx, cy = jogador.get_rect().center
    fator = max(0.0, min(1.0, getattr(jogador, "sanidade", 100) / 100.0))
    raio = F7_RAIO_VISAO * (0.65 + 0.35 * fator)          # sanidade baixa = enxerga menos
    if piscada:
        raio *= 0.55
    raio += 6 * math.sin(tempo_ms / 170) + 4 * math.sin(tempo_ms / 53)
    cx += int(3 * math.sin(tempo_ms / 97))
    cy += int(3 * math.cos(tempo_ms / 121))

    escuro = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    escuro.fill((2, 10, 6, F7_ESCURIDAO_ALPHA))
    passos = 9
    for k in range(passos):                                 # borda borrada, de fora para dentro
        r = int(raio * (1.25 - 0.95 * k / (passos - 1)))
        a = int(F7_ESCURIDAO_ALPHA * (1 - k / (passos - 1)) ** 1.3)
        pygame.draw.circle(escuro, (2, 10, 6, a), (cx - cam_x, cy - cam_y), max(2, r))
    surf.blit(escuro, (cam_x, cam_y))


def nivel_7(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.tem_pe_de_cabra = False
    jogador.agachado = False

    # ---- cenário: 3 fileiras de macas, posto de enfermagem, carrinhos ----
    macas = [pygame.Rect(x, y, 140, 70) for y in (120, 380, 640) for x in (250, 550, 850, 1150)]
    balcao = pygame.Rect(620, 890, 260, 70)
    carrinhos = [pygame.Rect(430, 900, 60, 60), pygame.Rect(1000, 900, 60, 60),
                 pygame.Rect(1500, 240, 60, 60), pygame.Rect(1560, 760, 60, 60)]
    obstaculos = macas + [balcao] + carrinhos

    sala = Sala(1800, 1000, ponto_entrada=(90, 470), largura_tela=LARGURA, altura_tela=ALTURA,
                obstaculos=obstaculos)
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = False

    rng = random.Random(7)
    cores = [(220, 60, 60), (235, 235, 235), (240, 200, 60), (70, 150, 230), (120, 200, 120)]
    remedios = []
    while len(remedios) < 90:
        x, y = rng.randint(60, 1720), rng.randint(60, 930)
        if any(pygame.Rect(x - 8, y - 8, 24, 20).colliderect(o) for o in obstaculos):
            continue
        remedios.append((x, y, rng.choice(cores), rng.randint(0, 2)))

    frascos = [FrascoSanidade(420, 300), FrascoSanidade(1000, 555), FrascoSanidade(1450, 420)]
    chave = Chave(740, 876, rotulo="Chave da Ala Médica")

    audio = AudioEspacial()
    agora = pygame.time.get_ticks()

    contexto = _estado_base(
        sala, 7,
        frascos=frascos,
        taxa_dano_sanidade=0.006,
        mensagem_intro='A VOZ: "Não há luz aqui. Confie só no som que se repete."',
        duracao_intro=5500,
        condicao_transicao=lambda contexto, jogador: False,
    )
    contexto["e7"] = {
        "audio": audio,
        "ultimo": agora,
        "tem_chave": False,
        "focando": False,
        "assistencia": not audio.ativo,      # sem áudio: seta visual ligada sozinha
        "pos_ant": None,
        "prox_bip_real": agora + 2500,
        "prox_bip_falso": agora + 9000,
        "prox_chiado": agora + 800,
        "prox_zumbido": agora + 22000,
        "zumbido_ate": 0,
        "prox_voz_real": agora + 6000,
        "n_falas_reais": 0,
        "perto_avisado": False,
        "prox_chamado": agora + 12000,
        "chamados": [],
        "legendas": [],
        "susto_ate": 0,
        "batida_ate": 0,
        "prox_piscada": agora + 8000,
        "piscada_ate": 0,
    }

    def origem_real():
        return F7_POS_PORTA if contexto["e7"]["tem_chave"] else F7_POS_CHAVE

    def ao_atualizar(contexto, jogador, teclas, tempo_ms):
        e = contexto["e7"]
        audio = e["audio"]
        sala = contexto["sala"]
        dt = min((tempo_ms - e["ultimo"]) / 1000, 0.1)
        e["ultimo"] = tempo_ms
        centro = jogador.get_rect().center

        # --- F: parar e escutar (sem andar, ouve mais longe e o chiado some um pouco) ---
        e["focando"] = bool(teclas[pygame.K_f])
        if e["focando"]:
            if e["pos_ant"] is not None:
                jogador.x, jogador.y = e["pos_ant"]
            jogador.andando = False
            jogador.dano_sanidade(F7_CUSTO_FOCO_SANIDADE * dt)
        e["pos_ant"] = (jogador.x, jogador.y)
        centro = jogador.get_rect().center

        zumbindo = tempo_ms < e["zumbido_ate"]
        ganho = 0.25 if zumbindo else 1.0                     # zumbido nos ouvidos abafa tudo
        alcance_real = F7_ALCANCE_BIP_REAL * (1.5 if e["focando"] else 1.0)
        ganho_ruido = 0.35 if e["focando"] else 1.0           # focar reduz o que é falso
        pan_erro = 0.18 * math.sin(tempo_ms / 2300)           # ouvido desregulado
        origem = origem_real()

        # --- o barulho REAL: mesmo tom, mesmo ritmo, mesmo lugar ---
        if tempo_ms >= e["prox_bip_real"]:
            if e["tem_chave"]:
                e["prox_bip_real"] = tempo_ms + F7_PERIODO_FECHADURA_MS
                audio.tocar_na_posicao("tique_porta", origem, centro, 1100, ganho=0.9 * ganho,
                                       pan_erro=pan_erro, forcar_abafado=zumbindo)
            else:
                e["prox_bip_real"] = tempo_ms + F7_PERIODO_BIP_MS
                audio.tocar_na_posicao("bip_real", origem, centro, alcance_real, ganho=0.9 * ganho,
                                       pan_erro=pan_erro, forcar_abafado=zumbindo)
            e["batida_ate"] = tempo_ms + 170

        # --- bipes FALSOS: lugar aleatório, tom/ritmo diferentes ---
        if tempo_ms >= e["prox_bip_falso"]:
            e["prox_bip_falso"] = tempo_ms + random.randint(2200, 4800)
            candidatos = [p for p in _f7_pontos_de_chamado()
                          if math.hypot(p[0] - origem[0], p[1] - origem[1]) > 250]
            nome = random.choice(("falso_agudo", "falso_grave", "falso_triplo", "falso_quase"))
            audio.tocar_na_posicao(nome, random.choice(candidatos), centro, F7_ALCANCE_BIP_FALSO,
                                   ganho=0.8 * ganho * ganho_ruido, pan_erro=pan_erro,
                                   forcar_abafado=zumbindo)

        # --- chiado do gás (o silêncio nunca é total) ---
        if tempo_ms >= e["prox_chiado"]:
            e["prox_chiado"] = tempo_ms + 970
            audio.tocar_central("chiado", ganho=0.16 * ganho_ruido)

        # --- zumbido nos ouvidos de vez em quando ---
        if tempo_ms >= e["prox_zumbido"]:
            e["prox_zumbido"] = tempo_ms + random.randint(20000, 34000)
            e["zumbido_ate"] = tempo_ms + 1800
            audio.tocar_central("zumbido", ganho=0.35)

        # --- A VOZ de antes (confiável): centrada, grave, legenda branca ---
        if not e["tem_chave"] and tempo_ms >= e["prox_voz_real"]:
            n = e["n_falas_reais"]
            if n < len(F7_FALAS_REAIS_SEQ):
                fala = F7_FALAS_REAIS_SEQ[n]
                e["prox_voz_real"] = tempo_ms + 14000
            else:
                fala = random.choice(F7_FALAS_REAIS_POOL)
                e["prox_voz_real"] = tempo_ms + random.randint(24000, 32000)
            e["n_falas_reais"] += 1
            _definir_mensagem(contexto, f'A VOZ: "{fala}"', tempo_ms, 4200)
            audio.tocar_central("voz_real", ganho=0.9 * ganho)

        if (not e["tem_chave"] and not e["perto_avisado"]
                and math.hypot(centro[0] - F7_POS_CHAVE[0], centro[1] - F7_POS_CHAVE[1]) < 420):
            e["perto_avisado"] = True
            _definir_mensagem(contexto, f'A VOZ: "{F7_FALA_PERTO}"', tempo_ms, 3500)
            audio.tocar_central("voz_real", ganho=0.9 * ganho)

        # --- vozes NOVAS (falsas): chamam de um ponto do mapa; ir até lá dá susto ---
        if tempo_ms >= e["prox_chamado"] and len(e["chamados"]) < 2:
            e["prox_chamado"] = tempo_ms + random.randint(10000, 17000)
            candidatos = [p for p in _f7_pontos_de_chamado()
                          if 350 <= math.hypot(p[0] - centro[0], p[1] - centro[1]) <= 900
                          and math.hypot(p[0] - F7_POS_CHAVE[0], p[1] - F7_POS_CHAVE[1]) > 300]
            if candidatos:
                e["chamados"].append({
                    "pos": random.choice(candidatos), "nasceu": tempo_ms, "prox": tempo_ms,
                    "falas": 0, "tipo": random.choice(("fv_agudo", "fv_sussurro", "fv_grave")),
                })

        for c in list(e["chamados"]):
            if tempo_ms >= c["prox"] and c["falas"] < 4:
                c["prox"] = tempo_ms + 2300
                c["falas"] += 1
                audio.tocar_na_posicao(c["tipo"], c["pos"], centro, F7_ALCANCE_VOZ_FALSA,
                                       ganho=0.85 * ganho * ganho_ruido, pan_erro=pan_erro,
                                       forcar_abafado=zumbindo)
                e["legendas"].append({"texto": random.choice(F7_FALAS_FALSAS), "pos": c["pos"],
                                      "nasceu": tempo_ms, "ate": tempo_ms + 2600,
                                      "semente": random.randint(1, 999)})
            if math.hypot(centro[0] - c["pos"][0], centro[1] - c["pos"][1]) < F7_RAIO_SUSTO:
                jogador.dano_sanidade(F7_DANO_SUSTO)
                e["susto_ate"] = tempo_ms + 400
                audio.tocar_central("susto", ganho=0.8)
                _definir_mensagem(contexto, "Não havia ninguém ali. Era só a alucinação.", tempo_ms, 3000)
                e["chamados"].remove(c)
            elif tempo_ms - c["nasceu"] > 12000:
                e["chamados"].remove(c)

        # --- a visão falha de vez em quando ---
        if tempo_ms >= e["prox_piscada"]:
            e["prox_piscada"] = tempo_ms + random.randint(6000, 14000)
            e["piscada_ate"] = tempo_ms + 350

        if sala.porta_aberta and sala.jogador_na_porta(jogador):
            audio.parar()
            contexto["final"] = True

    def ao_interagir(contexto, jogador):
        e = contexto["e7"]
        agora = pygame.time.get_ticks()
        sala = contexto["sala"]

        if not e["tem_chave"] and _perto(jogador, F7_POS_CHAVE, 105):
            e["tem_chave"] = True
            chave.coletada = True
            e["prox_bip_real"] = agora + 600          # o monitor cala; a fechadura passa a bater
            _definir_mensagem(contexto, f'A VOZ: "{F7_FALA_CHAVE}"', agora, 4500)
            e["audio"].tocar_central("voz_real", ganho=0.9)
            return

        if sala.jogador_na_porta(jogador):
            if not e["tem_chave"]:
                _definir_mensagem(contexto, "A porta da ala médica está trancada.", agora)
            elif not sala.porta_aberta:
                sala.porta_aberta = True
                _definir_mensagem(contexto, "A fechadura cede. A ala médica está aberta.", agora, 4000)

    def ao_tecla_down(contexto, jogador, evento):
        if evento.key == pygame.K_v:                   # V: liga/desliga a seta de ajuda
            e = contexto["e7"]
            e["assistencia"] = not e["assistencia"]
            _definir_mensagem(contexto, "Ajuda visual " + ("ligada." if e["assistencia"] else "desligada."),
                              pygame.time.get_ticks(), 2000)

    def ao_desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        e = contexto["e7"]
        sala = contexto["sala"]
        cam_x, cam_y = sala.calcular_camera(jogador)
        centro = jogador.get_rect().center

        # 1) cenário (a escuridão por cima esconde quase tudo)
        _f7_desenhar_remedios(surf, remedios)
        for i, m in enumerate(macas):
            _f7_desenhar_maca(surf, m)
            _f7_desenhar_silhueta(surf, m, tempo_ms, i)
        for c in carrinhos:
            pygame.draw.rect(surf, (96, 104, 112), c, border_radius=4)
            pygame.draw.rect(surf, (40, 44, 50), c, width=3, border_radius=4)
        _f7_desenhar_posto(surf, balcao, chave, e["tem_chave"], tempo_ms < e["batida_ate"])

        # 2) escuridão que falha (a visão pisca e encolhe com a sanidade baixa)
        _f7_desenhar_escuridao(surf, sala, jogador, tempo_ms, tempo_ms < e["piscada_ate"])

        # 3) por cima da escuridão: seta de ajuda, legendas das vozes falsas, susto
        if e["assistencia"]:
            alvo = origem_real()
            vx, vy = alvo[0] - centro[0], alvo[1] - centro[1]
            d = math.hypot(vx, vy) or 1.0
            ux, uy = vx / d, vy / d
            px, py = centro[0] + ux * 95, centro[1] + uy * 95
            tri = [(px + ux * 14, py + uy * 14),
                   (px - uy * 9 - ux * 6, py + ux * 9 - uy * 6),
                   (px + uy * 9 - ux * 6, py - ux * 9 - uy * 6)]
            pygame.draw.polygon(surf, CIANO_BRILHO, tri)

        for leg in list(e["legendas"]):
            restante = leg["ate"] - tempo_ms
            if restante <= 0:
                e["legendas"].remove(leg)
                continue
            alfa = int(255 * min(1.0, (tempo_ms - leg["nasceu"]) / 200, restante / 500))
            img = fonte.render(_f7_glitch(leg["texto"], tempo_ms, leg["semente"]), True, (185, 125, 255))
            img.set_alpha(max(0, alfa))
            x_tela = max(img.get_width() // 2 + 10,
                         min(LARGURA - img.get_width() // 2 - 10, leg["pos"][0] - cam_x))
            y_tela = max(130, min(ALTURA - 140, leg["pos"][1] - cam_y - 90))
            surf.blit(img, (cam_x + x_tela - img.get_width() // 2 + random.randint(-2, 2),
                            cam_y + y_tela + random.randint(-2, 2)))

        decorrido = e["susto_ate"] - tempo_ms
        if 0 < decorrido <= 400:
            cx, cy = centro
            marca = pygame.Surface((170, 170), pygame.SRCALPHA)
            pygame.draw.circle(marca, (*VERMELHO_ALARME, int(140 * decorrido / 400)), (85, 85), 85)
            surf.blit(marca, (cx - 85, cy - 85))

    def texto_status(contexto):
        e = contexto["e7"]
        if e["tem_chave"]:
            return "VOCÊ TEM: Chave da Ala Médica (ouça a fechadura da porta)"
        if e["focando"]:
            return "Escutando... (solte F para andar)"
        return "Ache a chave pelo som real  |  F: parar e escutar  |  V: ajuda visual"

    contexto["ao_atualizar"] = ao_atualizar
    contexto["ao_interagir"] = ao_interagir
    contexto["ao_tecla_down"] = ao_tecla_down
    contexto["ao_desenhar_extra"] = ao_desenhar_extra
    contexto["texto_status"] = texto_status
    return contexto


# ---------------------------------------------------------------------------
# FASE 8 — A ala das celas
#
# Zona A: corredor de celas com 2 guardas patrulhando. Dá para se esconder nos
#         vãos da parede (agachado). Visto = suspeita sobe; suspeita cheia = preso.
# Zona B: sala do guarda dormindo (porta entreaberta: só passa agachado). Cada
#         passo faz barulho; tábuas rangem. Pegue as chaves sem acordá-lo.
# Zona C: salão da porta de saída, com 2 guardas. Arremesse uma caneca (F) para
#         atraí-los, abra a porta com as chaves (E) e fuja.
# ---------------------------------------------------------------------------

F8_LARGURA, F8_ALTURA = 3400, 720
F8_FAIXA_TOPO, F8_FAIXA_BAIXO = 250, 470
F8_VAOS_TOPO = [(440, 600), (980, 1140), (1520, 1700)]
F8_VAOS_BAIXO = [(220, 380), (720, 880), (1260, 1420)]
F8_X_PORTA_SALA = 1700
F8_X_SAIDA_SALA = 2300
F8_DIRECOES = {'direita': (1, 0), 'esquerda': (-1, 0), 'costas': (0, -1), 'frente': (0, 1)}


def _f8_blocos(vaos, x_ini, x_fim, y0, y1):
    blocos, x = [], x_ini
    for a, b in vaos:
        if a > x:
            blocos.append(pygame.Rect(x, y0, a - x, y1 - y0))
        x = b
    if x < x_fim:
        blocos.append(pygame.Rect(x, y0, x_fim - x, y1 - y0))
    return blocos


def _f8_desenhar_celas(surf, bloco, lado, tempo_ms, indice_bloco):
    """Desenha as celas de um bloco: chão escuro, catre, preso (às vezes) e a grade."""
    n = max(1, round(bloco.width / 190))
    passo = bloco.width / n
    for i in range(n):
        x0 = int(bloco.x + i * passo)
        x1 = int(bloco.x + (i + 1) * passo)
        cela = pygame.Rect(x0, bloco.y, x1 - x0, bloco.height)
        pygame.draw.rect(surf, (24, 26, 34), cela.inflate(-8, -8))
        if lado == 'topo':
            catre = pygame.Rect(x0 + 18, bloco.y + 18, 70, 34)
            frente_y = bloco.bottom
            grade_y0 = frente_y - 28
        else:
            catre = pygame.Rect(x0 + 18, bloco.bottom - 52, 70, 34)
            frente_y = bloco.y
            grade_y0 = frente_y
        pygame.draw.rect(surf, (58, 52, 48), catre, border_radius=3)
        pygame.draw.rect(surf, (30, 28, 26), catre, width=2, border_radius=3)

        semente = indice_bloco * 7 + i * 3
        if semente % 2 == 0:  # cela ocupada: silhueta com olhos que piscam
            sx = x0 + (x1 - x0) // 2 + 20
            sy = bloco.y + 60 if lado == 'topo' else bloco.bottom - 60
            pygame.draw.ellipse(surf, (10, 10, 14), (sx - 18, sy - 14, 36, 30))
            if (tempo_ms // 1800 + semente) % 6 != 0:
                pygame.draw.circle(surf, (220, 220, 190), (sx - 6, sy - 4), 2)
                pygame.draw.circle(surf, (220, 220, 190), (sx + 6, sy - 4), 2)

        pygame.draw.rect(surf, (96, 102, 114), (x0 + 4, grade_y0, x1 - x0 - 8, 4))
        pygame.draw.rect(surf, (96, 102, 114), (x0 + 4, grade_y0 + 24, x1 - x0 - 8, 4))
        for bx in range(x0 + 10, x1 - 6, 14):
            pygame.draw.line(surf, (120, 126, 140), (bx, grade_y0), (bx, grade_y0 + 28), 3)
        pygame.draw.line(surf, (12, 14, 20), (x1 - 1, bloco.y), (x1 - 1, bloco.bottom), 3)


def _f8_desenhar_vao(surf, rect):
    pygame.draw.rect(surf, (9, 11, 16), rect)
    pygame.draw.rect(surf, (4, 5, 8), rect, width=3)
    pygame.draw.line(surf, (30, 34, 44), (rect.x + 14, rect.y + 20), (rect.right - 14, rect.y + 20), 2)


def nivel_8(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
    jogador.agachado = False

    # ---- geometria ----------------------------------------------------------
    blocos_topo = _f8_blocos(F8_VAOS_TOPO, 40, F8_X_PORTA_SALA, 40, F8_FAIXA_TOPO)
    blocos_baixo = _f8_blocos(F8_VAOS_BAIXO, 40, F8_X_PORTA_SALA, F8_FAIXA_BAIXO, F8_ALTURA - 40)

    # parede da sala do guarda: porta entreaberta (vão de 105px; em pé o jogador tem 110px, então só passa agachado)
    parede_sala = [pygame.Rect(F8_X_PORTA_SALA, 40, 40, 300),
                   pygame.Rect(F8_X_PORTA_SALA, 445, 40, F8_ALTURA - 40 - 445)]
    # saída da sala: abertura larga que dá no salão da porta
    parede_saida = [pygame.Rect(F8_X_SAIDA_SALA, 40, 40, 260),
                    pygame.Rect(F8_X_SAIDA_SALA, 470, 40, F8_ALTURA - 40 - 470)]

    mesa = pygame.Rect(1980, 300, 170, 80)
    estante = pygame.Rect(1800, 40, 220, 50)
    caixas_salao = [pygame.Rect(2560, 240, 100, 100), pygame.Rect(2760, 400, 100, 100),
                    pygame.Rect(2960, 260, 90, 90)]

    obstaculos = (blocos_topo + blocos_baixo + parede_sala + parede_saida
                  + [mesa, estante] + caixas_salao)

    sala = Sala(F8_LARGURA, F8_ALTURA, ponto_entrada=(60, 295), largura_tela=LARGURA, altura_tela=ALTURA,
                obstaculos=obstaculos, pos_porta=pygame.Rect(F8_LARGURA - 40, 280, 40, 160),
                cor_fundo=(24, 26, 33))
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = False
    paredes = sala.paredes_colisao()

    # esconderijos (agachado dentro deles, os guardas só te veem se esbarrarem em você)
    vaos = ([pygame.Rect(a, 40, b - a, F8_FAIXA_TOPO - 40) for a, b in F8_VAOS_TOPO]
            + [pygame.Rect(a, F8_FAIXA_BAIXO, b - a, F8_ALTURA - 40 - F8_FAIXA_BAIXO) for a, b in F8_VAOS_BAIXO])
    sombras_salao = [pygame.Rect(2340, 40, 760, 150), pygame.Rect(2340, 530, 760, 150)]
    esconderijos = vaos + sombras_salao

    # tábuas que rangem na sala do guarda (existe um caminho sem pisar em nenhuma)
    tabuas = [pygame.Rect(1930, 110, 90, 90), pygame.Rect(1850, 390, 80, 90),
              pygame.Rect(2100, 150, 90, 90), pygame.Rect(2000, 430, 70, 100),
              pygame.Rect(2090, 400, 60, 90), pygame.Rect(1870, 510, 80, 80)]

    ponto_guarda_dormindo = (2045, 268)
    chave = Chave(2005, 322, rotulo="Chaves das celas")
    canecas_prateleira = pygame.Rect(1870, 92, 40, 16)

    guardas = [
        GuardaPrisao(380, 360, rota=[(380, 360), (1050, 360)], angulo=0, velocidade=1.3,
                     alcance=330, abertura=56, pausa_ms=1600),
        GuardaPrisao(1640, 360, rota=[(1640, 360), (1190, 360)], angulo=180, velocidade=1.3,
                     alcance=330, abertura=56, pausa_ms=1600),
        GuardaPrisao(3230, 275, angulo=180, varredura=22, alcance=380, abertura=62),
        GuardaPrisao(3230, 445, angulo=180, varredura=22, alcance=380, abertura=62),
    ]
    for g in guardas:
        g.definir_mundo(paredes)

    frascos = [FrascoSanidade(500, 100), FrascoSanidade(1060, 600), FrascoSanidade(2420, 90)]

    sussurros = [
        (260, 'PRESO: "Psiu... eles dão meia-volta nas pontas."'),
        (760, 'PRESO: "Nos vãos da parede ninguém te vê. Agachado."'),
        (1330, 'PRESO: "O guarda do fim dorme... e as tábuas rangem."'),
    ]

    glow = pygame.Surface((220, 220), pygame.SRCALPHA)
    for r in range(110, 0, -10):
        pygame.draw.circle(glow, (255, 235, 170, int(46 * (1 - r / 110))), (110, 110), r)
    sombra_surfs = {}
    for s in sombras_salao:
        sf = pygame.Surface(s.size, pygame.SRCALPHA)
        sf.fill((0, 0, 14, 120))
        sombra_surfs[(s.x, s.y)] = sf

    ponto_inicio = sala.ponto_entrada
    ponto_sala_guarda = (1760, 290)
    ponto_salao = (2360, 305)

    contexto = _estado_base(
        sala, 8,
        frascos=frascos,
        guardas=guardas,
        taxa_dano_sanidade=0.004,
        mensagem_intro='A VOZ: "É por aqui que você deve passar. Sem ser visto."',
        duracao_intro=5500,
        condicao_transicao=lambda contexto, jogador: False,
    )

    e = {
        "tem_chave": False,
        "canecas": 0,
        "canecas_pegas": False,
        "ruido": 0.0,
        "agitado": False,
        "tabua_ativa": False,
        "escondido": False,
        "preso_ate": 0,
        "preso_inicio": 0,
        "preso_motivo": "",
        "pos_preso": (0, 0),
        "checkpoint": ponto_inicio,
        "arremesso": None,
        "ondas": [],
        "sussurros_dados": set(),
        "aviso_porta": False,
        "ultimo_tempo": pygame.time.get_ticks(),
    }
    contexto["e8"] = e

    def perto(jogador, rect, folga):
        return jogador.get_rect().colliderect(rect.inflate(folga, folga))

    def ponto_em_parede(px, py):
        return pygame.Rect(int(px), int(py), 1, 1).collidelist(paredes) != -1

    jogador_ref = [jogador]

    def prender(tempo_ms, motivo):
        e["preso_inicio"] = tempo_ms
        e["preso_ate"] = tempo_ms + 3200
        e["preso_motivo"] = motivo
        e["pos_preso"] = (jogador_ref[0].x, jogador_ref[0].y)

    def reaparecer(tempo_ms):
        j = jogador_ref[0]
        e["preso_ate"] = 0
        j.x, j.y = e["checkpoint"]
        j.agachado = False
        j.andando = False
        for g in guardas:
            g.reiniciar()
        e["ruido"] = 0.0
        e["agitado"] = False
        e["arremesso"] = None
        if e["canecas_pegas"]:
            e["canecas"] = 2
        j.dano_sanidade(8)
        _definir_mensagem(contexto, "Você foi solto na última área segura. Tente de novo.", tempo_ms, 3000)

    def ao_tecla_down(contexto, jogador, evento):
        jogador_ref[0] = jogador
        agora = pygame.time.get_ticks()
        if e["preso_ate"]:
            return

        if evento.key == pygame.K_q and not jogador.agachado:
            # acabou de levantar: se não houver espaço (teto baixo, porta), volta a ficar agachado
            if jogador.get_rect().collidelist(paredes) != -1:
                jogador.agachado = True
                _definir_mensagem(contexto, "Não há espaço para levantar aqui.", agora, 1800)

        if evento.key == pygame.K_f:
            if e["canecas"] <= 0 or e["arremesso"]:
                if not e["canecas_pegas"]:
                    _definir_mensagem(contexto, "Você não tem nada para arremessar.", agora, 1800)
                return
            origem = jogador.get_rect().center
            vx, vy = F8_DIRECOES[jogador.direcao]
            dist = 0
            while dist < 380 and not ponto_em_parede(origem[0] + vx * (dist + 10), origem[1] + vy * (dist + 10)):
                dist += 10
            if dist < 60:
                _definir_mensagem(contexto, "Não há espaço para arremessar nessa direção.", agora, 1800)
                return
            e["canecas"] -= 1
            e["arremesso"] = {"origem": origem,
                              "destino": (origem[0] + vx * dist, origem[1] + vy * dist),
                              "t0": agora, "dur": 550}

    def ao_interagir(contexto, jogador):
        jogador_ref[0] = jogador
        agora = pygame.time.get_ticks()
        if e["preso_ate"]:
            return

        if not e["tem_chave"] and perto(jogador, chave.rect, 120):
            chave.coletada = True
            e["tem_chave"] = True
            e["ruido"] += 45 if not jogador.agachado else 22
            _definir_mensagem(contexto, "Você pegou as chaves. Agora saia sem fazer barulho.", agora, 3500)
        elif not e["canecas_pegas"] and perto(jogador, canecas_prateleira, 70):
            e["canecas_pegas"] = True
            e["canecas"] = 2
            _definir_mensagem(contexto, "Você pegou 2 canecas de metal. [F] arremessa.", agora, 3500)
        elif perto(jogador, sala.rect_porta, 90):
            if sala.porta_aberta:
                return
            if e["tem_chave"]:
                sala.porta_aberta = True
                _definir_mensagem(contexto, "A porta se abre. Corra!", agora, 3000)
            else:
                _definir_mensagem(contexto, "Trancada. Você precisa das chaves do guarda.", agora, 2500)

    def atualizar_ruido(jogador, agora, f):
        dist = math.hypot(jogador.get_rect().centerx - ponto_guarda_dormindo[0],
                          jogador.get_rect().centery - ponto_guarda_dormindo[1])
        fator_dist = max(0.0, min(1.0, 1.0 - (dist - 250) / 450))
        pe = (jogador.get_rect().centerx, jogador.get_rect().bottom - 10)
        em_tabua = any(t.collidepoint(pe) for t in tabuas)

        if jogador.andando:
            e["ruido"] += (0.09 if jogador.agachado else 0.75) * fator_dist * f
            if em_tabua:
                if not e["tabua_ativa"]:
                    e["ruido"] += 28
                    _definir_mensagem(contexto, "A tábua range!", agora, 1500)
                e["ruido"] += 0.35 * f
            e["ruido"] -= 0.03 * f
        else:
            e["ruido"] -= 0.20 * f
        e["tabua_ativa"] = em_tabua and jogador.andando
        e["ruido"] = max(0.0, e["ruido"])

        if e["ruido"] >= 100:
            return True
        if e["ruido"] >= 50 and not e["agitado"]:
            e["agitado"] = True
            _definir_mensagem(contexto, "O guarda se mexeu na cadeira...", agora, 2200)
        elif e["ruido"] < 25:
            e["agitado"] = False
        return False

    def ao_atualizar(contexto, jogador, teclas, tempo_ms):
        jogador_ref[0] = jogador
        f = max(0.0, min(3.0, (tempo_ms - e["ultimo_tempo"]) / 16.667))
        e["ultimo_tempo"] = tempo_ms

        # preso: fica parado até o tempo acabar e volta ao último ponto seguro
        if e["preso_ate"]:
            jogador.x, jogador.y = e["pos_preso"]
            jogador.andando = False
            if tempo_ms >= e["preso_ate"]:
                reaparecer(tempo_ms)
            return

        rect = jogador.get_rect()
        cx, cy = rect.center
        e["escondido"] = jogador.agachado and any(v.collidepoint(cx, cy) for v in esconderijos)

        # checkpoints
        if e["tem_chave"] and jogador.x > F8_X_SAIDA_SALA + 40:
            e["checkpoint"] = ponto_salao
        elif jogador.x > F8_X_PORTA_SALA + 50 and not e["tem_chave"] and e["checkpoint"] == ponto_inicio:
            e["checkpoint"] = ponto_sala_guarda

        # dicas das celas / porta entreaberta
        for i, (sx, texto) in enumerate(sussurros):
            if i not in e["sussurros_dados"] and abs(cx - sx) < 220 and jogador.x < F8_X_PORTA_SALA:
                e["sussurros_dados"].add(i)
                _definir_mensagem(contexto, texto, tempo_ms, 3800)
        if not e["aviso_porta"] and jogador.x > F8_X_PORTA_SALA - 380:
            e["aviso_porta"] = True
            _definir_mensagem(contexto, "A porta está entreaberta. Só passa agachado (Q).", tempo_ms, 3500)

        # guardas
        for g in guardas:
            if g.atualizar(jogador, esconderijos, tempo_ms):
                prender(tempo_ms, "Um guarda te viu!")
                return

        # caneca no ar
        arr = e["arremesso"]
        if arr and tempo_ms >= arr["t0"] + arr["dur"]:
            destino = arr["destino"]
            e["ondas"].append({"pos": destino, "t0": tempo_ms})
            ouviram = sum(1 for g in guardas if g.ouvir(destino, tempo_ms))
            if math.hypot(destino[0] - ponto_guarda_dormindo[0], destino[1] - ponto_guarda_dormindo[1]) < 520:
                e["ruido"] += 100
            _definir_mensagem(contexto, "CLANG! Os guardas foram ver o que foi." if ouviram else "CLANG!",
                              tempo_ms, 3000)
            e["arremesso"] = None
        e["ondas"] = [w for w in e["ondas"] if tempo_ms - w["t0"] < 800]

        # guarda dormindo
        if atualizar_ruido(jogador, tempo_ms, f):
            prender(tempo_ms, "O guarda acordou!")
            return

        if sala.porta_aberta and sala.jogador_na_porta(jogador):
            contexto["final"] = True

    def ao_desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        # piso da sala do guarda e do salão
        pygame.draw.rect(surf, (40, 34, 29), (F8_X_PORTA_SALA + 40, 40, F8_X_SAIDA_SALA - F8_X_PORTA_SALA - 40, F8_ALTURA - 80))
        for yy in range(60, F8_ALTURA - 40, 40):
            pygame.draw.line(surf, (32, 27, 23), (F8_X_PORTA_SALA + 40, yy), (F8_X_SAIDA_SALA, yy), 1)
        pygame.draw.rect(surf, (28, 30, 38), (F8_X_SAIDA_SALA + 40, 40, F8_LARGURA - F8_X_SAIDA_SALA - 80, F8_ALTURA - 80))
        for xx in range(F8_X_SAIDA_SALA + 80, F8_LARGURA - 40, 80):
            pygame.draw.line(surf, (24, 26, 33), (xx, 40), (xx, F8_ALTURA - 40), 1)

        # celas, vãos, lâmpadas
        for i, b in enumerate(blocos_topo):
            _f8_desenhar_celas(surf, b, 'topo', tempo_ms, i)
        for i, b in enumerate(blocos_baixo):
            _f8_desenhar_celas(surf, b, 'baixo', tempo_ms, i + 10)
        for v in vaos:
            _f8_desenhar_vao(surf, v)
        for lx in (180, 560, 940, 1320):
            if not (lx == 940 and (tempo_ms // 140) % 9 == 0):
                surf.blit(glow, (lx - 110, 360 - 110))

        # porta entreaberta da sala do guarda
        pygame.draw.line(surf, (110, 80, 50), (F8_X_PORTA_SALA + 20, 340), (F8_X_PORTA_SALA + 66, 296), 8)
        pygame.draw.line(surf, (60, 40, 25), (F8_X_PORTA_SALA + 20, 340), (F8_X_PORTA_SALA + 66, 296), 2)

        # tábuas que rangem (um pouco mais claras que o piso)
        for t in tabuas:
            pygame.draw.rect(surf, (74, 58, 42), t)
            for k in range(t.x + 18, t.right, 18):
                pygame.draw.line(surf, (52, 40, 30), (k, t.y), (k, t.bottom), 1)
            pygame.draw.rect(surf, (96, 76, 54), t, width=2)

        # prateleira com canecas
        pygame.draw.rect(surf, (80, 66, 50), estante)
        pygame.draw.rect(surf, (40, 32, 24), estante, width=2)
        if not e["canecas_pegas"]:
            for k in range(2):
                pygame.draw.rect(surf, (170, 175, 185), (canecas_prateleira.x + 4 + k * 20, canecas_prateleira.y, 12, 14), border_radius=3)

        # mesa, cadeira, guarda dormindo e chaves
        pygame.draw.rect(surf, (96, 70, 46), mesa, border_radius=4)
        pygame.draw.rect(surf, (50, 34, 22), mesa, width=3, border_radius=4)
        pygame.draw.rect(surf, (60, 50, 44), (ponto_guarda_dormindo[0] - 30, 236, 60, 46), border_radius=6)
        gx, gy = ponto_guarda_dormindo
        agitado = e["agitado"]
        respira = int(2 * math.sin(tempo_ms / (350 if agitado else 900)))
        pygame.draw.ellipse(surf, (22, 26, 40), (gx - 34, gy - 18 + respira, 68, 40))
        pygame.draw.ellipse(surf, (58, 70, 108), (gx - 30, gy - 15 + respira, 60, 32))
        pygame.draw.circle(surf, (205, 175, 145), (gx + 4, gy + 22), 12)
        pygame.draw.circle(surf, (30, 34, 50), (gx + 4, gy + 22), 12, width=3)
        if not chave.coletada:
            chave.desenhar(surf)
        texto_z = fonte.render("!" if agitado else "Z z z", True, (255, 200, 80) if agitado else (150, 160, 200))
        surf.blit(texto_z, (gx + 26, gy - 52 - int(6 * math.sin(tempo_ms / 500))))

        # caixas do salão e sombras (esconderijos)
        for c in caixas_salao:
            pygame.draw.rect(surf, (105, 70, 45), c, border_radius=4)
            pygame.draw.rect(surf, (50, 30, 20), c, width=3, border_radius=4)
            pygame.draw.line(surf, (60, 38, 24), c.topleft, c.bottomright, 2)
            pygame.draw.line(surf, (60, 38, 24), c.topright, c.bottomleft, 2)
        for s in sombras_salao:
            surf.blit(sombra_surfs[(s.x, s.y)], s.topleft)

        # caneca voando e ondas de som
        arr = e["arremesso"]
        if arr:
            t = min(1.0, (tempo_ms - arr["t0"]) / arr["dur"])
            ox, oy = arr["origem"]
            dx_, dy_ = arr["destino"]
            px, py = ox + (dx_ - ox) * t, oy + (dy_ - oy) * t
            altura = 40 * math.sin(math.pi * t)
            pygame.draw.circle(surf, (20, 20, 25), (int(px), int(py)), 5)
            pygame.draw.circle(surf, (190, 195, 205), (int(px), int(py - altura)), 6)
        for w in e["ondas"]:
            prog = (tempo_ms - w["t0"]) / 800
            pygame.draw.circle(surf, (230, 230, 120), (int(w["pos"][0]), int(w["pos"][1])), int(20 + 150 * prog), width=3)


    def ao_desenhar_tela(contexto, tela, jogador, fonte, tempo_ms):
        if e["tem_chave"] and sala.porta_aberta:
            objetivo = "Fuja pela porta!"
        elif e["tem_chave"]:
            objetivo = "Distraia os guardas e abra a porta (E)"
        elif jogador.x >= F8_X_PORTA_SALA:
            objetivo = "Pegue as chaves sem acordar o guarda"
        else:
            objetivo = "Passe pela ala das celas sem ser visto"
        tela.blit(fonte.render(f"OBJETIVO: {objetivo}", True, (210, 220, 255)), (20, 124))
        extra = "Q: agachar   E: interagir"
        if e["canecas"] > 0:
            extra += f"   F: arremessar caneca ({e['canecas']})"
        tela.blit(fonte.render(extra, True, (140, 150, 175)), (20, 146))

        if e["escondido"]:
            tela.blit(fonte.render("ESCONDIDO", True, (120, 230, 160)), (20, 168))

        # medidor de ruído (aparece perto do guarda dormindo)
        if (F8_X_PORTA_SALA <= jogador.x <= F8_X_SAIDA_SALA + 40 and not e["tem_chave"]) or e["ruido"] > 1:
            y = 192
            pygame.draw.rect(tela, (40, 40, 45), (20, y, 200, 12), border_radius=3)
            cor = (255, 90, 60) if e["ruido"] >= 50 else (255, 200, 60)
            if e["ruido"] > 0:
                pygame.draw.rect(tela, cor, (20, y, int(min(100, e["ruido"]) * 2), 12), border_radius=3)
            pygame.draw.rect(tela, (200, 200, 200), (20, y, 200, 12), 2, border_radius=3)
            tela.blit(fonte.render("RUÍDO", True, (255, 255, 255)), (228, y - 4))

        # tela de "preso"
        if e["preso_ate"]:
            decorrido = tempo_ms - e["preso_inicio"]
            total = e["preso_ate"] - e["preso_inicio"]
            veu = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            veu.fill((120, 10, 10, min(150, int(decorrido / 3))))
            tela.blit(veu, (0, 0))
            deslocamento = min(1.0, decorrido / 350)
            for bx in range(0, LARGURA, 64):
                altura_barra = int(ALTURA * deslocamento)
                pygame.draw.rect(tela, (18, 18, 22), (bx + 24, 0, 16, altura_barra))
                pygame.draw.rect(tela, (90, 95, 108), (bx + 24, 0, 16, altura_barra), width=2)
            if decorrido > 350:
                titulo = fonte.render("PRESO!", True, (255, 80, 70))
                tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, ALTURA // 2 - 20)))
                motivo = fonte.render(e["preso_motivo"], True, (230, 230, 230))
                tela.blit(motivo, motivo.get_rect(center=(LARGURA // 2, ALTURA // 2 + 14)))
            restante = e["preso_ate"] - tempo_ms
            if restante < 450:
                fade = pygame.Surface((LARGURA, ALTURA))
                fade.fill((0, 0, 0))
                fade.set_alpha(int(255 * (1 - restante / 450)))
                tela.blit(fade, (0, 0))

    contexto["ao_atualizar"] = ao_atualizar
    contexto["ao_interagir"] = ao_interagir
    contexto["ao_tecla_down"] = ao_tecla_down
    contexto["ao_desenhar_extra"] = ao_desenhar_extra
    contexto["ao_desenhar_tela"] = ao_desenhar_tela
    return contexto

def nivel_9(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.agachado = False

    sala = Sala(
        1500,
        900,
        (100, 430),
        largura_tela=LARGURA,
        altura_tela=ALTURA
    )
    jogador.x, jogador.y = sala.ponto_entrada
    jogador.agachado = False

    posicoes_disjuntores = [
        (300, 200),
        (650, 200),
        (1000, 200),
        (1250, 500)
    ]

    puzzle_disjuntores = PuzzleDisjuntores(
        posicoes_disjuntores,
        [2, 0, 3, 1]
    )

    lanterna = {
        "pos": (180, 500),
        "coletada": False,
        "bateria": 100.0
    }

    vultos = [
        Inimigo(800, 300, velocidade=1.8, dano=4,
                recarga_ms=1200, atraso_ms=0, lado_desvio=1),

        Inimigo(1100, 650, velocidade=2.0, dano=4,
                recarga_ms=1200, atraso_ms=500, lado_desvio=-1),

        Inimigo(500, 700, velocidade=1.7, dano=3,
                recarga_ms=1300, atraso_ms=1000, lado_desvio=1)
    ]

    contexto = _estado_base(
        sala,
        9,
        objetos=[],
        puzzle_disjuntores=puzzle_disjuntores,
        lanterna=lanterna,
        vultos=vultos,
        usa_lanterna=True,
        mensagem_intro=(
            'A VOZ: "O elevador parou... '
            'Encontre os disjuntores."'
        ),
        duracao_intro=4000,
        taxa_dano_sanidade=0.004,
        texto_status="Reative a energia ligando os disjuntores."
    )

    def interagir(contexto, jogador):
        tempo_ms = pygame.time.get_ticks()
        if not lanterna["coletada"]:
            if _perto(jogador, lanterna["pos"], 60):
                lanterna["coletada"] = True
                _definir_mensagem(
                    contexto,
                    "Você encontrou uma lanterna. A bateria está acabando.",
                    tempo_ms
                )
                return

        disjuntor = puzzle_disjuntores.disjuntor_proximo(jogador)

        if disjuntor:
            sucesso = puzzle_disjuntores.acionar(disjuntor)

            if sucesso:
                if puzzle_disjuntores.resolvido:
                    sala.porta_aberta = True

                    _definir_mensagem(
                        contexto,
                        "Todos os disjuntores foram ativados! A energia voltou.",
                        tempo_ms,
                        4000
                    )

                    for vulto in vultos:
                        vulto.surgir(tempo_ms)

                else:
                    _definir_mensagem(
                        contexto,
                        "Disjuntor ativado.",
                        tempo_ms,
                        1200
                    )

            else:
                _definir_mensagem(
                    contexto,
                    "Sequência incorreta. Os disjuntores foram desligados.",
                    tempo_ms
                )

    def atualizar(contexto, jogador, teclas, tempo_ms):
        if lanterna["coletada"] and lanterna["bateria"] > 0:
            lanterna["bateria"] -= 0.025
            lanterna["bateria"] = max(
                0,
                lanterna["bateria"]
            )

        for vulto in vultos:
            if puzzle_disjuntores.resolvido:
                vulto.perseguir(
                    jogador,
                    sala.paredes_colisao(),
                    tempo_ms,
                    vultos
                )

                vulto.tentar_atacar(
                    jogador,
                    tempo_ms
                )

        if sala.porta_aberta and sala.jogador_na_porta(jogador):
            contexto["final"] = True

    def desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        puzzle_disjuntores.desenhar(surf)

        if not lanterna["coletada"]:
            pygame.draw.rect(
                surf,
                (230, 210, 80),
                (
                    lanterna["pos"][0] - 10,
                    lanterna["pos"][1] - 7,
                    20,
                    14
                )
            )

        for x, y in [(200, 120), (1350, 180)]:
            piscando = (tempo_ms // 400) % 2 == 0

            cor = (
                (255, 220, 80)
                if piscando
                else (80, 70, 40)
            )

            pygame.draw.rect(
                surf,
                (50, 50, 50),
                (x, y, 60, 70)
            )

            pygame.draw.circle(
                surf,
                cor,
                (x + 30, y + 25),
                7
            )

        for vulto in vultos:
            vulto.desenhar(surf, tempo_ms)

    contexto["ao_interagir"] = interagir
    contexto["ao_atualizar"] = atualizar
    contexto["ao_desenhar_extra"] = desenhar_extra

    def status(contexto):
        ativados = sum(
            1
            for d in puzzle_disjuntores.disjuntores
            if d["ligado"]
        )

        bateria = int(lanterna["bateria"])

        return (
            f"Disjuntores: {ativados}/4 | "
            f"Lanterna: {bateria}%"
        )

    contexto["texto_status"] = status

    return contexto


def nivel_10(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.agachado = False

    sala = Sala(
        1700,
        950,
        (90, 450),
        largura_tela=LARGURA,
        altura_tela=ALTURA
    )
    jogador.x, jogador.y = sala.ponto_entrada
    jogador.agachado = False

    frascos = gerar_frascos_na_sala(3)

    puzzle_fuzil = PuzzleFuzil(
        (850, 470),
        golpes_necessarios=3
    )

    contexto = _estado_base(
        sala,
        10,
        frascos=frascos,
        puzzle_fuzil=puzzle_fuzil,
        usa_lanterna=False,
        mensagem_intro=(
            'Você chegou a um pátio. '
            'Há materiais espalhados pelo local.'
        ),
        duracao_intro=3500,
        taxa_dano_sanidade=0.003,
        texto_status="Atravesse o pátio."
    )

    def interagir(contexto, jogador):
        tempo_ms = pygame.time.get_ticks()
        # Fuzil
        if puzzle_fuzil.perto(jogador):

            if puzzle_fuzil.consertado:
                _definir_mensagem(
                    contexto,
                    "O reparo já foi concluído.",
                    tempo_ms
                )
                return

            puzzle_fuzil.golpear()

            if puzzle_fuzil.consertado:
                sala.porta_aberta = True

                _definir_mensagem(
                    contexto,
                    "O fuzil foi consertado! As luzes se acendem e as sirenes começam a tocar.",
                    tempo_ms,
                    5000
                )

            else:
                _definir_mensagem(
                    contexto,
                    f"Você trabalha no reparo... "
                    f"{puzzle_fuzil.golpes}/"
                    f"{puzzle_fuzil.golpes_necessarios}",
                    tempo_ms,
                    1500
                )

    def atualizar(contexto, jogador, teclas, tempo_ms):
        if sala.porta_aberta and sala.jogador_na_porta(jogador):
            contexto["final"] = True

    def desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        for frasco in frascos:
            frasco.desenhar(surf)

        puzzle_fuzil.desenhar(
            surf,
            pygame.font.Font(None, 24)
        )

        if puzzle_fuzil.consertado:
            for x, y in [
                (250, 150),
                (600, 150),
                (1000, 150),
                (1400, 150)
            ]:
                pygame.draw.circle(
                    surf,
                    (255, 240, 150),
                    (x, y),
                    12
                )

        if puzzle_fuzil.consertado:
            if (tempo_ms // 250) % 2 == 0:
                pygame.draw.rect(
                    surf,
                    (200, 30, 30),
                    (20, 70, 30, 30)
                )

    contexto["ao_interagir"] = interagir
    contexto["ao_atualizar"] = atualizar
    contexto["ao_desenhar_extra"] = desenhar_extra

    def status(contexto):
        if puzzle_fuzil.consertado:
            return "Fuzil reparado. Atravesse o pátio!"

        return (
            f"Reparo do fuzil: "
            f"{puzzle_fuzil.golpes}/"
            f"{puzzle_fuzil.golpes_necessarios}"
        )

    contexto["texto_status"] = status

    return contexto


def nivel_11(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.agachado = False
        jogador.tem_pe_de_cabra = False

    obstaculos = [
        pygame.Rect(450, 300, 90, 90),
        pygame.Rect(750, 500, 100, 80),
        pygame.Rect(1050, 280, 90, 100),
        pygame.Rect(1350, 520, 100, 80)
    ]

    sala = Sala(
        1800,
        900,
        (80, 430),
        largura_tela=LARGURA,
        altura_tela=ALTURA,
        obstaculos=obstaculos
    )
    jogador.x, jogador.y = sala.ponto_entrada
    jogador.agachado = False

    sala.porta_aberta = False

    guardas = [
        Inimigo(
            650, 100,
            velocidade=2.8,
            dano=3,
            recarga_ms=1000,
            atraso_ms=0,
            lado_desvio=1
        ),

        Inimigo(
            1100, 700,
            velocidade=3.0,
            dano=3,
            recarga_ms=1000,
            atraso_ms=700,
            lado_desvio=-1
        ),

        Inimigo(
            1500, 100,
            velocidade=3.2,
            dano=3,
            recarga_ms=900,
            atraso_ms=1400,
            lado_desvio=1
        )
    ]

    pe_de_cabra = {
        "pos": (1550, 450),
        "coletado": False
    }

    contexto = _estado_base(
        sala,
        11,
        guardas=[],
        objetos=[],
        usa_lanterna=False,
        mensagem_intro=(
            'As câmeras detectam você. '
            'A VOZ: "CORRA!"'
        ),
        duracao_intro=3000,
        taxa_dano_sanidade=0.006,
        texto_status="Corra até a saída."
    )

    contexto["portas_fechando"] = True
    contexto["tempo_fechamento"] = None

    def interagir(contexto, jogador):
        tempo_ms = pygame.time.get_ticks()
        if not pe_de_cabra["coletado"]:
            distancia = math.hypot(
                jogador.get_rect().centerx -
                pe_de_cabra["pos"][0],

                jogador.get_rect().centery -
                pe_de_cabra["pos"][1]
            )

            if distancia <= 60:
                pe_de_cabra["coletado"] = True
                jogador.tem_pe_de_cabra = True

                _definir_mensagem(
                    contexto,
                    "Você pegou o pé de cabra!",
                    tempo_ms
                )

                return

        if (
            pe_de_cabra["coletado"]
            and sala.jogador_na_porta(jogador)
        ):
            sala.porta_aberta = True

            _definir_mensagem(
                contexto,
                "Você arrombou a porta!",
                tempo_ms,
                3000
            )

    def atualizar(contexto, jogador, teclas, tempo_ms):

        if contexto["tempo_inicio"] + 2500 < tempo_ms:
            for guarda in guardas:
                guarda.surgir(tempo_ms)

        for guarda in guardas:
            guarda.perseguir(
                jogador,
                sala.paredes_colisao(),
                tempo_ms,
                guardas
            )

            guarda.tentar_atacar(
                jogador,
                tempo_ms
            )

        if (
            sala.porta_aberta
            and sala.jogador_na_porta(jogador)
        ):
            contexto["final"] = True

    def desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        for caixa in obstaculos:
            pygame.draw.rect(
                surf,
                (105, 70, 45),
                caixa,
                border_radius=4
            )

            pygame.draw.rect(
                surf,
                (50, 30, 20),
                caixa,
                width=3,
                border_radius=4
            )

        for x, y in [
            (250, 100),
            (700, 100),
            (1150, 100),
            (1600, 100)
        ]:
            cor = (
                (255, 40, 40)
                if (tempo_ms // 300) % 2 == 0
                else (80, 20, 20)
            )

            pygame.draw.circle(
                surf,
                cor,
                (x, y),
                10
            )

        for guarda in guardas:
            guarda.desenhar(
                surf,
                tempo_ms
            )

        if not pe_de_cabra["coletado"]:
            pygame.draw.line(
                surf,
                (180, 140, 70),
                (
                    pe_de_cabra["pos"][0] - 15,
                    pe_de_cabra["pos"][1] + 8
                ),
                (
                    pe_de_cabra["pos"][0] + 15,
                    pe_de_cabra["pos"][1] - 8
                ),
                6
            )

    contexto["ao_interagir"] = interagir
    contexto["ao_atualizar"] = atualizar
    contexto["ao_desenhar_extra"] = desenhar_extra

    def status(contexto):
        if pe_de_cabra["coletado"]:
            return "Pé de cabra encontrado. Arrombe a porta!"

        return "Corra! Encontre uma saída."

    contexto["texto_status"] = status

    return contexto


def nivel_12(jogador, resetar_jogador=False):
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.agachado = False

    sala = Sala(
        1800,
        1100,
        (100, 500),
        largura_tela=LARGURA,
        altura_tela=ALTURA
    )
    jogador.x, jogador.y = sala.ponto_entrada
    jogador.agachado = False

    sala.porta_aberta = True

    documentos = [
        Documento(
            400,
            300,
            "Ficha: Paciente 724. Estado: instável.",
            especial=False
        ),

        Documento(
            750,
            600,
            "Relatório: o paciente afirma ouvir uma voz.",
            especial=False
        ),

        Documento(
            1100,
            350,
            "Ficha do paciente: Operário 724.",
            especial=True
        )
    ]

    janela = pygame.Rect(
        1600,
        450,
        100,
        150
    )

    contexto = _estado_base(
        sala,
        12,
        objetos=[],
        documentos=documentos,
        mensagem_intro=(
            'Você entra em uma grande biblioteca. '
            'A VOZ: "PARE!"'
        ),
        duracao_intro=4000,
        taxa_dano_sanidade=0.003,
        texto_status="Procure uma saída."
    )

    contexto["ficha_encontrada"] = False
    contexto["voz_revelada"] = False

    def interagir(contexto, jogador):
        tempo_ms = pygame.time.get_ticks()

        for documento in documentos:
            if documento.coletado:
                continue

            if jogador.get_rect().colliderect(
                documento.rect.inflate(30, 30)
            ):
                documento.coletado = True

                if documento.especial:
                    contexto["ficha_encontrada"] = True
                    contexto["voz_revelada"] = True

                    _definir_mensagem(
                        contexto,
                        (
                            'Você encontra sua própria ficha. '
                            '"Paciente 724"... A voz era a sua própria mente.'
                        ),
                        tempo_ms,
                        6000
                    )

                else:
                    _definir_mensagem(
                        contexto,
                        documento.texto,
                        tempo_ms,
                        3500
                    )

                return

        if (
            contexto["ficha_encontrada"]
            and jogador.get_rect().colliderect(
                janela.inflate(30, 30)
            )
        ):
            contexto["final"] = True

    def atualizar(contexto, jogador, teclas, tempo_ms):

        if contexto["ficha_encontrada"]:

            if (
                tempo_ms -
                contexto["tempo_inicio"]
            ) > 5000:

                contexto["texto_status"] = (
                    "A voz não desaparece. "
                    "Vá até a janela!"
                )

    def desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):

        for x in [250, 600, 950, 1300]:
            pygame.draw.rect(
                surf,
                (70, 45, 30),
                (x, 120, 160, 60)
            )

            pygame.draw.rect(
                surf,
                (70, 45, 30),
                (x, 800, 160, 60)
            )

        for documento in documentos:
            documento.desenhar(surf)

        pygame.draw.rect(
            surf,
            (30, 50, 80),
            janela
        )

        pygame.draw.rect(
            surf,
            (180, 180, 190),
            janela,
            width=5
        )

        pygame.draw.line(
            surf,
            (180, 180, 190),
            (janela.centerx, janela.top),
            (janela.centerx, janela.bottom),
            5
        )

        if contexto["ficha_encontrada"]:

            for y in [250, 500, 750]:
                pygame.draw.circle(
                    surf,
                    (180, 180, 180),
                    (1500, y),
                    8
                )

    contexto["ao_interagir"] = interagir
    contexto["ao_atualizar"] = atualizar
    contexto["ao_desenhar_extra"] = desenhar_extra

    def status(contexto):
        if not contexto["ficha_encontrada"]:
            return "Encontre documentos e descubra quem é o Paciente 724."

        return "A voz nunca irá desaparecer. Vá até a janela!"

    contexto["texto_status"] = status

    return contexto