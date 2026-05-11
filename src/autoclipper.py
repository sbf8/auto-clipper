# ====================================================================
# AUTOCLIPPER versão 5.0.0 | ORQUESTRADOR PRINCIPAL
# ====================================================================
# Este script atua como o cérebro do AutoClipper, gerenciando os menus,
# coordenando o fluxo de dados entre os módulos (download, corte, 
# transcrição, legenda) e lidando com processos em lote.
# ====================================================================

import warnings
warnings.filterwarnings("ignore", category=UserWarning)
import sys
import os
from pathlib import Path 
import inspect
import traceback
import csv
from datetime import datetime
import cutter
import cv2
from transcribe import DEVICE
import transcribe
import ajustar_legendas
import queimar_legendas
import time
import shutil
import analisador_contexto
import montador_reels
import transformador
import logging

# --- 1. RESOLUÇÃO DO DIRETÓRIO RAIZ (BASE_DIR) ---
try:
    # Obtém o caminho dinâmico do diretório onde este script está (ex: .../src)
    CURRENT_DIR = Path(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
    # O diretório base/raiz do projeto, tornando-o universal para qualquer OS
    BASE_DIR = CURRENT_DIR.parent 
except Exception:
    BASE_DIR = Path(os.path.dirname(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))))

# --- 2. DEFINIÇÃO DAS CONSTANTES DE CAMINHO ABSOLUTAS ---
PASTA_FINAL_EXPORT = BASE_DIR / "burned_sub"
PASTA_LOGS = BASE_DIR / "logs"
PASTA_LUTS = BASE_DIR / "luts"
PASTA_TEMP_GLOBAL = BASE_DIR / "temp" 
PASTA_BACKUP_GLOBAL = BASE_DIR / "backup" # Nova constante universal para backups
# -----------------------------------------------

# --- 3. INICIALIZAÇÃO DA ESTRUTURA DE DIRETÓRIOS ---
try:
    print("Verificando estrutura de pastas do projeto...")
    os.makedirs(PASTA_TEMP_GLOBAL, exist_ok=True)
    os.makedirs(PASTA_LOGS, exist_ok=True)
    os.makedirs(PASTA_FINAL_EXPORT, exist_ok=True)
    os.makedirs(PASTA_BACKUP_GLOBAL, exist_ok=True) # Garante que a pasta de backup exista
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao criar pastas estruturais. Verifique permissões. Erro: {e}")
    sys.exit(1)

# --- 4. CONFIGURAÇÃO DE LOGS ---
try: 
    # Silencia logs excessivos de bibliotecas de terceiros para manter o terminal limpo
    logging.getLogger('whisperx').setLevel(logging.ERROR)
    logging.getLogger().setLevel(logging.ERROR)
except Exception as e:
    pass 


# ====================================================================
# FUNÇÕES UTILITÁRIAS E INTERFACE COM O USUÁRIO
# ====================================================================

def _obter_int(prompt, min_valor=0):
    """Garante que a entrada do usuário seja um número inteiro válido."""
    while True:
        try:
            valor = int(input(prompt))
            if valor > min_valor: return valor
            else: print(f"O valor deve ser maior que {min_valor}.")
        except ValueError: print("Entrada inválida. Digite um número inteiro.")

def _obter_duracao_video(video_path):
    """Usa o OpenCV para extrair a duração total de um arquivo de vídeo em segundos."""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        cap.release()
        return duration
    except Exception:
        return None

def _obter_configuracao_posicao():
    """Menu para definir o posicionamento (X,Y) da legenda na tela."""
    print("=> Escolha a posição das legendas:")
    print("  [1] Superior Centralizado\n  [2] Meio Centralizado\n  [3] Baixo Centralizado")
    while True:
        try:
            escolha = int(input("=> Digite o número da sua escolha (1, 2 ou 3): "))
            margem_extra = 20 
            if escolha == 1: return 8, 250 + margem_extra
            elif escolha == 2: return 5, 20
            elif escolha == 3: return 2, 390 + margem_extra
            else: print("Opção inválida.")
        except ValueError: print("Entrada inválida. Digite um número.")

