import pygame
import random
import math

from configuracoes import LARGURA, ALTURA, AZUL_ESCURO, BRANCO, CINZA_BORDA, VERDE_GAS, VERMELHO_ALARME
from nivel import Sala
from personagem import Inimigo, GuardaPrisao
from sprites import (VultoSprite, GuardaSprite, GuardaPrisaoSprite, desenhar_jogador, desenhar_caixa,
                     blit_centro)
from itens import gerar_frascos_na_sala, Dica, Documento, Chave, MascaraGas
from interface_usuario import (desenhar_hud, desenhar_mensagem_contextual, desenhar_flash_detectado,
                                desenhar_barra_oxigenio, desenhar_overlay_gas,
                                desenhar_escuridao_com_lanterna, _quebrar_linhas)
from configuracoes import CIANO_BRILHO
from itens import FrascoSanidade
from audio import AudioEspacial, sons
from mapas import TEMA_POR_NIVEL, desenhar_estante, desenhar_duto
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


def _golpe_reparo(puzzle):
    """Golpe no reparo (vazamento / fuzil) com o som certo."""
    sons.tocar("golpe")
    feito = puzzle.golpear()
    if feito:
        sons.tocar("sucesso")
    return feito


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
    contexto["puzzle_modal"] = puzzle_senha

    def ao_interagir(contexto, jogador):
        for dica in contexto["objetos"]:
            if not dica.coletada and jogador.get_rect().colliderect(dica.rect.inflate(16, 16)):
                dica.coletada = True
                contexto["puzzle_senha"].registrar_pista(dica.indice, dica.valor)
                _definir_mensagem(contexto, "Fragmento de senha encontrado.", pygame.time.get_ticks(), 1600)
                return

        sala = contexto["sala"]
        if not sala.porta_aberta and sala.jogador_na_porta(jogador):
            if contexto["puzzle_senha"].completo():
                contexto["puzzle_senha"].ativo = True
            else:
                _definir_mensagem(contexto, "O painel exige quatro fragmentos. Continue procurando pela sala.", pygame.time.get_ticks(), 2200)

    def ao_atualizar(contexto, jogador, teclas, tempo_ms):
        if contexto["puzzle_senha"].resolvido:
            sala.porta_aberta = True

    def texto_status(contexto):
        puzzle = contexto["puzzle_senha"]
        if puzzle.resolvido:
            return "Senha aceita. A porta está destrancada."
        return f'Fragmentos: {sum(v is not None for v in puzzle.pistas_coletadas)}/4 | Pistas: {puzzle.texto_progresso()}'

    contexto["ao_interagir"] = ao_interagir
    contexto["ao_atualizar"] = ao_atualizar
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

    pistas_cofre = [
        Documento(250, 170, 'Fragmento de prontuário: "A senha possui seis letras e começa com AB."'),
        Documento(1180, 210, 'Papel dobrado: "As duas letras centrais são IS."'),
        Documento(280, 740, 'Recado quase apagado: "O código termina com MO."'),
    ]
    pistas_cofre_lidas = set()
    chave = Chave(1100, 590, rotulo="Chave da Porta")

    contexto = _estado_base(
        sala, 2,
        caixas=caixas,
        objetos=pistas_cofre,
        mensagem_intro='A VOZ: "A saída está trancada. Procure a chave — e descubra a palavra que abre o cofre."',
    )
    contexto["cofre"] = cofre
    contexto["puzzle_modal"] = cofre
    contexto["chave"] = chave
    contexto["sabe_palavra_chave"] = False
    contexto["tem_chave"] = False

    def ao_interagir(contexto, jogador):
        # Recupera a sala antes de qualquer uso (inclusive ao mover as caixas).
        sala = contexto["sala"]
        agora = pygame.time.get_ticks()
        for indice, pista in enumerate(pistas_cofre):
            if not pista.coletado and jogador.get_rect().colliderect(pista.rect.inflate(16, 16)):
                pista.coletado = True
                pistas_cofre_lidas.add(indice)
                _definir_mensagem(contexto, pista.texto, agora, 4000)
                if len(pistas_cofre_lidas) == len(pistas_cofre):
                    contexto["sabe_palavra_chave"] = True
                    _definir_mensagem(contexto, "Os três fragmentos formam uma palavra de seis letras.", agora, 4500)
                return

        # Empurre as caixas para descobrir a placa escondida no piso.
        centro_j = jogador.get_rect().center
        for caixa in contexto["caixas"]:
            if jogador.get_rect().inflate(34, 34).colliderect(caixa.rect):
                dx = caixa.rect.centerx - centro_j[0]
                dy = caixa.rect.centery - centro_j[1]
                deslocamento = (65 if dx >= 0 else -65, 0) if abs(dx) >= abs(dy) else (0, 65 if dy >= 0 else -65)
                novo = caixa.rect.move(*deslocamento)
                novo.clamp_ip(pygame.Rect(45, 45, sala.largura - 90, sala.altura - 90))
                outras = [c.rect for c in contexto["caixas"] if c is not caixa]
                if not any(novo.colliderect(r) for r in outras):
                    caixa.rect = novo
                    _definir_mensagem(contexto, "A caixa deslizou. Continue limpando a área da placa.", agora, 1800)
                return

        cofre = contexto["cofre"]
        cofre.checar_revelado(contexto["caixas"])
        if cofre.revelado and not cofre.aberto and jogador.get_rect().colliderect(cofre.rect_placa.inflate(20, 20)):
            if contexto["sabe_palavra_chave"]:
                cofre.tentar_abrir(True)
            else:
                _definir_mensagem(contexto, "O cofre pede uma palavra-chave. Encontre os três fragmentos.", agora)

        if contexto["tem_chave"] and not sala.porta_aberta and sala.jogador_na_porta(jogador):
            sala.porta_aberta = True

    def ao_desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        contexto["cofre"].checar_revelado(contexto["caixas"])
        if not contexto["cofre"].ativo:
            contexto["cofre"].desenhar(surf, fonte)
        if not contexto["chave"].coletada:
            contexto["chave"].desenhar(surf)

    def texto_status(contexto):
        if contexto["tem_chave"]:
            return "VOCÊ TEM: Chave da Porta"
        if len(pistas_cofre_lidas) < len(pistas_cofre):
            return f"Fragmentos da senha: {len(pistas_cofre_lidas)}/3 | Empurre as caixas para revelar o cofre."
        if not contexto["cofre"].revelado:
            return "Senha descoberta. Desobstrua a placa do cofre empurrando as caixas."
        return "O cofre foi revelado. Digite a palavra formada pelos três fragmentos."

    def ao_atualizar(contexto, jogador, teclas, tempo_ms):
        if contexto["cofre"].aberto and not contexto["tem_chave"]:
            contexto["tem_chave"] = True
            chave.coletada = True
            sons.tocar("chave")
            _definir_mensagem(contexto, "O cofre abriu. Você encontrou a chave da porta.", tempo_ms, 3000)

    contexto["ao_interagir"] = ao_interagir
    contexto["ao_atualizar"] = ao_atualizar
    contexto["ao_desenhar_extra"] = ao_desenhar_extra
    contexto["texto_status"] = texto_status
    return contexto


