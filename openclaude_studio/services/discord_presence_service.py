from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from openclaude_studio.models.config import DiscordConfig
from openclaude_studio.services.logging_service import get_logger

try:
    from pypresence import Presence
except Exception:  # pragma: no cover - optional dependency
    Presence = None


@dataclass
class PresenceState:
    details: str
    state: str


class DiscordPresenceService:
    def __init__(self, config: DiscordConfig) -> None:
        self.config = config
        self._logger = get_logger(__name__)
        self._client = None
        self._connected = False
        self._started_at = int(datetime.now().timestamp())
        self._last_payload: dict | None = None

    @property
    def available(self) -> bool:
        return Presence is not None

    def connect(self) -> None:
        if not self.config.enabled or not self.available or self._connected:
            return
        try:
            self._client = Presence(self.config.client_id)
            self._client.connect()
            self._connected = True
        except Exception as exc:  # pragma: no cover - runtime integration
            self._logger.warning("Discord RPC connection failed: %s", exc)
            self._client = None
            self._connected = False

    def disconnect(self) -> None:
        if self._client is None:
            return
        try:
            self._client.close()
        except Exception as exc:  # pragma: no cover - runtime integration
            self._logger.debug("Discord RPC close failed: %s", exc)
        finally:
            self._client = None
            self._connected = False

    def update(
        self,
        details: str,
        state: str,
        workspace: str = "",
        provider: str = "",
        buttons: list[dict] | None = None,
    ) -> None:
        if not self.config.enabled:
            self.disconnect()
            return
        self.connect()
        if not self._connected or self._client is None:
            return

        small_text_parts: list[str] = []
        if self.config.show_provider and provider:
            small_text_parts.append(provider)
        if self.config.show_workspace and workspace:
            small_text_parts.append(Path(workspace).name or workspace)
        small_text = " • ".join(small_text_parts)[:128]

        payload = {
            "details": details[:128],
            "state": state[:128],
            "large_image": "openclaude_studio",
            "large_text": "Openclaude Studio",
            "small_image": "openclaude_studio",
            "small_text": small_text or "Desktop client",
            "start": self._started_at,
        }
        if buttons:
            payload["buttons"] = buttons[:2]
        if payload == self._last_payload:
            return
        try:
            self._client.update(**payload)
            self._last_payload = payload
        except Exception as exc:  # pragma: no cover - runtime integration
            self._logger.warning("Discord RPC update failed: %s", exc)

    def set_idle(self, conversation_title: str, workspace: str = "", provider: str = "") -> None:
        self.update(
            details="Openclaude Studio",
            state=f"Idle in {conversation_title[:80] or 'New chat'}",
            workspace=workspace,
            provider=provider,
        )

    def set_running(self, conversation_title: str, workspace: str = "", provider: str = "") -> None:
        self.update(
            details="Working with OpenClaude",
            state=f"Active chat: {conversation_title[:80] or 'New chat'}",
            workspace=workspace,
            provider=provider,
        )

    def set_waiting_approval(self, conversation_title: str, workspace: str = "", provider: str = "") -> None:
        self.update(
            details="Waiting for approval",
            state=f"Chat: {conversation_title[:80] or 'New chat'}",
            workspace=workspace,
            provider=provider,
        )
