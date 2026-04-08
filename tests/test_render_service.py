from __future__ import annotations

import unittest

from openclaude_studio.services.render_service import RenderService


class RenderServiceTests(unittest.TestCase):
    def test_render_message_collects_code_blocks(self) -> None:
        service = RenderService()
        rendered = service.render_message("assistant", "```python\nprint('hi')\n```", "dark")
        self.assertIn("python", rendered.code_blocks[0][0])
        self.assertIn("print('hi')", rendered.code_blocks[0][1])
        self.assertIn("copy below", rendered.html)


if __name__ == "__main__":
    unittest.main()
