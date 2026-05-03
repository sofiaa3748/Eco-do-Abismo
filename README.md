## 1. Título do Jogo: 
**O Eco do Abismo.** 

## 2. Descrição Geral: 
* **Tipo de Jogo:** Thriller Psicológico / Aventura Narrativa.
* **Ambiente:** Estação mineradora espacial.
* **Ideia principal:** O personagem deve passar pelos puzzels e escapar de onde ele está preso. 

## 3. Objetivo do Jogo
O que o jogador precisa fazer pra vencer: Atravessar as salas industriais e "hackear" painéis de rádio para abrir portas antes que o tempo ou a sanidade do personagem se esgotem.
Qual é a meta principal: Concluir a narrativa alcançando a porta final (o terraço do hospital). 

## 4. Personagem Principal
* **Qual é o personagem:** Operário 724.
* **Movimentação:** WASD ou Setas direcionais.
* **Atributos:**
  * **Velocidade:** Fixa e constante.
  * **Barra de Sanidade:** Representa a lucidez do personagem. Afeta a interface e o cenário dinamicamente.

## 5. Inimigos e Obstáculos
* **Câmeras de Segurança:** Sentinelas eletrônicas fixas com campo de visão cônico e movimento automático. Se detectado, o jogador retorna ao início da sala.
* **Portas Eletrônicas Trancadas:** Bloqueios que exigem a resolução de minijogos de ondas de rádio para prosseguir.
* **Colapso Mental:** Se a barra de sanidade chegar a 0%, o jogador desmaia e reinicia na sala atual.
* **Vazamento de Gás:** Tubulações rompidas que espalham gás pelo cenário. Enquanto o jogador não fechar a válvula correspondente, a barra de sanidade diminui de forma acelerada.

## 6. Cenário:
* **Tipo de ambiente do jogo:** Salas e corredores da mineradora espacial.
* **Elementos do mapa:** Paredes, dutos de ventilação, portas, painéis de controle, terraço. 
* **Onde ficam os itens e o objetivo final:**
  * **Itens:** Espalhados pelo mapa. 
  * **Objetivo final:** Chegar a porta final que dá acesso ao teraço do hospital. 

## 7. Sistema de Pontuação
* Não terá sistema de pontuação. 

## 8. Sistema de vida 
* **Substituição de Vida por Sanidade:** Não há sistema de vidas numéricas. O jogo é gerido pela Barra de Sanidade (inicia em 100%).
* **Consumo de Pílulas:** Ao usar a pílula para enxergar pistas da alucinação, a sanidade cai drasticamente.
* **Efeito do Gás:** Enquanto houver um vazamento ativo na sala, a sanidade do jogador é drenada continuamente. Quanto mais tempo ele demorar para fechar a válvula de gás, mais rápido a barra esvazia.
* **Checkpoints:** Ser detectado pelas câmeras ou ter a sanidade zerada faz o jogador reiniciar na entrada da sala em que se encontra.
* **O que acontece quando a sanidade acaba:** Ele enloquece e o volta da estaca zero.

## 9. Controles
* **Quais teclas serão usadas:** W, A, S, D, ou Setas direcionais, E e Esc.
* **A função de cada tecla:**
  * **Movimento:** W, A, S, D ou Setas direcionais.
  * **Interagir / Tomar a pílula:** E
  * **Pausar:** Esc

## 10. Fluxo do jogo
* **Como o jogo começa:** O jogador começa em uma cela escura e a "Voz" sussurra instruções para fuga. Ele toma a primeira pílula acreditando que ela fará bem para sua estabilidade.
* **O que acontece durante a partida:** O jogador atravessa salas alternando o uso de pílulas para resolver puzzles, desviar de câmeras e conter vazamentos de gás. Ele precisa gerenciar a queda drástica de sanidade que ocorre toda vez que o efeito da pílula passa.
* **Condições de vitória e derrota:** 
  * **Vitória:** Resolver os puzzels e passar pelas fases pra chegar no final. 
  * **Derrota:** Ter a Barra de Sanidade zerada por falta de pílulas ou inalação de gás, ou ser pego pelas câmeras de segurança, forçando o retorno ao início da sala atual.

## 11. Regras do Jogo:
* **Colisões:** Proibido atravessar paredes ou obstáculos sólidos do mapa.
* **Interações (Coleta e Objetos):** Para coletar frascos de pílula ou fechar válvulas de gás, o personagem deve estar próximo ao objeto e pressionar a tecla de interação (`E`).
* **Progresso Obrigatório:** Portas trancadas só abrem após a resolução do puzzle de rádio e a contenção do vazamento de gás.
* **Uso Estratégico da Pílula:** O jogador precisa calcular exatamente quando tomar a pílula para colher pistas rápidas, pois a queda acelerada de sanidade após o término do efeito exige rapidez para evitar o colapso mental.

## 12. Estrutura do Projeto
o-eco-do-abismo/
│
├── assets/                  # Arquivos de mídia
│   ├── sprites/             # Pixel art da estação, válvulas, frascos e hospital
│   ├── sound/               # Efeitos de gás, estática e sussurros
│   └── fonts/               # Fontes cursiva e de jornal
│
├── src/                     # Código-fonte do jogo
│   ├── main.py              # Loop principal do jogo
│   ├── player.py            # Movimentação e lógica de sanidade
│   ├── level.py             # Gerenciamento de mapa, colisões e gás
│   ├── puzzle.py            # Minijogo de ondas senoidais
│   ├── UI.py                # Sistema de diálogos e efeitos visuais
│   └── settings.py          # Configurações de resolução e FPS
│
├── README.md                # Documentação do projeto
└── requirements.txt         # Dependências (ex: pygame)

## 13. Funcionalidades Mínimas
* **Movimentação e Colisão:** Movimentação do personagem nas quatro direções com W, A, S, D impedindo que ele atravesse paredes ou objetos sólidos.
* **Ciclo de Sanidade e Itens:** Barra de sanidade na tela que diminui com o tempo. Sistema de inventário simples para coleta e uso dos frascos de pílulas com a tecla E.
* **Obstáculos Ativos:** Pelo menos uma área com vazamento de gás funcional que drena a sanidade mais rápido até que o jogador use a tecla E na válvula.
* Uma câmera de segurança funcional com área de detecção que reseta o personagem ao início da sala se detectado.
* **Condição de Progresso:** Uma porta trancada que exige a resolução do minijogo de rádio para ser aberta.

## 14. Melhorias Futuras
* Filtro de distorção visual (efeito CRT) que chia e treme com sanidade baixa.
* Sistema de iluminação dinâmica com sombras em tempo real.
* Dublagem em áudio para a "Voz".
