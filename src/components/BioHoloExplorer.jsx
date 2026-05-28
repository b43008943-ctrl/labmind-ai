import React, { useState, useRef, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Environment, Center, Sphere, MeshDistortMaterial, Html, Line, useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { Search, ChevronUp, ChevronDown, X, Dna, Droplets, Leaf, ArrowLeft, Globe2, Activity, Bone, Info, Microscope } from 'lucide-react';
import { generateHoloImage } from '../services/geminiApi';

/* ═══════════════════════════════════════════════════════════════
   SCALABLE HOLOGRAPHIC MODEL CATALOG
   ═══════════════════════════════════════════════════════════════ */
const CATEGORIES = ['All', 'Genetics', 'Cells', 'Pathogens', 'Anatomy', 'Equipment'];

const modelCatalog = [
    {
        id: 'dna',
        name: 'DNA Helix',
        category: 'Genetics',
        description: 'Authentic high-fidelity procedural DNA model. Original photorealistic scientific colors.',
        icon: Dna,
        annotations: [
            { title: "5' Terminal", description: "Leading strand top.", startPoint: [0, 2.0, 0], endPoint: [-1.1, 2.2, 0] },
            { title: "Major Groove", description: "Protein binding.", startPoint: [0, 1.4, 0], endPoint: [1.1, 1.6, 0] },
            { title: "Adenine", description: "Purine base.", startPoint: [0, 0.8, 0], endPoint: [-1.1, 1.0, 0] },
            { title: "Thymine", description: "Pyrimidine base.", startPoint: [0, 0.2, 0], endPoint: [1.1, 0.4, 0] },
            { title: "Cytosine", description: "Pairs with Guanine.", startPoint: [0, -0.4, 0], endPoint: [-1.1, -0.2, 0] },
            { title: "Guanine", description: "Pairs with Cytosine.", startPoint: [0, -1.0, 0], endPoint: [1.1, -0.8, 0] },
            { title: "Minor Groove", description: "Narrow curve.", startPoint: [0, -1.6, 0], endPoint: [-1.1, -1.4, 0] },
            { title: "3' Terminal", description: "Strand bottom.", startPoint: [0, -2.2, 0], endPoint: [1.1, -2.0, 0] }
        ]
    },
    {
        id: 'blood',
        name: 'Erythrocyte',
        category: 'Cells',
        description: 'High-poly photorealistic erythrocyte geometry. Natural medical reds.',
        icon: Droplets,
        annotations: [
            { title: "Lipid Bilayer", description: "Outer membrane.", startPoint: [0, 1.4, 0], endPoint: [-1.1, 1.8, 0] },
            { title: "Cytoplasm", description: "Inner fluid.", startPoint: [0, 1.0, 0], endPoint: [1.1, 1.3, 0] },
            { title: "Concavity", description: "Max surface area.", startPoint: [0, 0.6, 0], endPoint: [-1.1, 0.8, 0] },
            { title: "Hemoglobin", description: "O2 transporter.", startPoint: [0, 0.2, 0], endPoint: [1.1, 0.3, 0] },
            { title: "Spectrin", description: "Cell matrix.", startPoint: [0, -0.2, 0], endPoint: [-1.1, -0.2, 0] },
            { title: "Periphery", description: "Thickest region.", startPoint: [0, -0.6, 0], endPoint: [1.1, -0.7, 0] },
            { title: "O2 Saturation", description: "Binding capacity.", startPoint: [0, -1.0, 0], endPoint: [-1.1, -1.2, 0] },
            { title: "Cell Base", description: "Lower bound.", startPoint: [0, -1.4, 0], endPoint: [1.1, -1.7, 0] }
        ]
    },
    {
        id: 'microbes',
        name: 'Microbe',
        category: 'Pathogens',
        description: 'Complex anatomical procedural representation of microbial structures.',
        icon: Leaf,
        annotations: [
            { title: "Viral Envelope", description: "Lipid armor.", startPoint: [0, 1.8, 0], endPoint: [-1.1, 2.0, 0] },
            { title: "Spike Proteins", description: "Cell attachment.", startPoint: [0, 1.3, 0], endPoint: [1.1, 1.5, 0] },
            { title: "Capsid", description: "Protein shell.", startPoint: [0, 0.8, 0], endPoint: [-1.1, 0.8, 0] },
            { title: "Nucleic Acid", description: "Viral RNA.", startPoint: [0, 0.3, 0], endPoint: [1.1, 0.3, 0] },
            { title: "Matrix", description: "Structural core.", startPoint: [0, -0.2, 0], endPoint: [-1.1, -0.4, 0] },
            { title: "Fusion Domain", description: "Entry point.", startPoint: [0, -0.7, 0], endPoint: [1.1, -1.0, 0] },
            { title: "Receptors", description: "Target lock.", startPoint: [0, -1.2, 0], endPoint: [-1.1, -1.6, 0] },
            { title: "Core Anchor", description: "Base support.", startPoint: [0, -1.7, 0], endPoint: [1.1, -2.4, 0] }
        ]
    },
    {
        id: 'neuron',
        name: 'Motor Neuron',
        category: 'Cells',
        description: 'Procedural multipolar neuron featuring a glowing soma, dendrites, and myelinated axons.',
        icon: Activity,
        annotations: [
            { title: "Dendrites", description: "Signal receivers.", startPoint: [0, 1.6, 0], endPoint: [-1.1, 2.0, 0] },
            { title: "Soma Base", description: "Cell body.", startPoint: [0, 1.1, 0], endPoint: [1.1, 1.4, 0] },
            { title: "Nucleus", description: "Genetic center.", startPoint: [0, 0.6, 0], endPoint: [-1.1, 0.8, 0] },
            { title: "Axon Hillock", description: "Action potential.", startPoint: [0, 0.1, 0], endPoint: [1.1, 0.2, 0] },
            { title: "Myelin Sheath", description: "Axon insulator.", startPoint: [0, -0.4, 0], endPoint: [-1.1, -0.4, 0] },
            { title: "Ranvier Node", description: "Signal booster.", startPoint: [0, -0.9, 0], endPoint: [1.1, -1.0, 0] },
            { title: "Schwann Cell", description: "Myelin source.", startPoint: [0, -1.4, 0], endPoint: [-1.1, -1.6, 0] },
            { title: "Axon Terminal", description: "Synapse sender.", startPoint: [0, -1.9, 0], endPoint: [1.1, -2.2, 0] }
        ]
    },
    {
        id: 'bone',
        name: 'Bone Fracture',
        category: 'Anatomy',
        description: 'Procedurally generated transverse bone fracture with cortical splinters.',
        icon: Bone,
        annotations: [
            { title: "Epiphysis", description: "Upper joint.", startPoint: [0, 1.8, 0], endPoint: [-1.1, 2.0, 0] },
            { title: "Spongy Bone", description: "Cancellous tissue.", startPoint: [0, 1.2, 0], endPoint: [1.1, 1.4, 0] },
            { title: "Compact Bone", description: "Dense outer.", startPoint: [0, 0.6, 0], endPoint: [-1.1, 0.8, 0] },
            { title: "Fracture Line", description: "Transverse shear.", startPoint: [0, 0.0, 0], endPoint: [1.1, 0.2, 0] },
            { title: "Splinter", description: "Bone fragment.", startPoint: [0, -0.5, 0], endPoint: [-1.1, -0.4, 0] },
            { title: "Medullary Site", description: "Marrow core.", startPoint: [0, -1.0, 0], endPoint: [1.1, -1.0, 0] },
            { title: "Periosteum", description: "Outer membrane.", startPoint: [0, -1.5, 0], endPoint: [-1.1, -1.6, 0] },
            { title: "Diaphysis", description: "Lower shaft.", startPoint: [0, -2.0, 0], endPoint: [1.1, -2.2, 0] }
        ]
    },
    {
        id: 'microscope',
        name: 'Holo-Microscope',
        category: 'Equipment',
        description: 'Procedural highly detailed electron microscope blueprint visualization.',
        icon: Microscope,
        annotations: [
            { title: "Eyepiece", description: "Top viewing lens.", startPoint: [0, 0.6, 0.2], endPoint: [-1.0, 1.0, 0] },
            { title: "Body Tube", description: "Main cylinder.", startPoint: [0, 0.3, 0.1], endPoint: [1.0, 0.7, 0] },
            { title: "Nosepiece", description: "Rotating mount.", startPoint: [0, 0.0, 0.2], endPoint: [-1.0, 0.1, 0] },
            { title: "Objectives", description: "Zoom lenses.", startPoint: [0, -0.2, 0.3], endPoint: [1.0, -0.2, 0] },
            { title: "Stage", description: "Slide platform.", startPoint: [0, -0.5, 0.4], endPoint: [-1.1, -0.6, 0] },
            { title: "Condenser", description: "Light focus.", startPoint: [0, -0.7, 0.2], endPoint: [1.1, -1.0, 0] },
            { title: "Knobs", description: "Focus controls.", startPoint: [-0.4, -0.6, 0], endPoint: [-1.1, -1.6, 0] },
            { title: "Base", description: "Power supply.", startPoint: [0, -1.1, 0], endPoint: [1.0, -2.0, 0] }
        ]
    }
];

/* ═══════════════════════════════════════════════════════════════
   CINEMATIC HOLOGRAPHIC ANNOTATIONS
   ═══════════════════════════════════════════════════════════════ */
const LaserAnnotation = ({ startPoint, endPoint, title, description, index }) => {
    const [lineParams] = useState({ progress: 0 });
    const lineRef = useRef();
    const vecStart = useMemo(() => new THREE.Vector3(...startPoint), [startPoint]);
    const vecEnd = useMemo(() => new THREE.Vector3(...endPoint), [endPoint]);
    const currentEnd = useMemo(() => new THREE.Vector3(...startPoint), [startPoint]);
    const [showUI, setShowUI] = useState(false);

    useFrame((state, delta) => {
        const delay = index * 0.15;
        if (state.clock.elapsedTime > delay) {
            if (lineParams.progress < 1) {
                lineParams.progress += delta * 2.5;
                if (lineParams.progress >= 1) {
                    lineParams.progress = 1;
                    setShowUI(true);
                }
                currentEnd.lerpVectors(vecStart, vecEnd, lineParams.progress);
                if (lineRef.current) {
                    const positions = lineRef.current.geometry.attributes.position.array;
                    positions[3] = currentEnd.x;
                    positions[4] = currentEnd.y;
                    positions[5] = currentEnd.z;
                    lineRef.current.geometry.attributes.position.needsUpdate = true;
                }
            }
        }
    });

    return (
        <group>
            <Line
                ref={lineRef}
                points={[startPoint, startPoint]}
                color="#00ffff"
                lineWidth={0.5}
                transparent
                opacity={0.8}
            />
            {showUI && (
                <Html position={endPoint} center zIndexRange={[10, 0]}>
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, ease: "easeOut" }}
                        className="flex flex-col pointer-events-none"
                        style={{
                            background: 'rgba(10, 15, 30, 0.4)',
                            backdropFilter: 'blur(12px)',
                            WebkitBackdropFilter: 'blur(12px)',
                            border: '1px solid rgba(0, 255, 255, 0.2)',
                            boxShadow: 'inset 0 0 10px rgba(0, 255, 255, 0.1)',
                            borderRadius: '6px',
                            padding: '6px 10px',
                            maxWidth: '110px',
                            minWidth: '90px',
                        }}
                    >
                        <h3 style={{ fontSize: '11px', color: '#00e5ff', fontWeight: '600', letterSpacing: '0.5px', margin: 0, padding: 0, lineHeight: 1.2 }}>{title}</h3>
                        <p style={{ fontSize: '9px', color: '#e2e8f0', margin: 0, marginTop: '2px', padding: 0, lineHeight: 1.2 }}>{description}</p>
                    </motion.div>
                </Html>
            )}
        </group>
    );
};

