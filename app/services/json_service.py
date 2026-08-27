import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

POSITION_X_MAP = {
    "left": -10,
    "far_left": -12,
    "middle_left": -7,
    "center_left": -4,
    "center": 0,
    "center_right": 4,
    "middle_right": 7,
    "far_right": 12,
    "right": 10,
}

POSITION_Z_MAP = {
    "top": 18,
    "top_left": 18,
    "top_center": 18,
    "top_right": 18,
    "middle": 10,
    "middle_left": 10,
    "center": 10,
    "center_left": 10,
    "center_right": 10,
    "middle_right": 10,
    "bottom": 3,
    "bottom_left": 3,
    "bottom_center": 3,
    "bottom_right": 3,
    "background": 25,
    "middle_background": 22,
    "center_background": 22,
    "middle_right_background": 22,
    "foreground": 1,
}


def parse_position(position_str):
    if not position_str:
        return {"x": 0, "y": 0, "z": 10}

    pos = str(position_str).lower().strip().replace(" ", "_")

    # Direct lookup
    x = POSITION_X_MAP.get(pos)
    z = POSITION_Z_MAP.get(pos)

    if x is not None and z is not None:
        return {"x": x, "y": 0, "z": z}

    # Parse compound positions
    x = 0
    z = 10

    if "left" in pos:
        x = -7
        if "far" in pos:
            x = -12
        elif "middle" in pos or "center" in pos:
            x = -5
    elif "right" in pos:
        x = 7
        if "far" in pos:
            x = 12
        elif "middle" in pos or "center" in pos:
            x = 5

    if "top" in pos:
        z = 18
    elif "bottom" in pos:
        z = 3
    elif "background" in pos:
        z = 25
    elif "foreground" in pos:
        z = 1

    if "horizon" in pos:
        z = 20

    return {"x": x, "y": 0, "z": z}


class JsonService:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        self.base_dir = Path(base_dir)
        self.data = None
        self.objects = []

    def load_json(self, path=None):
        if path is None:
            path = self.base_dir / "video_analysis.json"
        else:
            path = Path(path)

        if not path.exists():
            logger.error(f"JSON file not found: {path}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            logger.info(f"Loaded JSON from {path}")
            return self.data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            return None

    def get_video_info(self):
        if not self.data:
            return {}
        return self.data.get("video", {})

    def get_frames(self):
        if not self.data:
            return []
        return self.data.get("frames", [])

    def extract_all_objects(self):
        if not self.data:
            return []

        raw_objects = []
        frames = self.get_frames()

        for frame in frames:
            frame_num = frame.get("frame_number", 0)
            timestamp = frame.get("video_timestamp", 0)
            analysis = frame.get("analysis", {})
            objects = analysis.get("objects", [])

            for obj in objects:
                raw_objects.append({
                    "type": obj.get("type", "unknown"),
                    "position_str": obj.get("position", "center"),
                    "color": obj.get("color", "unknown"),
                    "estimated_size": obj.get("estimated_size", "medium"),
                    "movement": obj.get("movement", "static"),
                    "confidence": obj.get("confidence", 0.5),
                    "frame_number": frame_num,
                    "timestamp": timestamp,
                })

        return raw_objects

    def deduplicate_objects(self, raw_objects=None):
        if raw_objects is None:
            raw_objects = self.extract_all_objects()

        if not raw_objects:
            return []

        unique = []
        obj_counter = 0

        for obj in raw_objects:
            position = parse_position(obj["position_str"])
            obj_type = obj["type"]

            # Check if a similar object already exists
            is_duplicate = False
            for existing in unique:
                if existing["type"] != obj_type:
                    continue
                dx = abs(existing["position"]["x"] - position["x"])
                dz = abs(existing["position"]["z"] - position["z"])
                if dx < 4 and dz < 5:
                    # Same object, update confidence if higher
                    if obj["confidence"] > existing["confidence"]:
                        existing["confidence"] = obj["confidence"]
                        existing["color"] = obj["color"]
                        existing["estimated_size"] = obj["estimated_size"]
                    existing["frame_count"] = existing.get("frame_count", 1) + 1
                    is_duplicate = True
                    break

            if not is_duplicate:
                obj_counter += 1
                unique.append({
                    "id": f"obj_{obj_counter:03d}",
                    "type": obj_type,
                    "position": position,
                    "color": obj["color"],
                    "estimated_size": obj["estimated_size"],
                    "confidence": obj["confidence"],
                    "frame_number": obj["frame_number"],
                    "frame_count": 1,
                })

        self.objects = unique
        return unique

    def get_terrain_info(self):
        if not self.data:
            return {}
        frames = self.get_frames()
        if not frames:
            return {}
        analysis = frames[0].get("analysis", {})
        return analysis.get("terrain", {})

    def get_road_info(self):
        if not self.data:
            return {}
        frames = self.get_frames()
        if not frames:
            return {}
        analysis = frames[0].get("analysis", {})
        return analysis.get("road", {})

    def get_scene_info(self):
        if not self.data:
            return {}
        frames = self.get_frames()
        if not frames:
            return {}
        analysis = frames[0].get("analysis", {})
        return analysis.get("scene", {})
