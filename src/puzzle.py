import pygame
import random

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
        overlay.fill((10, 15, 25, 220))
        surf.blit(overlay, (0, 0))

        pygame.draw.rect(surf, (60, 40, 25), self.rect_painel, border_radius=12)
        pygame.draw.rect(surf, (25, 25, 30), self.rect_painel.inflate(-20, -20), border_radius=8)

        visor = pygame.Rect(self.rect_painel.x + 40, self.rect_painel.y + 40, 320, 80)

        if self.resolvido:
            pygame.draw.rect(surf, (10, 50, 20), visor, border_radius=6)
            pygame.draw.rect(surf, (0, 255, 100), visor, width=2, border_radius=6)

            txt_sucesso = fonte.render("SINAL SINTONIZADO!", True, (0, 255, 100))
            surf.blit(txt_sucesso, txt_sucesso.get_rect(center=(visor.centerx, visor.centery - 12)))

            txt_porta = fonte.render("PORTA DESBLOQUEADA", True, (255, 210, 0))
            surf.blit(txt_porta, txt_porta.get_rect(center=(visor.centerx, visor.centery + 18)))

            txt_sair = fonte.render("Pressione [ESPAÇO] para continuar", True, (255, 255, 255))
            surf.blit(txt_sair, txt_sair.get_rect(center=(self.largura // 2, self.rect_painel.bottom + 35)))
        else:
            pygame.draw.rect(surf, (10, 35, 15), visor, border_radius=6)
            pygame.draw.rect(surf, (0, 255, 100), visor, width=2, border_radius=6)

            txt_freq = fonte.render(f"SINTONIA: {self.freq_atual:.1f} MHz", True, (0, 255, 100))
            surf.blit(txt_freq, txt_freq.get_rect(center=(visor.centerx, visor.centery - 12)))

            txt_alvo = fonte.render(f"ALVO: {self.freq_alvo:.1f} MHz", True, (255, 210, 0))
            surf.blit(txt_alvo, txt_alvo.get_rect(center=(visor.centerx, visor.centery + 18)))

            escala_y = self.rect_painel.y + 165
            pygame.draw.line(surf, (80, 80, 85), (self.rect_painel.x + 40, escala_y), (self.rect_painel.x + 360, escala_y), 4)

            for f in range(88, 109, 4):
                proporcao = (f - 88) / (108 - 88)
                pos_x = self.rect_painel.x + 40 + int(proporcao * 320)
                pygame.draw.line(surf, (140, 140, 145), (pos_x, escala_y - 6), (pos_x, escala_y + 6), 2)

                txt_num = fonte.render(str(f), True, (120, 120, 125))
                surf.blit(txt_num, txt_num.get_rect(center=(pos_x, escala_y + 20)))

            prop_atual = (self.freq_atual - self.freq_min) / (self.freq_max - self.freq_min)
            agulha_x = self.rect_painel.x + 40 + int(prop_atual * 320)
            pygame.draw.line(surf, (250, 50, 50), (agulha_x, escala_y - 15), (agulha_x, escala_y + 15), 3)

            txt_ajuda = fonte.render("Use SETAS ou A/D para sintonizar", True, (160, 160, 170))
            surf.blit(txt_ajuda, txt_ajuda.get_rect(center=(self.largura // 2, self.rect_painel.bottom + 35)))

class CaixaArrastavel:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 55, 55)

    def desenhar(self, surf):
        pygame.draw.rect(surf, (105, 70, 45), self.rect, border_radius=4)
        pygame.draw.rect(surf, (65, 40, 25), self.rect, width=3, border_radius=4)
        pygame.draw.line(surf, (65, 40, 25), self.rect.topleft, self.rect.bottomright, 2)
        pygame.draw.line(surf, (65, 40, 25), self.rect.topright, self.rect.bottomleft, 2)

class PuzzleCaixaFerramentas:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        self.ativo = False
        self.resolvido = False
        self.etapa = 0 

    def atualizar(self, teclas_press):
        if self.ativo:
            if self.etapa < 2:
                self.etapa += 1
            else:
                self.resolvido = True
                self.ativo = False

    def desenhar(self, surf, fonte):
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((15, 10, 10, 235))
        surf.blit(overlay, (0, 0))

        painel = pygame.Rect(self.largura // 2 - 220, self.altura // 2 - 130, 440, 260)
        pygame.draw.rect(surf, (120, 30, 30), painel, border_radius=10)
        pygame.draw.rect(surf, (50, 15, 15), painel, width=4, border_radius=10)

        if self.etapa == 0:
            txt1 = fonte.render("CAIXA DE FERRAMENTAS ENCONTRADA", True, (255, 255, 255))
            txt2 = fonte.render("Pressione [ESPAÇO] para abrir as travas...", True, (200, 200, 200))
        elif self.etapa == 1:
            txt1 = fonte.render("REVIRANDO COMPARTIMENTOS...", True, (255, 210, 0))
            txt2 = fonte.render("Pressione [ESPAÇO] para procurar no fundo...", True, (200, 200, 200))
        else:
            txt1 = fonte.render("VOCÊ ENCONTROU O PÉ DE CABRA!", True, (0, 255, 100))
            txt2 = fonte.render("Pressione [ESPAÇO] para guardar no inventário.", True, (255, 255, 255))

        surf.blit(txt1, txt1.get_rect(center=(self.largura // 2, self.altura // 2 - 20)))
        surf.blit(txt2, txt2.get_rect(center=(self.largura // 2, self.altura // 2 + 30)))

class PuzzlePainelSenha:
    def __init__(self, senha):
        self.senha = list(senha)
        self.pistas_coletadas = [None] * len(self.senha)
        self.resolvido = False

    def registrar_pista(self, indice, valor):
        if 0 <= indice < len(self.pistas_coletadas):
            self.pistas_coletadas[indice] = valor

    def completo(self):
        return all(v is not None for v in self.pistas_coletadas)

    def tentar_abrir(self):
        if self.completo():
            self.resolvido = True
        return self.resolvido

    def texto_progresso(self):
        return " ".join(v if v is not None else "_" for v in self.pistas_coletadas)

    def desenhar_hud(self, surf, fonte, x, y):
        txt = fonte.render(f"SENHA: {self.texto_progresso()}", True, (0, 255, 140))
        surf.blit(txt, (x, y))


class PuzzleCofre:
    def __init__(self, rect_placa, palavra_chave):
        self.rect_placa = rect_placa
        self.palavra_chave = palavra_chave
        self.revelado = False
        self.aberto = False

    def checar_revelado(self, caixas):
        if not self.revelado:
            bloqueado = any(c.rect.colliderect(self.rect_placa) for c in caixas)
            self.revelado = not bloqueado
        return self.revelado

    def tentar_abrir(self, sabe_palavra_chave):
        if self.revelado and sabe_palavra_chave:
            self.aberto = True
        return self.aberto

    def desenhar(self, surf, fonte):
        if not self.revelado:
            return
        cor = (40, 160, 90) if self.aberto else (90, 70, 40)
        pygame.draw.rect(surf, cor, self.rect_placa, border_radius=4)
        pygame.draw.rect(surf, (20, 20, 20), self.rect_placa, width=3, border_radius=4)
        rotulo = "ABERTO" if self.aberto else "COFRE"
        txt = fonte.render(rotulo, True, (255, 255, 255))
        surf.blit(txt, txt.get_rect(center=self.rect_placa.center))


class PuzzleValvulas:
    def __init__(self, posicoes):
        self.valvulas = [{"pos": p, "girada": False} for p in posicoes]
        self.raio_interacao = 45

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
        valvula["girada"] = True

    def todas_giradas(self):
        return all(v["girada"] for v in self.valvulas)

    def desenhar(self, surf):
        for v in self.valvulas:
            cor = (60, 200, 100) if v["girada"] else (200, 70, 60)
            pygame.draw.circle(surf, cor, v["pos"], 16)
            pygame.draw.circle(surf, (20, 20, 20), v["pos"], 16, width=3)


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
            if f["real"]:
                brilho = 150 + int(40 * ((tempo_ms // 500) % 2))
                cor = (brilho, brilho, 255)
            else:
                cor = (200, 60, 220) if (tempo_ms // 180) % 2 == 0 else (90, 20, 110)
            pygame.draw.circle(surf, cor, f["pos"], 10)


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
        for d in self.disjuntores:
            cor = (60, 220, 120) if d["ligado"] else (70, 70, 80)
            pygame.draw.rect(surf, cor, (d["pos"][0] - 12, d["pos"][1] - 18, 24, 36), border_radius=3)
            pygame.draw.rect(surf, (15, 15, 20), (d["pos"][0] - 12, d["pos"][1] - 18, 24, 36), width=2, border_radius=3)


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
        cor = (60, 200, 100) if self.consertado else (140, 120, 60)
        pygame.draw.rect(surf, cor, (self.pos[0] - 22, self.pos[1] - 8, 44, 16), border_radius=3)
        pygame.draw.rect(surf, (20, 20, 20), (self.pos[0] - 22, self.pos[1] - 8, 44, 16), width=2, border_radius=3)
        if not self.consertado:
            txt = fonte.render(f"{self.golpes}/{self.golpes_necessarios}", True, (255, 255, 255))
            surf.blit(txt, txt.get_rect(center=(self.pos[0], self.pos[1] - 22)))