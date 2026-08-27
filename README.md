# 🚁 Drone 3D Studio

**Professional 3D Model Generation Tool from Drone Footage**

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-Proprietary-blue)

## Overview

Drone 3D Studio is a complete application for analyzing drone footage and generating interactive 3D scenes. Upload a video, analyze it, generate 3D models, and edit them all in one place.

## ✨ Key Features

- **📁 Project Management** - Create, load, save, and organize projects
- **🎬 Video Analysis** - Analyze drone footage automatically
- **🎨 3D Generation** - Generate realistic 3D scenes from video
- **✏️ Edit Objects** - Transform, position, and scale 3D models
- **📊 3D Viewer** - Full-featured Three.js viewer with controls
- **💾 Auto-Save** - Never lose your work (saves every 30 seconds)
- **🔄 Project Sync** - All data persists across sessions

## 🚀 Getting Started

### Installation
```bash
# Requirements
- Python 3.8 or higher
- PyQt5
- PyQtWebEngine
- 500MB free disk space
```

### Launch
```bash
# Simply run
double-click run.bat

# Or from command line
python run.py
```

### First Project (2 minutes)
1. Click **"+ Create Project"**
2. Enter a project name
3. Click **"Create"**
4. Click your project to load it
5. Go to **Video** tab and upload a drone video
6. Wait for analysis
7. Click **"Generate Scene"**
8. View your 3D models!

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - 30-second getting started guide
- **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** - Full technical setup documentation
- **[AUDIT_REPORT.md](AUDIT_REPORT.md)** - Complete system audit and optimization report

## 🏗️ Architecture

### Tabs (Left Sidebar)
1. **📁 Projects** - Project browser and manager
2. **⌂ Dashboard** - Overview and quick access
3. **▶ Video** - Video upload and analysis
4. **▦ Models** - Model browser
5. **◈ Scene** - 3D viewer and editor
6. **{} JSON** - Data viewer
7. **⚙ Settings** - Configuration

### Core Technology Stack
- **Frontend**: Three.js, HTML5, JavaScript
- **Backend**: PyQt5, Python
- **Communication**: WebChannel (PyQt5 ↔ JavaScript)
- **Storage**: localStorage (projects), File system (scenes)
- **Server**: SimpleHTTPServer (localhost:8765)

## 💡 Workflow

```
📁 Create Project
    ↓
⌂ Load in Dashboard
    ↓
▶ Upload Video
    ↓
◈ Generate 3D Scene
    ↓
✏️ Edit Models
    ↓
💾 Auto-Save
    ↓
📁 Project Saved
```

## 🎮 Controls

### 3D Viewer
| Action | Control |
|--------|---------|
| Rotate | Left mouse drag |
| Zoom | Mouse wheel |
| Pan | Middle mouse drag |
| Select | Left click |
| Transform | Inspector panel |

### Keyboard
| Key | Action |
|-----|--------|
| Enter | Submit form |
| Esc | Close dialog |
| Right-click | Context menu |

## 📦 Project Format

Projects are stored in browser localStorage with the following structure:

```json
{
  "name": "Project Name",
  "json_data": { "frames": [...] },
  "scene_data": {
    "objects": [...],
    "terrain": {...}
  },
  "createdAt": "2026-08-27T...",
  "updatedAt": "2026-08-27T..."
}
```

All data is automatically persisted and synchronized.

## ⚙️ Configuration

### Auto-Save
- **Interval**: 30 seconds
- **Trigger**: Automatic
- **On Close**: Saves final state
- **Status**: Always active

### File Locations
- **Projects**: Browser localStorage
- **Scenes**: `./projects/` directory
- **Models**: `./Models/` directory
- **Cache**: `./.cache/` directory

## 🔍 System Requirements

### Minimum
- Windows 7 or later / macOS 10.12+ / Linux (Ubuntu 18.04+)
- Python 3.8+
- 4GB RAM
- 500MB disk space
- WebGL-capable GPU

### Recommended
- Windows 10/11 or macOS 11+ or Linux Ubuntu 20.04+
- Python 3.10+
- 8GB RAM
- 2GB disk space
- Modern GPU (RTX 2060+)

## 🐛 Troubleshooting

### Projects won't load
- Ensure browser storage is enabled
- Try clearing cache and restarting
- Check browser console (F12) for errors

### 3D models not showing
- Verify Models directory contains .glb/.gltf files
- Check GPU drivers are up to date
- Try a different video file

### Video analysis fails
- Use MP4 format (AVI, MOV also supported)
- Ensure video is 1-2 minutes (not too long)
- Check sufficient disk space

### App won't start
- Verify Python 3.8+ installed: `python --version`
- Check PyQt5 installed: `pip list | grep PyQt`
- Try running directly: `python run.py`

## 🔗 File Structure

```
3dmodelgen/
├── app/
│   ├── main_window.py          # Main PyQt5 window
│   ├── theme.py                # UI styling
│   ├── workers.py              # Background workers
│   └── pages/
│       ├── projects_page.py    # Project manager
│       ├── dashboard.py        # Dashboard page
│       ├── scene_page.py       # 3D viewer page
│       ├── video_page.py       # Video upload
│       ├── models_page.py      # Model browser
│       ├── json_page.py        # JSON viewer
│       └── settings_page.py    # Settings
├── app/viewer/web/
│   ├── projects.html           # Project UI
│   ├── projects-manager.js     # Project logic
│   ├── index.html              # Viewer UI
│   ├── viewer.js               # Viewer logic
│   └── lib/                    # Three.js libraries
├── Models/                     # 3D model files
├── output/                     # Generated scenes
├── projects/                   # Saved projects
├── run.py                      # Entry point
├── run.bat                     # Windows launcher
└── settings.json               # Configuration
```

## 📞 Support

For issues or questions:
1. Check documentation files
2. Review system requirements
3. Check application logs
4. Verify file permissions
5. Try a fresh project

## 📝 Version History

### v1.0.0 (Current)
- ✅ Complete project management system
- ✅ Video analysis and 3D generation
- ✅ Full-featured 3D viewer
- ✅ Auto-save functionality
- ✅ PyQt5 + Web integration
- ✅ Production-ready

## ⚖️ License

Proprietary Software - All Rights Reserved

## 👨‍💻 Credits

**Development**: Claude AI Assistant
**Framework**: PyQt5 + Three.js
**Build Date**: 2026-08-27

---

**🎉 Ready to get started? See [QUICK_START.md](QUICK_START.md)**

**Have questions? Check [SETUP_COMPLETE.md](SETUP_COMPLETE.md)**

**Technical details? Read [AUDIT_REPORT.md](AUDIT_REPORT.md)**
# dronevideoto3d
