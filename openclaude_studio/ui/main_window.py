from __future__ import annotations

from difflib import unified_diff
from pathlib import Path

import qtawesome as qta
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QGuiApplication
from PyQt6.QtWidgets import (
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from openclaude_studio.models.conversation import Attachment, ChatMessage, Conversation
from openclaude_studio.services.conversation_service import ConversationService
from openclaude_studio.services.export_service import ExportService
from openclaude_studio.services.logging_service import get_logger
from openclaude_studio.services.openclaude_service import OpenClaudeRunner, RunRequest
from openclaude_studio.services.render_service import RenderService
from openclaude_studio.services.settings_service import SettingsService
from openclaude_studio.ui.chat_widgets import (
    AttachmentPreview,
    AttachmentPreviewList,
    CodeBlock,
    MessageCard,
    MessageStreamCard,
    PromptEditor,
    copy_to_clipboard,
)
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
        self._stream_card: MessageStreamCard | None = None
        self._runtime_state: dict = {"status": "idle"}
        self._pending_permission: dict | None = None
        self._pending_attachments: list[Attachment] = []

        self.setWindowTitle("Openclaude Studio")
        self.resize(1600, 960)

        self._build_toolbar()
        self._build_ui()
        self._wire_runner()
        self._apply_theme()
        self._load_conversations()
        self._show_conversation(self.current_conversation)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        new_action = QAction(qta.icon("fa6s.plus"), "New Chat", self)
        new_action.triggered.connect(self.new_chat)
        import_action = QAction(qta.icon("fa6s.file-import"), "Import Chat", self)
        import_action.triggered.connect(self.import_chat)
        duplicate_action = QAction(qta.icon("fa6s.copy"), "Duplicate", self)
        duplicate_action.triggered.connect(self.duplicate_current_chat)
        pin_action = QAction(qta.icon("fa6s.star"), "Pin", self)
        pin_action.triggered.connect(self.toggle_pin_current_chat)
        tags_action = QAction(qta.icon("fa6s.tags"), "Tags", self)
        tags_action.triggered.connect(self.edit_tags)
        attach_action = QAction(qta.icon("fa6s.paperclip"), "Attach Files", self)
        attach_action.triggered.connect(self.attach_files)
        edit_last_action = QAction(qta.icon("fa6s.pen-to-square"), "Edit Last Prompt", self)
        edit_last_action.triggered.connect(self.edit_last_prompt)
        regenerate_action = QAction(qta.icon("fa6s.rotate-right"), "Regenerate", self)
        regenerate_action.triggered.connect(self.regenerate_last_reply)
        continue_action = QAction(qta.icon("fa6s.play"), "Continue", self)
        continue_action.triggered.connect(self.continue_last_reply)
        settings_action = QAction(qta.icon("fa6s.gear"), "Settings", self)
        settings_action.triggered.connect(self.open_settings)
        rename_action = QAction(qta.icon("fa6s.pen"), "Rename Chat", self)
        rename_action.triggered.connect(self.rename_current_chat)
        delete_action = QAction(qta.icon("fa6s.trash"), "Delete Chat", self)
        delete_action.triggered.connect(self.delete_current_chat)
        export_action = QAction(qta.icon("fa6s.file-export"), "Export", self)
        export_action.triggered.connect(self.export_chat)
        print_action = QAction(qta.icon("fa6s.print"), "Print", self)
        print_action.triggered.connect(self.print_chat)
        screenshot_action = QAction(qta.icon("fa6s.camera"), "Screenshot", self)
        screenshot_action.triggered.connect(self.capture_screenshot)
        copy_last_action = QAction(qta.icon("fa6s.copy"), "Copy Last Reply", self)
        copy_last_action.triggered.connect(self.copy_last_assistant_message)
        copy_code_action = QAction(qta.icon("fa6s.code"), "Copy Last Code Block", self)
        copy_code_action.triggered.connect(self.copy_last_code_block)
        self.theme_toggle_action = QAction(self)
        self.theme_toggle_action.triggered.connect(self.toggle_theme)
        logs_action = QAction(qta.icon("fa6s.folder-open"), "Open Logs", self)
        logs_action.triggered.connect(self.open_logs_folder)
        exports_action = QAction(qta.icon("fa6s.box-archive"), "Open Exports", self)
        exports_action.triggered.connect(self.open_exports_folder)

        for action in (
            new_action,
            import_action,
            export_action,
            duplicate_action,
            None,
            pin_action,
            tags_action,
            attach_action,
            None,
            edit_last_action,
            regenerate_action,
            continue_action,
            None,
            settings_action,
            None,
            rename_action,
            delete_action,
            None,
            print_action,
            screenshot_action,
            copy_last_action,
            copy_code_action,
            None,
            self.theme_toggle_action,
            logs_action,
            exports_action,
        ):
            if action is None:
                toolbar.addSeparator()
            else:
                toolbar.addAction(action)

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(14)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_chat_panel())
        splitter.addWidget(self._build_session_panel())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 6)
        splitter.setStretchFactor(2, 3)

        root_layout.addWidget(splitter)
        self.setCentralWidget(root)

    def _build_sidebar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("Sidebar")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Topics")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search title, tags, content...")
        self.search_edit.textChanged.connect(self._refresh_sidebar)
        layout.addWidget(self.search_edit)

        self.sidebar_list = QListWidget()
        self.sidebar_list.itemClicked.connect(self._handle_conversation_selected)
        self.sidebar_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sidebar_list.customContextMenuRequested.connect(self._open_sidebar_context_menu)
        layout.addWidget(self.sidebar_list, 1)

        button_row = QHBoxLayout()
        new_button = QPushButton("New topic")
        new_button.setProperty("accent", True)
        new_button.clicked.connect(self.new_chat)
        reload_button = QPushButton("Pin")
        reload_button.setProperty("secondary", True)
        reload_button.clicked.connect(self.toggle_pin_current_chat)
        button_row.addWidget(new_button)
        button_row.addWidget(reload_button)
        layout.addLayout(button_row)
        return frame

    def _build_chat_panel(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header = QFrame()
        header.setObjectName("HeaderCard")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(18, 18, 18, 18)
        header_layout.setSpacing(8)

        top = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(4)
        self.title_label = QLabel("Openclaude Studio")
        self.title_label.setObjectName("HeroTitle")
        self.subtitle_label = QLabel("A clean desktop workspace for OpenClaude")
        self.subtitle_label.setObjectName("MutedLabel")
        left.addWidget(self.title_label)
        left.addWidget(self.subtitle_label)
        top.addLayout(left)
        top.addStretch()
        self.tags_badge = QLabel("")
        self.theme_badge = QLabel("Studio Midnight")
        top.addWidget(self.tags_badge, alignment=Qt.AlignmentFlag.AlignTop)
        top.addWidget(self.theme_badge, alignment=Qt.AlignmentFlag.AlignTop)
        header_layout.addLayout(top)

        meta = QHBoxLayout()
        meta.setSpacing(16)
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("MutedLabel")
        self.session_label = QLabel("Session: not started")
        self.session_label.setObjectName("MutedLabel")
        self.chat_mode_label = QLabel("Mode: standard")
        self.chat_mode_label.setObjectName("MutedLabel")
        meta.addWidget(self.status_label)
        meta.addWidget(self.session_label)
        meta.addWidget(self.chat_mode_label)
        meta.addStretch()
        header_layout.addLayout(meta)
        layout.addWidget(header)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(8, 8, 8, 8)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()
        self.chat_scroll.setWidget(self.chat_content)
        layout.addWidget(self.chat_scroll, 1)

        composer = QFrame()
        composer.setObjectName("ComposerCard")
        composer_layout = QVBoxLayout(composer)
        composer_layout.setContentsMargins(18, 18, 18, 18)
        composer_layout.setSpacing(10)

        composer_title_row = QHBoxLayout()
        composer_title = QLabel("Composer")
        composer_title.setObjectName("SectionTitle")
        composer_title_row.addWidget(composer_title)
        composer_title_row.addStretch()
        attach_button = QPushButton("Attach")
        attach_button.setProperty("secondary", True)
        attach_button.clicked.connect(self.attach_files)
        clear_attachments_button = QPushButton("Clear attachments")
        clear_attachments_button.setProperty("secondary", True)
        clear_attachments_button.clicked.connect(self.clear_attachments)
        composer_title_row.addWidget(attach_button)
        composer_title_row.addWidget(clear_attachments_button)
        composer_layout.addLayout(composer_title_row)

        self.attachment_list = AttachmentPreviewList()
        self.attachment_list.itemDoubleClicked.connect(self._remove_selected_attachment)
        composer_layout.addWidget(self.attachment_list)

        self.composer = PromptEditor()
        self.composer.setPlaceholderText("Describe the task, mention files, or drag attachments here...")
        self.composer.setFixedHeight(142)
        self.composer.submit_requested.connect(self.send_prompt)
        self.composer.files_dropped.connect(self._handle_dropped_files)
        composer_layout.addWidget(self.composer)

        self.composer_hint = QLabel("Ctrl+Enter to send • Shift+Enter for a line break • clearer prompts produce better tool runs.")
        self.composer_hint.setObjectName("MutedLabel")
        self.composer_hint.setText("Ctrl+Enter to send • Shift+Enter for a line break • double-click an attachment to remove it.")
        composer_layout.addWidget(self.composer_hint)

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

    def _build_session_panel(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("EventsPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Session")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.provider_label = QLabel("Provider: Custom")
        self.provider_label.setObjectName("MutedLabel")
        self.model_label = QLabel("Model: default")
        self.model_label.setObjectName("MutedLabel")
        self.connection_label = QLabel("Connection: idle")
        self.connection_label.setObjectName("MutedLabel")
        self.workspace_detail_label = QLabel("Workspace: current folder")
        self.workspace_detail_label.setObjectName("MutedLabel")
        self.event_summary_label = QLabel("No activity yet")
        self.event_summary_label.setObjectName("MutedLabel")
        for widget in (
            self.provider_label,
            self.model_label,
            self.connection_label,
            self.workspace_detail_label,
            self.event_summary_label,
        ):
            layout.addWidget(widget)

        self.permission_card = QFrame()
        self.permission_card.setObjectName("PermissionCard")
        permission_layout = QVBoxLayout(self.permission_card)
        permission_layout.setContentsMargins(12, 12, 12, 12)
        permission_layout.setSpacing(8)
        permission_title = QLabel("Permissions")
        permission_title.setObjectName("SectionTitle")
        self.permission_status_label = QLabel("No approval needed right now.")
        self.permission_status_label.setObjectName("MutedLabel")
        permission_actions = QHBoxLayout()
        self.permission_approve_button = QPushButton("Approve")
        self.permission_approve_button.setProperty("accent", True)
        self.permission_approve_button.clicked.connect(lambda: self._respond_to_permission(True))
        self.permission_reject_button = QPushButton("Reject")
        self.permission_reject_button.setProperty("danger", True)
        self.permission_reject_button.clicked.connect(lambda: self._respond_to_permission(False))
        permission_actions.addWidget(self.permission_approve_button)
        permission_actions.addWidget(self.permission_reject_button)
        permission_layout.addWidget(permission_title)
        permission_layout.addWidget(self.permission_status_label)
        permission_layout.addLayout(permission_actions)
        layout.addWidget(self.permission_card)

        history_title = QLabel("Permission History")
        history_title.setObjectName("SectionTitle")
        layout.addWidget(history_title)
        self.permission_history_list = QListWidget()
        layout.addWidget(self.permission_history_list, 1)

        row = QHBoxLayout()
        clear_button = QPushButton("Clear events")
        clear_button.setProperty("secondary", True)
        clear_button.clicked.connect(self.clear_event_view)
        copy_button = QPushButton("Copy events")
        copy_button.setProperty("secondary", True)
        copy_button.clicked.connect(self.copy_events)
        row.addWidget(clear_button)
        row.addWidget(copy_button)
        row.addStretch()
        layout.addLayout(row)

        events_title = QLabel("Runtime Events")
        events_title.setObjectName("SectionTitle")
        layout.addWidget(events_title)

        self.events_list = QListWidget()
        layout.addWidget(self.events_list, 1)
        return frame

    def _wire_runner(self) -> None:
        self.runner.assistant_delta.connect(self._append_assistant_delta)
        self.runner.event_received.connect(self._append_event)
        self.runner.status_changed.connect(self._handle_status_changed)
        self.runner.error_occurred.connect(self._show_error)
        self.runner.result_ready.connect(self._handle_runner_result)
        self.runner.session_initialized.connect(self._handle_session_initialized)
        self.runner.runtime_state_changed.connect(self._handle_runtime_state_changed)
        self.runner.permission_requested.connect(self._handle_permission_requested)
        self.runner.permission_resolved.connect(self._handle_permission_resolved)

    def _load_conversations(self) -> None:
        conversations = self.conversation_service.list_conversations()
        if conversations:
            self.current_conversation = conversations[0]
        self._refresh_sidebar()

    def _build_sidebar_label(self, conversation: Conversation) -> str:
        pin = "★ " if conversation.pinned else ""
        preview = conversation.messages[-1].content[:58].replace("\n", " ") if conversation.messages else "No messages yet"
        tags = f"\n#{' #'.join(conversation.tags[:3])}" if conversation.tags else ""
        return f"{pin}{conversation.title}\n{preview}{tags}"

    def _add_sidebar_item(self, conversation: Conversation) -> None:
        item = QListWidgetItem(self._build_sidebar_label(conversation))
        item.setData(Qt.ItemDataRole.UserRole, conversation)
        self.sidebar_list.addItem(item)

    def _handle_conversation_selected(self, item: QListWidgetItem) -> None:
        conversation = item.data(Qt.ItemDataRole.UserRole)
        self.current_conversation = conversation
        self._show_conversation(conversation)

    def _show_conversation(self, conversation: Conversation) -> None:
        self.title_label.setText(f"{'★ ' if conversation.pinned else ''}{conversation.title}")
        self.subtitle_label.setText("Session-ready workspace with prompts, attachments, and runtime history")
        session_text = conversation.openclaude_session_id or "not started"
        self.session_label.setText(f"Session: {session_text}")
        self.tags_badge.setText(f"Tags: {', '.join(conversation.tags)}" if conversation.tags else "")
        self._clear_chat_cards()
        self.events_list.clear()
        self.permission_history_list.clear()
        for index, message in enumerate(conversation.messages):
            self._append_message(message, index)
        for event in conversation.event_log[-200:]:
            self.events_list.addItem(str(event))
        for entry in conversation.permission_history[-100:]:
            verdict = "Approved" if entry.get("approved") else "Rejected"
            self.permission_history_list.addItem(f"{verdict}: {entry.get('details', 'permission request')}")
        self._update_event_summary()
        self._refresh_session_panel()

    def new_chat(self) -> None:
        self.current_conversation = Conversation()
        self.clear_attachments()
        self._show_conversation(self.current_conversation)
        self._refresh_sidebar()

    def send_prompt(self) -> None:
        prompt = self.composer.toPlainText().strip()
        if not prompt and not self._pending_attachments:
            return
        if self.runner.is_running:
            QMessageBox.information(self, "Busy", "OpenClaude is still processing the previous request.")
            return

        prompt_text = prompt or "Please inspect the attached files and continue."
        attachments = list(self._pending_attachments)
        self.current_conversation.add_message(
            "user",
            prompt_text,
            metadata={"attachment_count": len(attachments)} if attachments else {},
            attachments=attachments,
        )
        self.conversation_service.save(self.current_conversation)
        self.composer.clear()
        composed_prompt = self._compose_prompt_with_attachments(prompt_text, attachments)
        self.clear_attachments()
        self._show_conversation(self.current_conversation)
        self._refresh_sidebar()
        self._show_stream_card()

        request = RunRequest(
            prompt=composed_prompt,
            conversation=self.current_conversation,
            config=self.config.openclaude,
            attachments=[attachment.path for attachment in attachments],
        )
        self.runner.start(request)

    def _compose_prompt_with_attachments(self, prompt: str, attachments: list[Attachment]) -> str:
        if not attachments:
            return prompt
        lines = [prompt.strip(), "", "Attached local files:"]
        for attachment in attachments:
            prefix = "image" if attachment.kind == "image" else "file"
            lines.append(f"- {prefix}: {attachment.path}")
        lines.append("")
        lines.append("Use these local files as context when answering.")
        return "\n".join(lines).strip()

    def _append_message(self, message: ChatMessage, index: int) -> None:
        rendered = self.render_service.render_message(message.role, message.content, self.config.appearance.theme)
        code_blocks = [CodeBlock(language=language, code=code) for language, code in rendered.code_blocks]
        attachments = [
            AttachmentPreview(path=attachment.path, name=attachment.name, kind=attachment.kind)
            for attachment in message.attachments
        ]
        card = MessageCard(
            message.role,
            rendered.html,
            code_blocks,
            self._colors["muted"],
            attachments=attachments,
            footer_text=self._message_footer(message, index),
        )
        card.copy_requested.connect(self._copy_payload)
        self.chat_layout.insertWidget(max(0, self.chat_layout.count() - 1), card)
        self._scroll_chat_to_bottom()

    def _message_footer(self, message: ChatMessage, index: int) -> str:
        if message.role != "assistant":
            return ""
        current_code = self.render_service.extract_last_code_block(message.content)
        if not current_code.strip():
            return ""
        previous_code = ""
        for previous in reversed(self.current_conversation.messages[:index]):
            if previous.role != "assistant":
                continue
            previous_code = self.render_service.extract_last_code_block(previous.content)
            if previous_code.strip():
                break
        if not previous_code.strip():
            return "Code block detected in this reply."
        diff = list(unified_diff(previous_code.splitlines(), current_code.splitlines(), lineterm=""))
        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
        return f"Code diff vs previous assistant reply: +{added} / -{removed} changed lines."

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
        self._hide_stream_card()
        self._refresh_sidebar()
        self._show_conversation(self.current_conversation)

    def _handle_session_initialized(self, session_id: str) -> None:
        self.current_conversation.openclaude_session_id = session_id
        self.conversation_service.save(self.current_conversation)
        self._refresh_sidebar()
        self._refresh_session_panel()

    def _handle_status_changed(self, text: str) -> None:
        self.status_label.setText(text)

    def _handle_permission_requested(self, permission: dict) -> None:
        self._pending_permission = permission
        self.permission_status_label.setText(permission.get("details", "OpenClaude requested approval."))
        self.chat_mode_label.setText("Mode: waiting for approval")
        self._refresh_session_panel()

    def _handle_permission_resolved(self, permission: dict) -> None:
        self._pending_permission = None
        self.current_conversation.permission_history.append(permission)
        self.conversation_service.save(self.current_conversation)
        self.permission_status_label.setText("Approval sent to OpenClaude.")
        self.chat_mode_label.setText("Mode: resumed after approval")
        self._show_conversation(self.current_conversation)

    def _respond_to_permission(self, approved: bool) -> None:
        if not self._pending_permission:
            self.status_label.setText("No pending permission request")
            return
        self.runner.respond_to_permission(approved)

    def _refresh_sidebar(self) -> None:
        self.sidebar_list.clear()
        conversations = {self.current_conversation.id: self.current_conversation}
        for conversation in self.conversation_service.list_conversations():
            conversations[conversation.id] = conversation
        query = self.search_edit.text().strip().lower() if hasattr(self, "search_edit") else ""
        query_terms = [term for term in query.split() if term]
        ordered = sorted(conversations.values(), key=lambda item: item.updated_at, reverse=True)
        ordered.sort(key=lambda item: item.pinned, reverse=True)
        for conversation in ordered:
            haystack = " ".join(
                [
                    conversation.title,
                    " ".join(conversation.tags),
                    " ".join(message.content for message in conversation.messages[-8:]),
                ]
            ).lower()
            if query_terms and not all(term in haystack for term in query_terms):
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
            self.workspace_label.setText(self.config.openclaude.working_directory or str(Path.cwd()))
            self._apply_theme()
            self._show_conversation(self.current_conversation)

    def export_chat(self) -> None:
        if not self.current_conversation.messages:
            return
        default_path = self.export_service.make_default_path(self.current_conversation, "md")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export conversation",
            str(default_path),
            "Markdown (*.md);;HTML (*.html);;Text (*.txt);;JSON (*.json)",
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() == ".json":
            exported = self.conversation_service.export_json(self.current_conversation, target)
        else:
            exported = self.export_service.export_to_path(self.current_conversation, target)
        QMessageBox.information(self, "Exported", f"Conversation exported to:\n{exported}")

    def import_chat(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import conversation",
            str(self.settings_service.paths.exports_dir),
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            conversation = self.conversation_service.import_json(Path(path))
        except Exception as exc:
            self._show_error(f"Failed to import conversation: {exc}")
            return
        self.current_conversation = conversation
        self._refresh_sidebar()
        self._show_conversation(conversation)

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
        if not ok or not text.strip():
            return
        self.current_conversation.title = text.strip()
        self.conversation_service.save(self.current_conversation)
        self._refresh_sidebar()
        self._show_conversation(self.current_conversation)

    def duplicate_current_chat(self) -> None:
        duplicated = self.conversation_service.duplicate(self.current_conversation)
        self.current_conversation = duplicated
        self._refresh_sidebar()
        self._show_conversation(duplicated)

    def toggle_pin_current_chat(self) -> None:
        self.current_conversation.pinned = not self.current_conversation.pinned
        self.conversation_service.save(self.current_conversation)
        self._refresh_sidebar()
        self._show_conversation(self.current_conversation)

    def edit_tags(self) -> None:
        current = ", ".join(self.current_conversation.tags)
        text, ok = QInputDialog.getText(self, "Edit tags", "Comma-separated tags:", text=current)
        if not ok:
            return
        self.current_conversation.tags = [tag.strip() for tag in text.split(",") if tag.strip()]
        self.conversation_service.save(self.current_conversation)
        self._refresh_sidebar()
        self._show_conversation(self.current_conversation)

    def delete_current_chat(self) -> None:
        if not self.current_conversation.messages and not self.current_conversation.event_log:
            self.new_chat()
            return
        answer = QMessageBox.question(self, "Delete chat", f"Delete '{self.current_conversation.title}'?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.conversation_service.delete(self.current_conversation.id)
        remaining = self.conversation_service.list_conversations()
        self.current_conversation = remaining[0] if remaining else Conversation()
        self._refresh_sidebar()
        self._show_conversation(self.current_conversation)

    def edit_last_prompt(self) -> None:
        for message in reversed(self.current_conversation.messages):
            if message.role != "user":
                continue
            self.composer.setPlainText(message.content)
            self._pending_attachments = list(message.attachments)
            self._refresh_attachment_preview()
            self.status_label.setText("Loaded last prompt into the composer")
            return
        self.status_label.setText("No user prompt found")

    def regenerate_last_reply(self) -> None:
        if self.runner.is_running:
            self.status_label.setText("Wait for the current run to finish first")
            return
        for message in reversed(self.current_conversation.messages):
            if message.role != "user":
                continue
            self.composer.setPlainText(message.content)
            self._pending_attachments = list(message.attachments)
            self._refresh_attachment_preview()
            self.send_prompt()
            return
        self.status_label.setText("No user prompt available to regenerate")

    def continue_last_reply(self) -> None:
        if self.runner.is_running:
            self.status_label.setText("OpenClaude is already running")
            return
        self.composer.setPlainText("Continue from the previous answer and finish the task.")
        self.send_prompt()

    def attach_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Attach files", str(Path.cwd()))
        if paths:
            self._add_attachments(paths)

    def _handle_dropped_files(self, paths: list[str]) -> None:
        self._add_attachments(paths)

    def _add_attachments(self, paths: list[str]) -> None:
        existing = {attachment.path for attachment in self._pending_attachments}
        for raw_path in paths:
            path = Path(raw_path)
            if not path.exists() or str(path) in existing:
                continue
            kind = "image" if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"} else "file"
            self._pending_attachments.append(Attachment(path=str(path), name=path.name, kind=kind))
            existing.add(str(path))
        self._refresh_attachment_preview()
        self.status_label.setText(f"{len(self._pending_attachments)} attachment(s) ready")

    def _refresh_attachment_preview(self) -> None:
        previews = [
            AttachmentPreview(path=attachment.path, name=attachment.name, kind=attachment.kind)
            for attachment in self._pending_attachments
        ]
        self.attachment_list.set_attachments(previews)

    def _remove_selected_attachment(self, item: QListWidgetItem) -> None:
        target = item.data(Qt.ItemDataRole.UserRole)
        self._pending_attachments = [attachment for attachment in self._pending_attachments if attachment.path != target]
        self._refresh_attachment_preview()

    def clear_attachments(self) -> None:
        self._pending_attachments.clear()
        if hasattr(self, "attachment_list"):
            self.attachment_list.clear()

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
        copy_to_clipboard("\n".join(str(event) for event in self.current_conversation.event_log))
        self.status_label.setText("Events copied to clipboard")

    def copy_last_assistant_message(self) -> None:
        for message in reversed(self.current_conversation.messages):
            if message.role == "assistant" and message.content.strip():
                copy_to_clipboard(message.content)
                self.status_label.setText("Last reply copied")
                return
        self.status_label.setText("No assistant reply to copy")

    def copy_last_code_block(self) -> None:
        for message in reversed(self.current_conversation.messages):
            if message.role != "assistant":
                continue
            code = self.render_service.extract_last_code_block(message.content)
            if code:
                copy_to_clipboard(code)
                self.status_label.setText("Last code block copied")
                return
        self.status_label.setText("No code block found")

    def toggle_theme(self) -> None:
        self.config.appearance.theme = "light" if self.config.appearance.theme == "dark" else "dark"
        self.settings_service.save(self.config)
        self._apply_theme()
        self._show_conversation(self.current_conversation)

    def _apply_theme(self) -> None:
        self._colors = theme_colors(self.config.appearance.theme)
        self.setStyleSheet(build_stylesheet(self.config.appearance.theme))
        self.theme_badge.setStyleSheet(
            f"background:{self._colors['accent_soft']}; color:{self._colors['accent']};"
            "padding:6px 10px; border-radius:10px; font-weight:600;"
        )
        self.tags_badge.setStyleSheet(
            f"background:{self._colors['surface_alt']}; color:{self._colors['muted']};"
            "padding:6px 10px; border-radius:10px;"
        )
        self._refresh_theme_action()
        self._refresh_session_panel()
        self._refresh_attachment_preview()

    def _refresh_theme_action(self) -> None:
        is_dark = self.config.appearance.theme == "dark"
        self.theme_toggle_action.setIcon(qta.icon("fa6s.sun") if is_dark else qta.icon("fa6s.moon"))
        self.theme_toggle_action.setText("Light Mode" if is_dark else "Dark Mode")

    def _open_sidebar_context_menu(self, position) -> None:
        item = self.sidebar_list.itemAt(position)
        menu = QMenu(self)
        import_action = menu.addAction("Import conversation")
        if item is None:
            chosen = menu.exec(self.sidebar_list.mapToGlobal(position))
            if chosen == import_action:
                self.import_chat()
            return
        self.current_conversation = item.data(Qt.ItemDataRole.UserRole)
        rename_action = menu.addAction("Rename")
        duplicate_action = menu.addAction("Duplicate")
        tag_action = menu.addAction("Edit tags")
        pin_action = menu.addAction("Unpin" if self.current_conversation.pinned else "Pin")
        delete_action = menu.addAction("Delete")
        menu.addSeparator()
        export_action = menu.addAction("Export")
        chosen = menu.exec(self.sidebar_list.mapToGlobal(position))
        if chosen == rename_action:
            self.rename_current_chat()
        elif chosen == duplicate_action:
            self.duplicate_current_chat()
        elif chosen == tag_action:
            self.edit_tags()
        elif chosen == pin_action:
            self.toggle_pin_current_chat()
        elif chosen == delete_action:
            self.delete_current_chat()
        elif chosen == export_action:
            self.export_chat()

    def _copy_payload(self, text: str) -> None:
        copy_to_clipboard(text)
        self.status_label.setText("Copied to clipboard")

    def _clear_chat_cards(self) -> None:
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _show_stream_card(self) -> None:
        self._hide_stream_card()
        self._stream_card = MessageStreamCard(self._colors["muted"])
        self._stream_card.stop_requested.connect(self.runner.stop)
        self.chat_layout.insertWidget(max(0, self.chat_layout.count() - 1), self._stream_card)
        self._scroll_chat_to_bottom()

    def _hide_stream_card(self) -> None:
        if self._stream_card is not None:
            self._stream_card.deleteLater()
            self._stream_card = None

    def _scroll_chat_to_bottom(self) -> None:
        bar = self.chat_scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _handle_runtime_state_changed(self, state: dict) -> None:
        self._runtime_state = state
        self._refresh_session_panel()

    def _refresh_session_panel(self) -> None:
        provider = self._runtime_state.get("provider") or self.config.openclaude.provider_name or "Custom"
        model = self._runtime_state.get("model") or self.config.openclaude.model or "default"
        status = self._runtime_state.get("status", "idle")
        details = self._runtime_state.get("details", "")
        workspace = self._runtime_state.get("workspace") or self.config.openclaude.working_directory or str(Path.cwd())
        session_id = self._runtime_state.get("session_id") or self.current_conversation.openclaude_session_id or "not started"
        self.provider_label.setText(f"Provider: {provider}")
        self.model_label.setText(f"Model: {model}")
        self.connection_label.setText(f"Connection: {status}")
        self.workspace_detail_label.setText(f"Workspace: {workspace}")
        self.session_label.setText(f"Session: {session_id}")
        if details and status in {"error", "permission_required"}:
            self.permission_status_label.setText(details)
        elif not self._pending_permission:
            self.permission_status_label.setText("No approval needed right now.")
        enabled = self._pending_permission is not None
        self.permission_approve_button.setEnabled(enabled)
        self.permission_reject_button.setEnabled(enabled)
        if status == "permission_required":
            self.chat_mode_label.setText("Mode: waiting for approval")
        elif self.runner.is_running:
            self.chat_mode_label.setText("Mode: streaming")
        else:
            self.chat_mode_label.setText("Mode: standard")

    def _show_error(self, message: str) -> None:
        self.logger.error(message)
        self._hide_stream_card()
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("OpenClaude Error")
        box.setText("OpenClaude reported a problem.")
        box.setInformativeText(message[:300])
        box.setDetailedText(message)
        box.exec()
