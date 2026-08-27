# 3D Reconstruction from Video

## Purpose
Convert drone video footage into 3D scene representations using AI vision analysis and model matching.

## Workflow
1. Extract frames from video at regular intervals
2. Send frames to Groq Vision API (model: qwen/qwen3.6-27b) for analysis
3. Parse JSON responses identifying objects, positions, terrain, road info
4. Match detected objects to local GLB model library
5. Generate 3D scene with proper positioning and scaling

## Key Techniques
- Frame extraction: max 512x512, JPEG quality 50 for API efficiency
- Position mapping: Convert 2D frame positions to 3D coordinates using predefined position map
- Object deduplication: Track seen objects to avoid duplicates across frames
- Road network generation: Build connected road from directional info
- Terrain extraction: Identify ground type from analysis

## Position Map
- top_left/center/right: z=-18
- middle_left/center/right: z=0
- bottom_left/center/right: z=18
- Random offset ±2 applied for natural placement

## Constraints
- Groq rate limits: 3s sleep between frames, 30s retry on 429
- Retry logic: 3 attempts per frame, fallback to raw text JSON extraction
- Models folder: E:\3dmodelgen\Models\ (exclude syntheticmodels/)
