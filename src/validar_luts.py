# ====================================================================
# AUTOCLIPPER versão 5.0.0 | UTILITÁRIO DE VALIDAÇÃO DE LUTS
# ====================================================================
# Descrição: Este script testa todos os arquivos de Color Grading (.cube)
# presentes na pasta 'luts' contra um vídeo de amostra. Ele usa um dry-run
# do FFmpeg para garantir que o LUT não está corrompido ou em um formato
# não suportado, evitando quebras no processamento principal de monetização.
# ====================================================================

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import os
import subprocess
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
PASTA_LUTS = str(BASE_DIR / "luts")
VIDEO_AMOSTRA = str(BASE_DIR / "amostra.mp4")


# ====================================================================
# LÓGICA DE NEGÓCIO PRINCIPAL: TESTE DE ESTRESSE FFmpeg
# ====================================================================

def validar_luts():
    """
    Itera sobre a pasta de LUTs e executa uma renderização nula no FFmpeg
    para verificar a integridade estrutural de cada arquivo .cube.
    """
    print("="*60)
    print("      VALIDADOR DE COMPATIBILIDADE DE LUTS | AutoClipper")
    print("="*60)

    # Verifica se o vídeo de teste existe na raiz do projeto
    if not os.path.exists(VIDEO_AMOSTRA):
        print(f"\n[!] ERRO: Vídeo de amostra '{os.path.basename(VIDEO_AMOSTRA)}' não encontrado.")
        print(f"    Coloque um vídeo curto chamado 'amostra.mp4' na pasta raiz ({BASE_DIR}).")
        return

    # Verifica se a pasta luts existe e tem conteúdo
    if not os.path.isdir(PASTA_LUTS) or not os.listdir(PASTA_LUTS):
        print(f"\n[!] ERRO: Pasta '{PASTA_LUTS}' está vazia ou não existe.")
        return

    cube_files = sorted([f for f in os.listdir(PASTA_LUTS) if f.lower().endswith('.cube')])
    
    if not cube_files:
        print(f"\n[!] AVISO: Nenhum arquivo .cube encontrado na pasta 'luts'.")
        return

    aprovados = []
    reprovados = []

    print(f"\n-> Encontrados {len(cube_files)} LUTs para testar...\n")

    for i, lut_file in enumerate(cube_files):
        caminho_lut = os.path.join(PASTA_LUTS, lut_file).replace('\\', '/')
        
        # CRÍTICO: Escapa a letra do drive no Windows (ex: C:/ -> C\:/) 
        # Sem isso, o filtro lut3d do FFmpeg quebra ao ler caminhos absolutos.
        caminho_lut_escapado = re.sub(r'([a-zA-Z]):', r'\1\\:', caminho_lut)
        
        filtro_str = f"lut3d=file='{caminho_lut_escapado}'"

        # Comando FFmpeg que processa o vídeo em memória e descarta o output (-f null -)
        command = [
            'ffmpeg', '-y', '-i', VIDEO_AMOSTRA,
            '-vf', filtro_str,
            '-f', 'null', '-'
        ]

        # Formata a string para que os checks de aprovado/reprovado fiquem alinhados
        print(f"  Testando [{i+1:02d}/{len(cube_files):02d}] -> {lut_file[:30].ljust(30)} ... ", end="", flush=True)

        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print("✅ APROVADO")
            aprovados.append(lut_file)
        except subprocess.CalledProcessError:
            print("❌ REPROVADO")
            reprovados.append(lut_file)

    # --- RELATÓRIO FINAL ---
    print("\n" + "="*60)
    print("                  VALIDAÇÃO CONCLUÍDA")
    print("="*60)
    print(f"Resultados: {len(aprovados)} Aprovados | {len(reprovados)} Reprovados\n")

    if reprovados:
        print("--- ⚠️ LUTS REPROVADOS (REMOVA DA PASTA 'luts') ---")
        for r in reprovados:
            print(f"  - {r}")

    if aprovados:
        print("\n--- 🟢 LUTS APROVADOS (100% Compatíveis) ---")
        for a in aprovados:
            print(f"  - {a}")


# ====================================================================
# PONTO DE ENTRADA
# ====================================================================

if __name__ == "__main__":
    try:
        validar_luts()
    except KeyboardInterrupt:
        print("\nValidação cancelada pelo usuário.")