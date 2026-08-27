"""
Collision Detection and Spatial Analysis
Prevents overlaps between roads, objects, and entities
"""

import math
from typing import Dict, List, Tuple, Optional


class CollisionDetector:
    """Detects and prevents collisions between scene objects"""

    def __init__(self):
        self.road_buffer = 5.0  # Keep objects 5 units away from roads
        self.object_buffer = 3.0  # Keep objects 3 units from each other
        self.roads = []
        self.objects = []

    def set_roads(self, roads: List[Dict]):
        """Register road positions"""
        self.roads = roads

    def filter_objects(self, objects: List[Dict]) -> List[Dict]:
        """
        Filter objects to remove those that collide with roads or each other
        """
        # First, remove objects that overlap with roads
        safe_objects = []
        for obj in objects:
            if not self._collides_with_roads(obj):
                safe_objects.append(obj)

        # Then remove objects that overlap with each other
        final_objects = self._remove_object_overlaps(safe_objects)

        return final_objects

    def _collides_with_roads(self, obj: Dict) -> bool:
        """Check if object collides with any road"""
        if not obj.get("position"):
            return True

        obj_pos = obj["position"]
        obj_x = obj_pos.get("x", 0)
        obj_z = obj_pos.get("z", 0)
        obj_size = obj.get("scale", {}).get("x", 1.0) * 2.0  # Approximate radius

        for road in self.roads:
            road_pos = road["position"]
            road_x = road_pos.get("x", 0)
            road_z = road_pos.get("z", 0)

            # Distance to road
            distance = math.sqrt((obj_x - road_x) ** 2 + (obj_z - road_z) ** 2)

            # Check collision: object center too close to road, or object extends into road
            collision_distance = self.road_buffer + (obj_size / 2)
            if distance < collision_distance:
                return True

        return False

    def _remove_object_overlaps(self, objects: List[Dict]) -> List[Dict]:
        """Remove objects that overlap with each other"""
        kept = []

        for obj in objects:
            if not obj.get("position"):
                kept.append(obj)
                continue

            obj_pos = obj["position"]
            obj_x = obj_pos.get("x", 0)
            obj_z = obj_pos.get("z", 0)
            obj_size = obj.get("scale", {}).get("x", 1.0) * 2.0

            overlaps = False
            for kept_obj in kept:
                if not kept_obj.get("position"):
                    continue

                kept_pos = kept_obj["position"]
                kept_x = kept_pos.get("x", 0)
                kept_z = kept_pos.get("z", 0)
                kept_size = kept_obj.get("scale", {}).get("x", 1.0) * 2.0

                distance = math.sqrt((obj_x - kept_x) ** 2 + (obj_z - kept_z) ** 2)

                # Collision if distance < sum of radii
                collision_distance = self.object_buffer + (obj_size / 2) + (kept_size / 2)
                if distance < collision_distance:
                    overlaps = True
                    break

            if not overlaps:
                kept.append(obj)

        return kept


def detect_and_remove_collisions(scene_data: Dict) -> Dict:
    """Main function to clean collisions from scene"""
    detector = CollisionDetector()

    objects = scene_data.get("objects", [])
    roads = [o for o in objects if o.get("type") == "road"]
    non_roads = [o for o in objects if o.get("type") != "road"]

    # Register roads
    detector.set_roads(roads)

    # Filter non-road objects
    safe_non_roads = detector.filter_objects(non_roads)

    # Combine back
    scene_data["objects"] = roads + safe_non_roads

    return scene_data
