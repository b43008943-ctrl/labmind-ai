import { useState, useEffect, useMemo } from 'react';
import { Microscope } from 'lucide-react';
import VoidBackground from '../components/VoidBackground';

/* ================================================================
   MAXIMUM OVERDRIVE — CINEMATIC MICROSCOPIC PARTICLE SYSTEM
   50 elements across 3 extreme parallax layers + vignette
   ================================================================ */

function OverdriveMicroscopicBG() {
    const { deepBG, midGlow, foreBokeh, keyframesCSS } = useMemo(() => {
        const deep = []; // 15 elements — abyss nodes
        const mid = [];  // 20 elements — sharp bioluminescence
        const fore = []; // 15 elements — massive lens-blur blobs
        let css = '';

        // --- DEEP BACKGROUND: Dense web of connecting nodes ---
        for (let i = 0; i < 15; i++) {
            const id = `d${i}`;
            const s = {
                id, x: Math.random() * 100, y: Math.random() * 100,
                size: 4 + Math.random() * 12,
                dur: 30 + Math.random() * 40,
                delay: -(Math.random() * 50),
                dx: -20 + Math.random() * 40, dy: -20 + Math.random() * 40,
                rot: Math.random() * 360,
                hasLine: i < 10,
                lineAngle: Math.random() * 360,
                lineLen: 40 + Math.random() * 80,
            };
            deep.push(s);
            css += `@keyframes mv-${id}{0%,100%{transform:translate(0,0) rotate(${s.rot}deg)}50%{transform:translate(${s.dx}px,${s.dy}px) rotate(${s.rot + 60}deg)}}`;
        }

        // --- MIDGROUND: Sharp Neon Cyan / Electric Blue structures ---
        for (let i = 0; i < 20; i++) {
            const id = `m${i}`;
            const kind = i < 5 ? 'nucleus' : i < 10 ? 'helix' : 'spark';
            const s = {
                id, kind,
                x: Math.random() * 110 - 5, y: Math.random() * 110 - 5,
                size: kind === 'nucleus' ? 20 + Math.random() * 35
                    : kind === 'helix' ? 30 + Math.random() * 60
                        : 2 + Math.random() * 4,
                dur: 10 + Math.random() * 20,
                pDur: 2 + Math.random() * 3,
                delay: -(Math.random() * 25),
                dx: -50 + Math.random() * 100, dy: -40 + Math.random() * 80,
                rot: Math.random() * 360,
                opBase: kind === 'spark' ? 0.5 + Math.random() * 0.5 : 0.3 + Math.random() * 0.4,
            };
            mid.push(s);
            css += `@keyframes mv-${id}{0%,100%{transform:translate(0,0) rotate(${s.rot}deg)}33%{transform:translate(${s.dx * 0.7}px,${s.dy}px) rotate(${s.rot + 90}deg)}66%{transform:translate(${s.dx}px,${s.dy * 0.4}px) rotate(${s.rot - 45}deg)}}`;
            css += `@keyframes pl-${id}{0%,100%{opacity:${s.opBase * 0.3}}50%{opacity:${s.opBase}}}`;
        }

        // --- FOREGROUND: Massive aggressive bokeh cells ---
        for (let i = 0; i < 15; i++) {
            const id = `f${i}`;
            const isCell = i < 10;
            const s = {
                id, isCell,
                x: Math.random() * 140 - 20, y: Math.random() * 140 - 20,
                size: isCell ? 150 + Math.random() * 350 : 200 + Math.random() * 300,
                dur: 8 + Math.random() * 18,
                delay: -(Math.random() * 15),
                dx: -80 + Math.random() * 160, dy: -60 + Math.random() * 120,
                rot: Math.random() * 360,
                opacity: 0.08 + Math.random() * 0.15,
            };
            fore.push(s);
            css += `@keyframes mv-${id}{0%,100%{transform:translate(0,0) rotate(${s.rot}deg) scale(1)}25%{transform:translate(${s.dx * 0.5}px,${s.dy}px) rotate(${s.rot + 30}deg) scale(1.05)}50%{transform:translate(${s.dx}px,${s.dy * 0.3}px) rotate(${s.rot + 60}deg) scale(0.95)}75%{transform:translate(${s.dx * 0.3}px,${s.dy * 0.8}px) rotate(${s.rot + 90}deg) scale(1.02)}}`;
        }

        return { deepBG: deep, midGlow: mid, foreBokeh: fore, keyframesCSS: css };
    }, []);

    return (
        <>
            <style>{keyframesCSS}</style>

            {/* ===== LAYER 1: ABYSS — Deep-space node web (z-0) ===== */}
            <div className="absolute inset-0 z-0 pointer-events-none overflow-hidden" style={{ background: '#020617' }}>
                {/* Dense dark grid */}
                <div className="absolute inset-0 opacity-[0.08]" style={{
                    backgroundImage: `
                        linear-gradient(rgba(56,189,248,0.4) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(56,189,248,0.4) 1px, transparent 1px),
                        linear-gradient(rgba(99,102,241,0.2) 1px, transparent 1px),
                        linear-gradient(90deg, rgba(99,102,241,0.2) 1px, transparent 1px)
                    `,
                    backgroundSize: '80px 80px, 80px 80px, 20px 20px, 20px 20px',
                    animation: 'abyss-crawl 80s linear infinite',
                }} />
                <style>{`@keyframes abyss-crawl{0%{background-position:0 0}100%{background-position:80px 80px}}`}</style>

                {deepBG.map(s => (
                    <div key={s.id} style={{ position: 'absolute', left: `${s.x}%`, top: `${s.y}%` }}>
                        {/* Node dot */}
                        <div style={{
                            width: s.size, height: s.size, borderRadius: '50%',
                            background: 'radial-gradient(circle, rgba(56,189,248,0.5) 0%, rgba(99,102,241,0.2) 60%, transparent 100%)',
                            boxShadow: '0 0 8px 2px rgba(56,189,248,0.3)',
                            animation: `mv-${s.id} ${s.dur}s ease-in-out ${s.delay}s infinite`,
                        }} />
                        {/* Connecting neural line */}
                        {s.hasLine && <div style={{
                            position: 'absolute', top: '50%', left: '50%',
                            width: s.lineLen, height: 1,
                            background: 'linear-gradient(90deg, rgba(56,189,248,0.3), transparent)',
                            transformOrigin: '0 0', transform: `rotate(${s.lineAngle}deg)`,
                            opacity: 0.4,
                        }} />}
                    </div>
                ))}
            </div>

            {/* ===== LAYER 2: SHARP BIOLUMINESCENCE (z-[5], mix-blend-screen) ===== */}
            <div className="absolute inset-0 z-5 pointer-events-none overflow-hidden" style={{ mixBlendMode: 'screen' }}>
                {midGlow.map(s => {
                    const anim = `mv-${s.id} ${s.dur}s ease-in-out ${s.delay}s infinite, pl-${s.id} ${s.pDur}s ease-in-out infinite alternate`;

                    if (s.kind === 'nucleus') {
                        // Piercing glowing nucleus
                        return (
                            <div key={s.id} style={{
                                position: 'absolute', left: `${s.x}%`, top: `${s.y}%`,
                                width: s.size, height: s.size, borderRadius: '50%',
                                background: 'radial-gradient(circle, #06b6d4 0%, rgba(6,182,212,0.4) 40%, transparent 70%)',
                                boxShadow: '0 0 30px 10px rgba(6,182,212,0.6), 0 0 60px 20px rgba(6,182,212,0.2)',
                                animation: anim,
                            }} />
                        );
                    }
                    if (s.kind === 'helix') {
                        // DNA helix / tech-node connector
                        return (
                            <div key={s.id} style={{
                                position: 'absolute', left: `${s.x}%`, top: `${s.y}%`,
                                width: s.size, height: s.size * 0.3,
                                animation: anim,
                            }}>
                                {/* Double helix lines */}
                                <div style={{
                                    position: 'absolute', inset: 0,
                                    borderTop: '1.5px solid rgba(34,211,238,0.7)',
                                    borderBottom: '1.5px solid rgba(6,182,212,0.7)',
                                    borderRadius: '50%',
                                    boxShadow: '0 0 15px 3px rgba(34,211,238,0.4)',
                                }} />
                                {/* End nodes */}
                                <div style={{ position: 'absolute', left: 0, top: '50%', transform: 'translateY(-50%)', width: 5, height: 5, borderRadius: '50%', background: '#22d3ee', boxShadow: '0 0 10px 3px rgba(34,211,238,0.8)' }} />
                                <div style={{ position: 'absolute', right: 0, top: '50%', transform: 'translateY(-50%)', width: 5, height: 5, borderRadius: '50%', background: '#06b6d4', boxShadow: '0 0 10px 3px rgba(6,182,212,0.8)' }} />
                            </div>
                        );
                    }
                    // Sparks — tiny piercing particles
                    return (
                        <div key={s.id} style={{
                            position: 'absolute', left: `${s.x}%`, top: `${s.y}%`,
                            width: s.size, height: s.size, borderRadius: '50%',
                            background: '#fff',
                            boxShadow: '0 0 6px 2px rgba(6,182,212,1), 0 0 20px 6px rgba(34,211,238,0.6)',
                            animation: anim,
                        }} />
                    );
                })}
            </div>

            {/* ===== LAYER 3: FOREGROUND BOKEH — Massive aggressive lens-blur cells (z-[10]) ===== */}
            <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden">
                {foreBokeh.map(s => {
                    if (s.isCell) {
                        // Giant blood-cell-like biconcave disc sweeping over lens
                        return (
                            <div key={s.id} style={{
                                position: 'absolute', left: `${s.x}%`, top: `${s.y}%`,
                                width: s.size, height: s.size, borderRadius: '50%',
                                background: `radial-gradient(circle, rgba(2,6,23,0.7) 20%, rgba(34,211,238,${s.opacity * 3}) 45%, rgba(6,182,212,${s.opacity * 1.5}) 65%, transparent 100%)`,
                                filter: `blur(${s.size * 0.12}px)`,
                                opacity: s.opacity,
                                animation: `mv-${s.id} ${s.dur}s ease-in-out ${s.delay}s infinite`,
                            }} />
                        );
                    }
                    // Deep indigo macro-blob
                    return (
                        <div key={s.id} style={{
                            position: 'absolute', left: `${s.x}%`, top: `${s.y}%`,
                            width: s.size, height: s.size, borderRadius: '50%',
                            background: `radial-gradient(circle, rgba(67,56,202,${s.opacity * 3.5}) 0%, rgba(99,102,241,${s.opacity * 1.5}) 40%, transparent 80%)`,
                            filter: `blur(${s.size * 0.15}px)`,
                            opacity: s.opacity,
                            animation: `mv-${s.id} ${s.dur}s ease-in-out ${s.delay}s infinite`,
                        }} />
                    );
                })}
            </div>

            {/* ===== VIGNETTE OVERLAY — Brutal edge darkening + center spotlight ===== */}
            <div className="absolute inset-0 z-15 pointer-events-none" style={{
                background: 'radial-gradient(ellipse at 50% 50%, transparent 25%, rgba(2,6,23,0.4) 55%, rgba(2,6,23,0.85) 80%, #020617 100%)',
            }} />
        </>
    );
}

