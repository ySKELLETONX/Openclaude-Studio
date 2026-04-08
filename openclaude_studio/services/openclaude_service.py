from __future__ import annotations

import json
import os
import shlex
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, QProcess, pyqtSignal

from openclaude_studio.models.config import OpenClaudeConfig
from openclaude_studio.models.conversation import Conversation
from openclaude_studio.services.logging_service import get_logger


@dataclass
class RunRequest:
    prompt: str
    conversation: Conversation
    config: OpenClaudeConfig
    attachments: list[str] | None = None


class OpenClaudeRunner(QObject):
    assistant_delta = pyqtSignal(str)
    event_received = pyqtSignal(dict)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    result_ready = pyqtSignal(dict)
    session_initialized = pyqtSignal(str)
    runtime_state_changed = pyqtSignal(dict)
    permission_requested = pyqtSignal(dict)
    permission_resolved = pyqtSignal(dict)

    def __init__(self) -> None:
        super().__init__()
        self._logger = get_logger(__name__)
        self._process: QProcess | None = None
        self._stdout_buffer = ""
        self._stderr_buffer = ""
        self._partial_text = ""
        self._last_session_id = ""
        self._result_emitted = False
        self._request_config: OpenClaudeConfig | None = None
        self._pending_permission: dict | None = None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning

    def stop(self) -> None:
        if self._process is not None and self.is_running:
            self.status_changed.emit("Stopping OpenClaude...")
            self._process.kill()

    def respond_to_permission(self, approved: bool, note: str = "") -> None:
        if self._process is None or not self.is_running:
            return
        payload = "y"
        if not approved:
            payload = "n"
        if note.strip():
            payload = f"{payload} {note.strip()}"
        payload += "\n"
        self._process.write(payload.encode("utf-8"))
        details = dict(self._pending_permission or {})
        details.update({"approved": approved, "note": note.strip()})
        self.permission_resolved.emit(details)
        self.runtime_state_changed.emit(
            {
                "status": "running",
                "provider": self._request_config.provider_name if self._request_config else "Custom",
                "model": self._request_config.model if self._request_config else "",
                "workspace": self._request_config.working_directory if self._request_config else str(Path.cwd()),
                "session_id": self._last_session_id,
            }
        )
        self._pending_permission = None

    def start(self, request: RunRequest) -> None:
        if self.is_running:
            self.error_occurred.emit("OpenClaude is already running.")
            return

        self._stdout_buffer = ""
        self._stderr_buffer = ""
        self._partial_text = ""
        self._last_session_id = request.conversation.openclaude_session_id
        self._result_emitted = False
        self._request_config = request.config
        self._pending_permission = None

        process = QProcess(self)
        process.setProgram(request.config.executable)
        process.setArguments(self._build_arguments(request))
        process.setWorkingDirectory(request.config.working_directory or str(Path.cwd()))
        process.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)

        env = os.environ.copy()
        env.update({key: value for key, value in request.config.environment.items() if value})
        if request.config.print_options.streamlined_output:
            env["CLAUDE_CODE_STREAMLINED_OUTPUT"] = "true"

        process_env = process.processEnvironment()
        for key, value in env.items():
            process_env.insert(key, str(value))
        process.setProcessEnvironment(process_env)

        process.readyReadStandardOutput.connect(self._handle_stdout)
        process.readyReadStandardError.connect(self._handle_stderr)
        process.finished.connect(self._handle_finished)
        process.errorOccurred.connect(self._handle_process_error)

        self._process = process
        self._logger.info("Launching OpenClaude: %s %s", request.config.executable, " ".join(process.arguments()))
        self.status_changed.emit("Running OpenClaude...")
        self.runtime_state_changed.emit(
            {
                "status": "running",
                "provider": request.config.provider_name,
                "model": request.config.model or self._infer_model(request.config.environment),
                "workspace": request.config.working_directory or str(Path.cwd()),
                "session_id": self._last_session_id,
            }
        )
        process.start()

    def _build_arguments(self, request: RunRequest) -> list[str]:
        config = request.config
        args = ["--print", "--verbose", "--output-format", "stream-json"]
        if request.conversation.openclaude_session_id:
            args.extend(["--resume", request.conversation.openclaude_session_id])
        if config.model:
            args.extend(["--model", config.model])
        if config.system_prompt:
            args.extend(["--system-prompt", config.system_prompt])
        if config.append_system_prompt:
            args.extend(["--append-system-prompt", config.append_system_prompt])
        if config.print_options.include_partial_messages:
            args.append("--include-partial-messages")
        if config.print_options.include_hook_events:
            args.append("--include-hook-events")
        if config.print_options.bare_mode:
            args.append("--bare")
        if config.print_options.dangerously_skip_permissions:
            args.append("--dangerously-skip-permissions")
        if config.extra_args.strip():
            args.extend(shlex.split(config.extra_args, posix=False))
        args.append(request.prompt)
        return args

    def _handle_stdout(self) -> None:
        if self._process is None:
            return
        chunk = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self._stdout_buffer += chunk
        while "\n" in self._stdout_buffer:
            line, self._stdout_buffer = self._stdout_buffer.split("\n", 1)
            line = line.strip()
            if line:
                self._parse_stream_line(line)

    def _handle_stderr(self) -> None:
        if self._process is None:
            return
        chunk = bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace")
        self._stderr_buffer += chunk
        if chunk.strip():
            if "permission" in chunk.lower():
                self._emit_permission_request(chunk.strip(), "stderr")
            self.status_changed.emit(chunk.strip())

    def _parse_stream_line(self, line: str) -> None:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            self.event_received.emit({"type": "raw", "text": line})
            return

        self.event_received.emit(payload)
        self._last_session_id = payload.get("session_id", self._last_session_id)

        message_type = payload.get("type")
        if message_type == "streamlined_text":
            text = payload.get("text", "")
            self._partial_text += text
            self.assistant_delta.emit(text)
        elif message_type == "assistant":
            text = self._extract_assistant_text(payload)
            if text:
                self._partial_text += text
                self.assistant_delta.emit(text)
        elif message_type == "result":
            self._result_emitted = True
            self.result_ready.emit(
                {
                    "result": payload.get("result", self._partial_text),
                    "is_error": payload.get("is_error", False),
                    "session_id": self._last_session_id,
                    "payload": payload,
                }
            )
        elif message_type == "system":
            subtype = payload.get("subtype", "system")
            if subtype == "init":
                if self._last_session_id:
                    self.session_initialized.emit(self._last_session_id)
                self.status_changed.emit(f"Connected to session {self._last_session_id or 'new'}")
                self.runtime_state_changed.emit(
                    {
                        "status": "connected",
                        "provider": self._request_config.provider_name if self._request_config else "Custom",
                        "model": self._request_config.model if self._request_config else "",
                        "workspace": self._request_config.working_directory if self._request_config else "",
                        "session_id": self._last_session_id,
                    }
                )
            elif subtype in {"hook_progress", "task_progress"}:
                self.status_changed.emit(payload.get("output") or payload.get("description") or subtype)
            elif subtype in {"permission_request", "approval_required"}:
                details = payload.get("output") or payload.get("description") or "OpenClaude requested approval."
                self._emit_permission_request(details, subtype, payload)
        elif message_type in {"tool_progress", "tool_use_summary"}:
            self.status_changed.emit(payload.get("summary") or payload.get("tool_name", "Tool running"))
        elif message_type in {"permission_request", "approval_required"}:
            details = payload.get("output") or payload.get("description") or payload.get("message") or "OpenClaude requested approval."
            self._emit_permission_request(details, message_type, payload)

    def _extract_assistant_text(self, payload: dict) -> str:
        message = payload.get("message", {})
        blocks = message.get("content", [])
        parts: list[str] = []
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)

    def _handle_finished(self, exit_code: int, _exit_status) -> None:
        self._logger.info("OpenClaude finished with exit code %s", exit_code)
        if not self._result_emitted and self._partial_text:
            self.result_ready.emit(
                {
                    "result": self._partial_text,
                    "is_error": exit_code != 0,
                    "session_id": self._last_session_id,
                    "payload": {},
                }
            )
        if self._stderr_buffer.strip() and exit_code != 0:
            self.error_occurred.emit(self._stderr_buffer.strip())
            self.runtime_state_changed.emit({"status": "error", "details": self._stderr_buffer.strip(), "session_id": self._last_session_id})
        else:
            self.runtime_state_changed.emit({"status": "idle", "session_id": self._last_session_id})
        self.status_changed.emit("Ready")
        self._process = None

    def _handle_process_error(self, error) -> None:
        message = f"Failed to start OpenClaude: {error}"
        self.error_occurred.emit(message)
        self.runtime_state_changed.emit({"status": "error", "details": message, "session_id": self._last_session_id})

    def _emit_permission_request(self, details: str, source: str, payload: dict | None = None) -> None:
        permission = {
            "details": details.strip(),
            "source": source,
            "session_id": self._last_session_id,
            "payload": payload or {},
        }
        self._pending_permission = permission
        self.permission_requested.emit(permission)
        self.runtime_state_changed.emit(
            {
                "status": "permission_required",
                "details": details.strip(),
                "session_id": self._last_session_id,
            }
        )

    def _infer_model(self, environment: dict[str, str]) -> str:
        for key in ("OPENAI_MODEL", "ANTHROPIC_MODEL", "GEMINI_MODEL"):
            if environment.get(key):
                return environment[key]
        return ""
