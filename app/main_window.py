import os
import json
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from app.pages.projects_page import ProjectsPage
from app.pages.dashboard import DashboardPage
from app.pages.video_page import VideoPage
from app.pages.models_page import ModelsPage
from app.pages.scene_page import ScenePage
from app.pages.json_page import JsonPage
from app.pages.settings_page import SettingsPage
from app.workers import ModelScanWorker, SceneGenerationWorker

BASE_DIR = Path(__file__).parent.parent


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone 3D Studio")
        self.setMinimumSize(1200, 700)

        self.models_metadata = []
        self.json_data = None
        self.scan_worker = None
        self.scene_worker = None
        self.current_project = None
        self.current_project_name = None

        self._setup_ui()
        self._connect_signals()
        self._setup_autosave()

        QTimer.singleShot(500, self._start_model_scan)

    def _setup_autosave(self):
        """Setup auto-save timer for projects"""
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.auto_save_project)
        self.autosave_timer.start(30000)  # Auto-save every 30 seconds

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.projects_page = ProjectsPage(main_window=self)
        self.dashboard_page = DashboardPage()
        self.video_page = VideoPage()
        self.models_page = ModelsPage()
        self.scene_page = ScenePage()
        self.json_page = JsonPage()
        self.settings_page = SettingsPage()

        self.stack.addWidget(self.projects_page)
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.video_page)
        self.stack.addWidget(self.models_page)
        self.stack.addWidget(self.scene_page)
        self.stack.addWidget(self.json_page)
        self.stack.addWidget(self.settings_page)

        right_layout.addWidget(self.stack)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready")
        self.models_label = QLabel("Models: 0")
        self.objects_label = QLabel("Objects: 0")
        self.status_bar.addWidget(self.status_label, 1)
        self.status_bar.addPermanentWidget(self.models_label)
        self.status_bar.addPermanentWidget(self.objects_label)

    def _create_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("QFrame { background-color: #171A21; border-right: 1px solid #2A2D35; }")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        brand = QLabel("Drone 3D Studio")
        brand.setFont(QFont("Segoe UI", 13, QFont.Bold))
        brand.setStyleSheet("color: #4F8CFF; padding: 8px 4px 16px 4px; background: transparent;")
        layout.addWidget(brand)

        self.nav_buttons = []
        pages = [
            ("📁  Projects", 0),
            ("⌂  Dashboard", 1),
            ("▶  Video", 2),
            ("▦  Models", 3),
            ("◈  Scene", 4),
            ("{}  JSON", 5),
            ("⚙  Settings", 6),
        ]

        for label, idx in pages:
            btn = QPushButton(label)
            btn.setProperty("class", "sidebar-btn")
            btn.setFixedHeight(40)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self._navigate(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #555; font-size: 11px; padding: 8px; background: transparent;")
        layout.addWidget(version_label)

        self._set_active_nav(0)
        return sidebar

    def _navigate(self, index):
        self.stack.setCurrentIndex(index)
        self._set_active_nav(index)
        # Refresh projects page when navigating to it
        if index == 0 and hasattr(self.projects_page, '_refresh_projects'):
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(300, self.projects_page._refresh_projects)

    def _set_active_nav(self, active_index):
        for i, btn in enumerate(self.nav_buttons):
            if i == active_index:
                btn.setProperty("class", "sidebar-btn-active")
            else:
                btn.setProperty("class", "sidebar-btn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _connect_signals(self):
        self.dashboard_page.navigate_to.connect(self._navigate)
        self.dashboard_page.project_loaded.connect(self._on_project_loaded)
        self.video_page.analysis_complete.connect(self._on_analysis_complete)
        self.video_page.status_message.connect(self._set_status)
        self.models_page.status_message.connect(self._handle_models_action)
        self.scene_page.request_generate.connect(self._generate_scene)
        self.scene_page.status_message.connect(self._set_status)
        self.json_page.json_loaded.connect(self._on_json_loaded)
        self.json_page.status_message.connect(self._set_status)
        self.settings_page.status_message.connect(self._set_status)

    def _on_project_loaded(self, scene_data):
        self.scene_page.set_scene(scene_data)
        obj_count = len(scene_data.get("objects", []))
        self.dashboard_page.update_scene_count(obj_count)
        self._set_status(f"Project loaded: {obj_count} objects")
        self._navigate(4)

    def _set_status(self, msg):
        self.status_label.setText(msg)
        self.dashboard_page.add_log(msg)

    def _handle_models_action(self, action):
        if action == "scan_models":
            self._start_model_scan()
        else:
            self._set_status(action)

    def _start_model_scan(self):
        models_dir = str(BASE_DIR / "Models")
        if not os.path.isdir(models_dir):
            self._set_status(f"Models directory not found: {models_dir}")
            return

        self._set_status("Scanning models...")
        self.scan_worker = ModelScanWorker(models_dir)
        self.scan_worker.progress.connect(lambda msg, pct: self._set_status(msg))
        self.scan_worker.finished.connect(self._on_models_scanned)
        self.scan_worker.error.connect(lambda e: self._set_status(f"Scan error: {e[:80]}"))
        self.scan_worker.start()

    def _on_models_scanned(self, models):
        self.models_metadata = models
        valid_count = sum(1 for m in models if m.get("valid", False))
        self.models_label.setText(f"Models: {valid_count}")
        self.models_page.set_models(models)
        self.dashboard_page.update_models_count(valid_count)
        self._set_status(f"Model scan complete: {valid_count} valid models found")

        cache_dir = BASE_DIR / ".cache"
        cache_dir.mkdir(exist_ok=True)
        try:
            with open(cache_dir / "models_metadata.json", "w") as f:
                json.dump({"models": models}, f, indent=2)
        except Exception:
            pass

    def _on_analysis_complete(self, result):
        self.json_data = result
        self.json_page.set_json_data(result)
        self.dashboard_page.update_analysis_status("Complete")

        # Save to current project if loaded
        if self.current_project:
            self.current_project["json_data"] = result
            self.save_current_project()

        total_objects = sum(
            len(f.get("analysis", {}).get("objects", []))
            for f in result.get("frames", [])
        )
        self.objects_label.setText(f"Objects: {total_objects}")
        self.dashboard_page.update_scene_count(total_objects)
        self._set_status("Analysis complete - ready to generate scene")

    def _on_json_loaded(self, data):
        self.json_data = data
        self.dashboard_page.update_analysis_status("Loaded")

        # Save to current project if loaded
        if self.current_project:
            self.current_project["json_data"] = data
            self.save_current_project()

        total_objects = sum(
            len(f.get("analysis", {}).get("objects", []))
            for f in data.get("frames", [])
        )
        self.objects_label.setText(f"Objects: {total_objects}")

    def _generate_scene(self):
        if not self.json_data:
            fallback = BASE_DIR / "video_analysis.json"
            if fallback.exists():
                try:
                    with open(fallback, "r", encoding="utf-8") as f:
                        self.json_data = json.load(f)
                    self._set_status("Loaded video_analysis.json for scene generation")
                except Exception:
                    pass
            if not self.json_data:
                self.scene_page.show_progress("No JSON data. Analyze a video or load JSON first.", 0)
                self._set_status("No JSON data loaded. Load or analyze a video first.")
                return
        if not self.models_metadata:
            self.scene_page.show_progress("No models scanned yet. Please wait...", 0)
            self._set_status("No models scanned. Scan models first.")
            return

        models_dir = str(BASE_DIR / "Models")
        self.scene_page.show_progress("Generating scene...", 0)
        self._set_status("Generating 3D scene...")

        self.scene_worker = SceneGenerationWorker(self.json_data, self.models_metadata, models_dir)
        self.scene_worker.progress.connect(self.scene_page.show_progress)
        self.scene_worker.finished.connect(self._on_scene_generated)
        self.scene_worker.error.connect(self._on_scene_error)
        self.scene_worker.start()

    def _on_scene_error(self, e):
        self.scene_page.show_progress(f"Error: {e[:80]}", 0)
        self._set_status(f"Scene error: {e[:80]}")

    def _on_scene_generated(self, scene_data):
        self.scene_page.hide_progress()
        self.scene_page.set_scene(scene_data)
        obj_count = len(scene_data.get("objects", []))
        self.dashboard_page.update_scene_count(obj_count)
        self._set_status(f"Scene generated: {obj_count} objects placed")

        # Save to current project if loaded
        if self.current_project:
            self.current_project["scene_data"] = scene_data
            self.save_current_project()

        self._save_project(scene_data)
        self._navigate(4)

    def _save_project(self, scene_data):
        projects_dir = BASE_DIR / "projects"
        projects_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scene_{timestamp}.3dv"
        filepath = projects_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(scene_data, f, indent=2)
            self.dashboard_page.refresh_projects()
            self._set_status(f"Project saved: {filename}")
        except Exception as e:
            self._set_status(f"Save error: {str(e)[:60]}")

    def load_project_from_browser(self, project_data):
        """Load a project from the browser Projects page"""
        try:
            data = json.loads(project_data)
            self.current_project = data
            self.current_project_name = data.get("name", "Untitled Project")

            # Load JSON data if available
            if "json_data" in data:
                self.json_data = data["json_data"]
                self.json_page.set_json_data(self.json_data)

            # Load scene data if available
            if "scene_data" in data:
                self.scene_page.set_scene(data["scene_data"])

            # Update UI
            self.setWindowTitle(f"Drone 3D Studio - {self.current_project_name}")
            self._navigate(1)  # Go to Dashboard
            self._set_status(f"Project loaded: {self.current_project_name}")
        except Exception as e:
            self._set_status(f"Failed to load project: {str(e)[:80]}")

    def save_current_project(self):
        """Save current project state"""
        if not self.current_project:
            self._set_status("No project loaded")
            return

        self.current_project["json_data"] = self.json_data if self.json_data else {}
        if hasattr(self.scene_page, 'scene_data') and self.scene_page.scene_data:
            self.current_project["scene_data"] = self.scene_page.scene_data

        self.current_project["updated_at"] = str(datetime.now())
        self._set_status(f"Project '{self.current_project_name}' saved")

    def auto_save_project(self):
        """Periodically auto-save the current project"""
        if self.current_project:
            self.save_current_project()

    def closeEvent(self, event):
        """Save project when app closes"""
        if self.current_project:
            self.save_current_project()
        event.accept()
