from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrintPreviewDialog, QPrinter

from openclaude_studio.models.conversation import Conversation


class ExportService:
    def __init__(self, exports_dir: Path) -> None:
        self.exports_dir = exports_dir
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def build_markdown(self, conversation: Conversation) -> str:
        lines = [f"# {conversation.title}", ""]
        for message in conversation.messages:
            lines.append(f"## {message.role.title()}")
            lines.append("")
            lines.append(message.content)
            lines.append("")
        return "\n".join(lines)

    def export_to_path(self, conversation: Conversation, target: Path) -> Path:
        markdown = self.build_markdown(conversation)
        suffix = target.suffix.lower()
        if suffix in {".md", ".txt"}:
            target.write_text(markdown, encoding="utf-8")
        elif suffix == ".html":
            html = (
                "<html><body><pre>"
                + markdown.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                + "</pre></body></html>"
            )
            target.write_text(html, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported export format: {suffix}")
        return target

    def make_default_path(self, conversation: Conversation, extension: str) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        slug = conversation.title[:32].replace(" ", "_").replace("/", "_") or "conversation"
        return self.exports_dir / f"{slug}-{timestamp}.{extension}"

    def print_preview(self, parent, conversation: Conversation) -> None:
        printer = QPrinter(QPrinter.HighResolution)
        preview = QPrintPreviewDialog(printer, parent)
        document = QTextDocument()
        document.setMarkdown(self.build_markdown(conversation))
        preview.paintRequested.connect(document.print_)
        preview.exec()