/* ═══════════════════════════════════════════════════════════════
   PHOTOREALISTIC PROCEDURAL GEOMETRY (MEDICAL GRADE)
   ═══════════════════════════════════════════════════════════════ */

// --- 1. REALISTIC DNA (InstancedMesh Double Helix) ---
const RealisticDNA = () => {
    const groupRef = useRef();
    const numPairs = 40;

    useFrame((state, delta) => {
        if (groupRef.current) {
            groupRef.current.rotation.y += delta * 0.2;
            groupRef.current.position.y = Math.sin(state.clock.elapsedTime) * 0.2;
        }
    });

    const rungs = [];
    // Deep physiological colors (Adenine, Thymine, Cytosine, Guanine)
    const colors = ['#e63946', '#f4a261', '#2a9d8f', '#264653'];

    for (let i = 0; i < numPairs; i++) {
        const y = (i - numPairs / 2) * 0.3;
        const angle = i * 0.4;
        const radius = 1.6;

        const x1 = Math.cos(angle) * radius;
        const z1 = Math.sin(angle) * radius;
        const x2 = Math.cos(angle + Math.PI) * radius;
        const z2 = Math.sin(angle + Math.PI) * radius;

        const rungColor = colors[i % 4];

        rungs.push(
            <group key={i}>
                {/* Backbone 1 */}
                <mesh position={[x1, y, z1]}>
                    <sphereGeometry args={[0.25, 32, 32]} />
                    <meshPhysicalMaterial
                        color="#e2e8f0"
                        roughness={0.2}
                        clearcoat={1}
                        transmission={0.6}
                        thickness={0.5}
                    />
                </mesh>
                {/* Backbone 2 */}
                <mesh position={[x2, y, z2]}>
                    <sphereGeometry args={[0.25, 32, 32]} />
                    <meshPhysicalMaterial
                        color="#e2e8f0"
                        roughness={0.2}
                        clearcoat={1}
                        transmission={0.6}
                        thickness={0.5}
                    />
                </mesh>
                {/* Connecting Rung (Base Pair) */}
                <mesh position={[0, y, 0]} rotation={[0, -angle, Math.PI / 2]}>
                    <cylinderGeometry args={[0.1, 0.1, radius * 2, 16]} />
                    <meshStandardMaterial color={rungColor} roughness={0.3} metalness={0.2} />
                </mesh>
            </group>
        );
    }

    return (
        <group ref={groupRef} scale={1.2}>
            {rungs}
        </group>
    );
};

