from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


class LanguageService:
    def __init__(self, languages_dir: Path, language_file: str) -> None:
        self.languages_dir = languages_dir
        self.languages_dir.mkdir(parents=True, exist_ok=True)
        self.language_file = language_file
        self._strings: dict[str, str] = {}
        self.load(language_file)

    def available_languages(self) -> list[str]:
        return sorted(path.name for path in self.languages_dir.glob("*.xml"))

    def load(self, language_file: str) -> None:
        target = self.languages_dir / language_file
        if not target.exists():
            fallback = self.languages_dir / "en.US.xml"
            target = fallback if fallback.exists() else target
        self.language_file = target.name
        self._strings = self._read_strings(target) if target.exists() else {}

    def set_language(self, language_file: str) -> None:
        self.load(language_file)

    def t(self, key: str, fallback: str = "") -> str:
        return self._strings.get(key, fallback or key)

    def _read_strings(self, target: Path) -> dict[str, str]:
        root = ET.fromstring(target.read_text(encoding="utf-8"))
        strings: dict[str, str] = {}
        for item in root.findall("./string"):
            key = item.attrib.get("key", "").strip()
            if not key:
                continue
            strings[key] = item.text or ""
        return strings
