import os
import pygame
import sprites as S
from personagem import Inimigo

pygame.init()
pygame.display.set_mode((1, 1))
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sprites")
for p in ("objetos", "puzzles", "mapa", "inimigos"):
    os.makedirs(os.path.join(base, p), exist_ok=True)
fonte = pygame.font.SysFont(None, 18)
peças = []   # (rotulo, surface)


def salvar(pasta, nome, surf):
    pygame.image.save(surf, os.path.join(base, pasta, nome + ".png"))
    peças.append((nome, surf))


def em_surface(w, h, fn):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    fn(s)
    return s


# objetos
for nome in ("pilula", "chave", "documento", "documento_especial", "dica", "mascara", "lanterna", "pe_de_cabra", "caixa_base"):
    salvar("objetos", nome, S._CONSTRUTORES[nome]())

# puzzles
salvar("puzzles", "valvula_fechada", em_surface(60, 60, lambda s: S.desenhar_valvula(s, (30, 40), False, 0)))
salvar("puzzles", "valvula_aberta", em_surface(60, 60, lambda s: S.desenhar_valvula(s, (30, 40), True, 0)))
salvar("puzzles", "disjuntor_desligado", em_surface(40, 56, lambda s: S.desenhar_disjuntor(s, (20, 28), False, 0)))
salvar("puzzles", "disjuntor_ligado", em_surface(40, 56, lambda s: S.desenhar_disjuntor(s, (20, 28), True, 0)))
salvar("puzzles", "cofre_fechado", em_surface(90, 90, lambda s: S.desenhar_cofre(s, pygame.Rect(0, 0, 90, 90), False)))
salvar("puzzles", "cofre_aberto", em_surface(90, 90, lambda s: S.desenhar_cofre(s, pygame.Rect(0, 0, 90, 90), True)))
salvar("puzzles", "vazamento", em_surface(64, 56, lambda s: S.desenhar_reparo(s, (32, 40), False, 300)))
salvar("puzzles", "vazamento_consertado", em_surface(64, 56, lambda s: S.desenhar_reparo(s, (32, 40), True, 0)))
salvar("puzzles", "caixa", em_surface(55, 55, lambda s: S.desenhar_caixa(s, pygame.Rect(0, 0, 55, 55))))

# mapa
chao = pygame.Surface((160, 160)); S._pintar_chao(chao, (20, 22, 28), 1)
salvar("mapa", "chao", chao)
parede = pygame.Surface((160, 80)); S._pintar_parede(parede, pygame.Rect(0, 0, 160, 80))
salvar("mapa", "parede", parede)
salvar("mapa", "porta_fechada", em_surface(60, 100, lambda s: S.desenhar_porta(s, pygame.Rect(10, 10, 40, 80), False, 0)))
salvar("mapa", "porta_aberta", em_surface(60, 100, lambda s: S.desenhar_porta(s, pygame.Rect(10, 10, 40, 80), True, 0)))

# inimigos
for q in range(4):
    salvar("inimigos", f"vulto_{q + 1}", S._vulto_img(q).copy())
for uni, rotulo in (((58, 70, 108), "guarda_prisao"), ((96, 52, 52), "guarda_perseguidor")):
    for d in ("frente", "costas", "direita", "esquerda"):
        for passo in (0, 1):
            salvar("inimigos", f"{rotulo}_{d}_{passo + 1}", S._guarda_img(d, passo, uniforme=uni).copy())

# folha geral
cel, cols = 120, 10
linhas = (len(peças) + cols - 1) // cols
folha = pygame.Surface((cols * cel, linhas * cel + 0))
folha.fill((36, 38, 50))
for i, (nome, surf) in enumerate(peças):
    r = surf.get_rect()
    f = min(1.0, (cel - 24) / max(r.w, r.h))
    img = pygame.transform.scale(surf, (max(1, int(r.w * f)), max(1, int(r.h * f)))) if f < 1 else surf
    x, y = (i % cols) * cel, (i // cols) * cel
    folha.blit(img, img.get_rect(center=(x + cel // 2, y + cel // 2 - 6)))
    t = fonte.render(nome[:16], True, (170, 180, 200))
    folha.blit(t, t.get_rect(midbottom=(x + cel // 2, y + cel - 3)))
pygame.image.save(folha, os.path.join(base, "folha_geral.png"))
print(len(peças), "sprites exportadas em", base)
