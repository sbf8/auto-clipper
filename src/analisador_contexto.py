# ====================================================================
# AUTOCLIPPER versão 5.0.0 | MÓDULO DE ANÁLISE DE CONTEXTO (TEXTO)
# ====================================================================
# Descrição: Este módulo atua como o cérebro de marcação de cortes.
# Ele lê a transcrição JSON gerada pelo WhisperX e utiliza heurísticas
# (como densidade de palavras por segundo e duração de falas contínuas)
# para ranquear e selecionar os trechos com maior potencial de retenção.
# ====================================================================

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
import json
from pathlib import Path 
import inspect

# --- 1. RESOLUÇÃO DO DIRETÓRIO RAIZ (BASE_DIR) ---
try:
    CURRENT_DIR = Path(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
    BASE_DIR = CURRENT_DIR.parent 
except Exception:
    BASE_DIR = Path(os.getcwd())

# --- 2. CONSTANTES DE CAMINHOS ABSOLUTOS ---
PASTA_TEMP_GLOBAL = BASE_DIR / "temp"
SUBS_FOLDER = str(PASTA_TEMP_GLOBAL / "subs")


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL: CÁLCULO DE RELEVÂNCIA
# ====================================================================

def analisar_contexto_cortes(json_path, num_clips):
    """
    Analisa a estrutura da transcrição para encontrar blocos de fala densos.
    A heurística atual valoriza segmentos longos com muitas palavras,
    indicando uma linha de raciocínio contínua (ideal para Shorts/Reels).
    
    Args:
        json_path (str): Caminho absoluto para o arquivo JSON da transcrição.
        num_clips (int): Quantidade de clipes desejados no final do processo.

    Returns:
        list: Lista de dicionários contendo 'inicio', 'fim' e 'score' dos melhores cortes.
    """
    print(f"  -> Analisando contexto semântico do arquivo: {os.path.basename(json_path)}")
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            transcription = json.load(f)

        # Validação segura (evita IndexError se o vídeo for mudo/sem falas)
        segments = transcription.get('segments', [])
        if not segments:
            print("  -> AVISO: Nenhuma fala detectada na transcrição (segmentos vazios).")
            return []

        picos_de_impacto = []
        
        # Iterar sobre os segmentos da transcrição para calcular a relevância
        for segment in segments:
            start_time = segment.get('start', 0)
            end_time = segment.get('end', 0)
            segment_duration = end_time - start_time
            words = segment.get('words', [])
            
            # Condição base: Segmentos maiores que 5 segundos e que contenham palavras
            if words and segment_duration > 5:
                # CÁLCULO DE SCORE: 
                # Multiplica a duração do segmento pela quantidade de palavras.
                # Segmentos longos e com fala rápida (densidade) recebem notas maiores.
                score = segment_duration * len(words)
                
                picos_de_impacto.append({
                    'inicio': start_time,
                    'fim': end_time,
                    'score': score
                })

        # Ranqueia os picos por pontuação (do maior para o menor)
        sorted_picos = sorted(picos_de_impacto, key=lambda x: x['score'], reverse=True)
        
        # Filtra a quantidade exata de clipes solicitada pelo usuário
        final_clips = sorted_picos[:num_clips]

        print(f"  -> Análise concluída. {len(final_clips)} momentos de impacto capturados.")
        return final_clips

    except Exception as e:
        print(f"  -> ERRO Crítico na análise de contexto: {e}")
        return []


# ====================================================================
# FUNÇÃO DE INICIALIZAÇÃO / TESTE DE MÓDULO ISOLADO
# ====================================================================

if __name__ == "__main__":
    print("="*60)
    print("--- Teste Unitário: analisador_contexto.py ---")
    print("="*60)
    
    json_de_exemplo = os.path.join(SUBS_FOLDER, 'exemplo.json')
    
    if os.path.exists(json_de_exemplo):
        melhores_cortes = analisar_contexto_cortes(json_de_exemplo, 5)
        if melhores_cortes:
            for i, corte in enumerate(melhores_cortes):
                print(f"Corte #{i+1}: Início = {corte['inicio']:.2f}s | Fim = {corte['fim']:.2f}s | Score = {corte['score']:.2f}")
    else:
        print(f"AVISO: Arquivo de mock '{json_de_exemplo}' não encontrado para teste local.")