DARK_THEME = """
QMainWindow, QDialog {
    background-color: #0e0e0e;
}

QWidget#centralWidget {
    background-color: #0e0e0e;
}

QLabel {
    color: #c0c0c0;
    font-size: 12px;
}

QPushButton {
    background-color: #161616;
    color: #c0c0c0;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 8px;
    font-size: 12px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #222222;
    border-color: #e94560;
}

QPushButton:pressed {
    background-color: #1a1a1a;
    border-color: #e94560;
}

QTabBar::tab {
    background-color: #161616;
    color: #808080;
    border: 1px solid #2a2a2a;
    border-bottom: none;
    padding: 6px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 12px;
}

QTabBar::tab:selected {
    background-color: #0e0e0e;
    color: #e94560;
    border-color: #333333;
}

QTabBar::tab:hover:!selected {
    background-color: #1e1e1e;
    color: #c0c0c0;
}

QMenu {
    background-color: #141414;
    color: #c0c0c0;
    border: 1px solid #2a2a2a;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #222222;
}

QMenu::separator {
    height: 1px;
    background-color: #2a2a2a;
    margin: 4px 8px;
}

QLineEdit, QSpinBox, QComboBox {
    background-color: #141414;
    color: #c0c0c0;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 6px;
    font-size: 12px;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #e94560;
}

QCheckBox {
    color: #c0c0c0;
    font-size: 12px;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #2a2a2a;
    background-color: #141414;
}

QCheckBox::indicator:checked {
    background-color: #e94560;
    border-color: #e94560;
}

QGroupBox {
    color: #c0c0c0;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-size: 12px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}

QScrollBar:vertical {
    background-color: #0e0e0e;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #2a2a2a;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background-color: #404040;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QListWidget {
    background-color: #141414;
    color: #c0c0c0;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 4px;
    outline: none;
}

QListWidget::item {
    padding: 4px 8px;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #222222;
    color: #e94560;
}

QDialogButtonBox QPushButton {
    min-width: 80px;
    padding: 6px 16px;
}

QSlider::groove:horizontal {
    height: 4px;
    background: #2a2a2a;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #e94560;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}

QSlider::handle:horizontal:hover {
    background: #ff6b81;
}

QSlider::sub-page:horizontal {
    background: #e94560;
    border-radius: 2px;
}

QSplitter::handle {
    background-color: #1a1a1a;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #333333;
}
"""

DECK_BUTTON_STYLE = """
QPushButton#deckButton {
    background-color: #0a0a0a;
    color: #e0e0e0;
    border: 2px solid #1a1a1a;
    border-radius: 10px;
    font-size: 15px;
    padding: 4px;
}

QPushButton#deckButton:hover {
    background-color: #1a1a1a;
    border-color: #e94560;
    color: #ffffff;
}

QPushButton#deckButton:pressed {
    background-color: #111111;
    border-color: #e94560;
}
"""

DECK_BUTTON_EMPTY_STYLE = """
QPushButton#deckButton {
    background-color: #080808;
    color: #303030;
    border: 1px dashed #1a1a1a;
    border-radius: 10px;
    font-size: 15px;
    padding: 4px;
}

QPushButton#deckButton:hover {
    background-color: #0e0e0e;
    border-color: #2a2a2a;
    color: #505050;
}
"""

MONITOR_BUTTON_STYLE = """
QPushButton#deckButton {
    background-color: #0a0a0a;
    color: #4caf50;
    border: 2px solid #1a1a1a;
    border-radius: 10px;
    font-size: 15px;
    padding: 4px;
}
"""

FOLDER_TREE_STYLE = """
QTreeWidget#folderTree {
    background-color: #0a0a0a;
    color: #c0c0c0;
    border: none;
    border-right: 1px solid #1a1a1a;
    outline: none;
    font-size: 12px;
}

QTreeWidget#folderTree::item {
    padding: 4px 8px;
    border-radius: 0px;
}

QTreeWidget#folderTree::item:selected {
    background-color: #1a1a1a;
    color: #e94560;
}

QTreeWidget#folderTree::item:hover:!selected {
    background-color: #141414;
}

QTreeWidget#folderTree::branch {
    background-color: #0a0a0a;
}

QTreeWidget#folderTree::branch:has-children:!has-siblings:closed,
QTreeWidget#folderTree::branch:closed:has-children:has-siblings {
    image: none;
    border-image: none;
}

QTreeWidget#folderTree::branch:open:has-children:!has-siblings,
QTreeWidget#folderTree::branch:open:has-children:has-siblings {
    image: none;
    border-image: none;
}

QHeaderView::section {
    background-color: #0a0a0a;
    color: #e94560;
    border: none;
    border-bottom: 1px solid #1a1a1a;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: bold;
}
"""

TITLE_BAR_STYLE = """
QWidget#titleBar {
    background-color: #080808;
    border-bottom: 1px solid #1a1a1a;
    padding: 5px;
}
"""
