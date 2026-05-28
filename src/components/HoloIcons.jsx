import React from 'react';
import { FileHeart, Dna, BookOpen, Gauge, Plus, Activity, Zap } from 'lucide-react';

const commonStyles = `
@keyframes holoFloat {
    0%, 100% { transform: translateY(0) scale(1.05); }
    50% { transform: translateY(-4px) scale(1.05); }
}
@keyframes holoPulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 0.8; }
}
@keyframes holoScan {
    0% { transform: translateY(-100%); opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { transform: translateY(100%); opacity: 0; }
}
@keyframes ringSpin {
    0% { transform: rotate(0deg) scale(1); }
    50% { transform: rotate(180deg) scale(1.05); }
    100% { transform: rotate(360deg) scale(1); }
}
`;

export const HoloFileHeart = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-500">
        <style>{commonStyles}</style>
        {/* Hologram Projector Base */}
        <div className="absolute bottom-1 w-[80%] h-[15%] bg-cyan-400/40 rounded-[50%] blur-[3px] shadow-[0_0_15px_#00f2ff]"></div>
        {/* Hologram Beam */}
        <div className="absolute bottom-1 w-[70%] h-[90%] bg-linear-to-t from-cyan-400/30 to-transparent blur-[1px]" style={{ clipPath: 'polygon(20% 100%, 80% 100%, 100% 0, 0 0)' }}></div>

        {/* Main 3D Composition */}
        <div className="relative w-full h-full flex items-center justify-center" style={{ animation: 'holoFloat 3s ease-in-out infinite' }}>
            {/* File Layers */}
            <FileHeart className="absolute w-10 h-10 text-cyan-600/50 -translate-z-4 translate-y-1 scale-95 blur-[1px]" strokeWidth={1.5} />
            <FileHeart className="absolute w-10 h-10 text-cyan-400/80 -translate-z-2 translate-y-0.5 scale-[0.98]" strokeWidth={1.5} />
            <FileHeart className="relative w-10 h-10 text-cyan-100 drop-shadow-[0_0_10px_#00f2ff]" strokeWidth={2} />

            {/* Floating Details */}
            <div className="absolute inset-0 flex items-center justify-center">
                <div className="absolute w-[30%] h-[30%] rounded-full bg-cyan-300/40 animate-ping" style={{ animationDuration: '2s' }}></div>
            </div>

            <Plus className="absolute top-1 right-2 w-3 h-3 text-cyan-200 animate-[spin_4s_linear_infinite] drop-shadow-[0_0_5px_currentColor]" />
        </div>

        <div className="absolute inset-0 overflow-hidden rounded-xl">
            <div className="w-full h-0.5 bg-cyan-200/60 shadow-[0_0_8px_#00f2ff]" style={{ animation: 'holoScan 2s linear infinite' }}></div>
        </div>
    </div>
);

export const HoloDna = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-500 group-hover:scale-110 transition-transform duration-500">
        <style>{commonStyles}</style>
        <div className="absolute bottom-1 w-[80%] h-[15%] bg-orange-500/40 rounded-[50%] blur-[3px] shadow-[0_0_15px_#f97316]"></div>
        <div className="absolute bottom-1 w-[70%] h-[90%] bg-linear-to-t from-orange-500/30 to-transparent blur-[1px]" style={{ clipPath: 'polygon(20% 100%, 80% 100%, 100% 0, 0 0)' }}></div>

        <div className="relative w-full h-full flex items-center justify-center" style={{ animation: 'holoFloat 3.5s ease-in-out infinite' }}>
            {/* DNA Strands */}
            <Dna className="absolute w-11 h-11 text-orange-600/50 -translate-z-4 translate-x-1 scale-95 blur-[1px]" />
            <Dna className="absolute w-11 h-11 text-orange-400/80 -translate-z-2 translate-x-0.5 scale-[0.98]" />
            <Dna className="relative w-11 h-11 text-orange-200 drop-shadow-[0_0_10px_#f97316]" strokeWidth={1.5} style={{ animation: 'spin 8s linear infinite' }} />

            {/* Outer rings simulating cellular structure */}
            <div className="absolute w-[80%] h-[80%] rounded-full border border-orange-500/30 border-dashed" style={{ animation: 'ringSpin 10s linear infinite' }}></div>
            <div className="absolute w-[95%] h-[95%] rounded-full border border-orange-400/20 border-dotted" style={{ animation: 'ringSpin 15s linear infinite reverse' }}></div>

            {/* Microscopic particles */}
            <div className="absolute top-2 left-2 w-1 h-1 rounded-full bg-orange-300 shadow-[0_0_6px_#f97316]" style={{ animation: 'holoPulse 1.2s infinite alternate' }}></div>
            <div className="absolute bottom-2 right-1 w-1.5 h-1.5 rounded-full bg-yellow-300 shadow-[0_0_6px_#fde047]" style={{ animation: 'holoPulse 1.8s infinite alternate' }}></div>
        </div>

        <div className="absolute inset-0 overflow-hidden rounded-xl">
            <div className="w-full h-0.5 bg-orange-200/60 shadow-[0_0_8px_#f97316]" style={{ animation: 'holoScan 2.5s linear infinite 0.5s' }}></div>
        </div>
    </div>
);