// --- 2. REALISTIC BLOOD CELLS (Concave Erythrocytes) ---
const RealisticBloodCell = ({ position, initialRotation }) => {
    const ref = useRef();
    useFrame((_, delta) => {
        if (ref.current) {
            ref.current.rotation.x += delta * 0.2;
            ref.current.rotation.y += delta * 0.1;
        }
    });

    return (
        <group position={position} rotation={initialRotation}>
            {/* Outer Torus Rim */}
            <mesh>
                <torusGeometry args={[0.6, 0.3, 32, 48]} />
                <meshStandardMaterial color="#8a0303" roughness={0.4} metalness={0.1} />
            </mesh>
            {/* Inner Dimpled Core */}
            <mesh scale={[1, 1, 0.4]}>
                <sphereGeometry args={[0.65, 32, 32]} />
                <meshStandardMaterial color="#6a0202" roughness={0.5} metalness={0.1} />
            </mesh>
        </group>
    );
};

const RealisticBloodCluster = () => {
    const groupRef = useRef();

    useFrame((state, delta) => {
        if (groupRef.current) {
            groupRef.current.rotation.y += delta * 0.05;
            groupRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.2;
        }
    });

    const cells = [];
    for (let i = 0; i < 40; i++) {
        // Randomly scatter in a loose sphere formation
        const radius = Math.random() * 5 + 1;
        const theta = Math.random() * 2 * Math.PI;
        const phi = Math.acos(Math.random() * 2 - 1);

        const x = radius * Math.sin(phi) * Math.cos(theta);
        const y = radius * Math.sin(phi) * Math.sin(theta);
        const z = radius * Math.cos(phi);

        const rot = [Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI];

        cells.push(
            <RealisticBloodCell key={i} position={[x, y, z]} initialRotation={rot} />
        );
    }

    return (
        <group ref={groupRef} scale={0.7}>
            {cells}
        </group>
    );
};

