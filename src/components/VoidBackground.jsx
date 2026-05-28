import { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function VoidBackground() {
    const mountRef = useRef(null);

    useEffect(() => {
        if (!mountRef.current) return;

        const bgScene = new THREE.Scene();
        bgScene.background = new THREE.Color(0x030510);
        bgScene.fog = new THREE.FogExp2(0x030510, 0.008);

        const bgCam = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 200);
        bgCam.position.set(0, 0, 22);
        bgCam.lookAt(0, 0, 0);

        const bgRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
        bgRenderer.setSize(window.innerWidth, window.innerHeight);
        bgRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        bgRenderer.toneMapping = THREE.ACESFilmicToneMapping;
        bgRenderer.toneMappingExposure = 1.0;

        mountRef.current.appendChild(bgRenderer.domElement);

        // === FLOATING PARTICLES (subtle purple/cyan star-dust) ===
        const dustCount = 400;
        const dustPositions = new Float32Array(dustCount * 3);
        for (let i = 0; i < dustCount; i++) {
            dustPositions[i * 3] = (Math.random() - 0.5) * 50;
            dustPositions[i * 3 + 1] = (Math.random() - 0.5) * 40;
            dustPositions[i * 3 + 2] = (Math.random() - 0.5) * 40;
        }
        const dustGeo = new THREE.BufferGeometry();
        dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPositions, 3));
        const dustMat = new THREE.PointsMaterial({
            color: 0x8B5CF6, size: 0.05, transparent: true, opacity: 0.4,
            blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true,
        });
        const points = new THREE.Points(dustGeo, dustMat);
        bgScene.add(points);

        // === LIGHTING (subtle ambient glow) ===
        bgScene.add(new THREE.AmbientLight(0x0a0515, 0.4));

        // === ANIMATION (particle drift + breathing light) ===
        let animationFrameId;

        function animateVoid(timeMs) {
            animationFrameId = requestAnimationFrame(animateVoid);
            const t = (timeMs || performance.now()) * 0.001;

            // Dust subtle drift
            const pArr = dustGeo.attributes.position.array;
            for (let i = 0; i < dustCount; i++) {
                pArr[i * 3 + 1] += Math.sin(t * 0.3 + i * 0.1) * 0.002;
                pArr[i * 3] += Math.cos(t * 0.2 + i * 0.2) * 0.001;
            }
            dustGeo.attributes.position.needsUpdate = true;

            bgRenderer.render(bgScene, bgCam);
        }
        animateVoid(performance.now());

        const handleResize = () => {
            bgRenderer.setSize(window.innerWidth, window.innerHeight);
            bgCam.aspect = window.innerWidth / window.innerHeight;
            bgCam.updateProjectionMatrix();
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrameId);
            if (mountRef.current && bgRenderer.domElement) {
                mountRef.current.removeChild(bgRenderer.domElement);
            }
            bgRenderer.dispose();
            dustGeo.dispose();
            dustMat.dispose();
        };
    }, []);

    return (
        <div className="absolute inset-0 w-full h-full -z-20 pointer-events-none overflow-hidden">
            {/* The 3D Particles Layer */}
            <div ref={mountRef} className="absolute inset-0 w-full h-full pointer-events-none z-10" />

            {/* The Dynamic Green DNA Holographic Layer */}
            <div className="absolute inset-0 z-0 opacity-25 mix-blend-screen blur-[2px] flex items-center justify-center pointer-events-none">
                <style>
                    {`
                        @keyframes verticalDrift {
                            0% { transform: translateY(-5%) scale(1.1); opacity: 0.15; }
                            50% { transform: translateY(0%) scale(1.1); opacity: 0.25; }
                            100% { transform: translateY(-5%) scale(1.1); opacity: 0.15; }
                        }
                    `}
                </style>
                {/* SVG representation of an intricate DNA helix that drifts slowly */}
                <svg
                    viewBox="0 0 800 1200"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-full h-[120%] object-cover text-green-500 drop-shadow-[0_0_20px_#22c55e]"
                    style={{ animation: 'verticalDrift 15s ease-in-out infinite' }}
                >
                    <path
                        d="M200,0 C300,300 600,300 600,600 C600,900 300,900 200,1200 M600,0 C500,300 200,300 200,600 C200,900 500,900 600,1200"
                        stroke="currentColor"
                        strokeWidth="8"
                        strokeOpacity="0.4"
                    />
                    <path
                        d="M200,0 C300,300 600,300 600,600 C600,900 300,900 200,1200 M600,0 C500,300 200,300 200,600 C200,900 500,900 600,1200"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeDasharray="4 8"
                    />
                    {/* Cross-links (Base pairs) */}
                    {[...Array(20)].map((_, i) => {
                        const y = (i + 1) * 55;
                        const t = y / 1200;
                        const factor = Math.sin(t * Math.PI * 2);
                        const x1 = 400 - (factor * 200);
                        const x2 = 400 + (factor * 200);
                        return (
                            <line
                                key={i}
                                x1={x1} y1={y} x2={x2} y2={y}
                                stroke="currentColor"
                                strokeWidth="3"
                                strokeOpacity={0.6}
                                strokeLinecap="round"
                            />
                        );
                    })}
                </svg>
            </div>

            {/* Radiant 3D Holographic Microscopic Elements */}
            <div className="absolute inset-0 -z-10 pointer-events-none overflow-hidden">
                <style>
                    {`
                        @keyframes floatHolo1 {
                            0%, 100% { transform: translate(0, 0) rotate(0deg) scale(1.1); opacity: 0.15; }
                            33% { transform: translate(30px, -50px) rotate(45deg) scale(1.2); opacity: 0.25; filter: drop-shadow(0 0 20px rgba(0,242,255,0.8)); }
                            66% { transform: translate(-20px, 40px) rotate(90deg) scale(1.0); opacity: 0.1; filter: drop-shadow(0 0 10px rgba(0,242,255,0.4)); }
                        }
                        @keyframes floatHolo2 {
                            0%, 100% { transform: translate(0, 0) rotate(0deg) scale(0.8); opacity: 0.1; }
                            50% { transform: translate(-40px, -30px) rotate(-30deg) scale(0.9); opacity: 0.2; filter: drop-shadow(0 0 25px rgba(168,85,247,0.7)); }
                        }
                        @keyframes floatHolo3 {
                            0%, 100% { transform: translate(0, 0) scale(1.5); opacity: 0.05; }
                            50% { transform: translate(20px, 60px) scale(1.6); opacity: 0.15; filter: drop-shadow(0 0 30px rgba(16,185,129,0.5)); }
                        }
                    `}
                </style>

                {/* Foreground (Fast, Blurred heavily) */}
                <div className="absolute top-[10%] left-[15%] w-32 h-32 rounded-full border-4 border-cyan-500 border-dashed opacity-10 blur-[6px] shadow-[0_0_30px_#00f2ff]" style={{ animation: 'floatHolo1 18s ease-in-out infinite' }}></div>
                <div className="absolute bottom-[20%] right-[10%] w-48 h-48 rounded-full border border-purple-500 opacity-20 blur-sm shadow-[inset_0_0_20px_#a855f7]" style={{ animation: 'floatHolo2 22s ease-in-out infinite reverse' }}></div>

                {/* Midground (Medium speed, sharp edges) */}
                <div className="absolute top-[40%] right-[25%] w-16 h-16 rounded-full border-2 border-green-400 opacity-20 blur-[1px] shadow-[0_0_15px_#22c55e]" style={{ animation: 'floatHolo3 15s ease-in-out infinite' }}>
                    <div className="absolute inset-2 border border-green-300 rounded-full animate-ping" style={{ animationDuration: '4s' }}></div>
                </div>
                <div className="absolute bottom-[35%] left-[20%] w-20 h-20 rounded-full bg-cyan-500/10 border border-cyan-400 opacity-25 blur-[2px] shadow-[0_0_20px_#00f2ff,inset_0_0_10px_#00f2ff]" style={{ animation: 'floatHolo1 25s ease-in-out infinite 2s' }}>
                    <div className="w-full h-full border border-dashed border-cyan-300 rounded-full animate-[spin_10s_linear_infinite]"></div>
                </div>

                {/* Background Depth (Slow, tiny, dim) */}
                <div className="absolute top-[70%] left-[40%] w-8 h-8 rounded-full bg-purple-500/20 blur-[1px] shadow-[0_0_10px_#a855f7]" style={{ animation: 'floatHolo2 30s ease-in-out infinite 5s' }}></div>
                <div className="absolute top-[25%] left-[60%] w-12 h-12 rounded-full border border-dotted border-green-500 opacity-15 blur-[3px]" style={{ animation: 'floatHolo3 28s ease-in-out infinite 1s' }}></div>
                <div className="absolute bottom-[10%] left-[60%] w-6 h-6 rounded-full bg-cyan-400/30 blur-[2px] shadow-[0_0_12px_#00f2ff]" style={{ animation: 'floatHolo1 20s ease-in-out infinite 4s' }}></div>
            </div>
        </div>
    );
}
