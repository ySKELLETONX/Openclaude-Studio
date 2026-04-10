from __future__ import annotations

import shutil
import socket
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

from openclaude_studio.models.config import OpenClaudeConfig


@dataclass
class ProviderTestResult:
    ok: bool
    summary: str
    details: list[str]


class ProviderTestService:
    def test(self, config: OpenClaudeConfig) -> ProviderTestResult:
        details: list[str] = []

        executable = self._resolve_executable(config.executable)
        if executable:
            details.append(f"Executable resolved: {executable}")
        elif config.executable:
            details.append(f"Executable configured: {config.executable}")
        if not executable and config.executable not in {"", "openclaude"}:
            details.append("Executable path was not found on PATH; make sure it points to a valid binary.")
        elif not executable and config.executable == "openclaude":
            details.append("OpenClaude executable not found on PATH.")

        required = self._required_keys(config.provider_name)
        missing = [key for key in required if not config.environment.get(key)]
        if missing:
            details.append("Missing required environment variables: " + ", ".join(missing))
        else:
            details.append("Required provider variables look good.")

        base_url = config.environment.get("OPENAI_BASE_URL") or config.environment.get("GEMINI_BASE_URL")
        if base_url:
            details.append(self._test_host(base_url))

        ok = bool(executable) and not missing
        summary = "Connection profile looks ready." if ok else "Configuration still needs attention."
        return ProviderTestResult(ok=ok, summary=summary, details=details)

    def _resolve_executable(self, executable: str) -> str:
        configured = executable.strip() or "openclaude"
        resolved = shutil.which(configured)
        if resolved:
            return resolved
        candidate = Path(configured)
        if candidate.exists():
            return str(candidate.resolve())
        return ""

    def _required_keys(self, provider_name: str) -> list[str]:
        mapping = {
            "Anthropic": ["ANTHROPIC_API_KEY"],
            "OpenAI Compatible": ["CLAUDE_CODE_USE_OPENAI", "OPENAI_API_KEY", "OPENAI_MODEL"],
            "Ollama": ["CLAUDE_CODE_USE_OPENAI", "OPENAI_BASE_URL", "OPENAI_MODEL"],
            "LM Studio": ["CLAUDE_CODE_USE_OPENAI", "OPENAI_BASE_URL", "OPENAI_MODEL"],
            "Gemini": ["CLAUDE_CODE_USE_GEMINI", "GEMINI_API_KEY", "GEMINI_MODEL"],
            "GitHub Models": ["CLAUDE_CODE_USE_GITHUB", "GITHUB_TOKEN"],
        }
        return mapping.get(provider_name, [])

    def _test_host(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            if not host:
                return "Base URL is set but could not be parsed."
            with socket.create_connection((host, port), timeout=2):
                return f"Network check OK: reached {host}:{port}"
        except OSError as exc:
            return f"Network check failed: {exc}"
