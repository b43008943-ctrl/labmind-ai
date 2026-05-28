import { useState, useEffect } from 'react';
import { X, Activity, Brain, Server, ChevronLeft } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function AiDiagnosticPanel({ isOpen, onOpen, onClose, reportData, sampleType }) {
    const [displayedInsight, setDisplayedInsight] = useState('');

    // Typewriter Effect
    useEffect(() => {
        if (isOpen && reportData?.insight) {
            setDisplayedInsight('');
            let currentIndex = 0;
            const insightText = reportData.insight;

            const typingInterval = setInterval(() => {
                if (currentIndex < insightText.length) {
                    setDisplayedInsight(insightText.substring(0, currentIndex + 1));
                    currentIndex++;
                } else {
                    clearInterval(typingInterval);
                }
            }, 25); // 25ms per char for fast AI typing

            return () => clearInterval(typingInterval);
        } else {
            setDisplayedInsight('');
        }
    }, [isOpen, reportData]);


    // Helper logic to normalize different report objects (Hematology vs Urinalysis) into an array of metrics
    let metrics = [];
    if (sampleType === 'blood' && reportData) {
        metrics = [
            { label: 'RBC Count', value: reportData.rbc, unit: 'M/mcL', status: reportData.rbcStatus },
            { label: 'WBC Count', value: reportData.wbc, unit: 'K/mcL', status: reportData.wbcStatus },
            { label: 'Hemoglobin', value: reportData.hgb, unit: 'g/dL', status: reportData.hgbStatus },
        ];
    } else if (sampleType === 'urine' && reportData) {
        metrics = [
            { label: 'Appearance', value: reportData.appearance, unit: '', status: reportData.appearance === 'Clear/Pale Yellow' ? 'NORMAL' : 'ABNORMAL' },
            { label: 'pH Level', value: reportData.ph, unit: '', status: reportData.ph === '6.0' ? 'NORMAL' : (reportData.ph === '7.5' ? 'HIGH' : 'LOW') },
            { label: 'Protein', value: reportData.protein, unit: '', status: reportData.protein === 'Negative' ? 'NORMAL' : 'ELEVATED' },
            { label: reportData.findingLabel || 'Finding', value: reportData.finding, unit: '', status: reportData.findingStatus || 'ABNORMAL' },
        ];
    }

    const drawerVariants = {
        closed: { x: "100%", opacity: 0.5 },
        open: {
            x: 0,
            opacity: 1,
            transition: { type: "spring", damping: 25, stiffness: 200 }
        },
        exit: { x: "100%", opacity: 0, transition: { duration: 0.5, ease: "anticipate" } }
    };

    const contentContainerVariants = {
        closed: { opacity: 0 },
        open: {
            opacity: 1,
            transition: {
                delayChildren: 0.3,
                staggerChildren: 0.1
            }
        },
        exit: { opacity: 0 }
    };

    const itemVariants = {
        closed: { opacity: 0, y: 20 },
        open: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
    };

    return (
        <>
            {/* Custom Animation Keyframes (keeping peek for the handle) */}
            <style>{`
                @keyframes peek {
                    0%, 90% { transform: translateX(0); }
                    95% { transform: translateX(-5px); }
                    100% { transform: translateX(0); }
                }
                .animate-peek {
                    animation: peek 3s cubic-bezier(0.34, 1.56, 0.64, 1) infinite;
                }
            `}</style>

            {/* Sliding Trigger Tab */}
            {reportData && (
                <div className={`fixed right-0 top-1/2 -translate-y-1/2 z-10000 pointer-events-none`}>
                    <motion.button
                        onClick={() => {
                            if (isOpen && onClose) {
                                onClose();
                            } else if (onOpen) {
                                onOpen();
                            }
                        }}
                        initial={false}
                        animate={{
                            x: isOpen ? 48 : 0,
                            opacity: isOpen ? 0 : 1
                        }}
                        transition={{ type: "spring", damping: 20, stiffness: 150 }}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className={`w-6 h-32 rounded-l-2xl bg-slate-900/40 backdrop-blur-3xl border border-white/10 border-r-0 flex items-center justify-center cursor-pointer group pointer-events-auto`}
                    >
                        {/* Neon Accent */}
                        <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-cyan-400 shadow-[0_0_15px_#22d3ee] rounded-l-2xl"></div>

                        <motion.div
                            animate={{ rotate: isOpen ? 180 : 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <ChevronLeft strokeWidth={1} className={`w-5 h-5 text-slate-300 group-hover:text-white transition-colors duration-300 animate-peek`} />
                        </motion.div>
                    </motion.button>
                </div>
            )}

            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop Overlay */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.5 }}
                            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-9000 pointer-events-auto"
                            onClick={onClose}
                        />

                        {/* Slide-over Drawer */}
                        <motion.div
                            variants={drawerVariants}
                            initial="closed"
                            animate="open"
                            exit="exit"
                            className="fixed top-0 right-0 h-full w-full md:w-[400px] z-9999 bg-slate-950/80 backdrop-blur-2xl border-l border-cyan-900/50 shadow-[-20px_0_60px_rgba(0,0,0,0.8)] flex flex-col font-rajdhani origin-right pointer-events-auto"
                        >
                            {/* Header */}
                            <div className="p-6 border-b border-cyan-900/30 flex flex-col relative shrink-0">
                                <button
                                    onClick={onClose}
                                    className="absolute top-6 right-6 text-slate-500 hover:text-white transition-colors"
                                >
                                    <X className="w-6 h-6" />
                                </button>

                                <div className="flex items-center gap-2 mb-2">
                                    <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee] animate-pulse"></div>
                                    <h2 className="text-xl font-black uppercase tracking-widest bg-linear-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                                        Diagnostic Report: Generated
                                    </h2>
                                </div>

                                <p className="text-xs text-slate-400 font-mono tracking-widest flex items-center gap-2">
                                    <Server className="w-3 h-3 text-cyan-600" />
                                    PATIENT ID: 894-XX-A9 | BIO-SCAN COMPLETE
                                </p>
                            </div>

                            {/* Content Body */}
                            <motion.div
                                variants={contentContainerVariants}
                                initial="closed"
                                animate="open"
                                exit="exit"
                                className="flex-1 overflow-y-auto p-6 flex flex-col gap-8 no-scrollbar"
                            >

                                {/* The Results Grid (Critical Value Highlighting) */}
                                <motion.div variants={itemVariants}>
                                    <h3 className="text-sm font-bold text-slate-300 uppercase tracking-widest mb-4 flex items-center gap-2">
                                        <Activity className="w-4 h-4 text-cyan-500" /> Identified Parameters
                                    </h3>
                                    <div className="grid grid-cols-1 gap-4">
                                        {metrics.map((m, idx) => {
                                            const isAbnormal = m.status !== 'NORMAL';
                                            const isCritical = m.status === 'CRITICAL' || m.status === 'WARNING';

                                            return (
                                                <div key={idx} className="flex justify-between items-center bg-slate-900/40 border border-white/5 rounded-xl p-4 transition-all hover:bg-slate-800/50">
                                                    <div className="flex flex-col">
                                                        <span className="text-xs text-slate-500 uppercase tracking-widest font-mono mb-1">{m.label}</span>
                                                        <span className={`text-[10px] font-bold tracking-widest uppercase ${isAbnormal ? 'text-red-400 drop-shadow-[0_0_5px_rgba(248,113,113,0.5)] animate-pulse' : 'text-emerald-500'}`}>
                                                            {m.status}
                                                        </span>
                                                    </div>
                                                    <div className="text-right">
                                                        <span className={`text-2xl font-bold tracking-wider ${isAbnormal ? (isCritical ? 'text-red-500 drop-shadow-[0_0_20px_rgba(248,113,113,1)]' : 'text-red-400 drop-shadow-[0_0_10px_rgba(248,113,113,0.8)]') : 'text-cyan-300'}`}>
                                                            {m.value}
                                                        </span>
                                                        {m.unit && <span className="text-xs text-slate-500 font-sans ml-1">{m.unit}</span>}
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </motion.div>

                                {/* AI Interpretation (Typewriter Effect) */}
                                <motion.div variants={itemVariants} className="mt-auto pt-4">
                                    <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-5 relative overflow-hidden group">
                                        {/* Glass gradient overlay */}
                                        <div className="absolute inset-0 bg-linear-to-br from-cyan-900/10 to-transparent opacity-50 pointer-events-none"></div>

                                        <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-3 flex items-center gap-2 drop-shadow-[0_0_8px_rgba(34,211,238,0.5)]">
                                            <Brain className="w-4 h-4" /> AI Summary
                                        </h4>

                                        <p className="font-mono text-sm text-cyan-50 leading-relaxed tracking-wide min-h-20">
                                            {displayedInsight}
                                            <span className={`inline-block ml-1 align-middle w-2 h-4 ${isOpen ? 'bg-cyan-400 animate-pulse shadow-[0_0_8px_#22d3ee]' : 'bg-transparent'}`}></span>
                                        </p>
                                    </div>
                                </motion.div>

                            </motion.div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </>
    );
}
