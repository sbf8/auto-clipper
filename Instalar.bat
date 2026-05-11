@echo off
:: Forca o terminal a trabalhar na mesma pasta onde este arquivo .bat esta salvo
cd /d "%~dp0"

chcp 65001 >nul
title Instalador AutoClipper v5.0.0
color 0A

echo ===========================================================
echo            INSTALADOR DO AUTOCLIPPER V5.0.0
echo ===========================================================
echo.

echo [1/5] Procurando o Python 3.10 no sistema...

set PYTHON_CMD=

py -3.10 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py -3.10
    echo - Python 3.10 detectado pelo Launcher Oficial!
    goto :criar_venv
)

for /f "delims=" %%i in ('where python 2^>nul') do (
    echo "%%i" | findstr /i /v "WindowsApps" >nul
    if not errorlevel 1 (
        "%%i" --version 2>nul | findstr /R "3\.10" >nul
        if not errorlevel 1 (
            set PYTHON_CMD="%%i"
            echo - Python 3.10 detectado no caminho: %%i
            goto :criar_venv
        )
    )
)

color 0C
echo [!] ERRO CRITICO: Python 3.10 nao encontrado!
pause
exit /b

:criar_venv
echo.
echo [2/5] Criando o ambiente virtual isolado (venv)...
%PYTHON_CMD% -m venv venv
echo.

echo [3/5] Ativando a venv e atualizando instaladores...
if not exist venv\Scripts\activate.bat (
    color 0C
    echo [!] Erro ao criar venv. Verifique permissoes de pasta.
    pause
    exit /b
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
echo.

echo [4/5] Instalando o motor da Inteligencia Artificial (PyTorch)...
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
echo.

echo [5/5] Instalando as ferramentas de video e metadados...
pip install -r requirements.txt
echo.

echo ===========================================================
echo             INSTALACAO CONCLUIDA COM SUCESSO!
echo ===========================================================
pause