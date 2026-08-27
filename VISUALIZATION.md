# Taj Mahal Scene Visualization

## 3D View - Top Down (Bird's Eye)

```
              NORTH (z = 20)
        
        T5              T5
        |               |
        T4              T4
        |               |
        T3      [WATER]   T3
        |       |||||||||   |
   x=-8 T2 -----+TAJ+----- T2 x=+8
        |       |||||||||   |
        T1      [WATER]   T1
        |               |
        T0              T0
        
              SOUTH (z = -15)
        
Legend:
  T0-T5  = Tree pairs (7 pairs = 14 total)
  [WATER] = Blue water path (9 segments)
  [TAJ]   = Taj Mahal structure
  +++     = Water line at center
```

---

## 3D View - Side (Z-X Plane)

```
        LEFT (-8)         CENTER (0)         RIGHT (+8)
          
        Tree 5            Water 8            Tree 5
          |                 |                  |
        Tree 4            Water 7            Tree 4
          |                 |                  |
        Tree 3            Water 6            Tree 3
          |              [TAJ MAHAL]          |
        Tree 2            Water 5            Tree 2
          |              (central)            |
        Tree 1            Water 4            Tree 1
          |                 |                  |
        Tree 0            Water 3            Tree 0
          |                 |                  |
          
        Water 2 -------- Water 1 -------- Water 0
```

---

## Front View (Camera Perspective)

```
                    FAR BACKGROUND (z = 20)
                    
                       Tree - Water - Tree
                       
                    MIDDLE GROUND (z = 0)
                    
              Tree - Tree    TAJ    Tree - Tree
                       MAHAL
                    
                   FOREGROUND (z = -15)
                   
                       Tree - Water - Tree
```

---

## Color Scheme

### Water Path
```
Color:      RGB(0.1, 0.4, 0.9) - Bright Blue
Material:   Metalness 0.3, Roughness 0.2
Emissive:   RGB(0.0, 0.15, 0.4) - Blue Glow
Opacity:    0.8 (slightly transparent)
Width:      0.25 units (thin line)
Height:     0.03 units (ground level)
```

### Trees
```
Color:      Green RGB(0.2, 0.35, 0.2)
Position:   Left: x = -8
            Right: x = +8
Rotation:   Random 0-360° per tree
Confidence: 0.9
Size:       Large (model: tree.glb)
```

### Taj Mahal
```
Color:      White
Position:   (0, 0, 0) - Center
Rotation:   0°, 0°, 0°
Model:      tajmahal.glb
Scale:      1.0 (original)
Confidence: 0.95
```

---

## Path Positioning

### Water Path Z-Coordinates
```
Segment 0: z = 20.0  (Far)
Segment 1: z = 15.6
Segment 2: z = 11.3
Segment 3: z = 6.9
Segment 4: z = 2.5   (Center)
Segment 5: z = -1.9
Segment 6: z = -6.3
Segment 7: z = -10.6
Segment 8: z = -15.0 (Near)
```

### Tree Pairs Z-Coordinates (with natural variation)
```
Pair 0: z = 15.4  (both sides)
Pair 1: z = 10.2
Pair 2: z = 4.6
Pair 3: z = 0.1
Pair 4: z = -4.9
Pair 5: z = -10.4
Pair 6: z = -15.3
```

---

## Material Preview

### Water (Blue Line)

```
             Side View
             
      Y (height)
      |
      | 0.03 (thin)
      |_____________
  x=0 | blue glow
      |___________
           → (depth)
```

### Tree (Green)

```
             Side View
             
      Y (height)
      |
      | (full model height)
      | model.glb
      | (random rotation)
      |
      |_____________
           → x
      -8 or +8
```

---

## Generation Flow Diagram

```
INPUT: Video with Taj Mahal detected

    ↓ Detection Check ↓
    "taj" or "monument" keyword found?
    
    ↓ YES ↓
    
    Create Taj Mahal object:
    ├─ Position: (0, 0, 0)
    ├─ Scale: 1.0
    └─ Rotation: 0°
    
    ↓
    
    Generate Water Path:
    ├─ 9 segments
    ├─ Z: 20 to -15
    ├─ X: 0 (center line)
    ├─ Color: RGB(0.1, 0.4, 0.9)
    └─ Material: Blue with glow
    
    ↓
    
    Generate Trees:
    ├─ 7 pairs (14 trees)
    ├─ Left: x = -8
    ├─ Right: x = +8
    ├─ Z: 15.4 to -15.3
    ├─ Color: Green
    └─ Rotation: Random
    
    ↓
    
    OUTPUT: Scene JSON (24 objects)
    
    ↓ Viewer Renders ↓
    
    3D Scene displayed with:
    ✓ Blue water path down center
    ✓ Green trees on sides
    ✓ Taj Mahal at focal point
```

---

## Object Count Summary

| Component | Count | Details |
|-----------|-------|---------|
| Taj Mahal | 1 | Central structure, centered |
| Water Path | 9 | Blue segments, z: 20→-15 |
| Trees (Left) | 7 | x=-8, green |
| Trees (Right) | 7 | x=+8, green |
| **TOTAL** | **24** | **Complete scene** |

---

## Spatial Relationships

```
Distances from Taj Mahal (center):

Trees:        8 units (x-axis)
Water Path:   On center line (x = 0)

Tree Spacing: ~5 units (z-axis between pairs)
Water Steps:  ~5.4 units (z-axis between segments)

Scene Bounds:
  X: -12 to +12 (24 units wide)
  Z: -15 to +20 (35 units deep)
  Y: -0.15 to +5 (assuming tree height)
```

---

## Rendering Order

```
1. Ground plane (grass terrain)
2. Water path segments (blue line, back to front)
3. Trees left side (random order with depth sorting)
4. Taj Mahal (center, focal point)
5. Trees right side (random order with depth sorting)
```

---

## Visual Result (ASCII Representation)

```
┌─────────────────────────────────────┐
│                                     │
│  🌳          💧          🌳         │ FAR
│   T          W           T          │
│                                     │
│  🌳          💧          🌳         │
│   T          W           T          │
│                                     │
│  🌳        [TAJ]         🌳         │ CENTER
│   T        MAHAL         T          │
│                                     │
│  🌳          💧          🌳         │
│   T          W           T          │
│                                     │
│  🌳          💧          🌳         │ NEAR
│   T          W           T          │
│                                     │
└─────────────────────────────────────┘
```

---

## Quality Metrics

- **Symmetry**: Perfect (7 trees each side)
- **Centering**: Exact (0, 0, 0)
- **Spacing**: Evenly distributed (natural variation added)
- **Color Accuracy**: RGB values precise
- **Material Definition**: Complete PBR properties
- **Realism**: Trees have random rotation, water has glow effect

---

**Status**: Ready for 3D rendering! 🚀