/* ================================================================
   MAIN SPLASH SCREEN — UI FORTRESS AT z-50
   ================================================================ */
export default function SplashScreen({ onStart }) {
    const [screenState, setScreenState] = useState('screen-transition-hidden');
    const [isStarting, setIsStarting] = useState(false);

    useEffect(() => {
        const t = setTimeout(() => setScreenState('screen-visible'), 50);
        return () => clearTimeout(t);
    }, []);

    const handleStart = () => {
        if (isStarting) return;
        setIsStarting(true);
        setTimeout(() => {
            setScreenState('screen-exit');
            setTimeout(() => onStart(), 500);
        }, 400);
    };

    return (
        <div id="splash-screen" className={`absolute inset-0 z-20 ${screenState}`}>
            <VoidBackground />

            {/* MAXIMUM OVERDRIVE Microscopic Particle System */}
            <OverdriveMicroscopicBG />

            {/* ===== IMMOVABLE UI FORTRESS — z-50, above ALL chaos ===== */}
            <div className="flex flex-col items-center justify-between w-full max-w-md mx-auto px-4 py-12 min-h-screen z-50 relative">

                {/* Monolithic Titanium "SMART ANALYST" */}
                <div className="w-full max-w-7xl mx-auto flex flex-col items-center justify-center mt-8 text-center drop-shadow-[0_0_20px_rgba(34,211,238,0.8)]">
                    <h1 className="text-center font-black leading-none tracking-tight flex flex-col items-center justify-center w-full uppercase text-transparent bg-clip-text bg-linear-to-b from-[#b5f5ec] via-[#22d3ee] to-[#0891b2] drop-shadow-[0_0_30px_rgba(34,211,238,1)]">
                        <span className="block whitespace-nowrap text-5xl sm:text-7xl md:text-8xl lg:text-9xl">SMART</span>
                        <span className="block whitespace-nowrap text-5xl sm:text-7xl md:text-8xl lg:text-9xl text-cyan-400">ANALYST</span>
                    </h1>
                    <p className="mt-4 text-xs text-cyan-400 tracking-widest uppercase font-medium drop-shadow-[0_0_8px_rgba(34,211,238,0.8)]">
                        Clinical Diagnostic Intelligence
                    </p>
                </div>

                {/* Premium Frosted Glass Lens */}
                <div className="relative flex items-center justify-center my-8">
                    {/* Glass container */}
                    <div className="relative flex items-center justify-center w-56 h-56 md:w-64 md:h-64 rounded-full bg-[#020617]/50 backdrop-blur-xl border-2 border-cyan-400 shadow-[0_0_60px_rgba(34,211,238,0.8),inset_0_0_40px_rgba(34,211,238,0.3)] animate-[float_5s_ease-in-out_infinite]">

                        {/* Top-edge glass reflection highlight */}
                        <div className="absolute top-0 inset-x-0 h-1/3 rounded-t-full bg-linear-to-b from-cyan-300/20 to-transparent pointer-events-none"></div>

                        {/* Inner radiant cyan glow */}
                        <div className="absolute inset-px rounded-full pointer-events-none" style={{ boxShadow: 'inset 0 0 50px rgba(34,211,238,0.8), inset 0 2px 10px rgba(255,255,255,0.4)' }}></div>

                        {/* Microscope Icon — White Center, Cyan Aura */}
                        <Microscope
                            size={100}
                            className="text-white relative z-10"
                            strokeWidth={1.5}
                            style={{ filter: 'drop-shadow(0px 0px 30px rgba(34,211,238,1)) drop-shadow(0px 0px 10px rgba(255,255,255,0.8))' }}
                        />
                    </div>

                    {/* Soft floor reflection under the glass */}
                    <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 w-48 h-12 bg-slate-500/5 rounded-[100%] blur-2xl pointer-events-none"></div>
                </div>

                {/* Start Button — Delayed Press Physics */}
                <div className="w-full space-y-4 mb-8">
                    <button
                        onClick={handleStart}
                        className={`group relative w-full h-16 bg-[#020617]/80 backdrop-blur-md border border-cyan-500/50 rounded-2xl flex items-center justify-center overflow-hidden cursor-pointer shadow-[0_0_30px_rgba(34,211,238,0.5)] ${isStarting ? 'scale-90 bg-cyan-900 border-cyan-400' : 'hover:scale-105 active:scale-95 hover:border-cyan-300 hover:bg-cyan-950/40 hover:shadow-[0_0_50px_rgba(34,211,238,0.8)]'} transition-all duration-300 ease-out`}
                    >
                        <div className="absolute inset-0 bg-linear-to-r from-transparent via-white/4 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out"></div>
                        <div className="absolute top-0 left-4 right-4 h-px bg-linear-to-r from-transparent via-slate-500/30 to-transparent"></div>
                        <span className="text-sm font-semibold tracking-[0.25em] text-slate-300 group-hover:text-white transition-colors z-10 uppercase">
                            Initialize System
                        </span>
                    </button>
                    <p className="text-xs text-center text-slate-600 font-medium tracking-widest uppercase">Biometric Security Active</p>
                </div>
            </div>
        </div>
    );
}