// --- 3. REALISTIC MICROBES (Virus Geometry with MeshDistortMaterial) ---
const RealisticMicrobe = () => {
    const groupRef = useRef();

    useFrame((state, delta) => {
        if (groupRef.current) {
            // Eerie floating rotation
            groupRef.current.rotation.x += delta * 0.1;
            groupRef.current.rotation.y += delta * 0.15;
            groupRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
        }
    });

    return (
        <group ref={groupRef} scale={1.2}>
            {/* 1. Core Organism - Bumping / Breathing organically using safe Drei material */}
            <Sphere args={[2, 64, 64]}>
                <MeshDistortMaterial
                    color="#2a005e"
                    emissive="#4a00e0"
                    emissiveIntensity={0.5}
                    distort={0.4}
                    speed={2}
                    roughness={0.2}
                    metalness={0.1}
                />
            </Sphere>

            {/* 2. Viral Membrane Halo - Stable translucent cage */}
            <Sphere args={[2.2, 32, 32]}>
                <meshPhysicalMaterial
                    color="#00e5ff"
                    transparent={true}
                    opacity={0.15}
                    roughness={0}
                    transmission={1}
                    wireframe={true}
                />
            </Sphere>
        </group>
    );
};

// --- 4. PROCEDURAL NEURON ---
const RealisticNeuron = () => {
    const groupRef = useRef();

    useFrame((state, delta) => {
        if (groupRef.current) {
            groupRef.current.rotation.y += delta * 0.1;
            groupRef.current.rotation.x += delta * 0.05;
        }
    });

    return (
        <group ref={groupRef} scale={1.5}>
            {/* Soma (Cell Body) */}
            <mesh>
                <icosahedronGeometry args={[1, 2]} />
                <meshPhysicalMaterial color="#3b82f6" transmission={0.7} opacity={1} transparent roughness={0.3} wireframe />
            </mesh>
            {/* Nucleus */}
            <mesh>
                <sphereGeometry args={[0.4, 16, 16]} />
                <meshStandardMaterial color="#60a5fa" emissive="#3b82f6" emissiveIntensity={2} />
            </mesh>

            {/* Axons & Dendrites */}
            {[...Array(6)].map((_, i) => (
                <group key={i} rotation={[Math.random() * Math.PI, Math.random() * Math.PI, 0]}>
                    <mesh position={[0, 1.2, 0]}>
                        <cylinderGeometry args={[0.06, 0.15, 1.5, 8]} />
                        <meshStandardMaterial color="#93c5fd" emissive="#3b82f6" emissiveIntensity={0.5} />
                    </mesh>
                    <mesh position={[0, 2.1, 0]}>
                        <sphereGeometry args={[0.12, 8, 8]} />
                        <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={1.5} />
                    </mesh>
                </group>
            ))}
        </group>
    );
};

