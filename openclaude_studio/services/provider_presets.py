from __future__ import annotations


PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "Anthropic": {
        "ANTHROPIC_API_KEY": "sk-ant-your-key-here",
        "ANTHROPIC_MODEL": "claude-sonnet-4-5",
    },
    "OpenAI Compatible": {
        "CLAUDE_CODE_USE_OPENAI": "1",
        "OPENAI_API_KEY": "sk-your-key-here",
        "OPENAI_MODEL": "gpt-4o",
        "OPENAI_BASE_URL": "https://api.openai.com/v1",
    },
    "Ollama": {
        "CLAUDE_CODE_USE_OPENAI": "1",
        "OPENAI_BASE_URL": "http://localhost:11434/v1",
        "OPENAI_API_KEY": "ollama",
        "OPENAI_MODEL": "llama3.2",
    },
    "LM Studio": {
        "CLAUDE_CODE_USE_OPENAI": "1",
        "OPENAI_BASE_URL": "http://localhost:1234/v1",
        "OPENAI_API_KEY": "lmstudio",
        "OPENAI_MODEL": "your-model-id",
    },
    "Gemini": {
        "CLAUDE_CODE_USE_GEMINI": "1",
        "GEMINI_API_KEY": "your-gemini-key",
        "GEMINI_MODEL": "gemini-2.0-flash",
    },
    "GitHub Models": {
        "CLAUDE_CODE_USE_GITHUB": "1",
        "GITHUB_TOKEN": "ghp_your-token-here",
    },
}


def preset_names() -> list[str]:
    return list(PROVIDER_PRESETS.keys())


def preset_to_text(name: str) -> str:
    env = PROVIDER_PRESETS.get(name, {})
    return "\n".join(f"{key}={value}" for key, value in env.items())
