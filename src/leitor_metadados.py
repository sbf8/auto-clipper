# ====================================================================
# AUTOCLIPPER versão 5.0.0 | UTILITÁRIO DE LEITURA DE METADADOS
# ====================================================================
# Descrição: Ferramenta de auditoria técnica. Lê os arquivos de mídia
# e extrai um relatório limpo e organizado com as propriedades cruciais
# (Codec, Bitrate, Resolução, FPS) usando a biblioteca 'pymediainfo'.
# ====================================================================

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
from pathlib import Path
import inspect
from pymediainfo import MediaInfo

# --- 1. RESOLUÇÃO DO DIRETÓRIO RAIZ (BASE_DIR) ---
try:
    CURRENT_DIR = Path(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
    BASE_DIR = CURRENT_DIR.parent 
except Exception:
    BASE_DIR = Path(os.getcwd())


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL: EXTRAÇÃO LIMPA
# ====================================================================

def ler_metadados(caminho_do_video):
    """
    Analisa o arquivo de mídia e imprime um relatório limpo focando 
    nas propriedades mais relevantes para edição de vídeo para redes sociais.
    """
    if not os.path.exists(caminho_do_video):
        print(f"\n[!] ERRO: Arquivo não encontrado no caminho:\n{caminho_do_video}")
        return

    try:
        print("\n" + "="*50)
        print(f"📄 RELATÓRIO DE METADADOS: {os.path.basename(caminho_do_video)}")
        print("="*50)

        media_info = MediaInfo.parse(caminho_do_video)

        if not media_info.tracks:
            print("[!] Não foi possível extrair os metadados. Arquivo corrompido ou formato não suportado.")
            return

        # Filtra e exibe os dados mais importantes organizados por categoria
        for track in media_info.tracks:
            if track.track_type == "General":
                print("\n📁 [GERAL]")
                print(f"  ├─ Formato: {track.format}")
                print(f"  ├─ Tamanho do Arquivo: {track.file_size_string}")
                print(f"  └─ Duração Total: {track.duration_string3}")
                
            elif track.track_type == "Video":
                print("\n🎬 [VÍDEO]")
                print(f"  ├─ Codec / Formato: {track.format} ({track.codec_id})")
                print(f"  ├─ Resolução: {track.width} x {track.height} (Proporção {track.display_aspect_ratio_string})")
                print(f"  ├─ Taxa de Quadros (FPS): {track.frame_rate} fps")
                print(f"  ├─ Bitrate: {track.bit_rate_string if track.bit_rate_string else 'Variável/Desconhecido'}")
                print(f"  └─ Espaço de Cor: {track.color_space}")

            elif track.track_type == "Audio":
                print("\n🎵 [ÁUDIO]")
                print(f"  ├─ Codec / Formato: {track.format}")
                print(f"  ├─ Canais: {track.channel_s}_canais")
                print(f"  ├─ Taxa de Amostragem: {track.sampling_rate} Hz")
                print(f"  └─ Bitrate: {track.bit_rate_string if track.bit_rate_string else 'Variável/Desconhecido'}")

        print("\n" + "="*50 + "\n")

    except Exception as e:
        print(f"\n[!] Ocorreu um erro fatal ao processar a mídia: {e}")


# ====================================================================
# PONTO DE ENTRADA / MENU INTERATIVO
# ====================================================================

if __name__ == "__main__":
    print("="*60)
    print("      Auditoria de Mídia | AutoClipper v5.0.0")
    print("="*60)
    
    while True:
        print("Dica: Você pode arrastar e soltar o vídeo diretamente aqui no terminal.")
        entrada = input("\n=> Insira o caminho do vídeo (ou digite 'sair'): ").strip()
        
        if entrada.lower() in ['sair', 'exit', 'quit']:
            print("Encerrando utilitário...")
            break
            
        # Limpa as aspas invisíveis que o Windows adiciona ao "arrastar e soltar" arquivos no terminal
        caminho_limpo = entrada.replace('"', '').replace("'", "")
        
        ler_metadados(caminho_limpo)