def nivel_3(jogador, resetar_jogador=False):
    """Escritório de investigação: leia documentos, descubra o código e pegue a chave."""
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.tem_pe_de_cabra = False
    jogador.agachado = False

    moveis = [
        pygame.Rect(430, 145, 190, 78),   # mesa de trabalho
        pygame.Rect(760, 145, 190, 78),   # mesa com computador
        pygame.Rect(300, 520, 170, 75),   # arquivo baixo
        pygame.Rect(760, 570, 180, 75),   # armário de documentos
        pygame.Rect(1080, 270, 105, 175), # estante lateral
    ]
    sala = Sala(1450, 900, ponto_entrada=(90, 430), largura_tela=LARGURA,
                altura_tela=ALTURA, obstaculos=moveis)
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = False

    # Cada relatório revela um algarismo. A ficha do mapa é um documento separado.
    documentos_codigo = [
        Documento(245, 190, 'Relatório de acesso: "O primeiro número do código é 7."'),
        Documento(680, 300, 'Registro de plantão: "O segundo número anotado foi 2."'),
        Documento(1120, 690, 'Relatório técnico: "O terceiro número é 4."'),
        Documento(500, 760, 'Bilhete do supervisor: "O último número do código é 9."'),
    ]
    documento_mapa = Documento(
        1120, 180,
        'Mapa da instalação: a saída fica no corredor leste. A anotação no verso diz: '
        '"A chave da porta foi guardada na gaveta do escritório."', especial=True
    )
    documentos = documentos_codigo + [documento_mapa]
    puzzle_senha = PuzzlePainelSenha(['7', '2', '4', '9'])
    chave = Chave(1015, 690, rotulo="Chave da saída")
    chave_disponivel = {"valor": False}
    mapa_lido = {"valor": False}

    contexto = _estado_base(
        sala, 3,
        objetos=documentos,
        mensagem_intro='A VOZ: "Este lugar era um escritório. Leia os relatórios. Um deles pode explicar por que você está aqui."',
        duracao_intro=5200,
    )
    contexto["puzzle_senha"] = puzzle_senha
    contexto["puzzle_modal"] = puzzle_senha
    contexto["chave_escritorio"] = chave
    contexto["documentos_codigo"] = documentos_codigo
    contexto["mapa_lido"] = mapa_lido

    def ao_interagir(c, j):
        agora = pygame.time.get_ticks()
        rect_j = j.get_rect()

        # Ler documentos é obrigatório para descobrir todos os quatro algarismos.
        for doc in documentos:
            if not doc.coletado and rect_j.colliderect(doc.rect.inflate(24, 24)):
                doc.coletado = True
                _definir_mensagem(c, doc.texto, agora, 4300)
                if doc is documento_mapa:
                    mapa_lido["valor"] = True
                    _definir_mensagem(c, "Mapa encontrado. A saída fica no corredor leste; falta recuperar a chave na gaveta.", agora, 4300)
                elif all(d.coletado for d in documentos_codigo):
                    _definir_mensagem(c, "Você reuniu os quatro algarismos. Procure o painel da gaveta.", agora, 3200)
                return

        # Painel da gaveta: só pode ser usado depois da leitura dos quatro relatórios.
        painel_gaveta = pygame.Rect(1000, 520, 65, 48)
        if rect_j.colliderect(painel_gaveta.inflate(45, 45)) and not puzzle_senha.resolvido:
            if all(d.coletado for d in documentos_codigo):
                puzzle_senha.ativo = True
                puzzle_senha.mensagem = "Digite os quatro números dos relatórios."
            else:
                lidos = sum(d.coletado for d in documentos_codigo)
                _definir_mensagem(c, f"A gaveta tem um painel. Relatórios encontrados: {lidos}/4.", agora, 2600)
            return

        # Depois de abrir a gaveta, recolha a chave com E.
        if chave_disponivel["valor"] and not chave.coletada and rect_j.colliderect(chave.rect.inflate(35, 35)):
            chave.coletada = True
            c["tem_chave_saida"] = True
            sons.tocar("chave")
            _definir_mensagem(c, "Você pegou a chave da porta de saída.", agora, 2600)
            return

        if sala.jogador_na_porta(j):
            if c.get("tem_chave_saida") and mapa_lido["valor"]:
                sala.porta_aberta = True
                _definir_mensagem(c, "A chave girou. O mapa indica o caminho: siga para o leste.", agora, 2800)
            elif not mapa_lido["valor"]:
                _definir_mensagem(c, "A porta precisa de uma chave. O mapa pode indicar onde encontrá-la.", agora, 2800)
            else:
                _definir_mensagem(c, "A porta está trancada. Encontre a chave na gaveta do escritório.", agora, 2800)

    def ao_atualizar(c, j, teclas, tempo_ms):
        if puzzle_senha.resolvido and not chave_disponivel["valor"]:
            chave_disponivel["valor"] = True
            _definir_mensagem(c, "Código correto! A gaveta abriu e revelou uma chave.", tempo_ms, 3200)
        if c.get("tem_chave_saida") and mapa_lido["valor"]:
            # A porta só fica liberada depois de cumprir os dois objetivos.
            c["sala"].porta_aberta = True

    def ao_desenhar_extra(c, surf, j, fonte, tempo_ms):
        # Mobiliário desenhado por cima do piso para deixar o escritório legível.
        for r, tom in zip(moveis, ((82, 58, 42), (70, 76, 84), (92, 72, 52), (58, 66, 76), (72, 78, 82))):
            pygame.draw.rect(surf, (30, 32, 38), r.move(0, 7), border_radius=4)
            pygame.draw.rect(surf, tom, r, border_radius=4)
            pygame.draw.rect(surf, (145, 130, 105), r, 2, border_radius=4)
        # Computador antigo e luminária sobre a mesa superior.
        pygame.draw.rect(surf, (25, 32, 38), (805, 158, 78, 48), border_radius=3)
        pygame.draw.rect(surf, (75, 115, 112), (811, 164, 66, 34), border_radius=2)
        pygame.draw.line(surf, (150, 150, 140), (844, 206), (844, 215), 4)
        pygame.draw.line(surf, (150, 150, 140), (828, 216), (860, 216), 4)
        # Painel da gaveta, destacado visualmente.
        pygame.draw.rect(surf, (38, 44, 52), (1000, 520, 65, 48), border_radius=4)
        pygame.draw.rect(surf, (180, 155, 90), (1000, 520, 65, 48), 2, border_radius=4)
        pygame.draw.circle(surf, (65, 220, 150) if puzzle_senha.resolvido else (220, 170, 65), (1032, 544), 6)
        if chave_disponivel["valor"] and not chave.coletada:
            chave.desenhar(surf)
        if puzzle_senha.resolvido:
            # Gaveta aberta, com interior escuro.
            pygame.draw.rect(surf, (24, 25, 29), (990, 575, 92, 48), border_radius=3)
            pygame.draw.rect(surf, (115, 90, 62), (990, 575, 92, 48), 3, border_radius=3)

    def texto_status(c):
        lidos = sum(d.coletado for d in documentos_codigo)
        if not puzzle_senha.resolvido:
            return f"Relatórios para o código: {lidos}/4 | Leia todos e examine o painel da gaveta."
        if not chave.coletada:
            return "Gaveta aberta: pegue a chave e encontre o mapa da saída." if not mapa_lido["valor"] else "Pegue a chave da gaveta e siga o mapa até a porta leste."
        if not mapa_lido["valor"]:
            return "Chave encontrada. Ainda falta localizar e ler o mapa da instalação."
        return "Chave e mapa encontrados. A saída fica no corredor leste."

    contexto["ao_interagir"] = ao_interagir
    contexto["ao_atualizar"] = ao_atualizar
    contexto["ao_desenhar_extra"] = ao_desenhar_extra
    contexto["texto_status"] = texto_status
    return contexto


