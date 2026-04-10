from __future__ import annotations


THEMES = {
    "dark": {
        "window": "#0c1117",
        "surface": "#121923",
        "surface_alt": "#192331",
        "sidebar": "#101720",
        "panel_border": "#26364a",
        "text": "#c8d1dc",
        "muted": "#8a96a3",
        "accent": "#4aa3ff",
        "accent_strong": "#ff7a59",
        "accent_soft": "#17293d",
        "input": "#0e151d",
        "input_border": "#294059",
        "hover": "#182330",
        "selected": "#1f3247",
        "user_bubble": "#17324d",
        "assistant_bubble": "#121b25",
        "system_bubble": "#18212c",
        "toolbar": "#101720",
        "success": "#4fd1a5",
    },
    "light": {
        "window": "#f3f7fc",
        "surface": "#ffffff",
        "surface_alt": "#ecf3fb",
        "sidebar": "#dfeaf6",
        "panel_border": "#cad8e8",
        "text": "#263443",
        "muted": "#67798d",
        "accent": "#2f80ed",
        "accent_strong": "#f26d4f",
        "accent_soft": "#e6f0ff",
        "input": "#f9fbff",
        "input_border": "#c5d6e8",
        "hover": "#e6eef8",
        "selected": "#dcecff",
        "user_bubble": "#dcecff",
        "assistant_bubble": "#ffffff",
        "system_bubble": "#eef4fb",
        "toolbar": "#e6eef7",
        "success": "#157f3b",
    },
}


def build_stylesheet(theme_name: str) -> str:
    colors = THEMES.get(theme_name, THEMES["dark"])
    return f"""
QWidget {{
    background: {colors["window"]};
    color: {colors["text"]};
    font-family: "Segoe UI Variable", "Segoe UI", "Inter";
    font-size: 9pt;
    font-weight: 400;
}}
QMainWindow, QDialog {{
    background: {colors["window"]};
}}
QLabel {{
    color: {colors["text"]};
}}
QToolTip {{
    color: {colors["text"]};
    background-color: {colors["surface"]};
    border: none;
    border-left: 3px solid {colors["accent_strong"]};
    padding: 7px 9px;
}}
QToolBar#TopBar {{
    background: {colors["toolbar"]};
    border: none;
    border-bottom: 1px solid {colors["panel_border"]};
    spacing: 8px;
    padding: 10px 14px;
}}
QToolBar#TopBar QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 11px;
    padding: 7px 12px;
    color: {colors["muted"]};
    font-size: 8.7pt;
    min-height: 18px;
}}
QToolBar#TopBar QToolButton:hover {{
    background: {colors["hover"]};
    border: 1px solid {colors["panel_border"]};
    color: {colors["text"]};
}}
QToolBar#TopBar QToolButton:pressed {{
    background: {colors["selected"]};
}}
QToolBar#TopBar QToolButton[accent="true"] {{
    background: {colors["surface_alt"]};
    border: 1px solid {colors["panel_border"]};
    color: {colors["text"]};
    font-weight: 600;
}}
QToolBar#TopBar QToolButton::menu-indicator {{
    width: 12px;
    subcontrol-origin: padding;
    subcontrol-position: right center;
}}
QFrame#Sidebar, QFrame#EventsPanel, QFrame#ComposerCard, QFrame#HeaderCard, QFrame#PermissionCard {{
    background: {colors["surface"]};
    border: 1px solid {colors["panel_border"]};
    border-radius: 18px;
}}
QFrame#MessageCard, QFrame#StreamCard {{
    background: {colors["surface"]};
    border: 1px solid {colors["panel_border"]};
    border-radius: 18px;
}}
QFrame[messageRole="user"] {{
    background: {colors["user_bubble"]};
}}
QFrame[messageRole="assistant"] {{
    background: {colors["assistant_bubble"]};
}}
QFrame[messageRole="system"] {{
    background: {colors["system_bubble"]};
}}
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    background: transparent;
    padding: 10px;
    margin: 4px 0;
    border-radius: 12px;
    color: {colors["muted"]};
}}
QListWidget::item:hover {{
    background: {colors["hover"]};
    color: {colors["text"]};
}}
QListWidget::item:selected {{
    background: {colors["selected"]};
    color: {colors["text"]};
}}
QPushButton {{
    background: {colors["surface_alt"]};
    border: 1px solid {colors["panel_border"]};
    border-radius: 14px;
    padding: 10px 14px;
    color: {colors["muted"]};
    font-size: 9pt;
}}
QPushButton:hover {{
    background: {colors["hover"]};
    color: {colors["text"]};
}}
QPushButton[accent="true"] {{
    background: {colors["accent"]};
    color: #ffffff;
    border: none;
    font-weight: 700;
}}
QPushButton[secondary="true"] {{
    background: transparent;
    color: {colors["muted"]};
}}
QPushButton[secondary="true"]:hover {{
    background: {colors["hover"]};
    color: {colors["text"]};
}}
QPushButton[danger="true"] {{
    background: {colors["accent_strong"]};
    color: #ffffff;
    border: none;
}}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
    background: {colors["input"]};
    border: 1px solid {colors["input_border"]};
    border-radius: 16px;
    padding: 9px 12px;
    selection-background-color: {colors["accent"]};
    color: {colors["text"]};
    font-size: 9pt;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid {colors["accent"]};
}}
QTextBrowser {{
    background: {colors["window"]};
    border: 1px solid {colors["panel_border"]};
    border-radius: 18px;
    padding: 10px;
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QLabel#MutedLabel {{
    color: {colors["muted"]};
}}
QLabel#SectionTitle {{
    color: {colors["text"]};
    font-size: 12pt;
    font-weight: 600;
}}
QLabel#HeroTitle {{
    color: {colors["text"]};
    font-size: 13pt;
    font-weight: 600;
}}
QLabel#MutedBadge {{
    color: {colors["muted"]};
}}
QTabWidget::pane {{
    border: 1px solid {colors["panel_border"]};
    border-radius: 14px;
    top: -1px;
    background: {colors["surface"]};
}}
QTabBar::tab {{
    background: {colors["surface_alt"]};
    border: 1px solid {colors["panel_border"]};
    padding: 8px 14px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    color: {colors["muted"]};
}}
QTabBar::tab:selected {{
    background: {colors["selected"]};
    color: {colors["text"]};
}}
QMenu {{
    background: {colors["surface"]};
    border: 1px solid {colors["panel_border"]};
    padding: 8px;
}}
QMenu::item {{
    padding: 8px 18px;
    border-radius: 8px;
    color: {colors["muted"]};
}}
QMenu::item:selected {{
    background: {colors["hover"]};
    color: {colors["text"]};
}}
"""


def theme_colors(theme_name: str) -> dict[str, str]:
    return THEMES.get(theme_name, THEMES["dark"])
