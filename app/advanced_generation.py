"""
Advanced 3D Scene Generation Engine
Implements realistic positioning, rotation, scaling, and LOD system
"""

import math
import random
from typing import Dict, List, Tuple, Optional


class AdvancedSceneGenerator:
    """Enhanced scene generation with realism and efficiency"""

    def __init__(self, models_metadata: List[Dict], base_scene_size: float = 50.0):
        self.models_metadata = models_metadata
        self.base_scene_size = base_scene_size
        self.placed_objects = []
        self.object_grid = {}  # For collision detection

    def generate_enhanced_scene(self, json_data: Dict, scene_objects: List[Dict]) -> List[Dict]:
        """
        Generate scene with enhanced realism

        Args:
            json_data: Video analysis data with rich metadata
            scene_objects: Basic scene objects from standard generation

        Returns:
            Enhanced scene objects with realistic properties
        """
        enhanced_objects = []
        frame_data = json_data.get("frames", [{}])[0].get("analysis", {})

        # Extract scene metadata
        time_of_day = frame_data.get("scene", {}).get("time_of_day", "day")
        terrain_info = frame_data.get("terrain", {})
        weather = frame_data.get("scene", {}).get("weather", "clear")

        # Calculate lighting based on time
        lighting = self._calculate_lighting(time_of_day, weather)

        # Process each object with enhanced calculations
        for i, obj in enumerate(scene_objects):
            enhanced_obj = obj.copy()

            # Extract object-specific metadata from analysis
            obj_analysis = self._find_object_analysis(frame_data, obj["type"], i)

            # SKIP ALL ENHANCEMENTS FOR ROADS - keep them pristine for connection
            if obj.get("type") == "road":
                # For roads, ONLY keep original position/rotation/scale - NO CHANGES
                pass
            else:
                # For objects: apply enhancements BUT KEEP ORIGINAL SCALE
                # Enhanced positioning with depth awareness
                enhanced_obj["position"] = self._calculate_position_realistic(
                    obj, obj_analysis, i, len(scene_objects)
                )

                # Realistic rotation and orientation
                enhanced_obj["rotation"] = self._calculate_rotation(obj, obj_analysis)

                # DO NOT MODIFY SCALE - keep original from video analysis
                # enhanced_obj["scale"] = self._calculate_scale_advanced(obj, obj_analysis)

            # Apply detected colors and materials
            enhanced_obj["material"] = self._generate_material(obj, obj_analysis, lighting)

            # Calculate LOD level based on distance from camera
            enhanced_obj["lod"] = self._calculate_lod(enhanced_obj["position"])

            # Add shadows and lighting
            enhanced_obj["shadow"] = self._calculate_shadows(enhanced_obj, lighting)

            # Store for collision detection
            self.placed_objects.append(enhanced_obj)
            enhanced_objects.append(enhanced_obj)

        return enhanced_objects

    def _calculate_lighting(self, time_of_day: str, weather: str) -> Dict:
        """Calculate realistic lighting based on time and weather"""

        lighting_presets = {
            "sunrise": {"intensity": 0.6, "color": (1.0, 0.7, 0.5), "angle": 20},
            "morning": {"intensity": 0.9, "color": (1.0, 1.0, 0.95), "angle": 45},
            "noon": {"intensity": 1.0, "color": (1.0, 1.0, 1.0), "angle": 70},
            "afternoon": {"intensity": 0.95, "color": (1.0, 0.95, 0.8), "angle": 50},
            "sunset": {"intensity": 0.7, "color": (1.0, 0.6, 0.3), "angle": 15},
            "dusk": {"intensity": 0.4, "color": (0.5, 0.3, 0.6), "angle": -5},
            "night": {"intensity": 0.2, "color": (0.3, 0.3, 0.5), "angle": 0},
            "day": {"intensity": 0.9, "color": (1.0, 1.0, 1.0), "angle": 45},
        }

        lighting = lighting_presets.get(time_of_day.lower(), lighting_presets["day"])

        # Adjust for weather
        if "rain" in weather.lower() or "overcast" in weather.lower():
            lighting["intensity"] *= 0.7

        elif "clear" in weather.lower():
            lighting["intensity"] *= 1.1

        return lighting

    def _find_object_analysis(self, frame_data: Dict, obj_type: str, index: int) -> Optional[Dict]:
        """Find matching object analysis from frame data"""
        objects = frame_data.get("objects", [])

        # Try to match by type
        type_matches = [o for o in objects if o.get("type", "").lower() == obj_type.lower()]

        if type_matches and index < len(type_matches):
            return type_matches[index]

        return None

    def _calculate_position_realistic(
        self, obj: Dict, obj_analysis: Optional[Dict], index: int, total: int
    ) -> Dict:
        """
        Calculate realistic position with depth awareness

        Improvements:
        - Uses depth/distance if available
        - Applies perspective scaling
        - Prevents overlaps
        - Considers object importance
        """

        # Base position from analysis
        base_pos = self._convert_position_with_depth(obj_analysis)

        # Apply depth-based perspective
        if obj_analysis and "estimated_size" in obj_analysis:
            size = str(obj_analysis.get("estimated_size", "medium")).lower()
            depth_offset = self._get_depth_from_size(size)
            base_pos["z"] += depth_offset

        # Weight by confidence - higher confidence objects placed more carefully
        confidence = obj.get("confidence", 0.5)
        position_jitter = 2.0 * (1.0 - confidence)  # High confidence = precise placement

        # Add natural variation but prevent too much scatter
        base_pos["x"] += random.uniform(-position_jitter, position_jitter)
        base_pos["z"] += random.uniform(-position_jitter, position_jitter)

        # Prevent collisions with already placed objects
        while self._check_collision(base_pos, obj.get("scale", {}).get("x", 1.0)):
            base_pos["x"] += random.uniform(-1, 1)
            base_pos["z"] += random.uniform(-1, 1)

        # Clamp to scene bounds
        scene_half = self.base_scene_size / 2
        base_pos["x"] = max(-scene_half, min(scene_half, base_pos["x"]))
        base_pos["z"] = max(-scene_half, min(scene_half, base_pos["z"]))

        return base_pos

    def _convert_position_with_depth(self, obj_analysis: Optional[Dict]) -> Dict:
        """Convert position with depth awareness"""

        if not obj_analysis:
            return {"x": 0, "y": 0, "z": 0}

        position_str = obj_analysis.get("position", "center")

        # Position map with depth context
        position_depth_map = {
            "top_left": {"x": -15, "y": 0, "z": -20},
            "top_center": {"x": 0, "y": 0, "z": -20},
            "top_right": {"x": 15, "y": 0, "z": -20},
            "middle_left": {"x": -15, "y": 0, "z": -5},
            "center": {"x": 0, "y": 0, "z": 0},
            "center_left": {"x": -8, "y": 0, "z": 0},
            "center_right": {"x": 8, "y": 0, "z": 0},
            "middle_right": {"x": 15, "y": 0, "z": -5},
            "bottom_left": {"x": -15, "y": 0, "z": 15},
            "bottom_center": {"x": 0, "y": 0, "z": 15},
            "bottom_right": {"x": 15, "y": 0, "z": 15},
            "background": {"x": 0, "y": 0, "z": -25},
            "foreground": {"x": 0, "y": 0, "z": 10},
        }

        return position_depth_map.get(position_str, {"x": 0, "y": 0, "z": 0})

    def _get_depth_from_size(self, size_str: str) -> float:
        """Get depth (z) offset based on object size"""
        depth_map = {
            "very_small": 5,
            "small": 3,
            "medium": 0,
            "large": -3,
            "very_large": -5,
        }

        for key, val in depth_map.items():
            if key in size_str:
                return val

        return 0

    def _calculate_rotation(self, obj: Dict, obj_analysis: Optional[Dict]) -> Dict:
        """
        Calculate realistic rotation and orientation

        Improvements:
        - Extracts heading from movement data
        - Applies object-specific orientations
        - Adds realistic variation
        """

        # Base rotation (all zeros by default)
        rotation = {"x": 0, "y": 0, "z": 0}

        if not obj_analysis:
            return rotation

        # Extract heading from analysis
        heading = 0
        movement = obj_analysis.get("movement", "static")

        if "left" in movement.lower():
            heading = 45
        elif "right" in movement.lower():
            heading = -45
        elif "forward" in movement.lower():
            heading = 0
        elif "backward" in movement.lower():
            heading = 180

        # Add natural variation based on object type
        if "turbine" in obj["type"].lower():
            # Turbines slightly rotated for realism
            rotation["y"] = heading + random.uniform(-5, 5)
            rotation["z"] = random.uniform(-2, 2)  # Slight tilt

        elif "vehicle" in obj["type"].lower() or "car" in obj["type"].lower():
            rotation["y"] = heading + random.uniform(-10, 10)

        elif "tree" in obj["type"].lower() or "building" in obj["type"].lower():
            # Trees/buildings slightly rotated for variety
            rotation["y"] = random.uniform(0, 360)
            rotation["z"] = random.uniform(-1, 1)  # Slight tilt

        else:
            # Default: small random rotation for variety
            rotation["y"] = random.uniform(0, 360)
            rotation["z"] = random.uniform(-3, 3)

        return rotation

    def _calculate_scale_advanced(self, obj: Dict, obj_analysis: Optional[Dict]) -> Dict:
        """
        Calculate scale with multiple factors

        Improvements:
        - Uses confidence weighting
        - Considers object type
        - Applies perspective scaling
        - More realistic proportions
        """

        base_scale = obj.get("scale", {})

        # Start with base scale from standard generation
        scale_value = base_scale.get("x", 1.0)

        if obj_analysis:
            # Weight by confidence
            confidence = obj_analysis.get("confidence", 0.5)
            size_str = obj_analysis.get("estimated_size", "medium").lower()

            # Confidence-based scaling: low confidence = smaller
            confidence_factor = 0.5 + (confidence * 0.5)

            # Size-based scaling with more nuance
            size_factors = {
                "very_small": 0.3,
                "small": 0.6,
                "medium": 1.0,
                "large": 1.4,
                "very_large": 1.8,
            }

            size_factor = 1.0
            for key, val in size_factors.items():
                if key in size_str:
                    size_factor = val
                    break

            # Apply confidence weighting
            scale_value *= confidence_factor * size_factor

            # Type-specific scaling adjustments
            obj_type_lower = obj.get("type", "").lower()

            if "turbine" in obj_type_lower:
                # Turbines are typically large
                scale_value *= 1.2

            elif "tree" in obj_type_lower:
                # Trees vary greatly in size
                scale_value *= random.uniform(0.8, 1.3)

            elif "vehicle" in obj_type_lower or "car" in obj_type_lower:
                # Vehicles are relatively uniform
                scale_value *= 0.9

            # Perspective scaling: far objects slightly smaller
            z_distance = abs(obj.get("position", {}).get("z", 0))
            perspective_factor = 1.0 - (z_distance / 50.0) * 0.1
            scale_value *= max(0.5, perspective_factor)

        # Clamp to reasonable range
        scale_value = max(0.2, min(5.0, scale_value))

        return {
            "x": round(scale_value, 3),
            "y": round(scale_value, 3),
            "z": round(scale_value, 3),
        }

    def _generate_material(self, obj: Dict, obj_analysis: Optional[Dict], lighting: Dict) -> Dict:
        """
        Generate realistic material properties

        Improvements:
        - Applies detected colors
        - PBR material properties
        - Lighting-aware materials
        """

        material = {
            "color": (1.0, 1.0, 1.0),
            "metalness": 0.0,
            "roughness": 0.8,
            "emissive": (0.0, 0.0, 0.0),
        }

        if obj_analysis and "color" in obj_analysis:
            color = obj_analysis["color"].lower()
            material["color"] = self._color_string_to_rgb(color)

        # Object-type-specific materials
        obj_type = obj.get("type", "").lower()

        if "metal" in obj_type or "turbine" in obj_type:
            material["metalness"] = 0.8
            material["roughness"] = 0.3

        elif "wood" in obj_type or "tree" in obj_type:
            material["metalness"] = 0.0
            material["roughness"] = 0.95
            if material["color"] == (1.0, 1.0, 1.0):
                material["color"] = (0.4, 0.3, 0.2)  # Default brown

        elif "concrete" in obj_type or "building" in obj_type or "road" in obj_type:
            material["metalness"] = 0.0
            material["roughness"] = 0.7
            if material["color"] == (1.0, 1.0, 1.0):
                material["color"] = (0.5, 0.5, 0.5)  # Default gray

        # Apply lighting tint to material
        lighting_color = lighting.get("color", (1.0, 1.0, 1.0))
        material["color"] = (
            material["color"][0] * lighting_color[0],
            material["color"][1] * lighting_color[1],
            material["color"][2] * lighting_color[2],
        )

        return material

    def _color_string_to_rgb(self, color_str: str) -> Tuple[float, float, float]:
        """Convert color string to RGB tuple"""

        colors = {
            "white": (1.0, 1.0, 1.0),
            "black": (0.2, 0.2, 0.2),
            "red": (1.0, 0.0, 0.0),
            "green": (0.0, 1.0, 0.0),
            "blue": (0.0, 0.0, 1.0),
            "yellow": (1.0, 1.0, 0.0),
            "gray": (0.5, 0.5, 0.5),
            "grey": (0.5, 0.5, 0.5),
            "dark_gray": (0.3, 0.3, 0.3),
            "dark_grey": (0.3, 0.3, 0.3),
            "light_gray": (0.7, 0.7, 0.7),
            "light_grey": (0.7, 0.7, 0.7),
            "orange": (1.0, 0.5, 0.0),
            "brown": (0.6, 0.4, 0.2),
            "cyan": (0.0, 1.0, 1.0),
            "magenta": (1.0, 0.0, 1.0),
            "dark_green": (0.0, 0.5, 0.0),
            "light_green": (0.5, 1.0, 0.5),
            "dark_blue": (0.0, 0.0, 0.5),
            "light_blue": (0.5, 0.5, 1.0),
            "blue_gray": (0.4, 0.4, 0.5),
            "beige": (0.9, 0.85, 0.73),
            "tan": (0.82, 0.71, 0.55),
        }

        return colors.get(color_str, (1.0, 1.0, 1.0))

    def _calculate_lod(self, position: Dict) -> int:
        """
        Calculate level-of-detail based on distance from camera

        LOD 0: Close (detailed)
        LOD 1: Medium (reduced)
        LOD 2: Far (simple)
        LOD 3: Very far (billboard)
        """

        z_distance = abs(position.get("z", 0))
        xy_distance = math.sqrt(position.get("x", 0) ** 2 + position.get("y", 0) ** 2)
        total_distance = math.sqrt(z_distance**2 + xy_distance**2)

        if total_distance < 10:
            return 0
        elif total_distance < 20:
            return 1
        elif total_distance < 35:
            return 2
        else:
            return 3

    def _calculate_shadows(self, obj: Dict, lighting: Dict) -> Dict:
        """Calculate shadow properties based on lighting"""

        return {
            "cast": True,
            "receive": True,
            "intensity": lighting.get("intensity", 1.0) * 0.7,
        }

    def _check_collision(self, position: Dict, radius: float) -> bool:
        """Check if position collides with already placed objects"""

        collision_distance = radius + 2.0  # Add buffer

        for placed_obj in self.placed_objects:
            placed_pos = placed_obj.get("position", {})
            distance = math.sqrt(
                (position["x"] - placed_pos.get("x", 0)) ** 2
                + (position["z"] - placed_pos.get("z", 0)) ** 2
            )

            if distance < collision_distance:
                return True

        return False


def enhance_scene_generation(json_data: Dict, scene_objects: List[Dict], models_metadata: List[Dict]) -> List[Dict]:
    """
    Convenience function to enhance scene objects

    Args:
        json_data: Video analysis data
        scene_objects: Generated scene objects
        models_metadata: Available models metadata

    Returns:
        Enhanced scene objects
    """

    generator = AdvancedSceneGenerator(models_metadata)
    return generator.generate_enhanced_scene(json_data, scene_objects)
