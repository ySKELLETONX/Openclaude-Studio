from __future__ import annotations

import unittest

from openclaude_studio.models.config import OpenClaudeConfig
from openclaude_studio.services.provider_test_service import ProviderTestService


class ProviderTestServiceTests(unittest.TestCase):
    def test_missing_executable_returns_failure(self) -> None:
        service = ProviderTestService()
        result = service.test(
            OpenClaudeConfig(
                executable="definitely-missing-openclaude",
                provider_name="OpenAI Compatible",
                environment={},
            )
        )
        self.assertFalse(result.ok)
        self.assertTrue(any("not found" in detail.lower() for detail in result.details))


if __name__ == "__main__":
    unittest.main()
