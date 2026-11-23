import pygame
import random

import sprites

# Identidade visual unificada: metal envelhecido, latão e luz de emergência.
def _moldura(surf, rect, titulo=None, fonte=None):
    sombra = rect.move(7, 9)
    pygame.draw.rect(surf, (3, 7, 12), sombra, border_radius=15)
    pygame.draw.rect(surf, (25, 34, 42), rect, border_radius=13)
    pygame.draw.rect(surf, (97, 115, 122), rect, 3, border_radius=13)
    pygame.draw.rect(surf, (154, 117, 65), rect.inflate(-12, -12), 1, border_radius=10)
    pygame.draw.rect(surf, (37, 48, 55), (rect.x + 16, rect.y + 15, rect.w - 32, 46), border_radius=6)
    for x in (rect.left + 12, rect.right - 12):
        for y in (rect.top + 12, rect.bottom - 12):
            pygame.draw.circle(surf, (9, 14, 19), (x, y), 5)
            pygame.draw.circle(surf, (151, 147, 127), (x, y), 3, 1)
    if titulo and fonte:
        img = fonte.render(titulo, True, (234, 204, 147))
        surf.blit(img, img.get_rect(center=(rect.centerx, rect.y + 37)))


def _ferramenta_arte(surf, rect, tipo):
    cx, cy = rect.centerx, rect.centery - 8
    metal, luz, cabo, borracha = (146, 166, 174), (222, 232, 238), (136, 81, 54), (58, 64, 72)
    pygame.draw.ellipse(surf, (0, 0, 0, 45), (rect.x + 18, rect.bottom - 20, rect.width - 36, 10))
    if tipo in ('chave', 'inglesa'):
        pygame.draw.line(surf, metal, (cx - 23, cy + 12), (cx + 15, cy - 11), 8)
        pygame.draw.line(surf, luz, (cx - 22, cy + 11), (cx + 10, cy - 8), 2)
        pygame.draw.circle(surf, luz, (cx - 22, cy + 13), 6, 2)
        pygame.draw.lines(surf, luz, False, [(cx + 8, cy - 18), (cx + 18, cy - 12), (cx + 25, cy - 21)], 5)
        pygame.draw.line(surf, borracha, (cx - 18, cy + 15), (cx - 10, cy + 9), 3)
    elif tipo == 'alicate':
        pygame.draw.line(surf, cabo, (cx - 17, cy + 19), (cx + 2, cy - 6), 8)
        pygame.draw.line(surf, cabo, (cx + 18, cy + 19), (cx + 2, cy - 6), 8)
        pygame.draw.line(surf, (176, 106, 74), (cx - 16, cy + 17), (cx, cy - 4), 2)
        pygame.draw.line(surf, (176, 106, 74), (cx + 16, cy + 17), (cx, cy - 4), 2)
        pygame.draw.lines(surf, luz, False, [(cx - 13, cy - 20), (cx + 2, cy - 6), (cx + 15, cy - 21)], 5)
        pygame.draw.circle(surf, borracha, (cx + 2, cy - 6), 5)
        pygame.draw.circle(surf, luz, (cx + 2, cy - 6), 2)
    elif tipo == 'pe':
        pygame.draw.line(surf, metal, (cx - 23, cy + 19), (cx + 15, cy - 17), 8)
        pygame.draw.line(surf, luz, (cx - 21, cy + 17), (cx + 13, cy - 15), 2)
        pygame.draw.lines(surf, luz, False, [(cx + 10, cy - 13), (cx + 21, cy - 20), (cx + 28, cy - 14)], 5)
        pygame.draw.arc(surf, luz, (cx + 14, cy - 24, 14, 14), 3.7, 6.0, 2)
    elif tipo == 'martelo':
        pygame.draw.line(surf, cabo, (cx - 12, cy + 19), (cx + 10, cy - 15), 8)
        pygame.draw.line(surf, (180, 104, 74), (cx - 9, cy + 16), (cx + 8, cy - 12), 2)
        pygame.draw.rect(surf, metal, (cx - 8, cy - 24, 30, 12), border_radius=3)
        pygame.draw.rect(surf, luz, (cx - 6, cy - 22, 26, 4), border_radius=2)
        pygame.draw.rect(surf, borracha, (cx + 18, cy - 22, 8, 8), border_radius=2)
    else:
        pygame.draw.line(surf, cabo, (cx - 21, cy + 17), (cx + 3, cy - 3), 9)
        pygame.draw.line(surf, (180, 104, 74), (cx - 18, cy + 14), (cx, cy - 1), 2)
        pygame.draw.line(surf, metal, (cx + 2, cy - 2), (cx + 23, cy - 20), 5)
        pygame.draw.circle(surf, (215, 154, 76), (cx - 19, cy + 15), 4)
        pygame.draw.circle(surf, (240, 210, 120), (cx - 19, cy + 15), 2)



