import pygame
import math
from abc import ABC, abstractmethod

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
 
    def get_rect(self):
        if self.agachado:
            return pygame.Rect(self.x, self.y + 12, 32, 20)
        return pygame.Rect(self.x, self.y, 32, 32)
 
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
        vel = 2.0 if self.agachado else 4.0
 
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

        self.x = max(0, min(self.x, largura - 32))
        self.y = max(0, min(self.y, altura - 32))

    def dano_sanidade(self, valor):
        self.sanidade -= valor
        if self.sanidade < 0:
            self.sanidade = 0
 
    def atacar(self, personagem):
        return super().atacar(personagem)


class Inimigo(Personagem):
 
    def __init__(self, x, y, nome, largura_tela, altura_tela):
        super().__init__(x, y, nome, dano=10)
        self.nome = 'Inimigos'
        self.largura_tela = largura_tela
        self.altura_tela = altura_tela
        self.tamanho = 20
        self.cor = (255, 255, 255)
        self.vida = 120.0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.tamanho, self.tamanho)

    def atacar(self, personagem):
        return super().atacar(personagem)
 
    def fora_da_tela(self):
        return self.rect.top > self.altura_tela
 
    def desenhar(self, superficie):
        pygame.draw.rect(superficie, self.cor, self.rect)
 
    def mover(self, direcao, velocidade=2.0):
        if direcao == 'esquerda':
            self.x -= velocidade
        elif direcao == 'direita':
            self.x += velocidade
        elif direcao == 'cima':
            self.y -= velocidade
        elif direcao == 'baixo':
            self.y += velocidade
 
    def perseguir(self, jogador):
        if self.x < jogador.x:
            self.mover('direita')
        elif self.x > jogador.x:
            self.mover('esquerda')
        elif self.y < jogador.y:
            self.mover('baixo')
        elif self.y > jogador.y:
            self.mover('cima')
 
    def tomar_dano(self, quantidade):
        return super().tomar_dano(quantidade)

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