def _obter_configuracao_animacao():
    """Menu para o usuário escolher o estilo de animação de entrada/saída das legendas."""
    print("=> Escolha um efeito de animação para as legendas:")
    print("  [1] Padrão (Sem movimento)")
    print("  --- Efeitos de Entrada ---")
    print("  [2] Fade-in Suave\n  [3] Slide-in (Vindo de baixo)\n  [4] Slide-in (Vindo de cima)")
    print("  [5] Slide-in (Vindo da esquerda)\n  [6] Slide-in (Vindo da direita)")
    print("  [7] Efeito Pop (Zoom rápido)\n  [8] Revelação (Foco suave)")
    print("  --- Efeitos de Ênfase ---")
    print("  [9] Pulso Sutil\n  [10] Flip-in 3D\n  [11] Brilho Suave")
    print("  --- Modo Criativo ---")
    print("  [12] Variação Automática (Sorteio por bloco)")

    while True:
        try:
            escolha = int(input("=> Digite o número da sua escolha: "))
            opcoes = {
                1: "padrao", 2: "fade", 3: "slide_baixo", 4: "slide_cima",
                5: "slide_esquerda", 6: "slide_direita", 7: "pop", 8: "revelacao",
                9: "pulso", 10: "flip_3d", 11: "brilho", 12: "variado"
            }
            if escolha in opcoes: return opcoes[escolha]
            else: print("Opção inválida.")
        except ValueError: print("Entrada inválida. Digite um número.")

def _obter_opcoes_transformacao():
    """Coleta os filtros do FFmpeg que serão aplicados para evitar detecção de conteúdo duplicado."""
    print("\n--- Menu de Transformações (Monetização) ---")
    print("Selecione os efeitos a serem aplicados (ex: 1,3,8):")
    print("  [1] Espelhar Vídeo\n  [2] Ajustar Cores\n  [3] Acelerar Levemente (5%)")
    print("  [4] Adicionar Vinheta\n  [5] Granulação\n  [6] Pitch Shift (Áudio)")
    print("  [7] Adicionar Zoom Lento\n  [8] Aplicar LUT (Color Grading)\n  [9] Aplicar TODOS")
    
    escolhas_usuario = input("Digite os números das suas escolhas: ")
    todos = '9' in escolhas_usuario
    
    return {
        'espelhar': '1' in escolhas_usuario or todos,
        'cores': '2' in escolhas_usuario or todos,
        'velocidade': '3' in escolhas_usuario or todos,
        'vinheta': '4' in escolhas_usuario or todos,
        'granulacao': '5' in escolhas_usuario or todos,
        'pitch_shift': '6' in escolhas_usuario or todos,
        'zoom_lento': '7' in escolhas_usuario or todos,
        'luts': '8' in escolhas_usuario or todos,
    }

def _check_if_processed(title):
    """Verifica no log se o vídeo atual já passou pelo pipeline anteriormente."""
    history_file = os.path.join(PASTA_LOGS, "processed_videos.txt")
    if not os.path.exists(history_file): return False
    with open(history_file, "r", encoding="utf-8") as f:
        processed_titles = [line.strip() for line in f]
    return title in processed_titles

def _add_to_processed_list(title):
    """Registra um vídeo processado com sucesso no arquivo de histórico."""
    history_file = os.path.join(PASTA_LOGS, "processed_videos.txt")
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(title + "\n")
    print(f"\nVídeo '{title}' adicionado ao histórico de processamento.")

def log_error(error_details):
    """Registra falhas detalhadas na pasta de logs para auditoria/debugging."""
    log_file = os.path.join(PASTA_LOGS, "error_log.txt")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write(f"ERRO OCORRIDO EM: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n" + error_details + "\n\n")

def _executar_fluxo_final(videos_da_sessao, configs):
    """Responsável apenas pela etapa bônus de agrupar clipes num 'Super Reels'."""
    if not videos_da_sessao:
        print("\nAVISO: Nenhum vídeo foi legendado nesta sessão. Pulando etapas finais.")
        return

    if configs.get('criar_super_reels', False):
        print("\n--- Criando 'Super Reels' com base nas configurações iniciais... ---")
        montador_reels.montar_supercut(
            num_top_clips=configs['super_reels_clips'],
            duracao_maxima=configs['super_reels_duracao']
        )
    else:
        print("\nCriação de 'Super Reels' pulada.")