export const HoloBookOpen = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-500 group-hover:scale-110 transition-transform duration-500">
        <style>{commonStyles}</style>
        <div className="absolute bottom-1 w-[80%] h-[15%] bg-green-500/40 rounded-[50%] blur-[3px] shadow-[0_0_15px_#22c55e]"></div>
        <div className="absolute bottom-1 w-[70%] h-[90%] bg-linear-to-t from-green-500/30 to-transparent blur-[1px]" style={{ clipPath: 'polygon(20% 100%, 80% 100%, 100% 0, 0 0)' }}></div>

        <div className="relative w-full h-full flex items-center justify-center" style={{ animation: 'holoFloat 4s ease-in-out infinite' }}>
            {/* Holographic Book Base */}
            <BookOpen className="absolute w-10 h-10 text-green-700/50 -translate-z-4 translate-y-1 scale-95 blur-[1px]" />
            <BookOpen className="absolute w-10 h-10 text-green-400/80 -translate-z-2 translate-y-0.5 scale-[0.98]" />
            <BookOpen className="relative w-10 h-10 text-green-200 drop-shadow-[0_0_10px_#22c55e]" strokeWidth={1.5} />

            {/* Page details via absolute div slices */}
            <div className="absolute w-3 h-0.5 bg-green-300/60 rounded-full top-[40%] right-[30%] drop-shadow-[0_0_2px_#22c55e]"></div>
            <div className="absolute w-2 h-0.5 bg-green-300/60 rounded-full top-[50%] right-[35%] drop-shadow-[0_0_2px_#22c55e]"></div>

            {/* Floating medical symbols over book */}
            <Activity className="absolute -top-1 -left-1 w-3.5 h-3.5 text-green-200 drop-shadow-[0_0_5px_currentColor]" style={{ animation: 'holoFloat 2s ease-in-out infinite reverse' }} />
            <Plus className="absolute -top-2 right-0 w-3 h-3 text-green-300 drop-shadow-[0_0_5px_currentColor]" style={{ animation: 'holoFloat 2.5s ease-in-out infinite' }} />

            {/* Knowledge Aura */}
            <div className="absolute w-[120%] h-[120%] rounded-full bg-[radial-gradient(circle,rgba(34,197,94,0.1)_0%,transparent_70%)] animate-pulse"></div>
        </div>

        <div className="absolute inset-0 overflow-hidden rounded-xl">
            <div className="w-full h-0.5 bg-green-200/60 shadow-[0_0_8px_#22c55e]" style={{ animation: 'holoScan 3s linear infinite 0.2s' }}></div>
        </div>
    </div>
);