// --- 5. PROCEDURAL BONE FRACTURE (FEMUR — EXACT ANATOMY) ---
const RealisticBoneFracture = () => {
    const groupRef = useRef();

    useFrame((state, delta) => {
        if (groupRef.current) {
            groupRef.current.rotation.y += delta * 0.15;
        }
    });

    // Medical grade osteology material (STRICTLY enforced)
    const boneMatProps = {
        color: "#d4cbb3",
        roughness: 0.9,
        metalness: 0.05
    };

    return (
        <group ref={groupRef} scale={1.0}>
            {/* Ambient & Directional Lighting for clinical highlighting */}
            <ambientLight intensity={0.4} color="#ffffff" />
            <directionalLight position={[5, 10, 5]} intensity={2.0} castShadow />

            {/* ─── UPPER BONE HALF (PROXIMAL FEMUR) ─── */}
            <group position={[0, 1.2, 0]} rotation={[0, 0, 0.05]}>
                {/* Shaft */}
                <mesh position={[0, 0, 0]}>
                    <cylinderGeometry args={[0.22, 0.25, 2.5, 32]} />
                    <meshStandardMaterial {...boneMatProps} />
                </mesh>
                {/* Femoral Head (Right) */}
                <mesh position={[0.35, 1.3, 0]}>
                    <sphereGeometry args={[0.45, 32, 32]} />
                    <meshStandardMaterial {...boneMatProps} />
                </mesh>
                {/* Greater Trochanter (Left) */}
                <mesh position={[-0.3, 1.1, 0]}>
                    <sphereGeometry args={[0.35, 32, 32]} />
                    <meshStandardMaterial {...boneMatProps} />
                </mesh>
            </group>

            {/* ─── LOWER BONE HALF (DISTAL FEMUR) ─── */}
            {/* Shifted down and angulated to show a severe break */}
            <group position={[0.2, -1.5, 0.1]} rotation={[0, 0, 0.15]}>
                {/* Shaft */}
                <mesh position={[0, 0, 0]}>
                    <cylinderGeometry args={[0.25, 0.35, 2.5, 32]} />
                    <meshStandardMaterial {...boneMatProps} />
                </mesh>
                {/* Medial Condyle */}
                <mesh position={[0.25, -1.3, 0.1]} scale={[1, 1.2, 1.2]}>
                    <sphereGeometry args={[0.4, 32, 32]} />
                    <meshStandardMaterial {...boneMatProps} />
                </mesh>
                {/* Lateral Condyle */}
                <mesh position={[-0.25, -1.3, -0.1]} scale={[1, 1.2, 1.2]}>
                    <sphereGeometry args={[0.4, 32, 32]} />
                    <meshStandardMaterial {...boneMatProps} />
                </mesh>
            </group>
        </group>
    );
};

