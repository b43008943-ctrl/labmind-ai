import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, Search, Play, Trash2, BrainCircuit } from 'lucide-react';

/* ═══════════════════════════════════════════════════════════════
   ARCHIVE SCREEN — SAVED AI VIDEOS GALLERY
═══════════════════════════════════════════════════════════════ */

export default function ArchiveScreen({ onNavigate }) {
    const [searchQuery, setSearchQuery] = useState('');

    // Dummy Data for Saved Videos
    const [videos, setVideos] = useState([
        { id: 1, title: 'Physics Lecture 01: Quantum Mechanics Basics', date: 'Feb 28', duration: '2:30 min' },
        { id: 2, title: 'Neural Anatomy: 3D Brain Mapping', date: 'Feb 27', duration: '5:45 min' },
        { id: 3, title: 'Microbiology Sim: Virus Propagation', date: 'Feb 26', duration: '1:15 min' },
        { id: 4, title: 'Cardiac Cycle Explainer (Clinical)', date: 'Feb 24', duration: '4:20 min' },
        { id: 5, title: 'Biochemistry: Kreb Cycle deep-dive', date: 'Feb 20', duration: '10:00 min' },
    ]);

    // Delete a video
    const handlePurge = (id) => {
        setVideos(videos.filter(v => v.id !== id));
        const purgeEvent = new CustomEvent('nymph-dialog-event', { detail: 'purged' });
        window.dispatchEvent(purgeEvent);
    };

    // Filter videos based on search
    const filteredVideos = videos.filter(video =>
        video.title.toLowerCase().includes(searchQuery.toLowerCase())
    );



    return (
        <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 z-50 overflow-y-auto overflow-x-hidden w-full h-dvh text-white"
            style={{ fontFamily: "'Montserrat', sans-serif" }}
        >
            {/* ─── AMBIENT BACKGROUND ─── */}
            <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
                <div className="absolute top-[-25%] left-[-10%] w-[55%] h-[55%] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255,215,0,0.12) 0%, transparent 70%)', filter: 'blur(150px)' }} />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full" style={{ background: 'radial-gradient(circle, rgba(0,240,255,0.1) 0%, transparent 70%)', filter: 'blur(150px)' }} />
                <div className="absolute top-[50%] left-[50%] -translate-x-1/2 -translate-y-1/2 w-[35%] h-[35%] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255,215,0,0.06) 0%, transparent 70%)', filter: 'blur(120px)' }} />
            </div>

            {/* ─── TOP BAR ─── */}
            <div className="sticky top-0 left-0 w-full px-4 md:px-8 py-3 flex items-center justify-between z-40 border-b border-white/5"
                style={{ background: 'rgba(5,5,16,0.5)', backdropFilter: 'blur(30px)', WebkitBackdropFilter: 'blur(30px)' }}>
                <div className="flex items-center gap-3">
                    <button onClick={() => onNavigate('academic-hub')}
                        className="flex items-center gap-2 px-3 py-2 rounded-full border border-white/10 text-white/70 hover:text-white hover:bg-white/5 hover:border-[#FFD700]/30 transition-all cursor-pointer"
                        style={{ background: 'rgba(255,255,255,0.03)' }}>
                        <ChevronLeft size={16} strokeWidth={2} />
                        <span className="text-[10px] font-bold tracking-[0.12em] uppercase">Back</span>
                    </button>
                    <div className="hidden md:block ml-1">
                        <h2 className="text-[18px] font-bold tracking-tight text-white flex items-center gap-2">
                            <BrainCircuit size={20} strokeWidth={1.5} className="text-[#00F0FF]" style={{ filter: 'drop-shadow(0 0 8px rgba(0,240,255,0.6))' }} />
                            Archive Gallery
                        </h2>
                        <p className="text-[9px] text-[#00F0FF] font-semibold tracking-[0.2em] uppercase">Secure Video Vault</p>
                    </div>
                    {/* Mobile title */}
                    <h2 className="md:hidden text-[14px] font-bold tracking-tight text-white flex items-center gap-2">
                        <BrainCircuit size={16} strokeWidth={1.5} className="text-[#00F0FF]" />
                        Archive
                    </h2>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-[#00FF9D] animate-pulse" style={{ boxShadow: '0 0 8px #00FF9D' }} />
                    <span className="text-[9px] font-bold tracking-widest uppercase text-[#00FF9D] hidden sm:inline">Secure</span>
                </div>
            </div>

            <div className="relative z-10 w-full max-w-7xl mx-auto p-4 md:p-8 flex flex-col gap-8">

                {/* ─── SEARCH BAR ─── */}
                <div className="w-full max-w-md mx-auto">
                    <div className="relative flex items-center w-full" style={{
                        background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(15px)',
                        border: '1px solid rgba(255,255,255,0.1)', borderRadius: '20px', padding: '12px 20px',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.3), inset 0 0 10px rgba(255,255,255,0.02)'
                    }}>
                        <Search size={18} className="text-white/40 mr-3" />
                        <input
                            type="text"
                            placeholder="Search archived videos..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="bg-transparent border-none outline-none text-white text-[13px] font-medium tracking-wide w-full placeholder-white/30"
                        />
                    </div>
                </div>

                {/* ─── FLOATING GRID ─── */}
                <div className="grid gap-5" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
                    {filteredVideos.map((video) => (
                        <div key={video.id} className="video-card group cursor-pointer flex flex-col gap-3">
                            <div className="video-thumbnail relative w-full overflow-hidden flex items-center justify-center" style={{
                                aspectRatio: '16/9', background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(15px)',
                                border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px',
                                boxShadow: '0 10px 30px rgba(0,0,0,0.5), inset 0 0 15px rgba(255,255,255,0.05)'
                            }}>
                                {/* Play Icon Overlay */}
                                <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/40 transition-colors z-10">
                                    <Play size={48} strokeWidth={1} className="text-white opacity-40 group-hover:opacity-100 group-hover:scale-110 transition-all duration-300" style={{ filter: 'drop-shadow(0 0 10px rgba(255,255,255,0.6))' }} />
                                </div>

                                {/* Trash Icon (Top Right) */}
                                <button
                                    onClick={(e) => { e.stopPropagation(); handlePurge(video.id); }}
                                    className="absolute top-3 right-3 z-20 opacity-0 group-hover:opacity-100 transition-opacity p-2 rounded-full hover:bg-white/10"
                                >
                                    <Trash2 size={16} strokeWidth={1.5} className="text-white drop-shadow-[0_0_5px_rgba(255,255,255,0.6)] hover:scale-110 transition-transform" />
                                </button>
                            </div>

                            {/* Metadata */}
                            <div className="flex flex-col gap-1 px-1">
                                <h3 className="text-[13px] font-bold tracking-wide text-white/90 leading-snug group-hover:text-[#00F0FF] transition-colors">{video.title}</h3>
                                <div className="flex items-center gap-2 text-[10px] font-semibold tracking-widest uppercase text-white/40">
                                    <span>{video.date}</span>
                                    <span className="w-1 h-1 rounded-full bg-white/20" />
                                    <span>{video.duration}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {filteredVideos.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 opacity-50">
                        <Search size={48} strokeWidth={1} className="text-white/20 mb-4" />
                        <p className="text-[12px] font-bold tracking-[0.15em] uppercase text-white/40">No records found in Vault</p>
                    </div>
                )}
            </div>

            <style>{`
                .video-card .video-thumbnail {
                    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
                }
                .video-card:hover .video-thumbnail {
                    transform: scale(1.03);
                    border-color: rgba(255,255,255,0.4);
                    box-shadow: 0 15px 40px rgba(0,0,0,0.6), inset 0 0 25px rgba(255,255,255,0.1), 0 0 20px rgba(255,255,255,0.2);
                }
            `}</style>
        </motion.div>
    );
}
