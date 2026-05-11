# ====================================================================
# AUTOCLIPPER versão 5.0.0 | MÓDULO DE GERAÇÃO E ESTILIZAÇÃO DE LEGENDAS
# ====================================================================
# Descrição: Este módulo recebe os arquivos JSON com os tempos exatos
# das palavras (gerados pelo WhisperX) e os converte para o formato
# Advanced SubStation Alpha (.ASS), aplicando estilos, fontes, cores
# e animações dinâmicas para vídeos verticais virais (Shorts/Reels).
# ====================================================================

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import json
import os
import random
from pathlib import Path 
import inspect

from banco_de_efeitos import EFEITOS_CRIATIVOS

# --- 1. RESOLUÇÃO DO DIRETÓRIO RAIZ (BASE_DIR) ---
try:
    CURRENT_DIR = Path(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
    BASE_DIR = CURRENT_DIR.parent 
except Exception:
    BASE_DIR = Path(os.getcwd())

# --- 2. CONSTANTES DE CAMINHOS ABSOLUTOS ---
PASTA_TEMP_GLOBAL = BASE_DIR / "temp"
PASTA_JSON = str(PASTA_TEMP_GLOBAL / "subs")
PASTA_SAIDA_ASS = str(PASTA_TEMP_GLOBAL / "subs_ass")

# --- 3. CONFIGURAÇÕES PADRÃO DE ESTILO VISUAL ---
COR_BASE = "&H00FFFFFF"        # Branco opaco
COR_DESTAQUE = "&H0000FFFF"    # Amarelo opaco
COR_CONTORNO = "&H00000000"    # Preto opaco
COR_SOMBRA = "&H80000000"      # Preto semitransparente
FONTE = "Montserrat SemiBold"
TAMANHO_BASE = 95
TAMANHO_DESTAQUE = 115
NEGRITO = -3


# ====================================================================
# REFERÊNCIAS: FONTES RECOMENDADAS PARA PROJETOS (OPEN-SOURCE)
# ====================================================================
# --- FONTES DE ALTO IMPACTO (Estilo "Viral") ---
# "Impact", "Anton Regular", "Bebas Neue Regular", "Arial Black"
#
# --- FONTES MODERNAS E LIMPAS (Estilo "Profissional") ---
# "Montserrat Black", "Poppins Black", "Roboto Black", "Bahnschrift"
#
# --- PRESETS DE TAMANHO POR NICHO (Guia Rápido) ---
# [1. Impacto Máximo]: FONTE="Anton Regular", TAM_BASE=127, TAM_DESTAQUE=177 (1/2 pal/bloco)
# [2. Moderno Artístico]: FONTE="Poppins Bold", TAM_BASE=107, TAM_DESTAQUE=127 (2 pal/bloco)
# [3. Profissional/Saúde]: FONTE="Montserrat SemiBold", TAM_BASE=95, TAM_DESTAQUE=115 (2/3 pal/bloco)
# ====================================================================


# ====================================================================
# FUNÇÕES UTILITÁRIAS E MATEMÁTICA DE TEMPO
# ====================================================================

def formatar_tempo_ass(segundos):
    """Converte segundos em ponto flutuante para o formato exigido pelo .ASS (H:MM:SS.cs)."""
    if segundos < 0: segundos = 0
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    cs = int((segundos % 1) * 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"

def gerar_string_de_efeitos(nome_do_efeito, alinhamento, margem_vertical):
    """Gera a string de tags de formatação SSA/ASS com base no menu selecionado."""
    # Lógica de Cálculo de Posição (Resolução Base: 1080x1920)
    pos_x = 540
    if alinhamento == 8:   # Superior
        pos_y = 270
    elif alinhamento == 5: # Meio
        pos_y = 960
    else:                  # Baixo (padrão, ideal para não cobrir o rosto)
        pos_y = 1530 

    pos_tag = f"{{\\an5\\pos({pos_x},{pos_y})}}"

    efeitos = {
        "padrao": "",
        "fade": f"{pos_tag}{{\\fad(250, 0)}}",
        "slide_baixo": f"{pos_tag}{{\\move({pos_x}, {pos_y+30}, {pos_x}, {pos_y}, 0, 250)\\fad(250, 0)}}",
        "slide_cima": f"{pos_tag}{{\\move({pos_x}, {pos_y-30}, {pos_x}, {pos_y}, 0, 250)\\fad(250, 0)}}",
        "slide_esquerda": f"{pos_tag}{{\\move({pos_x-30}, {pos_y}, {pos_x}, {pos_y}, 0, 250)\\fad(250, 0)}}",
        "slide_direita": f"{pos_tag}{{\\move({pos_x+30}, {pos_y}, {pos_x}, {pos_y}, 0, 250)\\fad(250, 0)}}",
        "pop": f"{pos_tag}{{\\t(0, 150, \\fscx100\\fscy100)\\fscx80\\fscy80}}",
        "revelacao": f"{pos_tag}{{\\fad(250, 0)\\t(0, 250, \\blur2\\alpha&HFF&, \\blur0\\alpha&H00&)}}",
        "pulso": f"{pos_tag}{{\\t(0, 300, \\fscx105\\fscy105, \\fscx100\\fscy100)}}",
        "flip_3d": f"{pos_tag}{{\\t(0, 300, \\fry-45, \\fry0)\\fad(250,0)}}", # Rotação no eixo Y
        "brilho": f"{pos_tag}{{\\t(0, 300, \\be1, \\be0)\\fad(250,0)}}"        # Blur suave nas bordas
    }

    return efeitos.get(nome_do_efeito, "")


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL: CRIAÇÃO DO ARQUIVO .ASS
# ====================================================================

def criar_legenda_ass(caminho_json, caminho_saida_ass, alinhamento, margem_vertical, palavras_por_bloco, efeito_animacao):
    """
    Lê o JSON de transcrição e constrói o arquivo .ASS final, aplicando
    cores de destaque palavra por palavra e organizando em blocos.
    """
    try:
        with open(caminho_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  AVISO: Não foi possível ler o arquivo JSON '{os.path.basename(caminho_json)}'. Pulando. Erro: {e}")
        return

    # Cabeçalho padrão do formato ASS (Advanced SubStation Alpha)
    header = f"""[Script Info]
Title: Legendas Geradas Automaticamente (AutoClipper)
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONTE},{TAMANHO_BASE},{COR_BASE},{COR_DESTAQUE},{COR_CONTORNO},{COR_SOMBRA},{NEGRITO},0,0,0,100,100,0,0,1,8.0,1.5,{alinhamento},40,40,{margem_vertical},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(caminho_saida_ass, 'w', encoding='utf-8-sig') as f:
        f.write(header)

        lista_de_efeitos = ["fade", "slide_baixo", "slide_cima", "slide_esquerda", "slide_direita", "pop", "revelacao", "pulso", "flip_3d", "brilho"]

        for segment in data.get('segments', []):
            words = segment.get('words', [])
            if not words: continue

            # Agrupa as palavras na tela de acordo com a escolha do usuário
            for i in range(0, len(words), palavras_por_bloco):
                bloco_palavras = words[i:i + palavras_por_bloco]

                efeito_a_ser_usado = efeito_animacao
                if efeito_animacao == "variado":
                    efeito_a_ser_usado = random.choice(lista_de_efeitos)

                # Cria o efeito de "KARAOKÊ" destacando a palavra atual
                for j, palavra_destacada in enumerate(bloco_palavras):
                    texto_completo = []
                    
                    for k, palavra_atual in enumerate(bloco_palavras):
                        palavra_limpa = palavra_atual.get('word', '').strip()
                        if not palavra_limpa: continue

                        if k == j:
                            # Aplica cor de destaque na palavra atual
                            texto_completo.append(f"{{\\c{COR_DESTAQUE}\\fs{TAMANHO_DESTAQUE}}}{palavra_limpa}{{\\c{COR_BASE}\\fs{TAMANHO_BASE}}}")
                        else:
                            texto_completo.append(palavra_limpa)

                    texto_linha = " ".join(texto_completo)
                    inicio = formatar_tempo_ass(palavra_destacada['start'])
                    fim = formatar_tempo_ass(palavra_destacada['end'])

                    # --- CAMINHO LÓGICO PARA APLICAÇÃO DE EFEITOS ---
                    linha_final = ""
                    if efeito_animacao == "variado":
                        # Puxa do script 'banco_de_efeitos' ignorando o menu principal
                        efeito_sorteado = random.choice(EFEITOS_CRIATIVOS)
                        linha_final = f"{efeito_sorteado}{texto_linha}"
                    else:
                        efeitos_str = gerar_string_de_efeitos(efeito_animacao, alinhamento, margem_vertical)
                        linha_final = f"{efeitos_str}{texto_linha}"

                    f.write(f"Dialogue: 0,{inicio},{fim},Default,,0,0,0,,{linha_final}\n")

    print(f"  -> Legenda .ASS com efeito '{efeito_animacao}' gerada: {os.path.basename(caminho_saida_ass)}")


# ====================================================================
# WORKER PRINCIPAL DE ORQUESTRAÇÃO
# ====================================================================

def main(alinhamento, margem_vertical, palavras_por_bloco, efeito_animacao="padrao", specific_file=None):
    """
    Função principal chamada pelo orquestrador.
    Itera sobre a pasta de JSONs e converte todos (ou um específico) para .ASS.
    """
    os.makedirs(PASTA_SAIDA_ASS, exist_ok=True)
    if not os.path.isdir(PASTA_JSON) or not os.listdir(PASTA_JSON):
        print(f"AVISO: A pasta '{PASTA_JSON}' está vazia ou não existe. Nada a fazer.")
        return

    print("\nIniciando a estilização final das legendas...")

    arquivos_a_processar = []
    if specific_file:
        json_filename = f"{specific_file}.json"
        if os.path.exists(os.path.join(PASTA_JSON, json_filename)):
            arquivos_a_processar.append(json_filename)
        else:
            print(f"AVISO: Arquivo JSON '{json_filename}' não encontrado.")
    else:
        arquivos_a_processar = [f for f in os.listdir(PASTA_JSON) if f.endswith(".json")]

    for filename in arquivos_a_processar:
        caminho_json = os.path.join(PASTA_JSON, filename)
        nome_base = os.path.splitext(filename)[0]
        caminho_saida_ass = os.path.join(PASTA_SAIDA_ASS, f"{nome_base}.ass")

        criar_legenda_ass(caminho_json, caminho_saida_ass, alinhamento, margem_vertical, palavras_por_bloco, efeito_animacao)

    print("\nEstilização concluída!")