// --- 6. REAL GLB MICROSCOPE (HOLOGRAPHIC OVERRIDE) ---
const Microscope3D = () => {
    const { scene } = useGLTF('/models/microscope.glb');

    // Create the global sci-fi emissive hologram material
    const holoMat = useMemo(() => new THREE.MeshStandardMaterial({
        color: '#00e5ff',
        transparent: true,
        opacity: 0.4,
        metalness: 0.8,
        roughness: 0.1,
        emissive: '#004455',
        emissiveIntensity: 0.8,
        wireframe: false
    }), []);

    // Traverse the loaded GLB scene and universally overwrite all inherited default materials
    useMemo(() => {
        if (scene) {
            scene.traverse((child) => {
                if (child.isMesh) {
                    child.material = holoMat;
                }
            });
        }
    }, [scene, holoMat]);

    return (
        <Center position={[0, -1, 0]}>
            <primitive object={scene} scale={[0.12, 0.12, 0.12]} />
        </Center>
    );
};

// Auto-preload the WebGL model for zero-latency mounting
useGLTF.preload('/models/microscope.glb');

class BioHoloErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true };
    }
    componentDidCatch(error, errorInfo) {
        console.error("BioHoloExplorer Crash:", error, errorInfo);
    }
    render() {
        if (this.state.hasError) {
            return (
                <div className="w-full h-[100dvh] bg-[#050510] text-cyan-500 flex items-center justify-center flex-col font-mono text-center px-4 relative overflow-hidden">
                    <p className="mb-4">SYSTEM REBOOTING... REFRESHING UI.</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-6 py-2 bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 rounded-lg active:scale-95 transition-transform"
                    >
                        REBOOT NOW
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}

function BioHoloExplorerBase({ onBack }) {
    const [activeModelId, setActiveModelId] = useState('dna');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All');
    const [isLibraryOpen, setIsLibraryOpen] = useState(false);
    const [showInfo, setShowInfo] = useState(true);

    const activeModel = modelCatalog.find(m => m.id === activeModelId) || modelCatalog[0];

    // Auto-hide info panel after 4 seconds when a new model is selected
    useEffect(() => {
        setShowInfo(true);
        const timer = setTimeout(() => {
            setShowInfo(false);
        }, 4000);
        return () => clearTimeout(timer);
    }, [activeModelId]);

    // Filter models
    const filteredModels = modelCatalog.filter(model => {
        const matchesCategory = selectedCategory === 'All' || model.category === selectedCategory;
        const matchesSearch = model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            model.category.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesCategory && matchesSearch;
    });

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 z-50 flex flex-col bg-[#050a19] w-full h-[100dvh] md:max-w-md md:mx-auto md:shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-hidden"
            style={{ fontFamily: "'Inter', sans-serif" }}
        >
            {/* ── TOP GLASSMORPHISM SEARCH & FILTER BAR ── */}
            <div className="absolute top-0 inset-x-0 z-30 pt-12 pb-4 px-5 bg-linear-to-b from-[#050a19]/90 to-transparent pointer-events-none">
                <div className="pointer-events-auto flex flex-col gap-3">
                    <div className="flex items-center gap-3">
                        {onBack && (
                            <button
                                onClick={onBack}
                                className="flex items-center justify-center min-w-[40px] h-10 rounded-full bg-white/5 border border-white/10 text-white active:scale-95 transition-transform cursor-pointer"
                            >
                                <ArrowLeft size={16} />
                            </button>
                        )}
                        <div className="flex flex-col">
                            <h1 className="text-sm font-mono font-bold text-teal-400 tracking-widest uppercase flex items-center gap-2">
                                <Globe2 size={16} /> BIOLOGY VAULT
                            </h1>
                            <span className="text-[10px] text-teal-500/50 uppercase tracking-widest font-mono">Medical Procedural Geometry</span>
                        </div>
                    </div>

                    <div className="relative flex-1 mt-3">
                        <Search className="absolute left-3 top-2.5 text-cyan-400/50" size={16} />
                        <input
                            type="text"
                            placeholder="Search holograms..."
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                            onPointerDown={e => e.stopPropagation()}
                            onTouchStart={e => e.stopPropagation()}
                            className="w-full bg-[#050a19]/50 border border-cyan-500/30 rounded-full py-2 pl-10 pr-8 text-white text-sm focus:outline-none focus:border-cyan-400 backdrop-blur-md"
                        />
                        {searchQuery && (
                            <button
                                onClick={() => setSearchQuery('')}
                                className="absolute right-3 top-2.5 text-white/50 hover:text-white"
                            >
                                <X size={14} />
                            </button>
                        )}
                    </div>

                    {/* Filter Chips */}
                    <div
                        className="flex w-full overflow-x-auto no-scrollbar snap-x snap-mandatory gap-2 pb-1"
                        onPointerDown={e => e.stopPropagation()}
                        onTouchStart={e => e.stopPropagation()}
                        onWheel={e => e.stopPropagation()}
                    >
                        {CATEGORIES.map(cat => (
                            <button
                                key={cat}
                                onClick={() => setSelectedCategory(cat)}
                                className={`px-4 py-1.5 rounded-full text-xs font-mono tracking-wider whitespace-nowrap snap-center active:scale-95 transition-all ${selectedCategory === cat
                                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.3)]'
                                    : 'bg-white/5 text-white/50 border border-white/10'
                                    }`}
                            >
                                {cat}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── MAIN VIEWPORT (PORTRAIT & TOUCH OPTIMIZED) ── */}
            <div className="flex-1 w-full h-full relative z-0" style={{ touchAction: 'none' }}>
                <Canvas
                    gl={{ alpha: true, antialias: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 1.0, failIfMajorPerformanceCaveat: false }}
                    camera={{ position: [0, 0, 8], fov: 45 }}
                    className="absolute inset-0 w-full h-full"
                    style={{ background: 'transparent' }}
                    shadows={{ type: THREE.PCFShadowMap }}
                    onCreated={({ gl }) => {
                        gl.domElement.addEventListener('webglcontextlost', (e) => { e.preventDefault(); console.warn('WebGL context lost — will attempt recovery'); }, false);
                        gl.domElement.addEventListener('webglcontextrestored', () => { console.log('WebGL context restored'); }, false);
                    }}
                >
                    <Environment preset="studio" />
                    <ambientLight intensity={0.4} color="#ffffff" />
                    <spotLight position={[0, 10, 0]} intensity={1.5} color="#00e5ff" castShadow />
                    <directionalLight position={[5, 10, 5]} intensity={2.0} color="#ffffff" castShadow />
                    <directionalLight position={[-5, -5, -3]} intensity={0.5} color="#d4cbb3" />

                    <Center position={[0, -0.5, 0]}>
                        <group scale={0.25}>
                            {activeModelId === 'dna' && <RealisticDNA />}
                            {activeModelId === 'blood' && <RealisticBloodCluster />}
                            {activeModelId === 'microbes' && <RealisticMicrobe />}
                            {activeModelId === 'neuron' && <RealisticNeuron />}
                            {activeModelId === 'bone' && <RealisticBoneFracture />}
                        </group>
                    </Center>

                    {activeModelId === 'microscope' && <Microscope3D />}

                    {/* MOUNT CINEMATIC HOLOGRAPHIC ANNOTATIONS */}
                    {activeModel.annotations?.map((anno, index) => (
                        <LaserAnnotation key={index} index={index} {...anno} />
                    ))}

                    <OrbitControls
                        enableZoom={true}
                        enablePan={true}
                        enableRotate={true}
                        makeDefault={true}
                        enableDamping={true}
                        dampingFactor={0.05}
                        minDistance={0.5}
                        maxDistance={100}
                        target={[0, 0, 0]}
                    />
                </Canvas>

                {/* Floating Info Toggle Button */}
                <AnimatePresence>
                    {!isLibraryOpen && !showInfo && (
                        <motion.button
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            onClick={() => setShowInfo(true)}
                            className="absolute bottom-28 right-4 z-20 w-10 h-10 rounded-full bg-cyan-500/20 backdrop-blur-md border border-cyan-500/50 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.3)] active:scale-95 transition-all"
                        >
                            <Info size={20} />
                        </motion.button>
                    )}
                </AnimatePresence>

                {/* Auto-Hiding Micro Info Panel */}
                <div
                    className={`absolute bottom-28 left-4 right-4 z-20 transition-all duration-700 ease-in-out pointer-events-none ${showInfo && !isLibraryOpen ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
                        }`}
                >
                    <div className="bg-[#050a19]/80 backdrop-blur-md border border-cyan-500/30 rounded-2xl p-3 shadow-[0_0_20px_rgba(0,0,0,0.5)]">
                        <div className="flex items-center gap-2 mb-1.5">
                            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20 shrink-0">
                                <activeModel.icon size={16} className="text-cyan-400" />
                            </div>
                            <div>
                                <h2 className="text-xs font-mono font-bold uppercase tracking-widest text-cyan-100">{activeModel.name}</h2>
                                <p className="text-[9px] text-cyan-500/80 font-mono tracking-widest uppercase">{activeModel.category}</p>
                            </div>
                            {/* Manual Close Button */}
                            <button
                                onClick={() => setShowInfo(false)}
                                className="ml-auto pointer-events-auto w-6 h-6 flex items-center justify-center rounded-full bg-white/5 text-white/40 hover:text-white/80 active:scale-95"
                            >
                                <X size={12} />
                            </button>
                        </div>
                        <p className="text-[10px] text-gray-400 leading-tight font-mono line-clamp-2 pr-2">
                            {activeModel.description}
                        </p>
                    </div>
                </div>

                {/* ── RETRACTABLE BOTTOM SHEET (THE LIBRARY) ── */}
                <motion.div
                    className="absolute bottom-0 inset-x-0 z-9999 bg-[#050a19]/90 backdrop-blur-2xl border-t border-cyan-500/20 rounded-t-3xl flex flex-col pointer-events-auto"
                    initial={false}
                    animate={{ height: isLibraryOpen ? '60%' : '80px' }}
                    transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                    onPointerDown={e => e.stopPropagation()}
                    onTouchStart={e => e.stopPropagation()}
                    onWheel={e => e.stopPropagation()}
                >
                    {/* Drag Handle Area */}
                    <div
                        className="w-full flex justify-center pt-3 pb-5 cursor-pointer"
                        onClick={() => setIsLibraryOpen(!isLibraryOpen)}
                    >
                        <div className="w-12 h-1.5 bg-white/20 rounded-full" />
                    </div>

                    {/* Library Header (Visible when collapsed) */}
                    <div
                        className="px-6 pb-4 flex justify-between items-center cursor-pointer"
                        onClick={() => setIsLibraryOpen(!isLibraryOpen)}
                    >
                        <h3 className="text-sm font-mono font-bold text-white tracking-widest uppercase">Model Library</h3>
                        {isLibraryOpen ? <ChevronDown size={18} className="text-white/50" /> : <ChevronUp size={18} className="text-white/50" />}
                    </div>

                    {/* Expanded Content: Model Grid */}
                    <div className="flex-1 overflow-y-auto px-4 pb-8 no-scrollbar">
                        {filteredModels.length > 0 ? (
                            <div className="grid grid-cols-2 gap-3">
                                {filteredModels.map(model => (
                                    <button
                                        key={model.id}
                                        onClick={() => {
                                            setActiveModelId(model.id);
                                            setIsLibraryOpen(false);
                                        }}
                                        className={`flex flex-col items-center justify-center p-4 rounded-2xl border transition-all active:scale-95 ${activeModelId === model.id
                                            ? 'bg-cyan-500/20 border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                                            : 'bg-white/5 border-white/5 hover:bg-white/10'
                                            }`}
                                    >
                                        <model.icon size={28} className={`mb-3 ${activeModelId === model.id ? 'text-cyan-400' : 'text-white/50'}`} />
                                        <span className={`text-xs font-mono font-bold mb-1 ${activeModelId === model.id ? 'text-white' : 'text-white/70'}`}>
                                            {model.name}
                                        </span>
                                        <span className="text-[9px] font-mono text-white/40 uppercase tracking-wider">{model.category}</span>
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-40 text-white/40">
                                <Search size={24} className="mb-2 opacity-50" />
                                <p className="text-xs font-mono">No holograms found</p>
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>
        </motion.div >
    );
}

export default function BioHoloExplorer(props) {
    return (
        <BioHoloErrorBoundary>
            <BioHoloExplorerBase {...props} />
        </BioHoloErrorBoundary>
    );
}
