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