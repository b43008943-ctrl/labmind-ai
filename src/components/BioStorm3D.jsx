import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float } from '@react-three/drei';
import * as THREE from 'three';

/* ═══════════════════════════════════════════════════════
   ERYTHROCYTE — Grand-scale red blood cell (biconcave)
   ═══════════════════════════════════════════════════════ */
const Erythrocyte = ({ position, scale = 1 }) => {
    const meshRef = useRef();
    useFrame((state) => {
        if (meshRef.current) {
            meshRef.current.rotation.x += 0.002;
            meshRef.current.rotation.z += 0.001;
        }
    });
    return (
        <Float speed={0.6} rotationIntensity={0.4} floatIntensity={0.8} position={position}>
            <group ref={meshRef} scale={scale}>
                {/* Outer torus ring */}
                <mesh>
                    <torusGeometry args={[1, 0.42, 12, 24]} />
                    <meshStandardMaterial
                        color="#dc2626"
                        emissive="#991b1b"
                        emissiveIntensity={0.5}
                        roughness={0.35}
                        transparent
                        opacity={0.75}
                        side={THREE.DoubleSide}
                    />
                </mesh>
                {/* Inner dimple — gives biconcave illusion */}
                <mesh scale={[0.75, 0.75, 0.15]}>
                    <sphereGeometry args={[1, 12, 12]} />
                    <meshStandardMaterial
                        color="#b91c1c"
                        emissive="#7f1d1d"
                        emissiveIntensity={0.3}
                        roughness={0.4}
                        transparent
                        opacity={0.55}
                    />
                </mesh>
            </group>
        </Float>
    );
};

/* ═══════════════════════════════════════════════════════
   NEURON — Glowing soma with radiating axons
   ═══════════════════════════════════════════════════════ */
const Neuron = ({ position, scale = 1 }) => {
    const axons = useMemo(() =>
        [...Array(5)].map(() => [
            Math.random() * Math.PI * 2,
            Math.random() * Math.PI * 2,
            0
        ]), []);

    return (
        <Float speed={0.8} rotationIntensity={0.6} floatIntensity={0.7} position={position}>
            <group scale={scale}>
                {/* Soma wireframe */}
                <mesh>
                    <icosahedronGeometry args={[0.8, 1]} />
                    <meshStandardMaterial
                        color="#38bdf8"
                        emissive="#0284c7"
                        emissiveIntensity={1.8}
                        wireframe
                        transparent
                        opacity={0.45}
                    />
                </mesh>
                {/* Bright core */}
                <mesh>
                    <sphereGeometry args={[0.35, 10, 10]} />
                    <meshBasicMaterial color="#bae6fd" transparent opacity={0.9} />
                </mesh>
                {/* Axon branches */}
                {axons.map((rot, i) => (
                    <group key={i} rotation={rot}>
                        <mesh position={[0, 1.2, 0]}>
                            <cylinderGeometry args={[0.025, 0.06, 2.4, 6]} />
                            <meshStandardMaterial color="#7dd3fc" emissive="#0ea5e9" emissiveIntensity={2.5} />
                        </mesh>
                        {/* Synaptic bouton */}
                        <mesh position={[0, 2.4, 0]}>
                            <sphereGeometry args={[0.12, 8, 8]} />
                            <meshBasicMaterial color="#ffffff" transparent opacity={0.85} />
                        </mesh>
                    </group>
                ))}
            </group>
        </Float>
    );
};

/* ═══════════════════════════════════════════════════════
   MITOCHONDRIA — Glowing organic capsule
   ═══════════════════════════════════════════════════════ */
const Mitochondria = ({ position, scale = 1 }) => {
    const meshRef = useRef();
    useFrame(() => {
        if (meshRef.current) {
            meshRef.current.rotation.z += 0.003;
            meshRef.current.rotation.x += 0.001;
        }
    });
    return (
        <Float speed={0.5} rotationIntensity={0.5} floatIntensity={0.6} position={position}>
            <group ref={meshRef} scale={scale}>
                <mesh>
                    <capsuleGeometry args={[0.6, 1, 8, 12]} />
                    <meshStandardMaterial
                        color="#c026d3"
                        emissive="#86198f"
                        emissiveIntensity={0.7}
                        roughness={0.35}
                        transparent
                        opacity={0.65}
                    />
                </mesh>
                {/* Inner cristae ridge */}
                <mesh rotation={[0, 0, Math.PI / 6]}>
                    <capsuleGeometry args={[0.35, 0.5, 6, 8]} />
                    <meshStandardMaterial
                        color="#e879f9"
                        emissive="#a855f7"
                        emissiveIntensity={0.4}
                        transparent
                        opacity={0.3}
                    />
                </mesh>
            </group>
        </Float>
    );
};

/* ═══════════════════════════════════════════════════════
   DNA HELIX — Grand rotating double helix
   ═══════════════════════════════════════════════════════ */
