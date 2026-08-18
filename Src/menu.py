import pygame
import sys
import random
import math

class Particula:
    def __init__(self, largura, altura):
        self.x = random.randint(0, largura)
        self.y = random.randint(0, altura)
        self.vy = random.uniform(-0.3, -1.5)
        self.tamanho = random.randint(1, 4)
        self.brilho = random.randint(100, 255)
        
    def atualizar(self, altura):
        self.y += self.vy
        if self.y < 0:
            self.y = altura
            
    def desenhar(self, tela):
        brilho_extra = min(255, int(self.brilho) + 20)
        cor = (int(self.brilho), int(self.brilho), brilho_extra)
        pygame.draw.circle(tela, cor, (int(self.x), int(self.y)), self.tamanho)

class Botao:
    def __init__(self, x, y, texto, fonte):
        self.texto = texto
        self.fonte = fonte
        self.imagem = self.fonte.render(self.texto, True, (255, 255, 255))
        self.rect = self.imagem.get_rect(center=(x, y))
        self.hover = False

    def atualizar(self, mouse_pos):
        self.hover = self.rect.inflate(60, 30).collidepoint(mouse_pos)

    def desenhar(self, tela):
        cor_fundo = (60, 120, 200) if self.hover else (40, 60, 100)
        caixa = self.rect.inflate(60, 30)
        pygame.draw.rect(tela, cor_fundo, caixa, border_radius=8)
        pygame.draw.rect(tela, (200, 220, 255), caixa, width=2, border_radius=8)
        tela.blit(self.imagem, self.rect)

    def clicado(self, evento):
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.rect.inflate(60, 30).collidepoint(evento.pos):
                return True
        return False

def criar_botoes(centro_x, fonte):
    return [
        Botao(centro_x, 380, "JOGAR", fonte),
        Botao(centro_x, 460, "SAIR", fonte),
    ]

def desenhar_fundo(tela, tempo, largura, altura):
    tela.fill((10, 10, 30))

def desenhar_titulo(tela, tempo, largura, fonte_titulo, fonte_sub):
    oscilacao = math.sin(tempo / 400) * 8
    
    txt = fonte_titulo.render("ECO DO ABISMO", True, (220, 230, 255))
    sombra = fonte_titulo.render("ECO DO ABISMO", True, (50, 50, 80))
    
    tela.blit(sombra, sombra.get_rect(center=(largura // 2 + 4, 150 + int(oscilacao) + 4)))
    tela.blit(txt, txt.get_rect(center=(largura // 2, 150 + int(oscilacao))))
    
    sub = fonte_sub.render("Tome as pílulas e mantenha sua sanidade...", True, (130, 140, 160))
    tela.blit(sub, sub.get_rect(center=(largura // 2, 230 + int(oscilacao))))
