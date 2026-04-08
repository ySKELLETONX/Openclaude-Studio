from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from openclaude_studio.models.conversation import Conversation


class ConversationService:
    def __init__(self, conversations_dir: Path) -> None:
        self.conversations_dir = conversations_dir
        self.conversations_dir.mkdir(parents=True, exist_ok=True)

    def list_conversations(self) -> list[Conversation]:
        conversations: list[Conversation] = []
        for path in sorted(self.conversations_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            conversations.append(Conversation.from_dict(payload))
        conversations.sort(key=lambda item: item.updated_at, reverse=True)
        return conversations

    def save(self, conversation: Conversation) -> None:
        file_path = self.conversations_dir / f"{conversation.id}.json"
        file_path.write_text(
            json.dumps(conversation.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def duplicate(self, conversation: Conversation) -> Conversation:
        payload = deepcopy(conversation.to_dict())
        payload["id"] = Conversation().id
        payload["title"] = f"{conversation.title} Copy"
        payload["openclaude_session_id"] = ""
        duplicated = Conversation.from_dict(payload)
        duplicated.touch()
        self.save(duplicated)
        return duplicated

    def export_json(self, conversation: Conversation, target: Path) -> Path:
        target.write_text(json.dumps(conversation.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return target

    def import_json(self, source: Path) -> Conversation:
        payload = json.loads(source.read_text(encoding="utf-8"))
        conversation = Conversation.from_dict(payload)
        if (self.conversations_dir / f"{conversation.id}.json").exists():
            conversation.id = Conversation().id
        conversation.touch()
        self.save(conversation)
        return conversation

    def delete(self, conversation_id: str) -> None:
        file_path = self.conversations_dir / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
