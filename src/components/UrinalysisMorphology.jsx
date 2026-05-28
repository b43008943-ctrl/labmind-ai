import { motion } from 'framer-motion';

export default function UrinalysisMorphology({ sampleId }) {

    // Animation variants for Staggering
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1,
            }
        },
        exit: {
            opacity: 0,
            transition: {
                staggerChildren: 0.05,
                staggerDirection: -1
            }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, scale: 0.5, filter: "blur(4px)" },
        visible: {
            opacity: 1,
            scale: 1,
            filter: "blur(0px)",
            transition: { type: "spring", stiffness: 200, damping: 20 }
        },
        exit: { opacity: 0, scale: 0.8, filter: "blur(4px)", transition: { duration: 0.2 } }
    };

    // Layout generators
    const renderNormalSample = () => {
        // Clear view with minimal floating micro-particles
        return Array.from({ length: 8 }).map((_, i) => {
            const size = Math.random() * 6 + 4; // 4-10px small particles
            return (
                <motion.div
                    key={`norm-particle-${i}`}
                    variants={itemVariants}
                    className="absolute rounded-full bg-yellow-100/30 blur-[1px]"
                    style={{
                        width: size,
                        height: size,
                        left: `${Math.random() * 90 + 5}%`,
                        top: `${Math.random() * 90 + 5}%`,
                        boxShadow: '0 0 5px rgba(253,224,71,0.2)'
                    }}
                    animate={{
                        x: [0, Math.random() * 40 - 20, 0],
                        y: [0, Math.random() * 40 - 20, 0],
                    }}
                    transition={{
                        duration: Math.random() * 8 + 8,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />
            );
        });
    };

    const renderInfectionSample = () => {
        // Pus Cell Clusters (spherical grainy shapes with internal dots) + Rod-shaped Bacteria
        const particles = [];

        // Pus Cells (WBCs in urine)
        for (let i = 0; i < 15; i++) {
            const size = Math.random() * 25 + 30;
            particles.push(
                <motion.div
                    key={`pus-cell-${i}`}
                    variants={itemVariants}
                    className="absolute rounded-full flex items-center justify-center overflow-hidden"
                    style={{
                        width: size,
                        height: size,
                        left: `${Math.random() * 80 + 10}%`,
                        top: `${Math.random() * 80 + 10}%`,
                        background: 'radial-gradient(circle at 40% 40%, rgba(209,250,229,0.7) 0%, rgba(16,185,129,0.4) 100%)',
                        border: '1px dashed rgba(52,211,153,0.5)',
                        boxShadow: 'inset 0 0 10px rgba(4,120,87,0.3), 0 0 15px rgba(16,185,129,0.2)',
                    }}
                    animate={{
                        scale: [1, 1.05, 1],
                        rotate: [0, Math.random() * 20 - 10, 0]
                    }}
                    transition={{ duration: Math.random() * 4 + 4, repeat: Infinity, ease: "easeInOut" }}
                >
                    {/* Add grainy dots inside the pus cell (granules) */}
                    {Array.from({ length: 5 }).map((_, j) => (
                        <div
                            key={`granule-${i}-${j}`}
                            className="absolute rounded-full bg-emerald-700/60"
                            style={{
                                width: Math.random() * 4 + 2,
                                height: Math.random() * 4 + 2,
                                left: `${Math.random() * 60 + 20}%`,
                                top: `${Math.random() * 60 + 20}%`,
                            }}
                        />
                    ))}
                </motion.div>
            );
        }

        // Rod-shaped Bacteria (Bacilli)
        for (let i = 0; i < 20; i++) {
            const width = Math.random() * 10 + 15;
            const height = Math.random() * 3 + 3;
            particles.push(
                <motion.div
                    key={`bacteria-${i}`}
                    variants={itemVariants}
                    className="absolute rounded-full bg-emerald-400/80"
                    style={{
                        width: width,
                        height: height,
                        left: `${Math.random() * 90 + 5}%`,
                        top: `${Math.random() * 90 + 5}%`,
                        rotate: Math.random() * 360,
                        boxShadow: '0 0 8px rgba(52,211,153,0.6)'
                    }}
                    animate={{
                        x: [0, Math.random() * 100 - 50, 0],
                        y: [0, Math.random() * 100 - 50, 0],
                        rotate: [0, Math.random() * 180, 0] // Tumble translation
                    }}
                    transition={{ duration: Math.random() * 6 + 4, repeat: Infinity, ease: "linear" }}
                />
            );
        }

        return particles;
    };

    const renderStoneSample = () => {
        // Crystal Shapes: sharp geometric diamonds/squares that shimmer
        const particles = [];

        // Add some background debris
        for (let i = 0; i < 10; i++) {
            particles.push(
                <motion.div
                    key={`debris-${i}`}
                    variants={itemVariants}
                    className="absolute bg-amber-900/30 blur-[2px] rounded-full"
                    style={{
                        width: Math.random() * 15 + 10,
                        height: Math.random() * 15 + 10,
                        left: `${Math.random() * 90 + 5}%`,
                        top: `${Math.random() * 90 + 5}%`,
                    }}
                />
            );
        }

        // Add distinct geometric Crystals (Calcium Oxalate/Uric Acid representations)
        for (let i = 0; i < 12; i++) {
            const size = Math.random() * 30 + 30; // 30-60px
            const isSquare = Math.random() > 0.5; // Mix of squares (envelope) and diamonds

            particles.push(
                <motion.div
                    key={`crystal-${i}`}
                    variants={itemVariants}
                    className="absolute overflow-hidden"
                    style={{
                        width: size,
                        height: size,
                        left: `${Math.random() * 80 + 10}%`,
                        top: `${Math.random() * 80 + 10}%`,
                        rotate: Math.random() * 180,
                        background: 'linear-gradient(135deg, rgba(255,255,255,0.8) 0%, rgba(251,191,36,0.5) 50%, rgba(217,119,6,0.8) 100%)',
                        border: '1px solid rgba(255,255,255,0.8)',
                        borderRadius: isSquare ? '2px' : '4px',
                        clipPath: isSquare
                            ? 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' // Box
                            : 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)', // Diamond
                        boxShadow: '0 0 20px rgba(245,158,11,0.4), inset 0 0 15px rgba(255,255,255,0.6)'
                    }}
                    animate={{
                        rotate: [0, Math.random() * 20 - 10, 0], // Slight wobble
                        x: [0, Math.random() * 10 - 5, 0],
                        y: [0, Math.random() * 10 - 5, 0]
                    }}
                    transition={{ duration: Math.random() * 4 + 4, repeat: Infinity, ease: "easeInOut" }}
                >
                    {/* Inner X or lines for "envelope" appearance of typical oxalate crystals */}
                    {isSquare && (
                        <>
                            <div className="absolute top-0 left-0 w-[141%] h-px bg-white/60 origin-top-left rotate-45" />
                            <div className="absolute top-0 right-0 w-[141%] h-px bg-white/60 origin-top-right -rotate-45" />
                        </>
                    )}
                    {/* Shimmer sweeping effect */}
                    <motion.div
                        className="absolute top-0 left-0 w-full h-full bg-linear-to-r from-transparent via-white/80 to-transparent"
                        animate={{ x: ['-100%', '200%'] }}
                        transition={{ duration: 3, repeat: Infinity, ease: "linear", repeatDelay: Math.random() * 3 + 1 }}
                        style={{ transform: 'skewX(-20deg)' }}
                    />
                </motion.div>
            );
        }

        return particles;
    };

    return (
        <motion.div
            className="absolute inset-0 pointer-events-none z-10 overflow-hidden mix-blend-screen"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
        >
            {sampleId === 'sample-a' && renderNormalSample()}
            {sampleId === 'sample-b' && renderInfectionSample()}
            {sampleId === 'sample-c' && renderStoneSample()}
        </motion.div>
    );
}
