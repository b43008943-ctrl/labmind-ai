/* LeaderboardTab — Podium top-3 + battalion roster #4-#10 + floating rank card */

import { motion } from 'framer-motion';
import { Trophy } from 'lucide-react';
import { MOCK_LEADERBOARD } from './communityData';
import GroupIcon from './GroupIcon';

export default function LeaderboardTab() {
    return (
        <motion.div key="tab-leaderboard" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 30 }} className="flex flex-col w-full max-w-2xl mx-auto pt-6 pb-24 relative min-h-dvh overflow-y-auto select-none bg-[#020202]" style={{ WebkitOverflowScrolling: 'touch' }}>

            {/* Header - Command Terminal */}
            <div className="text-center mb-10 w-full flex flex-col items-center">
                <span className="text-[8px] font-mono text-cyan-600/50 tracking-[0.3em] mb-2">{'>'}_ QUERY: LEADERBOARD_DATA_STREAM</span>
                <h3 className="text-2xl font-black tracking-[0.5em] uppercase text-cyan-400 font-mono drop-shadow-[0_0_15px_rgba(34,211,238,0.6)]">
                    Global Ranks
                </h3>
                <p className="text-[10px] text-gray-500 tracking-[0.3em] font-mono mt-1">HALL OF HEROES</p>
            </div>

            {/* ----- THE ALPHA PODIUM (Top 3) ----- */}
            <div className="flex items-end justify-center gap-3 mb-14 h-72 relative font-mono mt-4 px-2">

                {/* Rank 2 (Left - Cyan/Ice) */}
                <div className="flex flex-col items-center w-[30%] z-10 translate-y-6">
                    <div className="relative w-20 h-20 mb-3 flex justify-center items-center">
                        <div className="absolute inset-0 rounded-full border border-cyan-500/40 shadow-[0_0_12px_rgba(34,211,238,0.3)]" />
                        <div className="w-14 h-14 relative z-10"><GroupIcon type={MOCK_LEADERBOARD[1].group} /></div>
                        <div className="absolute -top-2 left-1/2 -translate-x-1/2 z-20 w-5 h-5 bg-[#050505] border border-cyan-500/60 rotate-45 flex items-center justify-center shadow-[0_0_8px_rgba(34,211,238,0.5)]">
                            <span className="text-[8px] font-black text-cyan-400 -rotate-45">2</span>
                        </div>
                    </div>
                    <div className="w-full bg-[#0a0a0a]/80 backdrop-blur-md border border-cyan-500/20 rounded-lg p-2 flex flex-col items-center">
                        <span className="text-[10px] font-black text-cyan-400 tracking-widest truncate w-full text-center">{MOCK_LEADERBOARD[1].name}</span>
                        <span className="text-[8px] font-mono text-cyan-400/40 mt-0.5 truncate w-full text-center">{MOCK_LEADERBOARD[1].group}</span>
                        <span className="text-[9px] font-mono text-cyan-500/60 mt-0.5">{MOCK_LEADERBOARD[1].xp.toLocaleString()} XP</span>
                    </div>
                </div>

                {/* Rank 1 (Center - Gold/Amber) */}
                <div className="flex flex-col items-center w-[35%] z-20">
                    <div className="relative w-28 h-28 mb-3 flex justify-center items-center">
                        <div className="absolute inset-0 rounded-full border border-yellow-500/50 shadow-[0_0_20px_rgba(234,179,8,0.3)]" />
                        <div className="absolute inset-1.5 rounded-full border border-yellow-400/30" />
                        <div className="absolute -top-6 z-30">
                            <Trophy size={24} className="text-yellow-500 drop-shadow-[0_0_10px_rgba(234,179,8,0.8)]" />
                        </div>
                        <div className="w-20 h-20 relative z-10"><GroupIcon type={MOCK_LEADERBOARD[0].group} /></div>
                        <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 z-20 w-6 h-6 bg-[#050505] border border-yellow-500/60 rotate-45 flex items-center justify-center shadow-[0_0_10px_rgba(234,179,8,0.5)]">
                            <span className="text-[9px] font-black text-yellow-400 -rotate-45">1</span>
                        </div>
                    </div>
                    <div className="w-full bg-[#0a0a0a]/80 backdrop-blur-md border border-yellow-500/30 rounded-lg p-3 mt-2 flex flex-col items-center">
                        <span className="text-sm font-black text-yellow-400 tracking-widest truncate w-full text-center">{MOCK_LEADERBOARD[0].name}</span>
                        <span className="text-[8px] font-mono text-yellow-400/40 mt-0.5 truncate w-full text-center">{MOCK_LEADERBOARD[0].group}</span>
                        <span className="text-[10px] font-mono text-yellow-500/70 mt-0.5">{MOCK_LEADERBOARD[0].xp.toLocaleString()} XP</span>
                    </div>
                </div>

                {/* Rank 3 (Right - Bronze/Orange) */}
                <div className="flex flex-col items-center w-[30%] z-10 translate-y-10">
                    <div className="relative w-20 h-20 mb-3 flex justify-center items-center">
                        <div className="absolute inset-0 rounded-full border border-orange-500/40 shadow-[0_0_12px_rgba(249,115,22,0.3)]" />
                        <div className="w-14 h-14 relative z-10"><GroupIcon type={MOCK_LEADERBOARD[2].group} /></div>
                        <div className="absolute -top-2 left-1/2 -translate-x-1/2 z-20 w-5 h-5 bg-[#050505] border border-orange-500/60 rotate-45 flex items-center justify-center shadow-[0_0_8px_rgba(249,115,22,0.5)]">
                            <span className="text-[8px] font-black text-orange-400 -rotate-45">3</span>
                        </div>
                    </div>
                    <div className="w-full bg-[#0a0a0a]/80 backdrop-blur-md border border-orange-500/20 rounded-lg p-2 flex flex-col items-center">
                        <span className="text-[10px] font-black text-orange-400 tracking-widest truncate w-full text-center">{MOCK_LEADERBOARD[2].name}</span>
                        <span className="text-[8px] font-mono text-orange-400/40 mt-0.5 truncate w-full text-center">{MOCK_LEADERBOARD[2].group}</span>
                        <span className="text-[9px] font-mono text-orange-500/60 mt-0.5">{MOCK_LEADERBOARD[2].xp.toLocaleString()} XP</span>
                    </div>
                </div>
            </div>

            {/* ----- BATTALION ROSTER (#4 - #10) ----- */}
            <div className="flex flex-col gap-2 font-mono px-4 relative z-10">
                {MOCK_LEADERBOARD.slice(3).map((entry) => (
                    <div key={entry.rank} className="flex items-center justify-between bg-[#050505]/60 backdrop-blur-md border border-white/5 hover:bg-[#111]/80 hover:border-cyan-500/30 p-3 rounded-lg transition-all group cursor-pointer">
                        <div className="flex items-center gap-3">
                            <span className="text-cyan-600/50 font-mono font-bold w-6 text-right text-xs group-hover:text-cyan-400 transition-colors">{String(entry.rank).padStart(2, '0')}</span>
                            <span className="text-xl w-8 text-center">{entry.badge}</span>
                            <div className="flex flex-col">
                                <span className="text-xs font-black tracking-wide text-white group-hover:brightness-125 transition-all truncate max-w-[120px] md:max-w-none" style={{ color: entry.color }}>{entry.name}</span>
                                <span className="text-[9px] text-white/30 font-mono truncate">{entry.group} · {entry.faculty}</span>
                            </div>
                        </div>
                        <div className="flex flex-col items-end">
                            <span className="text-[10px] font-mono font-bold text-cyan-400 tracking-wider">{entry.xp.toLocaleString()} XP</span>
                            <span className="text-[8px] font-mono text-white/30">{entry.accuracy}</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* --- FLOATING RANK CARD --- */}
            <div className="relative mt-8 left-0 right-0 px-4 z-50">
                <div className="bg-[#050505]/90 backdrop-blur-xl border border-cyan-500/30 p-4 rounded-lg shadow-[0_0_20px_rgba(6,182,212,0.15)] flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-9 h-9 bg-[#0a0a0a] border border-cyan-500/40 rotate-45 shadow-[0_0_8px_rgba(6,182,212,0.3)]">
                            <span className="text-cyan-400 font-black text-xs -rotate-45">#1</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-white font-black text-sm tracking-wide">YOU (Commander)</span>
                            <span className="text-[9px] text-cyan-600/60 uppercase tracking-widest font-mono">Elite Operative</span>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-cyan-400 font-black text-xl font-mono tracking-tight">15,420</div>
                        <div className="text-[8px] text-gray-500 uppercase font-mono tracking-widest">Total XP</div>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
