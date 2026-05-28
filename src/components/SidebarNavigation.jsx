import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Home, FolderHeart, Settings, Sparkles, ChevronRight } from 'lucide-react';

export default function SidebarNavigation({ onNavigate }) {
    const [isOpen, setIsOpen] = useState(false);

    const navItems = [
        { id: 'dashboard', label: 'Dashboard', icon: Home },
        { id: 'history', label: 'Patient History', icon: FolderHeart },
        { id: 'settings', label: 'Lab Settings', icon: Settings },
        { id: 'guide', label: 'Help & AI Guide', icon: Sparkles },
    ];

    return (
        <div
            className="fixed left-0 top-1/2 -translate-y-1/2 z-9000 flex items-center print:hidden"
            onMouseEnter={() => setIsOpen(true)}
            onMouseLeave={() => setIsOpen(false)}
        >
            {/* The sliding panel */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 240, opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                        className="h-[60vh] max-h-[500px] bg-slate-900/80 backdrop-blur-3xl border border-white/10 border-l-0 rounded-r-3xl shadow-[20px_0_50px_rgba(0,0,0,0.5)] overflow-hidden flex flex-col py-6"
                    >
                        <div className="px-6 mb-6">
                            <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest flex items-center gap-2 drop-shadow-[0_0_8px_rgba(34,211,238,0.8)]">
                                <Sparkles className="w-4 h-4" /> LabMind Sys
                            </h3>
                        </div>

                        <div className="flex flex-col gap-2 px-3">
                            {navItems.map((item) => (
                                <button
                                    key={item.id}
                                    onClick={() => {
                                        if (item.id === 'dashboard') onNavigate('dashboard');
                                        setIsOpen(false);
                                    }}
                                    className="group flex items-center gap-4 w-full p-3 rounded-xl hover:bg-slate-800/80 transition-all border border-transparent hover:border-cyan-500/30"
                                >
                                    <item.icon className="w-5 h-5 text-slate-400 group-hover:text-cyan-400 group-hover:drop-shadow-[0_0_10px_rgba(34,211,238,0.8)] transition-all" />
                                    <span className="text-sm font-semibold text-slate-300 group-hover:text-white tracking-wide transition-colors whitespace-nowrap">
                                        {item.label}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* The Pull Handle */}
            <motion.div
                animate={{ x: isOpen ? 0 : 0 }}
                className="w-8 h-32 rounded-r-2xl bg-slate-900/40 backdrop-blur-3xl border border-white/10 border-l-0 flex items-center justify-center cursor-pointer group shadow-[5px_0_15px_rgba(0,0,0,0.3)] pointer-events-auto"
                onClick={() => setIsOpen(!isOpen)}
            >
                {/* Neon Accent */}
                <div className="absolute right-0 top-0 bottom-0 w-[2px] bg-cyan-400 shadow-[0_0_15px_#22d3ee] rounded-r-2xl opacity-50 group-hover:opacity-100 transition-opacity"></div>

                <ChevronRight
                    strokeWidth={1.5}
                    className={`w-5 h-5 text-slate-300 group-hover:text-cyan-400 group-hover:drop-shadow-[0_0_8px_rgba(34,211,238,0.8)] transition-all duration-300 ${isOpen ? 'rotate-180' : ''}`}
                />
            </motion.div>
        </div>
    );
}
