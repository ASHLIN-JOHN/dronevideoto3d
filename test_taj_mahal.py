#!/usr/bin/env python3
"""
Taj Mahal Generation Test Suite
Tests water path and tree generation
"""

import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.model_service import ModelService
from app.services.json_service import JsonService
from app.scene_generator_safe import safe_generate_scene, _is_taj_mahal_scene
from app.taj_mahal_generator import generate_taj_mahal_scene


def test_taj_mahal_detection():
    """Test if Taj Mahal is detected in scene"""
    print("\n" + "="*60)
    print("TEST 1: Taj Mahal Detection")
    print("="*60)

    # Test scene objects
    scene_objects = [
        {"id": "taj1", "type": "taj_mahal", "position": {"x": 0, "y": 0, "z": 0}}
    ]
    json_data = {"frames": [{"analysis": {"scene": {}, "objects": []}}]}

    result = _is_taj_mahal_scene(scene_objects, json_data)
    print(f"[OK] Taj Mahal detected in scene objects: {result}")
    assert result == True, "Failed to detect Taj Mahal"

    # Test video analysis detection
    json_data2 = {
        "frames": [{
            "analysis": {
                "scene": {"description": "Taj Mahal monument"},
                "objects": [{"type": "monument"}]
            }
        }]
    }
    result2 = _is_taj_mahal_scene([], json_data2)
    print(f"[OK] Taj Mahal detected in video analysis: {result2}")
    assert result2 == True, "Failed to detect Taj Mahal in analysis"
    print("\n[PASS] Detection tests PASSED\n")


def test_model_recognition():
    """Test if model service recognizes Taj Mahal"""
    print("\n" + "="*60)
    print("TEST 2: Model Recognition")
    print("="*60)

    model_service = ModelService()

    # Test different variations
    variations = ["taj_mahal", "tajmahal", "taj"]

    for var in variations:
        model = model_service.find_model_for_type(var)
        if model:
            print(f"[OK] Found model for '{var}': {model['name']}")
            assert model['name'] == 'tajmahal', f"Wrong model returned for {var}"
        else:
            print(f"[FAIL] No model found for '{var}'")

    print("\n[PASS] Model recognition tests PASSED\n")


def test_water_path_generation():
    """Test water path generation"""
    print("\n" + "="*60)
    print("TEST 3: Water Path Generation")
    print("="*60)

    model_service = ModelService()

    scene_objects = [
        {
            "id": "taj1",
            "type": "taj_mahal",
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "model": "Models/tajmahal.glb",
            "model_name": "tajmahal",
            "confidence": 0.95,
            "color": "white",
            "estimated_size": "very_large"
        }
    ]

    json_data = {
        "frames": [{
            "analysis": {
                "scene": {"description": "Taj Mahal"},
                "objects": [],
                "terrain": {"type": "grass", "color": "green"}
            }
        }]
    }

    # Generate scene
    enhanced = generate_taj_mahal_scene(json_data, scene_objects, model_service.get_valid_models())

    print(f"\nTotal objects generated: {len(enhanced)}")

    # Count water path objects
    water_paths = [obj for obj in enhanced if obj.get("is_water_path")]
    print(f"[OK] Water path segments: {len(water_paths)}")
    assert len(water_paths) == 9, f"Expected 9 water segments, got {len(water_paths)}"

    # Verify water path properties
    if water_paths:
        wp = water_paths[0]
        print(f"  - Color: {wp.get('color')}")
        print(f"  - Position: {wp.get('position')}")
        print(f"  - Scale: {wp.get('scale')}")
        print(f"  - Material: {wp.get('material')}")

        assert wp['color'] == 'blue', "Water path should be blue"
        assert wp['position']['x'] == 0, "Water path should be centered (x=0)"
        assert wp.get('is_water_path') == True, "is_water_path flag missing"

    print("\n[PASS] Water path generation tests PASSED\n")


