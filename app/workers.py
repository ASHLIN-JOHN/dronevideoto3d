import os
import json
import time
import traceback
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal
from app.scene_generator_safe import safe_generate_scene
from app.road_network import generate_connected_road_network


class ModelScanWorker(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, models_dir):
        super().__init__()
        self.models_dir = models_dir

    def run(self):
        try:
            import trimesh
            models = []
            glb_files = [f for f in os.listdir(self.models_dir)
                         if f.endswith('.glb') and 'synthetic' not in f.lower()]
            total = len(glb_files)

            for i, filename in enumerate(sorted(glb_files)):
                self.progress.emit(f"Scanning {filename}...", int((i / max(total, 1)) * 100))
                filepath = os.path.join(self.models_dir, filename)
                try:
                    scene = trimesh.load(filepath)
                    if isinstance(scene, trimesh.Scene):
                        bounds = scene.bounds
                        extents = scene.extents
                        center = (bounds[0] + bounds[1]) / 2
                        mesh_count = len(scene.geometry)
                    else:
                        bounds = scene.bounds
                        extents = scene.extents
                        center = (bounds[0] + bounds[1]) / 2
                        mesh_count = 1

                    models.append({
                        "name": filename.replace('.glb', ''),
                        "file": f"Models/{filename}",
                        "dimensions": {
                            "x": round(float(extents[0]), 4),
                            "y": round(float(extents[1]), 4),
                            "z": round(float(extents[2]), 4)
                        },
                        "center": {
                            "x": round(float(center[0]), 4),
                            "y": round(float(center[1]), 4),
                            "z": round(float(center[2]), 4)
                        },
                        "mesh_count": mesh_count,
                        "file_size_mb": round(os.path.getsize(filepath) / 1048576, 2),
                        "valid": True
                    })
                except Exception as e:
                    models.append({
                        "name": filename.replace('.glb', ''),
                        "file": f"Models/{filename}",
                        "valid": False,
                        "error": str(e)
                    })

            self.progress.emit("Scan complete", 100)
            self.finished.emit(models)
        except Exception as e:
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")