def _obter_configuracoes_finais_lote():
    """Coleta configs de Pós-Produção que se aplicam de forma global (Lote ou Unitário)."""
    configs_finais = {}
    print("\n--- FASE FINAL: Pós-Produção Automática ---")
    
    while True:
        resposta_reels = input("=> Deseja criar um 'Super Reels' ao final de cada vídeo processado? [s/n]: ").lower()
        if resposta_reels in ['s', 'sim']:
            configs_finais['criar_super_reels'] = True
            configs_finais['super_reels_duracao'] = _obter_int("=> Duração MÁXIMA para cada Super Reels (segundos)? (ex: 45): ")
            configs_finais['super_reels_clips'] = _obter_int("=> Quantos clipes de topo usar? (ex: 3): ")
            break
        elif resposta_reels in ['n', 'nao', 'não']:
            configs_finais['criar_super_reels'] = False
            break
        else: print("Resposta inválida.")
            
    while True:
        resposta_transform = input("=> Deseja aplicar transformações de vídeo para monetização? [s/n]: ").lower()
        if resposta_transform in ['s', 'sim']:
            configs_finais['aplicar_transformacoes'] = True
            configs_finais['opcoes_transformacao'] = _obter_opcoes_transformacao()
            break
        elif resposta_transform in ['n', 'nao', 'não']:
            configs_finais['aplicar_transformacoes'] = False
            break
        else: print("Resposta inválida.")
            
    return configs_finais


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL (MODOS DE EXECUÇÃO UNITÁRIOS)
# ====================================================================

def modo_processo_completo():
    """Pipeline focado em encontrar trechos virais através de densidade de palavras-chave."""
    configs = obter_configuracoes_gerais()
    print("\n--- Verificando histórico do vídeo... ---")
    
    video_title = cutter.get_video_title(configs["url"])
    if not video_title: return
    
    if _check_if_processed(video_title):
        print(f"AVISO: O vídeo '{video_title}' já foi processado anteriormente. Cancelado.")
        return

    configs["escolha_animacao"] = _obter_configuracao_animacao()
    configs_finais = _obter_configuracoes_finais_lote()
    configs.update(configs_finais) 
    
    print("\n" + "="*60)
    print("      INICIANDO PROCESSAMENTO (MODO PALAVRAS-CHAVE)...")
    print("="*60)
    
    print("\n--- [FASE 1/4] Baixando e Cortando ---")
    video_path, video_title_dl = cutter.download_video(configs["url"], os.path.join(PASTA_TEMP_GLOBAL, "youtube_original"))
    if not video_path: return

    cutter.main(video_path=video_path, num_clips=configs["num_clips"], min_duration=configs["min_duration"], max_duration=configs["max_duration"])
    PASTA_CLIPS_KW = os.path.join(PASTA_TEMP_GLOBAL, "final") 

    if not os.path.isdir(PASTA_CLIPS_KW) or not any(fname.lower().endswith(('.mp4', '.mov', '.mkv')) for fname in os.listdir(PASTA_CLIPS_KW)):
        print("\nAVISO: O processo de corte não gerou vídeos. Finalizando.")
        return

    print("\n--- [FASE 2/4] Transcrevendo os clipes curtos ---")
    transcribe.transcribe_clips_final()

    print("\n" + "="*60 + "\n      INICIANDO FASE DE LEGENDAGEM\n" + "="*60)
    
    print("\n--- [FASE 3/4] Gerando legendas (.ass) ---")
    ajustar_legendas.main(
        alinhamento=configs["alinhamento"], margem_vertical=configs["margem_vertical"],
        palavras_por_bloco=configs["palavras_por_bloco"], efeito_animacao=configs["escolha_animacao"]
    )
    
    print("\n--- [FASE 4/4] Queimando legendas na imagem ---")
    videos_legendados_sessao = queimar_legendas.main(pasta_destino_final=PASTA_FINAL_EXPORT)
    
    _executar_fluxo_final(videos_legendados_sessao, configs)
    _add_to_processed_list(video_title)


