"""
Configuration management for Windows AI Agent
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict, field


DEFAULT_CONFIG = {
    "llm_provider": "openai",          # openai | ollama | none
    "openai_api_key": "",
    "openai_model": "gpt-4o-mini",
    "openai_base_url": "https://api.openai.com/v1",
    "ollama_base_url": "http://localhost:11434",
    "ollama_model": "llama3.2",
    "max_iterations": 20,
    "temperature": 0.2,
    "system_prompt": (
        "You are a helpful AI agent running on a Windows PC. "
        "You can use tools to inspect the system, run commands, read/write files, "
        "and help the user accomplish tasks. Always confirm before destructive actions. "
        "Respond clearly and take action when requested."
    ),
    "safe_mode": True,                 # Ask before shell commands that modify system
    "working_directory": "",           # Empty = current dir
    "log_level": "INFO",
}


@dataclass
class AgentConfig:
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    max_iterations: int = 20
    temperature: float = 0.2
    system_prompt: str = DEFAULT_CONFIG["system_prompt"]
    safe_mode: bool = True
    working_directory: str = ""
    log_level: str = "INFO"

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AgentConfig":
        config_path = path or cls._default_path()
        data = dict(DEFAULT_CONFIG)

        # Environment variables override
        env_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("WAA_OPENAI_API_KEY")
        if env_key:
            data["openai_api_key"] = env_key

        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                data.update(file_data)
            except Exception as e:
                print(f"Warning: could not load config from {config_path}: {e}")

        # Filter to known fields
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def save(self, path: Optional[Path] = None) -> None:
        config_path = path or self._default_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)
        print(f"Config saved to {config_path}")

    @staticmethod
    def _default_path() -> Path:
        # Prefer user AppData on Windows
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            return base / "WindowsAIAgent" / "config.json"
        return Path.home() / ".windows_ai_agent" / "config.json"


def get_config() -> AgentConfig:
    return AgentConfig.load()
