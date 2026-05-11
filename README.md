<div align="center">
  
  <h1>🎬 AutoClipper v5.0.0</h1>
  
  **Automação Inteligente para Cortes Virais, Legendagem Dinâmica (.ass) e Inteligência Artificial**

  [![Python](https://img.shields.io/badge/Python-3.10-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![PyTorch](https://img.shields.io/badge/PyTorch-CUDA_12.1-EE4C2C.svg?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-success.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
  [![Suporte: WhatsApp](https://img.shields.io/badge/Suporte-WhatsApp-25D366?style=for-the-badge&logo=whatsapp&logoColor=white)](https://wa.me/5534984241729)

  Uma ferramenta de código aberto que transforma vídeos longos em clipes curtos (Shorts/Reels/TikTok) de forma 100% autônoma. 
</div>

<br>

O **AutoClipper** utiliza Inteligência Artificial local para detectar picos acústicos de emoção, transcrever áudios com extrema precisão e aplicar legendas cinematográficas avançadas, prontas para monetização. Se você precisa de suporte ou quer falar sobre o projeto, **[clique aqui para me chamar no WhatsApp](https://wa.me/5534984241729)**.

---

## 📑 Índice
- [Principais Recursos](#-principais-recursos)
- [Demonstração](#-demonstração)
- [Pré-requisitos](#pre-requisitos)
- [Instalação](#-instalação)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Licença](#-licença)

---

## ✨ Principais Recursos

* 🧠 **Inteligência Artificial Local:** Processamento via `WhisperX` e `PyTorch`, garantindo alinhamento perfeito de palavras sem depender de APIs pagas. Suporte dinâmico a processamento via CPU ou GPU (CUDA).
* 🎯 **Motores de Decisão Duplos:**
  * **Modo Emoção:** O "Cérebro Auditivo" utiliza a biblioteca `Librosa` para rastrear ondas sonoras e isolar gritos, risadas ou ênfases verbais, respeitando o silêncio e as pausas naturais.
  * **Modo Palavras-Chave:** Varredura textual inteligente para cortes focados em nichos específicos.
* 🎞️ **Legendagem Cinematográfica (.ASS):** Esqueça as legendas estáticas. O motor de renderização aplica matemática espacial para gerar efeitos de *Fade*, *Slide In*, *Bounce (Pop)*, *Flip 3D* e *Shear* programaticamente.
* ⚙️ **Automação em Lote (Batch):** Capacidade de ler listas de URLs e orquestrar múltiplos vídeos durante a noite, com autolimpeza de arquivos temporários.
* 🎨 **Pipeline de Color Grading:** Validador integrado de arquivos LUTs (`.cube`) para aplicação de filtros de cor, auxiliando na prevenção de bloqueios de copyright.

---

## 🎥 Demonstração

Veja como é simples e rápido operar o **AutoClipper v5.0.0** direto do seu terminal:

**1. Menu Interativo e Inserção da Mídia** O painel principal oferece opções claras para processos unitários ou em lote. Basta escolher o motor inteligente (ex: Emoções) e colar o link do YouTube.

<img width="939" height="478" alt="Captura de tela 2026-05-11 044736" src="https://github.com/user-attachments/assets/19ad30a5-000b-4bfb-bf77-a7d51a65ad53" />

<br>

**2. Configuração Cinematográfica das Legendas** Você tem controle total sobre a estética visual. Escolha a posição na tela, a densidade de palavras por bloco e aplique dezenas de efeitos de animação dinâmicos (Fade, Slide, Pop, etc.).

<img width="939" height="1018" alt="Captura de tela 2026-05-11 045014" src="https://github.com/user-attachments/assets/81f4f897-1dd2-4ded-9a73-eb9450544414" />

<br>

**3. Pós-Produção e Processamento com IA** Defina ajustes finais para monetização (colorização/edição estrutural) e deixe a máquina trabalhar. O sistema baixa na melhor qualidade, transcreve com WhisperX e executa os cortes automaticamente.

<img width="939" height="1016" alt="Captura de tela 2026-05-11 045041" src="https://github.com/user-attachments/assets/69387c3e-d014-4975-85f0-e6eccbee999f" />

## <a id="pre-requisitos"></a> 🛠️ Pré-requisitos

Para rodar este projeto localmente, você precisará de:

**1. Python 3.10.x**
> Versões mais recentes como 3.12 podem causar conflito com as dependências do PyTorch. Certifique-se de marcar a opção *"Add Python to PATH"* durante a instalação do Python.

**2. FFmpeg**
> Essencial para o processamento de áudio e vídeo. Para não precisar configurar variáveis de ambiente complexas no Windows, basta baixar o `ffmpeg.exe` e o `ffprobe.exe` oficiais e colocá-los dentro de uma pasta chamada `bin/` na raiz deste projeto. O AutoClipper os encontrará automaticamente.

---

## 🚀 Instalação

Escolha o método que melhor se adapta ao seu perfil.

### Opção A: Instalação Automática (Plug & Play)
Recomendado para usuários de Windows que desejam praticidade. O projeto inclui rotinas seguras de automação em lote.

**Passo 1:** Faça o clone do repositório no seu terminal (ou baixe o arquivo ZIP):
```bash
git clone [https://github.com/sbf8/auto-clipper.git](https://github.com/sbf8/auto-clipper.git)

```

**Passo 2:** Adicione os binários do FFmpeg na pasta `bin/`.

**Passo 3:** Dê dois cliques no arquivo **`Instalar.bat`**. 
> Ele fará a verificação da sua versão do Python, criará o ambiente virtual (`venv`) isolado, instalará o PyTorch com suporte a aceleração de hardware (CUDA) e configurará os requisitos automaticamente.

<br>

### Opção B: Instalação Manual (Avançada)
Para quem prefere controle total ou utiliza sistemas baseados em Unix (Linux/Mac).

**Passo 1:** Clone o projeto e entre no diretório:
```bash
git clone https://github.com/sbf8/auto-clipper.git
cd auto-clipper
```

**Passo 2:** Crie e ative um ambiente virtual:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3.10 -m venv venv
source venv/bin/activate
```

**Passo 3:** Instale o PyTorch com suporte a CUDA e depois os requisitos:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

---

## 💻 Como Usar

Com o ambiente devidamente instalado, inicie a interface interativa:

**Para quem usou a Instalação Automática:**
Basta dar dois cliques no arquivo **`Iniciar.bat`**.

**Para quem prefere o Terminal:**
```bash
python src/autoclipper.py
```

No painel interativo, você poderá:
1. Colar a URL do vídeo de origem (YouTube).
2. Selecionar o motor de corte (Emoção ou Palavra-chave).
3. Configurar a estética das legendas (Blocos de texto, posições e dezenas de efeitos de animação).
4. *(Opcional)* Adicionar LUTs ou ativar o modo de Super Reels para juntar os cortes.

---

## 📁 Estrutura do Projeto

A arquitetura foi desenhada para separar a inteligência da mídia bruta:

```text
auto-clipper/
├── bin/                 # Coloque o ffmpeg.exe aqui para uso portátil
├── luts/                # Diretório para os filtros de color grading (.cube)
├── src/                 # Código-fonte principal (Orquestrador, Inteligência, Estilos)
├── temp/                # Pasta de trabalho (Limpa automaticamente via menu)
│   ├── cortes/          # Clipes isolados pré-renderização
│   ├── legendas/        # Arquivos .ass gerados
│   └── subs/            # Transcrições JSON (WhisperX)
├── Instalar.bat         # Automação de setup inteligente (Windows)
├── Iniciar.bat          # Inicializador de uso diário (Windows)
└── requirements.txt     # Dependências de alto nível curadas
```

---

## 📜 Licença

Este projeto é distribuído sob a Licença **MIT**. Você tem a liberdade de usar, modificar e distribuir o código comercialmente, desde que mantenha os avisos de direitos autorais originais.

---
*Desenvolvido com dedicação para a comunidade criativa.*
