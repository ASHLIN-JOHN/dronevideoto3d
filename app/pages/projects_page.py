from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QUrl, QTimer, QObject, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False


class ProjectBridge(QObject):
    def __init__(self, main_window, projects_page):
        super().__init__()
        self.main_window = main_window
        self.projects_page = projects_page

    @pyqtSlot(str)
    def load_project_from_browser(self, project_data):
        if self.main_window:
            self.main_window.load_project_from_browser(project_data)

    @pyqtSlot(str)
    def update_project_in_storage(self, project_data):
        """Update project in localStorage from main window"""
        if self.projects_page and self.projects_page.web_view:
            js = f"if(window.updateProjectInStorage) window.updateProjectInStorage('{project_data.replace(chr(34), chr(92)+chr(34))}');"
            self.projects_page.web_view.page().runJavaScript(js)


class ProjectsPage(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.web_view = None
        self.main_window = main_window
        self.bridge = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()

            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)

            # Setup WebChannel bridge
            if self.main_window:
                self.bridge = ProjectBridge(self.main_window, self)
                channel = QWebChannel()
                channel.registerObject("mainWindow", self.bridge)
                self.web_view.page().setWebChannel(channel)

            self.web_view.loadFinished.connect(self._on_page_loaded)
            self.web_view.setUrl(QUrl("http://127.0.0.1:8765/app/viewer/web/projects.html"))
            layout.addWidget(self.web_view)
        else:
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtCore import Qt
            placeholder = QLabel("WebEngine not available.\nInstall PyQtWebEngine for projects manager.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #888; font-size: 16px; background: #171A21;")
            layout.addWidget(placeholder)

    def _on_page_loaded(self, ok):
        if ok and self.web_view:
            # Refresh projects list when page loads
            QTimer.singleShot(500, self._refresh_projects)

    def _refresh_projects(self):
        if self.web_view:
            self.web_view.page().runJavaScript("if(window.refreshProjects) window.refreshProjects();")
