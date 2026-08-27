"""
Groq-Powered Road Network Planning
Uses Groq to analyze video data and design optimal road layouts
"""

import json
from typing import Dict, List, Optional


def plan_road_network_with_groq(
    json_data: Dict,
    models_metadata: List[Dict],
    api_key: str
) -> Dict:
    """
    Use Groq to analyze video and plan optimal road network
    Returns: {segments: [...], layout_description: "..."}
    """

    try:
        from groq import Groq
    except ImportError:
        print("[GROQ] Library not available, using default layout")
        return None

    # Initialize Groq client
    client = Groq(api_key=api_key)

    # Extract road data from video analysis
    frames = json_data.get("frames", [])
    road_descriptions = []

    for frame in frames:
        analysis = frame.get("analysis", {})
        road = analysis.get("road", {})
        if road.get("present"):
            road_descriptions.append({
                "direction": road.get("direction_in_image", ""),
                "type": road.get("type", ""),
                "width": road.get("width", "")
            })

    # Get available road models
    road_models_info = {}
    for model in models_metadata:
        if not model.get("valid"):
            continue
        name = model["name"].lower()
        if "road" in name:
            dims = model.get("dimensions", {})
            road_models_info[name] = {
                "z_length": dims.get("z", 0),
                "x_width": dims.get("x", 0)
            }

    # Create Groq prompt
    prompt = f"""
Analyze this road network design requirement and provide optimal positioning:

VIDEO ANALYSIS DATA:
{json.dumps(road_descriptions[:2], indent=2)}

AVAILABLE ROAD MODELS:
{json.dumps(road_models_info, indent=2)}

SCENE CONSTRAINTS:
- Scene size: 100x100 units
- Main spine should be vertical (Z-axis)
- Objects need to avoid roads (5 units buffer)

TASK:
Design a connected road network with these requirements:
1. Main vertical spine of straight roads
2. If video shows "left" or "curving left": add LEFT turn branch
3. If video shows "right" or "curving right": add RIGHT turn branch
4. All pieces must connect end-to-end
5. Return exact Z positions for each segment

RESPONSE FORMAT (JSON ONLY):
{{
  "main_spine": [
    {{"z": value, "type": "straight"}},
    ...
  ],
  "left_branch": {{"z": value, "x": value, "type": "left_turn"}} or null,
  "right_branch": {{"z": value, "x": value, "type": "right_turn"}} or null,
  "explanation": "brief description of layout"
}}

Return ONLY valid JSON, no markdown or extra text.
"""

    print("[GROQ] Sending road planning request...")

    try:
        message = client.messages.create(
            model="mixtral-8x7b-32768",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()
        print("[GROQ] Received response")

        # Parse JSON response
        layout = json.loads(response_text)
        print(f"[GROQ] Layout: {layout.get('explanation', 'N/A')}")

        return layout

    except json.JSONDecodeError as e:
        print(f"[GROQ] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[GROQ] Error: {e}")
        return None


def implement_groq_layout(layout: Dict, start_idx: int, models_metadata: List[Dict]) -> List[Dict]:
    """
    Implement the road layout designed by Groq
    """

    if not layout:
        return []

    road_objects = []
    straight_model = _find_model("straightroad", models_metadata)
    left_turn_model = _find_model("leftturnroad", models_metadata)
    right_turn_model = _find_model("rightturnroad", models_metadata)

    obj_idx = start_idx

    # Add main spine
    print("[LAYOUT] Main spine:")
    main_spine = layout.get("main_spine", [])
    for segment in main_spine:
        obj_idx += 1
        z_pos = segment.get("z", 0)
        seg_type = segment.get("type", "straight")

        if seg_type == "straight" and straight_model:
            road_obj = {
                "id": f"road_{obj_idx:03d}",
                "type": "road",
                "model": straight_model["file"],
                "model_name": straight_model["name"],
                "position": {"x": 0.0, "y": 0.0, "z": z_pos},
                "rotation": {"x": 0, "y": 0, "z": 0},
                "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
                "confidence": 0.95,
                "color": "gray",
                "estimated_size": "large",
            }
            road_objects.append(road_obj)
            print(f"  z={z_pos:.2f}")

    # Add left branch
    left_branch = layout.get("left_branch")
    if left_branch and left_turn_model:
        print("[LAYOUT] Left branch:")
        obj_idx += 1
        road_obj = {
            "id": f"road_{obj_idx:03d}",
            "type": "road",
            "model": left_turn_model["file"],
            "model_name": left_turn_model["name"],
            "position": {
                "x": left_branch.get("x", -4.37),
                "y": 0.0,
                "z": left_branch.get("z", 0)
            },
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
            "confidence": 0.95,
            "color": "gray",
            "estimated_size": "large",
        }
        road_objects.append(road_obj)
        print(f"  x={left_branch.get('x', -4.37):.2f}, z={left_branch.get('z', 0):.2f}")

    # Add right branch
    right_branch = layout.get("right_branch")
    if right_branch and right_turn_model:
        print("[LAYOUT] Right branch:")
        obj_idx += 1
        road_obj = {
            "id": f"road_{obj_idx:03d}",
            "type": "road",
            "model": right_turn_model["file"],
            "model_name": right_turn_model["name"],
            "position": {
                "x": right_branch.get("x", 4.37),
                "y": 0.0,
                "z": right_branch.get("z", 0)
            },
            "rotation": {"x": 0, "y": 0, "z": 0},
            "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
            "confidence": 0.95,
            "color": "gray",
            "estimated_size": "large",
        }
        road_objects.append(road_obj)
        print(f"  x={right_branch.get('x', 4.37):.2f}, z={right_branch.get('z', 0):.2f}")

    return road_objects


def _find_model(name: str, models_metadata: List[Dict]) -> Optional[Dict]:
    """Find a model by name"""
    for model in models_metadata:
        if model.get("valid") and model["name"].lower() == name.lower():
            return model
    return None
