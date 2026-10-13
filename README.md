# Windows AI Agent

A from-scratch AI agent for Windows PCs with built-in **prerequisite checker** and **installer**.

## Features

- Interactive CLI agent that can reason and use tools
- Built-in tools: list directories, read/write files, run shell commands, system info, file search
- Prerequisite checker (Python version, packages, Windows environment, disk, network)
- One-click style installer (batch + PowerShell) including automatic Python bootstrap via winget
- Optional standalone EXE build via PyInstaller
- Supports OpenAI API, Ollama (local models), and offline rule-based mode
- Safe mode that blocks obviously destructive commands
- Configuration stored in `%APPDATA%\WindowsAIAgent\config.json`

## Quick Start

### 1. Install Prerequisites (recommended)

Open **PowerShell as Administrator** in this folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_prerequisites.ps1
```

This script will:

- Detect Python 3.9+
- Install Python via `winget` if missing
- Ensure pip is available
- Install all packages from `requirements.txt`
- Create the launcher scripts (`run_agent.bat`, `check_prereqs.bat`, etc.)

### 2. Alternative (Python already installed)

```bat
install.bat
```

or:

```bat
python -m src.installer
```

### 3. Verify

```bat
check_prereqs.bat
```

or:

```bat
python -m src.prereq_checker
```

### 4. Run the agent

```bat
run_agent.bat
```

or:

```bat
python -m src.main
```

### 5. (Optional) Configure an LLM

**Option A – OpenAI**

```bat
set OPENAI_API_KEY=sk-your-key-here
python -m src.main
```

Or edit `%APPDATA%\WindowsAIAgent\config.json` and set `"openai_api_key"`.

**Option B – Local Ollama**

1. Install Ollama from https://ollama.com
2. `ollama pull llama3.2`
3. In config set `"llm_provider": "ollama"`

**Option C – Offline**

No key needed. The agent falls back to simple commands (`help`, `system info`, `list`, `read`, `run`).

## Project Layout

```
WindowsAIAgent/
├── requirements.txt
├── README.md
├── .gitignore
├── run_agent.bat
├── check_prereqs.bat
├── install.bat
├── build_exe.bat
├── scripts/
│   ├── install.ps1
│   └── install_prerequisites.ps1   # Full bootstrap (Python + packages)
├── src/
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── agent.py           # Core reasoning loop
│   ├── tools.py           # Tool registry & Windows tools
│   ├── config.py          # Configuration
│   ├── prereq_checker.py  # Prerequisite checker
│   └── installer.py       # Installer logic
├── tests/
└── docs/
```

## Building a Standalone EXE

```bat
build_exe.bat
```

or:

```bat
python -m src.installer --exe
```

The EXE will appear under `dist\WindowsAIAgent.exe`.

## Safety

- `safe_mode` is enabled by default. Destructive-looking commands are blocked.
- Disable with `--no-safe` or by setting `"safe_mode": false` in config (use with caution).

## License

MIT – free to use and modify.
