"""
Restriction / filter engine for Windows AI Agent.

Users can adjust safety levels, blocked command patterns, allowed tools,
path allow/deny lists, and confirmation requirements at runtime or via config.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# Preset levels
# ---------------------------------------------------------------------------

LEVEL_PRESETS: Dict[str, Dict[str, Any]] = {
    "strict": {
        "description": "Maximum safety – almost everything requires confirmation or is blocked",
        "safe_mode": True,
        "require_confirm_write": True,
        "require_confirm_shell": True,
        "allow_shell": True,
        "allow_write": True,
        "allow_read": True,
        "max_read_bytes": 20_000,
        "max_command_timeout": 30,
        "blocked_patterns": [
            r"format\s+",
            r"del\s+/s",
            r"rmdir\s+/s",
            r"rd\s+/s",
            r"remove-item\s+-recurse",
            r"shutdown",
            r"restart-computer",
            r"stop-computer",
            r"reg\s+delete",
            r"net\s+user",
            r"net\s+localgroup",
            r"bcdedit",
            r"diskpart",
            r"cipher\s+/w",
            r"takeown",
            r"icacls\s+.*\/grant",
        ],
        "blocked_tools": [],
        "allowed_path_prefixes": [],
        "denied_path_prefixes": [
            r"C:\\Windows\\System32",
            r"C:\\Windows\\SysWOW64",
            r"%SystemRoot%",
        ],
    },
    "balanced": {
        "description": "Default – blocks destructive commands, allows normal file/shell work",
        "safe_mode": True,
        "require_confirm_write": False,
        "require_confirm_shell": False,
        "allow_shell": True,
        "allow_write": True,
        "allow_read": True,
        "max_read_bytes": 50_000,
        "max_command_timeout": 60,
        "blocked_patterns": [
            r"format\s+",
            r"del\s+/s",
            r"rmdir\s+/s",
            r"rd\s+/s",
            r"remove-item\s+-recurse",
            r"shutdown",
            r"restart-computer",
            r"stop-computer",
            r"reg\s+delete",
        ],
        "blocked_tools": [],
        "allowed_path_prefixes": [],
        "denied_path_prefixes": [],
    },
    "permissive": {
        "description": "Relaxed – only the most dangerous OS commands are blocked",
        "safe_mode": True,
        "require_confirm_write": False,
        "require_confirm_shell": False,
        "allow_shell": True,
        "allow_write": True,
        "allow_read": True,
        "max_read_bytes": 200_000,
        "max_command_timeout": 120,
        "blocked_patterns": [
            r"format\s+c:",
            r"format\s+[a-z]:",
            r"shutdown\s+/s",
            r"shutdown\s+/r",
        ],
        "blocked_tools": [],
        "allowed_path_prefixes": [],
        "denied_path_prefixes": [],
    },
    "unrestricted": {
        "description": "No filters – full access (use with extreme caution)",
        "safe_mode": False,
        "require_confirm_write": False,
        "require_confirm_shell": False,
        "allow_shell": True,
        "allow_write": True,
        "allow_read": True,
        "max_read_bytes": 1_000_000,
        "max_command_timeout": 300,
        "blocked_patterns": [],
        "blocked_tools": [],
        "allowed_path_prefixes": [],
        "denied_path_prefixes": [],
    },
}


@dataclass
class Restrictions:
    """Runtime restriction state. Can be loaded from / saved to config."""

    level: str = "balanced"
    safe_mode: bool = True
    require_confirm_write: bool = False
    require_confirm_shell: bool = False
    allow_shell: bool = True
    allow_write: bool = True
    allow_read: bool = True
    max_read_bytes: int = 50_000
    max_command_timeout: int = 60
    blocked_patterns: List[str] = field(default_factory=list)
    blocked_tools: List[str] = field(default_factory=list)
    allowed_path_prefixes: List[str] = field(default_factory=list)
    denied_path_prefixes: List[str] = field(default_factory=list)
    pending_confirmations: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if self.level in LEVEL_PRESETS and not self.blocked_patterns:
            self.apply_level(self.level, keep_custom=False)

    def apply_level(self, level: str, keep_custom: bool = True) -> str:
        level = level.lower().strip()
        if level not in LEVEL_PRESETS:
            return f"Unknown level '{level}'. Available: {', '.join(LEVEL_PRESETS)}"
        preset = LEVEL_PRESETS[level]
        self.level = level
        self.safe_mode = preset["safe_mode"]
        self.require_confirm_write = preset["require_confirm_write"]
        self.require_confirm_shell = preset["require_confirm_shell"]
        self.allow_shell = preset["allow_shell"]
        self.allow_write = preset["allow_write"]
        self.allow_read = preset["allow_read"]
        self.max_read_bytes = preset["max_read_bytes"]
        self.max_command_timeout = preset["max_command_timeout"]
        if not keep_custom or not self.blocked_patterns:
            self.blocked_patterns = list(preset["blocked_patterns"])
        if not keep_custom or not self.blocked_tools:
            self.blocked_tools = list(preset["blocked_tools"])
        if not keep_custom:
            self.allowed_path_prefixes = list(preset["allowed_path_prefixes"])
            self.denied_path_prefixes = list(preset["denied_path_prefixes"])
        return f"Restriction level set to '{level}': {preset['description']}"

    def block_pattern(self, pattern: str) -> str:
        pattern = pattern.strip()
        if not pattern:
            return "Empty pattern ignored."
        if pattern not in self.blocked_patterns:
            self.blocked_patterns.append(pattern)
            return f"Added blocked pattern: {pattern}"
        return f"Pattern already blocked: {pattern}"

    def unblock_pattern(self, pattern: str) -> str:
        pattern = pattern.strip()
        if pattern in self.blocked_patterns:
            self.blocked_patterns.remove(pattern)
            return f"Removed blocked pattern: {pattern}"
        for p in list(self.blocked_patterns):
            if p.lower() == pattern.lower():
                self.blocked_patterns.remove(p)
                return f"Removed blocked pattern: {p}"
        return f"Pattern not found in block list: {pattern}"

    def block_tool(self, tool_name: str) -> str:
        name = tool_name.strip().lower()
        if name not in self.blocked_tools:
            self.blocked_tools.append(name)
            return f"Tool '{name}' is now blocked."
        return f"Tool '{name}' was already blocked."

    def unblock_tool(self, tool_name: str) -> str:
        name = tool_name.strip().lower()
        if name in self.blocked_tools:
            self.blocked_tools.remove(name)
            return f"Tool '{name}' is now allowed."
        return f"Tool '{name}' was not blocked."

    def set_flag(self, name: str, value: bool) -> str:
        name = name.lower().replace("-", "_")
        mapping = {
            "safe_mode": "safe_mode",
            "require_confirm_write": "require_confirm_write",
            "require_confirm_shell": "require_confirm_shell",
            "allow_shell": "allow_shell",
            "allow_write": "allow_write",
            "allow_read": "allow_read",
        }
        if name not in mapping:
            return f"Unknown flag. Available: {', '.join(mapping)}"
        setattr(self, mapping[name], bool(value))
        return f"Set {mapping[name]} = {bool(value)}"

    def is_tool_allowed(self, tool_name: str) -> tuple[bool, str]:
        name = tool_name.lower()
        if name in self.blocked_tools:
            return False, f"Tool '{tool_name}' is blocked by current restrictions."
        if name == "run_command" and not self.allow_shell:
            return False, "Shell commands are disabled (allow_shell=False)."
        if name == "write_file" and not self.allow_write:
            return False, "File writes are disabled (allow_write=False)."
        if name == "read_file" and not self.allow_read:
            return False, "File reads are disabled (allow_read=False)."
        return True, ""

    def is_command_allowed(self, command: str) -> tuple[bool, str]:
        if not self.safe_mode and self.level == "unrestricted":
            return True, ""
        lower = command.lower()
        for pat in self.blocked_patterns:
            try:
                if re.search(pat, lower, re.IGNORECASE):
                    return False, (
                        f"Blocked by restriction filter (pattern: {pat}). "
                        f"Current level: {self.level}. "
                        "Use 'restrictions unblock <pattern>' or set a lower level if you are sure."
                    )
            except re.error:
                if pat.lower() in lower:
                    return False, f"Blocked by restriction filter (substring: {pat})."
        return True, ""

    def is_path_allowed(self, path: str) -> tuple[bool, str]:
        try:
            resolved = str(Path(path).expanduser().resolve())
        except Exception:
            resolved = path
        for prefix in self.denied_path_prefixes:
            expanded = os_expand(prefix)
            if resolved.lower().startswith(expanded.lower()):
                return False, f"Path denied by restriction (prefix: {prefix})."
        if self.allowed_path_prefixes:
            ok = False
            for prefix in self.allowed_path_prefixes:
                expanded = os_expand(prefix)
                if resolved.lower().startswith(expanded.lower()):
                    ok = True
                    break
            if not ok:
                return False, "Path not in allowed_path_prefixes list."
        return True, ""

    def summary(self) -> str:
        lines = [
            f"Restriction level : {self.level}",
            f"Description       : {LEVEL_PRESETS.get(self.level, {}).get('description', '')}",
            f"safe_mode         : {self.safe_mode}",
            f"allow_shell       : {self.allow_shell}",
            f"allow_write       : {self.allow_write}",
            f"allow_read        : {self.allow_read}",
            f"require_confirm_write : {self.require_confirm_write}",
            f"require_confirm_shell : {self.require_confirm_shell}",
            f"max_read_bytes    : {self.max_read_bytes}",
            f"max_command_timeout: {self.max_command_timeout}s",
            f"blocked_tools     : {self.blocked_tools or '(none)'}",
            f"blocked_patterns  : {len(self.blocked_patterns)} pattern(s)",
        ]
        if self.blocked_patterns:
            for p in self.blocked_patterns[:12]:
                lines.append(f"  - {p}")
            if len(self.blocked_patterns) > 12:
                lines.append(f"  ... and {len(self.blocked_patterns) - 12} more")
        if self.denied_path_prefixes:
            lines.append(f"denied_paths      : {self.denied_path_prefixes}")
        if self.allowed_path_prefixes:
            lines.append(f"allowed_paths     : {self.allowed_path_prefixes}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("pending_confirmations", None)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Restrictions":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        filtered = {k: v for k, v in data.items() if k in known and k != "pending_confirmations"}
        return cls(**filtered)


def os_expand(path: str) -> str:
    import os
    return os.path.expandvars(os.path.expanduser(path))


def available_levels() -> str:
    lines = ["Available restriction levels:"]
    for name, preset in LEVEL_PRESETS.items():
        lines.append(f"  {name:12} – {preset['description']}")
    return "\n".join(lines)
