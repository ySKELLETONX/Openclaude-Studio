from __future__ import annotations

import unittest
from pathlib import Path

from openclaude_studio.services.language_service import LanguageService


class LanguageServiceTests(unittest.TestCase):
    def test_loads_known_translation(self) -> None:
        service = LanguageService(Path.cwd() / "languages", "pt_br.xml")
        self.assertEqual(service.t("toolbar.settings", "Settings"), "Configurações")
        service.set_language("en.US.xml")
        self.assertEqual(service.t("toolbar.settings", "Settings"), "Settings")


if __name__ == "__main__":
    unittest.main()