export const HoloGauge = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-500 group-hover:scale-110 transition-transform duration-500">
        <style>{commonStyles}</style>
        <div className="absolute bottom-1 w-[80%] h-[15%] bg-purple-500/40 rounded-[50%] blur-[3px] shadow-[0_0_15px_#a855f7]"></div>
        <div className="absolute bottom-1 w-[70%] h-[90%] bg-linear-to-t from-purple-500/30 to-transparent blur-[1px]" style={{ clipPath: 'polygon(20% 100%, 80% 100%, 100% 0, 0 0)' }}></div>

        <div className="relative w-full h-full flex items-center justify-center" style={{ animation: 'holoFloat 2.8s ease-in-out infinite' }}>
            {/* Glowing gauge outlines */}
            <Gauge className="absolute w-10 h-10 text-purple-700/50 -translate-z-4 translate-y-1 scale-95 blur-[1px]" />
            <Gauge className="absolute w-10 h-10 text-purple-400/80 -translate-z-2 translate-y-0.5 scale-[0.98]" />

            <div className="relative grid place-items-center">
                <Gauge className="relative w-11 h-11 text-purple-200 drop-shadow-[0_0_10px_#a855f7]" strokeWidth={1.5} />

                {/* 3D Gauge Core & Moving needle */}
                <div className="absolute w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_8px_#fff,0_0_15px_#a855f7] z-20"></div>

                {/* Simulated needle sweep via rotating linear gradient or raw div */}
                <div className="absolute inset-x-[48%] bottom-[50%] h-[35%] w-[4%] bg-purple-100 rounded-full origin-bottom shadow-[0_0_5px_#fff]" style={{ animation: 'spin 3s ease-in-out infinite alternate' }}></div>
            </div>

            {/* Precision data points orbiting */}
            <div className="absolute inset-[-10%] border border-purple-500/20 rounded-full border-dashed" style={{ animation: 'ringSpin 8s linear infinite reverse' }}>
                <div className="absolute top-0 right-1 w-1.5 h-1.5 bg-purple-300 rounded-full shadow-[0_0_6px_#a855f7]"></div>
            </div>
            <div className="absolute inset-[-20%] border border-purple-400/10 rounded-full border-dotted" style={{ animation: 'ringSpin 12s linear infinite' }}>
                <div className="absolute bottom-1 left-2 w-1 h-1 bg-fuchsia-300 rounded-full shadow-[0_0_5px_#d946ef]"></div>
            </div>
        </div>

        <div className="absolute inset-0 overflow-hidden rounded-xl">
            <div className="w-full h-0.5 bg-purple-200/60 shadow-[0_0_8px_#a855f7]" style={{ animation: 'holoScan 2.2s linear infinite 0.8s' }}></div>
        </div>
    </div>
);

