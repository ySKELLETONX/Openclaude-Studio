from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class TelemetryService:
    def __init__(self, target: Path, enabled: bool = True) -> None:
        self.target = target
        self.enabled = enabled
        self.target.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, payload: dict) -> None:
        if not self.enabled:
            return
        envelope = {
            "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "type": event_type,
            "payload": payload,
        }
        with self.target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(envelope, ensure_ascii=False) + "\n")

    def record_error(self, source: str, message: str, context: dict | None = None) -> None:
        self.record(
            "error",
            {
                "source": source,
                "message": message,
                "context": context or {},
            },
        )
