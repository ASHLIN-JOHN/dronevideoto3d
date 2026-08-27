(function() {
    'use strict';

    let scene, camera, renderer, orbitControls, transformControls;
    let groundPlane;
    const objects = new Map();
    let selectedId = null;
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    const loader = new THREE.GLTFLoader();
    let bridge = null;

    function init() {
        const container = document.getElementById('viewport');

        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0F1117);
        scene.fog = null;

        camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 2000);
        camera.position.set(20, 15, 20);
        camera.lookAt(0, 0, 0);

        renderer = new THREE.WebGLRenderer({ antialias: true, logarithmicDepthBuffer: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.shadowMap.enabled = false;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.outputEncoding = THREE.sRGBEncoding;
        container.appendChild(renderer.domElement);

        setupLights();
        setupGrid();
        setupGroundPlane();
        setupControls();
        setupTransformControls();
        setupEvents();
        initBridge();

        animate();
    }

    function setupLights() {
        const ambient = new THREE.AmbientLight(0xffffff, 0.5);
        scene.add(ambient);

        const hemi = new THREE.HemisphereLight(0x87CEEB, 0x4a7c3f, 0.4);
        scene.add(hemi);

        const dir = new THREE.DirectionalLight(0xfff4e0, 1.0);
        dir.position.set(30, 40, 20);
        dir.castShadow = false;
        dir.shadow.mapSize.width = 2048;
        dir.shadow.mapSize.height = 2048;
        dir.shadow.camera.near = 0.5;
        dir.shadow.camera.far = 150;
        dir.shadow.camera.left = -60;
        dir.shadow.camera.right = 60;
        dir.shadow.camera.top = 60;
        dir.shadow.camera.bottom = -60;
        scene.add(dir);

        const fill = new THREE.DirectionalLight(0x8899bb, 0.3);
        fill.position.set(-20, 10, -10);
        scene.add(fill);
    }

    function setupGrid() {
    }

    function noise2D(x, y) {
        var n = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
        return (n - Math.floor(n)) * 2.0 - 1.0;
    }

    function smoothNoise(x, y) {
        var ix = Math.floor(x), iy = Math.floor(y);
        var fx = x - ix, fy = y - iy;
        fx = fx * fx * (3 - 2 * fx);
        fy = fy * fy * (3 - 2 * fy);
        var a = noise2D(ix, iy);
        var b = noise2D(ix + 1, iy);
        var c = noise2D(ix, iy + 1);
        var d = noise2D(ix + 1, iy + 1);
        return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy;
    }

    function fbm(x, y, octaves) {
        var val = 0, amp = 1, freq = 1, total = 0;
        for (var i = 0; i < octaves; i++) {
            val += smoothNoise(x * freq, y * freq) * amp;
            total += amp;
            amp *= 0.5;
            freq *= 2.0;
        }
        return val / total;
    }

    var terrainGroup = null;

    function setupGroundPlane() {
        var geo = new THREE.PlaneGeometry(300, 300);
        var mat = new THREE.MeshBasicMaterial({ color: 0x1a1d24 });
        groundPlane = new THREE.Mesh(geo, mat);
        groundPlane.rotation.x = -Math.PI / 2;
        groundPlane.position.y = -0.01;
        groundPlane.name = '__ground__';
        scene.add(groundPlane);
    }

    function createTerrain(baseColor, size, terrainType, disaster, groundCondition, severity) {
        if (terrainGroup) {
            scene.remove(terrainGroup);
            terrainGroup.traverse(function(child) {
                if (child.geometry) child.geometry.dispose();
                if (child.material) {
                    if (Array.isArray(child.material)) child.material.forEach(function(m){m.dispose();});
                    else child.material.dispose();
                }
            });
        }
        if (groundPlane && groundPlane.parent === scene) {
            scene.remove(groundPlane);
            if (groundPlane.geometry) groundPlane.geometry.dispose();
            if (groundPlane.material) groundPlane.material.dispose();
        }
        terrainGroup = new THREE.Group();
        terrainGroup.name = '__terrain__';

        var textureLoader = new THREE.TextureLoader();
        var baseUrl = 'http://127.0.0.1:8765/Models/terrains/';
        var fullSize = 500;

        if (disaster === 'flood') {
            createFloodTerrain(terrainGroup, textureLoader, baseUrl, fullSize, severity);
        } else if (disaster === 'drought' || groundCondition === 'cracked' || groundCondition === 'dry') {
            createDroughtTerrain(terrainGroup, textureLoader, baseUrl, fullSize, severity);
        } else if (disaster === 'wildfire' || groundCondition === 'burnt') {
            createBurntTerrain(terrainGroup, textureLoader, baseUrl, fullSize, severity);
        } else if (disaster === 'snow' || groundCondition === 'frozen') {
            createSnowTerrain(terrainGroup, textureLoader, baseUrl, fullSize);
        } else {
            createNormalTerrain(terrainGroup, textureLoader, baseUrl, fullSize, size);
        }

        scene.add(terrainGroup);
    }

    function createNormalTerrain(group, textureLoader, baseUrl, fullSize, size) {
        var grassTex = textureLoader.load(baseUrl + 'Poliigon_GrassPatchyGround_4585/2K/Poliigon_GrassPatchyGround_4585_BaseColor.jpg');
        grassTex.wrapS = THREE.RepeatWrapping;
        grassTex.wrapT = THREE.RepeatWrapping;
        grassTex.repeat.set(40, 40);
        grassTex.anisotropy = 8;

        var grassNorm = textureLoader.load(baseUrl + 'Poliigon_GrassPatchyGround_4585/2K/Poliigon_GrassPatchyGround_4585_Normal.png');
        grassNorm.wrapS = THREE.RepeatWrapping;
        grassNorm.wrapT = THREE.RepeatWrapping;
        grassNorm.repeat.set(40, 40);

        var grassRough = textureLoader.load(baseUrl + 'Poliigon_GrassPatchyGround_4585/2K/Poliigon_GrassPatchyGround_4585_Roughness.jpg');
        grassRough.wrapS = THREE.RepeatWrapping;
        grassRough.wrapT = THREE.RepeatWrapping;
        grassRough.repeat.set(40, 40);

        var geo = new THREE.PlaneGeometry(fullSize, fullSize, 1, 1);
        var mat = new THREE.MeshStandardMaterial({
            map: grassTex,
            normalMap: grassNorm,
            roughnessMap: grassRough,
            roughness: 0.9,
            metalness: 0.0,
            polygonOffset: true,
            polygonOffsetFactor: 1,
            polygonOffsetUnits: 1
        });

        groundPlane = new THREE.Mesh(geo, mat);
        groundPlane.rotation.x = -Math.PI / 2;
        groundPlane.position.y = -0.1;
        groundPlane.receiveShadow = true;
        groundPlane.name = '__ground__';
        group.add(groundPlane);

        var roadTex = textureLoader.load(baseUrl + 'bicycle-trail-road-tile-texture/textures/BicycleTrailRoad_basecolor.jpg');
        roadTex.wrapS = THREE.RepeatWrapping;
        roadTex.wrapT = THREE.RepeatWrapping;
        roadTex.repeat.set(1, 12);

        var roadGeo = new THREE.PlaneGeometry(4, (size || 200) * 0.5, 1, 1);
        var roadMat = new THREE.MeshPhongMaterial({ map: roadTex, shininess: 10 });
        var roadSurface = new THREE.Mesh(roadGeo, roadMat);
        roadSurface.rotation.x = -Math.PI / 2;
        roadSurface.position.set(28, -0.05, 0);
        roadSurface.receiveShadow = true;
        roadSurface.name = '__road_surface__';
        group.add(roadSurface);

        var sandTex = textureLoader.load(baseUrl + 'GroundSand005/GroundSand005_COL_2K.jpg');
        sandTex.wrapS = THREE.RepeatWrapping;
        sandTex.wrapT = THREE.RepeatWrapping;
        sandTex.repeat.set(4, 4);
        var sandGeo = new THREE.PlaneGeometry(25, 25, 1, 1);
        var sandMat = new THREE.MeshPhongMaterial({ map: sandTex, shininess: 3 });
        var sandPatch = new THREE.Mesh(sandGeo, sandMat);
        sandPatch.rotation.x = -Math.PI / 2;
        sandPatch.position.set(-35, -0.07, -30);
        sandPatch.receiveShadow = true;
        group.add(sandPatch);

        var hdrImg = textureLoader.load(baseUrl + 'HdrOutdoorFieldBaseballDayClear001/HdrOutdoorFieldBaseballDayClear001_JPG_8K.JPG', function(tex) {
            tex.mapping = THREE.EquirectangularReflectionMapping;
            scene.background = tex;
        });

        addGrassBlades(group, fullSize);
        addBushes(group, fullSize);
    }

    function createFloodTerrain(group, textureLoader, baseUrl, fullSize, severity) {
        var waterDepth = severity === 'extreme' ? 2.0 : severity === 'severe' ? 1.2 : severity === 'moderate' ? 0.6 : 0.3;

        var mudGeo = new THREE.PlaneGeometry(fullSize, fullSize, 1, 1);
        var mudMat = new THREE.MeshStandardMaterial({
            color: 0x4a3520,
            roughness: 0.95,
            metalness: 0.0,
            polygonOffset: true,
            polygonOffsetFactor: 1,
            polygonOffsetUnits: 1
        });
        var mudPlane = new THREE.Mesh(mudGeo, mudMat);
        mudPlane.rotation.x = -Math.PI / 2;
        mudPlane.position.y = -0.2;
        mudPlane.receiveShadow = true;
        group.add(mudPlane);

        var waterGeo = new THREE.PlaneGeometry(fullSize, fullSize, 64, 64);
        var positions = waterGeo.attributes.position.array;
        for (var i = 0; i < positions.length; i += 3) {
            positions[i + 2] += (Math.random() - 0.5) * 0.05;
        }
        var waterMat = new THREE.MeshStandardMaterial({
            color: 0x2a4a3a,
            roughness: 0.1,
            metalness: 0.3,
            transparent: true,
            opacity: 0.75,
        });
        var waterPlane = new THREE.Mesh(waterGeo, waterMat);
        waterPlane.rotation.x = -Math.PI / 2;
        waterPlane.position.y = waterDepth;
        waterPlane.receiveShadow = true;
        waterPlane.name = '__flood_water__';
        group.add(waterPlane);

        var debrisColors = [0x5c3d1e, 0x3a2812, 0x6b4a2a];
        for (var i = 0; i < 30; i++) {
            var dx = (Math.random() - 0.5) * fullSize * 0.6;
            var dz = (Math.random() - 0.5) * fullSize * 0.6;
            var dGeo = new THREE.BoxGeometry(0.5 + Math.random() * 1.5, 0.1 + Math.random() * 0.3, 0.3 + Math.random());
            var dMat = new THREE.MeshPhongMaterial({ color: debrisColors[i % 3] });
            var debris = new THREE.Mesh(dGeo, dMat);
            debris.position.set(dx, waterDepth + 0.05, dz);
            debris.rotation.y = Math.random() * Math.PI;
            group.add(debris);
        }

        scene.background = new THREE.Color(0x4a5a6a);
        scene.fog = new THREE.Fog(0x6a7a8a, 50, 250);

        groundPlane = mudPlane;
    }

    function createDroughtTerrain(group, textureLoader, baseUrl, fullSize, severity) {
        var sandTex = textureLoader.load(baseUrl + 'GroundSand005/GroundSand005_COL_2K.jpg');
        sandTex.wrapS = THREE.RepeatWrapping;
        sandTex.wrapT = THREE.RepeatWrapping;
        sandTex.repeat.set(30, 30);
        sandTex.anisotropy = 8;

        var sandNorm = textureLoader.load(baseUrl + 'GroundSand005/GroundSand005_NRM_2K.jpg');
        sandNorm.wrapS = THREE.RepeatWrapping;
        sandNorm.wrapT = THREE.RepeatWrapping;
        sandNorm.repeat.set(30, 30);

        var geo = new THREE.PlaneGeometry(fullSize, fullSize, 32, 32);
        var positions = geo.attributes.position.array;
        for (var i = 0; i < positions.length; i += 3) {
            positions[i + 2] += (Math.random() - 0.5) * 0.15;
        }
        var mat = new THREE.MeshStandardMaterial({
            map: sandTex,
            normalMap: sandNorm,
            color: 0xc8a050,
            roughness: 1.0,
            metalness: 0.0,
            polygonOffset: true,
            polygonOffsetFactor: 1,
            polygonOffsetUnits: 1
        });

        groundPlane = new THREE.Mesh(geo, mat);
        groundPlane.rotation.x = -Math.PI / 2;
        groundPlane.position.y = -0.1;
        groundPlane.receiveShadow = true;
        groundPlane.name = '__ground__';
        group.add(groundPlane);

        var crackCount = severity === 'extreme' ? 80 : severity === 'severe' ? 50 : 25;
        for (var i = 0; i < crackCount; i++) {
            var cx = (Math.random() - 0.5) * fullSize * 0.7;
            var cz = (Math.random() - 0.5) * fullSize * 0.7;
            var cLen = 1 + Math.random() * 4;
            var cGeo = new THREE.PlaneGeometry(0.08 + Math.random() * 0.12, cLen);
            var cMat = new THREE.MeshBasicMaterial({ color: 0x2a1a0a, side: THREE.DoubleSide });
            var crack = new THREE.Mesh(cGeo, cMat);
            crack.rotation.x = -Math.PI / 2;
            crack.rotation.z = Math.random() * Math.PI;
            crack.position.set(cx, -0.05, cz);
            group.add(crack);
        }

        var deadTreeCount = 8;
        for (var i = 0; i < deadTreeCount; i++) {
            var tx = (Math.random() - 0.5) * fullSize * 0.4;
            var tz = (Math.random() - 0.5) * fullSize * 0.4;
            var trunk = new THREE.Mesh(
                new THREE.CylinderGeometry(0.08, 0.12, 1.5 + Math.random(), 5),
                new THREE.MeshPhongMaterial({ color: 0x3a2a1a })
            );
            trunk.position.set(tx, 0.7, tz);
            var branches = new THREE.Mesh(
                new THREE.CylinderGeometry(0, 0.04, 0.8, 4),
                new THREE.MeshPhongMaterial({ color: 0x2a1a0a })
            );
            branches.position.set(0, 0.9, 0);
            branches.rotation.z = 0.3 + Math.random() * 0.5;
            trunk.add(branches);
            group.add(trunk);
        }

        scene.background = new THREE.Color(0xd4a050);
        scene.fog = new THREE.Fog(0xd4a050, 80, 300);
    }

    function createBurntTerrain(group, textureLoader, baseUrl, fullSize, severity) {
        var geo = new THREE.PlaneGeometry(fullSize, fullSize, 1, 1);
        var mat = new THREE.MeshStandardMaterial({
            color: 0x1a1008,
            roughness: 1.0,
            metalness: 0.0,
            polygonOffset: true,
            polygonOffsetFactor: 1,
            polygonOffsetUnits: 1
        });

        groundPlane = new THREE.Mesh(geo, mat);
        groundPlane.rotation.x = -Math.PI / 2;
        groundPlane.position.y = -0.1;
        groundPlane.receiveShadow = true;
        groundPlane.name = '__ground__';
        group.add(groundPlane);

        var ashGeo = new THREE.PlaneGeometry(fullSize * 0.8, fullSize * 0.8, 1, 1);
        var ashMat = new THREE.MeshBasicMaterial({ color: 0x333333, transparent: true, opacity: 0.3 });
        var ash = new THREE.Mesh(ashGeo, ashMat);
        ash.rotation.x = -Math.PI / 2;
        ash.position.y = -0.08;
        group.add(ash);

        for (var i = 0; i < 15; i++) {
            var tx = (Math.random() - 0.5) * fullSize * 0.5;
            var tz = (Math.random() - 0.5) * fullSize * 0.5;
            var h = 1 + Math.random() * 2;
            var stump = new THREE.Mesh(
                new THREE.CylinderGeometry(0.1, 0.2, h, 6),
                new THREE.MeshPhongMaterial({ color: 0x1a0a00 })
            );
            stump.position.set(tx, h / 2, tz);
            group.add(stump);
        }

        scene.background = new THREE.Color(0x2a1a0a);
        scene.fog = new THREE.Fog(0x3a2a1a, 30, 150);
    }

    function createSnowTerrain(group, textureLoader, baseUrl, fullSize) {
        var geo = new THREE.PlaneGeometry(fullSize, fullSize, 32, 32);
        var positions = geo.attributes.position.array;
        for (var i = 0; i < positions.length; i += 3) {
            positions[i + 2] += (Math.random() - 0.5) * 0.2;
        }
        var mat = new THREE.MeshStandardMaterial({
            color: 0xf0f4f8,
            roughness: 0.6,
            metalness: 0.0,
            polygonOffset: true,
            polygonOffsetFactor: 1,
            polygonOffsetUnits: 1
        });

        groundPlane = new THREE.Mesh(geo, mat);
        groundPlane.rotation.x = -Math.PI / 2;
        groundPlane.position.y = -0.1;
        groundPlane.receiveShadow = true;
        groundPlane.name = '__ground__';
        group.add(groundPlane);

        for (var i = 0; i < 40; i++) {
            var sx = (Math.random() - 0.5) * fullSize * 0.6;
            var sz = (Math.random() - 0.5) * fullSize * 0.6;
            var snowPile = new THREE.Mesh(
                new THREE.SphereGeometry(0.5 + Math.random() * 1.5, 8, 6),
                new THREE.MeshStandardMaterial({ color: 0xe8ecf0, roughness: 0.8 })
            );
            snowPile.scale.y = 0.3;
            snowPile.position.set(sx, 0.1, sz);
            group.add(snowPile);
        }

        scene.background = new THREE.Color(0xc8d4e0);
        scene.fog = new THREE.Fog(0xd8e0ea, 40, 200);
    }

    function addGrassBlades(group, size) {
        var grassGeo = new THREE.PlaneGeometry(0.15, 0.6);
        grassGeo.translate(0, 0.3, 0);

        var grassColors = [0x2a6b2a, 0x3d7a2e, 0x4a8c3f, 0x557a30, 0x1f5c1f, 0x336b28, 0x4d9435];
        var grassCount = 5000;
        var halfSize = size / 2;

        for (var i = 0; i < grassCount; i++) {
            var px = (noise2D(i * 0.1, i * 0.2) * 0.5 + 0.5) * size - halfSize;
            var pz = (noise2D(i * 0.3, i * 0.15) * 0.5 + 0.5) * size - halfSize;

            if (Math.abs(px - 28) < 5) continue;

            var colorIdx = Math.abs(Math.floor(noise2D(i, i * 2) * 5)) % grassColors.length;
            var mat = new THREE.MeshBasicMaterial({
                color: grassColors[colorIdx],
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.85
            });

            var blade = new THREE.Mesh(grassGeo, mat);
            blade.position.set(px, 0, pz);
            blade.rotation.y = noise2D(i * 7, i * 3) * Math.PI;
            blade.rotation.x = noise2D(i * 5, i * 9) * 0.1;
            var s = 0.5 + noise2D(i * 2, i * 4) * 0.4;
            blade.scale.set(s, s + noise2D(i * 3, i * 6) * 0.3, s);
            group.add(blade);
        }
    }

    function addBushes(group, size) {
        var bushCount = 100;
        var halfSize = size / 2;

        for (var i = 0; i < bushCount; i++) {
            var px = (fbm(i * 0.7, i * 0.3, 2) * 0.5 + 0.5) * size - halfSize;
            var pz = (fbm(i * 0.4, i * 0.8, 2) * 0.5 + 0.5) * size - halfSize;

            if (Math.abs(px - 28) < 6) continue;

            var bushGroup = new THREE.Group();
            var numSpheres = 3 + Math.floor(Math.abs(noise2D(i * 5, i * 7)) * 3);

            for (var j = 0; j < numSpheres; j++) {
                var radius = 0.2 + Math.abs(noise2D(i * 3 + j, j * 5)) * 0.35;
                var sphereGeo = new THREE.SphereGeometry(radius, 6, 5);
                var green = 0.2 + Math.abs(noise2D(i + j, j)) * 0.25;
                var bushMat = new THREE.MeshPhongMaterial({
                    color: new THREE.Color(0.08, green, 0.04),
                    shininess: 3
                });
                var sphere = new THREE.Mesh(sphereGeo, bushMat);
                sphere.position.set(
                    noise2D(i * 2 + j, j * 3) * 0.3,
                    radius * 0.6 + j * 0.08,
                    noise2D(j * 2, i * 3 + j) * 0.3
                );
                sphere.castShadow = true;
                bushGroup.add(sphere);
            }

            bushGroup.position.set(px, 0, pz);
            var bushScale = 0.7 + Math.abs(noise2D(i * 9, i * 2)) * 0.6;
            bushGroup.scale.set(bushScale, bushScale, bushScale);
            group.add(bushGroup);
        }
    }

    function setTerrain(terrainJson) {
        var terrain;
        try { terrain = JSON.parse(terrainJson); } catch(e) { return; }
        var color = terrain.color || '#2d5a27';
        var size = terrain.size || 200;
        var type = terrain.type || 'grass';
        var disaster = terrain.disaster || 'none';
        var groundCondition = terrain.ground_condition || 'normal';
        var severity = terrain.severity || 'none';

        scene.fog = null;
        createTerrain(color, size, type, disaster, groundCondition, severity);
    }

    function setupControls() {
        orbitControls = new THREE.OrbitControls(camera, renderer.domElement);
        orbitControls.enableDamping = true;
        orbitControls.dampingFactor = 0.08;
        orbitControls.screenSpacePanning = true;
        orbitControls.maxPolarAngle = Math.PI * 0.95;
    }

    function setupTransformControls() {
        transformControls = new THREE.TransformControls(camera, renderer.domElement);
        transformControls.setSize(0.8);
        scene.add(transformControls);

        transformControls.addEventListener('dragging-changed', function(event) {
            orbitControls.enabled = !event.value;
        });

        transformControls.addEventListener('objectChange', function() {
            if (selectedId && objects.has(selectedId)) {
                const entry = objects.get(selectedId);
                const obj = entry.object3D;
                const transform = {
                    position: { x: obj.position.x, y: obj.position.y, z: obj.position.z },
                    rotation: {
                        x: THREE.MathUtils.radToDeg(obj.rotation.x),
                        y: THREE.MathUtils.radToDeg(obj.rotation.y),
                        z: THREE.MathUtils.radToDeg(obj.rotation.z)
                    },
                    scale: { x: obj.scale.x, y: obj.scale.y, z: obj.scale.z }
                };
                if (bridge) {
                    bridge.onTransformChanged(selectedId, JSON.stringify(transform));
                }
            }
        });
    }

    function setupEvents() {
        renderer.domElement.addEventListener('click', onMouseClick);
        renderer.domElement.addEventListener('mousemove', onMouseMove);
        window.addEventListener('resize', onResize);
        window.addEventListener('keydown', onKeyDown);
    }

    var hoverRaycaster = new THREE.Raycaster();
    var hoverMouse = new THREE.Vector2();

    function onMouseMove(event) {
        var tooltip = document.getElementById('tooltip');
        if (currentViewMode !== 'wireframe' && currentViewMode !== 'object') {
            tooltip.style.display = 'none';
            return;
        }

        var rect = renderer.domElement.getBoundingClientRect();
        hoverMouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        hoverMouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        hoverRaycaster.setFromCamera(hoverMouse, camera);

        var meshes = [];
        objects.forEach(function(entry) {
            entry.object3D.traverse(function(child) {
                if (child.isMesh) meshes.push(child);
            });
        });

        var hits = hoverRaycaster.intersectObjects(meshes, false);
        if (hits.length > 0) {
            var hitMesh = hits[0].object;
            var foundId = null;
            objects.forEach(function(entry, id) {
                if (isDescendant(entry.object3D, hitMesh)) {
                    foundId = id;
                }
            });

            if (foundId) {
                var entry = objects.get(foundId);
                var meta = entry.metadata || {};
                var label = meta.model_name || meta.type || foundId;
                label = label.replace(/_/g, ' ');
                var typeLine = meta.type ? meta.type.replace(/_/g, ' ') : '';
                var info = label;
                if (typeLine && typeLine !== label) {
                    info += '\nType: ' + typeLine;
                }
                if (meta.confidence) {
                    info += '\nConfidence: ' + Math.round(meta.confidence * 100) + '%';
                }

                tooltip.textContent = info;
                tooltip.style.display = 'block';
                tooltip.style.left = (event.clientX + 12) + 'px';
                tooltip.style.top = (event.clientY - 10) + 'px';
            } else {
                tooltip.style.display = 'none';
            }
        } else {
            tooltip.style.display = 'none';
        }
    }

    function initBridge() {
        function tryConnect() {
            try {
                if (typeof QWebChannel !== 'undefined' && window.qt && window.qt.webChannelTransport) {
                    new QWebChannel(qt.webChannelTransport, function(channel) {
                        bridge = channel.objects.bridge;
                        if (bridge) {
                            bridge.viewerReady();
                        }
                    });
                    return true;
                }
            } catch(e) {
                console.log('Bridge not available:', e);
            }
            return false;
        }
        if (!tryConnect()) {
            setTimeout(function() { tryConnect(); }, 500);
            setTimeout(function() { tryConnect(); }, 1500);
            setTimeout(function() { tryConnect(); }, 3000);
        }
    }

    function onResize() {
        const container = document.getElementById('viewport');
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    }

    function onMouseClick(event) {
        if (currentViewMode !== 'edit' && currentViewMode !== 'render') return;

        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);

        const clickableObjects = [];
        objects.forEach(function(entry) {
            entry.object3D.traverse(function(child) {
                if (child.isMesh) {
                    clickableObjects.push(child);
                }
            });
        });

        const intersects = raycaster.intersectObjects(clickableObjects, false);

        if (intersects.length > 0) {
            let hitObj = intersects[0].object;
            let foundId = null;
            while (hitObj) {
                objects.forEach(function(entry, id) {
                    if (entry.object3D === hitObj || isDescendant(entry.object3D, intersects[0].object)) {
                        foundId = id;
                    }
                });
                if (foundId) break;
                hitObj = hitObj.parent;
            }
            if (!foundId) {
                objects.forEach(function(entry, id) {
                    if (isDescendant(entry.object3D, intersects[0].object)) {
                        foundId = id;
                    }
                });
            }
            if (foundId) {
                selectObject(foundId);
                if (currentViewMode === 'edit') {
                    transformControls.attach(objects.get(foundId).object3D);
                    transformControls.visible = true;
                }
            }
        } else {
            deselectAll();
            if (currentViewMode === 'edit') {
                transformControls.detach();
            }
        }
    }

    function isDescendant(parent, child) {
        let current = child;
        while (current) {
            if (current === parent) return true;
            current = current.parent;
        }
        return false;
    }

    function onKeyDown(event) {
        switch(event.key.toLowerCase()) {
            case 'g':
                setTransformMode('translate');
                break;
            case 'r':
                setTransformMode('rotate');
                break;
            case 's':
                setTransformMode('scale');
                break;
            case 'escape':
                deselectAll();
                break;
        }
    }

    function animate() {
        requestAnimationFrame(animate);
        orbitControls.update();
        renderer.render(scene, camera);
    }

    // === Public API ===

    function loadModel(id, glbUrl, px, py, pz, rx, ry, rz, sx, sy, sz, metadata) {
        const loadingEl = document.getElementById('loading');
        loadingEl.style.display = 'block';

        loader.load(
            glbUrl,
            function(gltf) {
                const model = gltf.scene;
                model.name = id;

                model.scale.set(sx || 1, sy || 1, sz || 1);
                model.rotation.set(
                    THREE.MathUtils.degToRad(rx || 0),
                    THREE.MathUtils.degToRad(ry || 0),
                    THREE.MathUtils.degToRad(rz || 0)
                );
                model.position.set(0, 0, 0);
                model.updateMatrixWorld(true);
                var box = new THREE.Box3().setFromObject(model);
                var offsetY = -box.min.y;
                if (offsetY > 50) offsetY = 0;
                model.position.set(px || 0, offsetY, pz || 0);

                model.traverse(function(child) {
                    if (child.isMesh) {
                        child.castShadow = shadowsEnabled;
                        child.receiveShadow = shadowsEnabled;
                    }
                });

                scene.add(model);

                let meta = {};
                if (metadata) {
                    try { meta = JSON.parse(metadata); } catch(e) { meta = {}; }
                }

                // Apply special materials for water paths and trees
                if (meta.is_water_path && meta.material && meta.material.color) {
                    const waterColor = meta.material.color;
                    const colorHex = rgbToHex(waterColor[0], waterColor[1], waterColor[2]);
                    applyFlatMaterial(model, colorHex);
                } else if (meta.is_taj_mahal_tree) {
                    // Trees get slight color adjustment if needed
                    if (meta.color === "green") {
                        applyFlatMaterial(model, 0x2d5a27);  // Dark green
                    }
                }

                objects.set(id, {
                    object3D: model,
                    metadata: meta,
                    originalEmissive: new Map()
                });

                loadingEl.style.display = 'none';
                updateStatus();

                if (bridge) {
                    bridge.onModelLoaded(id);
                }
            },
            undefined,
            function(error) {
                loadingEl.style.display = 'none';
                console.error('Error loading model:', id, error);
                if (bridge) {
                    bridge.onModelError(id, error.message || 'Load failed');
                }
            }
        );
    }

    function removeModel(id) {
        if (objects.has(id)) {
            const entry = objects.get(id);
            if (selectedId === id) {
                deselectAll();
            }
            scene.remove(entry.object3D);
            entry.object3D.traverse(function(child) {
                if (child.geometry) child.geometry.dispose();
                if (child.material) {
                    if (Array.isArray(child.material)) {
                        child.material.forEach(function(m) { m.dispose(); });
                    } else {
                        child.material.dispose();
                    }
                }
            });
            objects.delete(id);
            updateStatus();
        }
    }

    function clearScene() {
        const ids = Array.from(objects.keys());
        ids.forEach(function(id) { removeModel(id); });
        deselectAll();

        if (terrainGroup) {
            scene.remove(terrainGroup);
            terrainGroup.traverse(function(child) {
                if (child.geometry) child.geometry.dispose();
                if (child.material) {
                    if (Array.isArray(child.material)) child.material.forEach(function(m){m.dispose();});
                    else child.material.dispose();
                }
            });
            terrainGroup = null;
        }

        scene.background = new THREE.Color(0x0F1117);
        scene.fog = null;
    }

    function selectObject(id) {
        if (!objects.has(id)) return;

        deselectAll();
        selectedId = id;
        const entry = objects.get(id);
        const obj = entry.object3D;

        obj.traverse(function(child) {
            if (child.isMesh && child.material) {
                const mats = Array.isArray(child.material) ? child.material : [child.material];
                mats.forEach(function(mat) {
                    if (mat.emissive) {
                        entry.originalEmissive.set(mat.uuid, mat.emissive.clone());
                        mat.emissive.set(0x1a3a6a);
                        mat.emissiveIntensity = 0.3;
                    }
                });
            }
        });

        transformControls.attach(obj);

        const transform = {
            position: { x: obj.position.x, y: obj.position.y, z: obj.position.z },
            rotation: {
                x: THREE.MathUtils.radToDeg(obj.rotation.x),
                y: THREE.MathUtils.radToDeg(obj.rotation.y),
                z: THREE.MathUtils.radToDeg(obj.rotation.z)
            },
            scale: { x: obj.scale.x, y: obj.scale.y, z: obj.scale.z }
        };

        if (bridge) {
            bridge.onObjectSelected(id, JSON.stringify(transform));
        }
    }

    function deselectAll() {
        if (selectedId && objects.has(selectedId)) {
            const entry = objects.get(selectedId);
            entry.object3D.traverse(function(child) {
                if (child.isMesh && child.material) {
                    const mats = Array.isArray(child.material) ? child.material : [child.material];
                    mats.forEach(function(mat) {
                        if (mat.emissive && entry.originalEmissive.has(mat.uuid)) {
                            mat.emissive.copy(entry.originalEmissive.get(mat.uuid));
                            mat.emissiveIntensity = 1.0;
                        }
                    });
                }
            });
            entry.originalEmissive.clear();
        }
        selectedId = null;
        transformControls.detach();

        if (bridge) {
            bridge.onObjectDeselected();
        }
    }

    function setTransformMode(mode) {
        if (mode === 'translate' || mode === 'rotate' || mode === 'scale') {
            transformControls.setMode(mode);
        }
    }

    function updateTransform(id, px, py, pz, rx, ry, rz, sx, sy, sz) {
        if (!objects.has(id)) return;
        const obj = objects.get(id).object3D;
        obj.position.set(px, py, pz);
        obj.rotation.set(
            THREE.MathUtils.degToRad(rx),
            THREE.MathUtils.degToRad(ry),
            THREE.MathUtils.degToRad(rz)
        );
        obj.scale.set(sx, sy, sz);
    }

    function getTransform(id) {
        if (!objects.has(id)) return '{}';
        const obj = objects.get(id).object3D;
        return JSON.stringify({
            position: { x: obj.position.x, y: obj.position.y, z: obj.position.z },
            rotation: {
                x: THREE.MathUtils.radToDeg(obj.rotation.x),
                y: THREE.MathUtils.radToDeg(obj.rotation.y),
                z: THREE.MathUtils.radToDeg(obj.rotation.z)
            },
            scale: { x: obj.scale.x, y: obj.scale.y, z: obj.scale.z }
        });
    }

    function setCameraPreset(preset) {
        const duration = 0.5;
        let targetPos, targetLookAt;

        switch(preset) {
            case 'top':
                targetPos = new THREE.Vector3(0, 50, 0.01);
                targetLookAt = new THREE.Vector3(0, 0, 0);
                break;
            case 'front':
                targetPos = new THREE.Vector3(0, 5, -30);
                targetLookAt = new THREE.Vector3(0, 2, 0);
                break;
            case 'side':
                targetPos = new THREE.Vector3(30, 5, 0);
                targetLookAt = new THREE.Vector3(0, 2, 0);
                break;
            case 'fit_all':
                fitAll();
                return;
            case 'perspective':
            default:
                targetPos = new THREE.Vector3(20, 15, 20);
                targetLookAt = new THREE.Vector3(0, 0, 0);
                break;
        }

        camera.position.copy(targetPos);
        orbitControls.target.copy(targetLookAt);
        orbitControls.update();
    }

    function fitAll() {
        if (objects.size === 0) {
            setCameraPreset('perspective');
            return;
        }

        const box = new THREE.Box3();
        objects.forEach(function(entry) {
            const objBox = new THREE.Box3().setFromObject(entry.object3D);
            box.union(objBox);
        });

        const center = new THREE.Vector3();
        box.getCenter(center);
        const size = new THREE.Vector3();
        box.getSize(size);

        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = camera.fov * (Math.PI / 180);
        let dist = maxDim / (2 * Math.tan(fov / 2));
        dist *= 1.5;

        camera.position.set(center.x + dist * 0.5, center.y + dist * 0.4, center.z + dist * 0.5);
        orbitControls.target.copy(center);
        orbitControls.update();
    }

    function updateStatus() {
        const statusEl = document.getElementById('status');
        statusEl.textContent = 'Objects: ' + objects.size;
    }

    // === View Modes ===
    var currentViewMode = 'render';
    var savedMaterials = new Map();
    var savedBackground = null;

    function setViewMode(mode) {
        currentViewMode = mode;

        var buttons = document.querySelectorAll('#view-modes button');
        buttons.forEach(function(btn) {
            btn.classList.toggle('active', btn.textContent.toLowerCase() === mode);
        });

        if (terrainGroup) {
            terrainGroup.visible = (mode === 'render');
        }

        if (mode === 'render') {
            if (savedBackground !== null) {
                scene.background = savedBackground;
            }
            objects.forEach(function(entry) {
                restoreOriginalMaterials(entry.object3D);
            });
            transformControls.detach();
            transformControls.visible = false;
        } else if (mode === 'object') {
            savedBackground = scene.background;
            scene.background = new THREE.Color(0x1a1d24);
            objects.forEach(function(entry) {
                applyFlatMaterial(entry.object3D, 0x888899);
            });
            transformControls.detach();
            transformControls.visible = false;
        } else if (mode === 'edit') {
            savedBackground = scene.background;
            scene.background = new THREE.Color(0x1a1d24);
            objects.forEach(function(entry) {
                applyFlatMaterial(entry.object3D, 0x5588aa);
            });
            transformControls.visible = true;
            if (selectedId && objects.has(selectedId)) {
                transformControls.attach(objects.get(selectedId).object3D);
            }
        } else if (mode === 'wireframe') {
            savedBackground = scene.background;
            scene.background = new THREE.Color(0x0a0c12);
            objects.forEach(function(entry) {
                applyWireframeMaterial(entry.object3D);
            });
            transformControls.detach();
            transformControls.visible = false;
        }
    }

    function rgbToHex(r, g, b) {
        const toHex = (n) => {
            const hex = Math.round(n * 255).toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        };
        return parseInt('0x' + toHex(r) + toHex(g) + toHex(b), 16);
    }

    function applyFlatMaterial(obj, color) {
        obj.traverse(function(child) {
            if (child.isMesh) {
                if (!savedMaterials.has(child.uuid)) {
                    savedMaterials.set(child.uuid, child.material);
                }
                child.material = new THREE.MeshPhongMaterial({
                    color: color,
                    shininess: 30,
                    specular: 0x222222,
                    flatShading: true
                });
            }
        });
    }

    function applyWireframeMaterial(obj) {
        obj.traverse(function(child) {
            if (child.isMesh) {
                if (!savedMaterials.has(child.uuid)) {
                    savedMaterials.set(child.uuid, child.material);
                }
                child.material = new THREE.MeshBasicMaterial({
                    color: 0x44aaff,
                    wireframe: true
                });
            }
        });
    }

    function restoreOriginalMaterials(obj) {
        obj.traverse(function(child) {
            if (child.isMesh && savedMaterials.has(child.uuid)) {
                child.material = savedMaterials.get(child.uuid);
                savedMaterials.delete(child.uuid);
            }
        });
    }

    // === Shadows Toggle ===
    var shadowsEnabled = false;

    function toggleShadows() {
        shadowsEnabled = !shadowsEnabled;
        renderer.shadowMap.enabled = shadowsEnabled;

        var btn = document.getElementById('shadow-btn');
        if (btn) {
            btn.classList.toggle('active', shadowsEnabled);
        }

        objects.forEach(function(entry) {
            entry.object3D.traverse(function(child) {
                if (child.isMesh) {
                    child.castShadow = shadowsEnabled;
                    child.receiveShadow = shadowsEnabled;
                }
            });
        });

        if (terrainGroup) {
            terrainGroup.traverse(function(child) {
                if (child.isMesh) {
                    child.receiveShadow = shadowsEnabled;
                }
            });
        }

        scene.traverse(function(child) {
            if (child.isLight && child.shadow) {
                child.castShadow = shadowsEnabled;
            }
        });

        renderer.shadowMap.needsUpdate = true;
    }

    // === Expose global API for PyQt5 bridge ===
    window.viewer_loadModel = loadModel;
    window.viewer_removeModel = removeModel;
    window.viewer_clearScene = clearScene;
    window.viewer_selectObject = selectObject;
    window.viewer_deselectAll = deselectAll;
    window.viewer_setTransformMode = setTransformMode;
    window.viewer_updateTransform = updateTransform;
    window.viewer_getTransform = getTransform;
    window.viewer_setCameraPreset = setCameraPreset;
    window.viewer_fitAll = fitAll;
    window.viewer_setTerrain = setTerrain;
    window.viewer_setViewMode = setViewMode;
    window.viewer_toggleShadows = toggleShadows;

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