def _desenhar_portinha_duto(surf, rect, aberta, tempo_ms):
    """Portinha (grade de ventilação) que dá acesso à sala do duto."""
    pygame.draw.rect(surf, (30, 32, 38), rect.inflate(10, 10), border_radius=3)
    if aberta:
        pygame.draw.rect(surf, (6, 6, 10), rect)
        brilho = 30 + int(20 * math.sin(tempo_ms / 300))
        halo = pygame.Surface(rect.size, pygame.SRCALPHA)
        halo.fill((120, 200, 255, brilho))
        surf.blit(halo, rect.topleft)
        # tampa pendurada de lado
        pygame.draw.polygon(surf, (120, 124, 136), [
            (rect.x, rect.y), (rect.x + 14, rect.y + 4),
            (rect.x + 10, rect.bottom - 2), (rect.x, rect.bottom)])
    else:
        pygame.draw.rect(surf, (150, 154, 166), rect)
        for yy in range(rect.y + 6, rect.bottom - 4, 9):
            pygame.draw.line(surf, (96, 100, 112), (rect.x + 3, yy), (rect.right - 4, yy), 2)
        for px, py in ((rect.x + 5, rect.y + 5), (rect.right - 6, rect.y + 5),
                       (rect.x + 5, rect.bottom - 6), (rect.right - 6, rect.bottom - 6)):
            pygame.draw.circle(surf, (60, 64, 74), (px, py), 3)
    pygame.draw.rect(surf, (80, 84, 96), rect, 2, border_radius=2)


