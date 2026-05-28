/* WarMapTab — Tournament bracket visualization */

import { motion } from 'framer-motion';
import GroupIcon from './GroupIcon';

export default function WarMapTab() {
    return (
        <motion.div key="tab-warmap" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="flex flex-col gap-6 pt-6 items-center w-full min-h-screen bg-[#020202] rounded-t-2xl relative overflow-y-auto" style={{ WebkitOverflowScrolling: 'touch' }}>

            {/* 1. Stealth Tactical Background */}
            <div className="absolute inset-0 pointer-events-none z-0">
                <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M20 0L40 10V30L20 40L0 30V10Z' fill='none' stroke='%2322d3ee' stroke-width='1'/%3E%3C/svg%3E")`, backgroundSize: '40px 40px' }} />
                <div className="absolute inset-0 bg-[conic-gradient(from_0deg,transparent,rgba(34,211,238,0.05),transparent)] animate-[spin_10s_linear_infinite]" />
                <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(ellipse at top, rgba(34,211,238,0.3) 0%, transparent 60%)' }} />
            </div>

            {/* Header */}
            <div className="text-center mb-6 relative w-full flex flex-col items-center z-10 mt-6">
                <h3 className="text-2xl font-black tracking-[0.5em] uppercase text-cyan-400 relative drop-shadow-[0_0_15px_rgba(34,211,238,0.8)]" style={{ animation: 'fp-pulse 3s infinite' }}>
                    Global War Map
                </h3>
                <p className="text-[10px] text-cyan-200/60 tracking-[0.4em] mt-1 font-mono mb-2 drop-shadow-[0_0_8px_rgba(34,211,238,0.4)]">NEURAL FACTION TOURNAMENT</p>
            </div>

            {/* THE BRACKET CONTAINER */}
            <div className="flex flex-col w-[95%] max-w-[500px] gap-8 relative font-mono select-none z-10 pb-24">

                {/* ----- QUARTER FINALS ----- */}
                <div className="w-full flex flex-col gap-6 relative z-10 mt-2">
                    <div className="flex items-center justify-center gap-3 mb-2">
                        <span className="text-[12px] text-cyan-500 font-mono tracking-widest uppercase py-1 border-b border-cyan-500/40 w-1/2 text-center shadow-[0_5px_15px_-5px_rgba(34,211,238,0.3)]">Quarter Finals</span>
                    </div>

                    {/* Tactical Node 1 */}
                    <div className="flex flex-col w-full bg-black/20 border-l-4 border-cyan-500 overflow-hidden shadow-[0_0_15px_rgba(34,211,238,0.1)] relative">
                        <div className="absolute top-0 right-0 w-8 h-8 border-t border-r border-cyan-500/40" />
                        <div className="absolute bottom-0 left-0 w-8 h-8 border-b border-l border-cyan-500/40" />
                        <div className="flex items-center justify-between p-3 relative z-10">
                            <div className="flex items-center gap-3 w-[40%]">
                                <div className="w-9 h-9 shrink-0"><GroupIcon type="epic neon fire dragon" /></div>
                                <span className="text-[10px] font-black text-white truncate tracking-widest">DRAGON SYN.</span>
                            </div>
                            <div className="flex flex-col items-center justify-center w-[20%]">
                                <span className="text-[10px] font-black text-red-500 bg-red-950/30 px-1 py-0.5 rounded-sm drop-shadow-[0_0_8px_rgba(239,68,68,0.8)]">// VS //</span>
                            </div>
                            <div className="flex items-center justify-end gap-3 w-[40%] text-right">
                                <span className="text-[10px] font-black text-white truncate tracking-widest">RAVEN CLAN</span>
                                <div className="w-9 h-9 shrink-0"><GroupIcon type="shadow assassin" /></div>
                            </div>
                        </div>
                        <div className="w-full bg-[#050505]/80 border-t border-cyan-500/20 px-3 py-1.5 flex items-center justify-center">
                            <span className="text-[10px] font-mono font-black text-red-500 tracking-widest uppercase drop-shadow-[0_0_5px_rgba(239,68,68,0.8)] animate-pulse">[ STATUS :: LIVE COMBAT ]</span>
                        </div>
                    </div>

                    {/* Tactical Node 2 */}
                    <div className="flex flex-col w-full bg-black/20 border-l-4 border-cyan-500 overflow-hidden shadow-[0_0_15px_rgba(34,211,238,0.1)] relative mt-2">
                        <div className="absolute top-0 right-0 w-8 h-8 border-t border-r border-cyan-500/40" />
                        <div className="absolute bottom-0 left-0 w-8 h-8 border-b border-l border-cyan-500/40" />
                        <div className="flex items-center justify-between p-3 relative z-10">
                            <div className="flex items-center gap-3 w-[40%]">
                                <div className="w-9 h-9 shrink-0"><GroupIcon type="giant glowing frost wolf" /></div>
                                <span className="text-[10px] font-black text-white truncate tracking-widest">FROST WOLF</span>
                            </div>
                            <div className="flex flex-col items-center justify-center w-[20%]">
                                <span className="text-[10px] font-black text-cyan-500 bg-cyan-950/30 px-1 py-0.5 rounded-sm drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]">// VS //</span>
                            </div>
                            <div className="flex items-center justify-end gap-3 w-[40%] text-right">
                                <span className="text-[10px] font-black text-white truncate tracking-widest">ASTRAL KNIGHTS</span>
                                <div className="w-9 h-9 shrink-0"><GroupIcon type="dark shadow knight" /></div>
                            </div>
                        </div>
                        <div className="w-full bg-[#050505]/80 border-t border-cyan-500/20 px-3 py-1.5 flex items-center justify-center">
                            <span className="text-[10px] font-mono font-bold text-cyan-400 tracking-widest uppercase">[ T-MINUS :: 04:22:10 ]</span>
                        </div>
                    </div>
                </div>

                {/* ----- THICK CIRCUIT TRACES ----- */}
                <div className="relative w-full h-10 flex justify-center mt-[-1.5rem] mb-[-1.5rem]">
                    <div className="absolute top-0 left-[25%] w-[2px] h-1/2 bg-cyan-500/60 shadow-[0_0_10px_#22d3ee]" />
                    <div className="absolute top-0 right-[25%] w-[2px] h-1/2 bg-cyan-500/60 shadow-[0_0_10px_#22d3ee]" />
                    <div className="absolute top-1/2 left-[25%] right-[25%] h-[2px] bg-cyan-500/60 shadow-[0_0_10px_#22d3ee]" />
                    <div className="absolute top-1/2 left-1/2 w-[2.5px] h-1/2 bg-cyan-400 shadow-[0_0_15px_#22d3ee,0_0_5px_#fff]" />
                </div>

                {/* ----- SEMI FINALS ----- */}
                <div className="w-[85%] mx-auto flex flex-col gap-6 relative z-10 mt-6">
                    <div className="flex items-center justify-center gap-3 mb-2">
                        <span className="text-[12px] text-cyan-500 font-mono tracking-widest uppercase py-1 border-b border-cyan-500/40 w-[60%] text-center shadow-[0_5px_15px_-5px_rgba(34,211,238,0.3)]">Semi Finals</span>
                    </div>

                    {/* Tactical Node 3 */}
                    <div className="flex flex-col w-full bg-black/20 border-l-4 border-cyan-500 overflow-hidden shadow-[0_0_20px_rgba(34,211,238,0.15)] relative">
                        <div className="absolute top-0 right-0 w-10 h-10 border-t-2 border-r-2 border-cyan-500/50" />
                        <div className="absolute bottom-0 left-0 w-10 h-10 border-b-2 border-l-2 border-cyan-500/50" />
                        <div className="flex items-center justify-between p-4 relative z-10">
                            <div className="flex flex-col items-center gap-3 w-[35%]">
                                <div className="w-12 h-12 shrink-0"><GroupIcon type="celestial angelic valkyrie" /></div>
                                <span className="text-[10px] font-black text-white text-center tracking-widest">CELESTIAL<br />EMPIRE</span>
                            </div>
                            <div className="flex flex-col items-center justify-center w-[30%]">
                                <span className="text-[11px] font-black text-cyan-500 bg-cyan-950/30 px-2 py-1 rounded-sm drop-shadow-[0_0_10px_rgba(34,211,238,0.6)]">// VS //</span>
                            </div>
                            <div className="flex flex-col items-center gap-3 w-[35%]">
                                <div className="w-12 h-12 shrink-0"><GroupIcon type="mythical deep sea siren" /></div>
                                <span className="text-[10px] font-black text-white text-center tracking-widest">MYSTIC<br />MERMAIDS</span>
                            </div>
                        </div>
                        <div className="w-full bg-[#050505]/80 border-t border-cyan-500/30 px-4 py-2 flex items-center justify-center">
                            <span className="text-[10px] font-mono font-bold text-cyan-400 tracking-widest uppercase">[ TIME :: 20:00 HRS ]</span>
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