def _linha_texto(surf, fonte, texto, x, y, cor, centro=True):
    img = fonte.render(texto, True, cor)
    rect = img.get_rect(center=(x, y)) if centro else img.get_rect(topleft=(x, y))
    surf.blit(img, rect)
    return rect

class PuzzleRadio:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura

        self.rect_painel = pygame.Rect(largura // 2 - 200, altura // 2 - 150, 400, 300)

        self.freq_min = 88.0
        self.freq_max = 108.0
        self.freq_atual = 88.0

        self.freq_alvo = random.choice([90.0, 92.5, 95.0, 98.2, 101.5, 104.0, 107.1])

        self.resolvido = False
        self.ativo = False  
        self.tolerancia = 0.4

    def processar_evento(self, evento):
        pass

    def atualizar(self, teclas):
        if self.resolvido:
            if teclas[pygame.K_SPACE]:
                self.ativo = False
            return

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.freq_atual -= 0.08
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.freq_atual += 0.08

        self.freq_atual = max(self.freq_min, min(self.freq_max, self.freq_atual))

        if abs(self.freq_atual - self.freq_alvo) <= self.tolerancia:
            self.freq_atual = self.freq_alvo
            self.resolvido = True

    def desenhar(self, surf, fonte):
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((4, 8, 14, 226))
        surf.blit(overlay, (0, 0))
        painel = self.rect_painel
        _moldura(surf, painel, "RADIO  /  SINTONIA", fonte)
        corpo = painel.inflate(-28, -76)
        corpo.y += 16
        pygame.draw.rect(surf, (15, 24, 29), corpo, border_radius=8)
        pygame.draw.rect(surf, (96, 106, 110), corpo, 2, border_radius=8)
        visor = pygame.Rect(painel.x + 36, painel.y + 86, painel.width - 72, 64)
        pygame.draw.rect(surf, (8, 31, 25), visor, border_radius=5)
        pygame.draw.rect(surf, (75, 214, 163), visor, 2, border_radius=5)
        status = "SINAL SINTONIZADO" if self.resolvido else f"{self.freq_atual:.1f} MHz"
        _linha_texto(surf, fonte, status, visor.centerx, visor.centery - 11, (112, 245, 177))
        subtitulo = "PORTA LIBERADA" if self.resolvido else f"ALVO {self.freq_alvo:.1f} MHz"
        _linha_texto(surf, fonte, subtitulo, visor.centerx, visor.centery + 14, (232, 198, 117))
        y = painel.y + 194
        x0, x1 = painel.x + 40, painel.right - 40
        pygame.draw.rect(surf, (24, 29, 34), (x0, y - 12, x1 - x0, 30), border_radius=5)
        pygame.draw.line(surf, (104, 119, 121), (x0, y), (x1, y), 4)
        for f in range(88, 109, 4):
            px = x0 + int((f - self.freq_min) / (self.freq_max - self.freq_min) * (x1 - x0))
            pygame.draw.line(surf, (187, 193, 190), (px, y - 8), (px, y + 8), 2)
            _linha_texto(surf, pygame.font.Font(None, 17), str(f), px, y + 30, (177, 185, 188))
        px = x0 + int((self.freq_atual - self.freq_min) / (self.freq_max - self.freq_min) * (x1 - x0))
        pygame.draw.line(surf, (246, 91, 77), (px, y - 16), (px, y + 17), 4)
        _linha_texto(surf, pygame.font.Font(None, 20), "L / R  -  SINTONIZAR", painel.centerx, painel.bottom - 27, (192, 211, 205))
        if self.resolvido:
            _linha_texto(surf, pygame.font.Font(None, 20), "ESPACO PARA CONTINUAR", painel.centerx, painel.bottom + 28, (126, 245, 175))

class CaixaArrastavel:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 55, 55)

    def desenhar(self, surf):
        sprites.desenhar_caixa(surf, self.rect)

