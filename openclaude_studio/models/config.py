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
    system_prompt: str = ""
    append_system_prompt: str = ""
    extra_args: str = ""
    environment: dict[str, str] = field(default_factory=dict)
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


@dataclass
class AppConfig:
    openclaude: OpenClaudeConfig = field(default_factory=OpenClaudeConfig)
    appearance: AppearanceConfig = field(default_factory=AppearanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "AppConfig":
        openclaude = payload.get("openclaude", {})
        appearance = payload.get("appearance", {})
        logging = payload.get("logging", {})
        return cls(
            openclaude=OpenClaudeConfig(
                executable=openclaude.get("executable", "openclaude"),
                working_directory=openclaude.get("working_directory", ""),
                model=openclaude.get("model", ""),
                system_prompt=openclaude.get("system_prompt", ""),
                append_system_prompt=openclaude.get("append_system_prompt", ""),
                extra_args=openclaude.get("extra_args", ""),
                environment=dict(openclaude.get("environment", {})),
                print_options=PrintOptions(**openclaude.get("print_options", {})),
            ),
            appearance=AppearanceConfig(**appearance),
            logging=LoggingConfig(**logging),
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