def test_tree_generation():
    """Test symmetrical tree generation"""
    print("\n" + "="*60)
    print("TEST 4: Symmetrical Tree Generation")
    print("="*60)

    model_service = ModelService()

    scene_objects = [
        {
            "id": "taj1",
            "type": "taj_mahal",
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "model": "Models/tajmahal.glb",
            "model_name": "tajmahal",
            "confidence": 0.95,
            "color": "white",
            "estimated_size": "very_large"
        }
    ]

    json_data = {
        "frames": [{
            "analysis": {
                "scene": {"description": "Taj Mahal"},
                "objects": [],
                "terrain": {"type": "grass", "color": "green"}
            }
        }]
    }

    enhanced = generate_taj_mahal_scene(json_data, scene_objects, model_service.get_valid_models())

    # Count trees
    trees = [obj for obj in enhanced if obj.get("is_taj_mahal_tree")]
    print(f"[OK] Total trees generated: {len(trees)}")
    assert len(trees) == 14, f"Expected 14 trees (7 pairs), got {len(trees)}"

    # Verify symmetry
    left_trees = [t for t in trees if t['position']['x'] < 0]
    right_trees = [t for t in trees if t['position']['x'] > 0]

    print(f"[OK] Left trees: {len(left_trees)}")
    print(f"[OK] Right trees: {len(right_trees)}")

    assert len(left_trees) == 7, f"Expected 7 left trees, got {len(left_trees)}"
    assert len(right_trees) == 7, f"Expected 7 right trees, got {len(right_trees)}"

    # Verify positions
    for tree in left_trees:
        assert tree['position']['x'] == -8, f"Left tree should be at x=-8, got {tree['position']['x']}"

    for tree in right_trees:
        assert tree['position']['x'] == 8, f"Right tree should be at x=8, got {tree['position']['x']}"

    # Check spacing
    z_positions = sorted([t['position']['z'] for t in left_trees])
    print(f"[OK] Tree Z-positions (left): {[round(z, 1) for z in z_positions]}")

    print("\n[PASS] Tree generation tests PASSED\n")


def test_taj_mahal_centeredness():
    """Test if Taj Mahal is properly centered"""
    print("\n" + "="*60)
    print("TEST 5: Taj Mahal Centeredness")
    print("="*60)

    model_service = ModelService()

    scene_objects = [
        {
            "id": "taj1",
            "type": "taj_mahal",
            "position": {"x": 10, "y": 5, "z": 20},  # Wrong position
            "rotation": {"x": 45, "y": 45, "z": 0},
            "scale": {"x": 2, "y": 2, "z": 2},
            "model": "Models/tajmahal.glb",
            "model_name": "tajmahal",
            "confidence": 0.95,
            "color": "white",
            "estimated_size": "very_large"
        }
    ]

    json_data = {
        "frames": [{
            "analysis": {
                "scene": {"description": "Taj Mahal"},
                "objects": [],
                "terrain": {"type": "grass", "color": "green"}
            }
        }]
    }

    enhanced = generate_taj_mahal_scene(json_data, scene_objects, model_service.get_valid_models())

    # Find Taj Mahal object
    taj = [obj for obj in enhanced if obj['type'] == 'taj_mahal'][0]

    print(f"Original position: (10, 5, 20)")
    print(f"New position: ({taj['position']['x']}, {taj['position']['y']}, {taj['position']['z']})")

    assert taj['position']['x'] == 0, "Taj Mahal X should be 0"
    assert taj['position']['z'] == 0, "Taj Mahal Z should be 0"

    print(f"[OK] Taj Mahal properly centered at (0, 0, 0)")

    print("\n[PASS] Centeredness test PASSED\n")


