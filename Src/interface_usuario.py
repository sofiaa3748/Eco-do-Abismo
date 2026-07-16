import pygame

def desenhar_hud(tela, jogador, fonte):
    pygame.draw.rect(tela, (40, 40, 45), (20, 20, 200, 20), border_radius=3)
    largura_sanidade = max(0, (jogador.sanidade / 100) * 200)
    
    cor_sanidade = (0, 255, 100) if jogador.sanidade > 60 else ((255, 200, 0) if jogador.sanidade > 30 else (255, 50, 50))
    if largura_sanidade > 0:
        pygame.draw.rect(tela, cor_sanidade, (20, 20, largura_sanidade, 20), border_radius=3)
        
    pygame.draw.rect(tela, (200, 200, 200), (20, 20, 200, 20), 2, border_radius=3)
    
    txt_sanidade = fonte.render(f"SANIDADE: {int(jogador.sanidade)}%", True, (255, 255, 255))
    tela.blit(txt_sanidade, (25, 45))

    if jogador.tem_pe_de_cabra:
        txt_item = fonte.render("INVENTÁRIO: Pé de Cabra [Equipado]", True, (150, 220, 255))
        tela.blit(txt_item, (20, 75))
    
    if jogador.agachado:
        txt_agachado = fonte.render("ESTADO: Agachado (Furtivo)", True, (200, 200, 200))
        tela.blit(txt_agachado, (20, 100))

def desenhar_mensagem_contextual(tela, texto, largura, altura, fonte, y=None):
    if y is None:
        y = altura - 60
        
    txt = fonte.render(texto, True, (255, 255, 200))
    rect = txt.get_rect(center=(largura // 2, y))
    
    fundo = pygame.Rect(rect.x - 15, rect.y - 8, rect.width + 30, rect.height + 16)
    pygame.draw.rect(tela, (15, 15, 20, 230), fundo, border_radius=6)
    pygame.draw.rect(tela, (100, 100, 110), fundo, width=2, border_radius=6)
    
    tela.blit(txt, rect)

def desenhar_flash_detectado(tela, largura, altura):
    flash = pygame.Surface((largura, altura), pygame.SRCALPHA)
    flash.fill((255, 0, 0, 120)) # Vermelho translúcido agressivo
    tela.blit(flash, (0, 0))