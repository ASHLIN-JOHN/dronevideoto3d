# Blender Automation

## Purpose
Automate Blender operations for batch processing GLB models, scene composition, and rendering.

## Capabilities
- Batch convert model formats (FBX/OBJ to GLB)
- Generate model thumbnails and metadata
- Compose scenes programmatically
- Apply materials and textures
- Export optimized GLB with Draco compression

## Common Scripts
```python
import bpy

# Clear scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import GLB
bpy.ops.import_scene.gltf(filepath="model.glb")

# Get bounding box dimensions
obj = bpy.context.selected_objects[0]
dims = obj.dimensions  # x, y, z in meters

# Export GLB
bpy.ops.export_scene.gltf(filepath="output.glb", export_format='GLB')
```

## Model Library Management
- Scan Models/ folder for GLB files
- Extract dimensions from bounding boxes
- Generate model_library.json with metadata
- Categories: vehicles, nature, buildings, infrastructure, props
