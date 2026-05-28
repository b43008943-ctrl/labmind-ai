import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Sphere, Torus, Cylinder } from '@react-three/drei';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { Trash2, Pin } from 'lucide-react';
import * as THREE from 'three';

// --- Shared Material Traits ---
const emissiveMaterialArgs = {
    color: "#002244",
    emissive: "#00e5ff",
    emissiveIntensity: 1.5,
    wireframe: true,
    transparent: true,
    opacity: 0.8
};

// --- MODEL A: THE ATOM ---
const AtomModel = () => {
    const groupRef = useRef(null);
    useFrame((state, delta) => {
        if (groupRef.current) {
            groupRef.current.rotation.y += delta * 0.5;
            groupRef.current.rotation.x += delta * 0.3;
        }
    });

    return (
        <group ref={groupRef}>
            <Sphere args={[0.3, 16, 16]}>
                <meshStandardMaterial {...emissiveMaterialArgs} wireframe={false} emissiveIntensity={2} />
            </Sphere>
            <Torus args={[0.8, 0.05, 16, 32]} rotation={[Math.PI / 2, 0, 0]}>
                <meshStandardMaterial {...emissiveMaterialArgs} />
            </Torus>
            <Torus args={[0.8, 0.05, 16, 32]} rotation={[0, Math.PI / 2, Math.PI / 4]}>
                <meshStandardMaterial {...emissiveMaterialArgs} />
            </Torus>
            <Torus args={[0.8, 0.05, 16, 32]} rotation={[0, Math.PI / 2, -Math.PI / 4]}>
                <meshStandardMaterial {...emissiveMaterialArgs} />
            </Torus>
        </group>
    );
};

// --- MODEL B: DNA FRAGMENT ---
const DNAModel = () => {
    const groupRef = useRef(null);
    useFrame((state, delta) => {
        if (groupRef.current) {
            groupRef.current.rotation.y += delta * 0.8;
        }
    });

    const numBasePairs = 8;
    const heightSpread = 2;
    const radius = 0.5;

    const basePairs = useMemo(() => {
        const pairs = [];
        for (let i = 0; i < numBasePairs; i++) {
            const y = (i / (numBasePairs - 1)) * heightSpread - heightSpread / 2;
            const angle = i * 0.8;
            const x1 = Math.cos(angle) * radius;
            const z1 = Math.sin(angle) * radius;
            const x2 = Math.cos(angle + Math.PI) * radius;
            const z2 = Math.sin(angle + Math.PI) * radius;
            pairs.push({ x1, y, z1, x2, z2, angle });
        }
        return pairs;
    }, []);

    return (
        <group ref={groupRef}>
            {basePairs.map((bp, i) => (
                <group key={i}>
                    <Sphere args={[0.1, 8, 8]} position={[bp.x1, bp.y, bp.z1]}>
                        <meshStandardMaterial {...emissiveMaterialArgs} wireframe={false} emissive="#00e5ff" color="#001133" />
                    </Sphere>
                    <Sphere args={[0.1, 8, 8]} position={[bp.x2, bp.y, bp.z2]}>
                        <meshStandardMaterial {...emissiveMaterialArgs} wireframe={false} emissive="#00aaff" color="#001133" />
                    </Sphere>
                    <Cylinder args={[0.03, 0.03, radius * 2, 8]} position={[0, bp.y, 0]} rotation={[0, -bp.angle, Math.PI / 2]}>
                        <meshStandardMaterial {...emissiveMaterialArgs} opacity={0.5} />
                    </Cylinder>
                </group>
            ))}
        </group>
    );
};

// --- MODEL C: COMPLEX MOLECULE ---
const MoleculeModel = () => {
    const groupRef = useRef(null);
    useFrame((state, delta) => {
        if (groupRef.current) {
            groupRef.current.rotation.y -= delta * 0.4;
            groupRef.current.rotation.z += delta * 0.2;
        }
    });

    return (
        <group ref={groupRef}>
            <Sphere args={[0.3, 16, 16]}>
                <meshStandardMaterial {...emissiveMaterialArgs} wireframe={false} emissiveIntensity={2} />
            </Sphere>

            {/* Branch 1 */}
            <Cylinder args={[0.04, 0.04, 1, 8]} position={[0.4, 0.4, 0]} rotation={[0, 0, -Math.PI / 4]}>
                <meshStandardMaterial {...emissiveMaterialArgs} />
            </Cylinder>
            <Sphere args={[0.15, 16, 16]} position={[0.8, 0.8, 0]}>
                <meshStandardMaterial {...emissiveMaterialArgs} wireframe={false} />
            </Sphere>

            {/* Branch 2 */}
            <Cylinder args={[0.04, 0.04, 1, 8]} position={[-0.4, -0.4, 0]} rotation={[0, 0, -Math.PI / 4]}>
                <meshStandardMaterial {...emissiveMaterialArgs} />
            </Cylinder>
            <Sphere args={[0.15, 16, 16]} position={[-0.8, -0.8, 0]}>
                <meshStandardMaterial {...emissiveMaterialArgs} wireframe={false} />
            </Sphere>

            {/* Branch 3 */}
            <Cylinder args={[0.04, 0.04, 1.2, 8]} position={[0, -0.5, 0.5]} rotation={[Math.PI / 4, 0, 0]}>
                <meshStandardMaterial {...emissiveMaterialArgs} />
            </Cylinder>
            <Sphere args={[0.2, 16, 16]} position={[0, -1, 1]}>
                <meshStandardMaterial {...emissiveMaterialArgs} wireframe={false} emissive="#00aaff" />
            </Sphere>
        </group>
    );
};

