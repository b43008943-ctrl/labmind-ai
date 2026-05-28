/* BattleAlert — Portal modal for combat deployment */

import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle } from 'lucide-react';
import GroupIcon from './GroupIcon';

export default function BattleAlert({
    showBattleAlert,
    setShowBattleAlert,
    onNavigate
}) {
    return (
        <AnimatePresence>
            {showBattleAlert && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md font-mono touch-none stop-propagation"
                    onClick={(e) => e.stopPropagation()}
                >
                    <motion.div
                        initial={{ scale: 0.9, y: 20 }}
                        animate={{ scale: 1, y: 0 }}
                        exit={{ scale: 0.9, y: 20 }}
                        className="w-full max-w-sm bg-[#050000]/90 border-2 border-red-600/50 rounded-2xl p-6 flex flex-col items-center shadow-[0_0_50px_rgba(220,38,38,0.5)] relative overflow-hidden"
                    >
                        {/* Flashing Red Ambient Glow */}
                        <div className="absolute inset-0 bg-red-500/10 animate-pulse pointer-events-none" />

                        {/* Danger Stripes Header */}
                        <div className="absolute top-0 inset-x-0 h-1 bg-[repeating-linear-gradient(45deg,transparent,transparent_5px,#ef4444_5px,#ef4444_10px)]" />

                        {/* Header */}
                        <AlertTriangle size={32} strokeWidth={2.5} className="text-red-500 mb-2 animate-bounce drop-shadow-[0_0_10px_rgba(239,68,68,0.8)]" />
                        <h2 className="text-xl font-black text-red-500 tracking-widest uppercase mb-1 drop-shadow-[0_0_15px_rgba(239,68,68,0.8)]">
                            Deployment Order
                        </h2>
                        <p className="text-[10px] text-red-300/60 uppercase tracking-widest text-center mb-6">
                            Priority Level: Alpha <br /> Immediate Action Required
                        </p>

                        {/* Matchup Avatars */}
                        <div className="flex items-center justify-center gap-4 w-full mb-6 relative z-10">
                            <div className="flex flex-col items-center gap-2">
                                <div className="w-16 h-16 pointer-events-none"><GroupIcon type="epic neon fire dragon" /></div>
                                <span className="text-[10px] font-bold text-red-400">YOUR SQUAD</span>
                            </div>

                            <div className="text-md font-black text-white px-2 py-1 bg-red-600/30 border border-red-500 rounded shadow-[0_0_15px_rgba(239,68,68,0.8)]">
                                VS
                            </div>

                            <div className="flex flex-col items-center gap-2">
                                <div className="w-16 h-16 pointer-events-none"><GroupIcon type="dark shadow knight" /></div>
                                <span className="text-[10px] font-bold text-purple-400">ENEMY TGT</span>
                            </div>
                        </div>

                        {/* Mission Details Terminal Block */}
                        <div className="w-full bg-red-950/30 border border-red-500/20 rounded p-3 mb-6 font-mono text-[10px] flex flex-col gap-1 tracking-widest">
                            <div className="flex justify-between">
                                <span className="text-red-500/60">TARGET:</span>
                                <span className="text-red-400 font-bold">ASTRAL KNIGHTS</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-red-500/60">SECTOR:</span>
                                <span className="text-red-400 font-bold">NEURO-GRID 7</span>
                            </div>
                            <div className="flex justify-between mt-1 pt-1 border-t border-red-500/20">
                                <span className="text-red-500/60">STATUS:</span>
                                <span className="text-red-500 font-black animate-pulse">LIVE MATCH</span>
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-col w-full gap-3 relative z-10">
                            <button
                                onClick={() => {
                                    setShowBattleAlert(false);
                                    if (onNavigate) onNavigate('battlefield');
                                }}
                                className="w-full py-3.5 bg-red-600 hover:bg-red-500 text-white font-black text-xs uppercase tracking-[0.2em] rounded-lg shadow-[0_0_20px_rgba(220,38,38,0.6)] transition-all active:scale-95 border border-red-400"
                            >
                                Enter Battlefield
                            </button>
                            <button
                                onClick={() => setShowBattleAlert(false)}
                                className="w-full py-2.5 bg-transparent hover:bg-white/5 text-white/50 hover:text-white text-[10px] font-bold uppercase tracking-[0.2em] rounded-lg transition-all border border-white/5"
                            >
                                Standby (Abort)
                            </button>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
