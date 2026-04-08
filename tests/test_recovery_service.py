from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openclaude_studio.services.recovery_service import RecoveryService


class RecoveryServiceTests(unittest.TestCase):
    def test_save_and_load_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = RecoveryService(Path(temp_dir) / "state.json")
            service.save_state("conv-1", "draft", [{"path": "a.txt", "name": "a.txt", "kind": "file"}])
            state = service.load_state()
            self.assertEqual(state["conversation_id"], "conv-1")
            self.assertEqual(state["draft"], "draft")
            self.assertEqual(state["attachments"][0]["name"], "a.txt")


if __name__ == "__main__":
    unittest.main()
