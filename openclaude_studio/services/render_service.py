from __future__ import annotations

from html import escape

from markdown_it import MarkdownIt


class RenderService:
    def __init__(self) -> None:
        self._md = MarkdownIt("commonmark", {"breaks": True, "html": False})

    def render_message(self, role: str, content: str) -> str:
        color = {
            "user": "#d9ecff",
            "assistant": "#f6f8fb",
            "system": "#d7dfeb",
        }.get(role, "#f6f8fb")
        background = {
            "user": "#284969",
            "assistant": "#171e28",
            "system": "#1d2632",
        }.get(role, "#171e28")

        body = self._render_body(content)
        return (
            f"<section style='margin:12px 0;padding:16px 18px;border-radius:18px;background:{background};"
            "border:1px solid rgba(255,255,255,0.05);'>"
            f"<div style='font-size:11px;color:#8ea4bb;margin-bottom:10px;text-transform:uppercase;"
            "letter-spacing:0.08em;'>"
            f"{escape(role)}</div>"
            f"<div style='color:{color}; line-height:1.55;'>{body}</div>"
            "</section>"
        )

    def _render_body(self, content: str) -> str:
        if not content.strip():
            return "<span style='color:#6f8193;'>Streaming...</span>"

        html = self._md.render(content)
        return (
            "<style>"
            "p{margin:0 0 10px 0;}"
            "pre{background:#0c1117;border:1px solid #293746;border-radius:14px;padding:14px;overflow:auto;}"
            "code{background:#0f1720;border-radius:6px;padding:2px 5px;}"
            "pre code{background:transparent;padding:0;}"
            "blockquote{border-left:3px solid #4aa3ff;margin:10px 0;padding-left:12px;color:#c8d4e0;}"
            "a{color:#7ec2ff;text-decoration:none;}"
            "ul,ol{margin:0 0 10px 22px;}"
            "</style>"
            + html
        )