def modo_processo_completo_emocoes():
    """Pipeline focado em encontrar trechos de alta retenção através de picos de volume/silêncio."""
    print("\n--- FASE 1: Configuração dos Cortes (Modo Emoção) ---")
    url = input("=> Por favor, cole a URL do vídeo do YouTube: ")

    video_title = cutter.get_video_title(url)
    if not video_title: return 
    if _check_if_processed(video_title):
        print(f"AVISO: O vídeo '{video_title}' já foi processado anteriormente. Cancelado.")
        return

    num_clips_desejado = 2
    
    print("\n--- FASE 2: Configuração das Legendas ---")
    alinhamento, margem_vertical = _obter_configuracao_posicao()
    palavras_por_bloco = _obter_int("=> Quantas palavras por bloco? (ex: 2 ou 3): ")
    escolha_animacao = _obter_configuracao_animacao()
    configs_finais = _obter_configuracoes_finais_lote() 
    
    configs_finais.update({
        "alinhamento": alinhamento, "margem_vertical": margem_vertical, 
        "palavras_por_bloco": palavras_por_bloco, "escolha_animacao": escolha_animacao
    })
    
    print("\n" + "="*60 + "\n      INICIANDO PROCESSAMENTO (MODO EMOÇÃO)\n" + "="*60)
    
    print("\n--- [FASE 1/5] Baixando o vídeo original ---")
    video_path, video_title_dl = cutter.download_video(url, os.path.join(PASTA_TEMP_GLOBAL, "youtube_original"))
    if not video_path: return
    
    print("\n--- [FASE 2/5] Transcrevendo vídeo completo para análise... ---")
    duracao_segundos = _obter_duracao_video(video_path)
    if duracao_segundos:
        msg_hw = "na CPU" if DEVICE == 'cpu' else "na GPU"
        fator = 5 if DEVICE == 'cpu' else 0.4
        print(f"O vídeo tem {duracao_segundos/60:.1f} minutos. A transcrição {msg_hw} levará ~{(duracao_segundos/60)*fator:.0f} minutos.")

    transcribe.transcribe_original_video(video_path)
    
    print("\n--- [FASE 3/5] Analisando contexto de picos... ---")
    json_path = os.path.join(PASTA_TEMP_GLOBAL, "subs", f"{cutter.format_filename(video_title, 1).split('_0')[0]}.json")
    picos_emocao = analisador_contexto.analisar_contexto_cortes(json_path, num_clips_desejado)

    if not picos_emocao: return
    
    print("\n--- [FASE 4/5] Cortando os clipes de maior impacto ---")
    cutter.main_emocoes(video_path=video_path, segments=picos_emocao, num_clips=num_clips_desejado)
    
    PASTA_CLIPS_FINAL = PASTA_TEMP_GLOBAL / "final"
    if not os.path.isdir(PASTA_CLIPS_FINAL) or not any(fname.lower().endswith(('.mp4', '.mov', '.mkv')) for fname in os.listdir(str(PASTA_CLIPS_FINAL))):     
        print("\nAVISO: O processo de corte não gerou vídeos. Finalizando.")
        return

    print("\n--- [FASE 5/5] Transcrevendo os clipes curtos... ---")
    transcribe.transcribe_clips_final()

    print("\n" + "="*60 + "\n      INICIANDO FASE DE LEGENDAGEM FINAL\n" + "="*60)
    
    ajustar_legendas.main(
        alinhamento=alinhamento, margem_vertical=margem_vertical,
        palavras_por_bloco=palavras_por_bloco, efeito_animacao=escolha_animacao 
    )

    sufixo_final = "_legendado"
    pasta_videos_fonte = PASTA_CLIPS_FINAL 

    if configs_finais.get('aplicar_transformacoes', False):
        print("\n" + "="*60 + "\n      MODO MONETIZAÇÃO ATIVADO.\n" + "="*60)
        sufixo_final = "_monetize"
        pasta_videos_transformados = PASTA_TEMP_GLOBAL / "transformed_temp"
        os.makedirs(pasta_videos_transformados, exist_ok=True)
        opcoes = configs_finais['opcoes_transformacao']

        arquivos_de_video = [f for f in os.listdir(pasta_videos_fonte) if f.lower().endswith(('.mp4', '.mov', '.mkv'))]
        for video_file in arquivos_de_video:
            transformador.aplicar_transformacoes(os.path.join(pasta_videos_fonte, video_file), os.path.join(pasta_videos_transformados, video_file), opcoes)
        pasta_videos_fonte = pasta_videos_transformados

    videos_legendados_sessao = queimar_legendas.main(
        pasta_destino_final=PASTA_FINAL_EXPORT,
        pasta_videos_fonte=pasta_videos_fonte, 
        sufixo_saida=sufixo_final
    )

    if 'pasta_videos_transformados' in locals() and os.path.isdir(pasta_videos_transformados):
        shutil.rmtree(pasta_videos_transformados)

    _executar_fluxo_final(videos_legendados_sessao, configs_finais)
    _add_to_processed_list(video_title)
    print(f"\n--- PROCESSAMENTO CONCLUÍDO PARA: {video_title} ---")


