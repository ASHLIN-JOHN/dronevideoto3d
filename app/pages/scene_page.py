import os
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSplitter, QFrame, QTreeWidget, QTreeWidgetItem,
    QDoubleSpinBox, QGroupBox, QGridLayout, QFileDialog,
    QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QUrl, QObject
from PyQt5.QtGui import QFont

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage
    from PyQt5.QtWebChannel import QWebChannel
    from PyQt5.QtWebEngineCore import QWebEngineScript
    HAS_WEBENGINE = True
except ImportError:
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage, QWebEngineScript
        from PyQt5.QtWebChannel import QWebChannel
        HAS_WEBENGINE = True
    except ImportError:
        HAS_WEBENGINE = False


class ViewerBridge(QObject):
    object_selected = pyqtSignal(str, dict)
    object_deselected = pyqtSignal()
    object_transformed = pyqtSignal(str, dict)
    model_loaded = pyqtSignal(str)
    model_error = pyqtSignal(str, str)
    viewer_ready = pyqtSignal()

    @pyqtSlot(str, str)
    def onObjectSelected(self, object_id, transform_json):
        try:
            transform = json.loads(transform_json)
            self.object_selected.emit(object_id, transform)
        except json.JSONDecodeError:
            self.object_selected.emit(object_id, {})

    @pyqtSlot()
    def onObjectDeselected(self):
        self.object_deselected.emit()

    @pyqtSlot(str, str)
    def onTransformChanged(self, object_id, transform_json):
        try:
            transform = json.loads(transform_json)
            self.object_transformed.emit(object_id, transform)
        except json.JSONDecodeError:
            pass

    @pyqtSlot(str)
    def onModelLoaded(self, object_id):
        self.model_loaded.emit(object_id)

    @pyqtSlot(str, str)
    def onModelError(self, object_id, error):
        self.model_error.emit(object_id, error)

    @pyqtSlot()
    def viewerReady(self):
        self.viewer_ready.emit()


