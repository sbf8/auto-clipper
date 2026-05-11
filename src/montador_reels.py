# ====================================================================
# AUTOCLIPPER versão 5.0.0 | MÓDULO MONTADOR DE SUPER REELS
# ====================================================================
# Descrição: Este script analisa os clipes gerados, extrai a "essência"
# (o trecho de maior impacto/volume sonoro usando Librosa) de cada um 
# e os concatena em um único "Super Reels" altamente engajador, 
# otimizado para o formato vertical.
# ====================================================================

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import os
import subprocess
import librosa
import numpy as np
from pathlib import Path 
import inspect

# --- 1. RESOLUÇÃO DO DIRETÓRIO RAIZ (BASE_DIR) ---
try:
    CURRENT_DIR = Path(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
    BASE_DIR = CURRENT_DIR.parent 
except Exception:
    BASE_DIR = Path(os.getcwd())

# --- 2. CONSTANTES DE CAMINHOS ABSOLUTOS ---
PASTA_CLIPS_TEMPORARIA = str(BASE_DIR / "temp" / "final") # A fonte dos clipes
PASTA_FINAL_EXPORT = str(BASE_DIR / "burned_sub")         # O destino do Super Reels

# --- 3. CONFIGURAÇÕES DO ALGORITMO ---
# Duração, em segundos, da "essência" que vamos extrair de cada clipe.
DURACAO_ESSENCIA = 5.0 


# ====================================================================
# FUNÇÕES UTILITÁRIAS / ANÁLISE DE ÁUDIO
# ====================================================================

def _encontrar_ponto_de_ouro(caminho_video):
    """
    Escaneia a trilha de áudio do clipe usando a biblioteca Librosa 
    para encontrar o frame com a maior energia RMS (pico de volume).
    Retorna o tempo de início ideal para o corte da essência.
    """
    try:
        y, sr = librosa.load(caminho_video, sr=None)
        rms = librosa.feature.rms(y=y)[0]
        pico_frame = np.argmax(rms)
        pico_tempo = librosa.frames_to_time(pico_frame, sr=sr)

        # Tenta centralizar o corte no pico de volume encontrado
        inicio_corte = max(0, pico_tempo - (DURACAO_ESSENCIA / 2))
        duracao_video = librosa.get_duration(y=y, sr=sr)
        
        # Se o clipe for menor que a essência exigida, usa o clipe na íntegra
        if duracao_video < DURACAO_ESSENCIA:
             print(f"  -> AVISO: Clipe '{os.path.basename(caminho_video)}' é curto. Usando na íntegra.")
             return 0.0, duracao_video

        # Ajusta o corte final para não estourar o limite temporal do vídeo
        if inicio_corte + DURACAO_ESSENCIA > duracao_video:
            inicio_corte = duracao_video - DURACAO_ESSENCIA
            
        return inicio_corte, DURACAO_ESSENCIA
        
    except Exception as e:
        print(f"  -> AVISO: Falha ao analisar áudio de {os.path.basename(caminho_video)}. Usando o início. Erro: {e}")
        return 0.0, DURACAO_ESSENCIA


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL: CONCATENAÇÃO (SUPER CUT)
# ====================================================================

def montar_supercut(num_top_clips, duracao_maxima, pasta_final=PASTA_CLIPS_TEMPORARIA, pasta_saida=PASTA_FINAL_EXPORT):
    """
    Seleciona os melhores clipes recentes, extrai os "pontos de ouro" 
    e constrói um comando FFmpeg com 'filter_complex' para concatenar 
    tudo em um único render rápido e fluido.
    """
    print("\n--- Iniciando a criação do Super Reels ---")
    
    # --- 1. Validação do Diretório ---
    if not os.path.isdir(pasta_final) or not os.listdir(pasta_final):
        print(f"ERRO: A pasta '{pasta_final}' está vazia. Não há clipes fonte para montar.")
        return

    # Coleta os vídeos mais recentes gerados na sessão
    todos_os_clipes = sorted([os.path.join(pasta_final, f) for f in os.listdir(pasta_final) if f.lower().endswith('.mp4')], reverse=True)
    clipes_selecionados = todos_os_clipes[:num_top_clips]

    if not clipes_selecionados:
        print("ERRO: Nenhum vídeo .mp4 encontrado na pasta de origem.")
        return

    # --- 2. Extração dos Pontos de Ouro ---
    micro_cortes_info = []
    duracao_total = 0
    print(f"  -> Escaneando {len(clipes_selecionados)} clipes para extrair a 'essência' magnética...")
    
    for caminho_video in clipes_selecionados:
        inicio_essencia, duracao_essencia = _encontrar_ponto_de_ouro(caminho_video)
        
        # Interrompe se o Super Reels atingiu o tempo máximo estipulado
        if (duracao_total + duracao_essencia) > duracao_maxima and micro_cortes_info:
            break

        if os.path.exists(caminho_video):
            micro_cortes_info.append({
                "path": caminho_video, "start": inicio_essencia, "duration": duracao_essencia
            })
            duracao_total += duracao_essencia

    if not micro_cortes_info:
        print("AVISO: Nenhum clipe válido capturado para o Super Reels.")
        return
        
    print(f"  -> {len(micro_cortes_info)} essências capturadas. Renderizando o vídeo final...")
    
    # --- 3. Construção do Comando FFmpeg (Filter Complex) ---
    inputs_ffmpeg = []
    filtro_preparacao = ""
    
    for i, mc in enumerate(micro_cortes_info):
        inputs_ffmpeg.extend(['-i', mc['path']])
        end_time = mc['start'] + mc['duration']
        
        # Prepara a timeline de Vídeo: Trim, Reseta PTS, Escala (1080x1920), Ajusta SAR e FPS
        filtro_preparacao += f"[{i}:v]trim={mc['start']}:{end_time},setpts=PTS-STARTPTS,scale=1080:1920,setsar=1,fps=30,format=yuv420p[v{i}];"
        # Prepara a timeline de Áudio: Trim e Reseta PTS
        filtro_preparacao += f"[{i}:a]atrim={mc['start']}:{end_time},asetpts=PTS-STARTPTS[a{i}];"

    # Junta as streams processadas no comando 'concat'
    filtro_concatenacao = ""
    for i in range(len(micro_cortes_info)):
        filtro_concatenacao += f"[v{i}][a{i}]"
    filtro_concatenacao += f"concat=n={len(micro_cortes_info)}:v=1:a=1[outv][outa]"

    filtro_final = filtro_preparacao + filtro_concatenacao

    # --- 4. Renderização Final ---
    os.makedirs(pasta_saida, exist_ok=True)

    # Cria o nome final baseando-se no primeiro clipe da lista
    nome_base_sem_data = os.path.splitext(os.path.basename(clipes_selecionados[0]))[0].rsplit('_', 2)[0]
    output_filename = os.path.join(pasta_saida, f"SUPER_REELS_{nome_base_sem_data}.mp4")
    
    command = ['ffmpeg', '-y'] + inputs_ffmpeg + [
        '-filter_complex', filtro_final,
        '-map', '[outv]', '-map', '[outa]',
        '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '192k',
        '-movflags', 'faststart', output_filename
    ]
    
    try:
        # Captura de erros habilitada (stderr=subprocess.PIPE) para facilitar o debug
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print(f"\n[+] SUPER REELS criado com sucesso!\nSalvo em: {os.path.basename(output_filename)}")
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode('utf-8', errors='ignore') if e.stderr else "Sem detalhes adicionais."
        print(f"\nERRO CRÍTICO: FFmpeg falhou ao criar o Super Reels.\nDetalhes técnicos:\n{error_output}")