const DNAHelix = ({ position, scale = 1 }) => {
    const groupRef = useRef();

    useFrame((state) => {
        if (groupRef.current) {
            groupRef.current.rotation.y += 0.004;
            groupRef.current.position.y += Math.sin(state.clock.elapsedTime * 0.4) * 0.005;
        }
    });

    const numPairs = 16;
    const height = 12;
    const radius = 1.2;

    const pairs = useMemo(() => {
        const arr = [];
        for (let i = 0; i < numPairs; i++) {
            const t = i / numPairs;
            const y = (t - 0.5) * height;
            const angle = t * Math.PI * 5;
            arr.push({
                y,
                x1: Math.cos(angle) * radius,
                z1: Math.sin(angle) * radius,
                x2: Math.cos(angle + Math.PI) * radius,
                z2: Math.sin(angle + Math.PI) * radius,
                angle,
            });
        }
        return arr;
    }, []);

    return (
        <group ref={groupRef} position={position} scale={scale}
            rotation={[Math.random() * 0.4, Math.random() * Math.PI, Math.random() * 0.4]}>
            {pairs.map((p, i) => (
                <group key={i}>
                    {/* Backbone sphere 1 — Cyan */}
                    <mesh position={[p.x1, p.y, p.z1]}>
                        <sphereGeometry args={[0.2, 8, 8]} />
                        <meshStandardMaterial color="#22d3ee" emissive="#0891b2" emissiveIntensity={3} />
                    </mesh>
                    {/* Backbone sphere 2 — Purple */}
                    <mesh position={[p.x2, p.y, p.z2]}>
                        <sphereGeometry args={[0.2, 8, 8]} />
                        <meshStandardMaterial color="#a855f7" emissive="#7e22ce" emissiveIntensity={3} />
                    </mesh>
                    {/* Connecting rung — Green */}
                    <mesh position={[0, p.y, 0]} rotation={[0, -p.angle, Math.PI / 2]}>
                        <cylinderGeometry args={[0.04, 0.04, radius * 2, 6]} />
                        <meshStandardMaterial color="#4ade80" emissive="#16a34a" emissiveIntensity={2} transparent opacity={0.7} />
                    </mesh>
                </group>
            ))}
        </group>
    );
};

/* ═══════════════════════════════════════════════════════
   BIOSTORM CANVAS — Grand-scale orbital layout
   ~18 total objects, orbiting PDF margins
   ═══════════════════════════════════════════════════════ */
export const BioStormCanvas = React.memo(({ layer = "background" }) => {
    const particles = useMemo(() => {
        const items = [];
        const count = layer === "background" ? 12 : 6;

        for (let i = 0; i < count; i++) {
            // ORBITAL SPAWN: place in left/right margins and corners
            // Avoid the central PDF rectangle
            let x, y;
            do {
                x = (Math.random() - 0.5) * 44;
                y = (Math.random() - 0.5) * 30;
            } while (Math.abs(x) < 8 && Math.abs(y) < 6);

            // ALL particles stay behind the camera (negative Z only)
            const z = layer === "background"
                ? -(Math.random() * 8 + 4)    // -4 to -12
                : -(Math.random() * 5 + 2);   // -2 to -7

            const type = Math.floor(Math.random() * 3);

            // GRAND SCALE: clearly visible, coin-to-apple sized
            const s = layer === "background"
                ? 1.5 + Math.random() * 1.5   // 1.5 — 3.0
                : 2.0 + Math.random() * 2.0;  // 2.0 — 4.0

            items.push({ id: i, pos: [x, y, z], type, scale: s });
        }
        return items;
    }, [layer]);

    const dnaHelices = useMemo(() => {
        if (layer === "background") {
            return [
                { pos: [-16, 3, -6], scale: 1.5 },
                { pos: [18, -4, -10], scale: 1.2 },
            ];
        }
        return [
            { pos: [-18, 8, -4], scale: 1.8 },
        ];
    }, [layer]);

    return (
        <Canvas
            camera={{ position: [0, 0, 25], fov: 50 }}
            gl={{ alpha: true, antialias: false, powerPreference: 'high-performance' }}
            dpr={[1, 1.5]}
            frameloop="always"
            style={{ pointerEvents: 'none' }}
        >
            {/* Ambient fill — deep navy tint */}
            <ambientLight intensity={0.5} color="#0c2461" />
            {/* Central backlight — the gemstone core glow */}
            <pointLight position={[0, 0, 12]} intensity={20} color="#22d3ee" distance={50} decay={2} />
            {/* Rim light from upper-right */}
            <directionalLight position={[12, 8, 8]} intensity={1.2} color="#e0f2fe" />

            {/* Fog only on background for atmospheric depth */}
            {layer === "background" && <fog attach="fog" args={['#01040a', 18, 45]} />}

            {/* DNA Helices */}
            {dnaHelices.map((dna, i) => (
                <DNAHelix key={`dna-${i}`} position={dna.pos} scale={dna.scale} />
            ))}

            {/* Biological Particles */}
            {particles.map(p => {
                if (p.type === 0) return <Erythrocyte key={p.id} position={p.pos} scale={p.scale} />;
                if (p.type === 1) return <Neuron key={p.id} position={p.pos} scale={p.scale} />;
                return <Mitochondria key={p.id} position={p.pos} scale={p.scale} />;
            })}
        </Canvas>
    );
});