export const HoloHematology = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-500 group-hover:scale-110 transition-transform duration-500">
        <style>{commonStyles}</style>
        <div className="absolute bottom-1 w-[80%] h-[15%] bg-rose-500/40 rounded-[50%] blur-[3px] shadow-[0_0_15px_#f43f5e]"></div>
        <div className="absolute bottom-1 w-[70%] h-[90%] bg-linear-to-t from-rose-500/30 to-transparent blur-[1px]" style={{ clipPath: 'polygon(20% 100%, 80% 100%, 100% 0, 0 0)' }}></div>

        <div className="relative w-full h-full flex items-center justify-center scale-[0.6]" style={{ animation: 'holoFloat 3.2s ease-in-out infinite' }}>
            {/* Hyper-Realistic 3D Microscope */}
            <div className="relative w-12 h-16 flex flex-col items-center">
                {/* Eyepiece */}
                <div className="w-3 h-3 border border-slate-300 bg-slate-100 rounded-t-sm shadow-[0_0_5px_#fff]"></div>
                {/* Arm/Body (Metallic Chrome) */}
                <svg className="absolute top-1 right-2 w-8 h-12 text-slate-300 drop-shadow-[0_2px_5px_rgba(255,255,255,0.5)] opacity-100" viewBox="0 0 24 24" fill="url(#chrome-gradient)" stroke="currentColor" strokeWidth="0.5">
                    <defs>
                        <linearGradient id="chrome-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stopColor="#f8fafc" />
                            <stop offset="30%" stopColor="#94a3b8" />
                            <stop offset="50%" stopColor="#334155" />
                            <stop offset="70%" stopColor="#94a3b8" />
                            <stop offset="100%" stopColor="#f1f5f9" />
                        </linearGradient>
                    </defs>
                    <path d="M14 4 C 18 4, 20 8, 20 12 C 20 16, 18 20, 14 20 L 10 20" />
                </svg>
                {/* Objective Lenses */}
                <div className="absolute top-6 left-1 w-6 h-3 flex gap-1 transform -rotate-15">
                    <div className="w-1.5 h-3 bg-slate-300 rounded-b-sm shadow-[inset_-1px_0_2px_#64748b]"></div>
                    <div className="w-2 h-4 bg-slate-200 rounded-b-sm shadow-[inset_-1px_0_2px_#64748b]"></div>
                </div>
                {/* Stage */}
                <div className="absolute top-10 w-8 h-1.5 bg-slate-700 border-t border-slate-400 rounded-sm shadow-[0_2px_5px_rgba(0,0,0,0.5)]"></div>
                {/* Base */}
                <div className="absolute bottom-0 w-10 h-3 bg-slate-800 border-t border-slate-500 rounded-t-md shadow-[0_3px_8px_rgba(0,0,0,0.8)]"></div>

                {/* Glowing Specimen */}
                <div className="absolute top-9 left-2 w-4 h-1 bg-white/80 box-shadow-[0_0_8px_#fff] animate-pulse">
                    <div className="w-1 h-1 bg-rose-500 rounded-full mx-auto shadow-[0_0_10px_#f43f5e]"></div>
                </div>
            </div>
            {/* Floating data */}
            <Activity className="absolute bottom-4 right-0 w-4 h-4 text-rose-200 drop-shadow-[0_0_5px_#f43f5e]" style={{ animation: 'spin 4s linear infinite' }} />
        </div>
        <div className="absolute inset-0 overflow-hidden rounded-xl">
            <div className="w-full h-0.5 bg-rose-200/60 shadow-[0_0_8px_#f43f5e]" style={{ animation: 'holoScan 2.5s linear infinite 0.3s' }}></div>
        </div>
    </div>
);

export const HoloUrinalysis = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-500 group-hover:scale-110 transition-transform duration-500">
        <style>{commonStyles}</style>
        <div className="absolute bottom-1 w-[80%] h-[15%] bg-yellow-400/40 rounded-[50%] blur-[3px] shadow-[0_0_15px_#facc15]"></div>
        <div className="absolute bottom-1 w-[70%] h-[90%] bg-linear-to-t from-yellow-500/30 to-transparent blur-[1px]" style={{ clipPath: 'polygon(20% 100%, 80% 100%, 100% 0, 0 0)' }}></div>

        <div className="relative w-full h-full flex items-center justify-center scale-[0.6]" style={{ animation: 'holoFloat 3.8s ease-in-out infinite' }}>
            {/* Clear Medical Glass Cup */}
            <div className="relative w-10 h-12 border-x-2 border-b-2 border-white/70 bg-white/10 rounded-b-xl backdrop-blur-md shadow-[inset_0_0_20px_rgba(255,255,255,0.4),0_0_15px_rgba(250,204,21,0.4)] flex items-end overflow-hidden pb-1">
                {/* Cup Rim with threads */}
                <div className="absolute -top-1 -left-1 -right-1 h-2 rounded-[50%] border-y-2 border-white/80 bg-white/30 flex flex-col justify-between shadow-[0_2px_5px_rgba(255,255,255,0.5)]">
                    <div className="w-full h-px bg-white/60"></div>
                </div>
                {/* Fluid Volume with caustic gradient */}
                <div className="relative w-full h-[65%] bg-linear-to-t from-yellow-500/80 to-yellow-200/50 rounded-b-lg border-t border-yellow-100 shadow-[inset_0_8px_15px_rgba(202,138,4,0.8),0_0_10px_rgba(250,204,21,0.5)]">
                    <div className="absolute top-0 w-full h-1 bg-white/60 blur-[1px]"></div>
                    {/* Tiny bubbles */}
                    <div className="absolute bottom-1 left-2 w-1 h-1 bg-yellow-100 rounded-full animate-ping"></div>
                    <div className="absolute bottom-2 right-2 w-1.5 h-1.5 bg-white rounded-full opacity-70"></div>
                </div>
            </div>

            {/* HD Floating Dipstick */}
            <div className="absolute w-2.5 h-14 border border-white/60 bg-white/20 backdrop-blur-md rounded-sm shadow-[0_0_10px_#fff,inset_1px_0_2px_#fff] flex flex-col justify-end pb-1.5 items-center gap-px" style={{ transform: 'rotate(12deg) translate(-2px, -6px)', animation: 'holoFloat 2.5s ease-in-out infinite reverse' }}>
                <div className="w-1.5 h-1.5 bg-rose-500 rounded-[1px] shadow-[0_0_3px_#f43f5e]"></div>
                <div className="w-1.5 h-1.5 bg-emerald-400 rounded-[1px] shadow-[0_0_3px_#34d399]"></div>
                <div className="w-1.5 h-1.5 bg-amber-300 rounded-[1px] shadow-[0_0_3px_#fbbf24]"></div>
                <div className="w-1.5 h-1.5 bg-cyan-400 rounded-[1px] shadow-[0_0_3px_#22d3ee]"></div>
            </div>
        </div>
        <div className="absolute inset-0 overflow-hidden rounded-xl">
            <div className="w-full h-0.5 bg-yellow-200/60 shadow-[0_0_8px_#facc15]" style={{ animation: 'holoScan 2.8s linear infinite 0.1s' }}></div>
        </div>
    </div>
);

