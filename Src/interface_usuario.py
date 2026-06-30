import pygame

BRANCO = (255, 255, 255)
CIANO_BRILHO = (0, 220, 255)
DOURADO_BRILHO = (255, 210, 80)
VERMELHO_SANGUE = (180, 20, 20)
PRETO_SEMI = (0, 0, 0, 160)


def desenhar_hud(surf, jogador, fonte):
    """HUD principal: sanidade, pílulas e efeito ativo."""
    pygame.draw.rect(surf, (40, 40, 40), (20, 20, 200, 18), border_radius=3)

    proporcao_barra = int(200 * (jogador.sanidade / 100))
    cor_barra = CIANO_BRILHO if jogador.efeito_pilula_ativo else VERMELHO_SANGUE
    if proporcao_barra > 0:
        pygame.draw.rect(surf, cor_barra, (20, 20, proporcao_barra, 18), border_radius=3)

    txt_sanidade = fonte.render(f"SANIDADE: {int(jogador.sanidade)}%", True, BRANCO)
    surf.blit(txt_sanidade, (20, 45))

    txt_inventario = fonte.render(f"PÍLULAS: {jogador.quantidade_pilulas}", True, DOURADO_BRILHO)
    surf.blit(txt_inventario, (20, 70))

    if jogador.efeito_pilula_ativo:
        txt_efeito = fonte.render("[EFEITO ATIVO]", True, CIANO_BRILHO)
        surf.blit(txt_efeito, (20, 95))


def desenhar_mensagem_contextual(surf, texto, largura_tela, altura_tela, fonte, y=None):
    """
    Mensagem central de aviso/objetivo, ex: 'Pressione E para interagir',
    'Resolva o puzzle para abrir a porta', 'Você foi detectado!'.
    """
    if y is None:
        y = altura_tela - 50

    txt = fonte.render(texto, True, BRANCO)
    largura_fundo = txt.get_width() + 24
    altura_fundo = txt.get_height() + 12

    fundo = pygame.Surface((largura_fundo, altura_fundo), pygame.SRCALPHA)
    fundo.fill(PRETO_SEMI)
    surf.blit(fundo, (largura_tela // 2 - largura_fundo // 2, y - altura_fundo // 2))
    surf.blit(txt, txt.get_rect(center=(largura_tela // 2, y)))


def desenhar_flash_detectado(surf, largura_tela, altura_tela, alfa=90):
    """Flash vermelho de tela cheia ao ser detectado pela câmera."""
    flash = pygame.Surface((largura_tela, altura_tela), pygame.SRCALPHA)
    flash.fill((180, 20, 20, alfa))
    surf.blit(flash, (0, 0))