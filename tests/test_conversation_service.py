from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from openclaude_studio.models.conversation import Attachment, Conversation
from openclaude_studio.services.conversation_service import ConversationService


class ConversationServiceTests(unittest.TestCase):
    def test_duplicate_and_import_export_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = ConversationService(Path(temp_dir))
            conversation = Conversation(title="Alpha")
            conversation.tags = ["gui", "release"]
            conversation.pinned = True
            conversation.add_message(
                "user",
                "Hello",
                attachments=[Attachment(path="C:/tmp/image.png", name="image.png", kind="image")],
            )
            service.save(conversation)

            duplicated = service.duplicate(conversation)
            self.assertNotEqual(duplicated.id, conversation.id)
            self.assertEqual(duplicated.openclaude_session_id, "")

            exported = service.export_json(conversation, Path(temp_dir) / "export.json")
            imported = service.import_json(exported)
            self.assertEqual(imported.title, "Alpha")
            self.assertEqual(imported.tags, ["gui", "release"])
            self.assertTrue(imported.pinned)


if __name__ == "__main__":
    unittest.main()
