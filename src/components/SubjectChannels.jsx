import React, { useState, useRef, useEffect } from 'react';
import { Send, Image as ImageIcon, Smile, Hash, ShieldAlert, Radio, Activity, Crown, FileText, HelpCircle, Lock, Unlock, Pin, Paperclip, Stethoscope, Dna, Microscope, BookOpen } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const SUBJECTS = [
    { id: 'general', name: 'GENERAL-FORUM', icon: BookOpen, status: 'subscribed', color: 'text-cyan-400' },
    { id: 'internal-med', name: 'INTERNAL-MEDICINE', icon: Stethoscope, status: 'subscribed', color: 'text-purple-400' },
    { id: 'bio-chem', name: 'BIO-CHEMISTRY', icon: Dna, status: 'subscribed', color: 'text-green-400' },
    { id: 'pathology', name: 'PATHOLOGY', icon: Microscope, status: 'locked', color: 'text-red-400' },
];

const INITIAL_MESSAGES = {
    'general': [
        { id: 1, user: 'Cipher', factionBadge: '🐉', text: 'Welcome to the global academic hub. Post questions clearly to get faster answers.', time: '10:41', isMVP: false },
        { id: 2, user: 'Vanguard', factionBadge: '🐺', text: 'Does anyone have the syllabus link for this semester?', time: '10:45', isMVP: true },
    ],
    'internal-med': [
        { id: 1, user: 'Dr. Nora', factionBadge: '👑', text: 'Review the latest case study on acute myocardial infarction. It will be on the midterm.', time: '09:00', isMVP: true },
        { id: 2, user: 'StealthWing', factionBadge: '🐉', text: 'Understood. Is the focus on the ECG manifestations?', time: '09:05', isMVP: false },
    ],
    'bio-chem': [
        { id: 1, user: 'AlphaOne', factionBadge: '🐺', text: 'The TCA cycle visualization tool is now live in the Simulator tab.', time: '08:30', isMVP: true },
    ]
};

const PINNED_INTEL = {
    'general': 'Pin: Community Guidelines & Term Schedule PDF',
    'internal-med': 'Pin: Cardiology Case Study #44 - Required Reading',
    'bio-chem': 'Pin: Metabolic Pathways Interactive Cheat Sheet',
    'pathology': 'Pin: Tissue Slide Library Access Restricted'
};

