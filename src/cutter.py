# ====================================================================
# AUTOCLIPPER versão 5.0.0 | MÓDULO DE CORTE E DOWNLOAD (CUTTER)
# ====================================================================
# Descrição: Este módulo é responsável por baixar vídeos do YouTube,
# extrair o áudio, realizar uma transcrição rápida para encontrar
# momentos de alta retenção (usando palavras-chave ou picos de emoção)
# e fatiar o vídeo original em clipes verticais prontos para as redes.
# ====================================================================

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
from pathlib import Path 
import inspect
import re
from datetime import datetime
import subprocess
import json
import sys
import traceback

from yt_dlp.utils import DownloadError
import yt_dlp
import whisper # Usado aqui para transcrição base ultrarrápida de marcação

# --- 1. RESOLUÇÃO DO DIRETÓRIO RAIZ (BASE_DIR) ---
try:
    CURRENT_DIR = Path(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
    BASE_DIR = CURRENT_DIR.parent 
except Exception:
    BASE_DIR = Path(os.getcwd())
    
# --- 2. CONSTANTES DE CAMINHOS ABSOLUTOS ---
PASTA_TEMP = str(BASE_DIR / "temp")
LOGS_FOLDER = str(BASE_DIR / "logs")
YOUTUBE_FOLDER = str(BASE_DIR / "temp" / "youtube_original")
CLIPS_FOLDER = str(BASE_DIR / "temp" / "final")
error_log_file = str(BASE_DIR / "logs" / "error_log.txt")

# --- 3. DICIONÁRIO DE PALAVRAS DE ALTA RETENÇÃO (POWER WORDS) ---
POWER_WORDS = [
    'chocante', 'inacreditável', 'verdade', 'segredo', 'perigoso', 'exclusivo', 'único',
    'porquê', 'real', 'autêntico', 'erro', 'nunca', 'jamais', 'sempre', 'precisa',
    'agora', 'o que', 'como', 'sem', 'dicas', 'viagem', 'país', 'cidade', 'lugar',
    'aventura', 'raiz', 'turismo', 'barato', 'preço', 'história', "what's", 'this',
    'loucura', 'isso', 'much', 'roteiro', 'vocês', 'massagem', 'coconout', 'coco',
    'massage', 'cheguei', 'bem-vindos', 'diretamente', 'golpe', 'gente', 'descobri',
    'encontrei', 'incrível', 'surpreendente', 'diferente', 'igual', 'não', 'só', 'André', 
    'meus amigos', 'o roteiro se cria', 'só vamos','final feliz', 'neymar', 'futebol', 'brasil', 'brazil',
    'alerta', 'ansiedade', 'aprender', 'aqui', 'atenção', 'cérebro',
    'conhecimento', 'controle', 'dica', 'entenda', 'essencial',
    'futuro', 'ganchos', 'hábito', 'incômodo', 'lição', 'mental',
    'minuto', 'mudança', 'passado', 'pensamentos', 'por que', 'problema',
    'programação', 'produtividade', 'saúde', 'simples', 'solução',
    'tecnologia', 'você', 'impressionante', 'consegue', 'poder', 'melhor', 
    'pior', 'mais', 'menos', 'se', 'porém', 'então', 'primeiro', 'segundo', 
    'terceiro', 'finalmente', 'depois', 'antes', 'mas'
]

# Configurações padrão de exportação do FFmpeg
codec_video = "libx264"
crf_qualidade = "23"
preset_velocidade = "medium"
bitrate_audio = "192k"


# ====================================================================
# FUNÇÕES UTILITÁRIAS E AUXILIARES
# ====================================================================

def log_error(message):
    """Registra erros operacionais do Cutter no arquivo central de logs."""
    os.makedirs(LOGS_FOLDER, exist_ok=True)
    with open(error_log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] ERROR: {message}\n")
        f.write(traceback.format_exc())
        f.write("\n" + "="*50 + "\n")

def format_filename(title, index):
    """Limpa o título do vídeo para criar nomes de arquivos seguros para o OS."""
    title = re.sub(r'[\u0300-\u036f]', '', title, flags=re.UNICODE)
    title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    title = title.replace(" ", "_").upper()
    timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
    return f"{title}_{index:03d}_{timestamp}.mp4"

def score_segment(text):
    """Calcula a pontuação de "viralidade" de um trecho com base nas Power Words."""
    score = 0
    text_lower = text.lower()
    for word in POWER_WORDS:
        score += text_lower.count(word) * 2
    if '?' in text:
        score += 5
    score += len(text.split()) / 10.0
    return score

def get_original_video_name(formatted_name):
    """Reverte o nome formatado do arquivo para extrair o título original aproximado."""
    match = re.match(r'^(.*)_\d{3}_\d{8}_\d{6}$', formatted_name)
    if match:
        original_name = match.group(1).replace('_', ' ')
        return original_name.title()
    return formatted_name

def _run_ffmpeg_with_progress(command, output_filename):
    """Executa comandos complexos do FFmpeg exibindo uma barra de progresso em linha única."""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
    line_buffer = ""
    
    while True:
        char = process.stderr.read(1)
        if char == '' and process.poll() is not None: break
        
        if char:
            line_buffer += char
            if char == '\r':
                if 'frame=' in line_buffer:
                    print(f"   -> Processando: {line_buffer.strip()}", end='')
                line_buffer = "" 

    print() 
    if process.returncode == 0:
        print(f"   -> Clipe criado com sucesso: {output_filename}")
    else:
        print(f"\n   -> ERRO ao criar o clipe {output_filename}.")


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL (DOWNLOAD E PROCESSAMENTO)
# ====================================================================

def download_video(url, output_folder):
    """Baixa o vídeo com a melhor qualidade possível (até 1080p) usando yt-dlp."""
    print(f"\n--- [FASE 1/4] Baixando o Vídeo em HD ---")
    os.makedirs(output_folder, exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo[height>=720][height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>=720][height<=1080]+bestaudio/best[height>=720][height<=1080]',
        'outtmpl': os.path.join(output_folder, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            video_title = info.get('title', 'video_sem_titulo')
            print(f"Vídeo baixado e salvo em: {filename}")
            return filename, video_title
    except DownloadError:
        print("\n" + "!"*60)
        print("  AVISO: Não foi possível baixar o vídeo em qualidade HD ou 720p.")
        print("  Isso pode ser um problema temporário do YouTube ou indisponibilidade da qualidade.")
        print("!"*60)
        return None, None 

def get_video_title(url):
    """Extrai apenas os metadados (título) do vídeo sem realizar o download."""
    ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', None)
    except Exception as e:
        print(f"ERRO: Não foi possível obter informações da URL fornecida. Detalhes: {e}")
        return None

def extract_audio(video_path, audio_output_path):
    """Separa a faixa de áudio do vídeo original para transcrição rápida."""
    print(f"   -> Extraindo áudio de: {os.path.basename(video_path)}")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
            "-ar", "44100", "-ac", "2", audio_output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   -> Áudio extraído com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"ERRO: FFmpeg falhou ao extrair o áudio. Verifique sua instalação. Erro: {e}")
        raise

def transcribe_audio_for_cuts(filepath):
    """Usa o modelo Whisper base (rápido) para gerar timestamps para análise de corte."""
    print("\n--- [FASE 2/4] Transcrevendo para Encontrar os Cortes (Modo Rápido) ---")
    model = whisper.load_model("base")
    result = model.transcribe(filepath, word_timestamps=True)
    print("Transcrição para cortes concluída com sucesso.")
    return result

def find_viral_segments(transcription, num_clips, min_duration, max_duration):
    """Varre a transcrição em busca de blocos de texto com alta densidade de Power Words."""
    print("\n--- [FASE 3/4] Analisando e Pontuando os Segmentos (Modo Palavras-Chave) ---")
    potential_clips = []
    segments = transcription['segments']
    
    for i in range(len(segments)):
        current_text_list = []
        start_time = segments[i]['start']
        for j in range(i, len(segments)):
            end_time = segments[j]['end']
            duration = end_time - start_time
            if duration > max_duration: break
            
            current_text_list.append(segments[j]['text'])
            full_text = " ".join(current_text_list).strip()
            
            if duration >= min_duration:
                score = score_segment(full_text)
                potential_clips.append({
                    'start': start_time, 'end': end_time,
                    'duration': duration, 'text': full_text, 'score': score
                })
                
    # Ordena pelos trechos de maior pontuação
    sorted_clips = sorted(potential_clips, key=lambda x: x['score'], reverse=True)
    final_clips = []
    
    # Filtra sobreposições para não gerar cortes redundantes
    for clip in sorted_clips:
        is_overlapping = any(clip['start'] < final_clip['end'] and clip['end'] > final_clip['start'] for final_clip in final_clips)
        if not is_overlapping:
            final_clips.append(clip)
        if len(final_clips) >= num_clips:
            break
            
    print(f"Análise concluída. {len(final_clips)} clipes de alto potencial encontrados.")
    return final_clips

def create_clip(video_path, clip_info, output_filename, video_title):
    """Fatia o vídeo original aplicando crop vertical (9:16)."""
    print(f"\n   -> Preparando clipe: {output_filename}")
    os.makedirs(CLIPS_FOLDER, exist_ok=True)
    final_output_path = os.path.join(CLIPS_FOLDER, output_filename)

    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-ss", str(clip_info['start']), "-to", str(clip_info['end']),
        "-vf", "scale=w=1080:h=1920:force_original_aspect_ratio=increase,crop=w=1080:h=1920",
        "-c:v", codec_video, "-crf", crf_qualidade, "-preset", preset_velocidade,
        "-c:a", "aac", "-b:a", bitrate_audio, "-movflags", "faststart",
        final_output_path
    ]
    _run_ffmpeg_with_progress(command, output_filename)

def create_clip_emocoes(video_path, clip_info, output_filename, video_title):
    """Fatia o vídeo com base nas marcações do modo emoções (picos de áudio)."""
    print(f"\n   -> Preparando clipe: {output_filename}")
    os.makedirs(CLIPS_FOLDER, exist_ok=True)
    final_output_path = os.path.join(CLIPS_FOLDER, output_filename)

    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-ss", str(clip_info['inicio']), "-to", str(clip_info['fim']),
        "-vf", "scale=w=1080:h=1920:force_original_aspect_ratio=increase,crop=w=1080:h=1920",
        "-c:v", codec_video, "-crf", crf_qualidade, "-preset", preset_velocidade,
        "-c:a", "aac", "-b:a", bitrate_audio, "-movflags", "faststart",
        final_output_path
    ]
    _run_ffmpeg_with_progress(command, output_filename)


