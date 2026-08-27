#!/usr/bin/env python3
"""
Test script to verify 3D scene generation without GUI
"""

import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.road_network import generate_connected_road_network
from app.scene_generator_safe import safe_generate_scene
from app.collision_detector import detect_and_remove_collisions

print("=" * 70)
print("3D SCENE GENERATION TEST")
print("=" * 70)

# Load test data
print("\n[1] Loading data...")
with open("video_analysis.json") as f:
    json_data = json.load(f)

with open("models_metadata.json") as f:
    models_metadata = json.load(f)["models"]

print(f"[OK] Loaded {len(json_data.get('frames', []))} frames")
print(f"[OK] Loaded {len(models_metadata)} models")

# Generate roads
print("\n[2] Generating road network...")
road_info = {"present": True, "directions": ["left", "right"], "type": "access_road"}
road_objects = generate_connected_road_network(road_info, 0, models_metadata)
print(f"[OK] Generated {len(road_objects)} road segments")

# Show first few road positions
if road_objects:
    print("\n   First 5 roads:")
    for road in road_objects[:5]:
        pos = road["position"]
        print(f"   - {road['id']}: x={pos['x']:.2f}, z={pos['z']:.2f}")

# Create basic test objects
print("\n[3] Creating test objects...")
test_objects = road_objects + [
    {
        "id": "tree_001",
        "type": "tree",
        "model": "Models/tree.glb",
        "model_name": "tree",
        "position": {"x": -10, "y": 0, "z": -10},
        "rotation": {"x": 0, "y": 0, "z": 0},
        "scale": {"x": 1, "y": 1, "z": 1},
        "confidence": 0.85,
    },
    {
        "id": "windturbine_001",
        "type": "wind_turbine",
        "model": "Models/windturbine.glb",
        "model_name": "windturbine",
        "position": {"x": 10, "y": 0, "z": 10},
        "rotation": {"x": 0, "y": 0, "z": 0},
        "scale": {"x": 1, "y": 1, "z": 1},
        "confidence": 0.9,
    },
]
print(f"[OK] Created {len(test_objects)} objects (roads + test objects)")

# Generate full scene
print("\n[4] Generating scene with enhancements...")
scene_data = safe_generate_scene(json_data, test_objects, models_metadata, enable_enhancements=True)
print(f"[OK] Scene generated with {len(scene_data['objects'])} objects")

# Apply collision detection
print("\n[5] Applying collision detection...")
scene_data = detect_and_remove_collisions(scene_data)
print(f"[OK] Final scene has {len(scene_data['objects'])} objects")

# Save and verify
print("\n[6] Saving output...")
with open("output/scene.json", "w") as f:
    json.dump(scene_data, f, indent=2)
print("[OK] Saved to output/scene.json")

# Analyze roads
print("\n[7] Road Analysis:")
roads = [o for o in scene_data["objects"] if o.get("type") == "road"]
print(f"   Total roads: {len(roads)}")
if roads:
    z_positions = sorted([r["position"]["z"] for r in roads if r["position"]["x"] == 0])
    print(f"   Main spine Z positions: {z_positions}")
    if len(z_positions) > 1:
        diffs = [z_positions[i+1] - z_positions[i] for i in range(len(z_positions)-1)]
        print(f"   Spacing between segments: {[f'{d:.2f}' for d in diffs]}")

print("\n" + "=" * 70)
print("[COMPLETE] Scene is ready for 3D viewer")
print("=" * 70)
