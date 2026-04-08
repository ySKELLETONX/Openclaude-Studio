from __future__ import annotations

import unittest

from openclaude_studio.models.config import DiscordConfig
from openclaude_studio.services.discord_presence_service import DiscordPresenceService


class DiscordPresenceServiceTests(unittest.TestCase):
    def test_disabled_presence_disconnects_cleanly(self) -> None:
        service = DiscordPresenceService(DiscordConfig(enabled=False))
        service.update("Openclaude Studio", "Idle")
        self.assertFalse(service._connected)


if __name__ == "__main__":
    unittest.main()
