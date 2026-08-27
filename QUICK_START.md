# Quick Start Guide

## Launch
```
Double-click: run.bat
```

## First Use (30 seconds)

### Step 1: Create a Project
1. Click **"+ Create Project"** button (top right)
2. Enter project name (e.g., "My First Project")
3. Leave JSON blank (optional)
4. Click **"Create"**

### Step 2: Load the Project
1. Click on your project card
2. App switches to **Dashboard**
3. Your project is now active

### Step 3: Generate a 3D Scene
1. Click **"⌂ Dashboard"** in sidebar (if not there)
2. Click **"Upload Video"** button
3. Select a drone video file (MP4, AVI, etc.)
4. Wait for analysis
5. Click **"Generate Scene"** button
6. Scene will generate in Scene tab (◈)

### Step 4: View Your 3D Model
1. Click **"◈ Scene"** tab in sidebar
2. 3D models display in viewer
3. Use mouse to rotate/zoom
4. Right-panel controls for editing

### Step 5: Save
- **Automatic** - Saves every 30 seconds
- **On close** - Saves when you exit

Done! Your project is saved with all your 3D models.

## Project Tab Features

| Feature | Action |
|---------|--------|
| **Create** | Click "+" button, fill form |
| **Load** | Click any project card |
| **View Code** | Right-click → "Open Code" |
| **Rename** | Right-click → "Rename" |
| **Delete** | Right-click → "Delete" |
| **3D View** | Right-click → "Open 3D View" |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **Enter** | Submit form (create/rename) |
| **Esc** | Close dialog |
| **Right-click** | Project context menu |
| **Mouse wheel** | Zoom in 3D viewer |
| **Left drag** | Rotate 3D view |
| **Middle drag** | Pan 3D view |

## Common Tasks

### Switch Between Projects
1. Click **"📁 Projects"** in sidebar
2. Click another project card
3. Dashboard loads with new project

### Edit 3D Models
1. Go to **"◈ Scene"** tab
2. Click an object in the 3D view
3. Adjust position/rotation/scale in right panel
4. Click **"Apply Transform"**

### View Project Data
1. Right-click project → **"Open Code"**
2. See all JSON data for that project
3. Click **"Save Changes"** to update

### Export Scene
1. Go to **"◈ Scene"** tab
2. Click **"Save"** button
3. Choose location to save (.json)

## Troubleshooting

**Projects not showing?**
- Click "Projects" tab in sidebar
- Projects load from browser storage

**Models not appearing in 3D viewer?**
- Ensure Models directory has .glb/.gltf files
- Check console for errors (F12)
- Try generating a new scene

**Project won't load?**
- Check browser console for errors
- Try refreshing (F5)
- Restart the app

**App won't start?**
- Ensure Python 3.8+ installed
- Check run.py exists
- Try running from Python directly: `python run.py`

## Tips & Tricks

- ✅ **Multiple tabs**: Create multiple tabs for different projects
- ✅ **Quick access**: Projects auto-save, no manual save needed
- ✅ **Browser storage**: Projects survive app restarts
- ✅ **Export import**: Save projects to file for backup
- ✅ **Keyboard navigation**: Use Enter/Esc for faster workflow

---

**Need help?** See SETUP_COMPLETE.md for technical details