def modo_ajuste():
    """Modo de resgate para regerar legendas de clipes cujo JSON foi ajustado manualmente."""
    print("\n--- MODO DE AJUSTE DE LEGENDAS ---")
    pasta_final = os.path.join(PASTA_TEMP_GLOBAL, "final")

    if not os.path.isdir(pasta_final) or not os.listdir(pasta_final):
        print(f"ERRO: A pasta '{pasta_final}' está vazia. Não há clipes para ajustar.")
        return

    videos = sorted([f for f in os.listdir(pasta_final) if f.lower().endswith(('.mp4', '.mov', '.mkv'))])
    
    print("\nLEMBRETE: Edite o arquivo .json na pasta 'subs/' ANTES de continuar.")
    print("Clipes disponíveis:")
    for i, video in enumerate(videos): print(f"  [{i+1}] {video}")
    
    videos_a_processar = []
    while not videos_a_processar:
        entrada = input("\nDigite o número do(s) clipe(s) que deseja regerar (ex: 2, 4-7, 9): ")
        indices_escolhidos = []
        partes_entrada = [p.strip() for p in entrada.split(',')]
        
        try:
            for parte in partes_entrada:
                if '-' in parte:
                    inicio, fim = map(int, parte.split('-'))
                    if inicio > fim: break
                    indices_escolhidos.extend(range(inicio, fim + 1))
                else:
                    indices_escolhidos.append(int(parte))
                    
            if all(1 <= idx <= len(videos) for idx in indices_escolhidos):
                videos_a_processar = [videos[i - 1] for i in indices_escolhidos]
            else: print("Erro: Números inválidos.")
        except ValueError: print("Entrada inválida.")

    print("\n--- Configuração de Estilo ---")
    alinhamento, margem_vertical = _obter_configuracao_posicao()
    palavras_por_bloco = _obter_int("=> Palavras por bloco? (ex: 3): ")
    escolha_animacao = _obter_configuracao_animacao()
    configs_finais = _obter_configuracoes_finais_lote()

    pasta_videos_fonte = pasta_final 
    sufixo_final = "_legendado"
    
    if configs_finais.get('aplicar_transformacoes', False):
        print("\n" + "="*60 + "\n      MODO MONETIZAÇÃO ATIVADO.\n" + "="*60)
        sufixo_final = "_monetize"
        pasta_videos_transformados = PASTA_TEMP_GLOBAL / "transformed_temp_ajuste"
        os.makedirs(pasta_videos_transformados, exist_ok=True)
        opcoes = configs_finais['opcoes_transformacao']
        
        for video_file in videos_a_processar:
            transformador.aplicar_transformacoes(os.path.join(pasta_videos_fonte, video_file), os.path.join(pasta_videos_transformados, video_file), opcoes)
        pasta_videos_fonte = pasta_videos_transformados
    
    videos_legendados_sessao = []
    print("\n--- [FASE 1/2] Gerando e Queimando legendas ---")
    for video_escolhido in videos_a_processar:
        nome_base = os.path.splitext(video_escolhido)[0]
        ajustar_legendas.main(alinhamento=alinhamento, margem_vertical=margem_vertical, palavras_por_bloco=palavras_por_bloco, efeito_animacao=escolha_animacao, specific_file=nome_base)
        arquivos_criados = queimar_legendas.main(specific_file=nome_base, pasta_destino_final=PASTA_FINAL_EXPORT, pasta_videos_fonte=pasta_videos_fonte, sufixo_saida=sufixo_final)
        videos_legendados_sessao.extend(arquivos_criados)
    
    if configs_finais.get('aplicar_transformacoes', False) and os.path.isdir(pasta_videos_transformados):
        shutil.rmtree(pasta_videos_transformados)

    _executar_fluxo_final(videos_legendados_sessao, configs_finais)
    print("\n--- Regeneração em lote concluída! ---")


# ====================================================================
# WORKERS E LÓGICA DE PROCESSAMENTO EM LOTE (FILA)
# ====================================================================