export const HoloMicrobiology = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-500 group-hover:scale-110 transition-transform duration-500">
        <style>{commonStyles}</style>
        <div className="absolute bottom-1 w-[80%] h-[15%] bg-indigo-500/40 rounded-[50%] blur-[3px] shadow-[0_0_15px_#8b5cf6]"></div>
        <div className="absolute bottom-1 w-[70%] h-[90%] bg-linear-to-t from-indigo-500/30 to-transparent blur-[1px]" style={{ clipPath: 'polygon(20% 100%, 80% 100%, 100% 0, 0 0)' }}></div>

        <div className="relative w-full h-full flex items-center justify-center scale-[0.6]" style={{ animation: 'holoFloat 4.2s ease-in-out infinite' }}>
            {/* Detailed Petri Dish */}
            <div className="absolute w-16 h-8 rounded-[50%] border-2 border-indigo-300/80 bg-indigo-500/20 shadow-[inset_0_0_20px_#6366f1,0_10px_15px_-3px_rgba(99,102,241,0.6)] backdrop-blur-md" style={{ transform: 'rotateX(55deg)' }}>
                {/* Dish Rim reflection */}
                <div className="absolute inset-0 rounded-[50%] border border-white/60"></div>
                {/* Agar Base */}
                <div className="absolute inset-1 rounded-[50%] bg-indigo-900/50 shadow-[inset_0_0_15px_#4338ca]">
                    {/* Organic Texturized Growths */}
                    <div className="absolute top-1 left-2 w-4 h-3 rounded-[50%] shadow-[inset_0_0_4px_#581c87,0_0_8px_#d8b4fe] opacity-95 blur-[0.5px] flex items-center justify-center border border-purple-300/60" style={{ background: 'radial-gradient(circle, #d8b4fe 0%, #9333ea 100%)' }}>
                        <div className="absolute w-1.5 h-1.5 bg-white/70 rounded-full top-0 right-0.5 shadow-[0_0_2px_#fff]"></div>
                        <div className="absolute w-1 h-1 bg-white/50 rounded-full bottom-0.5 left-0.5"></div>
                    </div>
                    <div className="absolute bottom-1 right-1 w-5 h-3 rounded-[50%] shadow-[inset_0_0_5px_#701a75,0_0_10px_#f5d0fe] opacity-90 blur-[0.5px] border border-fuchsia-200/60" style={{ background: 'radial-gradient(circle, #f5d0fe 0%, #c026d3 100%)' }}>
                        <div className="absolute w-2 h-1.5 bg-white/60 rounded-full top-0.5 left-1 transform rotate-45"></div>
                    </div>
                    <div className="absolute top-2 right-4 w-3 h-2 rounded-[50%] shadow-[inset_0_0_3px_#312e81,0_0_6px_#c7d2fe] opacity-95 border border-indigo-100/70" style={{ background: 'radial-gradient(circle, #c7d2fe 0%, #4f46e5 100%)' }}>
                        <div className="absolute w-1 h-1 bg-white/60 rounded-full center"></div>
                    </div>
                </div>
            </div>

            {/* Glowing Viral Spores hovering above */}
            <div className="absolute -top-4" style={{ animation: 'holoFloat 2s ease-in-out infinite reverse' }}>
                <svg className="w-6 h-6 text-purple-200 drop-shadow-[0_0_8px_#d8b4fe]" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="12" r="5" className="animate-pulse" />
                    <circle cx="12" cy="4" r="1.5" />
                    <circle cx="12" cy="20" r="1.5" />
                    <circle cx="4" cy="12" r="1.5" />
                    <circle cx="20" cy="12" r="1.5" />
                    <circle cx="6" cy="6" r="1.5" />
                    <circle cx="18" cy="18" r="1.5" />
                    <circle cx="18" cy="6" r="1.5" />
                    <circle cx="6" cy="18" r="1.5" />
                </svg>
            </div>
        </div>
        <div className="absolute inset-0 overflow-hidden rounded-xl">
            <div className="w-full h-0.5 bg-indigo-200/60 shadow-[0_0_8px_#8b5cf6]" style={{ animation: 'holoScan 3s linear infinite 0.7s' }}></div>
        </div>
    </div>
);

