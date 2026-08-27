# Python Architecture

## Purpose
Design patterns and structure for this PyQt5 desktop application.

## Project Structure
```
E:\3dmodelgen\
├── run.py                 # Entry point, HTTP server, Qt app launch
├── .env                   # GROQ_API_KEY (never commit)
├── app/
│   ├── main_window.py     # MainWindow with page navigation
│   ├── workers.py         # QThread workers (VideoAnalysis, SceneGeneration)
│   ├── pages/
│   │   └── scene_page.py  # 3D viewer page with QWebEngineView
│   └── viewer/
│       └── web/
│           ├── index.html  # Viewer HTML shell
│           ├── viewer.js   # Three.js scene logic
│           ├── qwebchannel.js
│           └── lib/        # Three.js r128 (local bundle)
├── Models/                # GLB models + terrain textures
└── video_analysis.json    # Cached analysis results
```

## Threading Model
- Main thread: UI (PyQt5 event loop)
- Worker threads: VideoAnalysisWorker, SceneGenerationWorker (QThread)
- HTTP server: Separate thread (port 8765)
- Signals/slots for thread-safe communication

## Key Patterns
- Workers emit progress/finished/error signals
- Scene data flows: Worker → JSON → scene_page → JavaScript
- Fallback: load video_analysis.json if no live analysis
- QWebChannel bridge for bidirectional Python↔JS communication

## Security Rules
- GROQ_API_KEY: .env only, never print/log/save to JSON
- No syntheticmodels/ folder access
- Local HTTP server bound to 127.0.0.1 only
- No external URL generation from user data