def _worker_processo_completo_emocoes(url, configs):
    """Worker silencioso que roda o pipeline de emoção de ponta a ponta para a fila em lote."""
    print("\n" + "="*80 + f"\n--- INICIANDO PROCESSAMENTO (MODO EMOÇÃO) PARA: {url} ---\n" + "="*80)
    
    video_title = cutter.get_video_title(url)
    if not video_title or _check_if_processed(video_title): return

    num_clips_desejado = 3
    video_path, video_title_dl = cutter.download_video(url, os.path.join(PASTA_TEMP_GLOBAL, "youtube_original"))
    if not video_path: return
    
    transcribe.transcribe_original_video(video_path)
    nome_base_video = cutter.format_filename(video_title, 1).split('_0')[0]
    json_path = os.path.join(PASTA_TEMP_GLOBAL, "subs", f"{nome_base_video}.json")

    picos_emocao = analisador_contexto.analisar_contexto_cortes(json_path, num_clips_desejado)
    if not picos_emocao: return
    
    cutter.main_emocoes(video_path=video_path, segments=picos_emocao, num_clips=num_clips_desejado)
    PASTA_CLIPS_FINAL_STRING = os.path.join(PASTA_TEMP_GLOBAL, "final")

    if not os.path.isdir(PASTA_CLIPS_FINAL_STRING) or not any(fname.lower().endswith('.mp4') for fname in os.listdir(PASTA_CLIPS_FINAL_STRING)): return

    transcribe.transcribe_clips_final()
    ajustar_legendas.main(
        alinhamento=configs["alinhamento"], margem_vertical=configs["margem_vertical"],
        palavras_por_bloco=configs["palavras_por_bloco"], efeito_animacao=configs["escolha_animacao"] 
    )

    pasta_videos_fonte = os.path.join(PASTA_TEMP_GLOBAL, "final")
    sufixo_final = "_legendado"

    if configs.get('aplicar_transformacoes', False):
        sufixo_final = "_monetize"
        pasta_videos_transformados = os.path.join(PASTA_TEMP_GLOBAL, "transformed_temp")
        os.makedirs(pasta_videos_transformados, exist_ok=True)
        opcoes = configs['opcoes_transformacao']
        for video_file in [f for f in os.listdir(pasta_videos_fonte) if f.lower().endswith('.mp4')]:
            transformador.aplicar_transformacoes(os.path.join(pasta_videos_fonte, video_file), os.path.join(pasta_videos_transformados, video_file), opcoes)
        pasta_videos_fonte = pasta_videos_transformados

    videos_legendados_sessao = queimar_legendas.main(pasta_videos_fonte=pasta_videos_fonte, sufixo_saida=sufixo_final)
    
    if configs.get('aplicar_transformacoes', False) and os.path.isdir(pasta_videos_transformados):
        shutil.rmtree(pasta_videos_transformados)

    _executar_fluxo_final(videos_legendados_sessao, configs)
    _add_to_processed_list(video_title)

def _worker_processo_completo(url, configs):
    """Worker silencioso que roda o pipeline de palavras-chave de ponta a ponta para a fila em lote."""
    print("\n" + "="*80 + f"\n--- INICIANDO PROCESSAMENTO (PALAVRAS-CHAVE) PARA: {url} ---\n" + "="*80)
    
    video_title = cutter.get_video_title(url)
    if not video_title or _check_if_processed(video_title): return

    video_path, video_title_dl = cutter.download_video(url, os.path.join(PASTA_TEMP_GLOBAL, "youtube_original"))
    if not video_path: return
    
    cutter.main(video_path=video_path, num_clips=configs["num_clips"], min_duration=configs["min_duration"], max_duration=configs["max_duration"])
    
    pasta_final = os.path.join(PASTA_TEMP_GLOBAL, "final")
    if not os.path.isdir(pasta_final) or not any(fname.lower().endswith('.mp4') for fname in os.listdir(pasta_final)): return

    transcribe.transcribe_clips_final()
    ajustar_legendas.main(alinhamento=configs["alinhamento"], margem_vertical=configs["margem_vertical"], palavras_por_bloco=configs["palavras_por_bloco"], efeito_animacao=configs["escolha_animacao"])
    
    pasta_videos_fonte = pasta_final 
    sufixo_final = "_legendado"
    
    if configs.get('aplicar_transformacoes', False):
        sufixo_final = "_monetize"
        pasta_videos_transformados = os.path.join(PASTA_TEMP_GLOBAL, "transformed_temp_kw") 
        os.makedirs(pasta_videos_transformados, exist_ok=True)
        opcoes = configs['opcoes_transformacao']
        for video_file in [f for f in os.listdir(pasta_videos_fonte) if f.lower().endswith('.mp4')]:
            transformador.aplicar_transformacoes(os.path.join(pasta_videos_fonte, video_file), os.path.join(pasta_videos_transformados, video_file), opcoes)
        pasta_videos_fonte = pasta_videos_transformados

    videos_legendados_sessao = queimar_legendas.main(pasta_videos_fonte=pasta_videos_fonte, sufixo_saida=sufixo_final)
    if 'pasta_videos_transformados' in locals() and os.path.isdir(pasta_videos_transformados): shutil.rmtree(pasta_videos_transformados)

    _executar_fluxo_final(videos_legendados_sessao, configs)
    _add_to_processed_list(video_title)

