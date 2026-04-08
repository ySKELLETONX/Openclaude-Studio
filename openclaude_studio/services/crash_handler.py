from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMessageBox

from openclaude_studio.services.telemetry_service import TelemetryService


def install_crash_handler(
    crash_dir: Path,
    telemetry: TelemetryService | None = None,
    open_log_on_crash: bool = False,
) -> None:
    crash_dir.mkdir(parents=True, exist_ok=True)

    def handle_exception(exc_type, exc_value, exc_traceback) -> None:
        crash_file = crash_dir / f"crash-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
        content = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        crash_file.write_text(content, encoding="utf-8")
        if telemetry is not None:
            telemetry.record_error(
                "crash_handler",
                str(exc_value),
                {
                    "exception_type": getattr(exc_type, "__name__", str(exc_type)),
                    "crash_file": str(crash_file),
                },
            )
        QMessageBox.critical(
            None,
            "Openclaude Studio Crash",
            f"An unexpected error occurred.\n\nCrash report saved to:\n{crash_file}",
        )
        if open_log_on_crash:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(crash_dir)))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception
