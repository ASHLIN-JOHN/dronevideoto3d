# Testing & Debugging

## Purpose
Debug and test the 3D model generation pipeline, from video analysis to scene rendering.

## Common Issues & Solutions

### Models Floating Above Ground
- Cause: Bounding box min.y too negative, lifting model high
- Fix: Cap Y offset at 50 units max
- Check: model.position.y should be between 0 and 5 for most objects

### Models Overlapping Roads
- Cause: Object positions overlap with road piece coordinates
- Fix: Road at x=28, branches go RIGHT (positive x only); objects placed at x=-22 to x=20
- Rule: Minimum 8-unit gap between road and object zones

### Z-Fighting / Flickering
- Cause: Overlapping planes at same Y level
- Fix: Logarithmic depth buffer + polygon offset on ground plane
- Ground at y=-0.1, road surface at y=-0.05

### Three.js Not Loading
- Cause: CDN blocked in QWebEngine
- Fix: Bundle Three.js r128 locally in lib/ folder

### CORS Errors on Model Loading
- Cause: file:// protocol blocked in Chromium
- Fix: Local HTTP server on port 8765 with CORS headers

### Groq 400 Error
- Cause: response_format not supported for all inputs
- Fix: Retry without response_format, extract JSON from raw text

### Rate Limited (429)
- Cause: Groq free tier limits
- Fix: Wait 30s, retry; 3s sleep between frames

## Debug Commands
```python
# Check if server is running
import requests
r = requests.get("http://127.0.0.1:8765/Models/")
print(r.status_code)

# Verify model file exists
import os
os.path.exists("Models/nature/tree.glb")

# Test Groq API
from groq import Groq
client = Groq()
models = client.models.list()
```

## Testing Checklist
- [ ] App launches without crash
- [ ] Video upload works (mp4/avi/mov)
- [ ] Frame analysis produces valid JSON
- [ ] Generate creates 3D scene
- [ ] Models visible and on ground
- [ ] Terrain covers full area
- [ ] Road doesn't overlap objects
- [ ] View modes switch correctly
- [ ] Transform controls work in Edit mode
- [ ] Tooltip shows in Wireframe mode
