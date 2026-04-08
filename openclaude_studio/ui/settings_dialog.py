from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QInputDialog,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from openclaude_studio.models.config import AppConfig
from openclaude_studio.services.language_service import LanguageService
from openclaude_studio.services.provider_presets import preset_names, preset_to_text
from openclaude_studio.services.provider_test_service import ProviderTestService


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, language_service: LanguageService, parent=None) -> None:
        super().__init__(parent)
        self._language_service = language_service
        self.setWindowTitle(self._l("dialog.settings", "Settings"))
        self.resize(860, 720)
        self._config = config
        self._tester = ProviderTestService()

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_openclaude_tab(), self._l("settings.tab.openclaude", "OpenClaude"))
        self.tabs.addTab(self._build_providers_tab(), self._l("settings.tab.providers", "Providers"))
        self.tabs.addTab(self._build_appearance_tab(), self._l("settings.tab.appearance", "Appearance"))
        self.tabs.addTab(self._build_git_tab(), self._l("settings.tab.git", "Git"))
        self.tabs.addTab(self._build_discord_tab(), "Discord")
        self.tabs.addTab(self._build_advanced_tab(), self._l("settings.tab.safety", "Safety & Logs"))

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(self._l("settings.save", "Save"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self._l("settings.cancel", "Cancel"))
        buttons.accepted.connect(self._handle_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addWidget(buttons)

    def _l(self, key: str, fallback: str) -> str:
        return self._language_service.t(key, fallback)

    def _build_openclaude_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)

        self.executable_edit = QLineEdit(self._config.openclaude.executable)
        browse = QPushButton("Browse")
        browse.clicked.connect(self._browse_executable)
        executable_row = QHBoxLayout()
        executable_row.addWidget(self.executable_edit)
        executable_row.addWidget(browse)

        self.workspace_edit = QLineEdit(self._config.openclaude.working_directory)
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Custom"] + preset_names())
        self.provider_combo.setCurrentText(self._config.openclaude.provider_name or "Custom")
        self.model_edit = QLineEdit(self._config.openclaude.model)
        self.system_prompt_edit = QTextEdit(self._config.openclaude.system_prompt)
        self.append_system_prompt_edit = QTextEdit(self._config.openclaude.append_system_prompt)
        self.extra_args_edit = QLineEdit(self._config.openclaude.extra_args)

        self.partial_check = QCheckBox("Include partial messages")
        self.partial_check.setChecked(self._config.openclaude.print_options.include_partial_messages)
        self.hooks_check = QCheckBox("Include hook events")
        self.hooks_check.setChecked(self._config.openclaude.print_options.include_hook_events)
        self.bare_check = QCheckBox("Bare mode")
        self.bare_check.setChecked(self._config.openclaude.print_options.bare_mode)
        self.skip_permissions_check = QCheckBox("Dangerously skip permissions")
        self.skip_permissions_check.setChecked(self._config.openclaude.print_options.dangerously_skip_permissions)
        self.streamlined_check = QCheckBox("Use streamlined output")
        self.streamlined_check.setChecked(self._config.openclaude.print_options.streamlined_output)
        test_button = QPushButton("Test provider / connection")
        test_button.clicked.connect(self._test_provider)

        form.addRow("Executable", executable_row)
        form.addRow("Workspace", self.workspace_edit)
        form.addRow("Provider", self.provider_combo)
        form.addRow("Model", self.model_edit)
        form.addRow("System prompt", self.system_prompt_edit)
        form.addRow("Append prompt", self.append_system_prompt_edit)
        form.addRow("Extra args", self.extra_args_edit)
        form.addRow(test_button)
        form.addRow(QLabel("Print mode options"))
        form.addRow(self.partial_check)
        form.addRow(self.hooks_check)
        form.addRow(self.bare_check)
        form.addRow(self.skip_permissions_check)
        form.addRow(self.streamlined_check)
        return widget

    def _build_providers_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Environment variables used for OpenClaude provider integration."))
        preset_row = QHBoxLayout()
        self.provider_preset_combo = QComboBox()
        self.provider_preset_combo.addItems(["Custom"] + preset_names())
        apply_preset = QPushButton("Apply preset")
        apply_preset.clicked.connect(self._apply_provider_preset)
        save_profile = QPushButton("Save profile")
        save_profile.clicked.connect(self._save_profile)
        preset_row.addWidget(self.provider_preset_combo)
        preset_row.addWidget(apply_preset)
        preset_row.addWidget(save_profile)
        layout.addLayout(preset_row)

        profile_row = QHBoxLayout()
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Select saved profile"] + sorted(self._config.openclaude.profiles.keys()))
        load_profile = QPushButton("Load profile")
        load_profile.clicked.connect(self._load_profile)
        profile_row.addWidget(self.profile_combo)
        profile_row.addWidget(load_profile)
        layout.addLayout(profile_row)

        self.environment_edit = QTextEdit()
        lines = [f"{key}={value}" for key, value in self._config.openclaude.environment.items()]
        self.environment_edit.setPlainText("\n".join(lines))
        layout.addWidget(self.environment_edit)
        layout.addWidget(QLabel("Examples: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, CLAUDE_CODE_USE_OPENAI=1"))
        return widget

    def _build_appearance_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.language_combo = QComboBox()
        self.language_combo.addItems(self._language_service.available_languages())
        self.language_combo.setCurrentText(self._config.localization.language_file)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self._config.appearance.theme)
        self.accent_edit = QLineEdit(self._config.appearance.accent_color)
        self.font_edit = QLineEdit(self._config.appearance.font_family)
        form.addRow(self._l("settings.language", "Language"), self.language_combo)
        form.addRow(self._l("settings.theme", "Theme"), self.theme_combo)
        form.addRow(self._l("settings.accent", "Accent"), self.accent_edit)
        form.addRow(self._l("settings.font", "Font"), self.font_edit)
        return widget

    def _build_advanced_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.logging_level_combo = QComboBox()
        self.logging_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.logging_level_combo.setCurrentText(self._config.logging.level)
        self.open_log_on_crash_check = QCheckBox("Open log folder on crash")
        self.open_log_on_crash_check.setChecked(self._config.logging.open_log_on_crash)
        self.telemetry_check = QCheckBox("Enable local error telemetry")
        self.telemetry_check.setChecked(self._config.logging.local_telemetry_enabled)
        self.restore_session_check = QCheckBox("Restore last opened session")
        self.restore_session_check.setChecked(self._config.recovery.restore_last_session)
        self.restore_draft_check = QCheckBox("Restore unsent draft and attachments")
        self.restore_draft_check.setChecked(self._config.recovery.restore_draft)
        form.addRow("Logging level", self.logging_level_combo)
        form.addRow(self.open_log_on_crash_check)
        form.addRow(self.telemetry_check)
        form.addRow(self.restore_session_check)
        form.addRow(self.restore_draft_check)
        return widget

    def _build_git_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.git_enabled_check = QCheckBox(self._l("settings.git_enabled", "Enable Git integration in the app"))
        self.git_enabled_check.setChecked(self._config.git.enabled)
        self.git_executable_edit = QLineEdit(self._config.git.executable)
        self.git_auto_refresh_check = QCheckBox(self._l("settings.git_auto_refresh", "Auto-refresh Git status"))
        self.git_auto_refresh_check.setChecked(self._config.git.auto_refresh)
        self.git_workspace_override_edit = QLineEdit(self._config.git.workspace_override)
        self.git_workspace_override_edit.setPlaceholderText(self._l("settings.git_workspace_placeholder", "Optional path override for Git operations"))
        form.addRow(self.git_enabled_check)
        form.addRow(self._l("settings.git_executable", "Git executable"), self.git_executable_edit)
        form.addRow(self.git_auto_refresh_check)
        form.addRow(self._l("settings.git_workspace", "Workspace override"), self.git_workspace_override_edit)
        return widget

    def _build_discord_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.discord_enabled_check = QCheckBox("Enable Discord Rich Presence")
        self.discord_enabled_check.setChecked(self._config.discord.enabled)
        self.discord_client_id_edit = QLineEdit(self._config.discord.client_id)
        self.discord_show_workspace_check = QCheckBox("Show workspace in presence")
        self.discord_show_workspace_check.setChecked(self._config.discord.show_workspace)
        self.discord_show_provider_check = QCheckBox("Show provider in presence")
        self.discord_show_provider_check.setChecked(self._config.discord.show_provider)
        form.addRow(self.discord_enabled_check)
        form.addRow("Discord Client ID", self.discord_client_id_edit)
        form.addRow(self.discord_show_workspace_check)
        form.addRow(self.discord_show_provider_check)
        return widget

    def _browse_executable(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select OpenClaude executable")
        if path:
            self.executable_edit.setText(path)

    def _apply_provider_preset(self) -> None:
        name = self.provider_preset_combo.currentText()
        if name == "Custom":
            return
        self.provider_combo.setCurrentText(name)
        self.environment_edit.setPlainText(preset_to_text(name))
        if not self.model_edit.text().strip():
            for line in preset_to_text(name).splitlines():
                if line.startswith("OPENAI_MODEL=") or line.startswith("ANTHROPIC_MODEL=") or line.startswith("GEMINI_MODEL="):
                    self.model_edit.setText(line.split("=", 1)[1])

    def _save_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "Save profile", "Profile name:")
        if not ok or not name.strip():
            return
        environment = self._parse_environment()
        self._config.openclaude.profiles[name.strip()] = environment
        if self.profile_combo.findText(name.strip()) == -1:
            self.profile_combo.addItem(name.strip())
        self.profile_combo.setCurrentText(name.strip())

    def _load_profile(self) -> None:
        name = self.profile_combo.currentText()
        if name == "Select saved profile":
            return
        environment = self._config.openclaude.profiles.get(name, {})
        self.environment_edit.setPlainText("\n".join(f"{key}={value}" for key, value in environment.items()))

    def _test_provider(self) -> None:
        temp_config = AppConfig.from_dict(self._config.to_dict())
        original = self._config
        self._config = temp_config
        temp_config = self.apply()
        self._config = original
        result = self._tester.test(temp_config.openclaude)
        icon = QMessageBox.Icon.Information if result.ok else QMessageBox.Icon.Warning
        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle("Provider Test")
        box.setText(result.summary)
        box.setDetailedText("\n".join(result.details))
        box.exec()

    def _parse_environment(self) -> dict[str, str]:
        environment: dict[str, str] = {}
        for line in self.environment_edit.toPlainText().splitlines():
            if not line.strip():
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            environment[key.strip()] = value.strip()
        return environment

    def _validate_inputs(self) -> str:
        if not self.executable_edit.text().strip():
            return "OpenClaude executable cannot be empty."
        workspace = self.workspace_edit.text().strip()
        if workspace and not Path(workspace).exists():
            return "The selected workspace folder does not exist."
        git_workspace = self.git_workspace_override_edit.text().strip()
        if git_workspace and not Path(git_workspace).exists():
            return "The Git workspace override folder does not exist."
        accent = self.accent_edit.text().strip()
        if accent and (not accent.startswith("#") or len(accent) not in {4, 7}):
            return "Accent color must be a valid hex value like #4aa3ff."
        if self.discord_enabled_check.isChecked() and not self.discord_client_id_edit.text().strip().isdigit():
            return "Discord Client ID must be numeric when Rich Presence is enabled."
        for line in self.environment_edit.toPlainText().splitlines():
            if line.strip() and "=" not in line:
                return f"Invalid environment line: {line}"
        return ""

    def _handle_accept(self) -> None:
        error = self._validate_inputs()
        if error:
            QMessageBox.warning(self, "Invalid settings", error)
            return
        self.accept()

    def apply(self) -> AppConfig:
        self._config.openclaude.executable = self.executable_edit.text().strip() or "openclaude"
        self._config.openclaude.working_directory = self.workspace_edit.text().strip()
        self._config.openclaude.model = self.model_edit.text().strip()
        self._config.openclaude.provider_name = self.provider_combo.currentText()
        self._config.openclaude.system_prompt = self.system_prompt_edit.toPlainText().strip()
        self._config.openclaude.append_system_prompt = self.append_system_prompt_edit.toPlainText().strip()
        self._config.openclaude.extra_args = self.extra_args_edit.text().strip()
        self._config.openclaude.print_options.include_partial_messages = self.partial_check.isChecked()
        self._config.openclaude.print_options.include_hook_events = self.hooks_check.isChecked()
        self._config.openclaude.print_options.bare_mode = self.bare_check.isChecked()
        self._config.openclaude.print_options.dangerously_skip_permissions = self.skip_permissions_check.isChecked()
        self._config.openclaude.print_options.streamlined_output = self.streamlined_check.isChecked()
        self._config.appearance.theme = self.theme_combo.currentText()
        self._config.appearance.accent_color = self.accent_edit.text().strip()
        self._config.appearance.font_family = self.font_edit.text().strip()
        self._config.localization.language_file = self.language_combo.currentText() or "en.US.xml"
        self._config.logging.level = self.logging_level_combo.currentText()
        self._config.logging.open_log_on_crash = self.open_log_on_crash_check.isChecked()
        self._config.logging.local_telemetry_enabled = self.telemetry_check.isChecked()
        self._config.recovery.restore_last_session = self.restore_session_check.isChecked()
        self._config.recovery.restore_draft = self.restore_draft_check.isChecked()
        self._config.git.enabled = self.git_enabled_check.isChecked()
        self._config.git.executable = self.git_executable_edit.text().strip() or "git"
        self._config.git.auto_refresh = self.git_auto_refresh_check.isChecked()
        self._config.git.workspace_override = self.git_workspace_override_edit.text().strip()
        self._config.discord.enabled = self.discord_enabled_check.isChecked()
        self._config.discord.client_id = self.discord_client_id_edit.text().strip() or "1391469843342889010"
        self._config.discord.show_workspace = self.discord_show_workspace_check.isChecked()
        self._config.discord.show_provider = self.discord_show_provider_check.isChecked()
        self._config.openclaude.environment = self._parse_environment()
        return self._config
