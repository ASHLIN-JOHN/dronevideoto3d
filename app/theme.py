COLORS = {
    "background": "#0F1117",
    "panel": "#171A21",
    "secondary": "#20242D",
    "accent": "#4F8CFF",
    "accent_hover": "#6BA0FF",
    "accent_pressed": "#3A7AEE",
    "success": "#36C275",
    "warning": "#F5B942",
    "error": "#E55353",
    "text": "#E0E0E0",
    "text_secondary": "#888888",
    "border": "#2A2D35",
    "border_light": "#363A45",
}


def get_stylesheet():
    c = COLORS
    return f"""
    QMainWindow {{
        background-color: {c['background']};
    }}
    QWidget {{
        background-color: {c['background']};
        color: {c['text']};
        font-family: "Segoe UI", "Inter", sans-serif;
        font-size: 13px;
    }}
    QLabel {{
        background: transparent;
        color: {c['text']};
    }}
    QPushButton {{
        background-color: {c['secondary']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {c['border']};
        border-color: {c['border_light']};
    }}
    QPushButton:pressed {{
        background-color: {c['panel']};
    }}
    QPushButton:disabled {{
        background-color: {c['panel']};
        color: {c['text_secondary']};
        border-color: {c['border']};
    }}
    QPushButton[class="accent-btn"] {{
        background-color: {c['accent']};
        color: #FFFFFF;
        border: none;
        font-weight: 600;
    }}
    QPushButton[class="accent-btn"]:hover {{
        background-color: {c['accent_hover']};
    }}
    QPushButton[class="accent-btn"]:pressed {{
        background-color: {c['accent_pressed']};
    }}
    QPushButton[class="sidebar-btn"] {{
        background-color: transparent;
        border: none;
        border-radius: 8px;
        padding: 10px 16px;
        text-align: left;
        font-size: 13px;
        color: {c['text_secondary']};
    }}
    QPushButton[class="sidebar-btn"]:hover {{
        background-color: {c['secondary']};
        color: {c['text']};
    }}
    QPushButton[class="sidebar-btn-active"] {{
        background-color: {c['secondary']};
        border: none;
        border-radius: 8px;
        border-left: 3px solid {c['accent']};
        padding: 10px 13px 10px 16px;
        text-align: left;
        font-size: 13px;
        color: {c['accent']};
        font-weight: 600;
    }}
    QProgressBar {{
        background-color: {c['secondary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background-color: {c['accent']};
        border-radius: 5px;
    }}
    QTabWidget::pane {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 6px;
    }}
    QTabBar::tab {{
        background-color: {c['secondary']};
        color: {c['text_secondary']};
        border: 1px solid {c['border']};
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        padding: 8px 16px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background-color: {c['panel']};
        color: {c['text']};
        border-color: {c['border']};
    }}
    QTabBar::tab:hover {{
        background-color: {c['border']};
    }}
    QSplitter::handle {{
        background-color: {c['border']};
    }}
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}
    QGroupBox {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 16px;
        margin-top: 8px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        color: {c['text']};
        subcontrol-origin: margin;
        padding: 4px 8px;
    }}
    QLineEdit {{
        background-color: {c['secondary']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 8px 12px;
    }}
    QLineEdit:focus {{
        border-color: {c['accent']};
    }}
    QSpinBox, QDoubleSpinBox {{
        background-color: {c['secondary']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px 10px;
    }}
    QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {c['accent']};
    }}
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background-color: {c['border']};
        border: none;
        width: 16px;
    }}
    QScrollArea {{
        background-color: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background-color: {c['panel']};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c['border']};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c['border_light']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: {c['panel']};
        height: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c['border']};
        border-radius: 5px;
        min-width: 30px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QTreeWidget, QTableWidget {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        alternate-background-color: {c['secondary']};
        gridline-color: {c['border']};
    }}
    QTreeWidget::item, QTableWidget::item {{
        padding: 6px;
    }}
    QTreeWidget::item:selected, QTableWidget::item:selected {{
        background-color: {c['accent']};
        color: #FFFFFF;
    }}
    QTreeWidget::item:hover, QTableWidget::item:hover {{
        background-color: {c['secondary']};
    }}
    QHeaderView::section {{
        background-color: {c['secondary']};
        color: {c['text']};
        border: none;
        border-right: 1px solid {c['border']};
        border-bottom: 1px solid {c['border']};
        padding: 8px;
        font-weight: 600;
    }}
    QStatusBar {{
        background-color: {c['panel']};
        color: {c['text_secondary']};
        border-top: 1px solid {c['border']};
        padding: 4px;
    }}
    QStatusBar QLabel {{
        color: {c['text_secondary']};
        padding: 0 8px;
    }}
    QDockWidget {{
        background-color: {c['panel']};
        border: 1px solid {c['border']};
        titlebar-close-icon: none;
    }}
    QDockWidget::title {{
        background-color: {c['secondary']};
        padding: 8px;
        border-bottom: 1px solid {c['border']};
    }}
    QToolBar {{
        background-color: {c['panel']};
        border: none;
        spacing: 4px;
        padding: 4px;
    }}
    QTextEdit, QPlainTextEdit {{
        background-color: {c['secondary']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 8px;
    }}
    QComboBox {{
        background-color: {c['secondary']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 8px 12px;
    }}
    QComboBox:hover {{
        border-color: {c['border_light']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['panel']};
        color: {c['text']};
        border: 1px solid {c['border']};
        selection-background-color: {c['accent']};
    }}
    QSlider::groove:horizontal {{
        background: {c['secondary']};
        height: 6px;
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {c['accent']};
        width: 14px;
        height: 14px;
        margin: -4px 0;
        border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{
        background: {c['accent']};
        border-radius: 3px;
    }}
    QToolTip {{
        background-color: {c['panel']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 4px 8px;
    }}
    """