export const HoloClinical = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-500 group-hover:scale-110 transition-transform duration-500">
        <style>{commonStyles}</style>
        <div className="absolute bottom-1 w-[80%] h-[15%] bg-purple-600/40 rounded-[50%] blur-[3px] shadow-[0_0_15px_#9333ea]"></div>
        <div className="absolute bottom-1 w-[70%] h-[90%] bg-linear-to-t from-purple-600/30 to-transparent blur-[1px]" style={{ clipPath: 'polygon(20% 100%, 80% 100%, 100% 0, 0 0)' }}></div>

        <div className="relative w-full h-full flex items-center justify-center scale-[0.6]" style={{ animation: 'holoFloat 3.5s ease-in-out infinite' }}>
            {/* Bio-CPU Chip + Double Helix */}
            <div className="relative w-12 h-12 rounded-lg border-2 border-purple-300 bg-purple-900/60 shadow-[inset_0_0_20px_#7e22ce,0_0_25px_#a855f7] flex items-center justify-center" style={{ transform: 'rotateX(25deg) rotateZ(15deg)' }}>
                {/* Inner Die */}
                <div className="w-6 h-6 rounded-sm border border-fuchsia-300 bg-purple-400/40 shadow-[inset_0_0_10px_#e879f9,0_0_15px_#d8b4fe] flex items-center justify-center overflow-hidden z-10">
                    {/* Double Helix projection inside chip */}
                    <Dna className="w-5 h-5 text-white drop-shadow-[0_0_5px_#fff]" style={{ animation: 'spin 10s linear infinite' }} />
                </div>
                {/* Copper/Gold Circuit Traces */}
                {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="absolute w-3 h-0.5 bg-amber-300 left-[-6px]" style={{ top: `${15 + i * 25}%`, boxShadow: '0 0 6px #f59e0b, 0 0 2px #fff' }}></div>
                ))}
                {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i + 4} className="absolute w-3 h-0.5 bg-amber-300 right-[-6px]" style={{ top: `${15 + i * 25}%`, boxShadow: '0 0 6px #f59e0b, 0 0 2px #fff' }}></div>
                ))}
                {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i + 8} className="absolute h-3 w-0.5 bg-amber-400 top-[-6px]" style={{ left: `${15 + i * 25}%`, boxShadow: '0 0 6px #f59e0b, 0 0 2px #fff' }}></div>
                ))}
                {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i + 12} className="absolute h-3 w-0.5 bg-amber-400 bottom-[-6px]" style={{ left: `${15 + i * 25}%`, boxShadow: '0 0 6px #f59e0b, 0 0 2px #fff' }}></div>
                ))}
            </div>

            {/* Glowing metabolic rings orbiting */}
            <div className="absolute w-20 h-20 border border-amber-400/50 rounded-full" style={{ transform: 'rotateX(60deg)', animation: 'spin 4s linear infinite' }}>
                <div className="absolute top-0 right-2 w-2 h-2 rounded-full bg-amber-200 shadow-[0_0_8px_#fcd34d]"></div>
            </div>
            <div className="absolute w-20 h-20 border border-fuchsia-400/30 rounded-full" style={{ transform: 'rotateX(60deg) rotateY(45deg)', animation: 'spin 6s linear infinite reverse' }}>
                <div className="absolute bottom-0 left-2 w-1.5 h-1.5 rounded-full bg-fuchsia-100 shadow-[0_0_6px_#f5d0fe]"></div>
            </div>
        </div>
        <div className="absolute inset-0 overflow-hidden rounded-xl">
            <div className="w-full h-0.5 bg-purple-200/60 shadow-[0_0_8px_#9333ea]" style={{ animation: 'holoScan 2.4s linear infinite 0.4s' }}></div>
        </div>
    </div>
);

