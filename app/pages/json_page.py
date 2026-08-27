import os
import json

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QFileDialog,
    QSplitter, QComboBox, QApplication, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class JsonPage(QWidget):
    object_selected = pyqtSignal(str)
    json_loaded = pyqtSignal(object)
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.json_data = None
        self.json_path = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("JSON Viewer")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        self.btn_load = QPushButton("Load JSON")
        self.btn_load.clicked.connect(self._load_json)
        header.addWidget(self.btn_load)

        self.btn_reload = QPushButton("Reload")
        self.btn_reload.clicked.connect(self._reload_json)
        self.btn_reload.setEnabled(False)
        header.addWidget(self.btn_reload)

        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self._save_json)
        self.btn_save.setEnabled(False)
        header.addWidget(self.btn_save)

        self.btn_copy = QPushButton("Copy")
        self.btn_copy.clicked.connect(self._copy_json)
        header.addWidget(self.btn_copy)

        layout.addLayout(header)

        self.frame_selector = QComboBox()
        self.frame_selector.addItem("All Frames")
        self.frame_selector.currentIndexChanged.connect(self._on_frame_selected)
        layout.addWidget(self.frame_selector)

        splitter = QSplitter(Qt.Vertical)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 11))
        self.text_edit.setPlaceholderText("Load a JSON file to view analysis results...")
        splitter.addWidget(self.text_edit)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Type", "Position", "Size", "Color", "Confidence"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellClicked.connect(self._on_table_click)
        splitter.addWidget(self.table)

        splitter.setSizes([400, 250])
        layout.addWidget(splitter)

    def _load_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "3DV Projects (*.3dv);;JSON Files (*.json);;All Files (*)"
        )
        if path:
            self._read_json_file(path)

    def _read_json_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.json_data = data
            self.json_path = path
            self.btn_reload.setEnabled(True)
            self.btn_save.setEnabled(True)

            self.text_edit.setText(json.dumps(data, indent=2, ensure_ascii=False))
            self._populate_frame_selector()
            self._populate_table()
            self.json_loaded.emit(data)
            self.status_message.emit(f"JSON loaded: {os.path.basename(path)}")
        except Exception as e:
            self.text_edit.setText(f"Error loading JSON:\n{str(e)}")
            self.status_message.emit(f"JSON load error: {str(e)[:60]}")

    def set_json_data(self, data):
        self.json_data = data
        self.text_edit.setText(json.dumps(data, indent=2, ensure_ascii=False))
        self._populate_frame_selector()
        self._populate_table()
        self.btn_save.setEnabled(True)

    def _reload_json(self):
        if self.json_path:
            self._read_json_file(self.json_path)

    def _save_json(self):
        if not self.json_data:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save JSON", "video_analysis.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.json_data, f, indent=2, ensure_ascii=False)
            self.status_message.emit(f"JSON saved to {path}")

    def _copy_json(self):
        text = self.text_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_message.emit("JSON copied to clipboard")

    def _populate_frame_selector(self):
        self.frame_selector.clear()
        self.frame_selector.addItem("All Frames")
        if not self.json_data:
            return
        frames = self.json_data.get("frames", [])
        for frame in frames:
            num = frame.get("frame_number", "?")
            ts = frame.get("video_timestamp", 0)
            self.frame_selector.addItem(f"Frame {num} ({ts:.1f}s)")

    def _on_frame_selected(self, index):
        self._populate_table(frame_index=index - 1 if index > 0 else None)

    def _populate_table(self, frame_index=None):
        self.table.setRowCount(0)
        if not self.json_data:
            return

        frames = self.json_data.get("frames", [])
        if frame_index is not None and 0 <= frame_index < len(frames):
            frames_to_show = [frames[frame_index]]
        else:
            frames_to_show = frames

        row = 0
        obj_counter = 0
        for frame in frames_to_show:
            analysis = frame.get("analysis", {})
            objects = analysis.get("objects", [])
            for obj in objects:
                obj_counter += 1
                self.table.insertRow(row)
                obj_id = obj.get("id", f"obj_{obj_counter:03d}")
                obj_type = obj.get("type", "unknown")
                position = obj.get("position", "")
                size = obj.get("estimated_size", "")
                color = obj.get("color", "")
                confidence = obj.get("confidence", 0)

                self.table.setItem(row, 0, QTableWidgetItem(str(obj_id)))
                self.table.setItem(row, 1, QTableWidgetItem(str(obj_type)))
                self.table.setItem(row, 2, QTableWidgetItem(str(position)))
                self.table.setItem(row, 3, QTableWidgetItem(str(size)))
                self.table.setItem(row, 4, QTableWidgetItem(str(color)))
                conf_str = f"{confidence:.2f}" if isinstance(confidence, (int, float)) else str(confidence)
                self.table.setItem(row, 5, QTableWidgetItem(conf_str))
                row += 1

    def _on_table_click(self, row, col):
        id_item = self.table.item(row, 0)
        if id_item:
            self.object_selected.emit(id_item.text())
