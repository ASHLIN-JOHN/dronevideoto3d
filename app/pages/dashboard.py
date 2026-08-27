import os
import json
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QGridLayout, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

BASE_DIR = Path(__file__).parent.parent.parent


class StatusCard(QFrame):
    def __init__(self, title, value="--", color="#4F8CFF"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #171A21;
                border: 1px solid #2A2D35;
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        self.setFixedHeight(100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #888888; font-size: 11px; font-weight: 600; text-transform: uppercase;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 700;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value):
        self.value_label.setText(str(value))


class DashboardPage(QWidget):
    navigate_to = pyqtSignal(int)
    project_loaded = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        welcome = QLabel("Drone 3D Studio")
        welcome.setFont(QFont("Segoe UI", 24, QFont.Bold))
        welcome.setStyleSheet("color: #4F8CFF;")
        layout.addWidget(welcome)

        subtitle = QLabel("Convert drone video footage into interactive 3D scenes using AI-powered analysis")
        subtitle.setStyleSheet("color: #888888; font-size: 14px;")
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)

        self.models_card = StatusCard("Models Loaded", "0", "#4F8CFF")
        self.video_card = StatusCard("Video Status", "None", "#F5B942")
        self.analysis_card = StatusCard("Analysis", "Pending", "#888888")
        self.scene_card = StatusCard("Scene Objects", "0", "#36C275")

        cards_layout.addWidget(self.models_card, 0, 0)
        cards_layout.addWidget(self.video_card, 0, 1)
        cards_layout.addWidget(self.analysis_card, 0, 2)
        cards_layout.addWidget(self.scene_card, 0, 3)

        layout.addLayout(cards_layout)

        actions_label = QLabel("Quick Actions")
        actions_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(actions_label)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        btn_video = QPushButton("  Upload Video")
        btn_video.setProperty("class", "accent-btn")
        btn_video.setFixedHeight(42)
        btn_video.clicked.connect(lambda: self.navigate_to.emit(2))

        btn_json = QPushButton("  Load JSON")
        btn_json.setFixedHeight(42)
        btn_json.clicked.connect(lambda: self.navigate_to.emit(5))

        btn_scene = QPushButton("  Generate Scene")
        btn_scene.setFixedHeight(42)
        btn_scene.clicked.connect(lambda: self.navigate_to.emit(4))

        actions_layout.addWidget(btn_video)
        actions_layout.addWidget(btn_json)
        actions_layout.addWidget(btn_scene)
        actions_layout.addStretch()

        layout.addLayout(actions_layout)

        projects_label = QLabel("Recent Projects")
        projects_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(projects_label)

        self.projects_container = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_container)
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_layout.setSpacing(8)

        projects_scroll = QScrollArea()
        projects_scroll.setWidgetResizable(True)
        projects_scroll.setWidget(self.projects_container)
        projects_scroll.setMaximumHeight(180)
        projects_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        layout.addWidget(projects_scroll)

        self.refresh_projects()

        log_label = QLabel("Activity Log")
        log_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(log_label)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(140)
        self.log.setStyleSheet("""
            QTextEdit {
                font-family: "Consolas", "Courier New", monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log)
        layout.addStretch()

    def refresh_projects(self):
        while self.projects_layout.count():
            child = self.projects_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        projects_dir = BASE_DIR / "projects"
        if not projects_dir.exists():
            projects_dir.mkdir(exist_ok=True)

        files = sorted(projects_dir.glob("*.3dv"), key=os.path.getmtime, reverse=True)

        if not files:
            empty = QLabel("No projects yet. Generate a scene to create your first project.")
            empty.setStyleSheet("color: #666; font-size: 12px; padding: 12px;")
            self.projects_layout.addWidget(empty)
            return

        for filepath in files[:10]:
            card = self._create_project_card(filepath)
            self.projects_layout.addWidget(card)

    def _create_project_card(self, filepath):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1c1f28;
                border: 1px solid #2A2D35;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QFrame:hover {
                border-color: #4F8CFF;
                background-color: #1f2230;
            }
        """)
        card.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)

        mtime = os.path.getmtime(str(filepath))
        dt = datetime.fromtimestamp(mtime)
        date_str = dt.strftime("%b %d, %Y  %I:%M %p")

        obj_count = 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                obj_count = len(data.get("objects", []))
        except Exception:
            pass

        name_label = QLabel(f"  {filepath.stem}")
        name_label.setStyleSheet("color: #dde; font-size: 12px; font-weight: 600; background: transparent;")

        info_label = QLabel(f"{date_str}  |  {obj_count} objects")
        info_label.setStyleSheet("color: #777; font-size: 11px; background: transparent;")

        open_btn = QPushButton("Open")
        open_btn.setFixedSize(60, 26)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a3a5a;
                color: #8ab4ff;
                border: 1px solid #3a5a8a;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #3a4a6a; }
        """)
        open_btn.clicked.connect(lambda checked, p=str(filepath): self._open_project(p))

        left = QVBoxLayout()
        left.setSpacing(2)
        left.addWidget(name_label)
        left.addWidget(info_label)

        layout.addLayout(left, 1)
        layout.addWidget(open_btn)

        return card

    def _open_project(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._loaded_project = data
            self.project_loaded.emit(data)
        except Exception:
            pass

    def add_log(self, message):
        self.log.append(message)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def update_models_count(self, count):
        self.models_card.set_value(str(count))

    def update_video_status(self, status):
        self.video_card.set_value(status)

    def update_analysis_status(self, status):
        self.analysis_card.set_value(status)

    def update_scene_count(self, count):
        self.scene_card.set_value(str(count))