def nivel_3c(jogador, resetar_jogador=False):
    """Corredor de fuga: os guardas invadem pela extremidade oposta à entrada."""
    jogador.agachado = False
    sala = Sala(
        2050, 850, ponto_entrada=(100, 420), largura_tela=LARGURA, altura_tela=ALTURA,
        lado_porta="direita",
        obstaculos=[
            pygame.Rect(500, 180, 110, 165), pygame.Rect(760, 510, 145, 125),
            pygame.Rect(1120, 190, 115, 160), pygame.Rect(1450, 505, 150, 125)
        ]
    )
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = True
    esconderijos = [
        pygame.Rect(465, 160, 180, 205), pygame.Rect(730, 485, 205, 175),
        pygame.Rect(1085, 170, 185, 205), pygame.Rect(1415, 480, 220, 175)
    ]
    # O jogador entra pela esquerda; os inimigos invadem pela direita.
    guardas = [
        GuardaPrisaoSprite(1950, 110, rota=[(1950, 110), (1500, 110), (1950, 110)],
                           angulo=180, velocidade=2.75, alcance=390, abertura=78,
                           pausa_ms=180, tempo_vista_em_pe=480, tempo_vista_agachado=900),
        GuardaPrisaoSprite(1950, 740, rota=[(1950, 740), (1480, 740), (1950, 740)],
                           angulo=180, velocidade=2.9, alcance=410, abertura=82,
                           pausa_ms=120, tempo_vista_em_pe=450, tempo_vista_agachado=850),
    ]
    for guarda in guardas:
        guarda.definir_mundo(sala.paredes_colisao())

    contexto = _estado_base(
        sala, "3C", guardas=guardas,
        mensagem_intro='A VOZ: "Eles fecharam o setor! Estão entrando pelo outro lado. Não fique no corredor aberto."',
        duracao_intro=4200, taxa_dano_sanidade=0.003,
        condicao_transicao=lambda c, j: c["sala"].jogador_na_porta(j)
    )
    contexto["esconderijos"] = esconderijos
    contexto["inicio_perseguicao"] = None
    contexto["onda_2"] = False

    def atualizar(c, j, teclas, tempo_ms):
        if c["inicio_perseguicao"] is None:
            c["inicio_perseguicao"] = tempo_ms + 900
        if tempo_ms >= c["inicio_perseguicao"]:
            for indice, guarda in enumerate(guardas):
                if indice == 2 and tempo_ms < c["inicio_perseguicao"] + 3200:
                    continue
                if indice == 2:
                    c["onda_2"] = True
                if guarda.atualizar(j, esconderijos, tempo_ms):
                    j.dano_sanidade(12)
                    guarda.reiniciar()
                    _definir_mensagem(c, "Você foi localizado! Quebre a linha de visão e mude de esconderijo.", tempo_ms, 2200)

    def desenhar(c, surf, j, fonte, tempo_ms):
        for r in esconderijos:
            pygame.draw.rect(surf, (40, 46, 58), r, border_radius=5)
            pygame.draw.rect(surf, (115, 125, 145), r, 3, border_radius=5)
            pygame.draw.line(surf, (22, 26, 36), (r.centerx, r.y + 8), (r.centerx, r.bottom - 8), 4)
        for x in range(180, 2000, 240):
            cor = (150, 35, 35) if (tempo_ms // 350) % 2 else (65, 22, 25)
            pygame.draw.circle(surf, cor, (x, 75), 8)

    contexto["ao_atualizar"] = atualizar
    contexto["ao_desenhar_extra"] = desenhar
    contexto["texto_status"] = lambda c: "Fuja até a porta à direita. Agache (Q) nos recuos e evite os cones de visão."
    return contexto


def nivel_4(jogador, resetar_jogador=False):
    """Sala de manutenção: destranque a caixa e procure o pé de cabra entre as ferramentas."""
    if resetar_jogador:
        jogador.sanidade = 100
        jogador.tem_pe_de_cabra = False
    jogador.agachado = False

    # Móveis formam obstáculos físicos e dão aparência de sala de manutenção.
    moveis = [
        pygame.Rect(250, 145, 190, 82), pygame.Rect(520, 115, 105, 170),
        pygame.Rect(1010, 145, 190, 82), pygame.Rect(1260, 380, 105, 190),
        pygame.Rect(260, 520, 150, 90), pygame.Rect(950, 690, 180, 90),
    ]
    sala = Sala(1500, 950, ponto_entrada=(90, 470), largura_tela=LARGURA,
                altura_tela=ALTURA, pos_porta=pygame.Rect(-200, -200, 1, 1),
                obstaculos=moveis)
    jogador.x, jogador.y = sala.ponto_entrada
    sala.porta_aberta = False

    # Caixotes decorativos ficam ao lado da caixa de ferramentas, sem bloquear a interação.
    caixas = [CaixaArrastavel(625, 650), CaixaArrastavel(900, 650)]
    caixa_ferramentas = pygame.Rect(760, 635, 58, 42)
    puzzle_caixa = PuzzleCaixaFerramentas(LARGURA, ALTURA)
    portinha = {"rect": pygame.Rect(1180, 44, 70, 56), "aberta": False}

    def entrou_na_portinha(contexto, jogador):
        return (portinha["aberta"] and jogador.agachado
                and jogador.get_rect().colliderect(portinha["rect"].inflate(6, 6)))

    contexto = _estado_base(
        sala, 4, caixas=caixas,
        mensagem_intro='A VOZ: "A sala de manutenção. Afaste o entulho e procure uma ferramenta para abrir o duto."',
        condicao_transicao=entrou_na_portinha,
    )
    contexto["caixa_ferramentas"] = caixa_ferramentas
    contexto["portinha"] = portinha
    contexto["puzzle_caixa"] = puzzle_caixa
    contexto["puzzle_modal"] = puzzle_caixa

    def ao_interagir(contexto, jogador):
        tempo_ms = pygame.time.get_ticks()
        rect_p = jogador.get_rect()
        coberta = any(c.rect.colliderect(caixa_ferramentas) for c in contexto["caixas"])
        if rect_p.colliderect(caixa_ferramentas.inflate(34, 34)):
            if coberta:
                _definir_mensagem(contexto, "A caixa está bloqueada por entulho.", tempo_ms, 2600)
            elif not jogador.tem_pe_de_cabra and not puzzle_caixa.resolvido:
                puzzle_caixa.ativo = True
                _definir_mensagem(contexto, "A fechadura tem três pinos. Resolva para abrir a caixa.", tempo_ms, 2600)
            return

        if rect_p.colliderect(portinha["rect"].inflate(50, 50)):
            if not jogador.tem_pe_de_cabra:
                _definir_mensagem(contexto, "A portinha está parafusada. Procure uma ferramenta na sala.", tempo_ms, 2400)
            elif not portinha["aberta"]:
                portinha["aberta"] = True
                sons.tocar("arrombar")
                _definir_mensagem(contexto, "Você forçou a grade. Agache (Q) e entre no duto.", tempo_ms, 3200)
            elif not jogador.agachado:
                _definir_mensagem(contexto, "A abertura é baixa. Agache (Q) para entrar.", tempo_ms)

    def ao_desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        for indice, r in enumerate(moveis):
            cor = (73, 78, 88) if indice in (1, 3, 5) else (92, 70, 52)
            pygame.draw.rect(surf, (25, 28, 35), r.move(0, 7), border_radius=5)
            pygame.draw.rect(surf, cor, r, border_radius=5)
            pygame.draw.rect(surf, (130, 135, 145), r, 3, border_radius=5)
            if indice in (0, 2):
                pygame.draw.line(surf, (45, 48, 56), (r.x + 12, r.y + 22), (r.right - 12, r.y + 22), 4)
                for x in (r.x + 22, r.right - 22):
                    pygame.draw.rect(surf, (48, 51, 60), (x, r.bottom - 5, 9, 22))
            else:
                for y in range(r.y + 35, r.bottom - 12, 42):
                    pygame.draw.line(surf, (40, 44, 53), (r.x + 8, y), (r.right - 8, y), 5)
        pygame.draw.rect(surf, (38, 43, 52), caixa_ferramentas, border_radius=4)
        pygame.draw.rect(surf, (155, 120, 65), caixa_ferramentas, 3, border_radius=4)
        pygame.draw.line(surf, (190, 195, 205), (caixa_ferramentas.x + 9, caixa_ferramentas.y + 14),
                         (caixa_ferramentas.right - 9, caixa_ferramentas.y + 14), 3)
        if puzzle_caixa.resolvido and not jogador.tem_pe_de_cabra:
            jogador.tem_pe_de_cabra = True
            _definir_mensagem(contexto, "Você encontrou o pé de cabra! Agora abra a grade do duto.", tempo_ms, 3500)
        _desenhar_portinha_duto(surf, portinha["rect"], portinha["aberta"], tempo_ms)

    def texto_status(contexto):
        if not jogador.tem_pe_de_cabra:
            return "Pressione E na caixa de ferramentas: alinhe os pinos e arraste as ferramentas até a bancada."
        if not portinha["aberta"]:
            return "Use o pé de cabra na portinha do duto, na parede de cima (E)."
        return "Agache (Q) e entre pelo duto."

    contexto["ao_interagir"] = ao_interagir
    contexto["ao_desenhar_extra"] = ao_desenhar_extra
    contexto["texto_status"] = texto_status
    return contexto


def nivel_4b(jogador, resetar_jogador=False):
    """Sala do duto: um corredor baixo e estreito. Entra pela portinha da sala 4
    e sai por outra portinha, no fim, rumo à sala 5."""
    if resetar_jogador:
        jogador.sanidade = 100
    jogador.tem_pe_de_cabra = True  # só se chega aqui arrombando a portinha

    # paredes de cima e de baixo deixam um corredor de 160 px (y 220 a 380);
    # o jogador agachado tem 68 px de altura, então precisa caber folgado
    obstaculos = [
        pygame.Rect(40, 40, 1420, 180),
        pygame.Rect(40, 380, 1420, 180),
    ]
    saida = pygame.Rect(1460, 240, 40, 120)
    sala = Sala(1500, 600, ponto_entrada=(90, 200), largura_tela=LARGURA, altura_tela=ALTURA,
                pos_porta=saida, obstaculos=obstaculos)
    jogador.x, jogador.y = sala.ponto_entrada
    jogador.agachado = True
    sala.porta_aberta = False

    contexto = _estado_base(
        sala, "4B",
        mensagem_intro='Você rasteja pelo duto. Siga até o fim.',
        duracao_intro=3500,
        taxa_dano_sanidade=0.004,
    )

    def ao_interagir(contexto, jogador):
        tempo_ms = pygame.time.get_ticks()
        if jogador.get_rect().colliderect(saida.inflate(90, 60)):
            if not sala.porta_aberta:
                sala.porta_aberta = True
                _definir_mensagem(contexto, "Você arromba a portinha de saída.", tempo_ms)

    def ao_atualizar(contexto, jogador, teclas, tempo_ms):
        # o duto é baixo demais para ficar de pé
        jogador.agachado = True

    def ao_desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        # grades de ventilação e luz fraca vindo delas
        for x in range(200, 1400, 220):
            pygame.draw.rect(surf, (30, 32, 38), (x, 224, 60, 8))
            for k in range(3):
                pygame.draw.line(surf, (110, 114, 126), (x + 4, 226 + k * 2), (x + 56, 226 + k * 2))

    def texto_status(contexto):
        if not sala.porta_aberta:
            return "Chegue ao fim do duto e abra a portinha de saída (E)."
        return "A saída está aberta. Siga em frente."

    contexto["ao_interagir"] = ao_interagir
    contexto["ao_atualizar"] = ao_atualizar
    contexto["ao_desenhar_extra"] = ao_desenhar_extra
    contexto["texto_status"] = texto_status
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

    valvulas = PuzzleValvulas([(300, 190), (1000, 230), (560, 700)], ordem_correta=[0, 2, 1])
    valvulas.raio_interacao = 80
    pistas_valvulas = [
        Documento(180, 760, 'Relatório de pressão: "A válvula junto ao ralo deve ser a primeira a girar."'),
        Documento(1240, 760, 'Bilhete úmido: "A válvula do canto inferior vem logo depois da do ralo."'),
        Documento(1280, 180, 'Etiqueta arrancada: "A válvula perto do armário metálico encerra a sequência."'),
    ]
    pistas_valvulas_lidas = set()
    mascara = MascaraGas(rect_armario.centerx - 13, rect_armario.y + 30)
    vazamento = PuzzleFuzil((1290, 250), golpes_necessarios=3)
    vazamento.raio_interacao = 90

    contexto = _estado_base(
        sala, 5,
        objetos=pistas_valvulas,
        mensagem_intro='A VOZ: "O ar está acabando. Ache as três válvulas — e descubra a ordem antes que a pressão caia."',
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
        for indice, pista in enumerate(pistas_valvulas):
            if not pista.coletado and jogador.get_rect().colliderect(pista.rect.inflate(18, 18)):
                pista.coletado = True
                pistas_valvulas_lidas.add(indice)
                _definir_mensagem(contexto, pista.texto, agora, 4500)
                return

        valvulas = contexto["valvulas"]
        if len(pistas_valvulas_lidas) < len(pistas_valvulas):
            if valvulas.valvula_proxima(jogador):
                _definir_mensagem(contexto, "As válvulas estão numeradas apenas por marcas apagadas. Encontre os três registros para deduzir a ordem.", agora, 2600)
            return

        valvula = valvulas.valvula_proxima(jogador)
        if valvula:
            sucesso = valvulas.girar(valvula)
            sons.tocar("valvula" if sucesso else "disjuntor_erro")
            if not sucesso:
                _definir_mensagem(contexto, valvulas.ultima_mensagem, agora, 3000)
                return
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
                sons.tocar("coletar")
                _definir_mensagem(contexto, "Você pegou a máscara de gás!", agora)
            else:
                _definir_mensagem(contexto, "O armário está vazio.", agora)
            return

        vazamento = contexto["vazamento"]
        if vazamento.perto(jogador) and not vazamento.consertado:
            if not contexto["tem_mascara"]:
                _definir_mensagem(contexto, "O gás é denso demais. Você precisa da máscara.", agora)
            elif _golpe_reparo(vazamento):
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
        VultoSprite(1650, 120, velocidade=2.6, atraso_ms=0, lado_desvio=1),
        VultoSprite(1650, 740, velocidade=2.9, atraso_ms=600, lado_desvio=-1),
        VultoSprite(2050, 440, velocidade=2.3, atraso_ms=1200, lado_desvio=1),
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
        GuardaPrisaoSprite(380, 360, rota=[(380, 360), (1050, 360)], angulo=0, velocidade=1.3,
                     alcance=330, abertura=56, pausa_ms=1600),
        GuardaPrisaoSprite(1640, 360, rota=[(1640, 360), (1190, 360)], angulo=180, velocidade=1.3,
                     alcance=330, abertura=56, pausa_ms=1600),
        GuardaPrisaoSprite(3230, 275, angulo=180, varredura=22, alcance=380, abertura=62),
        GuardaPrisaoSprite(3230, 445, angulo=180, varredura=22, alcance=380, abertura=62),
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
        sons.tocar("preso")
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
            sons.tocar("arremesso")
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
            sons.tocar("chave")
            e["ruido"] += 45 if not jogador.agachado else 22
            _definir_mensagem(contexto, "Você pegou as chaves. Agora saia sem fazer barulho.", agora, 3500)
        elif not e["canecas_pegas"] and perto(jogador, canecas_prateleira, 70):
            e["canecas_pegas"] = True
            sons.tocar("coletar")
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
                    sons.tocar("tabua")
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
            sons.tocar_pos("clang", destino, jogador.get_rect().center, 1200)
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
            desenhar_caixa(surf, c)
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
    pistas_disjuntores = [
        Documento(220, 760, 'Esquema rasgado: "Comece pelo painel superior que fica mais à direita."'),
        Documento(720, 720, 'Anotação elétrica: "Depois volte ao painel superior mais próximo da entrada; em seguida, use o painel isolado no canto inferior direito."'),
        Documento(1320, 760, 'Etiqueta queimada: "O painel superior central deve ser o último."'),
    ]
    pistas_disjuntores_lidas = set()

    lanterna = {
        "pos": (180, 500),
        "coletada": False,
        "bateria": 100.0
    }

    it = {"pos": (1400, 790), "sumiu": False}   # easter egg escondido no canto

    vultos = [
        VultoSprite(800, 300, velocidade=1.8, dano=4,
                recarga_ms=1200, atraso_ms=0, lado_desvio=1),

        VultoSprite(1100, 650, velocidade=2.0, dano=4,
                recarga_ms=1200, atraso_ms=500, lado_desvio=-1),

        VultoSprite(500, 700, velocidade=1.7, dano=3,
                recarga_ms=1300, atraso_ms=1000, lado_desvio=1)
    ]

    contexto = _estado_base(
        sala,
        9,
        objetos=pistas_disjuntores,
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
        for indice, pista in enumerate(pistas_disjuntores):
            if not pista.coletado and jogador.get_rect().colliderect(pista.rect.inflate(18, 18)):
                pista.coletado = True
                pistas_disjuntores_lidas.add(indice)
                _definir_mensagem(contexto, pista.texto, tempo_ms, 4300)
                return
        if not lanterna["coletada"]:
            if _perto(jogador, lanterna["pos"], 60):
                lanterna["coletada"] = True
                sons.tocar("coletar")
                _definir_mensagem(
                    contexto,
                    "Você encontrou uma lanterna. A bateria está acabando.",
                    tempo_ms
                )
                return

        disjuntor = puzzle_disjuntores.disjuntor_proximo(jogador)
        if disjuntor and len(pistas_disjuntores_lidas) < len(pistas_disjuntores):
            _definir_mensagem(contexto, "O quadro tem quatro disjuntores sem identificação. Encontre os três registros de manutenção.", tempo_ms, 2600)
            return

        if disjuntor:
            sucesso = puzzle_disjuntores.acionar(disjuntor)
            sons.tocar("disjuntor_ok" if sucesso else "disjuntor_erro")

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
            blit_centro(surf, "lanterna", lanterna["pos"])

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

        desenhar_it(surf, jogador, tempo_ms)

    def desenhar_it(surf, jogador, tempo_ms):
        """Easter egg: o 'It', uma criatura de olhos enormes escondida num canto
        escuro. Os olhos seguem o jogador; se ele chegar perto, ela some."""
        if it["sumiu"]:
            return
        cx, cy = it["pos"]
        centro = jogador.get_rect().center
        if math.hypot(centro[0] - cx, centro[1] - cy) < 90:
            it["sumiu"] = True
            sons.tocar("sussurro")
            _definir_mensagem(contexto, "...os olhos sumiram.", tempo_ms, 2500)
            return
        # corpo: sombra roxa quase preta
        corpo = pygame.Surface((120, 150), pygame.SRCALPHA)
        pygame.draw.ellipse(corpo, (14, 8, 20, 235), (0, 0, 120, 150))
        surf.blit(corpo, (cx - 60, cy - 75))
        piscando = (tempo_ms // 100) % 40 == 0
        for ox in (-24, 24):
            ex, ey = cx + ox, cy - 15
            if piscando:
                pygame.draw.line(surf, (200, 200, 170), (ex - 16, ey), (ex + 16, ey), 3)
                continue
            pygame.draw.ellipse(surf, (240, 238, 200), (ex - 18, ey - 24, 36, 48))
            pygame.draw.ellipse(surf, (90, 70, 40), (ex - 18, ey - 24, 36, 48), 2)
            dx, dy = centro[0] - ex, centro[1] - ey
            d = math.hypot(dx, dy) or 1
            px, py = ex + dx / d * 7, ey + dy / d * 10
            pygame.draw.circle(surf, (10, 0, 0), (int(px), int(py)), 11)
            pygame.draw.circle(surf, (255, 255, 255), (int(px) - 3, int(py) - 4), 3)

    def desenhar_brilho_lanterna(contexto, tela, jogador, fonte, tempo_ms):
        """Brilho pulsante sobre a lanterna, desenhado por cima da escuridão,
        para o jogador conseguir achá-la só com o pontinho de luz."""
        if lanterna["coletada"]:
            return
        cam_x, cam_y = sala.calcular_camera(jogador)
        px = lanterna["pos"][0] - cam_x
        py = lanterna["pos"][1] - cam_y
        if not (-40 <= px <= LARGURA + 40 and -40 <= py <= ALTURA + 40):
            return
        pulso = 0.5 + 0.5 * math.sin(tempo_ms / 350)
        halo = pygame.Surface((80, 80), pygame.SRCALPHA)
        for r in range(36, 4, -4):
            a = int((60 + 70 * pulso) * (1 - r / 36) ** 1.2)
            pygame.draw.circle(halo, (255, 240, 150, a), (40, 40), r)
        tela.blit(halo, (px - 40, py - 40))
        blit_centro(tela, "lanterna", (px, py))

    contexto["ao_interagir"] = interagir
    contexto["ao_atualizar"] = atualizar
    contexto["ao_desenhar_extra"] = desenhar_extra
    contexto["ao_desenhar_tela"] = desenhar_brilho_lanterna

    def status(contexto):
        ativados = sum(
            1
            for d in puzzle_disjuntores.disjuntores
            if d["ligado"]
        )

        if len(pistas_disjuntores_lidas) < len(pistas_disjuntores):
            return f"Registros elétricos: {len(pistas_disjuntores_lidas)}/3 | Procure a lanterna."
        if not lanterna["coletada"]:
            return (
                f"Disjuntores: {ativados}/4 | "
                f"Procure a lanterna no escuro."
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

            _golpe_reparo(puzzle_fuzil)

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
        GuardaSprite(
            650, 100,
            velocidade=2.8,
            dano=3,
            recarga_ms=1000,
            atraso_ms=0,
            lado_desvio=1
        ),

        GuardaSprite(
            1100, 700,
            velocidade=3.0,
            dano=3,
            recarga_ms=1000,
            atraso_ms=700,
            lado_desvio=-1
        ),

        GuardaSprite(
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
                sons.tocar("coletar")

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
            sons.tocar("arrombar")
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
            desenhar_caixa(surf, caixa)

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
            blit_centro(surf, "pe_de_cabra", pe_de_cabra["pos"])

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

    sala = Sala(1800, 1100, (100, 500), largura_tela=LARGURA, altura_tela=ALTURA)
    jogador.x, jogador.y = sala.ponto_entrada
    jogador.agachado = False
    sala.porta_aberta = True

    # Arquivos físicos: cada documento está guardado em uma gaveta específica.
    armarios = [
        {"rect": pygame.Rect(310, 245, 130, 118), "aberta": False, "documento": 0, "rotulo": "ARQUIVO A"},
        {"rect": pygame.Rect(650, 650, 130, 118), "aberta": False, "documento": 1, "rotulo": "ARQUIVO B"},
        {"rect": pygame.Rect(1120, 260, 130, 118), "aberta": False, "documento": 2, "rotulo": "ARQUIVO C"},
        {"rect": pygame.Rect(1370, 700, 130, 118), "aberta": False, "documento": None, "rotulo": "ARQUIVO D"},
        {"rect": pygame.Rect(900, 430, 130, 118), "aberta": False, "documento": None, "rotulo": "ARQUIVO E"},
    ]
    documentos = [
        Documento(0, 0, "Ficha clínica: Paciente 724. Estado: instável. Última transferência: ala norte."),
        Documento(0, 0, "Relatório de plantão: o paciente afirma ouvir uma voz nos alto-falantes, mesmo quando o sistema está desligado."),
        Documento(0, 0, "FICHA DE IDENTIFICAÇÃO: Operário 724. O nome registrado corresponde ao funcionário que está lendo este documento.", especial=True),
    ]
    janela = pygame.Rect(1600, 450, 100, 150)
    porta_varanda = janela  # acesso interativo ao exterior, apos encontrar a ficha

    contexto = _estado_base(
        sala, 12, objetos=[], documentos=documentos, armarios=armarios,
        mensagem_intro='A VOZ: "Não saia... procure nos arquivos. A resposta está guardada."',
        duracao_intro=4200, taxa_dano_sanidade=0.003,
        texto_status="Investigue os arquivos. Os documentos estão escondidos nas gavetas.",
        condicao_transicao=lambda contexto, jogador: False
    )
    contexto["ficha_encontrada"] = False
    contexto["voz_revelada"] = False
    contexto["mensagem_final"] = (
        "A ficha confirma: Paciente 724. O nome que você perseguia nunca esteve escondido em lugar nenhum, porque sempre foi o seu. "
        "A voz que o guiou, os corredores, os guardas, as sombras e cada promessa de fuga nasceram de lembranças quebradas, repetidas como um experimento. "
        "Quando você abre a porta e alcança a varanda, a mentira deixa de conseguir se sustentar. O exterior parece amplo, mas a paisagem denuncia a farsa: janelas iguais, blocos iguais, o mesmo brilho frio e o mesmo ruído mecânico vindo de muito perto. "
        "Não existe cidade, não existe liberdade do outro lado, e não existe ninguém esperando por você. O alto-falante estala: 'Paciente 724, retorne ao quarto.' "
        "Você permanece imóvel, inclina o corpo sobre a sacada, enquanto a imagem falha como uma memória em colapso. O som se distorce, a tela escurece e tudo termina em silêncio. "
        "Depois de alguns segundos, uma última gravação, quase inaudível: '...nunca era a saída.'"
    )

    def interagir(contexto, jogador):
        tempo_ms = pygame.time.get_ticks()
        jogador_rect = jogador.get_rect()

        # Primeiro abre/fecha a gaveta próxima. O papel só aparece depois de aberta.
        for indice, armario in enumerate(armarios):
            area = armario["rect"].inflate(54, 48)
            if jogador_rect.colliderect(area):
                doc_idx = armario["documento"]
                if armario["aberta"] and doc_idx is not None:
                    documento = documentos[doc_idx]
                    documento.rect.center = (armario["rect"].centerx, armario["rect"].y - 18)
                    if not documento.coletado and jogador_rect.colliderect(documento.rect.inflate(60, 50)):
                        documento.coletado = True
                        if documento.especial:
                            contexto["ficha_encontrada"] = True
                            contexto["voz_revelada"] = True
                            _definir_mensagem(contexto,
                                'A ficha é sua. "Paciente 724"... a voz conhecia cada passo porque vinha de você.',
                                tempo_ms, 6500)
                        else:
                            _definir_mensagem(contexto, documento.texto, tempo_ms, 5000)
                        return
                armario["aberta"] = not armario["aberta"]
                if armario["aberta"]:
                    if doc_idx is None:
                        msg = "A gaveta está vazia. Há etiquetas antigas e poeira."
                    else:
                        msg = "Você abriu a gaveta. Aproxime-se do papel e pressione E para ler."
                else:
                    msg = "Gaveta fechada."
                _definir_mensagem(contexto, msg, tempo_ms, 2600)
                return


        if contexto["ficha_encontrada"] and jogador_rect.colliderect(porta_varanda.inflate(45, 45)):
            contexto["final"] = True

    def atualizar(contexto, jogador, teclas, tempo_ms):
        pass

    def desenhar_extra(contexto, surf, jogador, fonte, tempo_ms):
        # Mesas de consulta, cadeiras e equipamentos abandonados.
        mesas = [pygame.Rect(480, 450, 190, 78), pygame.Rect(930, 790, 210, 82),
                 pygame.Rect(1320, 470, 170, 72)]
        for mesa in mesas:
            pygame.draw.rect(surf, (62, 42, 30), mesa, border_radius=5)
            pygame.draw.rect(surf, (130, 92, 58), mesa, 4, border_radius=5)
            pygame.draw.line(surf, (35, 26, 22), (mesa.x + 18, mesa.bottom), (mesa.x + 18, mesa.bottom + 28), 7)
            pygame.draw.line(surf, (35, 26, 22), (mesa.right - 18, mesa.bottom), (mesa.right - 18, mesa.bottom + 28), 7)
        # Cadeiras deslocadas e uma cadeira caída.
        for x, y, inclinada in [(430, 555, False), (720, 520, False), (1180, 850, True), (1450, 560, False)]:
            cadeira = pygame.Rect(x, y, 42, 42)
            pygame.draw.rect(surf, (48, 50, 58), cadeira, border_radius=4)
            pygame.draw.rect(surf, (115, 120, 128), cadeira, 3, border_radius=4)
            pygame.draw.line(surf, (75, 78, 85), (x + 7, y + 40), (x + 4, y + 65), 4)
            pygame.draw.line(surf, (75, 78, 85), (x + 35, y + 40), (x + 39, y + 65), 4)
            if inclinada:
                pygame.draw.line(surf, (145, 145, 150), (x - 8, y + 8), (x + 50, y + 50), 5)
        # Pilhas de livros, pastas, papéis e lâmpadas de mesa.
        for x, y in [(520, 438), (560, 440), (990, 775), (1360, 452), (1385, 455)]:
            pygame.draw.rect(surf, (95, 35, 38), (x, y, 30, 12))
            pygame.draw.rect(surf, (180, 150, 105), (x, y, 30, 12), 1)
        for x, y in [(250, 500), (820, 320), (1050, 580), (1510, 330), (760, 920), (1240, 930)]:
            pygame.draw.polygon(surf, (205, 198, 174), [(x, y), (x + 25, y - 5), (x + 38, y + 12), (x + 8, y + 18)])
            pygame.draw.line(surf, (120, 115, 105), (x + 6, y + 5), (x + 26, y + 2), 1)
        # Relógio parado e luminárias falhando.
        pygame.draw.circle(surf, (30, 32, 38), (900, 95), 28)
        pygame.draw.circle(surf, (170, 165, 145), (900, 95), 23, 2)
        pygame.draw.line(surf, (190, 185, 165), (900, 95), (900, 78), 2)
        pygame.draw.line(surf, (190, 185, 165), (900, 95), (914, 102), 2)
        for x in (360, 900, 1440):
            cor = (220, 190, 110) if (tempo_ms // 700 + x) % 4 else (85, 75, 55)
            pygame.draw.circle(surf, cor, (x, 65), 9)
            pygame.draw.circle(surf, (70, 62, 48), (x, 65), 15, 2)

        # Armários de arquivo com três gavetas visíveis cada.
        for armario in armarios:
            r = armario["rect"]
            pygame.draw.rect(surf, (48, 52, 60), r, border_radius=4)
            pygame.draw.rect(surf, (125, 132, 140), r, 3, border_radius=4)
            for n in range(3):
                gaveta = pygame.Rect(r.x + 10, r.y + 8 + n * 35, r.width - 20, 29)
                desloca = 12 if n == 1 and armario["aberta"] else 0
                gaveta.x += desloca
                pygame.draw.rect(surf, (82, 91, 101), gaveta, border_radius=3)
                pygame.draw.rect(surf, (155, 160, 164), gaveta, 2, border_radius=3)
                pygame.draw.rect(surf, (190, 175, 130), (gaveta.centerx - 9, gaveta.centery - 2, 18, 4), border_radius=2)
            if armario["aberta"] and armario["documento"] is not None:
                doc = documentos[armario["documento"]]
                if not doc.coletado:
                    doc.rect.center = (r.centerx, r.y - 18)
                    pygame.draw.rect(surf, (220, 215, 190), doc.rect.inflate(8, 6))
                    pygame.draw.line(surf, (90, 85, 75), (doc.rect.x + 3, doc.rect.y + 4), (doc.rect.right - 3, doc.rect.y + 4), 1)
                    pygame.draw.line(surf, (90, 85, 75), (doc.rect.x + 3, doc.rect.y + 8), (doc.rect.right - 3, doc.rect.y + 8), 1)
            etiqueta = fonte.render(armario["rotulo"], True, (185, 190, 195))
            surf.blit(etiqueta, (r.x - 2, r.bottom + 4))

        # Estantes laterais, janela e claridade externa.
        for x in [170, 820, 1510]:
            desenhar_estante(surf, pygame.Rect(x, 120, 170, 68))
            desenhar_estante(surf, pygame.Rect(x, 930, 170, 68))
        # Porta envidracada da varanda, com maçaneta e luz exterior.
        pygame.draw.rect(surf, (12, 23, 36), janela.inflate(12, 12), border_radius=3)
        pygame.draw.rect(surf, (50, 79, 98), janela)
        pygame.draw.rect(surf, (181, 168, 139), janela, width=6)
        pygame.draw.line(surf, (181, 168, 139), (janela.centerx, janela.top), (janela.centerx, janela.bottom), 5)
        pygame.draw.circle(surf, (231, 198, 122), (janela.centerx + 12, janela.centery + 13), 5)
        pygame.draw.line(surf, (117, 143, 159), (janela.left+8, janela.y+25), (janela.right-8, janela.y+25), 2)
        if contexto["ficha_encontrada"]:
            aviso = fonte.render("[E] VARANDA", True, (232, 205, 145))
            surf.blit(aviso, (janela.x-12, janela.y-27))
        # Feixes de luz e poeira no ar.
        luz = pygame.Surface((260, 260), pygame.SRCALPHA)
        pygame.draw.polygon(luz, (130, 165, 210, 24), [(0, 0), (260, 40), (260, 260), (0, 150)])
        surf.blit(luz, (1340, 410))
        for i in range(18):
            px = 150 + ((i * 173 + tempo_ms // 90) % 1500)
            py = 210 + ((i * 97) % 720)
            pygame.draw.circle(surf, (170, 160, 135), (px, py), 1)

    contexto["ao_interagir"] = interagir
    contexto["ao_atualizar"] = atualizar
    contexto["ao_desenhar_extra"] = desenhar_extra

    def status(contexto):
        encontrados = sum(doc.coletado for doc in documentos)
        if not contexto["ficha_encontrada"]:
            abertas = sum(a["aberta"] for a in armarios)
            return f"Documentos: {encontrados}/3 | Gavetas abertas: {abertas}/5 | Investigue os arquivos."
        return "A ficha é sua. Saia pela porta e descubra o que há do lado de fora."

    contexto["texto_status"] = status
    return contexto

NIVEIS = {
    1: nivel_1, 2: nivel_2, 3: nivel_3, "3C": nivel_3c, 4: nivel_4, "4B": nivel_4b, 5: nivel_5, 6: nivel_6, 7: nivel_7, 8: nivel_8, 9: nivel_9, 10: nivel_10, 11: nivel_11, 12: nivel_12
}

# ordem em que as salas são percorridas (a sala do duto fica entre a 4 e a 5)
ORDEM_NIVEIS = [1, 2, 3, "3C", 4, "4B", 5, 6, 7, 8, 9, 10, 11, 12]


def proximo_nivel(nivel):
    """Próxima sala depois de `nivel`, ou None se for a última."""
    i = ORDEM_NIVEIS.index(nivel)
    return ORDEM_NIVEIS[i + 1] if i + 1 < len(ORDEM_NIVEIS) else None


def iniciar_sala(jogador, nivel, resetar_jogador=False):
    fn = NIVEIS.get(nivel, nivel_1)
    contexto = fn(jogador, resetar_jogador=resetar_jogador)
    # Todas as salas recebem frascos; preserva os posicionamentos já definidos nas salas especiais.
    if len(contexto.get("frascos", [])) < 2:
        existentes = contexto.setdefault("frascos", [])
        faltam = 2 - len(existentes)
        for i in range(faltam):
            x = random.randint(130, max(180, contexto["sala"].largura - 130))
            y = random.randint(100, max(140, contexto["sala"].altura - 100))
            existentes.append(FrascoSanidade(x, y))
    contexto["tempo_inicio"] = pygame.time.get_ticks()
    contexto["sala"].tema = TEMA_POR_NIVEL.get(nivel)
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

    puzzle_modal = contexto.get("puzzle_modal")
    puzzle_aberto = bool(puzzle_modal and getattr(puzzle_modal, "ativo", False))
    for obj in contexto["objetos"]:
        if puzzle_aberto and isinstance(obj, (Dica, Documento)):
            continue
        if isinstance(obj, Documento) and obj.coletado and contexto.get("puzzle_modal"):
            # Pistas lidas continuam visíveis no cenário até o puzzle ser aberto.
            blit_centro(superficie_mundo, "documento_especial" if obj.especial else "documento", obj.rect.center)
        else:
            obj.desenhar(superficie_mundo)

    duto = contexto["duto"]
    if duto:
        desenhar_duto(superficie_mundo, duto)

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
        desenhar_jogador(superficie_mundo, jogador, sprites_jogador, tempo_ms)
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
        linha = texto_status_fn(contexto) if callable(texto_status_fn) else texto_status_fn
        if linha:
            for i, parte in enumerate(_quebrar_linhas(linha, fonte_sub, 560)[:2]):
                txt = fonte_sub.render(parte, True, (210, 220, 255))
                tela.blit(txt, (20, y_status + i * (fonte_sub.get_linesize() + 2)))

    texto_nivel = fonte_sub.render(f"SALA {contexto['nivel']}", True, CINZA_BORDA)
    tela.blit(texto_nivel, (LARGURA - texto_nivel.get_width() - 20, 20))

    if contexto.get("tint_gas"):
        desenhar_overlay_gas(tela, LARGURA, ALTURA, intensidade=70)

    if contexto.get("usa_lanterna"):
        pos_tela = (jogador.get_rect().centerx - cam_x + offset_x, jogador.get_rect().centery - cam_y + offset_y)
        info_lanterna = contexto.get("lanterna")
        if info_lanterna is not None:
            # só acende a lanterna depois de pegá-la e enquanto houver bateria;
            # antes disso o personagem tem apenas um pequeno ponto de luz
            ligada = bool(info_lanterna.get("coletada")) and info_lanterna.get("bateria", 0) > 0
            raio = 170
            if ligada and info_lanterna["bateria"] < 20:
                raio = int(80 + 90 * info_lanterna["bateria"] / 20)
                if (tempo_ms // 120) % 9 == 0:   # luz falhando
                    raio = max(60, raio - 35)
        else:
            ligada = getattr(jogador, "lanterna_ligada", False)
            raio = 170
        desenhar_escuridao_com_lanterna(tela, pos_tela, LARGURA, ALTURA,
                                         ligada=ligada, raio=raio)

    intro = contexto.get("mensagem_intro")
    if intro and tempo_ms - contexto["tempo_inicio"] < contexto.get("duracao_intro", 4500):
        desenhar_mensagem_contextual(tela, intro, LARGURA, ALTURA, fonte_sub, y=ALTURA - 70)

    msg = contexto.get("mensagem_temporaria")
    if msg and tempo_ms < contexto.get("mensagem_temporaria_expira", 0):
        desenhar_mensagem_contextual(tela, msg, LARGURA, ALTURA, fonte_sub, y=ALTURA - 40)

    hook_tela = contexto.get("ao_desenhar_tela")
    if hook_tela:
        hook_tela(contexto, tela, jogador, fonte_sub, tempo_ms)

    puzzle_modal = contexto.get("puzzle_modal")
    if puzzle_modal and getattr(puzzle_modal, "ativo", False):
        puzzle_modal.desenhar(tela, fonte_sub)

    if flash_ativo:
        desenhar_flash_detectado(tela, LARGURA, ALTURA)
