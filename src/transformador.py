# ====================================================================
# AUTOCLIPPER versão 5.0.0 | MÓDULO DE TRANSFORMAÇÃO E MONETIZAÇÃO
# ====================================================================
# Descrição: Este script aplica transformações visuais e de áudio aos
# clipes gerados. O objetivo é criar variações únicas de vídeos
# (color grading, espelhamento, pitch shift, etc.) para evitar
# bloqueios de conteúdo duplicado em plataformas de monetização.
# ====================================================================

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import subprocess
import random
import os
import cv2
import re
from pathlib import Path 
import inspect

# --- 1. RESOLUÇÃO DO DIRETÓRIO RAIZ (BASE_DIR) ---
try:
    CURRENT_DIR = Path(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
    BASE_DIR = CURRENT_DIR.parent 
except Exception:
    BASE_DIR = Path(os.getcwd())

# --- 2. CONSTANTES DE CAMINHOS ABSOLUTOS ---
PASTA_TEMP = str(BASE_DIR / "temp")
PASTA_LUTS = str(BASE_DIR / "luts")


# ====================================================================
# FUNÇÕES UTILITÁRIAS / AUXILIARES
# ====================================================================

def _obter_duracao_video(caminho_video):
    """
    Lê a duração exata de um vídeo usando OpenCV.
    Isso é crucial para calcular a taxa de incremento de filtros contínuos, como o zoom.
    """
    try:
        cap = cv2.VideoCapture(caminho_video)
        if not cap.isOpened(): 
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        # Evita divisão por zero caso os metadados do vídeo estejam corrompidos
        if fps is None or fps == 0: 
            fps = 30.0
            
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        cap.release()
        
        return duration
    except Exception:
        return None


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL: PIPELINE DE TRANSFORMAÇÃO
# ====================================================================

def aplicar_transformacoes(caminho_entrada, caminho_saida, transformacoes):
    """
    Aplica uma cadeia de filtros (vídeo e áudio) para tornar o clipe único.
    A execução é dividida em etapas sequenciais (arquivos temporários) para evitar 
    conflitos de codec e complexidade excessiva num único comando FFmpeg.
    """
    print(f"  -> Transformando clipe (Monetização): {os.path.basename(caminho_entrada)}")

    lut_usado = None 

    # Se nenhuma transformação foi selecionada, encerra cedo
    if not any(v for v in transformacoes.values() if v):
        return lut_usado

    os.makedirs(PASTA_TEMP, exist_ok=True)
    nome_base_temp = os.path.splitext(os.path.basename(caminho_entrada))[0]

    temp_files = []
    current_input = caminho_entrada

    try:
        # --- ETAPA 1: Filtros Visuais Simples (Cor, Vinheta, Granulação, LUTs) ---
        filtros_simples = []
        
        if transformacoes.get('espelhar'): 
            filtros_simples.append("hflip")
            
        if transformacoes.get('cores'):
            contraste = f"{random.uniform(1.05, 1.2):.2f}"
            saturacao = f"{random.uniform(1.05, 1.25):.2f}"
            brilho = f"{random.uniform(-0.05, 0.05):.2f}"
            filtros_simples.append(f"eq=contrast={contraste}:saturation={saturacao}:brightness={brilho}")
            
        if transformacoes.get('vinheta'): 
            filtros_simples.append("vignette")
            
        if transformacoes.get('granulacao'): 
            filtros_simples.append("noise=alls=3:allf=t+u")
            
        if transformacoes.get('luts'):
            if os.path.isdir(PASTA_LUTS) and os.listdir(PASTA_LUTS):
                cube_files = [f for f in os.listdir(PASTA_LUTS) if f.lower().endswith('.cube')]
                if cube_files:
                    lut_usado = random.choice(cube_files)
                    caminho_lut = os.path.join(PASTA_LUTS, lut_usado).replace('\\', '/')
                    # Escapa a letra do drive (ex: C:/) no Windows para o FFmpeg entender o caminho do LUT
                    caminho_lut = re.sub(r'([a-zA-Z]):', r'\1\\:', caminho_lut) 
                    print(f"    -> Aplicando Color Grading (LUT): {lut_usado}")
                    filtros_simples.append(f"lut3d=file='{caminho_lut}'")

        if filtros_simples:
            print("    -> Etapa 1/4: Aplicando filtros visuais e color grading...")
            temp_output = os.path.join(PASTA_TEMP, f"{nome_base_temp}_temp1.mp4")
            temp_files.append(temp_output)
            
            command = [
                'ffmpeg', '-y', '-i', current_input, 
                '-vf', ",".join(filtros_simples),
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', 
                '-c:a', 'copy', temp_output
            ]
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            current_input = temp_output

        # --- ETAPA 2: Manipulação de Velocidade e Áudio (Pitch Shift) ---
        if transformacoes.get('velocidade') or transformacoes.get('pitch_shift'):
            print("    -> Etapa 2/4: Ajustando frequência de áudio e velocidade temporal...")
            filtros_audio = []
            
            if transformacoes.get('velocidade'): 
                filtros_audio.append("atempo=1.05")
                
            if transformacoes.get('pitch_shift'):
                taxa_amostra_original = 44100
                nova_taxa_amostra = int(taxa_amostra_original * 1.015)
                filtros_audio.append(f"asetrate={nova_taxa_amostra},aresample={taxa_amostra_original}")

            temp_output = os.path.join(PASTA_TEMP, f"{nome_base_temp}_temp2.mp4")
            temp_files.append(temp_output)

            command = ['ffmpeg', '-y', '-i', current_input]
            
            if transformacoes.get('velocidade'):
                command.extend(['-filter:v', f"setpts={1/1.05:.3f}*PTS"])
                command.extend(['-c:v', 'libx264', '-preset', 'fast', '-crf', '23'])
            else: 
                # Se alterou apenas o áudio, não precisa recodificar o vídeo inteiro
                command.extend(['-c:v', 'copy'])

            command.extend(['-af', ",".join(filtros_audio), '-c:a', 'aac', '-b:a', '192k', temp_output])
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            current_input = temp_output

        # --- ETAPA 3: Movimento de Câmera (Zoom Lento) ---
        if transformacoes.get('zoom_lento'):
            print("    -> Etapa 3/4: Criando movimento de câmera (Zoom contínuo)...")
            duracao = _obter_duracao_video(current_input)

            if duracao and duracao > 0:
                z_final = 1.15
                incremento_zoom = (z_final - 1.0) / (duracao * 30)
                zoom_filter = f"zoompan=z='min(max(zoom,pzoom)+{incremento_zoom:.6f},{z_final})':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"
                
                temp_output = os.path.join(PASTA_TEMP, f"{nome_base_temp}_temp3.mp4")
                temp_files.append(temp_output)
                
                command = [
                    'ffmpeg', '-y', '-i', current_input, 
                    '-vf', zoom_filter,
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23', 
                    '-c:a', 'copy', temp_output
                ]
                subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                current_input = temp_output

        # --- ETAPA 4: Passe Final de Compressão e Compatibilidade ---
        print("    -> Etapa 4/4: Renderização final e adequação de formato (yuv420p)...")
        command_final = [
            'ffmpeg', '-y', '-i', current_input,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'copy', '-pix_fmt', 'yuv420p', caminho_saida
        ]
        subprocess.run(command_final, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        return lut_usado

    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode('utf-8', errors='ignore') if e.stderr else "Nenhuma saída de erro capturada pelo FFmpeg."
        print(f"  ERRO CRÍTICO ao transformar {os.path.basename(caminho_entrada)}.\nDetalhes do erro FFmpeg:\n{error_output}")
    finally:
        # --- LIMPEZA DE TEMPORÁRIOS ---
        # Remove os arquivos intermediários (temp1, temp2, temp3) para não estourar o disco
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass