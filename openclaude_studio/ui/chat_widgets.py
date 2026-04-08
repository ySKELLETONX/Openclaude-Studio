from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QTextEdit,
)


@dataclass
class CodeBlock:
    language: str
    code: str


class MessageCard(QFrame):
    copy_requested = pyqtSignal(str)

    def __init__(self, role: str, html: str, code_blocks: list[CodeBlock], muted_text: str, parent=None) -> None:
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

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.submit_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


def copy_to_clipboard(text: str) -> None:
    QApplication.clipboard().setText(text)
