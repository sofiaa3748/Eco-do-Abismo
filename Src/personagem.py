import pygame
    
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

    def dano(self, ataque):
        if ataque:
            self.sanidade -= 1

class Jogador(Personagem):
    def tomar_pilula(self, tomar=True):
        if tomar:
            self.sanidade += 5
        else:
            self.sanidade -= 1
            
    def andar_teclas(self, teclas):
        velocidade = 5
        if teclas[pygame.K_LEFT]:
            self.x -= velocidade
        if teclas[pygame.K_RIGHT]:
            self.x += velocidade
        if teclas[pygame.K_UP]:
            self.x -= velocidade
        if teclas[pygame.K_DOWN]:
            self.x += velocidade
        

