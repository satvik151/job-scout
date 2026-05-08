import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

function Particles() {
  const points = useRef<THREE.Points>(null);

  const particlesData = useMemo(() => {
    const positions = new Float32Array(120 * 3);
    for (let i = 0; i < 120; i++) {
      positions[i * 3] = Math.random() * 8 - 4; // x: [-4, 4]
      positions[i * 3 + 1] = Math.random() * 6 - 3; // y: [-3, 3]
      positions[i * 3 + 2] = Math.random() * 2 - 2; // z: [-2, 0]
    }
    return positions;
  }, []);

  useFrame(() => {
    if (points.current) {
      points.current.rotation.y += 0.0008;
      points.current.rotation.x += 0.0003;
    }
  });

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particlesData.length / 3}
          array={particlesData}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={0.03} color="#6366f1" transparent opacity={0.6} />
    </points>
  );
}

function Shape1() {
  const mesh = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (mesh.current) {
      mesh.current.rotation.x += 0.003;
      mesh.current.rotation.y += 0.005;
    }
  });

  return (
    <mesh position={[-2.5, 1, -1]} ref={mesh}>
      <icosahedronGeometry args={[0.6, 0]} />
      <meshBasicMaterial color="#6366f1" wireframe />
    </mesh>
  );
}

function Shape2() {
  const mesh = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (mesh.current) {
      mesh.current.rotation.x -= 0.002;
      mesh.current.rotation.y -= 0.003;
    }
  });

  return (
    <mesh position={[2.5, -1, -1.5]} ref={mesh}>
      <octahedronGeometry args={[0.4]} />
      <meshStandardMaterial color="#8b5cf6" transparent opacity={0.25} />
    </mesh>
  );
}

function Shape3() {
  const mesh = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (mesh.current) {
      mesh.current.rotation.z += 0.008;
      mesh.current.rotation.x += 0.003;
    }
  });

  return (
    <mesh position={[0.5, -2, -0.5]} ref={mesh}>
      <torusGeometry args={[0.3, 0.08, 8, 20]} />
      <meshBasicMaterial color="#6366f1" wireframe />
    </mesh>
  );
}

export function AuthBackground() {
  return (
    <div className="hidden sm:block">
      <Canvas
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          pointerEvents: "none",
        }}
        camera={{ position: [0, 0, 5], fov: 75 }}
        gl={{ alpha: true }}
      >
        <ambientLight intensity={0.4} />
        <pointLight position={[2, 3, 2]} intensity={1.5} color="#6366f1" />

        <Particles />
        <Shape1 />
        <Shape2 />
        <Shape3 />
      </Canvas>
    </div>
  );
}