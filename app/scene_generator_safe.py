"""
Safe Scene Generation with Fallback
Ensures scene always generates, with optional enhancements
"""

import json
from typing import Dict, List, Optional


def safe_generate_scene(
    json_data: Dict,
    scene_objects: List[Dict],
    models_metadata: List[Dict],
    enable_enhancements: bool = True
) -> Dict:
    """
    Safe scene generation that always produces output

    Args:
        json_data: Video analysis JSON
        scene_objects: Basic scene objects
        models_metadata: Available models
        enable_enhancements: Enable advanced features

    Returns:
        Complete scene data
    """

    try:
        terrain_info = extract_terrain(json_data)

        # Start with basic objects
        final_objects = list(scene_objects)  # Make a copy

        if enable_enhancements:
            # Check if scene is Taj Mahal - apply specialized generation
            if _is_taj_mahal_scene(final_objects, json_data):
                try:
                    from app.taj_mahal_generator import generate_taj_mahal_scene
                    final_objects = generate_taj_mahal_scene(json_data, final_objects, models_metadata)
                    print("[OK] Taj Mahal specialized generation applied")
                except Exception as e:
                    print(f"[WARNING] Taj Mahal generation failed, trying advanced enhancements: {str(e)}")
                    # Fallback to standard enhancements
                    try:
                        from app.advanced_generation import enhance_scene_generation
                        final_objects = enhance_scene_generation(json_data, final_objects, models_metadata)
                        print("[OK] Advanced enhancements applied")
                    except Exception as e2:
                        print(f"[WARNING] Advanced enhancements also failed: {str(e2)}")
            else:
                # Standard enhancements for non-Taj Mahal scenes
                try:
                    from app.advanced_generation import enhance_scene_generation
                    final_objects = enhance_scene_generation(json_data, final_objects, models_metadata)
                    print("[OK] Advanced enhancements applied")
                except Exception as e:
                    print(f"[WARNING] Enhancements failed, continuing with basic: {str(e)}")

        # Create basic scene
        scene_data = {
            "objects": final_objects,
            "terrain": terrain_info,
            "metadata": {
                "total_objects": len(final_objects),
                "source_frames": len(json_data.get("frames", [])),
                "enhanced": enable_enhancements,
            }
        }

        # Apply collision detection to remove overlaps
        try:
            from app.collision_detector import detect_and_remove_collisions
            scene_data = detect_and_remove_collisions(scene_data)
            print("[OK] Collision detection applied")
        except Exception as e:
            print(f"[WARNING] Collision detection failed, continuing: {str(e)}")

        # Save for debugging
        import json
        with open("output/scene.json", "w") as f:
            json.dump(scene_data, f, indent=2)
        print(f"[OK] Scene saved to output/scene.json with {len(scene_data.get('objects', []))} objects")

        return scene_data

    except Exception as e:
        print(f"[ERROR] Scene generation failed: {str(e)}")
        # Absolute fallback - return basic scene
        return {
            "objects": scene_objects,
            "terrain": extract_terrain(json_data),
            "metadata": {
                "total_objects": len(scene_objects),
                "source_frames": len(json_data.get("frames", [])),
                "enhanced": False,
                "error": str(e)
            }
        }


def _is_taj_mahal_scene(scene_objects: List[Dict], json_data: Dict) -> bool:
    """Check if scene contains Taj Mahal or monument"""

    # Check in scene objects
    for obj in scene_objects:
        obj_type = obj.get("type", "").lower()
        if any(keyword in obj_type for keyword in ["taj", "tajmahal", "monument", "palace"]):
            return True

    # Check in video analysis data
    frames = json_data.get("frames", [])
    if frames:
        analysis = frames[0].get("analysis", {})
        scene_info = analysis.get("scene", {})
        scene_str = str(scene_info).lower()
        if "taj" in scene_str or "monument" in scene_str:
            return True

        objects = analysis.get("objects", [])
        for obj in objects:
            obj_type = str(obj.get("type", "")).lower()
            if any(keyword in obj_type for keyword in ["taj", "tajmahal", "monument", "palace"]):
                return True

    return False


def extract_terrain(json_data: Dict) -> Dict:
    """Extract terrain information from JSON"""

    frames = json_data.get("frames", [])
    if not frames:
        return {"type": "flat", "size": 100}

    terrain_info = frames[0].get("analysis", {}).get("terrain", {})

    return {
        "type": terrain_info.get("type", "flat"),
        "size": 100,
        "vegetation": terrain_info.get("vegetation", "grass"),
        "slope": terrain_info.get("slope", "flat"),
    }
