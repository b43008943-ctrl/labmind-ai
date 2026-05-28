import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

// Sine-wave path generator
function generateSinePath(width, height, frequency, amplitude, phase, points = 200) {
    const mid = height / 2;
    let d = '';
    for (let i = 0; i <= points; i++) {
        const x = (i / points) * width;
        const y = mid + Math.sin((i / points) * Math.PI * 2 * frequency + phase) * amplitude;
        d += (i === 0 ? 'M' : 'L') + `${x.toFixed(2)},${y.toFixed(2)}`;
    }
    return d;
}

export default function DigitalAnalyzerView({
    activeSample = null,
    isRunning = false,
    progress = 0,
}) {
    const [phase, setPhase] = useState(0);
    const [absorbance, setAbsorbance] = useState(0);

    // Animate the sine wave phase continuously
    useEffect(() => {
        let frame;
        const animate = () => {
            setPhase(prev => prev + 0.03);
            frame = requestAnimationFrame(animate);
        };
        frame = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(frame);
    }, []);

    // Simulate absorbance reading when sample changes
    useEffect(() => {
        if (activeSample) {
            const target = activeSample.absorbance || 0.35;
            let current = 0;
            const interval = setInterval(() => {
                current += (target - current) * 0.08;
                if (Math.abs(current - target) < 0.001) {
                    current = target;
                    clearInterval(interval);
                }
                setAbsorbance(current);
            }, 50);
            return () => clearInterval(interval);
        } else {
            setAbsorbance(0);
        }
    }, [activeSample]);

    const svgWidth = 600;
    const svgHeight = 200;
    const freq = isRunning ? 4 : (activeSample ? 3 : 2);
    const amp = isRunning ? 70 : (activeSample ? 55 : 30);

    return (
        <div className="group relative rounded-3xl border border-white/10 bg-black overflow-hidden flex flex-col items-center justify-center shadow-[0_0_50px_rgba(0,0,0,0.5)] transition-all duration-300 w-full aspect-4/3 max-h-[45vh] md:max-h-[60vh]">

            {/* Spectro-Core: Dynamic Reaction Curve */}
            <div className="absolute inset-0 z-5 flex items-center justify-center">
                <svg
                    viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                    className="w-full h-full"
                    preserveAspectRatio="xMidYMid meet"
                >
                    <defs>
                        <linearGradient id="waveGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#3B82F6" stopOpacity="0" />
                            <stop offset="20%" stopColor="#3B82F6" stopOpacity="0.8" />
                            <stop offset="50%" stopColor="#06B6D4" stopOpacity="1" />
                            <stop offset="80%" stopColor="#3B82F6" stopOpacity="0.8" />
                            <stop offset="100%" stopColor="#3B82F6" stopOpacity="0" />
                        </linearGradient>
                        <linearGradient id="waveGlow" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#06B6D4" stopOpacity="0" />
                            <stop offset="50%" stopColor="#06B6D4" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="#06B6D4" stopOpacity="0" />
                        </linearGradient>
                        <filter id="glow">
                            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                            <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                    </defs>

                    {/* Background grid */}
                    {Array.from({ length: 13 }).map((_, i) => (
                        <line key={`vg-${i}`} x1={i * 50} y1={0} x2={i * 50} y2={svgHeight} stroke="rgba(59,130,246,0.06)" strokeWidth="0.5" />
                    ))}
                    {Array.from({ length: 5 }).map((_, i) => (
                        <line key={`hg-${i}`} x1={0} y1={i * 50} x2={svgWidth} y2={i * 50} stroke="rgba(59,130,246,0.06)" strokeWidth="0.5" />
                    ))}

                    {/* Centerline */}
                    <line x1={0} y1={svgHeight / 2} x2={svgWidth} y2={svgHeight / 2} stroke="rgba(6,182,212,0.12)" strokeWidth="1" strokeDasharray="6 4" />

                    {/* Glow trail behind the wave */}
                    <path
                        d={generateSinePath(svgWidth, svgHeight, freq, amp * 0.9, phase)}
                        fill="none"
                        stroke="url(#waveGlow)"
                        strokeWidth="12"
                        opacity="0.3"
                    />

                    {/* Main sine wave */}
                    <path
                        d={generateSinePath(svgWidth, svgHeight, freq, amp, phase)}
                        fill="none"
                        stroke="url(#waveGradient)"
                        strokeWidth="2.5"
                        filter="url(#glow)"
                    />

                    {/* Secondary harmonic */}
                    <path
                        d={generateSinePath(svgWidth, svgHeight, freq * 1.5, amp * 0.25, phase * 1.3)}
                        fill="none"
                        stroke="rgba(6,182,212,0.2)"
                        strokeWidth="1"
                    />
                </svg>
            </div>

            {/* Incubation progress bar */}
            {isRunning && (
                <div className="absolute bottom-0 left-0 w-full h-1.5 bg-blue-950/50 z-40">
                    <motion.div
                        className="h-full bg-linear-to-r from-blue-500 via-cyan-400 to-blue-500 shadow-[0_0_12px_rgba(6,182,212,0.8)]"
                        initial={{ width: '0%' }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.3, ease: 'linear' }}
                    />
                </div>
            )}

            {/* HUD Overlay */}
            <div className="absolute inset-0 pointer-events-none z-30 overflow-hidden rounded-3xl">
                {/* Top-left: Calibration status */}
                <div className="absolute top-4 left-4 flex flex-col gap-1">
                    <div className="text-[10px] text-blue-400 font-mono tracking-widest font-bold flex items-center gap-2">
                        <span className={`w-1.5 h-1.5 rounded-full ${isRunning ? 'bg-cyan-400 animate-pulse shadow-[0_0_6px_#06b6d4]' : 'bg-blue-600'}`}></span>
                        PHOTOMETRIC CALIBRATION: {isRunning ? 'ACTIVE' : 'STANDBY'}
                    </div>
                    <div className="text-[9px] text-cyan-300/50 font-mono tracking-widest">
                        WAVELENGTH: {activeSample?.wavelength || '540'}nm | INCUBATION TEMP: 37.0°C
                    </div>
                </div>

                {/* Top-right: Absorbance */}
                <div className="absolute top-4 right-4 text-right">
                    <div className="text-[10px] text-cyan-400 font-mono tracking-widest font-bold opacity-80">
                        ABS: {absorbance.toFixed(3)}
                    </div>
                    <div className="text-[9px] text-blue-300/50 font-mono tracking-widest">
                        {activeSample ? activeSample.name : 'NO PANEL'}
                    </div>
                </div>

                {/* Bottom: Formula display */}
                {activeSample && (
                    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-black/70 backdrop-blur-sm px-4 py-2 rounded-xl border border-cyan-500/30">
                        <div className="text-[10px] text-cyan-200 font-mono tracking-wider text-center">
                            C = (A<sub>sample</sub> / A<sub>standard</sub>) × C<sub>standard</sub>
                        </div>
                    </div>
                )}

                {/* Scan line */}
                {isRunning && (
                    <div className="w-full h-8 bg-linear-to-b from-transparent via-cyan-400/15 to-transparent absolute top-0 opacity-60 animate-[scanLaser_2s_linear_infinite]"></div>
                )}

                {/* Corner brackets */}
                <div className="absolute top-4 left-4 w-4 h-4 border-t-2 border-l-2 border-blue-500/40"></div>
                <div className="absolute top-4 right-4 w-4 h-4 border-t-2 border-r-2 border-blue-500/40"></div>
                <div className="absolute bottom-4 left-4 w-4 h-4 border-b-2 border-l-2 border-blue-500/40"></div>
                <div className="absolute bottom-4 right-4 w-4 h-4 border-b-2 border-r-2 border-blue-500/40"></div>
            </div>

            {/* Empty state */}
            {!activeSample && (
                <div className="absolute inset-0 z-2 flex flex-col items-center justify-center bg-slate-900/60 rounded-2xl">
                    {/* Hexagonal molecular icon */}
                    <svg viewBox="0 0 100 100" className="w-24 h-24 mb-6 opacity-40">
                        <defs>
                            <filter id="hexGlow"><feGaussianBlur stdDeviation="3" /><feMerge><feMergeNode /><feMergeNode in="SourceGraphic" /></feMerge></filter>
                        </defs>
                        <polygon
                            points="50,10 90,30 90,70 50,90 10,70 10,30"
                            fill="none" stroke="#3B82F6" strokeWidth="2" filter="url(#hexGlow)" opacity="0.7"
                        />
                        <circle cx="50" cy="10" r="4" fill="#3B82F6" />
                        <circle cx="90" cy="30" r="4" fill="#06B6D4" />
                        <circle cx="90" cy="70" r="4" fill="#3B82F6" />
                        <circle cx="50" cy="90" r="4" fill="#06B6D4" />
                        <circle cx="10" cy="70" r="4" fill="#3B82F6" />
                        <circle cx="10" cy="30" r="4" fill="#06B6D4" />
                        <line x1="50" y1="10" x2="50" y2="90" stroke="#3B82F6" strokeWidth="0.5" opacity="0.3" />
                        <line x1="10" y1="30" x2="90" y2="70" stroke="#06B6D4" strokeWidth="0.5" opacity="0.3" />
                        <line x1="10" y1="70" x2="90" y2="30" stroke="#3B82F6" strokeWidth="0.5" opacity="0.3" />
                    </svg>
                    <p className="text-blue-600/50 font-mono text-xs tracking-widest uppercase px-4 text-center">
                        SELECT BIOCHEMICAL PANEL TO INITIATE ASSAY
                    </p>
                </div>
            )}
        </div>
    );
}