# (Ocultadas as funções de coleta de inputs obter_configuracoes_gerais_* por brevidade, elas se mantiveram intactas)
def obter_configuracoes_gerais():
    print("\n--- FASE 1: Configuração dos Cortes ---")
    url = input("=> Por favor, cole a URL do vídeo do YouTube: ")
    num_clips = _obter_int("=> Quantos cortes você deseja gerar? (ex: 10): ")
    min_duration = _obter_int("=> Qual a DURAÇÃO MÍNIMA de cada corte (em segundos)? (ex: 7): ")
    max_duration = _obter_int(f"=> Qual a DURAÇÃO MÁXIMA de cada corte (em segundos)? (ex: 30): ", min_valor=min_duration)
    alinhamento, margem_vertical = _obter_configuracao_posicao()
    palavras_por_bloco = _obter_int("=> Quantas palavras por bloco? (ex: 3): ")
    return {"url": url, "num_clips": num_clips, "min_duration": min_duration, "max_duration": max_duration, "alinhamento": alinhamento, "margem_vertical": margem_vertical, "palavras_por_bloco": palavras_por_bloco}

def obter_configuracoes_palavras_chave_lote():
    print("\n--- CONFIGURAÇÃO DO PROCESSO EM LOTE ---")
    num_clips = _obter_int("=> Quantos cortes gerar por vídeo? (ex: 10): ")
    min_duration = _obter_int("=> DURAÇÃO MÍNIMA (segs)? (ex: 7): ")
    max_duration = _obter_int(f"=> DURAÇÃO MÁXIMA (segs)? (ex: 30): ", min_valor=min_duration)
    alinhamento, margem_vertical = _obter_configuracao_posicao()
    palavras_por_bloco = _obter_int("=> Palavras por bloco? (ex: 3): ")
    escolha_animacao = _obter_configuracao_animacao()
    configs = {"num_clips": num_clips, "min_duration": min_duration, "max_duration": max_duration, "alinhamento": alinhamento, "margem_vertical": margem_vertical, "palavras_por_bloco": palavras_por_bloco, "escolha_animacao": escolha_animacao}
    configs.update(_obter_configuracoes_finais_lote())
    return configs

def obter_configuracoes_emocoes_lote():
    print("\n--- CONFIGURAÇÃO DO LOTE (EMOÇÃO) ---")
    alinhamento, margem_vertical = _obter_configuracao_posicao()
    palavras_por_bloco = _obter_int("=> Palavras por bloco? (ex: 2): ")
    escolha_animacao = _obter_configuracao_animacao()
    configs = {"alinhamento": alinhamento, "margem_vertical": margem_vertical, "palavras_por_bloco": palavras_por_bloco, "escolha_animacao": escolha_animacao}
    configs.update(_obter_configuracoes_finais_lote())
    return configs


def modo_processo_em_lote():
    """Gerenciador da fila de URLs para o modo Palavras-Chave."""
    ARQUIVO_URLS = os.path.join(PASTA_LOGS, "urls.txt")
    if not os.path.exists(ARQUIVO_URLS): return print(f"ERRO: Arquivo 'urls.txt' não encontrado na pasta logs.")
    
    with open(ARQUIVO_URLS, "r", encoding="utf-8") as f: urls = [line.strip() for line in f if line.strip()]
    if not urls: return print("Arquivo vazio.")
        
    configs = obter_configuracoes_palavras_chave_lote()
    
    for i, url in enumerate(list(urls)):
        print(f"\n>>> Processando {i + 1}/{len(list(urls))} | {url} <<<")
        try:
            _worker_processo_completo(url, configs)
            limpar_pastas_temporarias()
            urls.pop(0) 
            with open(ARQUIVO_URLS, "w", encoding="utf-8") as f:
                for u in urls: f.write(u + "\n")
        except Exception as e:
            log_error(f"Erro na URL {url}\n{traceback.format_exc()}")
            print("Processamento desta URL falhou. Indo para a próxima.")

