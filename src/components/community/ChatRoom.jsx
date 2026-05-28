/* ChatRoom — Full-screen chat room portal with header, messages, input bar, keyboards */

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, Search, Send, X, Settings, Trash2, AlertTriangle, Paperclip, Smile, Mic, CheckCheck, MoreVertical, Info, BellOff, LogOut, Camera } from 'lucide-react';
import { getGroupColor, hex2rgba } from './communityData';
import GroupIcon from './GroupIcon';
import VoiceMessage from './VoiceMessage';

export default function ChatRoom({
    activeChat,
    groups,
    setGroups,
    setActiveChat,
    onClose,
}) {
    const [message, setMessage] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [isRecording, setIsRecording] = useState(false);
    const [activeKeyboard, setActiveKeyboard] = useState('none');
    const [pendingImage, setPendingImage] = useState(null);
    const [pendingAudio, setPendingAudio] = useState(null);
    const [isTransmitting, setIsTransmitting] = useState(false);
    const [audioSwipeOffset, setAudioSwipeOffset] = useState(0);
    const [isBinningAudio, setIsBinningAudio] = useState(false);

    const [isHeaderSearchActive, setIsHeaderSearchActive] = useState(false);
    const [headerSearchQuery, setHeaderSearchQuery] = useState('');
    const [isHeaderMenuOpen, setIsHeaderMenuOpen] = useState(false);

    const [showGroupSettings, setShowGroupSettings] = useState(false);
    const [editGroupName, setEditGroupName] = useState('');
    const [editGroupIcon, setEditGroupIcon] = useState('');
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const recordingStartTimeRef = useRef(null);
    const micTimeoutRef = useRef(null);
    const inputRef = useRef(null);

    useEffect(() => {
        setChatHistory([]);
    }, [activeChat]);

    useEffect(() => {
        if (activeChat && showGroupSettings) {
            setEditGroupName(activeChat.name || '');
            setEditGroupIcon(activeChat.iconName || activeChat.icon || activeChat.name || '');
        }
    }, [activeChat, showGroupSettings]);

    const handleSaveGroupSettings = () => {
        if (!editGroupName.trim() || !editGroupIcon) return;
        const groupIndex = groups.findIndex(g => g.id === activeChat.id);
        if (groupIndex === -1) return;
        const updatedGroup = {
            ...groups[groupIndex],
            name: editGroupName,
            icon: editGroupIcon,
            iconName: editGroupIcon.toLowerCase(),
        };
        const updatedGroupsArray = [...groups];
        updatedGroupsArray[groupIndex] = updatedGroup;
        setGroups(updatedGroupsArray);
        setActiveChat(updatedGroup);
        setShowGroupSettings(false);
    };

    const handleDeleteGroup = () => {
        setShowDeleteConfirm(true);
    };

    const handleSendMessage = () => {
        if (!message.trim() && !pendingImage && !pendingAudio) return;
        setIsTransmitting(true);
        setTimeout(() => {
            const tempHistory = [];
            const nowTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + " SEC_TRK";
            if (pendingAudio) {
                tempHistory.push({ id: Date.now() + 1, type: 'audio', audioUrl: pendingAudio.audioUrl, duration: pendingAudio.duration, time: nowTime });
            }
            if (pendingImage) {
                tempHistory.push({ id: Date.now() + 2, text: message.trim() ? message : '', type: 'image', image: pendingImage, time: nowTime });
            } else if (message.trim()) {
                tempHistory.push({ id: Date.now() + 3, text: message, type: 'text', time: nowTime });
            }
            setChatHistory(prev => [...prev, ...tempHistory]);
            setPendingAudio(null);
            setPendingImage(null);
            setMessage('');
            setActiveKeyboard('none');
            setIsTransmitting(false);
        }, 400);
    };

    const handleStartRecording = (e) => {
        if (e) { e.preventDefault(); e.stopPropagation(); }
        if (micTimeoutRef.current) clearTimeout(micTimeoutRef.current);
        micTimeoutRef.current = setTimeout(async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorderRef.current = new MediaRecorder(stream);
                mediaRecorderRef.current.ondataavailable = (event) => {
                    if (event.data.size > 0) audioChunksRef.current.push(event.data);
                };
                mediaRecorderRef.current.onstop = () => {
                    const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    const durationSeconds = recordingStartTimeRef.current ? Math.floor((Date.now() - recordingStartTimeRef.current) / 1000) : 0;
                    const displaySeconds = Math.max(1, durationSeconds);
                    const durationText = `0:${displaySeconds < 10 ? '0' : ''}${displaySeconds}`;
                    setPendingAudio({ audioUrl, duration: durationText, seconds: displaySeconds });
                    stream.getTracks().forEach(track => track.stop());
                    audioChunksRef.current = [];
                    setIsRecording(false);
                    setAudioSwipeOffset(0);
                };
                audioChunksRef.current = [];
                recordingStartTimeRef.current = Date.now();
                mediaRecorderRef.current.start();
                setIsRecording(true);
                setAudioSwipeOffset(0);
                setIsBinningAudio(false);
            } catch (err) {
                console.error("Microphone access denied or error:", err);
                alert("ACCESS DENIED: MICROPHONE PERMISSION REQUIRED.");
                setIsRecording(false);
            }
        }, 250);
    };

    const handleStopRecording = (e) => {
        if (e) { e.preventDefault(); e.stopPropagation(); }
        if (micTimeoutRef.current) { clearTimeout(micTimeoutRef.current); micTimeoutRef.current = null; }
        if (isBinningAudio) {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
                mediaRecorderRef.current = null;
            }
            setIsRecording(false);
            setTimeout(() => { setIsBinningAudio(false); setAudioSwipeOffset(0); }, 300);
            return;
        }
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
        } else {
            setIsRecording(false);
        }
        setAudioSwipeOffset(0);
    };

    const handleMicPointerMove = (e) => {
        if (!isRecording || isBinningAudio) return;
        if (e.movementX < 0) {
            setAudioSwipeOffset(prev => {
                const newOffset = prev + e.movementX;
                if (newOffset < -100) setIsBinningAudio(true);
                return newOffset;
            });
        }
    };

    const triggerImagePicker = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.onchange = (e) => {
            if (e.target.files && e.target.files[0]) {
                const reader = new FileReader();
                reader.onload = (event) => { setPendingImage(event.target.result); setActiveKeyboard('none'); };
                reader.readAsDataURL(e.target.files[0]);
            }
        };
        input.click();
    };

    const toggleKeyboard = (type) => {
        if (activeKeyboard === type) { setActiveKeyboard('none'); } else { setActiveKeyboard(type); if (inputRef.current) inputRef.current.blur(); }
    };

    const addEmoji = (emoji) => { setMessage(prev => prev + emoji); };

    if (!activeChat) return null;

    const chatColor = getGroupColor(activeChat.icon || activeChat.name);

    return (
        <div
            className="fixed inset-0 w-full h-full z-50 bg-[#0A0A0C] flex flex-col font-mono overscroll-none overflow-hidden touch-none"
            style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0 }}
            onTouchStart={(e) => e.stopPropagation()}
            onTouchMove={(e) => e.stopPropagation()}
            onTouchEnd={(e) => e.stopPropagation()}
        >
            {/* Corner Brackets HUD Overlay */}
            <div className="absolute top-[84px] left-4 w-4 h-4 border-l border-t border-white/20 pointer-events-none z-30" />
            <div className="absolute top-[84px] right-4 w-4 h-4 border-r border-t border-white/20 pointer-events-none z-30" />

            {/* 1. TACTICAL HEADER */}
            <div className="h-16 border-b border-white/5 bg-black/60 backdrop-blur-xl flex items-center justify-between px-3 relative shrink-0 z-50">
                <div className="absolute inset-x-0 bottom-0 h-px opacity-30" style={{ background: `linear-gradient(90deg, transparent, ${chatColor}, transparent)`, boxShadow: `0 0 15px ${chatColor}` }} />

                <AnimatePresence mode="popLayout">
                    {isHeaderSearchActive ? (
                        <motion.div key="search" initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -50 }} className="flex-1 flex items-center gap-2 h-full z-10 mr-2">
                            <div className="flex-1 flex items-center bg-black/40 border border-cyan-500/50 rounded-full px-4 py-2 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                                <Search size={16} className="text-cyan-400 mr-2" />
                                <input autoFocus type="text" value={headerSearchQuery} onChange={(e) => setHeaderSearchQuery(e.target.value)} placeholder="Search neuro-link..." className="flex-1 bg-transparent text-white text-sm outline-none placeholder:text-white/30 font-sans" style={{ caretColor: chatColor }} />
                                <button onClick={() => { setIsHeaderSearchActive(false); setHeaderSearchQuery(''); }} className="p-1 cursor-pointer text-cyan-400 hover:text-white transition-colors"><X size={16} strokeWidth={2.5} /></button>
                            </div>
                        </motion.div>
                    ) : (
                        <motion.div key="header-info" initial={{ opacity: 0, x: -50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 50 }} className="flex flex-1 items-center gap-1 z-10">
                            <button onClick={() => { onClose(); setShowGroupSettings(false); }} className="p-2 text-white/60 hover:text-white transition-colors cursor-pointer rounded-full hover:bg-white/5 -ml-2 shrink-0">
                                <ChevronLeft size={28} strokeWidth={1.5} />
                            </button>
                            <div className="w-10 h-10 relative flex items-center justify-center shrink-0 rounded-full cursor-pointer hover:scale-105 transition-transform" onClick={() => setShowGroupSettings(!showGroupSettings)}>
                                <div className="absolute inset-0 opacity-20 blur-md rounded-full" style={{ backgroundColor: chatColor }} />
                                <div className="w-full h-full p-1" style={{ dropShadow: `0 0 5px ${chatColor}` }}><GroupIcon type={activeChat.icon || activeChat.name} /></div>
                            </div>
                            <div className="ml-2 flex flex-col cursor-pointer overflow-hidden" onClick={() => setShowGroupSettings(!showGroupSettings)}>
                                <h2 className="text-[15px] font-bold tracking-wide text-white font-sans truncate">{activeChat?.name || "Network"}</h2>
                                <div className="flex items-center gap-1.5 mt-0.5">
                                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_#22c55e]" />
                                    <span className="text-[11px] text-green-400 font-sans tracking-wide whitespace-nowrap">{(activeChat?.members || "0") + " members, 12 online"}</span>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div className="flex items-center gap-1 text-white/60 z-20 shrink-0">
                    <button onClick={() => { if (!isHeaderMenuOpen) setIsHeaderSearchActive(prev => !prev); setIsHeaderMenuOpen(false); }} className={`p-2.5 rounded-full hover:bg-white/5 transition-colors cursor-pointer ${isHeaderSearchActive ? 'text-cyan-400' : ''}`}>
                        <Search size={22} strokeWidth={1.5} />
                    </button>
                    <div className="relative">
                        <button onClick={() => setIsHeaderMenuOpen(prev => !prev)} className={`p-2.5 rounded-full hover:bg-white/5 transition-colors cursor-pointer ${isHeaderMenuOpen ? 'text-cyan-400' : ''}`}>
                            <MoreVertical size={22} strokeWidth={1.5} />
                        </button>
                        <AnimatePresence>
                            {isHeaderMenuOpen && (
                                <motion.div initial={{ opacity: 0, scale: 0.8, y: -10 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.8, y: -10 }} transition={{ type: "spring", stiffness: 350, damping: 25 }} className="absolute top-full right-0 mt-2 w-56 bg-[#0A0A0C]/95 backdrop-blur-3xl border border-white/10 rounded-2xl shadow-[0_10px_40px_rgba(0,0,0,0.8)] overflow-hidden flex flex-col origin-top-right z-50">
                                    <button onClick={() => { setIsHeaderMenuOpen(false); setShowGroupSettings(true); }} className="flex items-center gap-3 px-4 py-3 hover:bg-white/5 transition-colors text-white/70 hover:text-white cursor-pointer w-full text-left">
                                        <Info size={16} /> <span className="text-sm font-sans font-medium">Group Info</span>
                                    </button>
                                    <button onClick={() => setIsHeaderMenuOpen(false)} className="flex items-center gap-3 px-4 py-3 hover:bg-white/5 transition-colors text-white/70 hover:text-white cursor-pointer w-full text-left">
                                        <BellOff size={16} /> <span className="text-sm font-sans font-medium">Mute Notifications</span>
                                    </button>
                                    <button onClick={() => { setIsHeaderMenuOpen(false); setChatHistory([]); }} className="flex items-center gap-3 px-4 py-3 hover:bg-white/5 transition-colors text-white/70 hover:text-white cursor-pointer w-full text-left">
                                        <Trash2 size={16} /> <span className="text-sm font-sans font-medium">Clear History</span>
                                    </button>
                                    <div className="h-px bg-white/10 mx-2" />
                                    <button onClick={() => { setIsHeaderMenuOpen(false); setShowDeleteConfirm(true); }} className="flex items-center gap-3 px-4 py-3 hover:bg-red-500/10 transition-colors text-red-500 hover:text-red-400 hover:[text-shadow:0_0_10px_rgba(239,68,68,0.8)] cursor-pointer w-full text-left">
                                        <LogOut size={16} /> <span className="text-sm font-sans font-bold">Leave Group</span>
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>

            {/* 2. Messages or Settings Panel */}
            {showGroupSettings ? (
                <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 items-center">
                    <h3 className="text-white/50 text-xs font-bold tracking-widest uppercase mt-4">Manage Faction Settings</h3>
                    <div className="flex flex-col items-center gap-4 w-full">
                        <div className="w-full max-w-[200px] h-40 flex items-center justify-center mb-2 animate-hologram-flicker relative">
                            <div className="absolute inset-0 opacity-15 blur-[60px] pointer-events-none rounded-2xl" style={{ backgroundColor: getGroupColor(editGroupIcon) }} />
                            <div className="absolute inset-0 bg-linear-to-b from-transparent via-white/5 to-transparent bg-[length:100%_4px] animate-scan opacity-50 rounded-2xl" />
                            <GroupIcon type={editGroupIcon} />
                        </div>
                        <span className="text-xs text-cyan-400">Select Hologram ID:</span>
                        <div className="flex flex-row gap-4 overflow-x-auto py-4 bg-black/40 p-4 rounded-lg border border-white/10 hide-scrollbar w-full">
                            {['Dragon', 'Mermaid', 'Beast', 'Crown', 'Robot', 'Unicorn', 'Alien', 'Ghost'].map(icon => (
                                <div key={icon} onClick={() => setEditGroupIcon(icon)} className={`cursor-pointer w-20 h-20 shrink-0 transition-colors flex items-center justify-center relative ${editGroupIcon.toLowerCase() === icon.toLowerCase() ? 'bg-cyan-500/10 border border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.5)] rounded-lg' : 'border border-transparent'}`}>
                                    <GroupIcon type={icon} />
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="flex flex-col gap-2 w-full mt-4">
                        <span className="text-xs text-white/50">Faction Designation:</span>
                        <input type="text" value={editGroupName} onChange={(e) => setEditGroupName(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg py-3 px-5 text-white outline-none focus:border-cyan-500 text-center transition-colors font-bold tracking-wide" />
                    </div>
                    <button onClick={handleSaveGroupSettings} className="w-full mt-8 py-3 bg-linear-to-r from-cyan-600 to-blue-600 text-white font-bold rounded-lg shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:shadow-[0_0_30px_rgba(6,182,212,0.6)] hover:scale-[1.02] transition-all tracking-widest">
                        INITIALIZE OVERRIDE
                    </button>
                    <div className="mt-6 pt-4 border-t w-full border-white/10">
                        <p className="text-[10px] text-red-500/60 uppercase tracking-widest mb-2 text-center">Danger Zone</p>
                        <button onClick={handleDeleteGroup} className="w-full py-2.5 bg-red-500/10 border border-red-500/30 text-red-500 rounded-xl text-xs font-bold hover:bg-red-500 hover:text-white transition-all shadow-[0_0_15px_rgba(239,68,68,0.1)] flex items-center justify-center gap-2">
                            <Trash2 size={14} /> Disband Faction
                        </button>
                    </div>
                </div>
            ) : (
                <div className="flex-1 overflow-y-auto p-4 pb-28 flex flex-col gap-2 relative bg-[#080808] z-0">
                    <div className="absolute inset-0 pointer-events-none opacity-[0.15] z-0" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.05) 2px, rgba(255,255,255,0.05) 4px)' }} />
                    <div className="absolute inset-0 pointer-events-none bg-black/40 mix-blend-multiply z-0" />
                    <div className="absolute inset-x-0 h-1 bg-white/10 animate-scan top-0 z-10 pointer-events-none shadow-[0_0_15px_rgba(255,255,255,0.2)]" />

                    <div className="flex justify-center my-2">
                        <div className="bg-black/40 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-sans text-white/40 border border-white/5">
                            Secure Network Initialized
                        </div>
                    </div>

                    {/* System Admin welcome message */}
                    <div className="flex flex-col items-start mb-2 relative group max-w-[85%]">
                        <div className="p-2.5 px-3.5 rounded-2xl rounded-tl-none relative bg-white/5 border border-white/10 shadow-md backdrop-blur-md">
                            <svg width="10" height="15" viewBox="0 0 10 15" className="absolute -left-[9px] -top-px text-white/5" fill="currentColor" style={{ filter: 'drop-shadow(-1px 0 0 rgba(255,255,255,0.1))' }}>
                                <path d="M10 0C10 0 0 0 0 0C0 0 0 5 3 8C6 11 10 15 10 15V0Z" />
                                <path d="M10 0L0 0C0 0 0 5 3 8" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="2" />
                            </svg>
                            <div className="text-[11px] font-sans font-semibold mb-0.5" style={{ color: chatColor }}>System Admin</div>
                            <p className="text-[13px] font-sans text-white/90 leading-relaxed wrap-break-word relative z-10">
                                Welcome to the <span className="font-bold">{activeChat?.name}</span> secure neural link. All tactical transmissions are end-to-end encrypted.
                            </p>
                            <div className="flex justify-end gap-1 mt-1 -mb-0.5 items-center opacity-40 relative z-10">
                                <span className="text-[9px] font-mono tracking-widest text-white">10:42 SEC_TRK</span>
                            </div>
                        </div>
                    </div>

                    {/* User Messages */}
                    {chatHistory.map((msg) => {
                        const bubbleBg = hex2rgba(chatColor, 0.10);
                        return (
                            <div key={msg.id} className="flex flex-col items-end mb-2 relative group self-end max-w-[85%]">
                                <div className="p-px relative rounded-2xl rounded-tr-none shadow-md overflow-visible" style={{ background: bubbleBg, boxShadow: `0 4px 10px rgba(0,0,0,0.5)`, border: `1px solid ${chatColor}` }}>
                                    <div className="p-2.5 px-3.5 backdrop-blur-xl rounded-2xl rounded-tr-none overflow-hidden relative">
                                        <div className="absolute inset-0 bg-linear-to-t from-white/5 to-transparent bg-size-[100%_4px] animate-scan opacity-20 pointer-events-none" />
                                        <svg width="10" height="15" viewBox="0 0 10 15" className="absolute -right-[10px] -top-px" fill={bubbleBg} style={{ filter: `drop-shadow(1px 0 0 ${chatColor})` }}>
                                            <path d="M0 0C0 0 10 0 10 0C10 0 10 5 7 8C4 11 0 15 0 15V0Z" />
                                            <path d="M0 0L10 0C10 0 10 5 7 8" fill="none" stroke={chatColor} strokeWidth="2" />
                                        </svg>
                                        {msg.type === 'audio' ? (
                                            <VoiceMessage msg={msg} chatColor={chatColor} hex2rgba={hex2rgba} />
                                        ) : msg.type === 'image' ? (
                                            <div className="flex flex-col gap-2 relative z-10 w-56 pb-1">
                                                <div className="rounded-xl overflow-hidden border border-white/20 shadow-[0_0_15px_rgba(0,0,0,0.5)] relative group cursor-pointer">
                                                    <div className="absolute inset-0 bg-current/10 pointer-events-none mix-blend-overlay" style={{ color: chatColor }} />
                                                    <img src={msg.image} alt="transferred visual data" className="w-full h-auto object-cover max-h-60" />
                                                    <div className="absolute top-0 left-0 w-full h-[2px] opacity-50 bg-current animate-scan pointer-events-none" style={{ color: chatColor, boxShadow: `0 0 10px ${chatColor}` }} />
                                                </div>
                                                {msg.text && <p className="text-[14px] font-sans text-white/95 leading-relaxed wrap-break-word">{msg.text}</p>}
                                            </div>
                                        ) : (
                                            <p className="text-[14px] font-sans text-white/95 leading-relaxed wrap-break-word relative z-10">{msg.text}</p>
                                        )}
                                        <div className="flex justify-end gap-1 mt-1 -mb-1 items-center relative z-10" style={{ color: chatColor }}>
                                            <span className="text-[9px] font-mono tracking-widest opacity-70">{msg.time || "10:45 SEC_TRK"}</span>
                                            <CheckCheck size={14} className="opacity-90 shadow-[0_0_5px_currentColor]" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* 3. MASTER INPUT BAR & KEYBOARD */}
            {!showGroupSettings && (
                <div className={`absolute left-0 right-0 bottom-0 flex flex-col transition-all duration-300 ${activeKeyboard !== 'none' ? 'h-[320px]' : 'h-auto'} bg-[#0A0A0C]/95 backdrop-blur-3xl border-t border-white/10 z-40 shadow-[0_-10px_30px_rgba(0,0,0,0.8)]`}>
                    <div className="p-2 px-3 shrink-0 flex flex-col gap-2">
                        <AnimatePresence>
                            {pendingImage && (
                                <motion.div initial={{ opacity: 0, scale: 0.5, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.8, filter: 'blur(10px)' }} className="self-start relative group mt-1 ml-1 origin-bottom-left">
                                    <div className="w-16 h-16 rounded-xl overflow-hidden border border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.3)] pointer-events-none">
                                        <img src={pendingImage} alt="Draft" className="w-full h-full object-cover" />
                                        <div className="absolute inset-0 bg-cyan-500/10 mix-blend-overlay pointer-events-none" />
                                    </div>
                                    <button onClick={() => setPendingImage(null)} className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white shadow-lg shadow-red-500/50 scale-0 group-hover:scale-100 transition-transform cursor-pointer z-10">
                                        <X size={14} strokeWidth={3} />
                                    </button>
                                </motion.div>
                            )}
                            {pendingAudio && (
                                <motion.div initial={{ opacity: 0, scale: 0.5, y: 10 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.8, filter: 'blur(10px)' }} className="self-start relative group mt-1 ml-1 origin-bottom-left flex items-center gap-2 bg-[#080808] border border-cyan-500/50 rounded-xl px-3 py-2 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                                    <div className="w-8 h-8 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400"><Mic size={14} /></div>
                                    <div className="flex flex-col">
                                        <span className="text-[10px] text-cyan-400 font-bold tracking-widest uppercase">Sec_Audio</span>
                                        <span className="text-xs text-white/70 font-mono">{pendingAudio.duration}</span>
                                    </div>
                                    <div className="w-16 h-4 flex items-center justify-between ml-2 opacity-50">
                                        {[1, 2, 3, 4, 5, 6].map(i => (
                                            <div key={i} className="w-1 bg-cyan-400 rounded-full" style={{ height: `${Math.random() * 100}%` }} />
                                        ))}
                                    </div>
                                    <button onClick={() => setPendingAudio(null)} className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white shadow-lg shadow-red-500/50 scale-0 group-hover:scale-100 transition-transform cursor-pointer z-10">
                                        <X size={14} strokeWidth={3} />
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Main Input Row */}
                        <div className="flex items-end gap-2 bg-black/40 rounded-3xl p-1.5 transition-colors focus-within:bg-black/60 focus-within:border-white/10 border border-transparent">
                            <div className="flex items-center self-end mb-1">
                                <button onClick={() => toggleKeyboard('emoji')} className={`p-1.5 transition-colors cursor-pointer rounded-full ${activeKeyboard === 'emoji' ? 'text-white bg-white/10' : 'text-white/40 hover:text-white/80'}`}>
                                    <Smile size={24} strokeWidth={1.5} />
                                </button>
                                <button onClick={() => toggleKeyboard('gallery')} className={`p-1.5 transition-colors cursor-pointer rounded-full ${activeKeyboard === 'gallery' ? 'text-white bg-white/10' : 'text-white/40 hover:text-white/80'}`}>
                                    <Paperclip size={24} strokeWidth={1.5} />
                                </button>
                            </div>
                            <div className="flex-1 relative h-10 flex items-center overflow-hidden">
                                <AnimatePresence mode="popLayout">
                                    {isRecording ? (
                                        <motion.div key="recording" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, y: -20, filter: 'blur(5px)' }} className="absolute inset-0 flex items-center justify-between px-2 w-full">
                                            <div className="flex items-center gap-2 text-red-500 animate-pulse">
                                                <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]" />
                                                <span className="text-xs font-mono font-bold">{recordingStartTimeRef.current ? `0:0${Math.floor((Date.now() - recordingStartTimeRef.current) / 1000)}` : '0:00'}</span>
                                            </div>
                                            <span className="text-[10px] text-white/30 uppercase tracking-widest font-bold flex items-center gap-1">
                                                <ChevronLeft size={12} /> Slide to shred
                                            </span>
                                        </motion.div>
                                    ) : (
                                        <motion.input key="text-input" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, y: isTransmitting ? -20 : 0 }} ref={inputRef} type="text" placeholder="WRITE NEURAL MESSAGE..." className="w-full h-full bg-transparent px-1 text-[15px] outline-none text-white placeholder:text-white/30 font-sans" style={{ caretColor: chatColor }} value={message || ""} onFocus={() => setActiveKeyboard('none')} onChange={(e) => setMessage(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && (message.trim() || pendingImage || pendingAudio) && handleSendMessage()} />
                                    )}
                                </AnimatePresence>
                            </div>
                            <div className="self-end mb-1 mr-1 relative w-10 h-10 flex items-center justify-center">
                                <AnimatePresence mode="popLayout">
                                    {(message.trim() || pendingImage || pendingAudio) ? (
                                        <motion.button key="send" initial={{ scale: 0, rotate: -45, opacity: 0 }} animate={isTransmitting ? { x: 50, y: -50, scale: 0.5, opacity: 0 } : { scale: 1, rotate: 0, opacity: 1 }} exit={{ scale: 0, opacity: 0 }} transition={{ type: "spring", stiffness: 400, damping: 25 }} onClick={handleSendMessage} className="absolute inset-0 m-auto w-9 h-9 rounded-full text-black flex items-center justify-center cursor-pointer shadow-[0_0_20px_rgba(0,240,255,0.8)] border border-cyan-400/50" style={{ backgroundColor: chatColor }}>
                                            <Send size={18} strokeWidth={2.5} className="ml-0.5 text-black filter drop-shadow-[0_0_5px_rgba(0,0,0,0.5)]" />
                                        </motion.button>
                                    ) : (
                                        <motion.button key="mic" initial={{ scale: 0 }} animate={{ scale: 1, x: audioSwipeOffset, opacity: isBinningAudio ? 0 : 1 }} exit={{ scale: 0, opacity: 0 }} onPointerDown={handleStartRecording} onPointerUp={handleStopRecording} onPointerLeave={handleStopRecording} onPointerMove={handleMicPointerMove} className="absolute inset-0 m-auto w-10 h-10 hover:text-white text-cyan-400 transition-colors cursor-pointer rounded-full flex items-center justify-center select-none touch-none">
                                            {isBinningAudio ? (
                                                <Trash2 size={24} className="text-red-500 animate-bounce" />
                                            ) : isRecording ? (
                                                <div className="w-full h-full rounded-full bg-red-500/20 flex items-center justify-center shadow-[0_0_15px_rgba(239,68,68,0.5)]">
                                                    <Mic size={24} className="text-red-500 animate-pulse" />
                                                </div>
                                            ) : (
                                                <Mic size={24} strokeWidth={1.5} />
                                            )}
                                            {isRecording && !isBinningAudio && (
                                                <div className="absolute -left-20 w-8 h-8 rounded-full bg-red-500/10 flex items-center justify-center pointer-events-none opacity-50">
                                                    <Trash2 size={14} className="text-red-500" />
                                                </div>
                                            )}
                                        </motion.button>
                                    )}
                                </AnimatePresence>
                            </div>
                        </div>
                    </div>

                    {/* CUSTOM KEYBOARD REPLACEMENT PANELS */}
                    <motion.div initial={false} animate={{ height: activeKeyboard !== 'none' ? 320 : 0 }} transition={{ type: "spring", stiffness: 300, damping: 30 }} className="flex-1 overflow-visible relative bg-black/60 rounded-t-xl mx-2 shadow-[inset_0_5px_15px_rgba(0,0,0,0.5)]">
                        <AnimatePresence>
                            {activeKeyboard === 'emoji' && (
                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 p-4">
                                    <div className="grid grid-cols-8 gap-3 content-start">
                                        {['🔥', '⚡', '💀', '👽', '🧠', '👁️', '🧬', '🔬', '🚀', '⭐', '⚠️', '☢️', '✅', '❌', '❤️', '💎', '🎯', '💯', '✨', '🌊', '💥', '💉', '💊', '🩸'].map((emoji, i) => (
                                            <button key={i} onClick={() => addEmoji(emoji)} className="w-10 h-10 flex items-center justify-center text-2xl hover:bg-white/10 rounded-xl transition-colors cursor-pointer active:scale-90">
                                                {emoji}
                                            </button>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                            {activeKeyboard === 'gallery' && (
                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 p-4 flex flex-col gap-4">
                                    <div className="flex items-center justify-between px-2">
                                        <span className="text-xs font-bold text-white/50 tracking-widest uppercase">Select Tactical Image</span>
                                        <button onClick={triggerImagePicker} className="text-[10px] bg-cyan-600/20 text-cyan-400 px-3 py-1.5 rounded-full hover:bg-cyan-600/40 transition-colors uppercase font-bold tracking-wider cursor-pointer active:scale-95 shadow-[0_0_10px_rgba(6,182,212,0.2)]">
                                            Device Gallery ↗
                                        </button>
                                    </div>
                                    <div className="grid grid-cols-3 gap-2 overflow-y-auto pb-safe">
                                        {[1, 2, 3, 4, 5, 6].map(i => (
                                            <div key={i} onClick={() => { setPendingImage(`https://picsum.photos/seed/${i * 10}/300/300`); setActiveKeyboard('none'); }} className="aspect-square bg-white/5 rounded-xl border border-white/10 flex items-center justify-center hover:border-cyan-500 cursor-pointer overflow-hidden group relative">
                                                <div className="absolute inset-0 bg-cyan-500/20 mix-blend-overlay z-10 opacity-0 group-hover:opacity-100 transition-opacity" />
                                                <img src={`https://picsum.photos/seed/${i * 10}/300/300`} alt="gallery mock" className="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-110 transition-all duration-500" />
                                            </div>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                </div>
            )}

            {/* 4. Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-red-950/40 backdrop-blur-xl transition-all animate-in fade-in duration-300">
                    <div className="bg-[#0B0F19] border-2 border-red-500/50 rounded-3xl p-8 w-full max-w-xs flex flex-col items-center gap-6 shadow-[0_0_50px_rgba(239,68,68,0.3)] relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-1 bg-linear-to-r from-transparent via-red-500 to-transparent animate-pulse" />
                        <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/40 flex items-center justify-center text-red-500 shadow-[0_0_20px_rgba(239,68,68,0.2)]">
                            <AlertTriangle size={32} className="animate-pulse" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-black tracking-tighter text-xl mb-2 italic uppercase">Critical Alert</h3>
                            <p className="text-white/60 text-xs leading-relaxed">
                                You are about to <span className="text-red-500 font-bold">PERMANENTLY DISBAND</span> this faction. All records and neural data will be purged. Proceed?
                            </p>
                        </div>
                        <div className="flex flex-col w-full gap-3 mt-2">
                            <button onClick={() => { setGroups(prev => prev.filter(g => g.id !== activeChat.id)); onClose(); setShowDeleteConfirm(false); setShowGroupSettings(false); }} className="w-full py-3 bg-red-600 hover:bg-red-500 text-white rounded-xl font-black text-xs uppercase tracking-widest shadow-[0_0_15px_rgba(239,68,68,0.4)] transition-all active:scale-95 cursor-pointer">
                                Confirm Purge
                            </button>
                            <button onClick={() => setShowDeleteConfirm(false)} className="w-full py-3 bg-white/5 hover:bg-white/10 text-white/70 rounded-xl font-bold text-xs uppercase transition-all cursor-pointer">
                                Abort Protocol
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
