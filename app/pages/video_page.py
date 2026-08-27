import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QSlider, QFrame, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPixmap


class VideoPage(QWidget):
    analysis_complete = pyqtSignal(object)
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.fps = 30
        self.worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Video Input")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)

        upload_frame = QFrame()
        upload_frame.setStyleSheet("""
            QFrame {
                background-color: #171A21;
                border: 2px dashed #2A2D35;
                border-radius: 12px;
                min-height: 80px;
            }
        """)
        upload_layout = QHBoxLayout(upload_frame)
        upload_layout.setContentsMargins(24, 16, 24, 16)

        self.file_label = QLabel("No video selected")
        self.file_label.setStyleSheet("color: #888888; border: none;")

        self.btn_browse = QPushButton("Browse Video")
        self.btn_browse.setProperty("class", "accent-btn")
        self.btn_browse.clicked.connect(self._browse_video)

        upload_layout.addWidget(self.file_label, 1)
        upload_layout.addWidget(self.btn_browse)
        layout.addWidget(upload_frame)

        info_layout = QHBoxLayout()
        info_layout.setSpacing(24)
        self.info_duration = QLabel("Duration: --")
        self.info_resolution = QLabel("Resolution: --")
        self.info_fps = QLabel("FPS: --")
        self.info_frames = QLabel("Frames: --")
        for lbl in [self.info_duration, self.info_resolution, self.info_fps, self.info_frames]:
            lbl.setStyleSheet("color: #888888; font-size: 12px;")
            info_layout.addWidget(lbl)
        info_layout.addStretch()
        layout.addLayout(info_layout)

        self.preview_label = QLabel()
        self.preview_label.setFixedHeight(300)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #171A21; border-radius: 8px;")
        self.preview_label.setText("Video preview will appear here")
        layout.addWidget(self.preview_label)

        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setEnabled(False)
        self.frame_slider.valueChanged.connect(self._on_slider_change)
        layout.addWidget(self.frame_slider)

        analyze_layout = QHBoxLayout()
        self.btn_analyze = QPushButton("Analyze Video with Groq")
        self.btn_analyze.setProperty("class", "accent-btn")
        self.btn_analyze.setFixedHeight(42)
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.clicked.connect(self._start_analysis)
        analyze_layout.addWidget(self.btn_analyze)
        analyze_layout.addStretch()
        layout.addLayout(analyze_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #888888;")
        layout.addWidget(self.progress_label)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        self.results_text.setVisible(False)
        self.results_text.setStyleSheet("font-family: 'Consolas', monospace; font-size: 12px;")
        layout.addWidget(self.results_text)

        layout.addStretch()

    def _browse_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "",
            "Video Files (*.mp4 *.mov *.avi *.mkv);;All Files (*)"
        )
        if path:
            self._load_video(path)

    def _load_video(self, path):
        import cv2
        self.video_path = path
        self.file_label.setText(os.path.basename(path))
        self.file_label.setStyleSheet("color: #E0E0E0; font-weight: bold; border: none;")

        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened():
            self.file_label.setText("Failed to open video")
            return

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = self.total_frames / self.fps

        self.info_duration.setText(f"Duration: {duration:.1f}s")
        self.info_resolution.setText(f"Resolution: {width}x{height}")
        self.info_fps.setText(f"FPS: {self.fps:.1f}")
        self.info_frames.setText(f"Frames: {self.total_frames}")

        self.frame_slider.setEnabled(True)
        self.frame_slider.setRange(0, max(0, self.total_frames - 1))
        self.frame_slider.setValue(0)
        self.btn_analyze.setEnabled(True)

        self._show_frame(0)
        self.status_message.emit(f"Video loaded: {os.path.basename(path)}")

    def _on_slider_change(self, value):
        if self.cap and self.cap.isOpened():
            self._show_frame(value)

    def _show_frame(self, frame_idx):
        import cv2
        if not self.cap:
            return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            scaled = pixmap.scaled(
                self.preview_label.width(), self.preview_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)

    def _start_analysis(self):
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            self.progress_label.setText("ERROR: GROQ_API_KEY not found in .env file")
            self.progress_label.setStyleSheet("color: #E55353;")
            return

        from app.workers import VideoAnalysisWorker
        self.btn_analyze.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(100)
        self.results_text.setVisible(False)

        self.worker = VideoAnalysisWorker(self.video_path, api_key)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, msg, pct):
        self.progress_label.setText(msg)
        self.progress_label.setStyleSheet("color: #888888;")
        self.progress_bar.setValue(pct)

    def _on_finished(self, result):
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Analysis complete!")
        self.progress_label.setStyleSheet("color: #36C275;")
        self.btn_analyze.setEnabled(True)
        self.results_text.setVisible(True)

        frames_analyzed = result.get("video", {}).get("frames_successfully_analyzed", 0)
        total_objects = sum(
            len(f.get("analysis", {}).get("objects", []))
            for f in result.get("frames", [])
        )
        self.results_text.setText(
            f"Frames analyzed: {frames_analyzed}\n"
            f"Total objects detected: {total_objects}\n"
            f"Ready to generate 3D scene."
        )
        self.analysis_complete.emit(result)
        self.status_message.emit(f"Analysis complete: {frames_analyzed} frames, {total_objects} objects")

    def _on_error(self, msg):
        self.progress_bar.setVisible(False)
        self.progress_label.setText(f"Error: {msg[:100]}")
        self.progress_label.setStyleSheet("color: #E55353;")
        self.btn_analyze.setEnabled(True)
        self.status_message.emit(f"Analysis error: {msg[:60]}")
