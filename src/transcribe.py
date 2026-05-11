# ====================================================================
# AUTOCLIPPER versão 5.0.0 | MÓDULO DE TRANSCRIÇÃO E ALINHAMENTO
# ====================================================================
# Descrição: Este módulo é o coração da Inteligência Artificial do AutoClipper.
# Ele utiliza a biblioteca WhisperX (baseada no modelo Whisper da OpenAI)
# para realizar a transcrição ultrarrápida e o alinhamento preciso
# de áudio/vídeo, gerando arquivos JSON com timestamps por palavra.
# ====================================================================

import warnings
# Suprime avisos não críticos de dependências (ex: depreciações futuras no PyTorch)
warnings.filterwarnings("ignore", category=UserWarning)

import sys
import os
from pathlib import Path 
import inspect
import json
import gc

# --- 1. RESOLUÇÃO DO DIRETÓRIO RAIZ (BASE_DIR) ---
try:
    CURRENT_DIR = Path(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
    BASE_DIR = CURRENT_DIR.parent 
except Exception:
    BASE_DIR = Path(os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))))

# --- 2. ISOLAMENTO DO CACHE DE MODELOS (PORTABILIDADE) ---
# Em vez de salvar modelos no disco 'E:\' do desenvolvedor original, 
# criamos uma pasta oculta local (.models_cache). Isso torna o projeto 100% portátil.
PASTA_CACHE_MODELOS = BASE_DIR / ".models_cache" / "huggingface"
os.makedirs(PASTA_CACHE_MODELOS, exist_ok=True)
os.environ['HF_HOME'] = str(PASTA_CACHE_MODELOS)

# --- 3. CORREÇÃO DE SEGURANÇA DO PYTORCH 2.6+ ---
import torch
# O WhisperX e o Pyannote tentam carregar modelos VAD usando o torch.load().
# A partir do PyTorch 2.6, 'weights_only' virou True por padrão, quebrando a importação.
# Este "monkey patch" força temporariamente a leitura para evitar crashs na máquina do usuário.
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

# Importações de terceiros (devem vir APÓS o patch do PyTorch)
import whisperx
import cutter

# --- 4. CONSTANTES DE DIRETÓRIOS E MODELOS ---
PASTA_TEMP_GLOBAL = BASE_DIR / "temp"
SUBS_FOLDER = PASTA_TEMP_GLOBAL / "subs"
CLIPS_FOLDER = PASTA_TEMP_GLOBAL / "final"

# Configurações do WhisperX (Pode ser abstraído para um config.py no futuro)
MODEL_NAME = 'large-v3'
BATCH_SIZE = 16
COMPUTE_TYPE = 'float32' # Use 'float16' se o usuário tiver GPU para otimizar VRAM

# --- INICIALIZAÇÃO DO MODELO ---
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# NOVO: Força o silêncio absoluto nas bibliotecas tagarelas de IA
import logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("speechbrain").setLevel(logging.ERROR)

# Silencia AMBAS as saídas (padrão e erro) durante o carregamento do modelo
devnull = open(os.devnull, 'w')
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = devnull
sys.stderr = devnull

try:
    MODEL = whisperx.load_model(MODEL_NAME, DEVICE, compute_type=COMPUTE_TYPE)
finally:
    # Restaura AMBAS as saídas para o normal após o carregamento.
    # OBS: Removemos o sys.stdout.close() daqui para evitar o erro 
    # de "I/O operation on closed file" caso threads de IA tentem logar algo depois.
    sys.stdout = old_stdout
    sys.stderr = old_stderr

print("Modelo Whisper carregado com sucesso. Aguardando comando...")


# ====================================================================
# FUNÇÕES AUXILIARES / WORKERS
# ====================================================================

def _processar_arquivo_de_audio(input_file, output_json_path):
    """
    Motor central de transcrição. Recebe um arquivo de áudio/vídeo,
    transcreve com WhisperX, alinha os tempos de cada palavra e salva em JSON.
    """
    if os.path.exists(output_json_path):
        print(f"  -> Legenda já existe, pulando processamento de: {os.path.basename(output_json_path)}")
        return
    
    try:
        # 1. Carrega o áudio nativamente
        audio = whisperx.load_audio(input_file)

        # 2. Transcreve todo o áudio (Geração do texto bruto)
        result = MODEL.transcribe(audio, batch_size=BATCH_SIZE)

        # 3. Alinha os timestamps (Garante que a palavra na tela bata com a fala)
        language_code = result["language"]
        model_a, metadata = whisperx.load_align_model(language_code=language_code, device=DEVICE)
        aligned_result = whisperx.align(result["segments"], model_a, metadata, audio, device=DEVICE, return_char_alignments=False)
        
        # 4. Liberação agressiva de memória (VRAM)
        del model_a
        gc.collect()
        if DEVICE == "cuda":
            torch.cuda.empty_cache()

        # 5. Salva o resultado final com a formatação correta
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(aligned_result, f, ensure_ascii=False, indent=2)
        
        print(f"  -> Legenda super-precisa gerada para: {os.path.basename(input_file)}")

    except Exception as e:
        print(f"  ERRO ao processar o áudio de {os.path.basename(input_file)}: {e}")


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL (APIs INTERNAS)
# ====================================================================

def transcribe_original_video(video_path):
    """
    Processa o vídeo completo do YouTube.
    Usado principalmente no 'Modo Emoções' para analisar o contexto do vídeo
    inteiro antes de decidir onde cortar.
    """
    os.makedirs(SUBS_FOLDER, exist_ok=True)
    
    # Extrai o nome base e formata para combinar com o padrão do AutoClipper
    original_base_name = os.path.splitext(os.path.basename(video_path))[0]
    clean_base_name = cutter.format_filename(original_base_name, 1).split('_0')[0]
    
    json_file = os.path.join(SUBS_FOLDER, f"{clean_base_name}.json")
    _processar_arquivo_de_audio(video_path, json_file)


def transcribe_clips_final():
    """
    Itera sobre a pasta temporária de clipes finais (temp/final) e 
    transcreve um por um. É o passo final antes de queimar as legendas na tela.
    """
    os.makedirs(SUBS_FOLDER, exist_ok=True)

    videos_na_pasta = [f for f in os.listdir(CLIPS_FOLDER) if f.lower().endswith(('.mp4', '.mov', '.mkv', '.avi'))]
    
    if not videos_na_pasta:
        print(f"AVISO: Nenhum vídeo encontrado na pasta '{CLIPS_FOLDER}' para transcrever.")
        return
           
    for filename in videos_na_pasta:
        input_file_path = os.path.join(CLIPS_FOLDER, filename)
        base_name = os.path.splitext(filename)[0]
        json_file_path = os.path.join(SUBS_FOLDER, f"{base_name}.json")
        _processar_arquivo_de_audio(input_file_path, json_file_path)