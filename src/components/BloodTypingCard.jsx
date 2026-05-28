import { motion, AnimatePresence } from 'framer-motion';
import ScientificTooltip from './ScientificTooltip';

// Defines the visual outcome for each well based on the sample
export default function BloodTypingCard({ sample, isMixing, hasMixed }) {
    if (!sample) {
        return (
            <div className="w-full max-w-full md:max-w-lg mx-auto aspect-3/1 bg-slate-100 rounded-3xl border border-slate-300 shadow-xl flex items-center justify-center">
                <span className="text-slate-400 font-bold uppercase tracking-widest text-xs md:text-sm">Awaiting Sample Selection</span>
            </div>
        );
    }

    // Reaction definitions (Agglutination = true, Smooth = false)
    const reactions = {
        'anti-a': sample.reactions.a,
        'anti-b': sample.reactions.b,
        'anti-d': sample.reactions.d
    };

    return (
        <div className="w-full max-w-full md:max-w-lg mx-auto bg-slate-100 rounded-3xl border border-slate-300 shadow-xl p-4 md:p-8 relative overflow-hidden">
            {/* Typing Card Header */}
            <div className="flex justify-between items-end mb-6 md:mb-8 border-b-2 border-slate-200 pb-3 md:pb-4 overflow-hidden">
                <div className="flex-1 min-w-0 pr-2">
                    <h3 className="text-slate-800 font-bold text-sm md:text-xl uppercase tracking-tighter truncate">Immunohematology</h3>
                    <p className="text-[9px] md:text-xs text-slate-500 uppercase tracking-widest font-mono truncate">ABO/Rh Blood Typing Card</p>
                </div>
                <div className="text-right shrink-0">
                    <span className="block text-[9px] md:text-xs font-bold text-slate-400 uppercase tracking-widest">Patient ID</span>
                    <span className="text-xs md:text-sm font-mono text-slate-800 font-bold bg-slate-200 px-2 py-1 rounded inline-block">{sample.name}</span>
                </div>
            </div>

            {/* The 3 Wells */}
            <div className="flex flex-row justify-between items-start gap-1 sm:gap-2 w-full px-0 sm:px-2">
                <ScientificTooltip text="Anti-A Reagent: Contains antibodies that cause Type A red blood cells to agglutinate (clump)." className="flex-1 flex w-full">
                    <Well id="anti-a" label="Anti-A" color="text-blue-600" isMixing={isMixing} hasMixed={hasMixed} isAgglutinated={reactions['anti-a']} />
                </ScientificTooltip>
                <Well id="anti-b" label="Anti-B" color="text-amber-500" isMixing={isMixing} hasMixed={hasMixed} isAgglutinated={reactions['anti-b']} />
                <Well id="anti-d" label="Anti-D (Rh)" color="text-slate-800" isMixing={isMixing} hasMixed={hasMixed} isAgglutinated={reactions['anti-d']} />
            </div>

            {/* Mixing Animation Overlay */}
            <AnimatePresence>
                {isMixing && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-white/20 backdrop-blur-[1px] z-10 flex items-center justify-center pointer-events-none"
                    >
                        <div className="bg-pink-600/90 text-white font-bold uppercase tracking-widest text-[10px] md:text-xs px-4 md:px-6 py-2 md:py-3 rounded-full flex items-center gap-2 md:gap-3 shadow-[0_0_20px_rgba(219,39,119,0.5)] backdrop-blur-md">
                            <motion.div
                                animate={{ rotate: 360 }}
                                transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                                className="w-3 h-3 md:w-4 md:h-4 border-2 border-white/30 border-t-white rounded-full shrink-0"
                            />
                            Adding Antisera & Mixing...
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

function Well({ id, label, color, isMixing, hasMixed, isAgglutinated }) {
    // Generate random dots for the agglutination effect so it looks natural. 
    // Kept size between 2-5px for smaller viewport compatibility.
    const dots = Array.from({ length: 45 }).map((_, i) => ({
        x: Math.random() * 80 + 10,
        y: Math.random() * 80 + 10,
        size: Math.random() * 3 + 2,
        delay: Math.random() * 0.5
    }));

    return (
        <div className="flex flex-col items-center gap-2 md:gap-3 flex-1 overflow-hidden relative">
            <span className={`text-[10px] md:text-xs font-extrabold uppercase tracking-widest truncate w-full text-center ${color}`}>{label}</span>

            {/* Hardcoded maximum dimensions to prevent flexing too wide and clipping */}
            <div className="w-16 h-16 sm:w-20 sm:h-20 shrink-0 rounded-full border-4 border-slate-200 bg-white shadow-inner relative overflow-hidden flex items-center justify-center">

                {/* Initial Blood Drop - Using percentage scale so it naturally fits */}
                {!hasMixed && !isMixing && (
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="w-[60%] h-[60%] bg-red-600 rounded-full shadow-[inset_0_-4px_8px_rgba(0,0,0,0.3)]"
                    />
                )}

                {/* Mixing/Mixed State */}
                {(isMixing || hasMixed) && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 1 }}
                        className="absolute inset-0 w-full h-full"
                    >
                        {/* Base fluid color */}
                        <div className={`absolute inset-0 transition-colors duration-2000 ${isAgglutinated && hasMixed ? 'bg-red-400/40' : 'bg-[#990000]'}`} />

                        {/* Agglutination Clumps */}
                        {isAgglutinated && (
                            <div className="absolute inset-0">
                                {dots.map((dot, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, scale: 0.5 }}
                                        animate={{ opacity: hasMixed ? 1 : 0, scale: hasMixed ? 1 : 0.5 }}
                                        transition={{ duration: 2 }}
                                        className="absolute bg-[#4A0404] rounded-full shadow-[0_1px_2px_rgba(0,0,0,0.4)]"
                                        style={{
                                            left: `${dot.x}%`,
                                            top: `${dot.y}%`,
                                            width: `${dot.size}px`,
                                            height: `${dot.size}px`,
                                        }}
                                    />
                                ))}
                            </div>
                        )}

                        {/* Liquid Reflection Highlight */}
                        <div className="absolute top-[10%] left-[20%] w-[25%] h-[25%] bg-white/20 rounded-full blur-[2px]" />
                    </motion.div>
                )}
            </div>

            {/* Reaction Text (Only visible after mixed) */}
            <div className="h-6 md:h-4 w-full text-center flex items-center justify-center">
                {hasMixed && !isMixing && (
                    <motion.span
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`text-[8px] sm:text-[10px] font-bold uppercase tracking-widest ${isAgglutinated ? 'text-pink-600' : 'text-slate-400'} leading-none`}
                    >
                        {isAgglutinated ? 'Agglutination (+)' : 'Smooth (-)'}
                    </motion.span>
                )}
            </div>
        </div>
    );
}
