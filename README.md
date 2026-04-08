<div align="center">

# Openclaude Studio

Modern desktop GUI for OpenClaude built with Python and PyQt6.

[English](#english) | [Português do Brasil](#portugues-do-brasil)

</div>

---

## English

Openclaude Studio is a modern desktop GUI for [OpenClaude](https://github.com/Gitlawb/openclaude), built with Python and `PyQt6`.

It brings a Codex / claude.ai inspired experience to OpenClaude with a modern chat interface, persistent conversations, configurable provider integration, transcript export/print, screenshots, and crash-safe logging.

### Features

- Modern desktop chat UI inspired by Codex and claude.ai
- OpenClaude CLI integration using `--print --verbose --output-format stream-json`
- Persistent local chat history with session resume support
- Full provider environment configuration
- OpenClaude print options exposed in the UI
- Tool and event timeline
- Markdown / HTML / TXT export
- Print preview and PDF printing
- Screenshot capture
- Rotating logs and crash reports
- Windows test build with PyInstaller

### Stack

- `PyQt6`
- `qtawesome`
- `markdown-it-py`
- `Pygments`

### Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
python main.py
```

### Windows Test Build

To generate a test `.exe`:

```powershell
.\build_windows.ps1
```

Or manually:

```powershell
pip install -r requirements.txt -r requirements-build.txt
pyinstaller --clean --noconfirm OpenclaudeStudio.spec
```

Expected output:

```text
dist/OpenclaudeStudio.exe
```

### OpenClaude Setup

Install OpenClaude separately:

```bash
npm install -g @gitlawb/openclaude
```

Then open the app and configure:

- executable path
- workspace directory
- model
- environment variables like `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `CLAUDE_CODE_USE_OPENAI`
- print flags such as `--include-partial-messages`, `--include-hook-events`, `--bare`

### Data Layout

The app stores project-local data in `data/`:

- `data/config.json`
- `data/conversations/*.json`
- `data/logs/app.log`
- `data/logs/crashes/*.log`
- `data/exports/*`

### Notes

- This version focuses on the stable OpenClaude CLI headless flow.
- The code structure is ready for a future gRPC client if you want to expand beyond CLI integration.
- On the first run of the compiled app, make sure `openclaude` is installed globally or configure the executable path in Settings.

---

## Portugues do Brasil

Openclaude Studio é uma interface desktop moderna para o [OpenClaude](https://github.com/Gitlawb/openclaude), desenvolvida em Python com `PyQt6`.

Ele traz uma experiência inspirada no Codex e no claude.ai para o OpenClaude, com interface de chat moderna, conversas persistentes, integração configurável com providers, exportação/impressão de transcrições, captura de tela e logs com tratamento de crash.

### Recursos

- Interface desktop moderna inspirada no Codex e claude.ai
- Integração com a CLI do OpenClaude usando `--print --verbose --output-format stream-json`
- Histórico local persistente com suporte a retomada de sessão
- Configuração completa de providers por variáveis de ambiente
- Opções de print do OpenClaude expostas na interface
- Linha do tempo de eventos e ferramentas
- Exportação em Markdown / HTML / TXT
- Visualização de impressão e geração de PDF
- Captura de screenshot
- Logs rotativos e relatórios de crash
- Build de teste para Windows com PyInstaller

### Tecnologias

- `PyQt6`
- `qtawesome`
- `markdown-it-py`
- `Pygments`

### Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Execução

```bash
python main.py
```

### Build de Teste no Windows

Para gerar um `.exe` de teste:

```powershell
.\build_windows.ps1
```

Ou manualmente:

```powershell
pip install -r requirements.txt -r requirements-build.txt
pyinstaller --clean --noconfirm OpenclaudeStudio.spec
```

Saída esperada:

```text
dist/OpenclaudeStudio.exe
```

### Configuração do OpenClaude

Instale o OpenClaude separadamente:

```bash
npm install -g @gitlawb/openclaude
```

Depois abra o app e configure:

- caminho do executável
- diretório de trabalho
- modelo
- variáveis de ambiente como `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `CLAUDE_CODE_USE_OPENAI`
- flags de print como `--include-partial-messages`, `--include-hook-events`, `--bare`

### Estrutura de Dados

O app salva dados locais do projeto em `data/`:

- `data/config.json`
- `data/conversations/*.json`
- `data/logs/app.log`
- `data/logs/crashes/*.log`
- `data/exports/*`

### Observações

- Esta versão foca no fluxo headless estável da CLI do OpenClaude.
- A estrutura do código já está preparada para um futuro cliente gRPC, caso você queira expandir além da integração por CLI.
- Na primeira execução da versão compilada, garanta que o `openclaude` esteja instalado globalmente ou configure o caminho do executável nas Settings.
