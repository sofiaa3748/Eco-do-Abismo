import pygame
import sys
import random

from configuracoes import LARGURA, ALTURA, BRANCO
from personagem import Jogador
from menu import Particula, criar_botoes, desenhar_fundo, desenhar_titulo, desenhar_intro_acordar
from fases import iniciar_sala, renderizar_jogo, NIVEIS, proximo_nivel
from sprites import carregar_sprites_operario, iniciar_animacao_pilula, carregar_tela
from audio import sons

def _coletados(contexto):
    itens = list(contexto.get("objetos", [])) + list(contexto.get("documentos", []))
    return {id(o): o for o in itens if getattr(o, "coletado", False) or getattr(o, "coletada", False)}


def main():
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Eco do Abismo")

    sons.iniciar()
    sons.pre_carregar()

    sprites_jogador = carregar_sprites_operario()

    try:
        fonte_titulo = pygame.font.SysFont("consolas", 64, bold=True)
        fonte_subtitulo = pygame.font.SysFont("consolas", 20)
        fonte_botao = pygame.font.SysFont("consolas", 26, bold=True)
    except Exception:
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

    contexto = iniciar_sala(jogador, nivel=nivel_atual)

    offset_tremor_x, offset_tremor_y = 0, 0
    mensagem_flash_ativo = False
    tempo_flash = 0

    DURACAO_INTRO = 3400  
    tempo_intro_inicio = 0
    tempo_game_over = 0

    while rodando:
        tempo = pygame.time.get_ticks()
        mouse = pygame.mouse.get_pos()
        teclas = pygame.key.get_pressed()

        sala = contexto["sala"]
        puzzle_modal = contexto.get("puzzle_modal")
        modal_ativo = puzzle_modal is not None and getattr(puzzle_modal, "ativo", False)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

            if estado == "MENU":
                for botao in botoes:
                    if botao.clicado(evento):
                        sons.tocar("clique")
                        if "JOGAR" in botao.texto:
                            estado = "INTRO"
                            tempo_intro_inicio = tempo
                            nivel_atual = 1
                            jogador = Jogador(100, 300, "Operário 724")
                            jogador.agachado = False
                            jogador.tem_pe_de_cabra = False
                            contexto = iniciar_sala(jogador, nivel_atual)
                        elif "SAIR" in botao.texto:
                            rodando = False

            elif estado == "INTRO":
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                    if tempo - tempo_intro_inicio >= DURACAO_INTRO:
                        estado = "JOGANDO"

            elif estado == "JOGANDO":
                if evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_ESCAPE:
                        if modal_ativo:
                            puzzle_modal.ativo = False
                        else:
                            estado = "MENU"

                    if evento.key == pygame.K_SPACE and modal_ativo:
                        puzzle_modal.atualizar(teclas)
                        sons.tocar("golpe", 0.5)

                    if evento.key == pygame.K_q:
                        jogador.agachado = not jogador.agachado
                        sons.tocar("agachar", 0.6)

                    if contexto.get("ao_tecla_down"):
                        contexto["ao_tecla_down"](contexto, jogador, evento)

                    if evento.key == pygame.K_e and not modal_ativo:
                        for f in contexto["frascos"]:
                            if not f.coletado and jogador.get_rect().colliderect(f.rect):
                                f.coletado = True
                                jogador.sanidade = min(100.0, jogador.sanidade + 10)
                                iniciar_animacao_pilula(jogador, tempo)
                                sons.tocar("pilula")

                        if contexto.get("ao_interagir"):
                            antes_porta = contexto["sala"].porta_aberta
                            antes_itens = _coletados(contexto)
                            antes_msg = contexto.get("mensagem_temporaria")
                            contexto["ao_interagir"](contexto, jogador)
                            novos = [o for k, o in _coletados(contexto).items() if k not in antes_itens]
                            if contexto["sala"].porta_aberta and not antes_porta:
                                sons.tocar("porta_abrir")
                            elif novos:
                                sons.tocar("papel" if hasattr(novos[0], "texto") else "coletar")
                            elif (contexto.get("mensagem_temporaria") != antes_msg
                                  and "trancad" in str(contexto.get("mensagem_temporaria")).lower()):
                                sons.tocar("porta_trancada")

            elif estado == "GAMEOVER":
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE and tempo - tempo_game_over > 1200:
                    sons.tocar("clique")
                    contexto = iniciar_sala(jogador, nivel_atual, resetar_jogador=True)
                    estado = "JOGANDO"
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    estado = "MENU"

            elif estado == "FINAL":
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                    estado = "MENU"

        if estado in ("MENU", "INTRO"):
            sons.musica(True, 0.18)

        if estado == "MENU":
            for p in particulas:
                p.atualizar(ALTURA)
            for botao in botoes:
                botao.atualizar(mouse)

        elif estado == "JOGANDO":
            if modal_ativo:
                jogador.andando = False
            else:
                if jogador.agachado:
                    jogador_rect_futuro = pygame.Rect(jogador.x, jogador.y, 50, 30)
                else:
                    jogador_rect_futuro = pygame.Rect(jogador.x, jogador.y, 50, 50)

                vel = 2.0 if jogador.agachado else 4.0
                dx, dy = 0, 0
                if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
                    dx = -vel
                if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
                    dx = vel
                if teclas[pygame.K_UP] or teclas[pygame.K_w]:
                    dy = -vel
                if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
                    dy = vel

                jogador.atualizar_animacao(dx, dy, tempo)

                if teclas[pygame.K_r] and contexto["caixas"]:
                    jogador_hitbox_exp = jogador_rect_futuro.inflate(15, 15)
                    for cx in contexto["caixas"]:
                        if jogador_hitbox_exp.colliderect(cx.rect):
                            if (dx or dy) and sons.cada("arrastar", tempo, 260):
                                sons.tocar("arrastar", 0.5)
                            cx.rect.x += dx
                            cx.rect.y += dy
                            cx.rect.x = max(40, min(sala.largura - 95, cx.rect.x))
                            cx.rect.y = max(40, min(sala.altura - 95, cx.rect.y))

                jogador.x += dx
                jogador.y += dy

                p_rect = pygame.Rect(jogador.x, jogador.y, jogador_rect_futuro.width, jogador_rect_futuro.height)

                duto = contexto.get("duto")
                if duto:
                    if not jogador.agachado:
                        if p_rect.colliderect(duto["corredor"]):
                            jogador.x -= dx
                            jogador.y -= dy
                    else:
                        if not duto["porta_entrada_aberta"] and p_rect.colliderect(duto["rect_entrada"]):
                            jogador.x -= dx
                        if not duto["porta_saida_aberta"] and p_rect.colliderect(duto["rect_saida"]):
                            jogador.x -= dx

                    for parede in sala.paredes_colisao():
                        if jogador.agachado and duto["corredor"].contains(p_rect):
                            continue
                        if p_rect.colliderect(parede):
                            jogador.x -= dx
                            jogador.y -= dy
                else:
                    jogador.x -= dx
                    jogador.y -= dy
                    jogador.andar_teclas(teclas, sala.largura, sala.altura, paredes=sala.paredes_colisao())

                jogador.x = max(sala.espessura_parede, min(sala.largura - sala.espessura_parede - 70, jogador.x))
                jogador.y = max(sala.espessura_parede, min(sala.altura - sala.espessura_parede - 70, jogador.y))

                jogador.dano_sanidade(contexto.get("taxa_dano_sanidade", 0.008))

                for camera in contexto["cameras"]:
                    camera.atualizar()
                    dentro_do_duto = duto is not None and duto["corredor"].contains(jogador.get_rect())
                    if dentro_do_duto:
                        continue
                    if camera.detecta(jogador):
                        mensagem_flash_ativo = True
                        tempo_flash = tempo
                        jogador.x, jogador.y = sala.ponto_entrada
                        jogador.agachado = False

                if mensagem_flash_ativo and tempo - tempo_flash > 250:
                    mensagem_flash_ativo = False

                if contexto.get("ao_atualizar"):
                    contexto["ao_atualizar"](contexto, jogador, teclas, tempo)

                sons.atualizar(nivel_atual, contexto, jogador, tempo)

                if contexto.get("final"):
                    if proximo_nivel(nivel_atual) is not None:
                        nivel_atual = proximo_nivel(nivel_atual)
                        sons.tocar("fase_completa")
                        contexto = iniciar_sala(jogador, nivel_atual, resetar_jogador=False)
                    else:
                        estado = "FINAL"
                        sons.parar_tudo()
                        sons.tocar("final")
                elif contexto["condicao_transicao"](contexto, jogador):
                    if proximo_nivel(nivel_atual) is not None:
                        nivel_atual = proximo_nivel(nivel_atual)
                        sons.tocar("fase_completa")
                        contexto = iniciar_sala(jogador, nivel_atual, resetar_jogador=False)

                if jogador.sanidade <= 0:
                    sons.tocar("game_over")
                    estado = "GAMEOVER"
                    tempo_game_over = tempo

            if jogador.sanidade < 30:
                offset_tremor_x = random.randint(-3, 3)
                offset_tremor_y = random.randint(-3, 3)
            else:
                offset_tremor_x, offset_tremor_y = 0, 0

        if estado == "MENU":
            desenhar_fundo(tela, tempo, LARGURA, ALTURA)
            for p in particulas:
                p.atualizar(ALTURA)
            desenhar_titulo(tela, tempo, LARGURA, fonte_titulo, fonte_subtitulo)
            for botao in botoes:
                botao.desenhar(tela)

            rodape = fonte_subtitulo.render("(c) 2026  Eco do Abismo", True, (40, 70, 100))
            tela.blit(rodape, rodape.get_rect(center=(LARGURA // 2, ALTURA - 20)))

        elif estado == "INTRO":
            desenhar_intro_acordar(tela, tempo - tempo_intro_inicio, LARGURA, ALTURA,
                                    fonte_subtitulo, sprites_jogador=sprites_jogador,
                                    duracao_total=DURACAO_INTRO)

        elif estado == "JOGANDO":
            renderizar_jogo(
                tela, jogador, contexto, offset_tremor_x, offset_tremor_y, mensagem_flash_ativo,
                fonte_subtitulo, sprites_jogador=sprites_jogador)

        elif estado == "GAMEOVER":
            fundo = carregar_tela("game_over")
            if fundo is not None:
                tela.blit(fundo, (0, 0))
            else:
                tela.fill((10, 2, 4))
            decorrido = tempo - tempo_game_over
            veu = pygame.Surface((LARGURA, ALTURA))
            veu.fill((0, 0, 0))
            veu.set_alpha(255 - max(0, min(255, int(255 * decorrido / 900))))
            tela.blit(veu, (0, 0))
            sombra = fonte_titulo.render("GAME OVER", True, (40, 0, 4))
            titulo = fonte_titulo.render("GAME OVER", True, (220, 40, 50))
            tela.blit(sombra, sombra.get_rect(center=(LARGURA // 2 + 4, 104)))
            tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, 100)))
            if decorrido > 1200 and (tempo // 500) % 2 == 0:
                dica = fonte_subtitulo.render("[ESPAÇO] tentar de novo     [ESC] menu", True, (235, 235, 235))
                tela.blit(dica, dica.get_rect(center=(LARGURA // 2, ALTURA - 50)))

        elif estado == "FINAL":
            tela.fill((5, 5, 10))
            linha1 = fonte_titulo.render("FIM", True, BRANCO)
            texto_final = contexto.get("mensagem_final", "Fim da demonstração.")
            linha2 = fonte_subtitulo.render(texto_final, True, (190, 190, 210))
            linha3 = fonte_subtitulo.render(
                "Pressione [ESPAÇO] para voltar ao menu", True, (130, 130, 150))
            tela.blit(linha1, linha1.get_rect(center=(LARGURA // 2, ALTURA // 2 - 60)))
            tela.blit(linha2, linha2.get_rect(center=(LARGURA // 2, ALTURA // 2)))
            tela.blit(linha3, linha3.get_rect(center=(LARGURA // 2, ALTURA // 2 + 60)))

        pygame.display.flip()
        relogio.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()