# ====================================================================
# AUTOCLIPPER versão 5.0.0 | MÓDULO DE QUEIMA DE LEGENDAS (HARDCODE)
# ====================================================================
# Descrição: Este script utiliza o FFmpeg para "queimar" (hardcode)
# as legendas estilizadas (.ass) diretamente nos frames do vídeo.
# Isso garante que as legendas funcionem nativamente e sem falhas em
# qualquer plataforma (Instagram Reels, TikTok, YouTube Shorts).
# ====================================================================

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
import subprocess
from pathlib import Path 
import inspect

# --- 1. RESOLUÇÃO DO DIRETÓRIO RAIZ (BASE_DIR) ---
try:
    CURRENT_DIR = Path(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
    BASE_DIR = CURRENT_DIR.parent 
except Exception:
    BASE_DIR = Path(os.getcwd())

# --- 2. CONSTANTES DE CAMINHOS ABSOLUTOS ---
PASTA_VIDEOS_PADRAO = str(BASE_DIR / "temp" / "final")
PASTA_LEGENDAS_ASS = str(BASE_DIR / "temp" / "subs_ass")
PASTA_SAIDA_PADRAO = str(BASE_DIR / "burned_sub")

# --- 3. CONFIGURAÇÕES DE ENCODE DE VÍDEO ---
ENCODER = 'libx264'
BITRATE_VIDEO = '6M'  # Mantém a qualidade alta para redes sociais
PRESET = 'fast'       # Equilíbrio ideal entre velocidade e compressão final


# ====================================================================
# FUNÇÕES UTILITÁRIAS / WORKERS
# ====================================================================

def queimar_legenda(caminho_video, caminho_legenda, caminho_saida):
    """
    Executa o comando FFmpeg para embutir a legenda no vídeo.
    Trata caminhos absolutos e escapa caracteres especiais do Windows
    para evitar erros de sintaxe no filtro de vídeo (vf).
    """
    # É fundamental escapar barras e dois-pontos para o FFmpeg no Windows
    caminho_legenda_ffmpeg = caminho_legenda.replace('\\', '/').replace(':', '\\:')
    filtro_vf = f"subtitles='{caminho_legenda_ffmpeg}'"

    # Redireciona a saída do FFmpeg para manter o console limpo
    with open(os.devnull, 'w') as devnull:
        try:
            command = [
                'ffmpeg', 
                '-i', str(caminho_video), 
                '-vf', filtro_vf, 
                '-c:v', ENCODER, 
                '-preset', PRESET, 
                '-b:v', BITRATE_VIDEO, 
                '-c:a', 'copy', # Copia o áudio sem re-encodar (rápido e sem perda)
                '-y', str(caminho_saida) 
            ]
            
            subprocess.run(command, check=True, stdout=devnull, stderr=devnull)
            print(f"  -> Vídeo renderizado com sucesso: '{os.path.basename(caminho_saida)}'")
            return True
            
        except subprocess.CalledProcessError:
            print(f"  ERRO ao processar o vídeo {os.path.basename(caminho_video)}. FFmpeg falhou.")
            return False


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL (ORQUESTRAÇÃO)
# ====================================================================

def main(pasta_videos_fonte=PASTA_VIDEOS_PADRAO, specific_file=None, sufixo_saida=None, pasta_destino_final=None):
    """
    Função principal acessada pelo orquestrador.
    Verifica as pastas, cruza os vídeos com os arquivos .ass correspondentes
    e aciona o worker de renderização do FFmpeg.
    """
    
    # Define a pasta de destino (padrão ou fornecida pelo orquestrador)
    pasta_saida_resolvida = str(pasta_destino_final) if pasta_destino_final else PASTA_SAIDA_PADRAO
    os.makedirs(pasta_saida_resolvida, exist_ok=True)
    arquivos_gerados = []
    
    # --- Verificação de Segurança Inicial ---
    if not os.path.isdir(pasta_videos_fonte) or not os.listdir(pasta_videos_fonte):
        print(f"AVISO: A pasta de vídeos fonte '{pasta_videos_fonte}' está vazia ou não existe.")
        return arquivos_gerados
        
    if not os.path.isdir(PASTA_LEGENDAS_ASS) or not os.listdir(PASTA_LEGENDAS_ASS):
        print(f"AVISO: A pasta de legendas '{PASTA_LEGENDAS_ASS}' está vazia ou não existe.")
        return arquivos_gerados
        
    print("\nIniciando o processo de 'queima' das legendas finais...")

    # --- Determinação dos Vídeos a Processar ---
    videos_a_processar = []
    
    if specific_file:
        # Modo unitário/ajuste
        found = False
        for ext in ['.mp4', '.mov', '.mkv', '.avi']:
            video_filename_test = f"{specific_file}{ext}"
            if os.path.exists(os.path.join(pasta_videos_fonte, video_filename_test)):
                videos_a_processar.append(video_filename_test)
                found = True
                break
        if not found:
            print(f"ERRO: O arquivo base '{specific_file}' não foi encontrado em {pasta_videos_fonte}/")
            return arquivos_gerados
    else:
        # Modo em lote/completo
        videos_a_processar = [f for f in os.listdir(pasta_videos_fonte) if f.lower().endswith(('.mp4', '.mov', '.mkv', '.avi'))]

    # --- Loop de Processamento e Renderização ---
    for filename in videos_a_processar:
        nome_base = os.path.splitext(filename)[0]
        caminho_video = os.path.join(pasta_videos_fonte, filename)
        caminho_legenda = os.path.join(PASTA_LEGENDAS_ASS, f"{nome_base}.ass")
        
        # Ajusta o nome final se o modo monetização foi ativado no orquestrador
        nome_final = f"{nome_base}{sufixo_saida}.mp4" if sufixo_saida else f"{nome_base}_legendado.mp4"
        caminho_saida = os.path.join(pasta_saida_resolvida, nome_final)

        if os.path.exists(caminho_legenda):
            sucesso = queimar_legenda(caminho_video, caminho_legenda, caminho_saida)
            if sucesso:
                arquivos_gerados.append(caminho_saida)
        else:
            print(f"  AVISO: O arquivo '{nome_base}.ass' não foi encontrado. O vídeo '{filename}' foi pulado.")
    
    print("\nProcesso de renderização das legendas finalizado!")
    return arquivos_gerados