from __future__ import annotations

from html import escape
from html import unescape

from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

from openclaude_studio.ui.theme import theme_colors


class RenderService:
    def __init__(self) -> None:
        self._md = MarkdownIt("commonmark", {"breaks": True, "html": False})
        self._md.renderer.rules["fence"] = self._render_fence
        self._formatter = HtmlFormatter(nowrap=True)

    def render_message(self, role: str, content: str, theme_name: str = "dark") -> str:
        colors = theme_colors(theme_name)
        color = {
            "user": colors["text"],
            "assistant": colors["text"],
            "system": colors["muted"],
        }.get(role, colors["text"])
        background = {
            "user": colors["user_bubble"],
            "assistant": colors["assistant_bubble"],
            "system": colors["system_bubble"],
        }.get(role, colors["assistant_bubble"])

        body = self._render_body(content)
        return (
            f"<section style='margin:12px 0;padding:16px 18px;border-radius:18px;background:{background};"
            f"border:1px solid {colors['panel_border']};'>"
            f"<div style='font-size:11px;color:{colors['muted']};margin-bottom:10px;text-transform:uppercase;"
            "letter-spacing:0.08em;'>"
            f"{escape(role)}</div>"
            f"<div style='color:{color}; line-height:1.55;'>{body}</div>"
            "</section>"
        )

    def extract_last_code_block(self, content: str) -> str:
        tokens = self._md.parse(content)
        fences = [token.content for token in tokens if token.type == "fence" and token.content.strip()]
        return fences[-1] if fences else ""

    def _render_body(self, content: str) -> str:
        if not content.strip():
            return "<span style='color:#6f8193;'>Streaming...</span>"

        html = self._md.render(content)
        return (
            "<style>"
            "p{margin:0 0 10px 0;}"
            "pre{background:rgba(0,0,0,0.12);border:1px solid rgba(127,127,127,0.22);border-radius:14px;padding:14px;overflow:auto;}"
            "code{background:rgba(127,127,127,0.14);border-radius:6px;padding:2px 5px;}"
            "pre code{background:transparent;padding:0;}"
            "blockquote{border-left:3px solid #4aa3ff;margin:10px 0;padding-left:12px;}"
            "a{color:#2f80ed;text-decoration:none;}"
            "ul,ol{margin:0 0 10px 22px;}"
            "</style>"
            + html
        )

    def _render_fence(self, tokens, idx, _options, _env) -> str:
        token = tokens[idx]
        info = (token.info or "").strip()
        language = info.split()[0] if info else "text"
        code = token.content.rstrip()
        highlighted = self._highlight_code(code, language)
        safe_language = escape(language.upper() if language else "TEXT")
        return (
            "<div style='margin:10px 0;'>"
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:8px 12px;border:1px solid rgba(127,127,127,0.22);border-bottom:none;"
            "border-top-left-radius:14px;border-top-right-radius:14px;background:rgba(127,127,127,0.08);"
            "font-size:11px;letter-spacing:0.08em;'>"
            f"<span>{safe_language}</span><span>copy from toolbar</span></div>"
            "<pre style='margin:0;border-top-left-radius:0;border-top-right-radius:0;'><code>"
            f"{highlighted}</code></pre></div>"
        )

    def _highlight_code(self, code: str, language: str) -> str:
        try:
            lexer = get_lexer_by_name(language, stripall=False)
        except ClassNotFound:
            lexer = TextLexer(stripall=False)
        rendered = highlight(code, lexer, self._formatter)
        return unescape(rendered)
