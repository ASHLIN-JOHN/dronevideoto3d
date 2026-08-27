import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "building": ["apartment1", "buildingbig1", "buildingsmall1"],
    "house": ["buildingsmall1", "apartment1"],
    "apartment": ["apartment1"],
    "structure": ["buildingbig1"],
    "taj_mahal": ["tajmahal"],
    "tajmahal": ["tajmahal"],
    "taj": ["tajmahal"],
    "tree": ["tree"],
    "trees": ["tree"],
    "tree_cluster": ["tree"],
    "vegetation": ["bush", "tree"],
    "bush": ["bush"],
    "shrub": ["bush"],
    "road": ["straightroad", "crosssectionroad"],
    "street": ["straightroad"],
    "path": ["straightroad"],
    "access_road": ["straightroad"],
    "paved_access_road": ["straightroad"],
    "rural_access_road": ["straightroad"],
    "person": ["malestudent", "baldmanindoctoruniform"],
    "people": ["malestudent"],
    "human": ["malestudent"],
    "man": ["malestudent"],
    "woman": ["malestudent"],
    "sign": ["norightturnsignboard"],
    "signboard": ["norightturnsignboard"],
    "traffic_sign": ["norightturnsignboard"],
    "wind_turbine": ["windturbine"],
    "windturbine": ["windturbine"],
    "turbine": ["windturbine"],
    "windmill": ["windturbine"],
    "dustbin": ["dustbin"],
    "bin": ["dustbin"],
    "trash": ["dustbin"],
    "dumpster": ["dustbin"],
    "car": [],
    "vehicle": [],
    "sedan": [],
    "truck": [],
    "motorcycle": [],
    "bicycle": [],
    "mountain": [],
    "mountains": [],
    "mountain_range": [],
    "hill": [],
    "rock": [],
    "cloud": [],
    "clouds": [],
    "sky": [],
    "sun": [],
    "water": [],
    "river": [],
}

SIZE_EXPECTED_HEIGHT = {
    "very_small": 0.5,
    "small": 1.5,
    "medium": 4.0,
    "large": 10.0,
    "very_large": 25.0,
    "large_tall": 15.0,
    "tall": 12.0,
}


class ModelService:
    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        self.base_dir = Path(base_dir)
        self.models_dir = self.base_dir / "Models"
        self.cache_dir = self.base_dir / ".cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata = []
        self._load_metadata()

    def _load_metadata(self):
        metadata_path = self.base_dir / "models_metadata.json"
        cache_path = self.cache_dir / "models_metadata.json"

        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                data = json.load(f)
                self.metadata = data.get("models", [])
        elif cache_path.exists():
            with open(cache_path, "r") as f:
                data = json.load(f)
                self.metadata = data.get("models", [])
        else:
            self.scan_models()

    def scan_models(self):
        self.metadata = []
        if not self.models_dir.exists():
            logger.warning(f"Models directory not found: {self.models_dir}")
            return self.metadata

        for f in sorted(self.models_dir.iterdir()):
            if f.is_dir():
                continue
            if not f.suffix.lower() == ".glb":
                continue
            if "syntheticdontseethisfolder" in str(f):
                continue

            entry = self._inspect_model(f)
            self.metadata.append(entry)

        self._save_cache()
        return self.metadata

    def _inspect_model(self, path):
        entry = {
            "name": path.stem,
            "file": f"Models/{path.name}",
            "dimensions": {"x": 0, "y": 0, "z": 0},
            "center": {"x": 0, "y": 0, "z": 0},
            "mesh_count": 0,
            "file_size_mb": round(path.stat().st_size / 1048576, 2),
            "valid": False,
        }

        try:
            import trimesh
            scene = trimesh.load(str(path))
            if hasattr(scene, "extents"):
                extents = scene.extents
                bounds = scene.bounds
                center = (bounds[0] + bounds[1]) / 2
                entry["dimensions"] = {
                    "x": round(float(extents[0]), 4),
                    "y": round(float(extents[1]), 4),
                    "z": round(float(extents[2]), 4),
                }
                entry["center"] = {
                    "x": round(float(center[0]), 4),
                    "y": round(float(center[1]), 4),
                    "z": round(float(center[2]), 4),
                }
            if hasattr(scene, "geometry"):
                entry["mesh_count"] = len(scene.geometry)
            else:
                entry["mesh_count"] = 1
            entry["valid"] = True
        except Exception as e:
            logger.error(f"Failed to load model {path.name}: {e}")
            entry["valid"] = False
            entry["error"] = str(e)

        return entry

    def _save_cache(self):
        cache_path = self.cache_dir / "models_metadata.json"
        with open(cache_path, "w") as f:
            json.dump({"models": self.metadata}, f, indent=2)

    def get_valid_models(self):
        return [m for m in self.metadata if m.get("valid", False)]

    def get_model_by_name(self, name):
        for m in self.metadata:
            if m["name"] == name:
                return m
        return None

    def find_model_for_type(self, object_type):
        if not object_type:
            return None

        obj_type = object_type.lower().strip().replace(" ", "_")

        # 1. Exact name match
        for m in self.metadata:
            if m["name"] == obj_type and m.get("valid"):
                return m

        # 2. Keyword in filename (strip underscores/spaces for comparison)
        obj_normalized = obj_type.replace("_", "").replace("-", "")
        for m in self.metadata:
            model_normalized = m["name"].replace("_", "").replace("-", "")
            if obj_normalized == model_normalized and m.get("valid"):
                return m
            if obj_normalized in model_normalized and m.get("valid"):
                return m
            if model_normalized in obj_normalized and m.get("valid"):
                return m

        # 3. Category mapping
        candidates = CATEGORY_MAP.get(obj_type, None)
        if candidates is None:
            for key, vals in CATEGORY_MAP.items():
                if key in obj_type or obj_type in key:
                    candidates = vals
                    break

        if candidates:
            for cname in candidates:
                model = self.get_model_by_name(cname)
                if model and model.get("valid"):
                    return model

        return None

    def calculate_scale(self, model, estimated_size):
        if not model or not estimated_size:
            return 1.0

        model_height = model["dimensions"].get("y", 1.0)
        if model_height <= 0:
            return 1.0

        size_str = str(estimated_size).lower().strip()

        # Try to parse from SIZE_EXPECTED_HEIGHT
        expected = None
        for key, val in SIZE_EXPECTED_HEIGHT.items():
            if key in size_str:
                expected = val
                break

        if expected is None:
            # Try to extract a number
            import re
            match = re.search(r"(\d+\.?\d*)\s*m", size_str)
            if match:
                expected = float(match.group(1))

        if expected is None:
            if "small" in size_str:
                expected = 1.5
            elif "large" in size_str:
                expected = 10.0
            elif "medium" in size_str:
                expected = 4.0
            else:
                return 1.0

        scale = expected / model_height

        # Clamp to reasonable range
        if scale < 0.01:
            scale = 0.01
        elif scale > 100.0:
            scale = 100.0

        return round(scale, 4)

    def get_all_metadata(self):
        return self.metadata
