# PyQt5 3D Viewer

## Purpose
Desktop 3D scene viewer using PyQt5 + QWebEngineView + Three.js for interactive model visualization.

## Architecture
```
PyQt5 MainWindow
├── QWebEngineView (Three.js renderer)
├── QWebChannel (Python↔JS bridge)
└── Local HTTP Server (port 8765, serves models/textures)
```

## Three.js Setup (r128, bundled locally)
- Logarithmic depth buffer (prevents z-fighting)
- PCFSoftShadowMap for shadows
- sRGB output encoding
- OrbitControls for camera navigation
- TransformControls for object manipulation
- GLTFLoader + DRACOLoader for models

## View Modes
1. **Render**: Full PBR materials, terrain, HDR sky, shadows
2. **Object**: Flat gray material, no terrain, dark background
3. **Edit**: Flat blue material, transform gizmo on click (G=move, R=rotate, S=scale)
4. **Wireframe**: Wire outlines, tooltip on hover showing object info

## Terrain System
- PBR grass texture (Poliigon_GrassPatchyGround_4585) with normal/roughness/AO maps
- 500x500 ground plane with MeshStandardMaterial
- Road surface texture at x=28
- Sand patches for variety
- 5000 procedural grass blades
- 100 procedural bushes
- HDR equirectangular skybox

## Model Loading
- Models served via HTTP (port 8765) to bypass CORS
- Bounding box calculation for ground placement
- Y offset capped at 50 to prevent floating
- Scale based on estimated_size target / model max dimension

## Bridge API (window.viewer_*)
- loadModel, removeModel, clearScene
- selectObject, deselectAll, setTransformMode
- updateTransform, getTransform
- setCameraPreset, fitAll
- setTerrain, setViewMode
