import pygame
import sys
import random

from configuracoes import LARGURA, ALTURA
from personagem import Jogador
from menu import Particula, criar_botoes, desenhar_fundo, desenhar_titulo
from fases import iniciar_sala, renderizar_jogo

def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Eco do Abismo")

    try:
        fonte_titulo = pygame.font.SysFont("consolas", 64, bold=True)
        fonte_subtitulo = pygame.font.SysFont("consolas", 20)
        fonte_botao = pygame.font.SysFont("consolas", 26, bold=True)
    except:
        fonte_titulo = pygame.font.SysFont(None, 64)
        fonte_subtitulo = pygame.font.SysFont(None, 20)
        fonte_botao = pygame.font.SysFont(None, 26)

    relogio = pygame.time.Clock()

    particulas = [Particula(LARGURA, ALTURA) for _ in range(90)]
    botoes = criar_botoes(LARGURA // 2, fonte_botao)

    rodando = True
    estado = "MENU"
    nivel_atual = 1

    jogador = Jogador(100, 300, "Operário 724")
    jogador.agachado = False
    jogador.tem_pe_de_cabra = False
    
    sala, frascos, cameras, puzzle, caixa_ferramentas, caixas, duto_dados, puzzle_caixa = iniciar_sala(jogador, nivel=nivel_atual)

    offset_tremor_x, offset_tremor_y = 0, 0
    mensagem_flash_ativo = False
    tempo_flash = 0

    while rodando:
        tempo = pygame.time.get_ticks()
        mouse = pygame.mouse.get_pos()
        teclas = pygame.key.get_pressed()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            if estado == "MENU":
                for botao in botoes:
                    if botao.clicado(evento):
                        if botao.texto.endswith("JOGAR"):
                            estado = "JOGANDO"
                            nivel_atual = 1
                            sala, frascos, cameras, puzzle, caixa_ferramentas, caixas, duto_dados, puzzle_caixa = iniciar_sala(jogador, nivel_atual)
                        elif botao.texto.endswith("SAIR"):
                            rodando = False

            elif estado == "JOGANDO":
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        if puzzle.ativo: puzzle.ativo = False
                        elif puzzle_caixa.ativo: puzzle_caixa.ativo = False
                        else: estado = "MENU"

                    if evento.key == pygame.K_SPACE:
                        if puzzle_caixa.ativo:
                            puzzle_caixa.atualizar(teclas)
                            if puzzle_caixa.resolvido:
                                jogador.tem_pe_de_cabra = True

                    if evento.key == pygame.K_q and nivel_atual == 2:
                        jogador.agachado = not jogador.agachado

                    if evento.key == pygame.K_e and not puzzle.ativo and not puzzle_caixa.ativo:
                        for f in frascos:
                            if not f.coletado and jogador.get_rect().colliderect(f.rect):
                                f.coletado = True
                                jogador.sanidade = min(100.0, jogador.sanidade + 10)

                        if nivel_atual == 2:
                            rect_p = jogador.get_rect()
                            if rect_p.colliderect(duto_dados["rect_entrada"].inflate(25, 25)):
                                if jogador.tem_pe_de_cabra and not duto_dados["porta_entrada_aberta"]:
                                    duto_dados["porta_entrada_aberta"] = True

                            elif rect_p.colliderect(duto_dados["rect_saida"].inflate(25, 25)):
                                if jogador.tem_pe_de_cabra and not duto_dados["porta_saida_aberta"]:
                                    duto_dados["porta_saida_aberta"] = True

                            elif caixa_ferramentas and rect_p.colliderect(caixa_ferramentas.inflate(15, 15)) and not jogador.tem_pe_de_cabra:
                                coberta = False
                                for cx in caixas:
                                    if cx.rect.colliderect(caixa_ferramentas): coberta = True
                                if not coberta:
                                    puzzle_caixa.ativo = True

                        if nivel_atual != 2 and not sala.porta_aberta and sala.jogador_na_porta(jogador):
                            puzzle.ativo = True

        if estado == "MENU":
            for p in particulas: p.atualizar(ALTURA)
            for botao in botoes: botao.atualizar(mouse)

        elif estado == "JOGANDO":
            if puzzle.ativo:
                puzzle.atualizar(teclas)
                if puzzle.resolvido: sala.porta_aberta = True
            elif puzzle_caixa.ativo:
                pass # Tratado no evento do teclado
            else:
                if jogador.agachado:
                    jogador_rect_futuro = pygame.Rect(jogador.x, jogador.y, 32, 20)
                else:
                    jogador_rect_futuro = pygame.Rect(jogador.x, jogador.y, 32, 32)
  
                vel = 2.0 if jogador.agachado else 4.0
                dx, dy = 0, 0
                if teclas[pygame.K_LEFT] or teclas[pygame.K_a]: dx = -vel
                if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]: dx = vel
                if teclas[pygame.K_UP] or teclas[pygame.K_w]: dy = -vel
                if teclas[pygame.K_DOWN] or teclas[pygame.K_s]: dy = vel

                if teclas[pygame.K_r] and nivel_atual == 2:
                    jogador_hitbox_exp = jogador_rect_futuro.inflate(15, 15)
                    for cx in caixas:
                        if jogador_hitbox_exp.colliderect(cx.rect):
                            cx.rect.x += dx
                            cx.rect.y += dy
                            cx.rect.x = max(40, min(LARGURA - 95, cx.rect.x))
                            cx.rect.y = max(40, min(ALTURA - 95, cx.rect.y))

                jogador.x += dx
                jogador.y += dy

                p_rect = pygame.Rect(jogador.x, jogador.y, jogador_rect_futuro.width, jogador_rect_futuro.height)
                
                if nivel_atual == 2:
                    if not jogador.agachado:
                        if p_rect.colliderect(duto_dados["corredor"]):
                            jogador.x -= dx
                            jogador.y -= dy
                    else:
                        if not duto_dados["porta_entrada_aberta"] and p_rect.colliderect(duto_dados["rect_entrada"]):
                            jogador.x -= dx
                        if not duto_dados["porta_saida_aberta"] and p_rect.colliderect(duto_dados["rect_saida"]):
                            jogador.x -= dx

                    for parede in sala.paredes_colisao():
                        if jogador.agachado and duto_dados["corredor"].contains(p_rect):
                            continue
                        if p_rect.colliderect(parede):
                            jogador.x -= dx
                            jogador.y -= dy
                else:
                    jogador.x -= dx
                    jogador.y -= dy
                    jogador.andar_teclas(teclas, LARGURA, ALTURA, paredes=sala.paredes_colisao())

                jogador.x = max(40, min(LARGURA - 75, jogador.x))
                jogador.y = max(40, min(ALTURA - 75, jogador.y))

                jogador.dano_sanidade(0.008) 

                for camera in cameras:
                    camera.atualizar()
                    if duto_dados and duto_dados["corredor"].contains(jogador.get_rect()):
                        continue
                    if camera.detecta(jogador):
                        mensagem_flash_ativo = True
                        tempo_flash = tempo
                        jogador.x, jogador.y = sala.ponto_entrada
                        jogador.agachado = False

                if mensagem_flash_ativo and tempo - tempo_flash > 250:
                    mensagem_flash_ativo = False

                if nivel_atual == 2:
                    if duto_dados["porta_saida_aberta"] and jogador.x > duto_dados["rect_saida"].x:
                        nivel_atual += 1
                        sala, frascos, cameras, puzzle, caixa_ferramentas, caixas, duto_dados, puzzle_caixa = iniciar_sala(jogador, nivel_atual, resetar_jogador=False)
                else:
                    if sala.porta_aberta and sala.jogador_na_porta(jogador):
                        nivel_atual += 1
                        sala, frascos, cameras, puzzle, caixa_ferramentas, caixas, duto_dados, puzzle_caixa = iniciar_sala(jogador, nivel_atual, resetar_jogador=False)

                if jogador.sanidade <= 0:
                    sala, frascos, cameras, puzzle, caixa_ferramentas, caixas, duto_dados, puzzle_caixa = iniciar_sala(jogador, nivel_atual, resetar_jogador=True)

            if jogador.sanidade < 30:
                offset_tremor_x = random.randint(-3, 3)
                offset_tremor_y = random.randint(-3, 3)
            else:
                offset_tremor_x, offset_tremor_y = 0, 0

        if estado == "MENU":
            desenhar_fundo(tela, tempo, LARGURA, ALTURA)
            for p in particulas: p.desenhar(tela)
            desenhar_titulo(tela, tempo, LARGURA, fonte_titulo, fonte_subtitulo)
            for botao in botoes: botao.desenhar(tela)
            
            rodape = fonte_subtitulo.render("© 2026  Eco do Abismo", True, (40, 70, 100))
            tela.blit(rodape, rodape.get_rect(center=(LARGURA // 2, ALTURA - 20)))

        elif estado == "JOGANDO":
            renderizar_jogo(
                tela, jogador, sala, frascos, cameras, puzzle, puzzle.ativo, 
                nivel_atual, offset_tremor_x, offset_tremor_y, mensagem_flash_ativo, 
                LARGURA, ALTURA, fonte_subtitulo, caixa_ferramentas, caixas, duto_dados, puzzle_caixa
            )

        pygame.display.flip()
        relogio.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()