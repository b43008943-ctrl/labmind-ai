import { useMemo } from 'react';

export default function FallbackBackground() {
    const { particles, keyframesCSS } = useMemo(() => {
        const parts = [];
        let css = '';
        
        // Generate floating CSS particles to simulate a lightweight 3D effect
        for (let i = 0; i < 40; i++) {
            const id = `fp${i}`;
            const size = 5 + Math.random() * 20;
            const s = {
                id,
                x: Math.random() * 100,
                y: Math.random() * 100,
                size,
                dur: 15 + Math.random() * 20,
                delay: -(Math.random() * 20),
                opacity: 0.1 + Math.random() * 0.3,
                dx: -30 + Math.random() * 60,
                dy: -30 + Math.random() * 60,
            };
            parts.push(s);
            css += `@keyframes mv-${id} { 0%, 100% { transform: translate(0, 0) scale(1); } 50% { transform: translate(${s.dx}px, ${s.dy}px) scale(1.2); } }`;
        }
        
        // Add smooth gradient animation
        css += `
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        `;
        
        return { particles: parts, keyframesCSS: css };
    }, []);

    return (
        <div className="absolute inset-0 z-0 overflow-hidden bg-[#020617]">
            <style>{keyframesCSS}</style>
            
            {/* Animated Gradient Background */}
            <div 
                className="absolute inset-0 opacity-40" 
                style={{
                    background: 'linear-gradient(-45deg, #020617, #082f49, #1e1b4b, #020617)',
                    backgroundSize: '400% 400%',
                    animation: 'gradientShift 20s ease infinite',
                }}
            />

            {/* Subtle floating particles */}
            <div className="absolute inset-0 mix-blend-screen opacity-50">
                {particles.map((p) => (
                    <div 
                        key={p.id}
                        style={{
                            position: 'absolute',
                            left: `${p.x}%`,
                            top: `${p.y}%`,
                            width: p.size,
                            height: p.size,
                            borderRadius: '50%',
                            background: `radial-gradient(circle, rgba(34,211,238,${p.opacity}) 0%, transparent 80%)`,
                            animation: `mv-${p.id} ${p.dur}s ease-in-out ${p.delay}s infinite`,
                            filter: 'blur(2px)',
                        }}
                    />
                ))}
            </div>
            
            {/* Dark vignette to focus center UI */}
            <div 
                className="absolute inset-0"
                style={{
                    background: 'radial-gradient(ellipse at center, transparent 30%, #020617 90%)',
                }}
            />
        </div>
    );
}
