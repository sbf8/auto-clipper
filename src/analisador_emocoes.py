# ====================================================================
# AUTOCLIPPER versão 5.0.0 | MÓDULO DE ANÁLISE DE EMOÇÕES (ÁUDIO)
# ====================================================================
# Descrição: O "Cérebro Auditivo" do projeto. Usa a biblioteca Librosa 
# para varrer as ondas sonoras em busca de picos de energia (gritos, 
# risadas, ênfases verbais). Ele mapeia o silêncio ao redor do pico 
# para garantir que o corte comece e termine em pausas naturais.
# ====================================================================

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
import inspect
from pathlib import Path

import librosa
import numpy as np

# --- 1. RESOLUÇÃO DO DIRETÓRIO RAIZ (BASE_DIR) ---
try:
    CURRENT_DIR = Path(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
    BASE_DIR = CURRENT_DIR.parent
except Exception:
    BASE_DIR = Path(os.getcwd())

# --- 2. CONSTANTES DE ANÁLISE ACÚSTICA ---
# Determina a granularidade da análise (resolução do escaneamento)
JANELA_ANALISE = 0.5 # em segundos

# Duração mínima para que um silêncio seja considerado uma "respiração/pausa"
DURACAO_MIN_PAUSA = 0.5 # em segundos


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL: MAPEAMENTO E PONTUAÇÃO DE ONDAS
# ====================================================================

def analisar_picos_volume(audio_path, threshold=0.2):
    """
    Analisa um arquivo de áudio para encontrar picos de volume e 
    estabelece pontos de corte seguros baseados no silêncio adjacente.

    Args:
        audio_path (str): Caminho absoluto para o arquivo de áudio temporário.
        threshold (float): Limite (0.0 a 1.0) para considerar um pico (gatilho).

    Returns:
        list: Dicionários contendo 'inicio', 'fim', 'intensidade' e 'score'.
    """
    print(f"  -> Escaneando picos de energia (Emoções) no áudio: {os.path.basename(audio_path)}")
    
    try:
        # Carrega o áudio nativamente
        y, sr = librosa.load(audio_path, sr=None)

        # 1. Análise da Energia RMS (Volume bruto)
        frame_length = int(JANELA_ANALISE * sr)
        rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=frame_length)[0]
        
        max_rms = np.max(rms)
        # Prevenção contra quebra (Divisão por zero se o áudio for mudo)
        if max_rms == 0:
            print("  -> AVISO: Áudio completamente mudo detectado. Nenhum corte possível.")
            return []
            
        volume_normalizado = rms / max_rms

        # 2. Mapeamento Estrutural de Silêncio (Pausas naturais)
        silence_threshold = 0.1 
        silence_frames = np.where(volume_normalizado < silence_threshold)[0]
        silence_segments = []
        
        # Agrupa frames isolados de silêncio em blocos contínuos (segmentos)
        if len(silence_frames) > 0:
            silence_start_frame = silence_frames[0]
            for i in range(1, len(silence_frames)):
                # Se houver um salto numérico, o silêncio foi quebrado por um som
                if silence_frames[i] != silence_frames[i-1] + 1:
                    silence_end_frame = silence_frames[i-1]
                    duracao = (silence_end_frame - silence_start_frame) * JANELA_ANALISE
                    
                    if duracao >= DURACAO_MIN_PAUSA:
                        silence_segments.append({
                            'start': silence_start_frame * JANELA_ANALISE, 
                            'end': (silence_end_frame + 1) * JANELA_ANALISE
                        })
                    silence_start_frame = silence_frames[i]

            # Processa o último segmento residual
            silence_end_frame = silence_frames[-1]
            duracao = (silence_end_frame - silence_start_frame) * JANELA_ANALISE
            if duracao >= DURACAO_MIN_PAUSA:
                silence_segments.append({
                    'start': silence_start_frame * JANELA_ANALISE, 
                    'end': (silence_end_frame + 1) * JANELA_ANALISE
                })

        # 3. Detecção de Picos e Expansão Contextual
        picos = []
        is_pico = False
        start_time_pico = 0

        for i, volume in enumerate(volume_normalizado):
            # Encontrou o gatilho de um pico
            if volume > threshold and not is_pico:
                is_pico = True
                start_time_pico = i * JANELA_ANALISE
                
            # Fim do pico atual
            elif volume <= threshold and is_pico:
                is_pico = False
                end_time_pico = i * JANELA_ANALISE
                
                # Procura a pausa mais próxima ANTES do pico (Início do corte)
                start_contexto = start_time_pico
                for seg in reversed(silence_segments):
                    if seg['end'] < start_time_pico:
                        start_contexto = seg['end']
                        break
                
                # Procura a pausa mais próxima DEPOIS do pico (Fim do corte)
                end_contexto = end_time_pico
                for seg in silence_segments:
                    if seg['start'] > end_time_pico:
                        end_contexto = seg['start']
                        break

                # Calcula a média da intensidade sonora apenas na área de pico
                idx_inicio = int(start_time_pico/JANELA_ANALISE)
                idx_fim = int(end_time_pico/JANELA_ANALISE)
                
                intensidade_media = 0
                if idx_fim > idx_inicio:
                    intensidade_media = np.mean(volume_normalizado[idx_inicio:idx_fim])

                picos.append({
                    'inicio': start_contexto, 
                    'fim': end_contexto, 
                    'intensidade': intensidade_media
                })

        # 4. Ranqueamento e Filtragem (Matemática de Valor)
        for pico in picos:
            pico['duracao'] = pico['fim'] - pico['inicio']
            pico['score'] = pico['intensidade'] * pico['duracao'] 

        sorted_picos = sorted(picos, key=lambda x: x['score'], reverse=True)
        
        # 5. Remove sobreposições (Impede que o mesmo momento gere dois cortes)
        final_picos = []
        for pico in sorted_picos:
            is_overlapping = any((pico['inicio'] < fp['fim'] and pico['fim'] > fp['inicio']) for fp in final_picos)
            if not is_overlapping:
                final_picos.append(pico)

        print(f"  -> Análise de áudio concluída. {len(final_picos)} picos magnéticos isolados.")
        return final_picos

    except Exception as e:
        print(f"  -> ERRO Crítico na análise de emoções/áudio: {e}")
        return []


# ====================================================================
# FUNÇÕES DE INICIALIZAÇÃO / TESTE DE MÓDULO ISOLADO
# ====================================================================

if __name__ == "__main__":
    print("="*60)
    print("--- Teste Unitário: analisador_emocoes.py ---")
    print("="*60)

    # Assume que um arquivo 'audio_teste.wav' está na mesma pasta durante o teste local
    audio_de_exemplo = os.path.join(CURRENT_DIR, 'audio_teste.wav')
    
    if os.path.exists(audio_de_exemplo):
        picos_encontrados = analisar_picos_volume(audio_de_exemplo, threshold=0.2)
        if picos_encontrados:
            for i, pico in enumerate(picos_encontrados):
                print(f"Pico {i+1}: Início = {pico['inicio']:.2f}s | Fim = {pico['fim']:.2f}s | Score = {pico['score']:.2f}")
        else:
            print("Nenhum pico de volume acima do limite encontrado.")
    else:
        print(f"AVISO: Arquivo de áudio de exemplo '{audio_de_exemplo}' não encontrado.")
        print("Para testar individualmente, coloque um 'audio_teste.wav' na pasta raiz do script.")