# ====================================================================
# WORKERS DE ORQUESTRAÇÃO DE CORTES
# ====================================================================

def main(video_path, num_clips, min_duration, max_duration):
    """Worker para o fluxo de cortes baseados em Palavras-Chave."""
    try:
        audio_file = os.path.join(PASTA_TEMP, "temp_audio.wav") 

        extract_audio(video_path, audio_file)
        transcription = transcribe_audio_for_cuts(audio_file)
        
        # Limpeza do temporário
        if os.path.exists(audio_file):
            os.remove(audio_file) 

        viral_segments = find_viral_segments(transcription, num_clips, min_duration, max_duration)
        if not viral_segments:
            print("\nNão foi possível encontrar segmentos que atendam aos seus critérios.")
            return

        video_title = os.path.splitext(os.path.basename(video_path))[0]
        
        print("\n--- [FASE 4/4] Criando e Salvando os Cortes ---")
        for i, clip in enumerate(viral_segments):
            start_minutes, start_seconds = divmod(int(clip['start']), 60)
            print(f"\nCorte #{i+1} de {len(viral_segments)} (inicia em {start_minutes:02d}:{start_seconds:02d})")
            output_filename = format_filename(video_title, i+1)
            create_clip(video_path, clip, output_filename, video_title)
        
        print("\n\n--- Processo de Cortes Finalizado! ---")
        print(f"Os clipes foram salvos na pasta temporária e estão prontos para a legendagem.")

    except Exception as e:
        print(f"\nOcorreu um erro inesperado no Cutter: {e}")
        log_error(f"Ocorreu um erro inesperado: {e}")
        return

