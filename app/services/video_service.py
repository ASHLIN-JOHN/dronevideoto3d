import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class VideoService:
    def __init__(self):
        self.current_path = None
        self.metadata = {}

    def get_metadata(self, video_path):
        path = Path(video_path)
        if not path.exists():
            return None

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        codec_int = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((codec_int >> 8 * i) & 0xFF) for i in range(4)])
        duration = total_frames / fps if fps > 0 else 0

        cap.release()

        self.current_path = str(path)
        self.metadata = {
            "path": str(path),
            "filename": path.name,
            "fps": round(fps, 2),
            "total_frames": total_frames,
            "width": width,
            "height": height,
            "codec": codec,
            "duration": round(duration, 2),
            "resolution": f"{width}x{height}",
        }
        return self.metadata

    def extract_frame(self, video_path, timestamp_seconds):
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30

        frame_number = int(timestamp_seconds * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None
        return frame

    def extract_frame_as_qimage(self, video_path, timestamp_seconds):
        frame = self.extract_frame(video_path, timestamp_seconds)
        if frame is None:
            return None

        from PyQt5.QtGui import QImage
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        return QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
