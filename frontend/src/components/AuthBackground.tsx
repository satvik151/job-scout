import { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import * as THREE from "three";

type Particle = {
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
};

function ParticleNetwork() {
  const particles = useMemo<Particle[]>(
    () =>
      Array.from({ length: 80 }, () => ({
        x: Math.random() * 10 - 5,
        y: Math.random() * 8 - 4,
        z: Math.random() * 2 - 2,
        vx: (Math.random() - 0.5) * 0.003,
        vy: (Math.random() - 0.5) * 0.003,
        vz: (Math.random() - 0.5) * 0.003,
      })),
    [],
  );

  const positions = useMemo(() => new Float32Array(80 * 3), []);
  const linePositions = useMemo(() => new Float32Array(80 * 79 * 3), []);

  const pointsGeometry = useMemo(() => {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return geometry;
  }, [positions]);

  const linesGeometry = useMemo(() => {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(linePositions, 3));
    return geometry;
  }, [linePositions]);

  useEffect(() => {
    return () => {
      pointsGeometry.dispose();
      linesGeometry.dispose();
    };
  }, [linesGeometry, pointsGeometry]);

  useFrame(() => {
    let lineIndex = 0;

    for (let i = 0; i < particles.length; i++) {
      const particle = particles[i];

      particle.x += particle.vx;
      particle.y += particle.vy;
      particle.z += particle.vz;

      if (particle.x > 5) particle.x = -5;
      if (particle.x < -5) particle.x = 5;
      if (particle.y > 4) particle.y = -4;
      if (particle.y < -4) particle.y = 4;

      positions[i * 3] = particle.x;
      positions[i * 3 + 1] = particle.y;
      positions[i * 3 + 2] = particle.z;
    }

    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const a = particles[i];
        const b = particles[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const dz = a.z - b.z;
        const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);

        if (distance < 1.8) {
          linePositions[lineIndex++] = a.x;
          linePositions[lineIndex++] = a.y;
          linePositions[lineIndex++] = a.z;
          linePositions[lineIndex++] = b.x;
          linePositions[lineIndex++] = b.y;
          linePositions[lineIndex++] = b.z;
        }
      }
    }

    pointsGeometry.attributes.position.needsUpdate = true;
    linesGeometry.attributes.position.needsUpdate = true;
    pointsGeometry.setDrawRange(0, particles.length);
    linesGeometry.setDrawRange(0, lineIndex / 3);
  });

  return (
    <group>
      <points geometry={pointsGeometry}>
        <pointsMaterial size={0.04} color="#6366f1" transparent opacity={0.7} />
      </points>
      <lineSegments geometry={linesGeometry}>
        <lineBasicMaterial color="#6366f1" transparent opacity={0.15} />
      </lineSegments>
    </group>
  );
}

function FloatingIcosahedron() {
  const mesh = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!mesh.current) return;
    mesh.current.rotation.x += 0.004;
    mesh.current.rotation.y += 0.006;
    mesh.current.position.y = 1.2 + Math.sin(clock.elapsedTime * 0.8) * 0.15;
  });

  return (
    <mesh position={[-2.8, 1.2, -1]} ref={mesh}>
      <icosahedronGeometry args={[0.7, 1]} />
      <meshBasicMaterial color="#6366f1" wireframe />
    </mesh>
  );
}

function FloatingOctahedron() {
  const mesh = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!mesh.current) return;
    mesh.current.rotation.x -= 0.003;
    mesh.current.rotation.y -= 0.004;
    mesh.current.position.y = -0.8 + Math.sin(clock.elapsedTime * 0.6 + 2) * 0.12;
  });

  return (
    <mesh position={[2.8, -0.8, -1.5]} ref={mesh}>
      <octahedronGeometry args={[0.5]} />
      <meshStandardMaterial
        color="#8b5cf6"
        emissive="#6366f1"
        emissiveIntensity={0.4}
        transparent
        opacity={0.5}
        roughness={0.1}
        metalness={0.8}
      />
    </mesh>
  );
}

function FloatingTorusKnot() {
  const mesh = useRef<THREE.Mesh>(null);

  useFrame(() => {
    if (!mesh.current) return;
    mesh.current.rotation.x += 0.008;
    mesh.current.rotation.y += 0.005;
    mesh.current.rotation.z += 0.003;
  });

  return (
    <mesh position={[0.8, 2.2, -2]} ref={mesh}>
      <torusKnotGeometry args={[0.25, 0.08, 80, 12]} />
      <meshStandardMaterial
        color="#6366f1"
        emissive="#6366f1"
        emissiveIntensity={0.3}
        roughness={0.2}
        metalness={0.6}
      />
    </mesh>
  );
}

function FloatingTorus() {
  const mesh = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!mesh.current) return;
    mesh.current.rotation.z += 0.01;
    mesh.current.rotation.x += 0.004;
    mesh.current.position.y = -2 + Math.sin(clock.elapsedTime * 1.1 + 4) * 0.1;
  });

  return (
    <mesh position={[-2, -2, -0.5]} ref={mesh}>
      <torusGeometry args={[0.3, 0.1, 8, 24]} />
      <meshBasicMaterial color="#4f46e5" wireframe />
    </mesh>
  );
}

function Scene() {
  const sceneRef = useRef<THREE.Group>(null);
  const mouse = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      mouse.current.x = (event.clientX / window.innerWidth - 0.5) * 2;
      mouse.current.y = -((event.clientY / window.innerHeight - 0.5) * 2);
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useFrame(() => {
    if (!sceneRef.current) return;
    sceneRef.current.rotation.y += (mouse.current.x * 0.08 - sceneRef.current.rotation.y) * 0.05;
    sceneRef.current.rotation.x += (mouse.current.y * 0.05 - sceneRef.current.rotation.x) * 0.05;
  });

  return (
    <group ref={sceneRef}>
      <fog attach="fog" args={["#0a0a0a", 6, 14]} />
      <ambientLight intensity={0.3} />
      <pointLight position={[3, 4, 3]} intensity={2} color="#6366f1" />
      <pointLight position={[-3, -2, 2]} intensity={1} color="#8b5cf6" />

      <ParticleNetwork />
      <FloatingIcosahedron />
      <FloatingOctahedron />
      <FloatingTorusKnot />
      <FloatingTorus />

      <EffectComposer>
        <Bloom
          luminanceThreshold={0.3}
          luminanceSmoothing={0.9}
          intensity={0.6}
          mipmapBlur
        />
      </EffectComposer>
    </group>
  );
}

export function AuthBackground() {
  return (
    <div className="hidden sm:block">
      <Suspense fallback={null}>
        <Canvas
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 0,
            pointerEvents: "none",
          }}
          camera={{ position: [0, 0, 6], fov: 70 }}
          gl={{ alpha: true, antialias: true }}
          dpr={[1, 2]}
          frameloop="always"
          performance={{ min: 0.5 }}
        >
          <Scene />
        </Canvas>
      </Suspense>
    </div>
  );
}