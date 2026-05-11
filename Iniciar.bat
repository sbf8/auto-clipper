@echo off
:: Forca o terminal a trabalhar na mesma pasta onde este arquivo .bat esta salvo
cd /d "%~dp0"

chcp 65001 >nul
title AutoClipper v5.0.0

:: INJECAO DO FFMPEG
set PATH=%~dp0bin;%PATH%

if not exist venv\Scripts\activate.bat (
    color 0C
    echo [!] AMBIENTE VIRTUAL NAO ENCONTRADO!
    echo O projeto ainda nao foi instalado na sua maquina.
    echo Por favor, execute o arquivo "Instalar.bat" primeiro.
    echo.
    pause
    exit /b
)

call venv\Scripts\activate.bat
color 0F
cls 

python src\autoclipper.py

pause