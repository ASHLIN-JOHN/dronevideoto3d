import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SceneService:
    def __init__(self, model_service, json_service, base_dir=None):
        self.model_service = model_service
        self.json_service = json_service
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        self.base_dir = Path(base_dir)
        self.scene_objects = []
        self.corrections_log = []

    def generate_scene(self, objects=None):
        if objects is None:
            objects = self.json_service.deduplicate_objects()

        self.scene_objects = []
        self.corrections_log = []

        for obj in objects:
            scene_obj = self._process_object(obj)
            if scene_obj:
                self.scene_objects.append(scene_obj)

        logger.info(f"Generated scene with {len(self.scene_objects)} objects")
        return self.scene_objects

    def _process_object(self, obj):
        obj_type = obj["type"]
        model = self.model_service.find_model_for_type(obj_type)

        if model is None:
            logger.info(f"No model found for type: {obj_type}")
            return None

        scale_factor = self.model_service.calculate_scale(
            model, obj.get("estimated_size")
        )

        corrections = []

        # Check for obviously wrong scale
        model_height = model["dimensions"].get("y", 1.0)
        scaled_height = model_height * scale_factor

        if scaled_height > 50:
            old_scale = scale_factor
            scale_factor = 20.0 / model_height
            corrections.append({
                "type": "scale_clamp",
                "reason": f"Scaled height {scaled_height:.1f}m exceeds 50m limit",
                "original_scale": old_scale,
                "corrected_scale": scale_factor,
            })
        elif scaled_height < 0.1:
            old_scale = scale_factor
            scale_factor = 0.5 / model_height
            corrections.append({
                "type": "scale_clamp",
                "reason": f"Scaled height {scaled_height:.3f}m too small",
                "original_scale": old_scale,
                "corrected_scale": scale_factor,
            })

        position = obj["position"].copy()

        # Ground objects should have Y=0
        if obj_type in ("road", "street", "path", "access_road"):
            position["y"] = -0.1

        scene_obj = {
            "id": obj["id"],
            "type": obj_type,
            "model": model["file"],
            "model_name": model["name"],
            "position": position,
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {
                "x": round(scale_factor, 4),
                "y": round(scale_factor, 4),
                "z": round(scale_factor, 4),
            },
            "confidence": obj.get("confidence", 0.5),
            "color": obj.get("color", "unknown"),
            "estimated_size": obj.get("estimated_size", "medium"),
            "corrections": corrections,
        }

        if corrections:
            self.corrections_log.append({
                "object_id": obj["id"],
                "model": model["file"],
                "corrections": corrections,
            })

        return scene_obj

    def get_scene_config(self):
        return {
            "objects": self.scene_objects,
            "terrain": self.json_service.get_terrain_info(),
            "road": self.json_service.get_road_info(),
            "scene": self.json_service.get_scene_info(),
            "corrections": self.corrections_log,
        }

    def save_scene(self, path=None):
        if path is None:
            path = self.base_dir / "output" / "scene.json"
        else:
            path = Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)

        config = self.get_scene_config()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"Scene saved to {path}")
        return str(path)

    def load_scene(self, path=None):
        if path is None:
            path = self.base_dir / "output" / "scene.json"
        else:
            path = Path(path)

        if not path.exists():
            logger.error(f"Scene file not found: {path}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.scene_objects = config.get("objects", [])
            self.corrections_log = config.get("corrections", [])
            logger.info(f"Loaded scene from {path} with {len(self.scene_objects)} objects")
            return config
        except Exception as e:
            logger.error(f"Error loading scene: {e}")
            return None

    def update_object(self, obj_id, updates):
        for obj in self.scene_objects:
            if obj["id"] == obj_id:
                for key, value in updates.items():
                    if key in ("position", "rotation", "scale"):
                        obj[key].update(value)
                    else:
                        obj[key] = value
                return obj
        return None

    def remove_object(self, obj_id):
        self.scene_objects = [o for o in self.scene_objects if o["id"] != obj_id]

    def get_corrections_log(self):
        return self.corrections_log
