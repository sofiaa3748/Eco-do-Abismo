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

    def dano_sanidade(self, quantidade):
        self.sanidade -= quantidade
        if self.sanidade < 0:
            self.sanidade = 0

class Jogador(Personagem):
    def __init__(self, x, y, nome):
        super().__init__(self, x, y, nome, sanidade =100)
        self.quantidade_pilulas = 0
        self.efeito_pilula_ativo = False
        self.tempo_pilula_ativa = 0
        self.duracao_efeito = 5000

        self.largura = 32
        self.altura = 32

    def tomar_pilula(self, tempo_atual):
        if self.quantidade_pilulas > 0 and not self.efeito_pilula_ativo:
            self.quantidade_pilulas -= 1
            self.efeito_pilula_ativo = True
            self.tempo_pilula_ativa = tempo_atual
            self.dano_sanidade (10)
            return True
        return False

    def atualizar_efeito_pilula(self, tempo_atual):
        if self.efeito_pilula_ativo:
            if tempo_atual - self.tempo_pilula_ativa > self.duracao_efeito:
                self.efeito_pilula_ativo = False
                self.dano_sanidade(25)
            
    def andar_teclas(self, teclas, largura_tela, altura_tela):
        velocidade = 4
      
        antigo_x = self.x
        antigo_y = self.y

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.x -= velocidade
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.x += velocidade
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            self.y -= velocidade
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            self.y += float(velocidade)

        if self.x < 0: self.x = 0
        if self.x > largura_tela - self.largura: self.x = largura_tela - self.largura
        if self.y < 0: self.y = 0
        if self.y > altura_tela - self.altura: self.y = altura_tela - self.altura

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.largura, self.altura)
    
        

