(function() {
    'use strict';

    const STORAGE_KEY = 'drone3d_projects';
    let projects = [];
    let currentContextMenuProject = null;
    let currentViewerTab = null;

    // Initialize
    function init() {
        loadProjects();
        renderProjects();
        setupEventListeners();
    }

    // Load projects from localStorage
    function loadProjects() {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            projects = stored ? JSON.parse(stored) : [];
            console.log('Projects loaded:', projects.length);
        } catch (e) {
            console.error('Failed to load projects:', e);
            projects = [];
        }
    }

    // Save projects to localStorage
    function saveProjects() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
            console.log('Projects saved:', projects.length);
        } catch (e) {
            console.error('Failed to save projects:', e);
            alert('Failed to save project: ' + e.message);
        }
    }

    // Render projects grid
    function renderProjects() {
        const projectsList = document.getElementById('projectsList');
        const emptyState = document.getElementById('emptyState');

        if (projects.length === 0) {
            projectsList.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';
        projectsList.innerHTML = projects.map((project, index) => `
            <div class="project-card" data-index="${index}">
                <div class="project-card-header">
                    <div class="project-card-title">${escapeHtml(project.name)}</div>
                    <div class="project-card-menu"></div>
                </div>
                <div class="project-card-date">${new Date(project.createdAt).toLocaleDateString()} ${new Date(project.createdAt).toLocaleTimeString()}</div>
                <div class="project-card-preview">${getJsonPreview(project.json)}</div>
                <div class="project-card-footer">
                    <span class="project-card-stat">Size: ${(new Blob([project.json]).size / 1024).toFixed(1)}KB</span>
                </div>
            </div>
        `).join('');

        // Add event handlers using event delegation
        attachProjectCardHandlers();
    }

    function attachProjectCardHandlers() {
        // Use event delegation for better performance
        document.querySelectorAll('.project-card').forEach(card => {
            const index = parseInt(card.dataset.index);

            card.addEventListener('click', (e) => {
                if (e.target.closest('.project-card-menu')) return;
                openProjectInViewer(index);
            });

            card.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                showContextMenu(e, index);
            });
        });
    }

    // Setup event listeners
    function setupEventListeners() {
        // Close context menu on click
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.project-card-menu') && !e.target.closest('.context-menu')) {
                document.getElementById('contextMenu').classList.remove('show');
            }
        });

        // Close modals on escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeCreateProjectModal();
                closeRenameModal();
            }
        });

        // Enter key in create modal
        const projectNameInput = document.getElementById('projectName');
        if (projectNameInput) {
            projectNameInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') createProject();
            });
        }

        const newProjectNameInput = document.getElementById('newProjectName');
        if (newProjectNameInput) {
            newProjectNameInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') renameProject();
            });
        }
    }

    // Refresh projects when page becomes visible
    window.refreshProjects = function() {
        loadProjects();
        renderProjects();
    };

    // Update a project in storage from main window
    window.updateProjectInStorage = function(projectJson) {
        try {
            const updated = JSON.parse(projectJson);
            const index = projects.findIndex(p => p.name === updated.name);
            if (index !== -1) {
                projects[index] = updated;
                saveProjects();
                console.log('Project updated in storage:', updated.name);
            }
        } catch (e) {
            console.error('Failed to update project:', e);
        }
    };

    // Show context menu
    window.showContextMenu = function(e, index) {
        e.preventDefault();
        currentContextMenuProject = index;

        const menu = document.getElementById('contextMenu');
        menu.style.left = e.clientX + 'px';
        menu.style.top = e.clientY + 'px';
        menu.classList.add('show');
    };

    // Open project in new viewer tab
    window.openProjectInViewer = function(index) {
        if (index === undefined) index = currentContextMenuProject;
        if (index === null) return;

        const project = projects[index];

        // Load project into main app via PyQt5 bridge
        if (window.qt && window.qt.webChannelTransport) {
            // We're in PyQt5
            if (window.mainWindow && window.mainWindow.load_project_from_browser) {
                window.mainWindow.load_project_from_browser(JSON.stringify(project));
            }
        } else {
            // Fallback: create viewer tab
            const tabName = `viewer-${index}`;
            let existingTab = document.querySelector(`[data-tab="${tabName}"]`);
            if (existingTab) {
                activateTab(tabName);
                return;
            }
            createViewerTab(project, index);
        }

        document.getElementById('contextMenu').classList.remove('show');
    };

    // Open project code in new tab
    window.openProjectCode = function() {
        if (currentContextMenuProject === null) return;

        const project = projects[currentContextMenuProject];
        const tabName = `code-${currentContextMenuProject}`;

        let existingTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (existingTab) {
            activateTab(tabName);
            return;
        }

        createCodeTab(project, currentContextMenuProject);
        document.getElementById('contextMenu').classList.remove('show');
    };

    // Create viewer tab
    function createViewerTab(project, projectIndex) {
        // Load viewer libraries when first viewer tab is created
        if (window.loadViewerLibraries) {
            window.loadViewerLibraries();
        }

        const tabName = `viewer-${projectIndex}`;
        const tabsHeader = document.getElementById('tabsHeader');
        const container = document.querySelector('.container');

        // Create tab button
        const tabButton = document.createElement('button');
        tabButton.className = 'tab-button';
        tabButton.setAttribute('data-tab', tabName);
        tabButton.innerHTML = `
            📊 ${escapeHtml(project.name)}
            <span class="close-tab" onclick="closeTab('${tabName}')" style="opacity: 1;">×</span>
        `;
        tabButton.addEventListener('click', () => activateTab(tabName));
        tabsHeader.appendChild(tabButton);

        // Create tab content
        const tabContent = document.createElement('div');
        tabContent.className = 'tab-content';
        tabContent.setAttribute('id', `tab-${tabName}`);
        tabContent.innerHTML = `
            <div class="viewer-container">
                <div id="viewport-${projectIndex}" style="width: 100%; height: 100%;"></div>
                <div class="viewer-controls">
                    <button class="active" onclick="setViewMode('${tabName}', 'render')">Render</button>
                    <button onclick="setViewMode('${tabName}', 'object')">Object</button>
                    <button onclick="setViewMode('${tabName}', 'edit')">Edit</button>
                    <button onclick="setViewMode('${tabName}', 'wireframe')">Wireframe</button>
                    <button id="shadow-btn-${tabName}" onclick="toggleShadows('${tabName}')">Shadows</button>
                </div>
                <div class="status" id="status-${tabName}"></div>
                <div class="loading" id="loading-${tabName}">Loading model...</div>
                <div class="error" id="error-${tabName}"></div>
                <div class="tooltip" id="tooltip-${tabName}"></div>
            </div>
        `;
        container.appendChild(tabContent);

        activateTab(tabName);

        // Load viewer script for this tab
        setTimeout(() => {
            initializeViewerTab(tabName, project, projectIndex);
        }, 100);
    }

    // Create code editor tab
    function createCodeTab(project, projectIndex) {
        const tabName = `code-${projectIndex}`;
        const tabsHeader = document.getElementById('tabsHeader');
        const container = document.querySelector('.container');

        // Create tab button
        const tabButton = document.createElement('button');
        tabButton.className = 'tab-button';
        tabButton.setAttribute('data-tab', tabName);
        tabButton.innerHTML = `
            {'<code>'}
            <span class="close-tab" onclick="closeTab('${tabName}')" style="opacity: 1;">×</span>
        `;
        tabButton.addEventListener('click', () => activateTab(tabName));
        tabsHeader.appendChild(tabButton);

        // Create tab content
        const tabContent = document.createElement('div');
        tabContent.className = 'tab-content';
        tabContent.setAttribute('id', `tab-${tabName}`);
        tabContent.innerHTML = `
            <div class="code-editor-header">
                <h2>${escapeHtml(project.name)} - Code</h2>
                <div class="code-editor-actions">
                    <button class="btn btn-primary" onclick="saveCodeChanges('${projectIndex}')">Save Changes</button>
                </div>
            </div>
            <div class="code-area">
                <textarea id="code-editor-${projectIndex}">${escapeHtml(project.json)}</textarea>
            </div>
        `;
        container.appendChild(tabContent);

        activateTab(tabName);
    }

    // Initialize viewer tab with Three.js
    function initializeViewerTab(tabName, project, projectIndex) {
        const viewportId = `viewport-${projectIndex}`;
        const viewport = document.getElementById(viewportId);
        if (!viewport) return;

        try {
            const projectData = JSON.parse(project.json);
            // Initialize a simple Three.js scene
            initViewerScene(viewportId, projectData, tabName, projectIndex);
        } catch (e) {
            const errorDiv = document.getElementById(`error-${tabName}`);
            if (errorDiv) {
                errorDiv.textContent = 'Invalid JSON: ' + e.message;
                errorDiv.style.display = 'block';
            }
        }
    }

    // Simple Three.js scene initialization
    function initViewerScene(containerId, data, tabName, projectIndex) {
        const container = document.getElementById(containerId);
        if (!container) return;

        let scene, camera, renderer;

        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0F1117);

        camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 2000);
        camera.position.set(20, 15, 20);

        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);

        // Add lights
        const ambient = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambient);

        const dir = new THREE.DirectionalLight(0xfff4e0, 1.0);
        dir.position.set(30, 40, 20);
        scene.add(dir);

        // Add a box as placeholder
        const geometry = new THREE.BoxGeometry(5, 5, 5);
        const material = new THREE.MeshPhongMaterial({ color: 0x3a6cff });
        const cube = new THREE.Mesh(geometry, material);
        scene.add(cube);

        // Add grid
        const gridHelper = new THREE.GridHelper(100, 10, 0x444444, 0x222222);
        scene.add(gridHelper);

        // Orbit controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.autoRotate = true;
        controls.autoRotateSpeed = 2;

        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }

        animate();

        // Handle window resize
        function onWindowResize() {
            const width = container.clientWidth;
            const height = container.clientHeight;
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        }

        window.addEventListener('resize', onWindowResize);

        // Store renderer for cleanup
        window[`renderer_${tabName}`] = renderer;
    }

    // Activate tab
    function activateTab(tabName) {
        // Remove active class from all tabs
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        // Add active class
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`tab-${tabName}`).classList.add('active');

        // Trigger resize for viewers
        window.dispatchEvent(new Event('resize'));
    }

    // Close tab
    window.closeTab = function(tabName) {
        event.stopPropagation();

        const tabButton = document.querySelector(`[data-tab="${tabName}"]`);
        const tabContent = document.getElementById(`tab-${tabName}`);

        // Clean up renderer first
        const renderer = window[`renderer_${tabName}`];
        if (renderer) {
            renderer.dispose();
            delete window[`renderer_${tabName}`];
        }

        if (tabButton) tabButton.remove();
        if (tabContent) tabContent.remove();

        // Activate first remaining tab
        const firstTabButton = document.querySelector('.tab-button');
        if (firstTabButton) {
            activateTab(firstTabButton.getAttribute('data-tab'));
        }
    };

    // Set view mode
    window.setViewMode = function(tabName, mode) {
        // Update active button
        document.querySelectorAll(`#tab-${tabName} .viewer-controls button`).forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
    };

    // Toggle shadows
    window.toggleShadows = function(tabName) {
        event.target.classList.toggle('active');
    };

    // Open/close modals
    window.openCreateProjectModal = function() {
        document.getElementById('createProjectModal').classList.add('show');
        document.getElementById('projectName').focus();
    };

    window.closeCreateProjectModal = function() {
        document.getElementById('createProjectModal').classList.remove('show');
        document.getElementById('projectName').value = '';
        document.getElementById('projectJson').value = '{}';
    };

    window.openRenameModal = function() {
        if (currentContextMenuProject === null) return;
        document.getElementById('newProjectName').value = projects[currentContextMenuProject].name;
        document.getElementById('renameProjectModal').classList.add('show');
        document.getElementById('newProjectName').focus();
    };

    window.closeRenameModal = function() {
        document.getElementById('renameProjectModal').classList.remove('show');
    };

    // Create project
    window.createProject = function() {
        const name = document.getElementById('projectName').value.trim();
        const json = document.getElementById('projectJson').value.trim();

        if (!name) {
            alert('Please enter a project name');
            return;
        }

        let jsonData = {};
        if (json) {
            try {
                jsonData = JSON.parse(json);
            } catch (e) {
                alert('Invalid JSON: ' + e.message);
                return;
            }
        }

        projects.push({
            name: name,
            json: JSON.stringify(jsonData),
            json_data: jsonData,
            scene_data: null,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        });

        saveProjects();
        renderProjects();
        closeCreateProjectModal();
        console.log('Project created:', name);
    };

    // Rename project
    window.renameProject = function() {
        if (currentContextMenuProject === null) return;

        const newName = document.getElementById('newProjectName').value.trim();
        if (!newName) {
            alert('Please enter a new name');
            return;
        }

        projects[currentContextMenuProject].name = newName;
        projects[currentContextMenuProject].updatedAt = new Date().toISOString();

        saveProjects();
        renderProjects();
        closeRenameModal();
        document.getElementById('contextMenu').classList.remove('show');
    };

    // Delete project
    window.deleteProject = function() {
        if (currentContextMenuProject === null) return;

        if (!confirm('Are you sure you want to delete this project?')) return;

        projects.splice(currentContextMenuProject, 1);
        saveProjects();
        renderProjects();
        document.getElementById('contextMenu').classList.remove('show');
    };

    // Save code changes
    window.saveCodeChanges = function(projectIndex) {
        const editor = document.getElementById(`code-editor-${projectIndex}`);
        if (!editor) return;

        const newJson = editor.value.trim();

        try {
            JSON.parse(newJson);
        } catch (e) {
            alert('Invalid JSON: ' + e.message);
            return;
        }

        if (projectIndex < projects.length) {
            projects[projectIndex].json = newJson;
            projects[projectIndex].updatedAt = new Date().toISOString();
            saveProjects();
            alert('Changes saved!');
        }
    };

    // Utility: Escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Utility: Get JSON preview
    function getJsonPreview(json, lines = 3) {
        try {
            const parsed = JSON.parse(json);
            const str = JSON.stringify(parsed, null, 2);
            return str.split('\n').slice(0, lines).join('\n') + (str.split('\n').length > lines ? '\n...' : '');
        } catch (e) {
            return 'Invalid JSON';
        }
    }

    // Initialize on load
    document.addEventListener('DOMContentLoaded', init);
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
