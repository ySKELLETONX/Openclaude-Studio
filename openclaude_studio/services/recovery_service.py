from __future__ import annotations

import json
from pathlib import Path


class RecoveryService:
    def __init__(self, target: Path) -> None:
        self.target = target
        self.target.parent.mkdir(parents=True, exist_ok=True)

    def save_state(self, conversation_id: str, draft: str, attachments: list[dict]) -> None:
        payload = {
            "conversation_id": conversation_id,
            "draft": draft,
            "attachments": attachments,
        }
        self.target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_state(self) -> dict:
        if not self.target.exists():
            return {}
        return json.loads(self.target.read_text(encoding="utf-8"))

    def clear_state(self) -> None:
        if self.target.exists():
            self.target.unlink()
