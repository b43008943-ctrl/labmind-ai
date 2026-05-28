import { useState, useRef } from 'react';

export default function DashboardCard({
    id, title, subtitle, icon: Icon, colorRGB, glowColor, onPointerDown, globalRotX, globalRotY, showAlert, index, isClicked, isFading
}) {
    const cardRef = useRef(null);
    const [localTilt, setLocalTilt] = useState({ x: 0, y: 0 });

    const handleMouseMove = (e) => {
        if (!cardRef.current) return;
        const rect = cardRef.current.getBoundingClientRect();
        const cx = (e.clientX - rect.left) / rect.width - 0.5;
        const cy = (e.clientY - rect.top) / rect.height - 0.5;
        setLocalTilt({ x: -cy * 18, y: cx * 18 });
    };

    const handleMouseLeave = () => {
        setLocalTilt({ x: 0, y: 0 });
    };

    const factor = 1 + (index * 0.08);
    const rotX = (globalRotX * factor) + (localTilt.x * 0.6);
    const rotY = (globalRotY * factor) + (localTilt.y * 0.6);

    const handlePress = () => {
        if (onPointerDown) onPointerDown();
    };

    // Determine intense glow shadow based on color theme when clicked
    let activeGlowShadow = '';
    if (isClicked) {
        if (glowColor === 'blue') activeGlowShadow = '0 0 60px rgba(59,130,246,0.9)';
        else if (glowColor === 'orange') activeGlowShadow = '0 0 60px rgba(249,115,22,0.9)';
        else if (glowColor === 'green') activeGlowShadow = '0 0 60px rgba(34,197,94,0.9)';
        else if (glowColor === 'magenta') activeGlowShadow = '0 0 60px rgba(168,85,247,0.9)';
    }

    return (
        <button
            type="button"
            id={id}
            ref={cardRef}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            onPointerDown={handlePress}
            onClick={handlePress} // Fallback for pure mouse clicks
            data-glow={glowColor}
            className={`p-3 md:p-6 aspect-square w-full relative flex flex-col justify-between text-left dashboard-card group cursor-pointer overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.25,1,0.5,1)] transform ${isClicked ? 'scale-90 opacity-80' : isFading ? 'opacity-60' : 'hover:scale-105'} ${showAlert ? 'overflow-visible relative' : ''}`}
            style={{
                background: 'rgba(5, 9, 20, 0.6)',
                backdropFilter: 'blur(16px)',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderBottom: `2px solid rgba(${colorRGB}, 1)`,
                boxShadow: isClicked
                    ? `inset 0 -30px 40px -20px rgba(${colorRGB}, 0.6), ${activeGlowShadow}`
                    : `inset 0 -30px 40px -20px rgba(${colorRGB}, 0.3), 0 10px 30px -10px rgba(0,0,0,0.5)`,
                transform: `perspective(1000px) rotateX(${isClicked ? 0 : rotX}deg) rotateY(${isClicked ? 0 : rotY}deg)`,
                opacity: 0,
                animation: `fadeInUp 0.6s ease-out forwards`,
                animationDelay: `${0.1 + index * 0.1}s`
            }}
        >


            <div
                className="absolute w-12 h-12 rounded-xl top-3 right-3 sm:top-4 sm:right-4 flex items-center justify-center transition-transform group-hover:scale-110 pointer-events-none"
                style={{
                    background: `rgba(${colorRGB}, 0.12)`,
                    border: `1px solid rgba(${colorRGB}, 0.35)`,
                    color: `rgb(${colorRGB})`,
                    boxShadow: `0 0 20px rgba(${colorRGB}, 0.25), inset 0 0 12px rgba(${colorRGB}, 0.1)`,
                    filter: `drop-shadow(0 0 15px rgba(${colorRGB}, 0.5))`,
                }}
            >
                <Icon className="w-6 h-6" strokeWidth={1.5} />

                {showAlert && (
                    <div id={`alert-dashboard-${id}`} className="absolute -top-[5px] -right-[5px] w-[14px] h-[14px] bg-rose-500 rounded-full shadow-[0_0_15px_rgba(244,63,94,1)] border-[3px] border-[#050914] z-50">
                        <div className="absolute inset-[-3px] bg-rose-500 animate-ping opacity-75 rounded-full -z-10"></div>
                    </div>
                )}
            </div>

            <div className="relative z-10 w-full flex flex-col items-start justify-end pointer-events-none mt-auto">
                <h3 className="text-xs sm:text-sm md:text-lg font-bold leading-tight text-white tracking-wide mb-1 drop-shadow-[0_0_8px_rgba(255,255,255,0.4)] group-hover:text-cyan-300 transition-colors">
                    {title}
                </h3>
                <p className="text-[9px] sm:text-xs md:text-sm leading-tight opacity-70 font-medium text-gray-400 group-hover:text-gray-300 transition-colors">
                    {subtitle}
                </p>
            </div>
        </button >
    );
}
