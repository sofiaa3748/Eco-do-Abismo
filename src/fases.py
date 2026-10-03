import pygame
import random
import math

from configuracoes import LARGURA, ALTURA, AZUL_ESCURO, BRANCO, CINZA_BORDA, VERDE_GAS, VERMELHO_ALARME
from nivel import Sala
from personagem import Inimigo
from itens import gerar_frascos_na_sala, Dica, Documento, Chave, MascaraGas
from interface_usuario import (desenhar_hud, desenhar_mensagem_contextual, desenhar_flash_detectado,
                                desenhar_barra_oxigenio, desenhar_overlay_gas,
                                desenhar_escuridao_com_lanterna)
from puzzle import (CaixaArrastavel, PuzzleCaixaFerramentas, PuzzlePainelSenha, PuzzleCofre,
                    PuzzleValvulas, PuzzleFuzil)

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


NIVEIS = {
    1: nivel_1, 2: nivel_2, 3: nivel_3, 4: nivel_4, 5: nivel_5, 6: nivel_6, 9: nivel_9, 10: nivel_10, 11: nivel_11, 12: nivel_12
}


def iniciar_sala(jogador, nivel, resetar_jogador=False):
    fn = NIVEIS.get(nivel, nivel_1)
    contexto = fn(jogador, resetar_jogador=resetar_jogador)
    contexto["tempo_inicio"] = pygame.time.get_ticks()
    return contexto


def renderizar_jogo(tela, jogador, contexto, offset_x, offset_y, flash_ativo,
                     fonte_sub, sprites_jogador=None):
    sala = contexto["sala"]
    tempo_ms = pygame.time.get_ticks()

    superficie_mundo = pygame.Surface((sala.largura, sala.altura))
    superficie_mundo.fill(AZUL_ESCURO)
    cone_surf = pygame.Surface((sala.largura, sala.altura), pygame.SRCALPHA)

    sala.desenhar(superficie_mundo)

    for f in contexto["frascos"]:
        f.desenhar(superficie_mundo)

    for obj in contexto["objetos"]:
        obj.desenhar(superficie_mundo)

    duto = contexto["duto"]
    if duto:
        pygame.draw.rect(superficie_mundo, (50, 50, 55), duto["corredor"])
        pygame.draw.rect(superficie_mundo, (80, 80, 85), duto["corredor"], width=2)
        if not duto["porta_entrada_aberta"]:
            pygame.draw.rect(superficie_mundo, (140, 140, 150), duto["rect_entrada"])
        if not duto["porta_saida_aberta"]:
            pygame.draw.rect(superficie_mundo, (140, 140, 150), duto["rect_saida"])

    caixa_ferramentas = contexto.get("caixa_ferramentas")
    if caixa_ferramentas:
        coberta = any(c.rect.colliderect(caixa_ferramentas) for c in contexto["caixas"])
        if not coberta:
            pygame.draw.rect(superficie_mundo, (150, 35, 35), caixa_ferramentas, border_radius=3)
            pygame.draw.rect(superficie_mundo, (220, 200, 50), (caixa_ferramentas.x + 10, caixa_ferramentas.y, 10, 4))

    for cx in contexto["caixas"]:
        cx.desenhar(superficie_mundo)

    if contexto.get("ao_desenhar_extra"):
        contexto["ao_desenhar_extra"](contexto, superficie_mundo, jogador, fonte_sub, tempo_ms)

    for camera in contexto["cameras"]:
        camera.atualizar()
        camera.desenhar(superficie_mundo, cone_surf, jogador)

    for guarda in contexto["guardas"]:
        guarda.desenhar(superficie_mundo, cone_surf, jogador)

    isca = contexto.get("isca")
    if isca and not isca["usada"]:
        pygame.draw.circle(superficie_mundo, (200, 180, 90), isca["rect"].center, 9)

    superficie_mundo.blit(cone_surf, (0, 0))

    if sprites_jogador:
        jogador.desenhar(superficie_mundo, sprites_jogador)
    else:
        cor_player = (180, 220, 255) if getattr(jogador, 'agachado', False) else BRANCO
        pygame.draw.rect(superficie_mundo, cor_player, jogador.get_rect(), border_radius=4)

    cam_x, cam_y = sala.calcular_camera(jogador)
    area_visivel = pygame.Rect(cam_x, cam_y, sala.largura_tela, sala.altura_tela)
    tela.blit(superficie_mundo, (offset_x, offset_y), area=area_visivel)

    desenhar_hud(tela, jogador, fonte_sub)

    y_status = 100
    if contexto.get("usa_oxigenio"):
        desenhar_barra_oxigenio(tela, jogador, fonte_sub)
        y_status = 175

    texto_status_fn = contexto.get("texto_status")
    if texto_status_fn:
        linha = texto_status_fn(contexto)
        if linha:
            txt = fonte_sub.render(linha, True, (210, 220, 255))
            tela.blit(txt, (20, y_status))

    texto_nivel = fonte_sub.render(f"SALA {contexto['nivel']}", True, CINZA_BORDA)
    tela.blit(texto_nivel, (LARGURA - texto_nivel.get_width() - 20, 20))

    if contexto.get("tint_gas"):
        desenhar_overlay_gas(tela, LARGURA, ALTURA, intensidade=70)

    if contexto.get("usa_lanterna"):
        pos_tela = (jogador.get_rect().centerx - cam_x + offset_x, jogador.get_rect().centery - cam_y + offset_y)
        desenhar_escuridao_com_lanterna(tela, pos_tela, LARGURA, ALTURA,
                                         ligada=getattr(jogador, "lanterna_ligada", False))

    intro = contexto.get("mensagem_intro")
    if intro and tempo_ms - contexto["tempo_inicio"] < contexto.get("duracao_intro", 4500):
        desenhar_mensagem_contextual(tela, intro, LARGURA, ALTURA, fonte_sub, y=ALTURA - 70)

    msg = contexto.get("mensagem_temporaria")
    if msg and tempo_ms < contexto.get("mensagem_temporaria_expira", 0):
        desenhar_mensagem_contextual(tela, msg, LARGURA, ALTURA, fonte_sub, y=ALTURA - 40)

    puzzle_modal = contexto.get("puzzle_modal")
    if puzzle_modal and getattr(puzzle_modal, "ativo", False):
        puzzle_modal.desenhar(tela, fonte_sub)

    if flash_ativo:
        desenhar_flash_detectado(tela, LARGURA, ALTURA)

