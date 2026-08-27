import os
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QGroupBox, QFormLayout, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "settings.json")


class SettingsPage(QWidget):
    status_message = pyqtSignal(str)
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = {}
        self._load_settings()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)

        api_group = QGroupBox("Groq API")
        api_layout = QFormLayout(api_group)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your Groq API key...")
        self.api_key_input.setText(self.settings.get("groq_api_key", ""))
        api_layout.addRow("API Key:", self.api_key_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("meta-llama/llama-4-scout-17b-16e-instruct")
        self.model_input.setText(self.settings.get("groq_model", "meta-llama/llama-4-scout-17b-16e-instruct"))
        api_layout.addRow("Model:", self.model_input)

        layout.addWidget(api_group)

        paths_group = QGroupBox("Directories")
        paths_layout = QFormLayout(paths_group)

        models_row = QHBoxLayout()
        self.models_dir_input = QLineEdit()
        self.models_dir_input.setText(self.settings.get("models_dir", "Models"))
        btn_models = QPushButton("Browse")
        btn_models.clicked.connect(lambda: self._browse_dir(self.models_dir_input))
        models_row.addWidget(self.models_dir_input)
        models_row.addWidget(btn_models)
        paths_layout.addRow("Models Dir:", models_row)

        video_row = QHBoxLayout()
        self.video_dir_input = QLineEdit()
        self.video_dir_input.setText(self.settings.get("video_dir", "video"))
        btn_video = QPushButton("Browse")
        btn_video.clicked.connect(lambda: self._browse_dir(self.video_dir_input))
        video_row.addWidget(self.video_dir_input)
        video_row.addWidget(btn_video)
        paths_layout.addRow("Video Dir:", video_row)

        layout.addWidget(paths_group)

        analysis_group = QGroupBox("Analysis")
        analysis_layout = QFormLayout(analysis_group)

        self.frame_interval_spin = QSpinBox()
        self.frame_interval_spin.setRange(1, 30)
        self.frame_interval_spin.setValue(self.settings.get("frame_interval", 2))
        self.frame_interval_spin.setSuffix(" seconds")
        analysis_layout.addRow("Frame Interval:", self.frame_interval_spin)

        layout.addWidget(analysis_group)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setProperty("class", "accent-btn")
        self.btn_save.setFixedHeight(40)
        self.btn_save.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _browse_dir(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)

    def _load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = {}
        else:
            self.settings = {}

        if not self.settings.get("groq_api_key"):
            from dotenv import load_dotenv
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
            load_dotenv(env_path)
            self.settings["groq_api_key"] = os.getenv("GROQ_API_KEY", "")

    def _save_settings(self):
        self.settings["groq_api_key"] = self.api_key_input.text().strip()
        self.settings["groq_model"] = self.model_input.text().strip()
        self.settings["models_dir"] = self.models_dir_input.text().strip()
        self.settings["video_dir"] = self.video_dir_input.text().strip()
        self.settings["frame_interval"] = self.frame_interval_spin.value()

        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f, indent=2)

            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
            api_key = self.settings.get("groq_api_key", "")
            if api_key:
                lines = []
                found = False
                if os.path.exists(env_path):
                    with open(env_path, "r") as f:
                        for line in f:
                            if line.startswith("GROQ_API_KEY"):
                                lines.append(f"GROQ_API_KEY={api_key}\n")
                                found = True
                            else:
                                lines.append(line)
                if not found:
                    lines.append(f"GROQ_API_KEY={api_key}\n")
                with open(env_path, "w") as f:
                    f.writelines(lines)

            self.settings_changed.emit(self.settings)
            self.status_message.emit("Settings saved successfully")
        except Exception as e:
            self.status_message.emit(f"Error saving settings: {e}")

    def get_settings(self):
        return self.settings
