from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class ModelCard(QFrame):
    clicked = pyqtSignal(dict)

    def __init__(self, model_data, parent=None):
        super().__init__(parent)
        self.model_data = model_data
        self.setFixedSize(260, 140)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: #171A21;
                border: 1px solid #2A2D35;
                border-radius: 10px;
            }
            QFrame:hover {
                border-color: #4F8CFF;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        name = self.model_data.get("name", "Unknown")
        valid = self.model_data.get("valid", False)

        header = QHBoxLayout()
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #E0E0E0; background: transparent;")

        status_label = QLabel("Valid" if valid else "Invalid")
        status_color = "#36C275" if valid else "#E55353"
        status_label.setStyleSheet(
            f"color: {status_color}; font-size: 10px; font-weight: 600; "
            f"background-color: {status_color}22; padding: 2px 6px; border-radius: 4px;"
        )
        header.addWidget(name_label)
        header.addStretch()
        header.addWidget(status_label)
        layout.addLayout(header)

        if valid:
            dims = self.model_data.get("dimensions", {})
            dim_text = f"{dims.get('x', 0):.1f} x {dims.get('y', 0):.1f} x {dims.get('z', 0):.1f}"
            dim_label = QLabel(f"Dimensions: {dim_text}")
            dim_label.setStyleSheet("color: #888888; font-size: 11px; background: transparent;")
            layout.addWidget(dim_label)

            size_mb = self.model_data.get("file_size_mb", 0)
            meshes = self.model_data.get("mesh_count", 0)
            info_label = QLabel(f"Meshes: {meshes}  |  Size: {size_mb:.1f} MB")
            info_label.setStyleSheet("color: #888888; font-size: 11px; background: transparent;")
            layout.addWidget(info_label)
        else:
            err = self.model_data.get("error", "Unknown error")
            err_label = QLabel(f"Error: {err[:50]}")
            err_label.setStyleSheet("color: #E55353; font-size: 11px; background: transparent;")
            err_label.setWordWrap(True)
            layout.addWidget(err_label)

        layout.addStretch()

    def mousePressEvent(self, event):
        self.clicked.emit(self.model_data)
        super().mousePressEvent(event)


class ModelsPage(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.models_data = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Model Library")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.addWidget(title)

        self.count_label = QLabel("0 models")
        self.count_label.setStyleSheet("color: #888888; font-size: 14px;")
        header.addWidget(self.count_label)
        header.addStretch()

        self.btn_scan = QPushButton("Scan Models")
        self.btn_scan.clicked.connect(self._request_scan)
        header.addWidget(self.btn_scan)

        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.grid_widget)

        layout.addWidget(self.scroll)

        self.detail_panel = QTextEdit()
        self.detail_panel.setReadOnly(True)
        self.detail_panel.setMaximumHeight(150)
        self.detail_panel.setVisible(False)
        self.detail_panel.setStyleSheet("font-family: 'Consolas', monospace; font-size: 12px;")
        layout.addWidget(self.detail_panel)

    def _request_scan(self):
        self.status_message.emit("scan_models")

    def set_models(self, models):
        self.models_data = models
        valid_count = sum(1 for m in models if m.get("valid", False))
        self.count_label.setText(f"{valid_count} valid / {len(models)} total")

        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        cols = 3
        for i, model in enumerate(models):
            card = ModelCard(model)
            card.clicked.connect(self._show_detail)
            self.grid_layout.addWidget(card, i // cols, i % cols)

    def _show_detail(self, model_data):
        self.detail_panel.setVisible(True)
        import json
        display = {k: v for k, v in model_data.items() if k != "meshes"}
        self.detail_panel.setText(json.dumps(display, indent=2))
