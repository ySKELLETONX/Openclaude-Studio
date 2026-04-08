from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from openclaude_studio.services.crash_handler import install_crash_handler
from openclaude_studio.services.logging_service import get_logger, setup_logging
from openclaude_studio.services.settings_service import SettingsService
from openclaude_studio.ui.main_window import MainWindow


def run() -> int:
    settings_service = SettingsService()
    setup_logging(settings_service.paths.logs_dir)
    install_crash_handler(settings_service.paths.crash_dir)

    app = QApplication([])
    app.setApplicationName("Openclaude Studio")
    app.setOrganizationName("Openclaude Studio")

    logger = get_logger(__name__)
    logger.info("Starting Openclaude Studio")

    window = MainWindow(settings_service)
    window.show()
    return app.exec()