def modo_emocao_em_lote():
    """Gerenciador da fila de URLs para o modo Emoção."""
    ARQUIVO_URLS = os.path.join(PASTA_LOGS, "urls.txt")
    if not os.path.exists(ARQUIVO_URLS): return print(f"ERRO: Arquivo 'urls.txt' não encontrado na pasta logs.")
    
    with open(ARQUIVO_URLS, "r", encoding="utf-8") as f: urls = [line.strip() for line in f if line.strip()]
    if not urls: return print("Arquivo vazio.")
        
    configs = obter_configuracoes_emocoes_lote()
    
    for i, url in enumerate(list(urls)):
        print(f"\n>>> Processando {i + 1}/{len(list(urls))} | {url} <<<")
        try:
            _worker_processo_completo_emocoes(url, configs)
            limpar_pastas_temporarias()
            urls.pop(0) 
            with open(ARQUIVO_URLS, "w", encoding="utf-8") as f:
                for u in urls: f.write(u + "\n")
        except Exception as e:
            log_error(f"Erro na URL {url}\n{traceback.format_exc()}")
            print("Processamento desta URL falhou. Indo para a próxima.")


def limpar_pastas_temporarias():
    """Faz backup dos metadados temporários e apaga a pasta temp para liberar disco."""
    print("\n    Iniciando backup e limpeza da pasta temporária...")
    
    pasta_temp = PASTA_TEMP_GLOBAL
    pasta_backup = PASTA_BACKUP_GLOBAL
    
    # Mapeamento dinâmico e universal usando os caminhos base do sistema
    pastas_para_backup = {
        os.path.join(pasta_temp, "final"): os.path.join(pasta_backup, "final"),
        os.path.join(pasta_temp, "subs"): os.path.join(pasta_backup, "subs"),
        os.path.join(pasta_temp, "subs_ass"): os.path.join(pasta_backup, "subs_ass")
    }

    if os.path.isdir(pasta_temp):
        for origem, destino in pastas_para_backup.items():
            if os.path.isdir(origem):
                os.makedirs(destino, exist_ok=True)
                try:
                    for arquivo in os.listdir(origem):
                        shutil.copy2(os.path.join(origem, arquivo), os.path.join(destino, arquivo))
                except Exception as e:
                    print(f"  > ERRO no backup de '{origem}': {e}")

        try:
            shutil.rmtree(pasta_temp)
            print(f"    Limpeza concluída.")
        except OSError as e: print(f"    Erro ao limpar: {e}")


# ====================================================================
# PONTO DE ENTRADA DO SCRIPT
# ====================================================================

def exibir_menu_principal():
    print("="*60 + "\n      AutoClipper v5.0.0\n" + "="*60)
    print("  [1] Processo Completo (URL -> Palavras-Chave)")
    print("  [2] Processo Completo (URL -> Emoções)")
    print("  [3] Ajustar/Regerar Legenda de um Clipe Específico")
    print("  [4] Sair\n  [5] Limpar Pastas Temporárias")
    print("  --- Modos em Lote ---")
    print("  [6] Processar em Lote (Palavras-Chave)\n  [7] Processar em Lote (Emoção)")
    while True:
        try: return int(input("Digite sua escolha: "))
        except ValueError: print("Opção inválida.")

def main():
    try:
        start_time = time.time()
        escolha = exibir_menu_principal()

        opcoes = {
            1: modo_processo_completo, 2: modo_processo_completo_emocoes, 
            3: modo_ajuste, 5: limpar_pastas_temporarias, 
            6: modo_processo_em_lote, 7: modo_emocao_em_lote
        }
        
        if escolha == 4: return print("Saindo...")
        elif escolha in opcoes: opcoes[escolha]()
        else: return print("Opção inválida.")

        if escolha in [1, 2, 6, 7]:
            print(f"\nTempo total: {int((time.time() - start_time) // 60)}m {int((time.time() - start_time) % 60)}s.")
            if input("\nDeseja apagar pastas temporárias? [s/n]: ").lower() in ['s', 'sim']: limpar_pastas_temporarias()

    except Exception as e:
        log_error(traceback.format_exc())
        print("\n!!! ERRO INESPERADO !!! Detalhes em logs/error_log.txt")

if __name__ == "__main__":
    main()