APP_STYLESHEET = """
QWidget {
    background: #11161d;
    color: #edf2f7;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMainWindow, QDialog {
    background: #0d1218;
}
QFrame#Sidebar, QFrame#EventsPanel, QFrame#ComposerCard, QFrame#HeaderCard {
    background: #151c25;
    border: 1px solid #263241;
    border-radius: 16px;
}
QListWidget {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 10px;
    margin: 4px 0;
    border-radius: 12px;
}
QListWidget::item:selected {
    background: #203145;
}
QPushButton {
    background: #203145;
    border: 1px solid #35506d;
    border-radius: 12px;
    padding: 8px 14px;
}
QPushButton:hover {
    background: #28415a;
}
QPushButton[accent="true"] {
    background: #4aa3ff;
    color: #08111b;
    border: none;
    font-weight: 700;
}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
    background: #0f151c;
    border: 1px solid #2c3c4f;
    border-radius: 12px;
    padding: 8px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QLabel#MutedLabel {
    color: #97a6b5;
}
QTabWidget::pane {
    border: 1px solid #2c3c4f;
    border-radius: 14px;
    top: -1px;
}
QTabBar::tab {
    background: #151c25;
    border: 1px solid #2c3c4f;
    padding: 8px 14px;
    margin-right: 4px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}
QTabBar::tab:selected {
    background: #203145;
}
"""
