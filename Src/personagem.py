import pygame
import math


class Personagem:
    def __init__(self, x, y, nome, sanidade=10):
        self.nome = nome
        self.x = x
        self.y = y
        self.sanidade = sanidade

    def mover(self, direcao):
        if direcao == 'pular':
            self.y -= 1
        elif direcao == 'agachar':
            self.y += 1
        elif direcao == 'esquerda':
            self.x -= 1
        elif direcao == 'direita':
            self.x += 1

    def dano_sanidade(self, quantidade):
        self.sanidade -= quantidade
        if self.sanidade < 0:
            self.sanidade = 0
        if self.sanidade > 100:
            self.sanidade = 100


class Jogador(Personagem):
    def __init__(self, x, y, nome):
        super().__init__(x, y, nome, sanidade=100)

        self.quantidade_pilulas = 0
        self.efeito_pilula_ativo = False
        self.tempo_pilula_ativa = 0
        self.duracao_efeito = 5000 

        self.largura = 32
        self.altura = 32

    def tomar_pilula(self, tempo_atual):
        """Consome uma pílula do inventário e ativa o efeito (visão de pistas)."""
        if self.quantidade_pilulas > 0 and not self.efeito_pilula_ativo:
            self.quantidade_pilulas -= 1
            self.efeito_pilula_ativo = True
            self.tempo_pilula_ativa = tempo_atual
            self.dano_sanidade(10)
            return True
        return False

    def tentar_tomar_pilula(self, tempo_atual):
        return self.tomar_pilula(tempo_atual)

    def atualizar_efeito_pilula(self, tempo_atual):
        if self.efeito_pilula_ativo:
            if tempo_atual - self.tempo_pilula_ativa > self.duracao_efeito:
                self.efeito_pilula_ativo = False
                self.dano_sanidade(25) 

    def andar_teclas(self, teclas, largura_tela, altura_tela, paredes=None):
        """
        Movimentação com colisão.
        'paredes' é uma lista de pygame.Rect (vem da Sala). Se None, só
        respeita os limites da tela (comportamento antigo).
        """
        velocidade = 4
        paredes = paredes or []

        antigo_x = self.x
        antigo_y = self.y

        dx = 0
        dy = 0
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx -= velocidade
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx += velocidade
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            dy -= velocidade
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            dy += velocidade

        self.x += dx
        if self._colide_com_paredes(paredes):
            self.x = antigo_x

        self.y += dy
        if self._colide_com_paredes(paredes):
            self.y = antigo_y

        if self.x < 0:
            self.x = 0
        if self.x > largura_tela - self.largura:
            self.x = largura_tela - self.largura
        if self.y < 0:
            self.y = 0
        if self.y > altura_tela - self.altura:
            self.y = altura_tela - self.altura

    def _colide_com_paredes(self, paredes):
        rect_jogador = self.get_rect()
        for parede in paredes:
            if rect_jogador.colliderect(parede):
                return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.largura, self.altura)


class CameraSeguranca:
    """
    Sentinela eletrônica com campo de visão em cone giratório (Semana 5).
    Se o jogador entrar no cone, conta-se como detectado.
    """

    def __init__(self, x, y, angulo_inicial=0, alcance=180,
                 abertura_graus=50, velocidade_giro=0.8, arco_max=60):
        self.x = x
        self.y = y
        self.angulo = angulo_inicial    
        self.alcance = alcance           
        self.abertura_graus = abertura_graus
        self.velocidade_giro = velocidade_giro
        self.arco_max = arco_max         
        self._direcao_giro = 1
        self._angulo_base = angulo_inicial

    def atualizar(self):
        self.angulo += self.velocidade_giro * self._direcao_giro

        limite_superior = self._angulo_base + self.arco_max
        limite_inferior = self._angulo_base - self.arco_max

        if self.angulo >= limite_superior:
            self.angulo = limite_superior
            self._direcao_giro = -1
        elif self.angulo <= limite_inferior:
            self.angulo = limite_inferior
            self._direcao_giro = 1

    def detecta(self, jogador):
        """Retorna True se o centro do jogador está dentro do cone de visão."""
        centro_jogador = jogador.get_rect().center
        dx = centro_jogador[0] - self.x
        dy = centro_jogador[1] - self.y
        distancia = math.hypot(dx, dy)

        if distancia > self.alcance:
            return False

        angulo_para_jogador = math.degrees(math.atan2(dy, dx)) % 360
        angulo_camera = self.angulo % 360

        diferenca = (angulo_para_jogador - angulo_camera + 180) % 360 - 180

        return abs(diferenca) <= self.abertura_graus / 2

    def pontos_do_cone(self):
        """Calcula os pontos do polígono do cone, para desenhar na tela."""
        meia_abertura = self.abertura_graus / 2
        ang_esq = math.radians(self.angulo - meia_abertura)
        ang_dir = math.radians(self.angulo + meia_abertura)

        p1 = (self.x, self.y)
        p2 = (self.x + math.cos(ang_esq) * self.alcance,
              self.y + math.sin(ang_esq) * self.alcance)
        p3 = (self.x + math.cos(ang_dir) * self.alcance,
              self.y + math.sin(ang_dir) * self.alcance)

        return [p1, p2, p3]