def main_emocoes(video_path, segments, num_clips):
    """Worker para o fluxo de cortes baseados em Análise de Contexto (Emoções/Áudio)."""
    try:
        os.makedirs(CLIPS_FOLDER, exist_ok=True)
        video_title = os.path.splitext(os.path.basename(video_path))[0]
        
        print("\n--- [FASE 3/4] Criando e Salvando os Cortes ---")
        
        final_segments = segments[:num_clips]
        if not final_segments:
            print("\nNão foi possível encontrar segmentos que atendam aos seus critérios.")
            return

        cortes_metadata = []

        for i, clip in enumerate(final_segments):
            start_minutes, start_seconds = divmod(int(clip['inicio']), 60)
            print(f"\nCorte #{i+1} de {len(final_segments)} (inicia em {start_minutes:02d}:{start_seconds:02d})")
            output_filename = format_filename(video_title, i+1)
            create_clip_emocoes(video_path, clip, output_filename, video_title)

            cortes_metadata.append({
                "filename": output_filename,
                "start": clip['inicio'],
                "end": clip['fim']
            })
        
        # Salva a lista de metadados para uso futuro ou debug
        metadata_path = os.path.join(CLIPS_FOLDER, "metadata_cortes.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(cortes_metadata, f, indent=4)
            
        print(f"\nMetadados dos cortes salvos em: {os.path.basename(metadata_path)}")
        print("\n\n--- Processo de Cortes Finalizado! ---")

    except Exception as e:
        print(f"\nOcorreu um erro inesperado no Cutter (Emoções): {e}")
        log_error(f"Ocorreu um erro inesperado (Emoções): {e}")
        return