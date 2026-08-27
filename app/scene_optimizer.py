"""
Scene Optimization and Cleanup
Removes invalid objects, prevents collisions, optimizes placement
"""

import math
from typing import Dict, List, Tuple, Optional


class SceneOptimizer:
    """Optimizes scene by removing overlaps, invalid placements, etc."""

    def __init__(self):
        self.road_buffer = 3.0  # Keep objects 3 units away from roads
        self.object_buffer = 2.0  # Keep objects 2 units from each other

    def optimize_scene(self, scene_objects: List[Dict]) -> List[Dict]:
        """
        Optimize scene by:
        1. Separating roads from other objects
        2. Removing objects placed on roads
        3. Preventing object overlaps
        4. Maintaining spatial organization
        """

        roads = [obj for obj in scene_objects if obj.get("type") in ("road", "road_turn")]
        non_roads = [obj for obj in scene_objects if obj.get("type") not in ("road", "road_turn")]

        # Remove non-road objects that overlap with roads
        filtered_objects = []
        for obj in non_roads:
            if not self._overlaps_with_roads(obj, roads):
                filtered_objects.append(obj)

        # Remove duplicate/overlapping non-road objects
        final_objects = self._remove_overlaps(filtered_objects)

        # Combine roads and cleaned objects
        return roads + final_objects

    def _overlaps_with_roads(self, obj: Dict, roads: List[Dict]) -> bool:
        """Check if object overlaps with any road"""

        obj_pos = obj.get("position", {})
        obj_x = obj_pos.get("x", 0)
        obj_z = obj_pos.get("z", 0)

        for road in roads:
            road_pos = road.get("position", {})
            road_x = road_pos.get("x", 0)
            road_z = road_pos.get("z", 0)

            # Calculate distance
            distance = math.sqrt((obj_x - road_x) ** 2 + (obj_z - road_z) ** 2)

            # If too close to road, it's overlapping
            if distance < self.road_buffer:
                return True

        return False

    def _remove_overlaps(self, objects: List[Dict]) -> List[Dict]:
        """Remove duplicate/overlapping objects"""

        kept = []

        for obj in objects:
            overlaps = False
            obj_pos = obj.get("position", {})
            obj_x = obj_pos.get("x", 0)
            obj_z = obj_pos.get("z", 0)

            for kept_obj in kept:
                kept_pos = kept_obj.get("position", {})
                kept_x = kept_pos.get("x", 0)
                kept_z = kept_pos.get("z", 0)

                distance = math.sqrt((obj_x - kept_x) ** 2 + (obj_z - kept_z) ** 2)

                # If overlapping with kept object, skip this one
                if distance < self.object_buffer:
                    overlaps = True
                    break

            if not overlaps:
                kept.append(obj)

        return kept

    def remove_invalid_objects(self, scene_objects: List[Dict]) -> List[Dict]:
        """
        Remove objects that shouldn't be in the scene:
        - Mountains, clouds, sky (not 3D objects)
        - Objects with very low confidence
        - Duplicate types in same location
        """

        invalid_types = {"mountain", "cloud", "sky", "sun", "water"}
        min_confidence = 0.5

        filtered = []
        for obj in scene_objects:
            obj_type = obj.get("type", "").lower()

            # Skip invalid types
            if obj_type in invalid_types:
                continue

            # Skip low confidence
            confidence = obj.get("confidence", 1.0)
            if confidence < min_confidence:
                continue

            filtered.append(obj)

        return filtered


def optimize_and_clean_scene(scene_data: Dict) -> Dict:
    """
    Main optimization function

    Args:
        scene_data: Scene with objects and terrain

    Returns:
        Optimized scene
    """

    optimizer = SceneOptimizer()

    # Clean invalid objects first
    objects = optimizer.remove_invalid_objects(scene_data.get("objects", []))

    # Then optimize placement
    objects = optimizer.optimize_scene(objects)

    # Update scene
    scene_data["objects"] = objects

    return scene_data
