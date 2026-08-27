"""
Taj Mahal Scene Generator
Generates specialized layouts with water path and symmetrical tree placement
"""

from typing import Dict, List, Optional


def generate_taj_mahal_scene(
    json_data: Dict,
    scene_objects: List[Dict],
    models_metadata: List[Dict]
) -> List[Dict]:
    """
    Generate Taj Mahal scene with water path and trees

    Layout:
    - Blue line (water path) down the center
    - Single trees on left and right sides with spacing
    - Taj Mahal as central structure

    Args:
        json_data: Video analysis data
        scene_objects: Basic scene objects
        models_metadata: Available models

    Returns:
        Enhanced scene objects with water path and trees
    """

    enhanced_objects = list(scene_objects)

    # Find if Taj Mahal is in the scene
    taj_mahal_obj = None
    for obj in enhanced_objects:
        if obj.get("type", "").lower() in ["taj_mahal", "tajmahal", "taj", "structure"]:
            taj_mahal_obj = obj
            break

    # If no Taj Mahal found, look for any building to use as center
    if not taj_mahal_obj:
        for obj in enhanced_objects:
            if "building" in obj.get("type", "").lower():
                taj_mahal_obj = obj
                break

    # Place Taj Mahal at center
    if taj_mahal_obj:
        taj_mahal_obj["position"] = {"x": 0, "y": 0, "z": 0}
        taj_mahal_obj["rotation"] = {"x": 0, "y": 0, "z": 0}

    # Add water path (blue line down center)
    water_path = _generate_water_path()
    enhanced_objects.extend(water_path)

    # Add trees on left and right sides
    trees = _generate_symmetrical_trees(models_metadata)
    enhanced_objects.extend(trees)

    return enhanced_objects


def _generate_water_path() -> List[Dict]:
    """
    Generate blue water path down the center of the scene
    Creates line segments rendered as thin objects with blue material

    Returns:
        List of water path segments
    """

    water_segments = []

    num_segments = 9
    z_start = 20
    z_end = -15
    z_step = (z_end - z_start) / (num_segments - 1) if num_segments > 1 else 0

    for i in range(num_segments):
        z_pos = z_start + (i * z_step)

        # Create water path segment
        # These will be rendered by the viewer with custom material
        segment = {
            "id": f"water_path_{i}",
            "type": "water_path",
            "model": "Models/straightroad.glb",
            "model_name": "straightroad",
            "position": {
                "x": 0,
                "y": -0.15,  # Slightly below ground
                "z": z_pos,
            },
            "rotation": {
                "x": 0,
                "y": 0,
                "z": 0,
            },
            "scale": {
                "x": 0.25,  # Very thin width
                "y": 0.03,  # Very thin height
                "z": 2.5,  # Segment length
            },
            "confidence": 0.99,
            "color": "blue",
            "estimated_size": "very_small",
            "material": {
                "color": (0.1, 0.4, 0.9),  # Bright blue
                "metalness": 0.3,
                "roughness": 0.2,
                "emissive": (0.0, 0.15, 0.4),  # Blue glow
                "transparent": True,
                "opacity": 0.8,
            },
            "is_water_path": True,
            "custom_geometry": "line",  # Signal to viewer to treat as water line
        }
        water_segments.append(segment)

    return water_segments


def _generate_symmetrical_trees(models_metadata: List[Dict]) -> List[Dict]:
    """
    Generate single trees on left and right sides with spacing

    Layout:
    - Trees placed in pairs (left/right symmetry)
    - Spacing between pairs
    - Along the length of the scene

    Args:
        models_metadata: Available models metadata

    Returns:
        List of tree objects
    """

    trees = []

    # Find tree model
    tree_model = None
    for model in models_metadata:
        if model.get("name", "").lower() == "tree" and model.get("valid"):
            tree_model = model
            break

    if not tree_model:
        return []

    # Parameters for tree placement
    tree_spacing_z = 5  # Distance between tree pairs along z-axis
    tree_lateral_distance = 8  # Distance from center (x offset)
    z_start = 15
    z_end = -15

    num_tree_pairs = 7
    z_step = (z_end - z_start) / (num_tree_pairs - 1) if num_tree_pairs > 1 else 0

    tree_id = 0
    for i in range(num_tree_pairs):
        z_pos = z_start + (i * z_step)

        # Add slight random variation to z for natural look
        import random
        z_variation = random.uniform(-0.5, 0.5)
        z_pos += z_variation

        # Left tree
        left_tree = {
            "id": f"tree_left_{i}",
            "type": "tree",
            "model": tree_model["file"],
            "model_name": tree_model["name"],
            "position": {
                "x": -tree_lateral_distance,
                "y": 0,
                "z": z_pos,
            },
            "rotation": {
                "x": 0,
                "y": random.uniform(0, 360),  # Random rotation for variety
                "z": random.uniform(-2, 2),  # Slight tilt
            },
            "scale": {
                "x": 1.0,
                "y": 1.0,
                "z": 1.0,
            },
            "confidence": 0.9,
            "color": "green",
            "estimated_size": "large",
            "is_taj_mahal_tree": True,
        }
        trees.append(left_tree)

        # Right tree (mirrored position)
        right_tree = {
            "id": f"tree_right_{i}",
            "type": "tree",
            "model": tree_model["file"],
            "model_name": tree_model["name"],
            "position": {
                "x": tree_lateral_distance,
                "y": 0,
                "z": z_pos,
            },
            "rotation": {
                "x": 0,
                "y": random.uniform(0, 360),  # Random rotation for variety
                "z": random.uniform(-2, 2),  # Slight tilt
            },
            "scale": {
                "x": 1.0,
                "y": 1.0,
                "z": 1.0,
            },
            "confidence": 0.9,
            "color": "green",
            "estimated_size": "large",
            "is_taj_mahal_tree": True,
        }
        trees.append(right_tree)

    return trees