class PuzzleCaixaFerramentas:
    """Puzzle simples: alinhar três pinos e depois arrastar ferramentas até achar o pé de cabra."""
    def __init__(self, largura, altura):
        self.largura, self.altura = largura, altura
        self.ativo = False
        self.resolvido = False
        self.etapa = "pinos"
        self.combinacao = [2, 1, 3]
        self.valores = [1, 1, 1]
        self.selecionado = 0
        self.mensagem = "Ajuste os 3 pinos para a marca indicada."
        self.ferramentas = [
            {"nome": "CHAVE", "tipo": "chave", "rect": pygame.Rect(0, 0, 100, 52), "cor": (130, 145, 160), "correta": False},
            {"nome": "ALICATE", "tipo": "alicate", "rect": pygame.Rect(0, 0, 100, 52), "cor": (170, 105, 55), "correta": False},
            {"nome": "PÉ DE CABRA", "tipo": "pe", "rect": pygame.Rect(0, 0, 100, 52), "cor": (185, 190, 198), "correta": True},
            {"nome": "CHAVE INGLESA", "tipo": "inglesa", "rect": pygame.Rect(0, 0, 100, 52), "cor": (105, 130, 145), "correta": False},
            {"nome": "MARTELO", "tipo": "martelo", "rect": pygame.Rect(0, 0, 100, 52), "cor": (135, 100, 70), "correta": False},
            {"nome": "CHAVE DE FENDA", "tipo": "fenda", "rect": pygame.Rect(0, 0, 100, 52), "cor": (155, 145, 95), "correta": False},
        ]
        self.arrastando = None
        self.mouse = (0, 0)
        self.zona_busca = pygame.Rect(largura // 2 - 210, altura // 2 + 65, 420, 95)
        self.ferramenta_encontrada = False

    def processar_evento(self, evento):
        if not self.ativo or self.resolvido:
            return
        if evento.type == pygame.KEYDOWN and self.etapa == "pinos":
            if evento.key in (pygame.K_LEFT, pygame.K_a):
                self.selecionado = (self.selecionado - 1) % 3
            elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                self.selecionado = (self.selecionado + 1) % 3
            elif evento.key in (pygame.K_UP, pygame.K_w):
                self.valores[self.selecionado] = self.valores[self.selecionado] % 3 + 1
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self.valores[self.selecionado] = (self.valores[self.selecionado] - 2) % 3 + 1
            elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.valores == self.combinacao:
                    self.etapa = "ferramentas"
                    self.mensagem = "Caixa aberta! Arraste cada ferramenta para a bancada de busca."
                else:
                    self.mensagem = "Ainda não encaixou. Tente novamente; não há penalidade."
        elif evento.type == pygame.MOUSEMOTION and self.etapa == "ferramentas":
            self.mouse = evento.pos
            if self.arrastando is not None:
                self.ferramentas[self.arrastando]["rect"].center = evento.pos
        elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and self.etapa == "ferramentas":
            for i in range(len(self.ferramentas) - 1, -1, -1):
                if self.ferramentas[i]["rect"].collidepoint(evento.pos):
                    self.arrastando = i
                    break
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and self.etapa == "ferramentas":
            if self.arrastando is not None:
                item = self.ferramentas[self.arrastando]
                if self.zona_busca.collidepoint(evento.pos):
                    if item["correta"]:
                        self.ferramenta_encontrada = True
                        self.resolvido = True
                        self.ativo = False
                        self.mensagem = "Pé de cabra encontrado!"
                    else:
                        self.mensagem = "Não é essa. Continue procurando."
                        item["rect"].topleft = self._posicao_item(self.arrastando)
                else:
                    item["rect"].topleft = self._posicao_item(self.arrastando)
                self.arrastando = None

    def _posicao_item(self, i):
        col, lin = i % 3, i // 3
        return (self.largura // 2 - 165 + col * 115, self.altura // 2 - 110 + lin * 65)

    def desenhar(self, surf, fonte):
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((4, 8, 14, 229))
        surf.blit(overlay, (0, 0))
        painel = pygame.Rect(self.largura // 2 - 305, self.altura // 2 - 225, 610, 450)
        titulo = "CAIXA DE FERRAMENTAS  /  TRAVA" if self.etapa == "pinos" else "CAIXA DE FERRAMENTAS  /  INVENTARIO"
        _moldura(surf, painel, titulo, fonte)
        interno = painel.inflate(-32, -82)
        pygame.draw.rect(surf, (18, 24, 30), interno, border_radius=10)
        pygame.draw.rect(surf, (82, 92, 101), interno, 2, border_radius=10)
        if self.etapa == "pinos":
            placa = pygame.Rect(interno.x + 26, interno.y + 12, interno.w - 52, 164)
            pygame.draw.rect(surf, (24, 32, 36), placa, border_radius=8)
            pygame.draw.rect(surf, (120, 124, 118), placa, 2, border_radius=8)
            for i, valor in enumerate(self.valores):
                x = placa.x + 95 + i * 160
                r = pygame.Rect(x - 42, placa.y + 24, 84, 112)
                pygame.draw.rect(surf, (55, 62, 70), r, border_radius=10)
                pygame.draw.rect(surf, (220, 174, 93) if i == self.selecionado else (112, 124, 136), r, 3, border_radius=10)
                visor = r.inflate(-18, -20)
                pygame.draw.rect(surf, (10, 16, 20), visor, border_radius=6)
                _linha_texto(surf, fonte, str(valor), visor.centerx, visor.centery - 8, (242, 214, 154))
                _linha_texto(surf, pygame.font.Font(None, 19), f"PINO {i+1:02}", visor.centerx, visor.bottom - 14, (177, 193, 188))
                for step in range(3):
                    py = visor.y + 18 + step * 20
                    pygame.draw.line(surf, (42, 55, 61), (visor.x + 8, py), (visor.right - 8, py), 1)
            linhas = ["SETAS: selecionar e ajustar", "MARCA DE INSPECAO: 2 - 1 - 3", "ENTER: destravar  |  ESC: sair"]
            for i, linha in enumerate(linhas):
                _linha_texto(surf, fonte, linha, painel.centerx, painel.y + 302 + i * 28, (204, 211, 203))
        else:
            if not any(item["rect"].topleft != (0, 0) for item in self.ferramentas):
                for i, item in enumerate(self.ferramentas):
                    item["rect"].topleft = self._posicao_item(i)
            area = pygame.Rect(interno.x + 18, interno.y + 12, interno.w - 36, 205)
            pygame.draw.rect(surf, (22, 28, 32), area, border_radius=8)
            pygame.draw.rect(surf, (108, 116, 121), area, 2, border_radius=8)
            for item in self.ferramentas:
                r = item["rect"]
                pygame.draw.rect(surf, (18, 24, 28), r.move(4, 5), border_radius=8)
                pygame.draw.rect(surf, (72, 80, 84), r, border_radius=8)
                pygame.draw.rect(surf, (171, 152, 111), r, 2, border_radius=8)
                pygame.draw.line(surf, (104, 112, 116), (r.x + 8, r.y + 8), (r.right - 8, r.y + 8), 1)
                _ferramenta_arte(surf, r, item["tipo"])
                mini = pygame.font.Font(None, 15)
                _linha_texto(surf, mini, item["nome"], r.centerx, r.bottom - 10, (245, 225, 179))
            pygame.draw.rect(surf, (10, 40, 36), self.zona_busca, border_radius=10)
            pygame.draw.rect(surf, (91, 190, 160), self.zona_busca, 3, border_radius=10)
            _linha_texto(surf, fonte, "BANCADA DE INSPECAO", self.zona_busca.centerx, self.zona_busca.centery - 10, (190, 235, 216))
            _linha_texto(surf, pygame.font.Font(None, 20), "Arraste as ferramentas ate aqui e encontre o pe de cabra.", self.zona_busca.centerx, self.zona_busca.centery + 18, (205, 225, 218))
        mini = pygame.font.Font(None, 20)
        _linha_texto(surf, mini, self.mensagem[:90], painel.centerx, painel.bottom - 22, (233, 184, 115))

class PuzzlePainelSenha:
    def __init__(self, senha):
        self.senha = list(senha)
        self.pistas_coletadas = [None] * len(self.senha)
        self.resolvido = False
        self.ativo = False
        self.entrada = ""
        self.erros = 0
        self.mensagem = "Insira os quatro números encontrados."

    def registrar_pista(self, indice, valor):
        if 0 <= indice < len(self.pistas_coletadas):
            self.pistas_coletadas[indice] = valor

    def completo(self):
        return all(v is not None for v in self.pistas_coletadas)

    def tentar_abrir(self):
        return self.resolvido

    def texto_progresso(self):
        return " ".join(v if v is not None else "_" for v in self.pistas_coletadas)

    def processar_evento(self, evento):
        if not self.ativo or self.resolvido or evento.type != pygame.KEYDOWN:
            return
        if pygame.K_0 <= evento.key <= pygame.K_9 and len(self.entrada) < 4:
            self.entrada += chr(evento.key)
        elif evento.key == pygame.K_BACKSPACE:
            self.entrada = self.entrada[:-1]
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if list(self.entrada) == self.senha:
                self.resolvido = True
                self.ativo = False
                self.mensagem = "Senha aceita. A porta foi destrancada."
            else:
                self.erros += 1
                self.entrada = ""
                self.mensagem = "Senha incorreta. Confira as pistas."

    def desenhar(self, surf, fonte):
        overlay = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
        overlay.fill((7, 10, 18, 238))
        surf.blit(overlay, (0, 0))
        painel = pygame.Rect(surf.get_width() // 2 - 250, surf.get_height() // 2 - 165, 500, 330)
        _moldura(surf, painel, "PAINEL DE ACESSO", fonte)
        corpo = painel.inflate(-30, -80)
        pygame.draw.rect(surf, (14, 20, 26), corpo, border_radius=9)
        pygame.draw.rect(surf, (116, 126, 136), corpo, 2, border_radius=9)
        linhas = [
            "Digite os quatro numeros encontrados pela sala.",
            "BACKSPACE apaga  |  ENTER confirma  |  ESC fecha",
        ]
        for i, linha in enumerate(linhas):
            _linha_texto(surf, fonte, linha, painel.centerx, painel.y + 86 + i * 28, (205, 215, 225))
        campo = pygame.Rect(painel.centerx - 142, painel.y + 176, 284, 60)
        pygame.draw.rect(surf, (7, 16, 20), campo, border_radius=7)
        pygame.draw.rect(surf, (70, 220, 170), campo, 2, border_radius=7)
        mostrado = self.entrada + "_" * (4 - len(self.entrada))
        _linha_texto(surf, fonte, "  ".join(mostrado), campo.centerx, campo.centery, (100, 255, 190))
        leds_y = campo.bottom + 28
        for i, v in enumerate(self.pistas_coletadas):
            cor = (86, 230, 172) if v is not None else (54, 66, 74)
            pygame.draw.circle(surf, cor, (painel.centerx - 90 + i * 60, leds_y), 7)
            rot = pygame.font.Font(None, 20).render(str(v) if v is not None else "?", True, (18, 24, 28) if v is not None else (175, 185, 194))
            surf.blit(rot, rot.get_rect(center=(painel.centerx - 90 + i * 60, leds_y)))
        rodape = f"{self.mensagem}  Erros: {self.erros}"[:56]
        _linha_texto(surf, pygame.font.Font(None, 22), rodape, painel.centerx, painel.bottom - 22, (255, 180, 130) if self.erros else (175, 205, 195))


class PuzzleCofre:
    def __init__(self, rect_placa, palavra_chave):
        self.rect_placa = rect_placa
        self.palavra_chave = palavra_chave.upper()
        self.revelado = False
        self.aberto = False
        self.ativo = False
        self.entrada = ""
        self.erros = 0
        self.mensagem = "Digite a palavra montada pelos fragmentos."

    def checar_revelado(self, caixas):
        if not self.revelado:
            bloqueado = any(c.rect.colliderect(self.rect_placa) for c in caixas)
            self.revelado = not bloqueado
        return self.revelado

    def tentar_abrir(self, sabe_palavra_chave):
        if self.revelado and sabe_palavra_chave:
            self.ativo = True
        return self.aberto

    def processar_evento(self, evento):
        if not self.ativo or self.aberto or evento.type != pygame.KEYDOWN:
            return
        if pygame.K_a <= evento.key <= pygame.K_z and len(self.entrada) < len(self.palavra_chave):
            self.entrada += chr(evento.key).upper()
        elif evento.key == pygame.K_BACKSPACE:
            self.entrada = self.entrada[:-1]
        elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.entrada == self.palavra_chave:
                self.aberto = True
                self.ativo = False
                self.mensagem = "Cofre aberto."
            else:
                self.erros += 1
                self.entrada = ""
                self.mensagem = "Palavra incorreta. Releia os fragmentos."

    def desenhar(self, surf, fonte):
        if self.ativo:
            overlay = pygame.Surface((surf.get_width(), surf.get_height()), pygame.SRCALPHA)
            overlay.fill((7, 10, 18, 238))
            surf.blit(overlay, (0, 0))
            painel = pygame.Rect(surf.get_width() // 2 - 255, surf.get_height() // 2 - 170, 510, 340)
            _moldura(surf, painel, "COFRE DE EVIDENCIAS", fonte)
            corpo = painel.inflate(-28, -84)
            pygame.draw.rect(surf, (18, 16, 13), corpo, border_radius=9)
            pygame.draw.rect(surf, (185, 155, 100), corpo, 2, border_radius=9)
            linhas = [
                "Monte a palavra usando os tres fragmentos.",
                "Digite as letras e pressione ENTER.  |  BACKSPACE apaga",
            ]
            for i, linha in enumerate(linhas):
                _linha_texto(surf, fonte, linha, painel.centerx, painel.y + 86 + i * 28, (215, 215, 205))
            campo = pygame.Rect(painel.centerx - 160, painel.y + 188, 320, 54)
            pygame.draw.rect(surf, (10, 9, 7), campo, border_radius=7)
            pygame.draw.rect(surf, (205, 170, 105), campo, 2, border_radius=7)
            mostrado = self.entrada + "_" * (len(self.palavra_chave) - len(self.entrada))
            _linha_texto(surf, fonte, "  ".join(mostrado), campo.centerx, campo.centery, (255, 220, 150))
            rodape = f"{self.mensagem} Erros: {self.erros}"[:60]
            _linha_texto(surf, pygame.font.Font(None, 22), rodape, painel.centerx, painel.bottom - 22, (255, 180, 130) if self.erros else (200, 200, 185))
            return
        if self.revelado:
            sprites.desenhar_cofre(surf, self.rect_placa, self.aberto, fonte)


class PuzzleValvulas:
    def __init__(self, posicoes, ordem_correta=None):
        self.valvulas = [{"pos": p, "girada": False, "id": i} for i, p in enumerate(posicoes)]
        self.raio_interacao = 45
        self.ordem_correta = list(ordem_correta) if ordem_correta is not None else list(range(len(posicoes)))
        self.progresso = []
        self.erros = 0
        self.ultima_mensagem = ""

    def valvula_proxima(self, jogador):
        centro = jogador.get_rect().center
        for v in self.valvulas:
            if v["girada"]:
                continue
            dist = ((centro[0] - v["pos"][0]) ** 2 + (centro[1] - v["pos"][1]) ** 2) ** 0.5
            if dist <= self.raio_interacao:
                return v
        return None

    def girar(self, valvula):
        if valvula["id"] == self.ordem_correta[len(self.progresso)]:
            valvula["girada"] = True
            self.progresso.append(valvula["id"])
            self.ultima_mensagem = "A válvula encaixou na sequência."
            return True
        self.erros += 1
        for v in self.valvulas:
            v["girada"] = False
        self.progresso = []
        self.ultima_mensagem = "Sequência errada! A pressão voltou e todas as válvulas retornaram."
        return False

    def todas_giradas(self):
        return len(self.progresso) == len(self.ordem_correta)

    def desenhar(self, surf):
        tempo = pygame.time.get_ticks()
        for v in self.valvulas:
            sprites.desenhar_valvula(surf, v["pos"], v["girada"], tempo)

class PuzzleSom:
    def __init__(self, posicoes, indice_real):
        self.fontes = [{"pos": p, "real": (i == indice_real)} for i, p in enumerate(posicoes)]
        self.raio_interacao = 45
        self.chave_revelada = False
        self.ultima_mensagem = ""

    def fonte_proxima(self, jogador):
        centro = jogador.get_rect().center
        for f in self.fontes:
            dist = ((centro[0] - f["pos"][0]) ** 2 + (centro[1] - f["pos"][1]) ** 2) ** 0.5
            if dist <= self.raio_interacao:
                return f
        return None

    def ouvir(self, fonte):
        if fonte["real"]:
            self.chave_revelada = True
            self.ultima_mensagem = "Esse som é real. A chave estava perto dele."
        else:
            self.ultima_mensagem = "Só era o gás mexendo com sua cabeça de novo."
        return self.chave_revelada

    def desenhar(self, surf, tempo_ms):
        for f in self.fontes:
            sprites.desenhar_fonte_som(surf, f["pos"], f["real"], tempo_ms)


class PuzzleDisjuntores:
    def __init__(self, posicoes, ordem_correta):
        self.disjuntores = [{"pos": p, "ligado": False, "id": i} for i, p in enumerate(posicoes)]
        self.ordem_correta = ordem_correta
        self.progresso = []
        self.resolvido = False
        self.raio_interacao = 40

    def disjuntor_proximo(self, jogador):
        centro = jogador.get_rect().center
        for d in self.disjuntores:
            if d["ligado"]:
                continue
            dist = ((centro[0] - d["pos"][0]) ** 2 + (centro[1] - d["pos"][1]) ** 2) ** 0.5
            if dist <= self.raio_interacao:
                return d
        return None

    def acionar(self, disjuntor):
        esperado = self.ordem_correta[len(self.progresso)]
        if disjuntor["id"] == esperado:
            disjuntor["ligado"] = True
            self.progresso.append(disjuntor["id"])
            if len(self.progresso) == len(self.ordem_correta):
                self.resolvido = True
            return True
        else:
            for d in self.disjuntores:
                d["ligado"] = False
            self.progresso = []
            return False

    def desenhar(self, surf):
        tempo = pygame.time.get_ticks()
        for d in self.disjuntores:
            sprites.desenhar_disjuntor(surf, d["pos"], d["ligado"], tempo)


class PuzzleFuzil:
    def __init__(self, pos, golpes_necessarios=3):
        self.pos = pos
        self.golpes_necessarios = golpes_necessarios
        self.golpes = 0
        self.consertado = False
        self.raio_interacao = 40

    def perto(self, jogador):
        centro = jogador.get_rect().center
        dist = ((centro[0] - self.pos[0]) ** 2 + (centro[1] - self.pos[1]) ** 2) ** 0.5
        return dist <= self.raio_interacao

    def golpear(self):
        if self.consertado:
            return True
        self.golpes += 1
        if self.golpes >= self.golpes_necessarios:
            self.consertado = True
        return self.consertado

    def desenhar(self, surf, fonte):
        sprites.desenhar_reparo(surf, self.pos, self.consertado, pygame.time.get_ticks())
        if not self.consertado:
            txt = fonte.render(f"{self.golpes}/{self.golpes_necessarios}", True, (255, 255, 255))
            surf.blit(txt, txt.get_rect(center=(self.pos[0], self.pos[1] - 22)))
