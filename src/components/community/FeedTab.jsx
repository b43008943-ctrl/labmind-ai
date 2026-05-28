/* FeedTab — Study groups grid with create/join forms */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Atom, Sparkles, X, Camera, Copy } from 'lucide-react';
import { getGroupColor, getGroupImage } from './communityData';
import GroupIcon from './GroupIcon';

export default function FeedTab({
    groups,
    setGroups,
    setActiveChat,
}) {
    const [showCreate, setShowCreate] = useState(false);
    const [showJoin, setShowJoin] = useState(false);
    const [newGroupName, setNewGroupName] = useState('');
    const [inviteCode, setInviteCode] = useState('');
    const [createFeedback, setCreateFeedback] = useState('');
    const [isPrivate, setIsPrivate] = useState(true);
    const [randomCode, setRandomCode] = useState(() => Math.random().toString(36).substring(2, 8).toUpperCase());
    const [showIconPicker, setShowIconPicker] = useState(false);
    const [selectedIcon, setSelectedIcon] = useState(null);

    const handleCreateGroup = () => {
        if (!newGroupName.trim() || !selectedIcon) return;
        const finalCode = isPrivate ? randomCode : "PUB-000";
        const newGroup = {
            id: 'g' + Date.now(),
            name: newGroupName,
            icon: selectedIcon,
            iconName: selectedIcon.toLowerCase(),
            members: 1,
            online: 1,
            subject: 'general',
            description: '',
            private: isPrivate,
            joined: true,
            code: finalCode
        };
        setGroups([...groups, newGroup]);
        setNewGroupName('');
        setSelectedIcon(null);
        setShowCreate(false);
        setRandomCode(Math.random().toString(36).substring(2, 8).toUpperCase());
    };

    const handleJoinGroup = () => {
        if (!inviteCode.trim()) return;
        const groupIndex = groups.findIndex(g => g.code === inviteCode);
        if (groupIndex !== -1) {
            const newGroups = [...groups];
            newGroups[groupIndex].joined = true;
            setGroups(newGroups);
            setInviteCode('');
            setShowJoin(false);
            alert("Joined group successfully!");
        } else {
            alert("Invalid invite code");
        }
    };

    return (
        <motion.div key="tab-feed" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="flex flex-col gap-4 pt-2">
            {/* ═══ STUDY GROUPS LIST ═══ */}
            <div>
                <div className="flex flex-row items-center justify-between w-full mb-6">
                    <div className="flex items-center gap-2">
                        <div className="w-5 h-5 rounded flex items-center justify-center bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.3)]">
                            <Atom size={12} className="animate-[spin_6s_linear_infinite]" />
                        </div>
                        <h3 className="text-cyan-50 text-xs font-bold tracking-widest uppercase drop-shadow-[0_0_5px_rgba(255,255,255,0.3)]">
                            Study Groups
                        </h3>
                    </div>
                    <div className="flex gap-2">
                        <button onClick={() => { setShowCreate(true); setShowJoin(false); }} className="px-5 py-2 bg-black/40 backdrop-blur-md text-cyan-400 text-[10px] font-black tracking-[0.2em] uppercase rounded-lg border border-cyan-400 hover:bg-cyan-900/30 hover:shadow-[0_0_20px_rgba(34,211,238,0.6),inset_0_0_10px_rgba(34,211,238,0.2)] transition-all flex items-center gap-2 cursor-pointer relative overflow-hidden group">
                            <div className="absolute inset-x-0 top-0 h-px bg-linear-to-r from-transparent via-cyan-300 to-transparent opacity-50" />
                            <Sparkles size={12} className="drop-shadow-[0_0_5px_currentColor]" /> INITIALIZE
                        </button>
                    </div>
                </div>

                <AnimatePresence>
                    {showCreate && (
                        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mb-4 overflow-hidden">
                            <div className="flex flex-col gap-4 p-5 bg-white/5 border border-white/10 rounded-2xl w-full mt-4">
                                <div className="flex justify-between items-center w-full mb-2">
                                    <span className="text-white/50 text-xs font-bold tracking-widest uppercase">Create Faction</span>
                                    <button onClick={() => setShowCreate(false)} className="text-white/40 hover:text-red-400 transition-colors"><X size={18} /></button>
                                </div>
                                <div className="flex flex-row items-center gap-4">
                                    <button onClick={() => setShowIconPicker(!showIconPicker)} className="w-16 h-16 shrink-0 rounded-full bg-[#0B0F19] border border-dashed border-white/30 flex items-center justify-center hover:border-cyan-500 transition-colors relative group outline-none">
                                        {selectedIcon ? <GroupIcon type={selectedIcon} /> : <Camera className="text-white/50 group-hover:text-cyan-400" size={24} />}
                                    </button>
                                    <input type="text" placeholder="Group Name..." value={newGroupName} onChange={e => setNewGroupName(e.target.value)} className="flex-1 bg-transparent border-b border-white/20 text-white p-2 outline-none focus:border-cyan-500 text-lg transition-colors" />
                                </div>
                                {showIconPicker && (
                                    <div className="flex flex-row gap-4 overflow-x-auto py-4 bg-black/40 p-4 rounded-lg border border-white/10 hide-scrollbar mt-2 items-center">
                                        {["epic neon fire dragon", "giant glowing frost wolf", "dark shadow knight", "mythical deep sea siren", "celestial angelic valkyrie"].map(icon => (
                                            <div key={icon} onClick={() => { setSelectedIcon(icon); setShowIconPicker(false); }} className="cursor-pointer p-2 rounded-full hover:bg-white/10 shrink-0 transition-all flex items-center justify-center relative w-16 h-16 hover:scale-110">
                                                <GroupIcon type={icon} />
                                            </div>
                                        ))}
                                    </div>
                                )}
                                <div className="flex flex-col gap-3 mt-2 border-t border-white/10 pt-4">
                                    <div className="flex gap-6">
                                        <label className="flex items-center gap-2 text-white/80 text-sm cursor-pointer hover:text-white transition-colors">
                                            <input type="radio" checked={isPrivate} onChange={() => setIsPrivate(true)} className="accent-cyan-500 w-4 h-4 cursor-pointer" /> 🔒 Private Group
                                        </label>
                                        <label className="flex items-center gap-2 text-white/80 text-sm cursor-pointer hover:text-white transition-colors">
                                            <input type="radio" checked={!isPrivate} onChange={() => setIsPrivate(false)} className="accent-cyan-500 w-4 h-4 cursor-pointer" /> 🌐 Public Group
                                        </label>
                                    </div>
                                    {isPrivate ? (
                                        <div className="flex items-center justify-between bg-black/40 p-3 rounded-lg border border-white/10">
                                            <div className="flex flex-col">
                                                <span className="text-[10px] text-white/50 uppercase font-bold tracking-wider mb-1">Auto-Generated Invite Code</span>
                                                <span className="text-cyan-400 font-mono tracking-wider font-bold">{randomCode}</span>
                                            </div>
                                            <button className="text-xs bg-cyan-600/20 text-cyan-400 px-3 py-1.5 rounded-md hover:bg-cyan-600/40 transition-colors flex items-center gap-1 font-bold outline-none cursor-pointer">
                                                <Copy size={14} /> Copy
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col gap-1">
                                            <span className="text-[10px] text-white/50 uppercase font-bold tracking-wider mb-1 mt-1">Create Searchable Link</span>
                                            <div className="flex items-center bg-black/40 rounded-lg border border-white/10 overflow-hidden focus-within:border-cyan-500 transition-colors">
                                                <span className="text-white/40 pl-3 text-sm">app.neural/</span>
                                                <input type="text" placeholder="my-group-name" className="bg-transparent p-3 text-white text-sm outline-none w-full" />
                                            </div>
                                        </div>
                                    )}
                                </div>
                                <button onClick={handleCreateGroup} className="mt-2 w-full py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl font-bold transition-all shadow-lg shadow-cyan-500/20 outline-none cursor-pointer">
                                    Create Group
                                </button>
                                {createFeedback && <p className="text-cyan-400 text-[10px] uppercase font-bold text-center mt-1">{createFeedback}</p>}
                            </div>
                        </motion.div>
                    )}

                    {showJoin && (
                        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mb-4 overflow-hidden">
                            <div className="p-3 bg-white/5 border border-white/10 rounded-xl flex flex-col gap-2">
                                <input type="text" placeholder="Enter Invite Code (e.g. A1B2C3)" value={inviteCode} onChange={(e) => setInviteCode(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-lg py-2 px-3 text-white text-xs outline-none focus:border-purple-500" />
                                <button onClick={handleJoinGroup} className="w-full bg-purple-600 text-white font-bold py-2 rounded-lg text-xs hover:bg-purple-500 transition-colors">
                                    Join Group
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Grid Groups Area */}
                <div className="relative grid grid-cols-2 gap-y-6 gap-x-4 p-2 justify-items-center mt-4">
                    <div className="absolute inset-y-0 w-px bg-white/10 animate-[scan-h_8s_linear_infinite] z-30 pointer-events-none" style={{ left: '50%' }} />
                    {groups.filter(group => !group.private || group.joined).map((group) => {
                        const groupColor = getGroupColor(group.icon || group.name);
                        const bgImage = getGroupImage(group.icon || group.name);
                        const membersCount = Math.floor(Math.random() * 200) + 50;

                        return (
                            <div
                                key={group.id}
                                onClick={() => setActiveChat(group)}
                                className="relative w-full aspect-square md:aspect-3/4 rounded-2xl overflow-hidden group hover:scale-[1.05] transition-all duration-500 bg-black border border-white/10 cursor-pointer"
                                style={{ boxShadow: groupColor ? `0 0 25px -5px ${groupColor}` : '0 0 25px -5px rgba(6, 182, 212, 0.4)', borderColor: groupColor || 'rgba(255, 255, 255, 0.1)' }}
                            >
                                <img src={bgImage} className="absolute inset-0 w-full h-full object-cover scale-[1.5] group-hover:scale-[1.65] transition-all duration-700 opacity-70 group-hover:opacity-100 z-0" alt={group.name} />
                                <div className="absolute inset-0 bg-linear-to-t from-black/95 via-black/40 to-transparent z-10 pointer-events-none"></div>
                                <div className="relative z-20 p-4 font-sans sm:p-5 h-full flex flex-col justify-between pointer-events-none">
                                    <div className="self-start px-3 py-1 rounded-full bg-black/60 backdrop-blur-md border text-white text-xs font-bold shadow-lg" style={{ borderColor: group.color || 'rgba(255,255,255,0.2)' }}>
                                        RANK : {group.rank < 10 ? `0${group.rank || 0}` : (group.rank || '01')}
                                    </div>
                                    <div className="mt-auto">
                                        <h3 className="font-black uppercase tracking-tighter text-2xl text-white mb-2 leading-none drop-shadow-md">{group.name}</h3>
                                        <div className="flex items-center gap-2 font-mono text-[9px] uppercase tracking-[0.3em] text-white/90 drop-shadow-md">
                                            <span className="w-2.5 h-2.5 rounded-full animate-pulse" style={{ backgroundColor: groupColor || '#22c55e', boxShadow: `0 0 10px ${groupColor || '#22c55e'}` }}></span>
                                            {membersCount} OPERATIVES ONLINE
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </motion.div>
    );
}