def nivel_9(jogador, reset=True):
    if reset:
        jogador.sanidade = 100
        jogador.agachado = False

    sala = Sala(
        1500,
        900,
        (100, 430),
        largura_tela=LARGURA,
        altura_tela=ALTURA
    )

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

    def interagir(jogador, tempo_ms):
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

    def atualizar(jogador, tempo_ms):
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

    def desenhar_extra(surf, tempo_ms):
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

    def status():
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

def nivel_10(jogador, reset=True):
    if reset:
        jogador.sanidade = 100
        jogador.agachado = False

    sala = Sala(
        1700,
        950,
        (90, 450),
        largura_tela=LARGURA,
        altura_tela=ALTURA
    )

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

    def interagir(jogador, tempo_ms):
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

    def atualizar(jogador, tempo_ms):
        if sala.porta_aberta and sala.jogador_na_porta(jogador):
            contexto["final"] = True

    def desenhar_extra(surf, tempo_ms):
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

    def status():
        if puzzle_fuzil.consertado:
            return "Fuzil reparado. Atravesse o pátio!"

        return (
            f"Reparo do fuzil: "
            f"{puzzle_fuzil.golpes}/"
            f"{puzzle_fuzil.golpes_necessarios}"
        )

    contexto["texto_status"] = status

    return contexto

def nivel_11(jogador, reset=True):
    if reset:
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
        guardas=guardas,
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

    def interagir(jogador, tempo_ms):
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

    def atualizar(jogador, tempo_ms):

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

    def desenhar_extra(surf, tempo_ms):
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

    def status():
        if pe_de_cabra["coletado"]:
            return "Pé de cabra encontrado. Arrombe a porta!"

        return "Corra! Encontre uma saída."

    contexto["texto_status"] = status

    return contexto

def nivel_12(jogador, reset=True):
    if reset:
        jogador.sanidade = 100
        jogador.agachado = False

    sala = Sala(
        1800,
        1100,
        (100, 500),
        largura_tela=LARGURA,
        altura_tela=ALTURA
    )

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

    def interagir(jogador, tempo_ms):

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

    def atualizar(jogador, tempo_ms):

        if contexto["ficha_encontrada"]:

            if (
                tempo_ms -
                contexto["tempo_inicio"]
            ) > 5000:

                contexto["texto_status"] = (
                    "A voz não desaparece. "
                    "Vá até a janela!"
                )

    def desenhar_extra(surf, tempo_ms):

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
            janela.centerx,
            janela.top,
            janela.centerx,
            janela.bottom
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

    def status():
        if not contexto["ficha_encontrada"]:
            return "Encontre documentos e descubra quem é o Paciente 724."

        return "A voz nunca irá desaparecer. Vá até a janela!"

    contexto["texto_status"] = status

    return contexto