from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QTextEdit,
)


@dataclass
class CodeBlock:
    language: str
    code: str


@dataclass
class AttachmentPreview:
    path: str
    name: str
    kind: str = "file"


class MessageCard(QFrame):
    copy_requested = pyqtSignal(str)

    def __init__(
        self,
        role: str,
        html: str,
        code_blocks: list[CodeBlock],
        muted_text: str,
        attachments: list[AttachmentPreview] | None = None,
        footer_text: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.role = role
        self.code_blocks = code_blocks
        self.setObjectName("MessageCard")
        self.setProperty("messageRole", role)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        label = QLabel(role.title())
        label.setStyleSheet(f"font-size:11px; color:{muted_text}; font-weight:600; letter-spacing:0.04em;")
        top.addWidget(label)
        top.addStretch()
        if role == "assistant":
            copy_text = QPushButton("Copy")
            copy_text.setProperty("secondary", True)
            copy_text.clicked.connect(lambda: self.copy_requested.emit(self.plain_text()))
            top.addWidget(copy_text)
        outer.addLayout(top)

        body = QTextBrowser()
        body.setOpenExternalLinks(True)
        body.setFrameShape(QFrame.Shape.NoFrame)
        body.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        body.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body.setHtml(html)
        body.document().setDocumentMargin(0)
        body.setMaximumHeight(max(80, int(body.document().size().height()) + 18))
        outer.addWidget(body)

        if attachments:
            attachment_row = QHBoxLayout()
            attachment_row.setContentsMargins(0, 0, 0, 0)
            attachment_row.setSpacing(8)
            for attachment in attachments:
                chip = QLabel(attachment.name)
                chip.setStyleSheet(
                    f"padding:6px 10px; border-radius:10px; background:rgba(127,127,127,0.10); color:{muted_text};"
                )
                attachment_row.addWidget(chip)
            attachment_row.addStretch()
            outer.addLayout(attachment_row)

        if code_blocks:
            buttons = QHBoxLayout()
            buttons.setContentsMargins(0, 0, 0, 0)
            for index, block in enumerate(code_blocks, start=1):
                title = block.language.upper() if block.language else f"CODE {index}"
                button = QPushButton(f"Copy {title}")
                button.setProperty("secondary", True)
                button.clicked.connect(lambda _=False, code=block.code: self.copy_requested.emit(code))
                buttons.addWidget(button)
            buttons.addStretch()
            outer.addLayout(buttons)

        if footer_text.strip():
            footer = QLabel(footer_text)
            footer.setWordWrap(True)
            footer.setStyleSheet(f"font-size:11px; color:{muted_text};")
            outer.addWidget(footer)

    def plain_text(self) -> str:
        pieces = []
        for block in self.findChildren(QTextBrowser):
            pieces.append(block.toPlainText())
        return "\n".join(piece for piece in pieces if piece).strip()


class MessageStreamCard(QFrame):
    stop_requested = pyqtSignal()

    def __init__(self, muted_text: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("StreamCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)
        label = QLabel("OpenClaude is streaming a reply...")
        label.setStyleSheet(f"color:{muted_text};")
        stop = QPushButton("Stop")
        stop.setProperty("secondary", True)
        stop.clicked.connect(self.stop_requested.emit)
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(stop)


class PromptEditor(QTextEdit):
    submit_requested = pyqtSignal()
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.submit_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        urls = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if urls:
            self.files_dropped.emit(urls)
            event.acceptProposedAction()
            return
        super().dropEvent(event)


class AttachmentPreviewList(QListWidget):
    remove_requested = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setMovement(QListWidget.Movement.Static)
        self.setSpacing(10)
        self.setFixedHeight(92)

    def set_attachments(self, attachments: list[AttachmentPreview]) -> None:
        self.clear()
        for attachment in attachments:
            item = QListWidgetItem(attachment.name)
            item.setData(Qt.ItemDataRole.UserRole, attachment.path)
            if attachment.kind == "image":
                pixmap = QPixmap(attachment.path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        64,
                        64,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    item.setIcon(QIcon(scaled))
            self.addItem(item)


def copy_to_clipboard(text: str) -> None:
    QApplication.clipboard().setText(text)
