from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderPresetDefinition:
    description: str
    environment: dict[str, str]
    suggested_models: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


PROVIDER_PRESETS: dict[str, ProviderPresetDefinition] = {
    "Anthropic": ProviderPresetDefinition(
        description="Direct Anthropic API integration for Claude models.",
        environment={
            "ANTHROPIC_API_KEY": "sk-ant-your-key-here",
            "ANTHROPIC_MODEL": "claude-sonnet-4-5",
        },
        suggested_models=(
            "claude-sonnet-4-5",
            "claude-opus-4-1",
            "claude-3-5-haiku-latest",
        ),
        notes=(
            "Use your Anthropic API key.",
            "Best option when you want direct Claude access.",
        ),
    ),
    "OpenAI Compatible": ProviderPresetDefinition(
        description="OpenAI-compatible API servers, including OpenAI and compatible gateways.",
        environment={
            "CLAUDE_CODE_USE_OPENAI": "1",
            "OPENAI_API_KEY": "sk-your-key-here",
            "OPENAI_MODEL": "gpt-4o",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
        },
        suggested_models=(
            "gpt-4o",
            "gpt-4.1",
            "gpt-4.1-mini",
        ),
        notes=(
            "Works with OpenAI and any provider exposing an OpenAI-compatible endpoint.",
            "If your provider has a custom base URL, change OPENAI_BASE_URL.",
        ),
    ),
    "Ollama": ProviderPresetDefinition(
        description="Local Ollama server using the OpenAI-compatible bridge.",
        environment={
            "CLAUDE_CODE_USE_OPENAI": "1",
            "OPENAI_BASE_URL": "http://localhost:11434/v1",
            "OPENAI_API_KEY": "ollama",
            "OPENAI_MODEL": "llama3.2",
        },
        suggested_models=(
            "llama3.2",
            "qwen2.5-coder",
            "deepseek-coder-v2",
        ),
        notes=(
            "Keep the Ollama server running locally before testing the provider.",
            "OPENAI_API_KEY can stay as a placeholder such as ollama.",
        ),
    ),
    "LM Studio": ProviderPresetDefinition(
        description="Local LM Studio server using its OpenAI-compatible API mode.",
        environment={
            "CLAUDE_CODE_USE_OPENAI": "1",
            "OPENAI_BASE_URL": "http://localhost:1234/v1",
            "OPENAI_API_KEY": "lmstudio",
            "OPENAI_MODEL": "your-model-id",
        },
        suggested_models=(
            "google/gemma-3-12b",
            "qwen/qwen2.5-coder-7b-instruct",
            "meta-llama-3.1-8b-instruct",
        ),
        notes=(
            "Enable the local server in LM Studio first.",
            "Replace OPENAI_MODEL with the exact loaded model identifier.",
        ),
    ),
    "Gemini": ProviderPresetDefinition(
        description="Google Gemini integration using the Gemini provider path.",
        environment={
            "CLAUDE_CODE_USE_GEMINI": "1",
            "GEMINI_API_KEY": "your-gemini-key",
            "GEMINI_MODEL": "gemini-2.0-flash",
        },
        suggested_models=(
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
        ),
        notes=(
            "Use a valid Google AI Studio or Vertex-backed Gemini API key.",
            "Start with Flash for speed and Pro for heavier reasoning.",
        ),
    ),
    "GitHub Models": ProviderPresetDefinition(
        description="GitHub Models integration through your GitHub token.",
        environment={
            "CLAUDE_CODE_USE_GITHUB": "1",
            "GITHUB_TOKEN": "ghp_your-token-here",
        },
        suggested_models=(
            "openai/gpt-4.1",
            "openai/gpt-4o",
            "microsoft/phi-4",
        ),
        notes=(
            "Use a GitHub token with access to GitHub Models.",
            "Model selection may happen on the provider side depending on your setup.",
        ),
    ),
}


def preset_names() -> list[str]:
    return list(PROVIDER_PRESETS.keys())


def preset_to_text(name: str) -> str:
    definition = PROVIDER_PRESETS.get(name)
    if definition is None:
        return ""
    return "\n".join(f"{key}={value}" for key, value in definition.environment.items())


def preset_model_hint(name: str) -> str:
    definition = PROVIDER_PRESETS.get(name)
    if definition is None or not definition.suggested_models:
        return ""
    return definition.suggested_models[0]


def preset_example_text(name: str) -> str:
    definition = PROVIDER_PRESETS.get(name)
    if definition is None:
        return (
            "Select a provider preset to see a ready-to-use environment template,\n"
            "suggested models, and setup notes."
        )

    lines = [definition.description, "", "Environment template:", preset_to_text(name)]
    if definition.suggested_models:
        lines.extend(["", "Suggested models:"])
        lines.extend(f"- {model}" for model in definition.suggested_models)
    if definition.notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"- {note}" for note in definition.notes)
    return "\n".join(lines)
