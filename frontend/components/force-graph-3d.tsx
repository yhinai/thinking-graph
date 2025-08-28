"use client"

import React, { useEffect, useRef, useState, useCallback } from "react"
import { GraphData, GraphNode, GraphLink } from "@/lib/api"

interface ForceGraph3DProps {
  data: GraphData;
  width?: number;
  height?: number;
  onNodeClick?: (node: GraphNode) => void;
  onNodeHover?: (node: GraphNode | null) => void;
}

export function ForceGraph3D({ 
  data, 
  width = 800, 
  height = 600, 
  onNodeClick, 
  onNodeHover 
}: ForceGraph3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const forceGraphRef = useRef<any>(null);
  const [isClient, setIsClient] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Generate node color hue based on label
  const getNodeHue = useCallback((label: string) => {
    if (!label) return 200;
    const hash = label.split('').reduce((a, b) => {
      a = ((a << 5) - a) + b.charCodeAt(0);
      return a & a;
    }, 0);
    return Math.abs(hash) % 360;
  }, []);

  // Get relationship color
  const getRelationshipColor = useCallback((type: string) => {
    const colors: Record<string, string> = {
      'CONNECTED_TO': '#00CED1',
      'RELATED_TO': '#FF6B6B',
      'PART_OF': '#4ECDC4',
      'BELONGS_TO': '#45B7D1',
      'CONTAINS': '#96CEB4',
      'default': '#888888'
    };
    return colors[type] || colors.default;
  }, []);

  useEffect(() => {
    if (!isClient || !containerRef.current) return;

    const loadForceGraph = async () => {
      try {
        setIsLoading(true);
        
        // Dynamic imports to avoid SSR issues
        const ForceGraph3D = (await import('3d-force-graph')).default;
        const THREE = await import('three');
        const SpriteText = (await import('three-spritetext')).default;

        if (!containerRef.current) return;

        // Clear previous content
        containerRef.current.innerHTML = '';

        const Graph = new ForceGraph3D(containerRef.current)
          .backgroundColor('rgba(15, 23, 42, 0.1)')
          .width(width)
          .height(height)
          .nodeLabel('name')
          .nodeAutoColorBy('type')
          .nodeThreeObject((node: any) => {
            // Create a glowing sphere for nodes
            const geometry = new THREE.SphereGeometry(node.val || 5, 16, 16);
            const material = new THREE.MeshLambertMaterial({
              color: `hsl(${getNodeHue(node.name)}, 70%, 60%)`,
              transparent: true,
              opacity: 0.9,
              emissive: `hsl(${getNodeHue(node.name)}, 70%, 30%)`,
              emissiveIntensity: 0.3
            });
            
            const sphere = new THREE.Mesh(geometry, material);
            
            // Add text label above the node
            const textSprite = new SpriteText(node.name || 'Node');
            textSprite.color = `hsl(${getNodeHue(node.name)}, 70%, 80%)`;
            textSprite.textHeight = 4;
            textSprite.position.set(0, 12, 0);
            
            // Create a group to hold both sphere and text
            const group = new THREE.Group();
            group.add(sphere);
            group.add(textSprite);
            
            return group;
          })
          .linkThreeObjectExtend(true)
          .linkThreeObject((link: any) => {
            // Create glowing line with text label
            const material = new THREE.LineBasicMaterial({
              color: getRelationshipColor(link.type || 'default'),
              transparent: true,
              opacity: 0.8,
              linewidth: 2
            });
            
            const geometry = new THREE.BufferGeometry().setFromPoints([
              new THREE.Vector3(0, 0, 0),
              new THREE.Vector3(0, 0, 0)
            ]);
            
            const line = new THREE.Line(geometry, material);
            
            // Add relationship type label
            const linkLabel = new SpriteText(link.type || 'RELATED_TO');
            linkLabel.color = getRelationshipColor(link.type || 'default');
            linkLabel.textHeight = 2;
            linkLabel.backgroundColor = 'rgba(0, 0, 0, 0.5)';
            linkLabel.padding = 2;
            
            // Create group for line and label
            const group = new THREE.Group();
            group.add(line);
            group.add(linkLabel);
            
            return group;
          })
          .linkPositionUpdate((linkObject: any, { start, end }) => {
            // Update line geometry
            const line = linkObject.children[0];
            if (line && line.geometry) {
              const positions = [start.x, start.y, start.z, end.x, end.y, end.z];
              line.geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
            }
            
            // Position label at middle of link
            const label = linkObject.children[1];
            if (label) {
              const middlePos = {
                x: start.x + (end.x - start.x) / 2,
                y: start.y + (end.y - start.y) / 2,
                z: start.z + (end.z - start.z) / 2
              };
              Object.assign(label.position, middlePos);
            }
          })
          .onNodeClick((node: any) => {
            // Focus camera on clicked node with smooth animation
            const distance = 80;
            const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
            
            Graph.cameraPosition(
              { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
              node,
              3000
            );

            if (onNodeClick) {
              onNodeClick(node);
            }
          })
          .onNodeHover((node: any) => {
            if (containerRef.current) {
              containerRef.current.style.cursor = node ? 'pointer' : '';
            }
            if (onNodeHover) {
              onNodeHover(node);
            }
          });

        // Add enhanced lighting
        const scene = Graph.scene();
        
        // Remove existing lights
        scene.children = scene.children.filter((child: any) => !(child instanceof THREE.Light));
        
        // Add ambient light for overall illumination
        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
        scene.add(ambientLight);
        
        // Add directional light for depth
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 100, 100);
        directionalLight.castShadow = true;
        scene.add(directionalLight);
        
        // Add point lights for dynamic lighting
        const pointLight1 = new THREE.PointLight(0x00ced1, 1, 300);
        pointLight1.position.set(50, 50, 50);
        scene.add(pointLight1);
        
        const pointLight2 = new THREE.PointLight(0xff6b6b, 0.8, 200);
        pointLight2.position.set(-50, -50, -50);
        scene.add(pointLight2);
        
        const pointLight3 = new THREE.PointLight(0x4ecdc4, 0.6, 150);
        pointLight3.position.set(0, 100, -100);
        scene.add(pointLight3);
        
        // Add animated lighting effects
        let animationId: number;
        const animateLights = () => {
          const time = Date.now() * 0.001;
          
          // Animate point lights
          pointLight1.intensity = 0.8 + Math.sin(time * 0.7) * 0.3;
          pointLight2.intensity = 0.6 + Math.cos(time * 0.5) * 0.2;
          pointLight3.intensity = 0.4 + Math.sin(time * 0.3) * 0.2;
          
          // Rotate lights around the scene
          pointLight1.position.x = Math.cos(time * 0.2) * 100;
          pointLight1.position.z = Math.sin(time * 0.2) * 100;
          
          pointLight2.position.x = Math.cos(time * 0.3 + Math.PI) * 80;
          pointLight2.position.z = Math.sin(time * 0.3 + Math.PI) * 80;
          
          animationId = requestAnimationFrame(animateLights);
        };
        // Start animation and store ID for cleanup
        animationId = requestAnimationFrame(animateLights);
        (Graph as any).lightAnimationId = animationId;
        
        // Adjust force simulation for better spread
        Graph.d3Force('charge')?.strength(-300);
        Graph.d3Force('link')?.distance(80);

        // Set initial camera position
        Graph.cameraPosition({ x: 0, y: 0, z: 200 });

        forceGraphRef.current = Graph;
        
        // Update graph data
        Graph.graphData(data);

        setIsLoading(false);

      } catch (error) {
        console.error('Error loading 3D force graph:', error);
        setIsLoading(false);
        
        // Fallback to error display
        if (containerRef.current) {
          containerRef.current.innerHTML = `
            <div style="
              width: ${width}px; 
              height: ${height}px; 
              background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              color: white;
              font-family: Arial, sans-serif;
              border-radius: 8px;
              border: 1px solid #444;
            ">
              <div style="text-align: center; padding: 20px;">
                <h3 style="margin: 0 0 10px 0; color: #ff6b6b;">3D Graph Error</h3>
                <p style="margin: 0 0 15px 0; color: #ccc;">Failed to load 3D visualization</p>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin-top: 15px;">
                  <p style="margin: 0; font-size: 14px;">Nodes: ${data.nodes.length}</p>
                  <p style="margin: 5px 0 0 0; font-size: 14px;">Links: ${data.links.length}</p>
                </div>
              </div>
            </div>
          `;
        }
      }
    };

    loadForceGraph();

    // Cleanup function
    return () => {
      if (forceGraphRef.current && (forceGraphRef.current as any).lightAnimationId) {
        cancelAnimationFrame((forceGraphRef.current as any).lightAnimationId);
      }
    };
  }, [data, width, height, isClient, getNodeHue, getRelationshipColor, onNodeClick, onNodeHover]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (forceGraphRef.current && containerRef.current) {
        forceGraphRef.current
          .width(containerRef.current.clientWidth)
          .height(containerRef.current.clientHeight);
      }
    };

    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  if (!isClient) {
    return (
      <div 
        style={{ width, height }} 
        className="flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-lg border border-slate-600"
      >
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          <p>Initializing 3D Graph...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative rounded-lg overflow-hidden border border-slate-600">
      {isLoading && (
        <div 
          style={{ width, height }} 
          className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 text-white z-10"
        >
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p>Loading 3D Visualization...</p>
          </div>
        </div>
      )}
      <div 
        ref={containerRef} 
        style={{ width, height }}
        className="bg-gradient-to-br from-slate-900 to-slate-800"
      />
    </div>
  );
}