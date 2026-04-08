from __future__ import annotations

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
from openclaude_studio.services.provider_presets import preset_names, preset_to_text
from openclaude_studio.services.provider_test_service import ProviderTestService


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(860, 720)
        self._config = config
        self._tester = ProviderTestService()

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_openclaude_tab(), "OpenClaude")
        self.tabs.addTab(self._build_providers_tab(), "Providers")
        self.tabs.addTab(self._build_appearance_tab(), "Appearance")

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addWidget(buttons)

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
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self._config.appearance.theme)
        self.accent_edit = QLineEdit(self._config.appearance.accent_color)
        self.font_edit = QLineEdit(self._config.appearance.font_family)
        form.addRow("Theme", self.theme_combo)
        form.addRow("Accent", self.accent_edit)
        form.addRow("Font", self.font_edit)
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
        temp_config = self.apply()
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
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            environment[key.strip()] = value.strip()
        return environment

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
        self._config.openclaude.environment = self._parse_environment()
        return self._config
