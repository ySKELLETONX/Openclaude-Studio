from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class PrintOptions:
    include_partial_messages: bool = True
    include_hook_events: bool = False
    bare_mode: bool = False
    dangerously_skip_permissions: bool = False
    verbose: bool = True
    streamlined_output: bool = True


@dataclass
class OpenClaudeConfig:
    executable: str = "openclaude"
    working_directory: str = ""
    model: str = ""
    provider_name: str = "Custom"
    system_prompt: str = ""
    append_system_prompt: str = ""
    extra_args: str = ""
    environment: dict[str, str] = field(default_factory=dict)
    profiles: dict[str, dict[str, str]] = field(default_factory=dict)
    print_options: PrintOptions = field(default_factory=PrintOptions)


@dataclass
class AppearanceConfig:
    theme: str = "dark"
    accent_color: str = "#4aa3ff"
    font_family: str = "Segoe UI"
    font_size: int = 10


@dataclass
class LoggingConfig:
    level: str = "INFO"
    open_log_on_crash: bool = False
    local_telemetry_enabled: bool = True


@dataclass
class RecoveryConfig:
    restore_last_session: bool = True
    restore_draft: bool = True


@dataclass
class GitConfig:
    enabled: bool = False
    executable: str = "git"
    auto_refresh: bool = True
    workspace_override: str = ""


@dataclass
class LocalizationConfig:
    language_file: str = "en.US.xml"


@dataclass
class DiscordConfig:
    enabled: bool = False
    client_id: str = "1391469843342889010"
    show_workspace: bool = True
    show_provider: bool = True


@dataclass
class AppConfig:
    openclaude: OpenClaudeConfig = field(default_factory=OpenClaudeConfig)
    appearance: AppearanceConfig = field(default_factory=AppearanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    recovery: RecoveryConfig = field(default_factory=RecoveryConfig)
    git: GitConfig = field(default_factory=GitConfig)
    localization: LocalizationConfig = field(default_factory=LocalizationConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "AppConfig":
        openclaude = payload.get("openclaude", {})
        appearance = payload.get("appearance", {})
        logging = payload.get("logging", {})
        recovery = payload.get("recovery", {})
        git = payload.get("git", {})
        localization = payload.get("localization", {})
        discord = payload.get("discord", {})
        return cls(
            openclaude=OpenClaudeConfig(
                executable=openclaude.get("executable", "openclaude"),
                working_directory=openclaude.get("working_directory", ""),
                model=openclaude.get("model", ""),
                provider_name=openclaude.get("provider_name", "Custom"),
                system_prompt=openclaude.get("system_prompt", ""),
                append_system_prompt=openclaude.get("append_system_prompt", ""),
                extra_args=openclaude.get("extra_args", ""),
                environment=dict(openclaude.get("environment", {})),
                profiles=dict(openclaude.get("profiles", {})),
                print_options=PrintOptions(**openclaude.get("print_options", {})),
            ),
            appearance=AppearanceConfig(**appearance),
            logging=LoggingConfig(**logging),
            recovery=RecoveryConfig(**recovery),
            git=GitConfig(**git),
            localization=LocalizationConfig(**localization),
            discord=DiscordConfig(**discord),
        )


@dataclass
class AppPaths:
    root: Path
    data_dir: Path
    config_file: Path
    conversations_dir: Path
    logs_dir: Path
    crash_dir: Path
    exports_dir: Path
    recovery_dir: Path
    session_state_file: Path
    telemetry_file: Path
    languages_dir: Path