class ScenePage(QWidget):
    status_message = pyqtSignal(str)
    request_generate = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_data = None
        self.selected_object_id = None
        self._viewer_ready = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        self.viewer_widget = self._create_viewer()
        splitter.addWidget(self.viewer_widget)

        self.side_panel = self._create_side_panel()
        splitter.addWidget(self.side_panel)

        splitter.setSizes([800, 320])
        layout.addWidget(splitter)

    def _create_viewer(self):
        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()

            settings = self.web_view.settings()
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
            settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
            settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
            settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)

            self.bridge = ViewerBridge()
            self.bridge.object_selected.connect(self._on_object_selected_with_transform)
            self.bridge.object_deselected.connect(self._on_object_deselected)
            self.bridge.object_transformed.connect(self._on_object_transformed)
            self.bridge.viewer_ready.connect(self._on_viewer_ready)

            self.channel = QWebChannel()
            self.channel.registerObject("bridge", self.bridge)
            self.web_view.page().setWebChannel(self.channel)

            self.web_view.loadFinished.connect(self._on_page_loaded)
            self.web_view.setUrl(QUrl("http://127.0.0.1:8765/app/viewer/web/index.html"))

            from PyQt5.QtCore import QTimer
            QTimer.singleShot(5000, self._force_viewer_ready)

            container_layout.addWidget(self.web_view)
        else:
            placeholder = QLabel("WebEngine not available.\nInstall PyQtWebEngine for 3D viewer.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #888; font-size: 16px; background: #171A21;")
            container_layout.addWidget(placeholder)

        return container

    def _create_side_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color: #171A21; }")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        toolbar = QHBoxLayout()
        self.btn_generate = QPushButton("Generate")
        self.btn_generate.setProperty("class", "accent-btn")
        self.btn_generate.clicked.connect(lambda: self.request_generate.emit())

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self._clear_scene)

        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self._save_scene)

        self.btn_load = QPushButton("Load")
        self.btn_load.clicked.connect(self._load_scene)

        toolbar.addWidget(self.btn_generate)
        toolbar.addWidget(self.btn_clear)
        toolbar.addWidget(self.btn_save)
        toolbar.addWidget(self.btn_load)
        layout.addLayout(toolbar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.progress_label)

        camera_layout = QHBoxLayout()
        for label, cmd in [("Perspective", "perspective"), ("Top", "top"),
                           ("Front", "front"), ("Side", "side"), ("Fit", "fitAll")]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda checked, c=cmd: self._set_camera(c))
            camera_layout.addWidget(btn)
        layout.addLayout(camera_layout)

        obj_label = QLabel("Objects")
        obj_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(obj_label)

        self.object_tree = QTreeWidget()
        self.object_tree.setHeaderLabels(["ID", "Type", "Model"])
        self.object_tree.setMaximumHeight(200)
        self.object_tree.setAlternatingRowColors(True)
        self.object_tree.itemClicked.connect(self._on_tree_item_clicked)
        layout.addWidget(self.object_tree)

        inspector_label = QLabel("Inspector")
        inspector_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        layout.addWidget(inspector_label)

        self.inspector_frame = QFrame()
        insp_layout = QGridLayout(self.inspector_frame)
        insp_layout.setContentsMargins(0, 0, 0, 0)
        insp_layout.setSpacing(6)

        self.lbl_id = QLabel("--")
        self.lbl_type = QLabel("--")
        self.lbl_model = QLabel("--")
        self.lbl_confidence = QLabel("--")

        insp_layout.addWidget(QLabel("ID:"), 0, 0)
        insp_layout.addWidget(self.lbl_id, 0, 1, 1, 3)
        insp_layout.addWidget(QLabel("Type:"), 1, 0)
        insp_layout.addWidget(self.lbl_type, 1, 1, 1, 3)
        insp_layout.addWidget(QLabel("Model:"), 2, 0)
        insp_layout.addWidget(self.lbl_model, 2, 1, 1, 3)
        insp_layout.addWidget(QLabel("Conf:"), 3, 0)
        insp_layout.addWidget(self.lbl_confidence, 3, 1, 1, 3)

        insp_layout.addWidget(QLabel("Position"), 4, 0, 1, 4)
        self.spin_px = self._make_spin(-500, 500)
        self.spin_py = self._make_spin(-500, 500)
        self.spin_pz = self._make_spin(-500, 500)
        insp_layout.addWidget(QLabel("X"), 5, 0)
        insp_layout.addWidget(self.spin_px, 5, 1)
        insp_layout.addWidget(QLabel("Y"), 5, 2)
        insp_layout.addWidget(self.spin_py, 5, 3)
        row6_lbl = QLabel("Z")
        insp_layout.addWidget(row6_lbl, 6, 0)
        insp_layout.addWidget(self.spin_pz, 6, 1)

        insp_layout.addWidget(QLabel("Rotation"), 7, 0, 1, 4)
        self.spin_rx = self._make_spin(-360, 360)
        self.spin_ry = self._make_spin(-360, 360)
        self.spin_rz = self._make_spin(-360, 360)
        insp_layout.addWidget(QLabel("X"), 8, 0)
        insp_layout.addWidget(self.spin_rx, 8, 1)
        insp_layout.addWidget(QLabel("Y"), 8, 2)
        insp_layout.addWidget(self.spin_ry, 8, 3)
        insp_layout.addWidget(QLabel("Z"), 9, 0)
        insp_layout.addWidget(self.spin_rz, 9, 1)

        insp_layout.addWidget(QLabel("Scale"), 10, 0, 1, 4)
        self.spin_sx = self._make_spin(0.01, 100)
        self.spin_sy = self._make_spin(0.01, 100)
        self.spin_sz = self._make_spin(0.01, 100)
        insp_layout.addWidget(QLabel("X"), 11, 0)
        insp_layout.addWidget(self.spin_sx, 11, 1)
        insp_layout.addWidget(QLabel("Y"), 11, 2)
        insp_layout.addWidget(self.spin_sy, 11, 3)
        insp_layout.addWidget(QLabel("Z"), 12, 0)
        insp_layout.addWidget(self.spin_sz, 12, 1)

        self.btn_apply = QPushButton("Apply Transform")
        self.btn_apply.clicked.connect(self._apply_transform)
        insp_layout.addWidget(self.btn_apply, 13, 0, 1, 4)

        layout.addWidget(self.inspector_frame)
        layout.addStretch()

        return panel

    def _make_spin(self, min_val, max_val):
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(3)
        spin.setSingleStep(0.1)
        spin.setFixedWidth(80)
        return spin

    def set_scene(self, scene_data):
        self.scene_data = scene_data
        self._populate_object_tree()
        self._send_scene_to_viewer()

    def _populate_object_tree(self):
        self.object_tree.clear()
        if not self.scene_data:
            return
        for obj in self.scene_data.get("objects", []):
            item = QTreeWidgetItem([
                obj.get("id", ""),
                obj.get("type", ""),
                obj.get("model_name", "")
            ])
            self.object_tree.addTopLevelItem(item)

    def _on_page_loaded(self, ok):
        if ok and HAS_WEBENGINE:
            inject_js = """
            if (typeof qt === 'undefined') {
                window.qt = { webChannelTransport: {
                    send: function(msg) { /* handled by Qt */ },
                    onmessage: null
                }};
            }
            """
            self.web_view.page().runJavaScript(inject_js)
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, self._force_viewer_ready)

    def _force_viewer_ready(self):
        if not self._viewer_ready:
            self._viewer_ready = True
            if self.scene_data:
                self._send_scene_to_viewer()

    def _on_viewer_ready(self):
        self._viewer_ready = True
        if self.scene_data:
            self._send_scene_to_viewer()

    def _on_object_selected_with_transform(self, obj_id, transform):
        self._select_object(obj_id)
        items = self.object_tree.findItems(obj_id, Qt.MatchExactly, 0)
        if items:
            self.object_tree.setCurrentItem(items[0])

    def _on_object_deselected(self):
        self.selected_object_id = None
        self.object_tree.clearSelection()

    def _send_scene_to_viewer(self):
        if not HAS_WEBENGINE or not self.scene_data:
            return
        if not self._viewer_ready:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1000, self._send_scene_to_viewer)
            return

        self.web_view.page().runJavaScript("window.viewer_clearScene();")

        terrain = self.scene_data.get("terrain", {})
        if terrain:
            terrain_json = json.dumps(terrain).replace("'", "\\'")
            self.web_view.page().runJavaScript(f"window.viewer_setTerrain('{terrain_json}');")

        for obj in self.scene_data.get("objects", []):
            model_rel = obj["model"].replace("\\", "/")
            model_url = f"http://127.0.0.1:8765/{model_rel}"
            pos = obj.get("position", {})
            rot = obj.get("rotation", {})
            scl = obj.get("scale", {})
            meta = {
                "type": obj.get("type", ""),
                "model_name": obj.get("model_name", ""),
                "confidence": obj.get("confidence", 0),
                "color": obj.get("color", ""),
                "material": obj.get("material", {}),
                "is_water_path": obj.get("is_water_path", False),
                "is_taj_mahal_tree": obj.get("is_taj_mahal_tree", False),
            }
            meta_json = json.dumps(meta)
            js = (f"window.viewer_loadModel('{obj['id']}', '{model_url}', "
                  f"{pos.get('x',0)}, {pos.get('y',0)}, {pos.get('z',0)}, "
                  f"{rot.get('x',0)}, {rot.get('y',0)}, {rot.get('z',0)}, "
                  f"{scl.get('x',1)}, {scl.get('y',1)}, {scl.get('z',1)}, "
                  f"'{meta_json}');")
            self.web_view.page().runJavaScript(js)

        from PyQt5.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.web_view.page().runJavaScript("window.viewer_fitAll();"))

    def _on_tree_item_clicked(self, item, column):
        obj_id = item.text(0)
        self._select_object(obj_id)

    def _select_object(self, obj_id):
        self.selected_object_id = obj_id
        if not self.scene_data:
            return
        for obj in self.scene_data.get("objects", []):
            if obj.get("id") == obj_id:
                self.lbl_id.setText(obj.get("id", "--"))
                self.lbl_type.setText(obj.get("type", "--"))
                self.lbl_model.setText(obj.get("model_name", "--"))
                conf = obj.get("confidence", 0)
                self.lbl_confidence.setText(f"{conf:.2f}" if isinstance(conf, (int, float)) else str(conf))

                pos = obj.get("position", {})
                self.spin_px.setValue(pos.get("x", 0))
                self.spin_py.setValue(pos.get("y", 0))
                self.spin_pz.setValue(pos.get("z", 0))

                rot = obj.get("rotation", {})
                self.spin_rx.setValue(rot.get("x", 0))
                self.spin_ry.setValue(rot.get("y", 0))
                self.spin_rz.setValue(rot.get("z", 0))

                scale = obj.get("scale", {})
                self.spin_sx.setValue(scale.get("x", 1))
                self.spin_sy.setValue(scale.get("y", 1))
                self.spin_sz.setValue(scale.get("z", 1))
                break

        if HAS_WEBENGINE:
            js = f"window.viewer_selectObject('{obj_id}');"
            self.web_view.page().runJavaScript(js)

    def _on_object_transformed(self, obj_id, transform):
        if not self.scene_data:
            return
        for obj in self.scene_data.get("objects", []):
            if obj.get("id") == obj_id:
                if "position" in transform:
                    obj["position"] = transform["position"]
                if "rotation" in transform:
                    obj["rotation"] = transform["rotation"]
                if "scale" in transform:
                    obj["scale"] = transform["scale"]
                if obj_id == self.selected_object_id:
                    self._select_object(obj_id)
                break

    def _apply_transform(self):
        if not self.selected_object_id or not self.scene_data:
            return

        for obj in self.scene_data.get("objects", []):
            if obj.get("id") == self.selected_object_id:
                obj["position"] = {"x": self.spin_px.value(), "y": self.spin_py.value(), "z": self.spin_pz.value()}
                obj["rotation"] = {"x": self.spin_rx.value(), "y": self.spin_ry.value(), "z": self.spin_rz.value()}
                obj["scale"] = {"x": self.spin_sx.value(), "y": self.spin_sy.value(), "z": self.spin_sz.value()}
                break

        if HAS_WEBENGINE:
            px, py, pz = self.spin_px.value(), self.spin_py.value(), self.spin_pz.value()
            rx, ry, rz = self.spin_rx.value(), self.spin_ry.value(), self.spin_rz.value()
            sx, sy, sz = self.spin_sx.value(), self.spin_sy.value(), self.spin_sz.value()
            js = (f"window.viewer_updateTransform('{self.selected_object_id}', "
                  f"{px}, {py}, {pz}, {rx}, {ry}, {rz}, {sx}, {sy}, {sz});")
            self.web_view.page().runJavaScript(js)

    def _set_camera(self, preset):
        if HAS_WEBENGINE:
            # Map button labels to viewer API presets
            preset_map = {"fitAll": "fit_all"}
            p = preset_map.get(preset, preset)
            js = f"window.viewer_setCameraPreset('{p}');"
            self.web_view.page().runJavaScript(js)

    def _clear_scene(self):
        self.scene_data = None
        self.object_tree.clear()
        self.selected_object_id = None
        if HAS_WEBENGINE:
            self.web_view.page().runJavaScript("window.viewer_clearScene();")
        self.status_message.emit("Scene cleared")

    def _save_scene(self):
        if not self.scene_data:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Scene", "scene.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.scene_data, f, indent=2)
            self.status_message.emit(f"Scene saved to {path}")

    def _load_scene(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Scene", "", "JSON (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.set_scene(data)
                self.status_message.emit(f"Scene loaded from {path}")
            except Exception as e:
                self.status_message.emit(f"Failed to load scene: {e}")

    def show_progress(self, msg, pct):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(pct)
        self.progress_label.setText(msg)

    def hide_progress(self):
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
