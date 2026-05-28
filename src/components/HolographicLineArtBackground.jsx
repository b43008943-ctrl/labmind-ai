export default function HolographicLineArtBackground() {
    return (
        <div className="fixed inset-0 -z-10 pointer-events-none overflow-hidden">
            {/* The SVG Line Art Overlay */}
            <div className="absolute inset-0 opacity-15 mix-blend-screen flex items-center justify-center pointer-events-none drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]">
                <svg
                    viewBox="0 0 1000 1000"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-full h-full object-cover text-cyan-400"
                    style={{ animation: 'slowDrift 40s ease-in-out infinite alternate' }}
                >
                    {/* Microscopic Line-Art Cells (Concentric Rings with nodes) */}
                    {[...Array(15)].map((_, i) => {
                        const cx = Math.random() * 1000;
                        const cy = Math.random() * 1000;
                        const r1 = Math.random() * 30 + 15;
                        const r2 = r1 + Math.random() * 15 + 10;
                        const duration = Math.random() * 30 + 20;
                        const delay = Math.random() * -30;
                        return (
                            <g key={`cell-${i}`} style={{ transformOrigin: `${cx}px ${cy}px`, animation: `spinLineArt ${duration}s linear infinite ${delay}s` }}>
                                <circle cx={cx} cy={cy} r={r1} stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.7" strokeDasharray="4 4" />
                                <circle cx={cx} cy={cy} r={r2} stroke="currentColor" strokeWidth="0.3" strokeOpacity="0.5" />
                                <circle cx={cx + r1} cy={cy} r="2" fill="currentColor" />
                                <circle cx={cx - r2} cy={cy} r="1.5" fill="currentColor" />
                                <line x1={cx} y1={cy - r2} x2={cx} y2={cy - r2 - 10} stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.4" />
                            </g>
                        );
                    })}

                    {/* Neuronal / Network Data lines */}
                    {[...Array(8)].map((_, i) => {
                        const x1 = Math.random() * 1000;
                        const y1 = Math.random() * 1000;
                        const x2 = x1 + (Math.random() - 0.5) * 300;
                        const y2 = y1 + (Math.random() - 0.5) * 300;
                        const x3 = x2 + (Math.random() - 0.5) * 300;
                        const y3 = y2 + (Math.random() - 0.5) * 300;

                        return (
                            <path
                                key={`net-${i}`}
                                d={`M${x1},${y1} L${x2},${y2} L${x3},${y3}`}
                                stroke="currentColor"
                                strokeWidth="0.4"
                                strokeDasharray="2 6"
                                strokeOpacity="0.6"
                            />
                        );
                    })}

                    {/* Atoms / Electron Orbitals */}
                    {[...Array(8)].map((_, i) => {
                        const cx = Math.random() * 1000;
                        const cy = Math.random() * 1000;
                        const rX = Math.random() * 20 + 30;
                        const rY = rX * 0.4;
                        const duration = Math.random() * 40 + 40;
                        const delay = Math.random() * -40;
                        return (
                            <g key={`atom-${i}`} style={{ transformOrigin: `${cx}px ${cy}px`, animation: `floatAtom ${duration}s ease-in-out infinite alternate ${delay}s` }}>
                                <ellipse cx={cx} cy={cy} rx={rX} ry={rY} stroke="currentColor" strokeWidth="0.4" transform={`rotate(30 ${cx} ${cy})`} opacity="0.6" />
                                <ellipse cx={cx} cy={cy} rx={rX} ry={rY} stroke="currentColor" strokeWidth="0.4" transform={`rotate(90 ${cx} ${cy})`} opacity="0.6" />
                                <ellipse cx={cx} cy={cy} rx={rX} ry={rY} stroke="currentColor" strokeWidth="0.4" transform={`rotate(150 ${cx} ${cy})`} opacity="0.6" />
                                <circle cx={cx} cy={cy} r="2" fill="currentColor" />
                            </g>
                        );
                    })}
                </svg>
            </div>

            <style>
                {`
                    @keyframes spinLineArt {
                        from { transform: rotate(0deg); }
                        to { transform: rotate(360deg); }
                    }
                    @keyframes floatAtom {
                        0% { transform: translateY(0px) translateX(0px) rotate(0deg); }
                        100% { transform: translateY(-50px) translateX(30px) rotate(15deg); }
                    }
                    @keyframes slowDrift {
                        0% { transform: scale(1) translate(0, 0); }
                        100% { transform: scale(1.05) translate(-2%, 2%); }
                    }
                `}
            </style>
        </div>
    );
}