class VideoAnalysisWorker(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, video_path, api_key, model_name="qwen/qwen3.6-27b",
                 frame_interval=2, max_width=512, max_height=512):
        super().__init__()
        self.video_path = video_path
        self.api_key = api_key
        self.model_name = model_name
        self.frame_interval = frame_interval
        self.max_width = max_width
        self.max_height = max_height

    def run(self):
        try:
            import cv2
            import base64
            from groq import Groq
            import time

            client = Groq(api_key=self.api_key)

            self.progress.emit("Opening video...", 0)
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self.error.emit(f"Could not open video: {self.video_path}")
                return

            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            interval_frames = max(1, int(fps * self.frame_interval))

            self.progress.emit("Extracting frames...", 5)
            frames = []
            frame_number = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if frame_number % interval_frames == 0:
                    h, w = frame.shape[:2]
                    scale = min(self.max_width / w, self.max_height / h, 1.0)
                    if scale < 1.0:
                        frame = cv2.resize(frame, (int(w * scale), int(h * scale)),
                                           interpolation=cv2.INTER_AREA)
                    _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                    if buffer is not None:
                        frames.append({
                            "image": base64.b64encode(buffer).decode("utf-8"),
                            "timestamp": frame_number / fps,
                            "frame_number": frame_number
                        })
                frame_number += 1
            cap.release()

            if not frames:
                self.error.emit("No frames extracted from video")
                return

            # Limit to 10 frames max to save API tokens
            if len(frames) > 10:
                step = len(frames) // 10
                frames = frames[::step][:10]
                print(f"[VIDEO] Limited frames to 10 for API efficiency")

            # Analyze frames
            self.progress.emit(f"Extracted {len(frames)} frames. Analyzing with Groq...", 10)
            print(f"\n[VIDEO] =====================================")
            print(f"[VIDEO] Total frames to analyze: {len(frames)}")
            print(f"[VIDEO] Model: {self.model_name}")
            print(f"[VIDEO] API Key present: {bool(self.api_key)}")
            print(f"[VIDEO] =====================================\n")

            analyses = []

            for i, frame_data in enumerate(frames):
                pct = 10 + int((i / len(frames)) * 85)
                self.progress.emit(f"Analyzing frame {i+1}/{len(frames)}...", pct)

                prompt = self._get_analysis_prompt(frame_data["timestamp"])

                try:
                    print(f"[VIDEO] Frame {i+1}/{len(frames)}: timestamp={frame_data['timestamp']:.2f}s, image_size={len(frame_data['image'])} bytes")

                    # Send to Groq with the qwen model
                    print(f"[VIDEO] Calling Groq API with model: {self.model_name}")
                    response = client.chat.completions.create(
                        model=self.model_name,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {
                                    "url": f"data:image/jpeg;base64,{frame_data['image']}"
                                }}
                            ]
                        }],
                        max_completion_tokens=2000,
                        temperature=1.0
                    )

                    print(f"[VIDEO] Response object type: {type(response)}")
                    print(f"[VIDEO] Response choices: {len(response.choices)}")

                    if not response.choices:
                        print(f"[VIDEO] ERROR: Empty response choices!")
                        print(f"[VIDEO] Full response: {response}")
                        continue

                    result_text = response.choices[0].message.content
                    print(f"[VIDEO] Content length: {len(result_text)} chars")
                    print(f"[VIDEO] Content preview: {result_text[:200]}")

                    # Extract JSON from response
                    if result_text:
                        start = result_text.find('{')
                        end = result_text.rfind('}')
                        print(f"[VIDEO] JSON search: start={start}, end={end}")
                        if start != -1 and end != -1:
                            result_text = result_text[start:end+1]
                            print(f"[VIDEO] Extracted JSON, length: {len(result_text)} chars")
                        else:
                            print(f"[VIDEO] WARNING: No JSON braces found in response")
                            print(f"[VIDEO] Full response: {result_text}")

                    data = json.loads(result_text)
                    analyses.append({
                        "frame_number": frame_data["frame_number"],
                        "video_timestamp": frame_data["timestamp"],
                        "analysis": data
                    })
                    print(f"[VIDEO] ✓ Frame {i+1} SUCCESS - {len(data.get('objects', []))} objects detected\n")

                except json.JSONDecodeError as e:
                    print(f"[VIDEO] ✗ Frame {i+1} JSON PARSE ERROR: {e}")
                    if 'result_text' in locals():
                        print(f"[VIDEO] Attempted to parse ({len(result_text)} chars):")
                        print(f"[VIDEO] {result_text[:500]}")
                    print()

                except Exception as e:
                    import traceback
                    err_msg = str(e)
                    print(f"[VIDEO] ✗ Frame {i+1} EXCEPTION: {type(e).__name__}: {err_msg}")
                    print(f"[VIDEO] Full traceback:")
                    print(traceback.format_exc())

                    if "rate_limit" in err_msg.lower() or "429" in err_msg or "quota" in err_msg.lower():
                        print(f"[VIDEO] RATE LIMIT REACHED - stopping")
                        break
                    print()

                # Minimal delay between frames
                if i < len(frames) - 1:
                    time.sleep(1)

            # Report results
            if len(analyses) == 0:
                print("\n[VIDEO] =====================================")
                print("[VIDEO] ERROR: No frames successfully analyzed!")
                print("[VIDEO] =====================================")
                print("[VIDEO] Possible causes:")
                print("  1. Groq API key expired or invalid")
                print("  2. API quota exceeded (rate limit)")
                print("  3. Video file corrupted or unreadable")
                print("  4. Groq API response format unexpected")
                print("[VIDEO] Check console output above for specific errors")
                print("[VIDEO] Try again after a few minutes if rate limited\n")
                self.progress.emit("ERROR: Video analysis failed. See console for details.", 100)

            final_result = {
                "video": {
                    "file": self.video_path,
                    "frame_interval_seconds": self.frame_interval,
                    "frames_extracted": len(frames),
                    "frames_successfully_analyzed": len(analyses)
                },
                "frames": analyses
            }

            self.progress.emit("Analysis complete!", 100)
            self.finished.emit(final_result)
        except Exception as e:
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")

    def _get_analysis_prompt(self, timestamp):
        return f"""CAREFULLY analyze this drone video frame. IMPORTANT: Detect and list EVERY object visible.

Return ONLY valid JSON. DO NOT use markdown or ```json.

Frame timestamp: {timestamp:.2f} seconds

CRITICAL: For the "objects" array, include EVERY single object you can see:
- Count wind turbines carefully - list each one individually
- Count vehicles, trees, buildings - everything
- If you see 5 turbines, list 5 separate objects with their positions

Return this structure:
{{
    "scene": {{"description": null, "weather": null, "time_of_day": null}},
    "objects": [
        {{"type": null, "position": null, "color": null, "estimated_size": null, "movement": null, "confidence": 0.0}}
    ],
    "object_summary": {{"total_count": 0, "turbines": 0, "vehicles": 0, "trees": 0, "buildings": 0}},
    "terrain": {{"type": null, "color": null, "texture": null, "vegetation": null, "slope": null, "dryness": null, "ground_condition": null, "confidence": 0.0}},
    "environment": {{"disaster_type": null, "severity": null, "water_level": null, "description": null}},
    "road": {{"present": false, "type": null, "color": null, "condition": null, "width": null, "direction_in_image": null, "lane_markings": null, "traffic": null, "confidence": 0.0}},
    "sun": {{"visible": false, "position": null, "lighting_direction": null, "shadow_direction": null, "shadow_length": null, "confidence": 0.0}},
    "directions": {{"camera_facing": null, "north": null, "east": null, "south": null, "west": null}}
}}

For environment.disaster_type use: "flood", "drought", "wildfire", "storm", "earthquake", "snow", "none"
For environment.severity use: "mild", "moderate", "severe", "extreme"
For terrain.ground_condition use: "normal", "flooded", "cracked", "dry", "muddy", "burnt", "frozen", "sandy"
For objects use positions: top_left, top_center, top_right, middle_left, center, middle_right, bottom_left, bottom_center, bottom_right
REMEMBER: List every wind turbine individually - if there are 8 turbines, create 8 separate objects entries"""