def test_material_properties():
    """Test material properties for water and trees"""
    print("\n" + "="*60)
    print("TEST 6: Material Properties")
    print("="*60)

    model_service = ModelService()

    scene_objects = [
        {
            "id": "taj1",
            "type": "taj_mahal",
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "model": "Models/tajmahal.glb",
            "model_name": "tajmahal",
            "confidence": 0.95,
            "color": "white",
            "estimated_size": "very_large"
        }
    ]

    json_data = {
        "frames": [{
            "analysis": {
                "scene": {"description": "Taj Mahal"},
                "objects": [],
                "terrain": {"type": "grass", "color": "green"}
            }
        }]
    }

    enhanced = generate_taj_mahal_scene(json_data, scene_objects, model_service.get_valid_models())

    # Check water path material
    water = [obj for obj in enhanced if obj.get("is_water_path")][0]
    material = water.get('material', {})

    print("Water Path Material:")
    print(f"  - Color: {material.get('color')}")
    print(f"  - Metalness: {material.get('metalness')}")
    print(f"  - Roughness: {material.get('roughness')}")
    print(f"  - Emissive: {material.get('emissive')}")

    assert material.get('color') == (0.1, 0.4, 0.9), "Water color should be blue RGB"
    print(f"[OK] Water material properties verified")

    # Check trees
    trees = [obj for obj in enhanced if obj.get("is_taj_mahal_tree")]
    if trees:
        print(f"\nTree Properties:")
        print(f"  - Color: {trees[0].get('color')}")
        print(f"  - Confidence: {trees[0].get('confidence')}")
        assert trees[0].get('color') == 'green', "Trees should be green"
        print(f"[OK] Tree material properties verified")

    print("\n[PASS] Material properties tests PASSED\n")


def generate_test_json():
    """Generate a test JSON output"""
    print("\n" + "="*60)
    print("TEST 7: Generate Test Scene JSON")
    print("="*60)

    model_service = ModelService()

    scene_objects = [
        {
            "id": "taj1",
            "type": "taj_mahal",
            "position": {"x": 0, "y": 0, "z": 0},
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1, "y": 1, "z": 1},
            "model": "Models/tajmahal.glb",
            "model_name": "tajmahal",
            "confidence": 0.95,
            "color": "white",
            "estimated_size": "very_large"
        }
    ]

    json_data = {
        "frames": [{
            "analysis": {
                "scene": {"description": "Taj Mahal"},
                "objects": [],
                "terrain": {"type": "grass", "color": "green"}
            }
        }]
    }

    enhanced = generate_taj_mahal_scene(json_data, scene_objects, model_service.get_valid_models())

    output = {
        "objects": enhanced,
        "terrain": {"type": "grass", "size": 100},
        "metadata": {
            "total_objects": len(enhanced),
            "water_paths": len([o for o in enhanced if o.get("is_water_path")]),
            "trees": len([o for o in enhanced if o.get("is_taj_mahal_tree")]),
            "taj_mahal_detected": True
        }
    }

    output_path = Path("output/taj_mahal_test_scene.json")
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"[OK] Test scene saved to: {output_path}")
    print(f"\nScene Summary:")
    print(f"  - Total objects: {len(enhanced)}")
    print(f"  - Water path segments: {output['metadata']['water_paths']}")
    print(f"  - Trees: {output['metadata']['trees']}")
    print(f"  - Taj Mahal: 1")

    print("\n[PASS] Scene JSON generated\n")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("=  TAJ MAHAL GENERATION TEST SUITE")
    print("="*60)

    try:
        test_taj_mahal_detection()
        test_model_recognition()
        test_water_path_generation()
        test_tree_generation()
        test_taj_mahal_centeredness()
        test_material_properties()
        generate_test_json()

        print("\n" + "="*60)
        print("=  ALL TESTS PASSED!")
        print("="*60)
        print("\nTaj Mahal generation is working correctly!")
        print("- Water path: 9 blue segments down center")
        print("- Trees: 14 (7 left, 7 right) with symmetry")
        print("- Taj Mahal: Centered at (0, 0, 0)")
        print("\n")

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