export default function SubjectChannels() {
    const [activeSubject, setActiveSubject] = useState('internal-med');
    const [messages, setMessages] = useState(INITIAL_MESSAGES);
    const [inputValue, setInputValue] = useState('');
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, activeSubject]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (!inputValue.trim()) return;

        const newMessage = {
            id: Date.now(),
            user: 'You',
            factionBadge: '🐉',
            text: inputValue,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            isMVP: true
        };

        setMessages(prev => ({
            ...prev,
            [activeSubject]: [...(prev[activeSubject] || []), newMessage]
        }));
        setInputValue('');
    };

    const currentMessages = messages[activeSubject] || [];
    const isLocked = SUBJECTS.find(s => s.id === activeSubject)?.status === 'locked';

    return (
        <div className="flex flex-col md:flex-row h-full w-full bg-[#050505] rounded-xl overflow-hidden border border-white/10 shadow-[0_0_30px_rgba(0,0,0,0.8)] font-sans relative z-10">
            {/* Background Texture */}
            <div className="absolute inset-0 pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-[0.03]" />

            {/* ─── SIDEBAR: SUBJECT DIRECTORY ─── */}
            <div className="w-full md:w-64 bg-black/80 border-b md:border-b-0 md:border-r border-white/5 flex flex-col z-10 shrink-0 backdrop-blur-md">
                <div className="p-4 border-b border-white/5">
                    <h3 className="text-[10px] text-white/40 font-black tracking-[0.2em] flex items-center gap-2">
                        <BookOpen size={12} className="text-cyan-500" /> ACADEMIC CHANNELS
                    </h3>
                </div>
                <div className="p-3 flex md:flex-col gap-2 overflow-x-auto md:overflow-y-auto hide-scrollbar">
                    {SUBJECTS.map(subject => {
                        const Icon = subject.icon;
                        const isActive = activeSubject === subject.id;
                        const isChannelLocked = subject.status === 'locked';

                        return (
                            <button
                                key={subject.id}
                                onClick={() => setActiveSubject(subject.id)}
                                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-left group shrink-0 w-52 md:w-auto ${isActive ? 'bg-white/10 border-white/20' : 'bg-transparent border-transparent hover:bg-white/5'} border`}
                            >
                                <Icon size={16} className={isActive ? subject.color : 'text-white/30'} />
                                <div className="flex flex-col flex-1 truncate">
                                    <span className={`text-xs font-bold tracking-widest truncate ${isActive ? 'text-white' : 'text-white/60 group-hover:text-white'} ${isChannelLocked ? 'opacity-50' : ''}`}>
                                        {subject.name}
                                    </span>
                                </div>
                                {isChannelLocked ? (
                                    <Lock size={12} className="text-red-400 shrink-0 opacity-70" />
                                ) : (
                                    <Unlock size={12} className="text-cyan-400 shrink-0 opacity-50" />
                                )}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* ─── MAIN AREA: SCHOLARLY FEED & INPUT ─── */}
            <div className="flex-1 flex flex-col relative z-20 min-w-0 bg-[#0a0a0a]/50">
                {/* Header Region for Active Channel */}
                <div className="px-6 py-4 border-b border-white/5 bg-black/40 backdrop-blur-sm flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-3">
                        <Hash size={20} className="text-white/30" />
                        <h2 className="text-sm font-black tracking-[0.2em] text-white flex items-center gap-2">
                            {SUBJECTS.find(s => s.id === activeSubject)?.name}
                        </h2>
                    </div>
                </div>

                {/* PINNED INTEL BANNER */}
                <div className="w-full bg-cyan-950/30 border-b border-cyan-500/20 px-6 py-2 flex items-center gap-3 shadow-[0_2px_10px_rgba(6,182,212,0.05)]">
                    <div className="bg-cyan-500/20 p-1 rounded">
                        <Pin size={12} className="text-cyan-400" />
                    </div>
                    <span className="text-[10px] text-cyan-100 font-bold tracking-wider truncate">
                        {PINNED_INTEL[activeSubject]}
                    </span>
                </div>

                {/* Messages Feed */}
                <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-4 font-mono hide-scrollbar">
                    {isLocked ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-center opacity-50">
                            <Lock size={48} className="text-red-500 mb-4" />
                            <h3 className="text-white font-bold tracking-widest mb-2">COURSE LOCKED</h3>
                            <p className="text-xs text-white/50 max-w-xs">You are not currently enrolled in this academic track. Visit the Curriculum Vault to register.</p>
                        </div>
                    ) : (
                        <AnimatePresence initial={false}>
                            {currentMessages.map((msg) => (
                                <motion.div
                                    key={msg.id}
                                    initial={{ opacity: 0, y: 10, scale: 0.98 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    className="flex flex-col"
                                >
                                    <div className="flex flex-col gap-1 w-full max-w-[90%] md:max-w-[70%]">
                                        <div className="flex items-baseline gap-2">
                                            {/* Faction Badge */}
                                            <span className="text-xs drop-shadow-[0_0_5px_rgba(255,255,255,0.3)]">{msg.factionBadge}</span>

                                            <span className={`text-xs font-bold leading-none ${msg.user === 'You' ? 'text-white' : 'text-white/80'}`}>
                                                {msg.user}
                                            </span>
                                            <span className="text-[8px] text-white/30 ml-2 font-sans tracking-wide">{msg.time}</span>
                                        </div>
                                        <div
                                            className={`p-3 rounded-tr-xl rounded-b-xl backdrop-blur-md border text-sm shadow-lg ${msg.user === 'You'
                                                    ? 'bg-cyan-900/20 border-cyan-500/30 text-cyan-50'
                                                    : msg.isMVP
                                                        ? 'bg-white/5 border-purple-500/50 text-white/90 shadow-[0_0_10px_rgba(168,85,247,0.1)]'
                                                        : 'bg-white/5 border-white/10 text-white/80'
                                                }`}
                                        >
                                            <p className="font-sans leading-relaxed tracking-wide">{msg.text}</p>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Tactical Input Region */}
                <div className="p-4 border-t border-white/5 bg-black/60 backdrop-blur-md shrink-0">
                    <form onSubmit={handleSendMessage} className="flex flex-col sm:flex-row items-center gap-3">
                        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto hide-scrollbar pb-2 sm:pb-0">
                            {/* Quick Action Button: Share Note */}
                            <button type="button" className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 hover:bg-cyan-500/20 text-cyan-400 transition-colors shrink-0 text-[10px] font-bold tracking-wider uppercase">
                                <FileText size={12} /> Note
                            </button>
                            {/* Quick Action Button: Ask Question */}
                            <button type="button" className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 text-purple-400 transition-colors shrink-0 text-[10px] font-bold tracking-wider uppercase">
                                <HelpCircle size={12} /> Ask
                            </button>
                        </div>

                        <div className="flex flex-1 items-center gap-2 w-full bg-black/50 border border-white/10 focus-within:border-cyan-500/50 rounded-lg pr-1 transition-all shadow-inner relative">
                            <input
                                type="text"
                                disabled={isLocked}
                                placeholder={isLocked ? "CHANNEL LOCKED" : "Input response or query..."}
                                value={inputValue}
                                onChange={e => setInputValue(e.target.value)}
                                className="flex-1 bg-transparent px-4 py-3 text-sm text-white placeholder-white/20 outline-none font-mono tracking-wide disabled:opacity-50"
                            />

                            <button type="button" disabled={isLocked} className="p-2 rounded-lg text-white/30 hover:text-white transition-colors disabled:opacity-50">
                                <Paperclip size={16} />
                            </button>

                            <button
                                type="submit"
                                disabled={!inputValue.trim() || isLocked}
                                className="p-2.5 mr-1 bg-cyan-600 hover:bg-cyan-500 disabled:bg-white/5 disabled:hover:bg-white/5 text-white disabled:text-white/20 rounded-lg transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)] disabled:shadow-none shrink-0 group focus:outline-none"
                            >
                                <Send size={16} className={(!inputValue.trim() || isLocked) ? '' : 'group-hover:translate-x-1 transition-transform'} />
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            <style>{`
                .hide-scrollbar::-webkit-scrollbar {
                    display: none;
                }
                .hide-scrollbar {
                    -ms-overflow-style: none;
                    scrollbar-width: none;
                }
            `}</style>
        </div>
    );
}