class SceneGenerationWorker(QThread):
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, json_data, models_metadata, models_dir):
        super().__init__()
        self.json_data = json_data
        self.models_metadata = models_metadata
        self.models_dir = models_dir

    def run(self):
        try:
            self.progress.emit("Parsing JSON data...", 10)
            frames = self.json_data.get("frames", [])
            if not frames:
                self.error.emit("No frames found in JSON data")
                return

            self.progress.emit("Tracking objects across frames...", 20)
            tracked_objects = self._track_objects(frames)

            self.progress.emit(f"Found {len(tracked_objects)} unique objects. Matching models...", 40)
            scene_objects = []
            has_road = False
            for i, obj in enumerate(tracked_objects):
                pct = 40 + int((i / max(len(tracked_objects), 1)) * 50)
                self.progress.emit(f"Processing object {i+1}/{len(tracked_objects)}: {obj['type']}", pct)

                if obj["type"].lower() in ("road", "roads", "access_road"):
                    has_road = True
                    continue

                model_match = self._find_best_model(obj["type"])
                if model_match is None:
                    continue

                position = self._convert_position(obj.get("position", "center"), obj.get("position_3d"))
                # Use uniform scale of 1.0 for all objects - NO VARIATION
                scale = 1.0

                scene_objects.append({
                    "id": obj.get("id", f"object_{i+1:03d}"),
                    "type": obj["type"],
                    "model": model_match["file"],
                    "model_name": model_match["name"],
                    "position": position,
                    "rotation": {"x": 0, "y": 0, "z": 0},
                    "scale": {"x": scale, "y": scale, "z": scale},
                    "confidence": obj.get("confidence", 0.5),
                    "color": obj.get("color", ""),
                    "estimated_size": obj.get("estimated_size", "medium"),
                })

            road_info = self._extract_road_info(frames)
            if has_road or road_info.get("present"):
                # Use new connected road network generator
                road_objects = generate_connected_road_network(road_info, len(scene_objects), self.models_metadata)
                scene_objects.extend(road_objects)

            terrain_info = self._extract_terrain(frames)

            # Generate scene with safe fallback system
            self.progress.emit("Finalizing scene with optimizations...", 95)
            scene_data = safe_generate_scene(
                self.json_data,
                scene_objects,
                self.models_metadata,
                enable_enhancements=True
            )

            self.progress.emit("Scene generation complete!", 100)
            self.finished.emit(scene_data)
        except Exception as e:
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")

    def _extract_road_info(self, frames):
        road_data = {"present": False, "directions": [], "type": "access_road"}
        for frame in frames:
            analysis = frame.get("analysis", {})
            road = analysis.get("road", {})
            if road.get("present"):
                road_data["present"] = True
                direction = road.get("direction_in_image", "")
                if direction:
                    road_data["directions"].append(str(direction).lower())
                if road.get("type"):
                    road_data["type"] = road["type"]
        return road_data

    def _generate_road_network(self, road_info, start_idx):
        road_objects = []
        straight_model = None
        cross_model = None
        left_turn_model = None
        right_turn_model = None

        for model in self.models_metadata:
            if not model.get("valid"):
                continue
            name = model["name"].lower()
            if name == "straightroad":
                straight_model = model
            elif name == "crosssectionroad":
                cross_model = model
            elif name == "leftturnroad":
                left_turn_model = model
            elif name == "rightturnroad":
                right_turn_model = model

        if not straight_model:
            return road_objects

        road_length = 8.73 * 0.5
        road_width = 4.16 * 0.5
        scale = 0.5
        road_x = 28

        directions = " ".join(road_info.get("directions", []))
        has_curve_left = "turn_left" in directions or "turning_left" in directions or "sharp_left" in directions
        has_curve_right = "turn_right" in directions or "turning_right" in directions or "sharp_right" in directions
        has_horizontal = "horizontal" in directions
        has_winding = "winding" in directions

        obj_idx = start_idx
        road_pieces = []

        main_road_count = 8
        start_z = -main_road_count * road_length / 2
        for i in range(main_road_count):
            obj_idx += 1
            road_pieces.append({
                "id": f"road_{obj_idx:03d}",
                "type": "road",
                "model": straight_model["file"],
                "model_name": straight_model["name"],
                "position": {"x": road_x, "y": 0, "z": start_z + i * road_length},
                "rotation": {"x": 0, "y": 0, "z": 0},
                "scale": {"x": scale, "y": scale, "z": scale},
                "confidence": 0.9,
                "color": "gray",
                "estimated_size": "large",
            })

        if has_curve_left and left_turn_model:
            obj_idx += 1
            road_pieces.append({
                "id": f"road_{obj_idx:03d}",
                "type": "road_turn",
                "model": left_turn_model["file"],
                "model_name": left_turn_model["name"],
                "position": {"x": road_x, "y": 0, "z": start_z + main_road_count * road_length},
                "rotation": {"x": 0, "y": 0, "z": 0},
                "scale": {"x": scale, "y": scale, "z": scale},
                "confidence": 0.85,
                "color": "gray",
                "estimated_size": "large",
            })
            for i in range(3):
                obj_idx += 1
                road_pieces.append({
                    "id": f"road_{obj_idx:03d}",
                    "type": "road",
                    "model": straight_model["file"],
                    "model_name": straight_model["name"],
                    "position": {"x": road_x + (i + 1) * road_length, "y": 0, "z": start_z + main_road_count * road_length + road_width},
                    "rotation": {"x": 0, "y": 90, "z": 0},
                    "scale": {"x": scale, "y": scale, "z": scale},
                    "confidence": 0.85,
                    "color": "gray",
                    "estimated_size": "large",
                })

        return road_pieces

    def _extract_terrain(self, frames):
        terrain_data = []
        environment_data = []
        for frame in frames:
            analysis = frame.get("analysis", {})
            terrain = analysis.get("terrain", {})
            environment = analysis.get("environment", {})
            if terrain:
                terrain_data.append(terrain)
            if environment:
                environment_data.append(environment)

        if not terrain_data:
            return {"type": "grass", "color": "#4a7c3f", "size": 200, "disaster": "none", "severity": "none", "ground_condition": "normal"}

        color_map = {
            "green": "#4a7c3f", "dark_green": "#2d5a27", "light_green": "#6db85c",
            "brown": "#8B6914", "dark_brown": "#5c4a1e", "sandy": "#c2b280",
            "gray": "#6b6b6b", "dark_gray": "#4a4a4a", "tan": "#d2b48c",
            "yellow": "#b8a840", "red": "#8b4513", "dry_brown": "#a0722a",
            "golden": "#b8860b", "olive": "#6b8e23", "beige": "#c8b88a",
        }

        terrain_type = "grass"
        terrain_color = "#4a7c3f"
        vegetation = "sparse"
        ground_condition = "normal"

        for t in terrain_data:
            if t.get("type"):
                terrain_type = t["type"]
            color_str = str(t.get("color", "")).lower().replace(" ", "_")
            for key, hex_val in color_map.items():
                if key in color_str:
                    terrain_color = hex_val
                    break
            if t.get("vegetation"):
                vegetation = t["vegetation"]
            if t.get("ground_condition"):
                ground_condition = t["ground_condition"]

        disaster_type = "none"
        severity = "none"
        water_level = "none"
        for env in environment_data:
            dt = str(env.get("disaster_type", "none")).lower()
            if dt and dt != "none" and dt != "null":
                disaster_type = dt
            sv = str(env.get("severity", "none")).lower()
            if sv and sv != "none" and sv != "null":
                severity = sv
            wl = str(env.get("water_level", "none")).lower()
            if wl and wl != "none" and wl != "null":
                water_level = wl

        if disaster_type == "flood":
            terrain_color = "#3a5c7a"
            ground_condition = "flooded"
        elif disaster_type == "drought":
            terrain_color = "#a07830"
            terrain_type = "dry_earth"
            ground_condition = "cracked"
        elif disaster_type == "wildfire":
            terrain_color = "#3d2a1a"
            ground_condition = "burnt"
        elif disaster_type == "snow":
            terrain_color = "#e8e8f0"
            ground_condition = "frozen"

        if ground_condition in ("dry", "cracked") and disaster_type == "none":
            terrain_color = "#b89050"
            terrain_type = "dry_earth"

        return {
            "type": terrain_type,
            "color": terrain_color,
            "vegetation": vegetation,
            "ground_condition": ground_condition,
            "disaster": disaster_type,
            "severity": severity,
            "water_level": water_level,
            "size": 200,
        }

    def _track_objects(self, frames):
        seen = {}
        for frame in frames:
            analysis = frame.get("analysis", {})
            objects = analysis.get("objects", [])
            for obj in objects:
                obj_type = obj.get("type", "unknown")
                obj_pos = obj.get("position", "center")
                key = f"{obj_type}_{obj_pos}"
                if key not in seen:
                    seen[key] = {
                        "type": obj_type,
                        "position": obj_pos,
                        "color": obj.get("color"),
                        "estimated_size": obj.get("estimated_size", "medium"),
                        "confidence": obj.get("confidence", 0.5),
                        "count": 0
                    }
                seen[key]["count"] += 1
                conf = obj.get("confidence", 0.5)
                if isinstance(conf, (int, float)) and conf > seen[key]["confidence"]:
                    seen[key]["confidence"] = conf

        return list(seen.values())

    def _find_best_model(self, obj_type):
        if not self.models_metadata:
            return None

        obj_type_lower = obj_type.lower().replace("_", "").replace("-", "").replace(" ", "")

        type_keywords = {
            "wind_turbine": ["windturbine", "turbine"],
            "windturbine": ["windturbine", "turbine"],
            "tree": ["tree", "bush"],
            "trees": ["tree", "bush"],
            "tree_cluster": ["tree"],
            "vegetation": ["tree", "bush"],
            "bush": ["bush", "tree"],
            "car": ["male"],
            "road": ["straightroad", "crosssectionroad", "leftturnroad", "rightturnroad"],
            "building": ["buildingbig1", "buildingsmall1", "apartment1"],
            "buildings": ["buildingbig1", "buildingsmall1", "apartment1"],
            "house": ["buildingsmall1", "apartment1"],
            "apartment": ["apartment1"],
            "person": ["male", "malestudent", "baldmanindoctoruniform"],
            "people": ["male", "malestudent", "baldmanindoctoruniform"],
            "sign": ["routeboard", "noleftturnsignboard", "norightturnsignboard", "nouturnsignboard"],
            "signboard": ["routeboard", "noleftturnsignboard"],
            "dustbin": ["dustbin"],
            "trash": ["dustbin"],
            "mountain": [],
            "mountains": [],
            "mountain_range": [],
            "cloud": [],
            "clouds": [],
            "sun": [],
            "sky": [],
        }

        keywords = type_keywords.get(obj_type_lower, type_keywords.get(obj_type.lower(), []))
        if not keywords:
            keywords = [obj_type_lower]

        for kw in keywords:
            for model in self.models_metadata:
                if not model.get("valid", False):
                    continue
                model_name = model["name"].lower().replace("_", "").replace("-", "")
                if kw == model_name or kw in model_name:
                    return model

        return None

    def _convert_position(self, position_str, position_3d=None):
        if position_3d and isinstance(position_3d, dict):
            return {
                "x": float(position_3d.get("x", 0)),
                "y": float(position_3d.get("z", 0)),
                "z": float(position_3d.get("y", 0))
            }

        position_map = {
            "top_left": {"x": -18, "y": 0, "z": -18},
            "top_center": {"x": 0, "y": 0, "z": -18},
            "top_right": {"x": 18, "y": 0, "z": -18},
            "middle_left": {"x": -18, "y": 0, "z": 0},
            "center": {"x": 0, "y": 0, "z": 0},
            "center_left": {"x": -10, "y": 0, "z": 0},
            "center_right": {"x": 10, "y": 0, "z": 0},
            "middle_right": {"x": 18, "y": 0, "z": 0},
            "bottom_left": {"x": -18, "y": 0, "z": 18},
            "bottom_center": {"x": 0, "y": 0, "z": 18},
            "bottom_right": {"x": 18, "y": 0, "z": 18},
            "far_left": {"x": -22, "y": 0, "z": -5},
            "left": {"x": -14, "y": 0, "z": 0},
            "right": {"x": 14, "y": 0, "z": 0},
            "background": {"x": 0, "y": 0, "z": -25},
            "middle": {"x": 0, "y": 0, "z": -10},
            "middle_background": {"x": 0, "y": 0, "z": -22},
            "middle_right_background": {"x": 12, "y": 0, "z": -22},
            "center_background": {"x": 0, "y": 0, "z": -20},
            "center_left_horizon": {"x": -12, "y": 0, "z": -25},
        }
        pos = position_map.get(position_str, {"x": 0, "y": 0, "z": 0})
        import random
        return {
            "x": pos["x"] + random.uniform(-2, 2),
            "y": pos["y"],
            "z": pos["z"] + random.uniform(-2, 2)
        }

    def _calculate_scale(self, obj, model):
        size_str = str(obj.get("estimated_size", "medium")).lower()
        dims = model.get("dimensions", {})
        max_dim = max(dims.get("x", 1), dims.get("y", 1), dims.get("z", 1))

        size_targets = {
            "very_small": 0.5,
            "small": 1.5,
            "medium": 3.0,
            "large": 5.0,
            "very_large": 8.0,
        }

        target = 3.0
        for key, val in size_targets.items():
            if key in size_str:
                target = val
                break

        if max_dim > 0:
            scale = target / max_dim
        else:
            scale = 1.0

        scale = max(0.1, min(scale, 10.0))
        return round(scale, 3)
