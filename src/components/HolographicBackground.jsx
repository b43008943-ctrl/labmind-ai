export default function HolographicBackground() {
    return (
        <div className="fixed inset-0 -z-10 pointer-events-none overflow-hidden bg-transparent">
            {/* The Green DNA Overlay & Microscopic Cells */}
            <div className="absolute inset-0 opacity-15 mix-blend-screen flex items-center justify-center pointer-events-none drop-shadow-[0_0_10px_rgba(34,211,238,0.4)]">
                <svg
                    viewBox="0 0 1000 1000"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-full h-[120%] object-cover text-cyan-400"
                    style={{ animation: 'floatHoloBackground 25s ease-in-out infinite' }}
                >
                    {/* DNA Strands */}
                    <path d="M300,0 C400,250 700,250 700,500 C700,750 400,750 300,1000" stroke="currentColor" strokeWidth="6" strokeOpacity="0.5" />
                    <path d="M300,0 C400,250 700,250 700,500 C700,750 400,750 300,1000" stroke="currentColor" strokeWidth="2" strokeDasharray="4 8" />

                    <path d="M700,0 C600,250 300,250 300,500 C300,750 600,750 700,1000" stroke="currentColor" strokeWidth="6" strokeOpacity="0.5" />
                    <path d="M700,0 C600,250 300,250 300,500 C300,750 600,750 700,1000" stroke="currentColor" strokeWidth="2" strokeDasharray="4 8" />

                    {/* Cross-links (Base pairs) */}
                    {[...Array(18)].map((_, i) => {
                        const y = (i + 1) * 52.6;
                        const t = y / 1000;
                        const factor = Math.sin(t * Math.PI * 2);
                        const x1 = 500 - (factor * 200);
                        const x2 = 500 + (factor * 200);
                        return <line key={`dna-${i}`} x1={x1} y1={y} x2={x2} y2={y} stroke="currentColor" strokeWidth="3" strokeOpacity={0.6} strokeLinecap="round" />;
                    })}

                    {/* Microscopic Cells / Particles */}
                    {[...Array(25)].map((_, i) => {
                        const r = Math.random() * 8 + 2;
                        const cx = Math.random() * 1000;
                        const cy = Math.random() * 1000;
                        const duration = Math.random() * 15 + 10;
                        const delay = Math.random() * -20;
                        return (
                            <circle
                                key={`cell-${i}`}
                                cx={cx}
                                cy={cy}
                                r={r}
                                fill="currentColor"
                                fillOpacity={Math.random() * 0.5 + 0.1}
                                style={{ animation: `pulseCell ${duration}s ease-in-out infinite alternate ${delay}s` }}
                            />
                        );
                    })}
                </svg>
            </div>

            <style>
                {`
                    @keyframes floatHoloBackground {
                        0%, 100% { transform: translateY(0) scale(1); }
                        50% { transform: translateY(-2vh) scale(1.05); }
                    }
                    @keyframes pulseCell {
                        0% { transform: scale(0.8); opacity: 0.3; }
                        100% { transform: scale(1.5); opacity: 0.8; }
                    }
                `}
            </style>
        </div>
    );
}
