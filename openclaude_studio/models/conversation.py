from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class Attachment:
    path: str
    name: str
    kind: str = "file"


@dataclass
class ChatMessage:
    role: str
    content: str
    created_at: str = field(default_factory=utc_now)
    metadata: dict = field(default_factory=dict)
    attachments: list[Attachment] = field(default_factory=list)


@dataclass
class Conversation:
    id: str = field(default_factory=lambda: str(uuid4()))
    title: str = "New chat"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    openclaude_session_id: str = ""
    messages: list[ChatMessage] = field(default_factory=list)
    event_log: list[dict] = field(default_factory=list)
    permission_history: list[dict] = field(default_factory=list)
    pinned: bool = False
    tags: list[str] = field(default_factory=list)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def add_message(
        self,
        role: str,
        content: str,
        metadata: dict | None = None,
        attachments: list[Attachment] | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata or {},
            attachments=list(attachments or []),
        )
        self.messages.append(message)
        if self.title == "New chat" and role == "user":
            self.title = content.strip()[:48] or "New chat"
        self.touch()
        return message

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict) -> "Conversation":
        messages = []
        for item in payload.get("messages", []):
            attachments = [Attachment(**attachment) for attachment in item.get("attachments", [])]
            messages.append(
                ChatMessage(
                    role=item["role"],
                    content=item.get("content", ""),
                    created_at=item.get("created_at", utc_now()),
                    metadata=dict(item.get("metadata", {})),
                    attachments=attachments,
                )
            )
        return cls(
            id=payload["id"],
            title=payload.get("title", "New chat"),
            created_at=payload.get("created_at", utc_now()),
            updated_at=payload.get("updated_at", utc_now()),
            openclaude_session_id=payload.get("openclaude_session_id", ""),
            messages=messages,
            event_log=list(payload.get("event_log", [])),
            permission_history=list(payload.get("permission_history", [])),
            pinned=bool(payload.get("pinned", False)),
            tags=list(payload.get("tags", [])),
        )