export const HoloFileCard = ({ file, onClick, onDelete, idx = 0, activeMenu, setActiveMenu, onTogglePin }) => {

    // Hold interaction timer
    const timerRef = useRef(null);

    const handlePointerDown = (e) => {
        timerRef.current = setTimeout(() => {
            setActiveMenu(file.id);
        }, 600);
    };

    const clearTimer = () => {
        if (timerRef.current) clearTimeout(timerRef.current);
    };

    // Switch between the three models based on the card's array index
    const renderModel = () => {
        const type = idx % 3;
        if (type === 0) return <AtomModel />;
        if (type === 1) return <DNAModel />;
        return <MoleculeModel />;
    };

    return (
        <div
            onPointerDown={handlePointerDown}
            onPointerUp={clearTimer}
            onPointerCancel={clearTimer}
            onPointerLeave={clearTimer}
            onClick={(e) => {
                if (activeMenu === file.id) return;
                onClick(e);
            }}
            className="relative flex flex-col items-center group cursor-pointer bg-[#0c4a6e]/10 backdrop-blur-xl border border-cyan-500/20 hover:border-cyan-400 hover:bg-cyan-900/20 shadow-[0_4px_20px_rgba(0,0,0,0.3)] hover:shadow-[0_0_20px_rgba(34,211,238,0.3)] rounded-2xl p-5 transition-all duration-400 hover:-translate-y-1.5 overflow-hidden select-none"
            style={{ WebkitUserSelect: 'none', userSelect: 'none' }}
        >
            {/* Context Menu Overlay */}
            {activeMenu === file.id && (
                <div
                    onClick={(e) => e.stopPropagation()}
                    className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-[100] min-w-[140px] bg-[#0f172a]/95 backdrop-blur-2xl border border-cyan-500/40 rounded-xl shadow-[0_0_30px_rgba(34,211,238,0.2)] overflow-hidden flex flex-col"
                >
                    <button
                        onClick={() => onTogglePin(file.id, file.isPinned)}
                        className="flex items-center gap-3 px-4 py-3 text-cyan-400 hover:bg-cyan-500/20 transition-colors text-xs font-mono font-bold uppercase"
                    >
                        <Pin size={14} />
                        {file.isPinned ? 'Unpin' : 'Pin'}
                    </button>
                    <button
                        onClick={() => { onDelete(file.id); setActiveMenu(null); }}
                        className="flex items-center gap-3 px-4 py-3 text-rose-400 hover:bg-rose-500/20 hover:text-rose-300 transition-colors text-xs font-mono font-bold uppercase border-t border-white/5"
                    >
                        <Trash2 size={14} />
                        Delete
                    </button>
                </div>
            )}

            {/* Visual Pin Indicator */}
            {file.isPinned && (
                <Pin size={16} className="absolute top-3 right-3 text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.8)] z-20" />
            )}

            {/* Quick Delete Button */}
            <button
                onClick={(e) => { e.stopPropagation(); onDelete(file.id); }}
                className="absolute top-2 right-2 z-20 p-2 bg-red-900/60 hover:bg-red-500 text-red-100 rounded-full opacity-0 group-hover:opacity-100 transition-all shadow-[0_0_15px_rgba(239,68,68,0.3)] backdrop-blur-md border border-red-500/50 hover:scale-110"
            >
                <Trash2 size={14} />
            </button>

            {/* Background Glow */}
            <div className="absolute inset-0 bg-gradient-to-b from-cyan-500/0 via-cyan-500/5 to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

            {/* 3D Canvas Container */}
            <div className="w-full h-32 relative mb-2 flex items-center justify-center">
                {/* Hologram Projector Base */}
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-16 h-2 bg-cyan-500/40 blur-md rounded-[100%] shadow-[0_0_20px_rgba(34,211,238,0.8)] mix-blend-screen group-hover:w-20 group-hover:bg-cyan-400/60 transition-all duration-500 pointer-events-none" />
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-1 bg-white/60 blur-[1px] rounded-[100%] mix-blend-screen group-hover:w-10 transition-all duration-500 pointer-events-none" />

                {/* TRULY TRANSPARENT CANVAS */}
                <Canvas
                    gl={{ alpha: true, antialias: true }}
                    camera={{ position: [0, 0, 3], fov: 50 }}
                    className="absolute inset-0 z-10 pointer-events-none"
                    style={{ background: 'transparent' }}
                >
                    <ambientLight intensity={0.5} color="#ffffff" />
                    <pointLight position={[10, 10, 10]} intensity={1.5} color="#00e5ff" />
                    <pointLight position={[-10, -10, -10]} intensity={0.5} color="#0044ff" />

                    <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
                        {renderModel()}
                    </Float>

                    {/* Post-processing with alpha to keep transparency */}
                    <EffectComposer disableNormalPass alpha={true}>
                        <Bloom
                            luminanceThreshold={0.2}
                            luminanceSmoothing={0.9}
                            intensity={1.5}
                        />
                    </EffectComposer>
                </Canvas>
            </div>

            {/* Meta Data */}
            <h3 className="relative z-10 text-cyan-50 text-sm font-mono font-bold text-center mt-2 line-clamp-2 transition-colors group-hover:text-cyan-300 drop-shadow-md">
                {file.name}
            </h3>
            <p className="relative z-10 text-cyan-500/60 text-[10px] font-mono tracking-widest text-center mt-2 group-hover:text-cyan-400/80 transition-colors uppercase">
                {idx % 3 === 0 ? 'Atom_Core' : idx % 3 === 1 ? 'Genetic_Data' : 'Mol_Structure'} / {String(file.stage).padStart(2, '0')}
            </p>
        </div>
    );
};
