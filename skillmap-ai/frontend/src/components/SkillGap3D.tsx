import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

interface SkillGap {
  skill_id: string;
  skill_name: string;
  gap_value: number;
  severity: "critical" | "high" | "moderate" | "low";
  current_level?: number;
  required_level?: number;
}

interface SkillGap3DProps {
  gaps: SkillGap[];
  similarity: number;
  gap_index: number;
}

export const SkillGap3D: React.FC<SkillGap3DProps> = ({ gaps, similarity, gap_index }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<SkillGap | null>(null);
  const [hoveredSkill, setHoveredSkill] = useState<string | null>(null);

  useEffect(() => {
    if (!mountRef.current || gaps.length === 0) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);
    sceneRef.current = scene;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight || 600;

    // Camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(0, 0, 15);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight1.position.set(10, 10, 5);
    scene.add(directionalLight1);

    const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
    directionalLight2.position.set(-10, -10, -5);
    scene.add(directionalLight2);

    // Color mapping for severity
    const severityColors: Record<string, number> = {
      critical: 0xdc3545, // Red
      high: 0xfd7e14,      // Orange
      moderate: 0xffc107,  // Yellow
      low: 0x28a745,       // Green
    };

    // Create skill nodes
    const nodes: THREE.Mesh[] = [];
    const labels: THREE.Sprite[] = [];
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    // Arrange skills in 3D space (spherical distribution)
    gaps.forEach((gap, index) => {
      // Spherical coordinates
      const phi = Math.acos(-1 + (2 * index) / gaps.length);
      const theta = Math.sqrt(gaps.length * Math.PI) * phi;
      const radius = 8;

      const x = radius * Math.cos(theta) * Math.sin(phi);
      const y = radius * Math.sin(theta) * Math.sin(phi);
      const z = radius * Math.cos(phi);

      // Size based on gap value (larger gap = larger sphere)
      const size = 0.3 + (gap.gap_value / 5) * 0.7;
      const geometry = new THREE.SphereGeometry(size, 32, 32);
      const color = severityColors[gap.severity] || 0x999999;
      const material = new THREE.MeshPhongMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.2,
        transparent: true,
        opacity: hoveredSkill === gap.skill_id ? 1.0 : 0.8,
      });

      const sphere = new THREE.Mesh(geometry, material);
      sphere.position.set(x, y, z);
      sphere.userData = { skill: gap };
      scene.add(sphere);
      nodes.push(sphere);

      // Add label sprite
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      if (context) {
        canvas.width = 256;
        canvas.height = 64;
        context.fillStyle = "#000";
        context.font = "Bold 24px Arial";
        context.textAlign = "center";
        context.textBaseline = "middle";
        const text = gap.skill_name.length > 20 
          ? gap.skill_name.substring(0, 20) + "..." 
          : gap.skill_name;
        context.fillText(text, 128, 32);
        
        const texture = new THREE.CanvasTexture(canvas);
        const spriteMaterial = new THREE.SpriteMaterial({ map: texture });
        const sprite = new THREE.Sprite(spriteMaterial);
        sprite.position.set(x, y + size + 0.5, z);
        sprite.scale.set(2, 0.5, 1);
        sprite.userData = { skill: gap };
        scene.add(sprite);
        labels.push(sprite);
      }
    });

    // Add connection lines between nodes (based on similarity)
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0xcccccc, opacity: 0.3, transparent: true });
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const gap1 = gaps[i];
        const gap2 = gaps[j];
        // Connect if both are critical or high severity
        if ((gap1.severity === "critical" || gap1.severity === "high") &&
            (gap2.severity === "critical" || gap2.severity === "high")) {
          const geometry = new THREE.BufferGeometry().setFromPoints([
            nodes[i].position,
            nodes[j].position,
          ]);
          const line = new THREE.Line(geometry, lineMaterial);
          scene.add(line);
        }
      }
    }

    // Mouse interaction - rotate camera around scene
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };
    let cameraAngleX = 0;
    let cameraAngleY = 0;
    const cameraDistance = 15;
    
    // Store for animate function (shared state)
    const cameraState = { angleX: 0, angleY: 0, isDragging: false };

    const onMouseDown = (event: MouseEvent) => {
      isDragging = true;
      cameraState.isDragging = true;
      previousMousePosition = { x: event.clientX, y: event.clientY };
    };

    const onMouseMove = (event: MouseEvent) => {
      if (isDragging) {
        const deltaX = event.clientX - previousMousePosition.x;
        const deltaY = event.clientY - previousMousePosition.y;
        
        cameraAngleY += deltaX * 0.01;
        cameraAngleX += deltaY * 0.01;
        cameraState.angleY = cameraAngleY;
        cameraState.angleX = cameraAngleX;
        
        // Limit vertical rotation
        cameraAngleX = Math.max(-Math.PI / 2, Math.min(Math.PI / 2, cameraAngleX));
        cameraState.angleX = cameraAngleX;
        
        // Update camera position (orbit around center)
        camera.position.x = Math.sin(cameraAngleY) * Math.cos(cameraAngleX) * cameraDistance;
        camera.position.y = Math.sin(cameraAngleX) * cameraDistance;
        camera.position.z = Math.cos(cameraAngleY) * Math.cos(cameraAngleX) * cameraDistance;
        camera.lookAt(0, 0, 0);
        
        previousMousePosition = { x: event.clientX, y: event.clientY };
      } else {
        // Hover detection
        mouse.x = (event.clientX / width) * 2 - 1;
        mouse.y = -(event.clientY / height) * 2 + 1;
        
        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(nodes);
        
        if (intersects.length > 0) {
          const intersected = intersects[0].object as THREE.Mesh;
          const skill = intersected.userData.skill as SkillGap;
          setHoveredSkill(skill.skill_id);
          
          // Highlight
          (intersected.material as THREE.MeshPhongMaterial).emissiveIntensity = 0.5;
        } else {
          setHoveredSkill(null);
          nodes.forEach((node) => {
            (node.material as THREE.MeshPhongMaterial).emissiveIntensity = 0.2;
          });
        }
      }
    };

    const onMouseUp = () => {
      isDragging = false;
      cameraState.isDragging = false;
    };

    const onMouseClick = (event: MouseEvent) => {
      mouse.x = (event.clientX / width) * 2 - 1;
      mouse.y = -(event.clientY / height) * 2 + 1;
      
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(nodes);
      
      if (intersects.length > 0) {
        const skill = intersects[0].object.userData.skill as SkillGap;
        setSelectedSkill(skill);
      }
    };

    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      const zoomSpeed = 0.1;
      const zoom = event.deltaY > 0 ? 1 + zoomSpeed : 1 - zoomSpeed;
      camera.position.multiplyScalar(zoom);
      camera.position.clampLength(5, 30);
    };

    renderer.domElement.addEventListener("mousedown", onMouseDown);
    renderer.domElement.addEventListener("mousemove", onMouseMove);
    renderer.domElement.addEventListener("mouseup", onMouseUp);
    renderer.domElement.addEventListener("click", onMouseClick);
    renderer.domElement.addEventListener("wheel", onWheel);

    // Auto-rotation (only when not dragging)
    let autoRotate = true;
    const animate = () => {
      if (autoRotate && !cameraState.isDragging) {
        cameraState.angleY += 0.005;
        camera.position.x = Math.sin(cameraState.angleY) * Math.cos(cameraState.angleX) * cameraDistance;
        camera.position.y = Math.sin(cameraState.angleX) * cameraDistance;
        camera.position.z = Math.cos(cameraState.angleY) * Math.cos(cameraState.angleX) * cameraDistance;
        camera.lookAt(0, 0, 0);
      }
      
      // Animate nodes (subtle rotation)
      nodes.forEach((node) => {
        node.rotation.x += 0.005;
        node.rotation.y += 0.005;
      });
      
      renderer.render(scene, camera);
      animationFrameRef.current = requestAnimationFrame(animate);
    };
    animate();

    // Cleanup
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      renderer.domElement.removeEventListener("mousedown", onMouseDown);
      renderer.domElement.removeEventListener("mousemove", onMouseMove);
      renderer.domElement.removeEventListener("mouseup", onMouseUp);
      renderer.domElement.removeEventListener("click", onMouseClick);
      renderer.domElement.removeEventListener("wheel", onWheel);
      
      if (mountRef.current && renderer.domElement.parentNode) {
        mountRef.current.removeChild(renderer.domElement);
      }
      
      // Dispose geometries and materials
      nodes.forEach((node) => {
        node.geometry.dispose();
        (node.material as THREE.Material).dispose();
      });
      labels.forEach((label) => {
        if (label.material.map) label.material.map.dispose();
        label.material.dispose();
      });
      renderer.dispose();
    };
  }, [gaps, hoveredSkill]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (mountRef.current && cameraRef.current && rendererRef.current) {
        const width = mountRef.current.clientWidth;
        const height = mountRef.current.clientHeight || 600;
        cameraRef.current.aspect = width / height;
        cameraRef.current.updateProjectionMatrix();
        rendererRef.current.setSize(width, height);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <div style={{ position: "relative", width: "100%", height: "600px" }}>
      <div
        ref={mountRef}
        style={{
          width: "100%",
          height: "100%",
          border: "2px solid #ddd",
          borderRadius: "8px",
          background: "#f0f0f0",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: "10px",
          left: "10px",
          background: "rgba(255, 255, 255, 0.9)",
          padding: "1rem",
          borderRadius: "8px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          maxWidth: "300px",
        }}
      >
        <h4 style={{ margin: "0 0 0.5rem 0", fontSize: "1rem" }}>3D Skill Gap Visualization</h4>
        <p style={{ margin: "0.25rem 0", fontSize: "0.85rem", color: "#666" }}>
          <strong>🖱️ Drag:</strong> Rotate view
        </p>
        <p style={{ margin: "0.25rem 0", fontSize: "0.85rem", color: "#666" }}>
          <strong>🔍 Scroll:</strong> Zoom in/out
        </p>
        <p style={{ margin: "0.25rem 0", fontSize: "0.85rem", color: "#666" }}>
          <strong>👆 Click:</strong> Select skill
        </p>
        <div style={{ marginTop: "0.5rem", paddingTop: "0.5rem", borderTop: "1px solid #ddd" }}>
          <p style={{ margin: "0.25rem 0", fontSize: "0.85rem" }}>
            <span style={{ color: "#dc3545" }}>●</span> Critical
          </p>
          <p style={{ margin: "0.25rem 0", fontSize: "0.85rem" }}>
            <span style={{ color: "#fd7e14" }}>●</span> High
          </p>
          <p style={{ margin: "0.25rem 0", fontSize: "0.85rem" }}>
            <span style={{ color: "#ffc107" }}>●</span> Moderate
          </p>
          <p style={{ margin: "0.25rem 0", fontSize: "0.85rem" }}>
            <span style={{ color: "#28a745" }}>●</span> Low
          </p>
        </div>
      </div>
      {selectedSkill && (
        <div
          style={{
            position: "absolute",
            bottom: "10px",
            left: "10px",
            right: "10px",
            background: "rgba(255, 255, 255, 0.95)",
            padding: "1rem",
            borderRadius: "8px",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h4 style={{ margin: "0 0 0.5rem 0" }}>{selectedSkill.skill_name}</h4>
              <p style={{ margin: "0.25rem 0", fontSize: "0.9rem" }}>
                <strong>Gap Value:</strong> {selectedSkill.gap_value.toFixed(2)}
              </p>
              {selectedSkill.current_level !== undefined && (
                <p style={{ margin: "0.25rem 0", fontSize: "0.9rem" }}>
                  <strong>Current Level:</strong> {selectedSkill.current_level.toFixed(1)}/5.0
                </p>
              )}
              {selectedSkill.required_level !== undefined && (
                <p style={{ margin: "0.25rem 0", fontSize: "0.9rem" }}>
                  <strong>Required Level:</strong> {selectedSkill.required_level.toFixed(1)}/5.0
                </p>
              )}
            </div>
            <button
              onClick={() => setSelectedSkill(null)}
              style={{
                padding: "0.5rem 1rem",
                background: "#dc3545",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              ✕ Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

