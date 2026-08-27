# GLB Inspector

## Purpose
Inspect and validate GLB/GLTF model files for compatibility with the Three.js viewer.

## Checks
- File integrity (valid GLTF binary)
- Mesh count and polygon budget
- Material types (PBR/Phong compatibility)
- Texture references and embedded textures
- Bounding box dimensions
- Animation presence
- Draco compression status

## Three.js Compatibility
- Supported: MeshStandardMaterial, MeshPhongMaterial, MeshBasicMaterial
- Texture formats: JPG, PNG (power-of-2 preferred)
- Max recommended polygons: 100k per model for real-time
- GLTFLoader r128 with DRACOLoader support

## Model Placement Rules
- Origin point determines ground contact
- Bounding box min.y used to offset model to ground level
- Scale calculated from target size / max dimension
- Cap Y offset at 50 to prevent floating from bad bounding boxes

## File Structure
```
Models/
├── nature/          # Trees, bushes, rocks
├── vehicles/        # Cars, trucks
├── buildings/       # Houses, structures
├── infrastructure/  # Roads, bridges, turbines
├── props/           # Signs, benches, lamps
└── terrains/        # PBR texture sets
```