export const HoloParasitology = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-500 group-hover:scale-110 transition-transform duration-500">
        <style>{commonStyles}</style>
        <div className="absolute bottom-1 w-[80%] h-[15%] bg-emerald-500/40 rounded-[50%] blur-[3px] shadow-[0_0_15px_#10b981]"></div>
        <div className="absolute bottom-1 w-[70%] h-[90%] bg-linear-to-t from-emerald-500/30 to-transparent blur-[1px]" style={{ clipPath: 'polygon(20% 100%, 80% 100%, 100% 0, 0 0)' }}></div>

        <div className="relative w-full h-full flex items-center justify-center scale-[0.6]" style={{ animation: 'holoFloat 4.5s ease-in-out infinite' }}>
            {/* HD Parasite Model with Semi-Transparent Membrane */}
            <div className="relative w-16 h-8 border-2 border-emerald-200/70 bg-emerald-500/20 shadow-[inset_0_0_15px_rgba(16,185,129,0.5),0_0_20px_rgba(52,211,153,0.6)] backdrop-blur-md" style={{ borderRadius: '50% 100% 50% 100%', transform: 'rotate(-30deg)', animation: 'holoPulse 3s infinite alternate' }}>
                {/* Thin inner membrane reflection */}
                <div className="absolute inset-0.5 border border-emerald-100/40 rounded-[inherit] mix-blend-overlay"></div>

                {/* Nuclei - High def */}
                <div className="absolute top-1 left-3 w-4 h-3 rounded-full border border-emerald-100 bg-emerald-400/80 shadow-[0_0_8px_#a7f3d0] z-10">
                    <div className="absolute inset-0.5 rounded-full bg-emerald-200 border border-emerald-50"></div>
                </div>

                {/* Flagella Tail - animated SVG */}
                <svg className="absolute top-0 -right-6 w-10 h-8 text-emerald-300 drop-shadow-[0_0_5px_#6ee7b7] z-0">
                    <path d="M0,20 Q10,0 20,15 T40,5" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="animate-[dash_2s_linear_infinite]" style={{ strokeDasharray: '10, 5' }} />
                </svg>

                {/* Internal organelle structures */}
                <div className="absolute bottom-2 right-4 w-2 h-2 rounded-full border border-teal-200 bg-teal-400/60 shadow-[0_0_6px_#5eead4] z-10"></div>
                <div className="absolute top-3 right-5 w-1.5 h-1.5 rounded-full bg-emerald-200 shadow-[0_0_4px_#a7f3d0] z-10"></div>
            </div>

            {/* Environmental 3D Context (Blood stream particles) */}
            <div className="absolute top-[-10px] right-2 w-3 h-3 rounded-[50%] border border-emerald-300/60 bg-emerald-500/20 shadow-[0_0_8px_#34d399]" style={{ transform: 'rotateX(45deg)', animation: 'holoFloat 2s infinite reverse' }}></div>
            <div className="absolute bottom-0 left-[-5px] w-2 h-5 rounded-full border border-teal-300/40 bg-teal-500/10 shadow-[0_0_5px_#2dd4bf]" style={{ transform: 'rotate(45deg)' }}></div>
        </div>
        <div className="absolute inset-0 overflow-hidden rounded-xl">
            <div className="w-full h-0.5 bg-emerald-200/60 shadow-[0_0_8px_#10b981]" style={{ animation: 'holoScan 3.5s linear infinite 0.2s' }}></div>
        </div>
    </div>
);

