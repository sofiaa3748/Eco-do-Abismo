import pygame
import math
from abc import ABC, abstractmethod

from configuracoes import ROXO_ALUCINACAO, VERMELHO_ALARME

class Personagem(ABC):
    def __init__(self, x, y, nome, dano):
        self.x = x
        self.y = y
        self.nome = nome
        self.dano = dano
        self.vida = 100.0

    def atacar(self, personagem):
        personagem.tomar_dano(self.dano)

    def tomar_dano(self, quantidade):
        self.vida -= quantidade
        if self.vida <= 0:
            self.vida = 0
            return True
        return False

    @abstractmethod
    def mover(self, direcao):
        raise NotImplementedError

class Jogador(Personagem):
    def __init__(self, x, y, nome):
        super().__init__(x, y, nome, dano=10)
        self.nome = 'Operário 724'
        self.agachado = False
        self.tem_pe_de_cabra = False
        self.direcao = 'frente'
        self.andando = False
        self.frame_index = 0
        self.tamanho_base = 110

    def get_rect(self):
        if self.agachado:
            return pygame.Rect(self.x, self.y + int(self.tamanho_base * 0.375), self.tamanho_base, int(self.tamanho_base * 0.625))
        return pygame.Rect(self.x, self.y, self.tamanho_base, self.tamanho_base)

    def mover(self, direcao):
        vel = 2.0 if self.agachado else 4.0
        if direcao == 'esquerda':
            self.x -= vel
        elif direcao == 'direita':
            self.x += vel
        elif direcao == 'cima':
            self.y -= vel
        elif direcao == 'baixo':
            self.y += vel

    def andar_teclas(self, teclas, largura, altura, paredes):
        vel = 1.5 if self.agachado else 4.0
        dx, dy = 0, 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx = -vel
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx = vel
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy = -vel
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy = vel

        self.x += dx
        for p in paredes:
            if self.get_rect().colliderect(p):
                self.x -= dx
                break

        self.y += dy
        for p in paredes:
            if self.get_rect().colliderect(p):
                self.y -= dy
                break

        self.x = max(0, min(self.x, largura - self.tamanho_base))
        self.y = max(0, min(self.y, altura - self.tamanho_base))

    def dano_sanidade(self, valor):
        self.sanidade -= valor
        if self.sanidade < 0:
            self.sanidade = 0

    def atualizar_animacao(self, dx, dy, tempo_ms):
        if dx != 0 or dy != 0:
            self.andando = True
            if abs(dx) >= abs(dy):
                self.direcao = 'direita' if dx > 0 else 'esquerda'
            else:
                self.direcao = 'costas' if dy < 0 else 'frente'
            self.frame_index = (tempo_ms // 150) % 2
        else:
            self.andando = False
            self.frame_index = 0

    def desenhar(self, tela, sprites, offset=(0, 0)):
        grupo = sprites[self.direcao]
        imagem = grupo['andando'][self.frame_index] if self.andando else grupo['parado']

        imagem = pygame.transform.scale(imagem, (self.tamanho_base, self.tamanho_base))

        if self.agachado:
            largura_img, altura_img = imagem.get_size()
            imagem = pygame.transform.scale(imagem, (largura_img, int(altura_img * 0.65)))

        rect_colisao = self.get_rect()

        pos_pes = (rect_colisao.centerx + offset[0], rect_colisao.bottom + offset[1] + 2)

        rect_imagem = imagem.get_rect(midbottom=pos_pes)
        tela.blit(imagem, rect_imagem)

    def atacar(self, personagem):
        return super().atacar(personagem)

class CameraSeguranca(Personagem):

    def __init__(self, x, y, angulo_inicial, alcance, abertura_graus, velocidade_giro, arco_max):
        super().__init__(x, y, nome='Câmera de segurança', dano=0)
        self.angulo_atual = angulo_inicial
        self.angulo_base = angulo_inicial
        self.alcance = alcance
        self.abertura = abertura_graus
        self.vel = velocidade_giro
        self.arco_max = arco_max
        self.direcao_giro = 1

    def mover(self, direcao):
        pass

    def atualizar(self):
        if self.arco_max > 0:
            self.angulo_atual += self.vel * self.direcao_giro
            if abs(self.angulo_atual - self.angulo_base) > self.arco_max:
                self.direcao_giro *= -1

    def desenhar(self, surf_base, cone_surf, jogador):
        pygame.draw.circle(surf_base, (50, 50, 50), (self.x, self.y), 10)
        pygame.draw.circle(surf_base, (255, 50, 50), (self.x, self.y), 4)

        pontos = [(self.x, self.y)]
        passos = 12
        ang_inicial = math.radians(self.angulo_atual - self.abertura / 2)
        ang_final = math.radians(self.angulo_atual + self.abertura / 2)

        for i in range(passos + 1):
            ang = ang_inicial + (ang_final - ang_inicial) * (i / passos)
            px = self.x + math.cos(ang) * self.alcance
            py = self.y + math.sin(ang) * self.alcance
            pontos.append((px, py))

        cor_cone = (255, 50, 50, 70) if self.detecta(jogador) else (255, 255, 100, 50)
        pygame.draw.polygon(cone_surf, cor_cone, pontos)

    def detecta(self, jogador):
        rect = jogador.get_rect()
        centro_j = rect.center
        dist = math.hypot(centro_j[0] - self.x, centro_j[1] - self.y)

        if dist > self.alcance:
            return False

        ang_j = math.degrees(math.atan2(centro_j[1] - self.y, centro_j[0] - self.x))
        ang_diff = (ang_j - self.angulo_atual + 180) % 360 - 180

        if abs(ang_diff) <= self.abertura / 2:
            return True
        return False


class Inimigo(Personagem):
    """Vulto que surge no escuro, persegue o jogador e drena a sanidade ao tocá-lo."""

    DURACAO_SURGIMENTO = 1000

    def __init__(self, x, y, velocidade=2.6, dano=7, recarga_ms=900, atraso_ms=0, lado_desvio=1):
        super().__init__(x, y, nome='Vulto', dano=dano)
        self.velocidade = velocidade
        self.recarga_ms = recarga_ms
        self.atraso_ms = atraso_ms
        self.lado_desvio = lado_desvio
        self.tamanho = 56
        self.tempo_surgimento = None
        self.ultimo_ataque = -10 ** 9
        self.semente = x * 0.013 + y * 0.007

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.tamanho, self.tamanho)

    def surgir(self, tempo_ms):
        if self.tempo_surgimento is None:
            self.tempo_surgimento = tempo_ms + self.atraso_ms

    def progresso_surgimento(self, tempo_ms):
        if self.tempo_surgimento is None:
            return 0.0
        return max(0.0, min(1.0, (tempo_ms - self.tempo_surgimento) / self.DURACAO_SURGIMENTO))

    def ativo(self, tempo_ms):
        return self.progresso_surgimento(tempo_ms) >= 1.0

    def mover(self, direcao):
        if direcao == 'esquerda':
            self.x -= self.velocidade
        elif direcao == 'direita':
            self.x += self.velocidade
        elif direcao == 'cima':
            self.y -= self.velocidade
        elif direcao == 'baixo':
            self.y += self.velocidade

    def _bate(self, paredes):
        rect = self.get_rect()
        return any(rect.colliderect(p) for p in paredes)

    def _deslocar(self, dx, dy, paredes):
        """Anda em X e em Y separadamente (assim ele desliza nas paredes). Devolve (moveu_x, moveu_y)."""
        moveu_x = moveu_y = True
        self.x += dx
        if self._bate(paredes):
            self.x -= dx
            moveu_x = False
        self.y += dy
        if self._bate(paredes):
            self.y -= dy
            moveu_y = False
        return moveu_x, moveu_y

    def perseguir(self, jogador, paredes, tempo_ms, outros=()):
        if not self.ativo(tempo_ms):
            return

        cx, cy = self.get_rect().center
        alvo_x, alvo_y = jogador.get_rect().center
        vx, vy = alvo_x - cx, alvo_y - cy
        dist = math.hypot(vx, vy)
        if dist < 50:
            return

        dx = vx / dist * self.velocidade
        dy = vy / dist * self.velocidade

        for outro in outros:
            if outro is self or not outro.ativo(tempo_ms):
                continue
            ox, oy = outro.get_rect().center
            d = math.hypot(cx - ox, cy - oy)
            if 0 < d < self.tamanho:
                dx += (cx - ox) / d * 0.8
                dy += (cy - oy) / d * 0.8

        moveu_x, moveu_y = self._deslocar(dx, dy, paredes)

        if not moveu_x and abs(dy) < self.velocidade * 0.5:
            self._deslocar(0, self.lado_desvio * self.velocidade, paredes)
        elif not moveu_y and abs(dx) < self.velocidade * 0.5:
            self._deslocar(self.lado_desvio * self.velocidade, 0, paredes)

    def pode_atacar(self, jogador, tempo_ms):
        if not self.ativo(tempo_ms):
            return False
        if tempo_ms - self.ultimo_ataque < self.recarga_ms:
            return False
        return self.get_rect().inflate(10, 10).colliderect(jogador.get_rect())

    def atacar(self, jogador, tempo_ms=0):
        self.ultimo_ataque = tempo_ms
        jogador.dano_sanidade(self.dano)

    def tentar_atacar(self, jogador, tempo_ms):
        if self.pode_atacar(jogador, tempo_ms):
            self.atacar(jogador, tempo_ms)
            return True
        return False

    def desenhar_corpo(self, surf, tempo_ms):
        prog = self.progresso_surgimento(tempo_ms)
        if prog <= 0:
            return
        a = int(255 * prog)
        rect = self.get_rect()
        tremor = int(2 * math.sin(tempo_ms / 90 + self.semente))

        fig = pygame.Surface((70, 90), pygame.SRCALPHA)
        pygame.draw.ellipse(fig, (*ROXO_ALUCINACAO, a // 6), (0, 10, 70, 80))
        manto = [(35 + tremor, 8), (58, 40), (62, 82), (52, 76), (44, 86),
                 (35, 76), (26, 86), (18, 76), (8, 82), (12, 40)]
        pygame.draw.polygon(fig, (22, 12, 34, int(a * 0.95)), manto)
        pygame.draw.polygon(fig, (70, 35, 105, a), manto, width=2)
        surf.blit(fig, (rect.centerx - 35, rect.bottom - 86))

    def desenhar_olhos(self, surf, tempo_ms):
        """Separado do corpo para os olhos poderem brilhar por cima da escuridão."""
        prog = self.progresso_surgimento(tempo_ms)
        if prog <= 0:
            return
        a = int(255 * prog)
        rect = self.get_rect()
        atacando = tempo_ms - self.ultimo_ataque < 250
        cor = VERMELHO_ALARME if atacando else (200, 120, 255)
        pulso = 3 + int(1.5 * math.sin(tempo_ms / 120 + self.semente))

        brilho = pygame.Surface((70, 30), pygame.SRCALPHA)
        for ox in (-9, 9):
            pygame.draw.circle(brilho, (*cor, a // 4), (35 + ox, 15), pulso + 6)
            pygame.draw.circle(brilho, (*cor, a), (35 + ox, 15), pulso)
        surf.blit(brilho, (rect.centerx - 35, rect.bottom - 86 + 15))

    def desenhar(self, surf, tempo_ms):
        self.desenhar_corpo(surf, tempo_ms)
        self.desenhar_olhos(surf, tempo_ms)

class GuardaPrisao(Personagem):
    """Guarda da prisão.

    Patrulha uma rota (ou fica parado num posto olhando de um lado para o outro),
    enxerga dentro de um cone, investiga barulhos e vai enchendo a "suspeita"
    enquanto vê o jogador. Quando a suspeita chega a 1.0, o jogador foi visto.

    - Agachado, o jogador só é visto de perto (metade do alcance).
    - Agachado dentro de um esconderijo, só é visto se o guarda quase esbarrar nele.
    - Paredes bloqueiam a visão.
    """

    TAMANHO = 50
    DISTANCIA_ESBARRAO = 45
    _fonte = None
    _ponto = None

    def __init__(self, x, y, rota=None, angulo=0.0, velocidade=1.3, alcance=330, abertura=56,
                 pausa_ms=1500, varredura=0.0, tempo_vista_em_pe=650, tempo_vista_agachado=1300):
        super().__init__(x, y, nome='Guarda', dano=0)
        self.origem = (x, y)
        self.angulo_inicial = angulo
        self.rota = [tuple(p) for p in rota] if rota else []
        self.velocidade = velocidade
        self.alcance = alcance
        self.abertura = abertura
        self.pausa_ms = pausa_ms
        self.varredura = varredura
        self.tempo_vista_em_pe = tempo_vista_em_pe
        self.tempo_vista_agachado = tempo_vista_agachado
        self.paredes = []
        self.reiniciar()

    def reiniciar(self):
        self.x, self.y = self.origem
        self.angulo = self.angulo_inicial
        self.indice_rota = 1 if len(self.rota) > 1 else 0
        self.estado = 'patrulha' if len(self.rota) > 1 else 'posto'
        self.espera_ate = 0
        self.alvo_som = None
        self.tempo_investigando = 6000
        self.olhando_ate = 0
        self.angulo_chegada = self.angulo
        self.travado_ms = 0.0
        self.suspeita = 0.0
        self.viu = False
        self._t = None

    def definir_mundo(self, paredes):
        self.paredes = paredes

    def get_rect(self):
        return pygame.Rect(int(self.x - self.TAMANHO // 2), int(self.y - self.TAMANHO // 2),
                           self.TAMANHO, self.TAMANHO)

    def mover(self, direcao):
        pass

    def _angulo_para(self, ponto):
        return math.degrees(math.atan2(ponto[1] - self.y, ponto[0] - self.x))

    def _virar(self, alvo, taxa):
        dif = (alvo - self.angulo + 180) % 360 - 180
        if abs(dif) <= taxa:
            self.angulo = alvo % 360
        else:
            self.angulo = (self.angulo + (taxa if dif > 0 else -taxa)) % 360

    def _bate(self):
        return self.get_rect().collidelist(self.paredes) != -1

    def _ir_para(self, ponto, velocidade, fator):
        vx, vy = ponto[0] - self.x, ponto[1] - self.y
        dist = math.hypot(vx, vy)
        passo = velocidade * fator
        if dist <= passo:
            self.x, self.y = ponto
            return True
        self._virar(self._angulo_para(ponto), 7 * fator)
        antes = (self.x, self.y)
        dx, dy = vx / dist * passo, vy / dist * passo
        self.x += dx
        if self._bate():
            self.x -= dx
        self.y += dy
        if self._bate():
            self.y -= dy
        if math.hypot(self.x - antes[0], self.y - antes[1]) < passo * 0.1:
            self.travado_ms += fator * 16.667
            if self.travado_ms > 1200:
                self.travado_ms = 0.0
                return True
        else:
            self.travado_ms = 0.0
        return False

    def ouvir(self, ponto, tempo_ms, raio=950, tempo_investigando=6000):
        if math.hypot(ponto[0] - self.x, ponto[1] - self.y) > raio:
            return False
        self.estado = 'investigando'
        self.alvo_som = (float(ponto[0]), float(ponto[1]))
        self.tempo_investigando = tempo_investigando
        self.travado_ms = 0.0
        return True

    def _comportamento(self, tempo_ms, fator):
        if self.estado == 'investigando':
            if self.alvo_som is not None:
                if self._ir_para(self.alvo_som, self.velocidade * 1.6, fator):
                    self.alvo_som = None
                    self.olhando_ate = tempo_ms + self.tempo_investigando
                    self.angulo_chegada = self.angulo
            else:
                self.angulo = (self.angulo_chegada + 40 * math.sin(tempo_ms / 450)) % 360
                if tempo_ms >= self.olhando_ate:
                    self.estado = 'voltando'
        elif self.estado == 'voltando':
            destino = self.rota[self.indice_rota] if self.rota else self.origem
            if self._ir_para(destino, self.velocidade, fator):
                self.estado = 'patrulha' if len(self.rota) > 1 else 'posto'
        elif self.estado == 'patrulha':
            destino = self.rota[self.indice_rota]
            if tempo_ms < self.espera_ate:
                self._virar(self._angulo_para(destino), 3 * fator)
            elif self._ir_para(destino, self.velocidade, fator):
                self.indice_rota = (self.indice_rota + 1) % len(self.rota)
                self.espera_ate = tempo_ms + self.pausa_ms
        else:  # posto
            self._virar(self.angulo_inicial + self.varredura * math.sin(tempo_ms / 1100), 2 * fator)

    def _em_parede(self, px, py):
        if GuardaPrisao._ponto is None:
            GuardaPrisao._ponto = pygame.Rect(0, 0, 1, 1)
        GuardaPrisao._ponto.x = int(px)
        GuardaPrisao._ponto.y = int(py)
        return GuardaPrisao._ponto.collidelist(self.paredes) != -1

    def enxerga(self, jogador, esconderijos=()):
        rect = jogador.get_rect()
        cx, cy = rect.center
        dist = math.hypot(cx - self.x, cy - self.y)

        escondido = jogador.agachado and any(e.collidepoint(cx, cy) for e in esconderijos)
        if escondido:
            alcance = self.DISTANCIA_ESBARRAO
        elif jogador.agachado:
            alcance = self.alcance * 0.5
        else:
            alcance = self.alcance
        if dist > alcance:
            return False

        if dist > self.DISTANCIA_ESBARRAO:
            ang = math.degrees(math.atan2(cy - self.y, cx - self.x))
            if abs((ang - self.angulo + 180) % 360 - 180) > self.abertura / 2:
                return False

        passos = int(dist // 12)
        for i in range(1, passos):
            t = i / passos
            if self._em_parede(self.x + (cx - self.x) * t, self.y + (cy - self.y) * t):
                return False
        return True

    def atualizar(self, jogador, esconderijos, tempo_ms):
        dt = 16.667 if self._t is None else max(0.0, min(50.0, tempo_ms - self._t))
        self._t = tempo_ms
        fator = dt / 16.667

        self.viu = self.enxerga(jogador, esconderijos)
        if self.viu:
            self._virar(self._angulo_para(jogador.get_rect().center), 9 * fator)
            tempo_total = self.tempo_vista_agachado if jogador.agachado else self.tempo_vista_em_pe
            self.suspeita = min(1.0, self.suspeita + dt / tempo_total)
            return self.suspeita >= 1.0

        self.suspeita = max(0.0, self.suspeita - dt / 2500)
        self._comportamento(tempo_ms, fator)
        return False

    def _pontos_do_cone(self):
        pontos = [(self.x, self.y)]
        passos = 14
        a0 = math.radians(self.angulo - self.abertura / 2)
        a1 = math.radians(self.angulo + self.abertura / 2)
        for i in range(passos + 1):
            ang = a0 + (a1 - a0) * i / passos
            c, s = math.cos(ang), math.sin(ang)
            d = 0
            while d < self.alcance:
                if self._em_parede(self.x + c * (d + 12), self.y + s * (d + 12)):
                    break
                d += 12
            pontos.append((self.x + c * d, self.y + s * d))
        return pontos

    def desenhar(self, surf_base, cone_surf, jogador):
        tempo_ms = pygame.time.get_ticks()
        cx, cy = int(self.x), int(self.y)

        perto = abs(jogador.get_rect().centerx - cx) < 900
        if perto:
            alerta = self.viu or self.suspeita >= 0.7
            if alerta:
                cor_cone = (255, 50, 50, 80)
            elif self.suspeita > 0.15 or self.estado == 'investigando':
                cor_cone = (255, 170, 40, 65)
            else:
                cor_cone = (255, 255, 120, 45)
            pygame.draw.polygon(cone_surf, cor_cone, self._pontos_do_cone())

        rad = math.radians(self.angulo)
        fx, fy = math.cos(rad), math.sin(rad)
        pygame.draw.circle(surf_base, (22, 26, 40), (cx, cy), 23)
        pygame.draw.circle(surf_base, (58, 70, 108), (cx, cy), 20)
        pygame.draw.line(surf_base, (30, 34, 50), (cx - fy * 20, cy + fx * 20), (cx + fy * 20, cy - fx * 20), 5)
        pygame.draw.circle(surf_base, (205, 175, 145), (int(cx + fx * 4), int(cy + fy * 4)), 11)
        pygame.draw.circle(surf_base, (30, 34, 50), (int(cx + fx * 7), int(cy + fy * 7)), 11, width=3)
        lanterna = (int(cx + fx * 30), int(cy + fy * 30))
        pygame.draw.line(surf_base, (90, 90, 100), (cx + fx * 18, cy + fy * 18), lanterna, 4)
        pygame.draw.circle(surf_base, (255, 240, 150), lanterna, 5)

        if self.suspeita > 0.04:
            if GuardaPrisao._fonte is None:
                GuardaPrisao._fonte = pygame.font.SysFont(None, 30, bold=True)
            largura = 44
            barra = pygame.Rect(cx - largura // 2, cy - 48, largura, 6)
            pygame.draw.rect(surf_base, (30, 30, 35), barra)
            cor = (255, 70, 60) if self.suspeita >= 0.7 else (255, 200, 60)
            pygame.draw.rect(surf_base, cor, (barra.x, barra.y, int(largura * self.suspeita), 6))
            pygame.draw.rect(surf_base, (210, 210, 210), barra, width=1)
            marca = GuardaPrisao._fonte.render("!" if self.suspeita >= 0.7 else "?", True, cor)
            surf_base.blit(marca, marca.get_rect(midbottom=(cx, cy - 50)))
        elif self.estado == 'investigando':
            if GuardaPrisao._fonte is None:
                GuardaPrisao._fonte = pygame.font.SysFont(None, 30, bold=True)
            marca = GuardaPrisao._fonte.render("?", True, (255, 200, 60))
            surf_base.blit(marca, marca.get_rect(midbottom=(cx, cy - 30)))