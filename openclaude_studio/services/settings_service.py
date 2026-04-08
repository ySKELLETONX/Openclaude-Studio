from __future__ import annotations

import json
from pathlib import Path

from openclaude_studio.models.config import AppConfig, AppPaths


class SettingsService:
    def __init__(self) -> None:
        root = Path.cwd()
        data_dir = root / "data"
        self.paths = AppPaths(
            root=root,
            data_dir=data_dir,
            config_file=data_dir / "config.json",
            conversations_dir=data_dir / "conversations",
            logs_dir=data_dir / "logs",
            crash_dir=data_dir / "logs" / "crashes",
            exports_dir=data_dir / "exports",
            recovery_dir=data_dir / "recovery",
            session_state_file=data_dir / "recovery" / "last_state.json",
            telemetry_file=data_dir / "logs" / "telemetry.jsonl",
            languages_dir=root / "languages",
        )
        self._ensure_dirs()
        self._config = self.load()

    def _ensure_dirs(self) -> None:
        for path in (
            self.paths.data_dir,
            self.paths.conversations_dir,
            self.paths.logs_dir,
            self.paths.crash_dir,
            self.paths.exports_dir,
            self.paths.recovery_dir,
            self.paths.languages_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppConfig:
        if not self.paths.config_file.exists():
            config = AppConfig()
            self.save(config)
            return config
        payload = json.loads(self.paths.config_file.read_text(encoding="utf-8"))
        return AppConfig.from_dict(payload)

    def save(self, config: AppConfig | None = None) -> None:
        if config is not None:
            self._config = config
        self.paths.config_file.write_text(
            json.dumps(self._config.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def config(self) -> AppConfig:
        return self._config
