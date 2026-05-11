# ====================================================================
# AUTOCLIPPER versão 5.0.0 | BANCO DE EFEITOS VISUAIS (.ASS)
# ====================================================================
# Descrição: Biblioteca estática contendo as tags de formatação do
# formato Advanced SubStation Alpha (.ass). Estas strings injetam
# animações matemáticas de alta complexidade no texto, alimentando
# o "Modo Criativo" (Variação Automática) do AutoClipper.
#
# Nota Arquitetural: Neste modo, a posição é ancorada rigorosamente 
# no centro absoluto da tela vertical (540, 960). Isso impede que 
# efeitos de distorção e rotação 3D saiam dos limites do enquadramento.
# ====================================================================

EFEITOS_CRIATIVOS = [
    # --- 1. EFEITOS DE FADE E REVELAÇÃO CINEMATOGRÁFICA ---
    "{\\an5\\pos(540,960)\\fad(300, 200)}", 
    "{\\an5\\pos(540,960)\\fad(250, 0)\\t(0, 250, \\blur2\\alpha&HFF&, \\blur0\\alpha&H00&)}", # Foco dinâmico
    "{\\an5\\pos(540,960)\\t(0, 400, \\be1, \\be0)\\fad(250,0)}", # Brilho mágico (Glow)

    # --- 2. EFEITOS DE DESLOCAMENTO DINÂMICO (SLIDES) ---
    "{\\an5\\pos(540,960)\\move(540, 1000, 540, 960, 0, 300)\\fad(300, 0)}", # Slide ascendente
    "{\\an5\\pos(540,960)\\move(480, 960, 540, 960, 0, 300)\\fad(300, 0)}",  # Entrada pela esquerda
    "{\\an5\\pos(540,960)\\move(540, 920, 540, 960, 0, 300)\\fad(300, 0)}",  # Slide descendente
    "{\\an5\\pos(540,960)\\move(600, 960, 540, 960, 0, 300)\\fad(300, 0)}",  # Entrada pela direita
    "{\\an5\\pos(540,960)\\move(480, 1000, 540, 960, 0, 300)\\fad(300, 0)}", # Entrada diagonal inferior

    # --- 3. EFEITOS DE ESCALA E RETENÇÃO (ZOOM E POP) ---
    "{\\an5\\pos(540,960)\\t(0, 200, \\fscx100\\fscy100)\\fscx80\\fscy80}",            # Pop Seco (Estilo TikTok)
    "{\\an5\\pos(540,960)\\t(0, 300, \\fscx105\\fscy105, \\fscx100\\fscy100)}",        # Pulso sutil contínuo
    "{\\an5\\pos(540,960)\\t(0, 400, \\fscx110\\fscy110, \\fscx100\\fscy100)}",        # Bounce / Quicada
    "{\\an5\\pos(540,960)\\t(0, 300, \\fscx50\\fscy50\\alpha&HAA&, \\fscx100\\fscy100\\alpha&H00&)}", # Zoom in translúcido

    # --- 4. EFEITOS DE ROTAÇÃO E PERSPECTIVA 3D ---
    "{\\an5\\pos(540,960)\\t(0, 300, \\fry-60, \\fry0)\\fad(250,0)}", # Flip Horizontal (Efeito virar página)
    "{\\an5\\pos(540,960)\\t(0, 300, \\frx45, \\frx0)\\fad(250,0)}",  # Flip Vertical (Efeito levantar painel)
    "{\\an5\\pos(540,960)\\t(0, 300, \\frz-15, \\frz0)\\fad(250,0)}", # Rotação de Eixo Z (Balanço de ponteiro)
    
    # --- 5. EFEITOS DE DISTORÇÃO TENSORIAL (SHEAR) ---
    "{\\an5\\pos(540,960)\\t(0, 250, \\fax0.3, \\fax0)\\fad(250,0)}",  # Correção de inclinação no eixo X
    "{\\an5\\pos(540,960)\\t(0, 250, \\fay-0.3, \\fay0)\\fad(250,0)}", # Correção de inclinação no eixo Y
]