from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from openclaude_studio import __version__
from openclaude_studio.services.crash_handler import install_crash_handler
from openclaude_studio.services.discord_presence_service import DiscordPresenceService
from openclaude_studio.services.language_service import LanguageService
from openclaude_studio.services.logging_service import get_logger, setup_logging
from openclaude_studio.services.telemetry_service import TelemetryService
from openclaude_studio.services.settings_service import SettingsService
from openclaude_studio.ui.main_window import MainWindow


def run() -> int:
    settings_service = SettingsService()
    language_service = LanguageService(
        settings_service.paths.languages_dir,
        settings_service.config.localization.language_file,
    )
    setup_logging(settings_service.paths.logs_dir, settings_service.config.logging.level)
    telemetry = TelemetryService(
        settings_service.paths.telemetry_file,
        enabled=settings_service.config.logging.local_telemetry_enabled,
    )
    discord_presence = DiscordPresenceService(settings_service.config.discord)
    install_crash_handler(
        settings_service.paths.crash_dir,
        telemetry,
        settings_service.config.logging.open_log_on_crash,
    )

    app = QApplication([])
    app.setApplicationName(language_service.t("app.title", "Openclaude Studio"))
    app.setOrganizationName("Openclaude Studio")
    app.setApplicationVersion(__version__)
    icon_path = Path.cwd() / "assets" / "openclaude_studio.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    logger = get_logger(__name__)
    logger.info("Starting Openclaude Studio")

    window = MainWindow(settings_service, language_service, telemetry, discord_presence)
    window.show()
    return app.exec()
