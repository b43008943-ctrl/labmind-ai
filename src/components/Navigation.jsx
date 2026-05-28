import { ScanLine, Fingerprint, Network, Home, User } from 'lucide-react';
import { useAppSettings } from '../context/AppSettingsContext';

export default function Navigation({ onOpenModal, onNavigateCommunity, onNavigateHome, onNavigateProfile, isCommunityActive, activeTab }) {
    const { isLight } = useAppSettings();
    return (
        <nav className={`mb-6 mx-4 rounded-3xl h-20 flex items-center justify-around px-2 sm:px-8 relative z-50 shrink-0 mt-auto backdrop-blur-2xl transition-colors duration-500 ${isLight
            ? 'bg-white/80 border border-gray-200 shadow-[0_-4px_30px_rgba(0,0,0,0.08)]'
            : 'bg-slate-900/40 border border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.1),0_20px_40px_rgba(0,0,0,0.5)]'
            }`}>

            {/* Premium Metallic Gradients */}
            <svg width="0" height="0" className="absolute pointer-events-none">
                <defs>
                    <linearGradient id="metallic-cyan" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#cffafe" />
                        <stop offset="20%" stopColor="#22d3ee" />
                        <stop offset="50%" stopColor="#0891b2" />
                        <stop offset="80%" stopColor="#22d3ee" />
                        <stop offset="100%" stopColor="#083344" />
                    </linearGradient>
                    <linearGradient id="metallic-slate" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#f8fafc" />
                        <stop offset="50%" stopColor="#94a3b8" />
                        <stop offset="100%" stopColor="#334155" />
                    </linearGradient>
                </defs>
            </svg>

            {/* Far Left — Profile icon */}
            <button
                onClick={onNavigateProfile}
                className={`nav-btn flex items-center justify-center w-11 h-11 rounded-xl transition-all duration-300 cursor-pointer outline-none ${activeTab === 0
                    ? 'drop-shadow-[0_0_10px_rgba(6,182,212,0.8)]'
                    : `hover:drop-shadow-[0_0_10px_rgba(6,182,212,0.8)] opacity-70 hover:opacity-100`
                    }`}
                style={activeTab === 0 ? { background: 'rgba(6,182,212,0.08)', boxShadow: '0 0 15px rgba(6,182,212,0.2)' } : {}}
            >
                <User className="w-5 h-5" stroke={activeTab === 0 ? "url(#metallic-cyan)" : "url(#metallic-slate)"} strokeWidth={1.5} />
            </button>

            {/* Left — Home icon */}
            <button
                onClick={onNavigateHome}
                className={`nav-btn flex items-center justify-center w-11 h-11 rounded-xl transition-all duration-300 cursor-pointer outline-none ${activeTab === 1
                    ? 'drop-shadow-[0_0_10px_rgba(6,182,212,0.8)]'
                    : `hover:drop-shadow-[0_0_10px_rgba(6,182,212,0.8)] opacity-70 hover:opacity-100`
                    }`}
                style={activeTab === 1 ? { background: 'rgba(6,182,212,0.08)', boxShadow: '0 0 15px rgba(6,182,212,0.2)' } : {}}
            >
                <Home className="w-5 h-5" stroke={activeTab === 1 ? "url(#metallic-cyan)" : "url(#metallic-slate)"} strokeWidth={1.5} />
            </button>

            {/* --- AI BIOMETRIC SCANNER (UPLOAD PORTAL) --- */}
            <div
                onClick={onOpenModal}
                className="relative -top-6 group cursor-pointer z-50 flex flex-col items-center justify-center"
            >
                {/* 1. BIOLOGICAL PULSE */}
                <div className="absolute w-20 h-20 bg-cyan-500/30 rounded-full animate-ping" style={{ animationDuration: '2.5s' }}></div>
                <div className="absolute w-16 h-16 bg-purple-500/20 rounded-full animate-pulse" style={{ animationDuration: '1.5s' }}></div>

                {/* 2. ENHANCED VOLUMETRIC PARTICLES */}
                <div className="absolute w-32 h-32 pointer-events-none">
                    {[...Array(12)].map((_, i) => (
                        <div
                            key={i}
                            className="absolute rounded-full"
                            style={{
                                width: `${2 + Math.random() * 4}px`,
                                height: `${2 + Math.random() * 4}px`,
                                background: i % 2 === 0 ? '#22d3ee' : '#c084fc',
                                boxShadow: `0 0 ${8 + Math.random() * 5}px ${i % 2 === 0 ? '#22d3ee' : '#a855f7'}`,
                                left: `${5 + Math.random() * 90}%`,
                                top: `${5 + Math.random() * 90}%`,
                                opacity: 0.8,
                                animation: `bioFloat ${2 + Math.random() * 3}s ease-in-out infinite alternate`,
                                animationDelay: `${Math.random() * 2}s`,
                            }}
                        />
                    ))}
                </div>

                {/* 3. VOLUMETRIC BIOMETRIC TERMINAL */}
                <div className="relative w-24 h-24 bg-[#020617]/90 backdrop-blur-xl rounded-full flex items-center justify-center border-[2px] border-cyan-500/40 shadow-[0_0_40px_rgba(6,182,212,0.5),inset_0_0_20px_rgba(6,182,212,0.6)] transition-all duration-400 group-hover:scale-105 group-hover:shadow-[0_0_60px_rgba(6,182,212,0.9),inset_0_0_30px_rgba(6,182,212,0.9)] group-hover:border-cyan-300 overflow-hidden">

                    {/* Deep Cyan Glass Containment */}
                    <div className="absolute inset-0 rounded-full bg-linear-to-b from-cyan-400/20 to-transparent pointer-events-none" />

                    {/* 4. VOLUMETRIC SCANNING LASERS */}
                    <div className="absolute w-full h-full pointer-events-none mix-blend-screen">
                        {/* Horizontal Laser */}
                        <div className="absolute left-0 w-full h-[3px] bg-cyan-300 shadow-[0_0_20px_#22d3ee,0_0_40px_#cffafe] opacity-90" style={{ animation: 'scanLaser 2s cubic-bezier(0.4, 0, 0.2, 1) infinite' }}></div>
                        {/* Secondary Vertical Laser */}
                        <div className="absolute top-0 w-[2px] h-full bg-cyan-300/60 shadow-[0_0_15px_#22d3ee] left-1/2 -translate-x-1/2 opacity-70" style={{ animation: 'scanLaserVertical 3s ease-in-out infinite' }}></div>
                    </div>

                    {/* 5. REFRACTIVE CROSSHAIR */}
                    <div className="absolute inset-0 pointer-events-none z-0 opacity-30 group-hover:opacity-60 transition-opacity duration-500">
                        <div className="absolute top-1/2 left-2 right-2 h-px bg-cyan-300 shadow-[0_0_5px_#22d3ee]"></div>
                        <div className="absolute left-1/2 top-2 bottom-2 w-px bg-cyan-300 shadow-[0_0_5px_#22d3ee]"></div>
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full border-[1.5px] border-cyan-400/60 shadow-[0_0_10px_#22d3ee]"></div>
                    </div>

                    {/* 6. THE METALLIC ICON (Fingerprint / Bio-ID) */}
                    <Fingerprint
                        className="w-10 h-10 transition-all duration-300 relative z-10"
                        stroke="url(#metallic-cyan)"
                        strokeWidth={1.5}
                        style={{ filter: 'drop-shadow(0 0 12px rgba(34,211,238,0.9))' }}
                    />

                    {/* 7. DATA MATRIX NOISE */}
                    <div className="absolute inset-0 opacity-20 mix-blend-overlay rounded-full" style={{
                        backgroundImage: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.2) 0%, transparent 40%), radial-gradient(circle at 70% 70%, rgba(6,182,212,0.2) 0%, transparent 40%)'
                    }}></div>
                </div>

                {/* 8. FLOATING LABEL */}
                <div className="absolute -top-12 opacity-0 group-hover:opacity-100 transition-opacity duration-300 px-3 py-1 bg-cyan-950/90 border border-cyan-400/50 rounded-full backdrop-blur-md shadow-[0_0_20px_rgba(6,182,212,0.5)]">
                    <span className="text-[10px] text-cyan-200 font-mono tracking-widest font-black whitespace-nowrap drop-shadow-[0_0_5px_#22d3ee]">BIOMETRIC UPLOAD</span>
                </div>

                {/* 9. BOTTOM IDENTIFIER */}
                <span className="text-[8px] text-cyan-400/80 font-mono tracking-[0.25em] uppercase mt-2 group-hover:text-cyan-300 group-hover:drop-shadow-[0_0_8px_#22d3ee] transition-all font-bold">AI ANALYZE</span>
            </div>

            {/* Right — Network/Community icon */}
            <button
                onClick={onNavigateCommunity}
                className={`nav-btn flex items-center justify-center w-11 h-11 rounded-xl transition-all duration-300 cursor-pointer outline-none ${activeTab === 2
                    ? 'drop-shadow-[0_0_10px_rgba(6,182,212,0.8)]'
                    : `hover:drop-shadow-[0_0_10px_rgba(6,182,212,0.8)] opacity-70 hover:opacity-100`
                    }`}
                style={activeTab === 2 ? { background: 'rgba(6,182,212,0.08)', boxShadow: '0 0 15px rgba(6,182,212,0.2)' } : {}}
            >
                <Network className="w-5 h-5" stroke={activeTab === 2 ? "url(#metallic-cyan)" : "url(#metallic-slate)"} strokeWidth={1.5} />
            </button>

            {/* Bio-Scanner Keyframes */}
            <style>{`
                @keyframes scanLaser {
                    0% { top: -10%; opacity: 0; }
                    10% { opacity: 1; }
                    50% { top: 110%; opacity: 1; }
                    60% { opacity: 0; }
                    100% { top: 110%; opacity: 0; }
                }
                @keyframes scanLaserVertical {
                    0% { left: 10%; opacity: 0.3; }
                    50% { left: 90%; opacity: 0.8; }
                    100% { left: 10%; opacity: 0.3; }
                }
                @keyframes bioFloat {
                    0% { transform: translateY(0px) translateX(0px) scale(1); opacity: 0.4; }
                    50% { transform: translateY(-12px) translateX(8px) scale(1.4); opacity: 0.9; }
                    100% { transform: translateY(4px) translateX(-6px) scale(0.8); opacity: 0.5; }
                }
            `}</style>
        </nav>
    );
}