export const HoloBloodBank = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none perspective-500 group-hover:scale-110 transition-transform duration-500">
        <style>{commonStyles}</style>
        <div className="absolute bottom-1 w-[80%] h-[15%] bg-pink-600/40 rounded-[50%] blur-[3px] shadow-[0_0_15px_#db2777]"></div>
        <div className="absolute bottom-1 w-[70%] h-[90%] bg-linear-to-t from-pink-600/30 to-transparent blur-[1px]" style={{ clipPath: 'polygon(20% 100%, 80% 100%, 100% 0, 0 0)' }}></div>

        <div className="relative w-full h-full flex items-center justify-center scale-[0.6]" style={{ animation: 'holoFloat 3.6s ease-in-out infinite' }}>
            {/* Realistic Blood Bag (Matt Plastic) */}
            <div className="relative w-12 h-16 border-2 border-white/30 rounded-b-xl rounded-t-sm bg-pink-950/60 shadow-[inset_0_0_10px_rgba(255,255,255,0.1),0_4px_15px_rgba(219,39,119,0.5)] backdrop-blur-md flex flex-col items-center">
                {/* Top hang loop */}
                <div className="absolute -top-3 w-4 h-3 border-2 border-white/50 rounded-t-full"></div>
                {/* Ports */}
                <div className="absolute -bottom-2 left-2 w-2 h-3 bg-white/80 border border-white rounded-b-sm shadow-[0_0_5px_#fff]"></div>
                <div className="absolute -bottom-2 right-2 w-2 h-3 bg-white/80 border border-white rounded-b-sm shadow-[0_0_5px_#fff]"></div>

                {/* Dense Blood Volume */}
                <div className="absolute bottom-0 w-full h-[70%] bg-linear-to-t from-red-800 to-red-600 rounded-b-lg border-t border-red-400 shadow-[inset_0_4px_10px_#7f1d1d]">
                    <div className="absolute top-1 left-2 w-3 h-0.5 bg-white/40 rounded-full blur-[0.5px]"></div>
                </div>

                {/* High-Contrast A+ Label */}
                <div className="absolute top-2 w-[85%] h-7 bg-white border-2 border-gray-300 rounded shadow-[0_2px_4px_rgba(0,0,0,0.3)] flex flex-col items-center justify-center overflow-hidden z-10">
                    <div className="w-full h-1 bg-red-600 mb-px"></div>
                    <span className="text-[13px] leading-none font-black text-black tracking-tighter shadow-none mt-px">A+</span>
                </div>
            </div>

            {/* Glowing IV Tubing extending out */}
            <svg className="absolute -bottom-6 left-2 w-8 h-8 overflow-visible text-rose-200 drop-shadow-[0_0_8px_#f43f5e]">
                <path d="M0,0 C 0,10 -10,15 -15,20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>

            {/* Floating Y-Antibodies */}
            <div className="absolute right-[-10px] top-0 text-pink-200 drop-shadow-[0_0_8px_#f9a8d4]" style={{ animation: 'holoFloat 2.5s ease-in-out infinite reverse' }}>
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 22V12M12 12L4 4M12 12l8-8" />
                </svg>
            </div>
        </div>
        <div className="absolute inset-0 overflow-hidden rounded-xl">
            <div className="w-full h-0.5 bg-pink-200/60 shadow-[0_0_8px_#db2777]" style={{ animation: 'holoScan 2.6s linear infinite 0.6s' }}></div>
        </div>
    </div>
);
