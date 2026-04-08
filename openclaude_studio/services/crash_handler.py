from __future__ import annotations

import sys
import traceback
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QMessageBox


def install_crash_handler(crash_dir: Path) -> None:
    crash_dir.mkdir(parents=True, exist_ok=True)

    def handle_exception(exc_type, exc_value, exc_traceback) -> None:
        crash_file = crash_dir / f"crash-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
        content = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        crash_file.write_text(content, encoding="utf-8")
        QMessageBox.critical(
            None,
            "Openclaude Studio Crash",
            f"An unexpected error occurred.\n\nCrash report saved to:\n{crash_file}",
        )
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception
