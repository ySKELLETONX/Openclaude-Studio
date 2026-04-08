from __future__ import annotations

from pathlib import Path

import qtawesome as qta
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QGuiApplication, QTextCursor
from PyQt6.QtWidgets import (
    QApplication,
    QInputDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from openclaude_studio.models.conversation import Conversation
from openclaude_studio.services.conversation_service import ConversationService
from openclaude_studio.services.export_service import ExportService
from openclaude_studio.services.logging_service import get_logger
from openclaude_studio.services.openclaude_service import OpenClaudeRunner, RunRequest
from openclaude_studio.services.render_service import RenderService
from openclaude_studio.services.settings_service import SettingsService
from openclaude_studio.ui.settings_dialog import SettingsDialog
from openclaude_studio.ui.theme import build_stylesheet, theme_colors


class MainWindow(QMainWindow):
    def __init__(self, settings_service: SettingsService) -> None:
        super().__init__()
        self.settings_service = settings_service
        self.config = settings_service.config
        self.logger = get_logger(__name__)
        self.conversation_service = ConversationService(settings_service.paths.conversations_dir)
        self.export_service = ExportService(settings_service.paths.exports_dir)
        self.render_service = RenderService()
        self.runner = OpenClaudeRunner()
        self.current_conversation = Conversation()
        self._colors = theme_colors(self.config.appearance.theme)

        self.setWindowTitle("Openclaude Studio")
        self.resize(1480, 900)
        self._apply_theme()

        self._build_toolbar()
        self._build_ui()
        self._wire_runner()
        self._load_conversations()
        self._show_conversation(self.current_conversation)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        new_action = QAction(qta.icon("fa6s.plus"), "New Chat", self)
        new_action.triggered.connect(self.new_chat)
        settings_action = QAction(qta.icon("fa6s.gear"), "Settings", self)
        settings_action.triggered.connect(self.open_settings)
        export_action = QAction(qta.icon("fa6s.file-export"), "Export", self)
        export_action.triggered.connect(self.export_chat)
        print_action = QAction(qta.icon("fa6s.print"), "Print", self)
        print_action.triggered.connect(self.print_chat)
        screenshot_action = QAction(qta.icon("fa6s.camera"), "Screenshot", self)
        screenshot_action.triggered.connect(self.capture_screenshot)
        logs_action = QAction(qta.icon("fa6s.folder-open"), "Open Logs", self)
        logs_action.triggered.connect(self.open_logs_folder)
        exports_action = QAction(qta.icon("fa6s.box-archive"), "Open Exports", self)
        exports_action.triggered.connect(self.open_exports_folder)
        self.theme_toggle_action = QAction(self)
        self.theme_toggle_action.triggered.connect(self.toggle_theme)
        copy_last_action = QAction(qta.icon("fa6s.copy"), "Copy Last Reply", self)
        copy_last_action.triggered.connect(self.copy_last_assistant_message)
        copy_code_action = QAction(qta.icon("fa6s.code"), "Copy Last Code Block", self)
        copy_code_action.triggered.connect(self.copy_last_code_block)
        rename_action = QAction(qta.icon("fa6s.pen"), "Rename Chat", self)
        rename_action.triggered.connect(self.rename_current_chat)
        delete_action = QAction(qta.icon("fa6s.trash"), "Delete Chat", self)
        delete_action.triggered.connect(self.delete_current_chat)

        toolbar.addAction(new_action)
        toolbar.addAction(settings_action)
        toolbar.addSeparator()
        toolbar.addAction(rename_action)
        toolbar.addAction(delete_action)
        toolbar.addSeparator()
        toolbar.addAction(export_action)
        toolbar.addAction(print_action)
        toolbar.addAction(screenshot_action)
        toolbar.addAction(copy_last_action)
        toolbar.addAction(copy_code_action)
        toolbar.addSeparator()
        toolbar.addAction(self.theme_toggle_action)
        toolbar.addAction(logs_action)
        toolbar.addAction(exports_action)
        self._refresh_theme_action()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_chat_panel())
        splitter.addWidget(self._build_events_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 2)

        root_layout.addWidget(splitter)
        self.setCentralWidget(root)

    def _build_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("Sidebar")
        layout = QVBoxLayout(frame)

        title = QLabel("Conversations")
        title.setStyleSheet(f"font-size: 12pt; font-weight: 600; color: {self._colors['text']};")
        layout.addWidget(title)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search chats...")
        self.search_edit.textChanged.connect(self._refresh_sidebar)
        layout.addWidget(self.search_edit)

        self.sidebar_list = QListWidget()
        self.sidebar_list.itemClicked.connect(self._handle_conversation_selected)
        self.sidebar_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar_list.customContextMenuRequested.connect(self._open_sidebar_context_menu)
        layout.addWidget(self.sidebar_list)

        button = QPushButton("New chat")
        button.setProperty("accent", True)
        button.clicked.connect(self.new_chat)
        layout.addWidget(button)
        return frame

    def _build_chat_panel(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)

        header = QFrame()
        header.setObjectName("HeaderCard")
        header_layout = QVBoxLayout(header)
        self.title_label = QLabel("Openclaude Studio")
        self.title_label.setStyleSheet(f"font-size: 13pt; font-weight: 600; color: {self._colors['text']};")
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("MutedLabel")
        self.session_label = QLabel("Session: not started")
        self.session_label.setObjectName("MutedLabel")
        self.theme_badge = QLabel("Studio Midnight")
        self.theme_badge.setStyleSheet(
            f"background:{self._colors['accent_soft']}; color:{self._colors['accent']};"
            "padding:6px 10px; border-radius:10px; font-weight:600;"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.session_label)
        header_layout.addWidget(self.theme_badge, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(header)

        self.chat_view = QTextBrowser()
        self.chat_view.setOpenExternalLinks(True)
        layout.addWidget(self.chat_view, 1)

        composer = QFrame()
        composer.setObjectName("ComposerCard")
        composer_layout = QVBoxLayout(composer)
        self.composer = QTextEdit()
        self.composer.setPlaceholderText("Describe what you want OpenClaude to do...")
        self.composer.setFixedHeight(120)
        composer_layout.addWidget(self.composer)

        actions = QHBoxLayout()
        self.workspace_label = QLabel(self.config.openclaude.working_directory or str(Path.cwd()))
        self.workspace_label.setObjectName("MutedLabel")
        actions.addWidget(self.workspace_label)
        actions.addStretch()

        self.stop_button = QPushButton("Stop")
        self.stop_button.setProperty("danger", True)
        self.stop_button.clicked.connect(self.runner.stop)
        self.send_button = QPushButton("Send to OpenClaude")
        self.send_button.setProperty("accent", True)
        self.send_button.clicked.connect(self.send_prompt)
        actions.addWidget(self.stop_button)
        actions.addWidget(self.send_button)
        composer_layout.addLayout(actions)
        layout.addWidget(composer)
        return wrapper

    def _build_events_panel(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("EventsPanel")
        layout = QVBoxLayout(frame)
        label = QLabel("Events & Tools")
        label.setStyleSheet(f"font-size: 12pt; font-weight: 600; color: {self._colors['text']};")
        self.event_summary_label = QLabel("No activity yet")
        self.event_summary_label.setObjectName("MutedLabel")
        actions = QHBoxLayout()
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_event_view)
        copy_button = QPushButton("Copy events")
        copy_button.clicked.connect(self.copy_events)
        actions.addWidget(clear_button)
        actions.addWidget(copy_button)
        actions.addStretch()
        self.events_list = QListWidget()
        layout.addWidget(label)
        layout.addWidget(self.event_summary_label)
        layout.addLayout(actions)
        layout.addWidget(self.events_list)
        return frame

    def _wire_runner(self) -> None:
        self.runner.assistant_delta.connect(self._append_assistant_delta)
        self.runner.event_received.connect(self._append_event)
        self.runner.status_changed.connect(self.status_label.setText)
        self.runner.error_occurred.connect(self._show_error)
        self.runner.result_ready.connect(self._handle_runner_result)
        self.runner.session_initialized.connect(self._handle_session_initialized)

    def _load_conversations(self) -> None:
        conversations = self.conversation_service.list_conversations()
        if conversations:
            self.current_conversation = conversations[0]
        for conversation in conversations:
            self._add_sidebar_item(conversation)

    def _add_sidebar_item(self, conversation: Conversation) -> None:
        item = QListWidgetItem(conversation.title)
        item.setData(Qt.ItemDataRole.UserRole, conversation)
        self.sidebar_list.addItem(item)

    def _handle_conversation_selected(self, item: QListWidgetItem) -> None:
        conversation = item.data(Qt.ItemDataRole.UserRole)
        self.current_conversation = conversation
        self._show_conversation(conversation)

    def _show_conversation(self, conversation: Conversation) -> None:
        self.title_label.setText(conversation.title)
        self.session_label.setText(
            f"Session: {conversation.openclaude_session_id}" if conversation.openclaude_session_id else "Session: not started"
        )
        self.chat_view.clear()
        self.events_list.clear()
        for message in conversation.messages:
            self._append_message(message.role, message.content)
        for event in conversation.event_log[-200:]:
            self.events_list.addItem(str(event))
        self._update_event_summary()

    def new_chat(self) -> None:
        self.current_conversation = Conversation()
        self.title_label.setText(self.current_conversation.title)
        self.chat_view.clear()
        self.events_list.clear()
        self.session_label.setText("Session: not started")
        self._refresh_sidebar()

    def send_prompt(self) -> None:
        prompt = self.composer.toPlainText().strip()
        if not prompt:
            return
        if self.runner.is_running:
            QMessageBox.information(self, "Busy", "OpenClaude is still processing the previous request.")
            return

        self.current_conversation.add_message("user", prompt)
        self.conversation_service.save(self.current_conversation)
        self._refresh_sidebar()
        self._show_conversation(self.current_conversation)
        self.composer.clear()

        request = RunRequest(
            prompt=prompt,
            conversation=self.current_conversation,
            config=self.config.openclaude,
        )
        self.runner.start(request)

    def _append_message(self, role: str, content: str) -> None:
        html = self.render_service.render_message(role, content, self.config.appearance.theme)
        self.chat_view.append(html)
        self.chat_view.moveCursor(QTextCursor.MoveOperation.End)

    def _append_assistant_delta(self, text: str) -> None:
        if not self.current_conversation.messages or self.current_conversation.messages[-1].role != "assistant":
            self.current_conversation.add_message("assistant", "")
        self.current_conversation.messages[-1].content += text
        self._show_conversation(self.current_conversation)

    def _append_event(self, payload: dict) -> None:
        self.current_conversation.event_log.append(payload)
        self.events_list.addItem(str(payload))
        self.events_list.scrollToBottom()
        self._update_event_summary()

    def _handle_runner_result(self, result: dict) -> None:
        session_id = result.get("session_id")
        if session_id:
            self.current_conversation.openclaude_session_id = session_id

        text_result = result.get("result", "").strip()
        if text_result:
            if not self.current_conversation.messages or self.current_conversation.messages[-1].role != "assistant":
                self.current_conversation.add_message("assistant", text_result)
            elif not self.current_conversation.messages[-1].content.strip():
                self.current_conversation.messages[-1].content = text_result

        if result.get("is_error"):
            self.current_conversation.add_message("system", result.get("result", "Execution error"))

        self.conversation_service.save(self.current_conversation)
        self._refresh_sidebar()
        self._show_conversation(self.current_conversation)

    def _handle_session_initialized(self, session_id: str) -> None:
        self.current_conversation.openclaude_session_id = session_id
        self.session_label.setText(f"Session: {session_id}")
        self.conversation_service.save(self.current_conversation)
        self._refresh_sidebar()

    def _refresh_sidebar(self) -> None:
        self.sidebar_list.clear()
        conversations = {self.current_conversation.id: self.current_conversation}
        for conversation in self.conversation_service.list_conversations():
            conversations[conversation.id] = conversation
        query = self.search_edit.text().strip().lower() if hasattr(self, "search_edit") else ""
        visible = sorted(conversations.values(), key=lambda item: item.updated_at, reverse=True)
        for conversation in visible:
            if query and query not in conversation.title.lower():
                joined = "\n".join(message.content for message in conversation.messages[-6:]).lower()
                if query not in joined:
                    continue
            self._add_sidebar_item(conversation)
            if conversation.id == self.current_conversation.id:
                self.sidebar_list.setCurrentRow(self.sidebar_list.count() - 1)

    def _update_event_summary(self) -> None:
        total = len(self.current_conversation.event_log)
        if total == 0:
            self.event_summary_label.setText("No activity yet")
            return
        last_type = self.current_conversation.event_log[-1].get("type", "event")
        self.event_summary_label.setText(f"{total} events captured • latest: {last_type}")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.config = dialog.apply()
            self.settings_service.save(self.config)
            self._apply_theme()
            self._refresh_theme_action()
            self._show_conversation(self.current_conversation)
            self.workspace_label.setText(self.config.openclaude.working_directory or str(Path.cwd()))

    def export_chat(self) -> None:
        if not self.current_conversation.messages:
            return
        default_path = self.export_service.make_default_path(self.current_conversation, "md")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export conversation",
            str(default_path),
            "Markdown (*.md);;HTML (*.html);;Text (*.txt)",
        )
        if not path:
            return
        exported = self.export_service.export_to_path(self.current_conversation, Path(path))
        QMessageBox.information(self, "Exported", f"Conversation exported to:\n{exported}")

    def print_chat(self) -> None:
        if self.current_conversation.messages:
            self.export_service.print_preview(self, self.current_conversation)

    def capture_screenshot(self) -> None:
        target_dir = self.settings_service.paths.exports_dir / "screenshots"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{self.current_conversation.id}.png"
        screenshot = QGuiApplication.primaryScreen().grabWindow(self.winId())
        screenshot.save(str(target))
        QMessageBox.information(self, "Screenshot saved", f"Saved to:\n{target}")

    def rename_current_chat(self) -> None:
        text, ok = QInputDialog.getText(self, "Rename chat", "Title:", text=self.current_conversation.title)
        if not ok:
            return
        text = text.strip()
        if not text:
            return
        self.current_conversation.title = text
        self.conversation_service.save(self.current_conversation)
        self._refresh_sidebar()
        self._show_conversation(self.current_conversation)

    def delete_current_chat(self) -> None:
        if not self.current_conversation.messages and not self.current_conversation.event_log:
            self.new_chat()
            return
        answer = QMessageBox.question(
            self,
            "Delete chat",
            f"Delete '{self.current_conversation.title}'?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        conversation_id = self.current_conversation.id
        self.conversation_service.delete(conversation_id)
        remaining = self.conversation_service.list_conversations()
        self.current_conversation = remaining[0] if remaining else Conversation()
        self._refresh_sidebar()
        self._show_conversation(self.current_conversation)

    def open_logs_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.settings_service.paths.logs_dir)))

    def open_exports_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.settings_service.paths.exports_dir)))

    def clear_event_view(self) -> None:
        self.current_conversation.event_log.clear()
        self.events_list.clear()
        self._update_event_summary()
        self.conversation_service.save(self.current_conversation)

    def copy_events(self) -> None:
        text = "\n".join(str(event) for event in self.current_conversation.event_log)
        QApplication.clipboard().setText(text)
        self.status_label.setText("Events copied to clipboard")

    def copy_last_assistant_message(self) -> None:
        for message in reversed(self.current_conversation.messages):
            if message.role == "assistant" and message.content.strip():
                QApplication.clipboard().setText(message.content)
                self.status_label.setText("Last reply copied")
                return
        self.status_label.setText("No assistant reply to copy")

    def copy_last_code_block(self) -> None:
        for message in reversed(self.current_conversation.messages):
            if message.role != "assistant":
                continue
            code = self.render_service.extract_last_code_block(message.content)
            if code:
                QApplication.clipboard().setText(code)
                self.status_label.setText("Last code block copied")
                return
        self.status_label.setText("No code block found")

    def toggle_theme(self) -> None:
        self.config.appearance.theme = "light" if self.config.appearance.theme == "dark" else "dark"
        self.settings_service.save(self.config)
        self._apply_theme()
        self._refresh_theme_action()
        self._show_conversation(self.current_conversation)

    def _apply_theme(self) -> None:
        self._colors = theme_colors(self.config.appearance.theme)
        self.setStyleSheet(build_stylesheet(self.config.appearance.theme))
        if hasattr(self, "theme_badge"):
            self.theme_badge.setStyleSheet(
                f"background:{self._colors['accent_soft']}; color:{self._colors['accent']};"
                "padding:6px 10px; border-radius:10px; font-weight:600;"
            )
        if hasattr(self, "title_label"):
            self.title_label.setStyleSheet(f"font-size: 13pt; font-weight: 600; color: {self._colors['text']};")

    def _refresh_theme_action(self) -> None:
        is_dark = self.config.appearance.theme == "dark"
        icon = qta.icon("fa6s.sun") if is_dark else qta.icon("fa6s.moon")
        text = "Light Mode" if is_dark else "Dark Mode"
        self.theme_toggle_action.setIcon(icon)
        self.theme_toggle_action.setText(text)

    def _open_sidebar_context_menu(self, position) -> None:
        item = self.sidebar_list.itemAt(position)
        if item is None:
            return
        conversation = item.data(Qt.ItemDataRole.UserRole)
        self.current_conversation = conversation

        menu = QMenu(self)
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        action = menu.exec(self.sidebar_list.mapToGlobal(position))
        if action == rename_action:
            self.rename_current_chat()
        elif action == delete_action:
            self.delete_current_chat()

    def _show_error(self, message: str) -> None:
        self.logger.error(message)
        QMessageBox.critical(self, "OpenClaude Error", message)
