import { useState, useEffect } from 'react';
import { Activity, Target, Star, Award, Edit3, X, Loader2, Save, Camera, FileText, ShoppingBag, FolderOpen, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useProfile } from '../context/ProfileContext';
import { useNavigation } from '../context/NavigationContext';
import { useAppState } from '../context/AppStateContext';

const ITEMS_MAP = {
    // Avatars
    'a1': { name: 'Lab Scientist', icon: '🥼', rarity: 'Common' },
    'a2': { name: 'Microscope Master', icon: '🔬', rarity: 'Rare' },
    'a3': { name: 'Cell Hunter', icon: '🧬', rarity: 'Epic' },
    'a4': { name: 'DNA Decoder', icon: '🧪', rarity: 'Legendary' },
    // Titles
    't1': { name: 'Junior Analyst', icon: '📋', rarity: 'Common' },
    't2': { name: 'Senior Technician', icon: '🏷️', rarity: 'Rare' },
    't3': { name: 'Chief Pathologist', icon: '🎖️', rarity: 'Epic' },
    't4': { name: 'Laboratory Director', icon: '👑', rarity: 'Legendary' },
    // Frames
    'f1': { name: 'Bronze Frame', icon: '🟤', rarity: 'Common' },
    'f2': { name: 'Silver Frame', icon: '⚪', rarity: 'Rare' },
    'f3': { name: 'Gold Frame', icon: '🟡', rarity: 'Epic' },
    'f4': { name: 'Diamond Frame', icon: '💎', rarity: 'Legendary' },
    // Badges
    'b1': { name: 'First Analysis', icon: '🏅', rarity: 'Common' },
    'b2': { name: '100 Scans Club', icon: '💯', rarity: 'Rare' },
    'b3': { name: 'Perfect Score', icon: '⭐', rarity: 'Epic' },
    'b4': { name: 'AI Master', icon: '🤖', rarity: 'Legendary' },
    // Lab Coats
    'l1': { name: 'Standard White', icon: '🧥', rarity: 'Common' },
    'l2': { name: 'Blue Scrubs', icon: '👔', rarity: 'Rare' },
    'l3': { name: 'Neon Lab Coat', icon: '✨', rarity: 'Epic' },
    'l4': { name: 'Holographic Coat', icon: '🌈', rarity: 'Legendary' },
};

export default function UserProfile() {
    const { currentUser, logout, setCurrentUser } = useAuth();
    const { saveProfile, isSaving, saveError, saveSuccess, clearSaveStatus } = useProfile();
    const { navigate } = useNavigation();
    const { xp, level, equipped, ownedItems } = useAppState();

    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({
        userName: '',
        rank: '',
        avatarUrl: ''
    });

    // Initialize form when editing starts or when currentUser loads
    useEffect(() => {
        if (currentUser) {
            setFormData({
                userName: currentUser.full_name || '',
                rank: currentUser.rank_title || '',
                avatarUrl: currentUser.avatar_url || ''
            });
        }
    }, [currentUser, isEditing]);

    const handleSave = async () => {
        const result = await saveProfile(formData, setCurrentUser);
        if (result.success) {
            setIsEditing(false);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('login');
    };

    // Safe fallbacks for display
    const displayName = currentUser?.full_name || 'Dr. Commander';
    const displayRank = currentUser?.rank_title || 'Chief Pathologist';
    const displayEmail = currentUser?.email || 'user@labmind.ai';
    const displayRole = currentUser?.role || 'user';
    const displayAvatar = currentUser?.avatar_url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${displayName}`;

    // Mock stats
    const stats = [
        { label: 'Analyses', value: '142', icon: Activity, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
        { label: 'Accuracy', value: '94%', icon: Target, color: 'text-green-400', bg: 'bg-green-500/10' },
        { label: 'XP Points', value: xp.toLocaleString(), icon: Star, color: 'text-amber-400', bg: 'bg-amber-500/10' },
        { label: 'Level', value: String(level), icon: Award, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    ];

    const frameColors = {
        'f1': '#CD7F32', // Bronze Frame
        'f2': '#C0C0C0', // Silver Frame
        'f3': '#FFD700', // Gold Frame
        'f4': '#00D4FF', // Diamond Frame
    };
    const frameColor = frameColors[equipped?.frame] || null;

    return (
        <div style={{
            minHeight:'100vh',
            background:'radial-gradient(ellipse at 50% 10%, rgba(16,185,129,0.07), transparent 50%), linear-gradient(180deg,#070C1A,#050810)',
            fontFamily:"'Plus Jakarta Sans',sans-serif",
            color:'#E8F4FF',
            overflowY:'auto',
            WebkitOverflowScrolling:'touch',
        }}>


            {/* ══════════ HEADER ══════════ */}
            <div style={{
                position:'sticky',top:0,zIndex:20,
                padding:'14px 20px',
                background:'rgba(5,8,16,0.9)',
                backdropFilter:'blur(24px)',
                WebkitBackdropFilter:'blur(24px)',
                borderBottom:'1px solid rgba(255,255,255,0.05)',
                display:'flex',alignItems:'center',gap:12,
            }}>
                <button
                    onClick={() => navigate('dashboard')}
                    style={{
                        width:36,height:36,borderRadius:10,
                        background:'rgba(255,255,255,0.04)',
                        border:'1px solid rgba(255,255,255,0.08)',
                        display:'flex',alignItems:'center',justifyContent:'center',
                        cursor:'pointer',color:'rgba(255,255,255,0.6)',fontSize:16,
                    }}
                >←</button>
                <h1 style={{
                    margin:0,fontSize:17,fontWeight:800,
                    color:'#F0F9FF',letterSpacing:-0.3,flex:1,
                }}>👤 Profile</h1>

                {!isEditing ? (
                    <button
                        onClick={() => { clearSaveStatus(); setIsEditing(true); }}
                        style={{
                            padding:'6px 14px',borderRadius:8,
                            background:'rgba(16,185,129,0.1)',
                            border:'1px solid rgba(16,185,129,0.25)',
                            color:'#10B981',
                            fontSize:11,fontWeight:700,cursor:'pointer',
                            fontFamily:"'Plus Jakarta Sans',sans-serif",
                            display:'flex',alignItems:'center',gap:6,
                        }}
                    >✏️ Edit</button>
                ) : (
                    <div style={{display:'flex',gap:8}}>
                        <button
                            onClick={() => { clearSaveStatus(); setIsEditing(false); }}
                            disabled={isSaving}
                            style={{
                                width:36,height:36,borderRadius:8,
                                background:'rgba(255,255,255,0.05)',
                                border:'1px solid rgba(255,255,255,0.1)',
                                display:'flex',alignItems:'center',justifyContent:'center',
                                cursor: isSaving ? 'not-allowed' : 'pointer',
                                color:'rgba(255,255,255,0.5)',fontSize:14,
                                opacity: isSaving ? 0.5 : 1,
                            }}
                        >✕</button>
                        <button
                            onClick={handleSave}
                            disabled={isSaving}
                            style={{
                                padding:'6px 14px',borderRadius:8,
                                background: isSaving ? 'rgba(16,185,129,0.2)' : 'linear-gradient(135deg,#059669,#10B981)',
                                border:'none',
                                color:'#fff',
                                fontSize:11,fontWeight:700,cursor: isSaving ? 'not-allowed' : 'pointer',
                                fontFamily:"'Plus Jakarta Sans',sans-serif",
                                display:'flex',alignItems:'center',gap:6,
                                opacity: isSaving ? 0.7 : 1,
                            }}
                        >{isSaving ? '⏳ Saving...' : '✓ Save'}</button>
                    </div>
                )}
            </div>

            <div style={{padding:'20px 16px 100px',maxWidth:600,margin:'0 auto'}}>

                {/* ══════════ STATUS MESSAGES ══════════ */}
                {saveError && (
                    <div style={{
                        marginBottom:16,padding:'10px 14px',borderRadius:10,
                        background:'rgba(239,68,68,0.08)',
                        border:'1px solid rgba(239,68,68,0.2)',
                        fontSize:12,color:'#EF4444',fontWeight:500,
                    }}>{saveError}</div>
                )}
                {saveSuccess && (
                    <div style={{
                        marginBottom:16,padding:'10px 14px',borderRadius:10,
                        background:'rgba(16,185,129,0.08)',
                        border:'1px solid rgba(16,185,129,0.2)',
                        fontSize:12,color:'#10B981',fontWeight:500,
                    }}>Profile updated successfully!</div>
                )}

                {/* ══════════ AVATAR SECTION ══════════ */}
                <div style={{textAlign:'center',marginBottom:28}}>
                    <div style={{position:'relative',display:'inline-block',marginBottom:12}}>
                        <div style={{
                            width:90,height:90,borderRadius:'50%',
                            background:'radial-gradient(circle at 35% 35%, rgba(16,185,129,0.9), rgba(0,80,50,0.9))',
                            margin:'0 auto',
                            display:'flex',alignItems:'center',justifyContent:'center',
                            fontSize:32,color:'#fff',
                            boxShadow: frameColor ? `0 0 0 3px ${frameColor}, 0 0 20px ${frameColor}60` : '0 0 30px rgba(16,185,129,0.3), 0 0 0 3px rgba(16,185,129,0.15)',
                            position:'relative',overflow:'hidden',
                        }}>
                            {(isEditing ? (formData.avatarUrl || displayAvatar) : displayAvatar) ? (
                                <img
                                    src={isEditing ? (formData.avatarUrl || displayAvatar) : displayAvatar}
                                    alt="Profile Avatar"
                                    style={{width:'100%',height:'100%',objectFit:'cover',borderRadius:'50%'}}
                                    onError={(e) => { e.target.style.display='none'; e.target.nextSibling && (e.target.nextSibling.style.display='flex'); }}
                                />
                            ) : null}
                            <span style={{
                                display: (isEditing ? (formData.avatarUrl || displayAvatar) : displayAvatar) ? 'none' : 'flex',
                                alignItems:'center',justifyContent:'center',
                                width:'100%',height:'100%',position:'absolute',
                                fontWeight:800,fontSize:32,
                            }}>{(displayName || 'U')[0].toUpperCase()}</span>
                        </div>

                        {isEditing && (
                            <div style={{
                                position:'absolute',bottom:0,right:0,
                                width:28,height:28,borderRadius:'50%',
                                background:'#10B981',border:'2px solid #070C1A',
                                display:'flex',alignItems:'center',justifyContent:'center',
                                cursor:'pointer',fontSize:12,
                            }}>📷</div>
                        )}
                    </div>

                    <h2 style={{margin:'0 0 4px',fontSize:18,fontWeight:800,color:'#F0F9FF'}}>
                        {displayName}
                    </h2>
                    <p style={{margin:'0 0 4px',fontSize:11,color:'rgba(0,212,255,0.6)',letterSpacing:1,fontFamily:"'JetBrains Mono',monospace",textTransform:'uppercase'}}>
                        {displayRank}
                    </p>
                    <p style={{margin:'0 0 12px',fontSize:10,color:'rgba(255,255,255,0.25)'}}>
                        {displayEmail}
                    </p>

                    {/* Stats row */}
                    <div style={{
                        display:'inline-flex',gap:0,
                        background:'rgba(255,255,255,0.03)',
                        border:'1px solid rgba(255,255,255,0.06)',
                        borderRadius:12,overflow:'hidden',
                    }}>
                        {stats.map((stat, i) => (
                            <div key={i} style={{
                                padding:'10px 20px',textAlign:'center',
                                borderRight: i < stats.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                            }}>
                                <p style={{margin:0,fontSize:16,fontWeight:800,color: stat.color.includes('cyan') ? '#22D3EE' : stat.color.includes('green') ? '#10B981' : stat.color.includes('amber') ? '#F59E0B' : '#A78BFA'}}>{stat.value}</p>
                                <p style={{margin:0,fontSize:9,color:'rgba(255,255,255,0.3)',textTransform:'uppercase',letterSpacing:0.5}}>{stat.label}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* ══════════ PROFILE FIELDS ══════════ */}
                <div style={{marginBottom:24}}>
                    <p style={{
                        fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.25)',
                        textTransform:'uppercase',letterSpacing:2,margin:'0 0 10px 4px',
                    }}>◆ {isEditing ? 'Edit Information' : 'Personal Information'}</p>

                    <div style={{
                        background:'rgba(255,255,255,0.03)',
                        border:'1px solid rgba(255,255,255,0.07)',
                        borderRadius:14,overflow:'hidden',
                    }}>
                        {!isEditing ? (
                            /* View mode */
                            <>
                                {[
                                    {icon:'👤', label:'Full Name', value: displayName},
                                    {icon:'📧', label:'Email', value: displayEmail},
                                    {icon:'🎖️', label:'Title / Rank', value: displayRank},
                                    {icon:'🛡️', label:'Role', value: displayRole?.toUpperCase()},
                                ].map((item, i, arr) => (
                                    <div key={i} style={{
                                        display:'flex',alignItems:'center',gap:12,
                                        padding:'14px 16px',
                                        borderBottom: i < arr.length-1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                                    }}>
                                        <div style={{
                                            width:36,height:36,borderRadius:10,
                                            background:'rgba(16,185,129,0.08)',
                                            border:'1px solid rgba(16,185,129,0.15)',
                                            display:'flex',alignItems:'center',justifyContent:'center',
                                            fontSize:16,flexShrink:0,
                                        }}>{item.icon}</div>
                                        <div style={{flex:1,minWidth:0}}>
                                            <p style={{margin:'0 0 2px',fontSize:10,color:'rgba(255,255,255,0.3)',textTransform:'uppercase',letterSpacing:0.5}}>{item.label}</p>
                                            <p style={{margin:0,fontSize:13,fontWeight:600,color:'#F0F9FF',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{item.value || '—'}</p>
                                        </div>
                                    </div>
                                ))}
                            </>
                        ) : (
                            /* Edit mode */
                            <>
                                {[
                                    {icon:'👤', label:'Full Name', field:'userName', placeholder:'Enter your name'},
                                    {icon:'🎖️', label:'Title / Rank', field:'rank', placeholder:'e.g. Chief Pathologist'},
                                    {icon:'🖼️', label:'Avatar URL', field:'avatarUrl', placeholder:'https://...'},
                                ].map((item, i, arr) => (
                                    <div key={i} style={{
                                        padding:'14px 16px',
                                        borderBottom: i < arr.length-1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                                    }}>
                                        <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:8}}>
                                            <div style={{
                                                width:30,height:30,borderRadius:8,
                                                background:'rgba(16,185,129,0.08)',
                                                border:'1px solid rgba(16,185,129,0.15)',
                                                display:'flex',alignItems:'center',justifyContent:'center',
                                                fontSize:14,flexShrink:0,
                                            }}>{item.icon}</div>
                                            <span style={{fontSize:10,fontWeight:700,color:'#10B981',textTransform:'uppercase',letterSpacing:1}}>{item.label}</span>
                                        </div>
                                        <input
                                            type="text"
                                            value={formData[item.field]}
                                            onChange={e => setFormData(p => ({...p, [item.field]: e.target.value}))}
                                            placeholder={item.placeholder}
                                            style={{
                                                width:'100%',
                                                background:'rgba(0,0,0,0.3)',
                                                border:'1px solid rgba(255,255,255,0.1)',
                                                borderRadius:10,
                                                padding:'10px 14px',
                                                fontSize:13,fontWeight:500,color:'#F0F9FF',
                                                fontFamily:"'Plus Jakarta Sans',sans-serif",
                                                outline:'none',
                                                transition:'border-color 0.2s',
                                                boxSizing:'border-box',
                                            }}
                                            onFocus={e => e.target.style.borderColor='rgba(16,185,129,0.5)'}
                                            onBlur={e => e.target.style.borderColor='rgba(255,255,255,0.1)'}
                                        />
                                        {item.field === 'avatarUrl' && (
                                            <p style={{margin:'6px 0 0 2px',fontSize:10,color:'rgba(255,255,255,0.2)'}}>Provide a direct link to an image.</p>
                                        )}
                                    </div>
                                ))}
                            </>
                        )}
                    </div>
                </div>

                {/* ══════════ EQUIPPED ARMORY ITEMS ══════════ */}
                <div style={{marginBottom:24}}>
                    <p style={{
                        fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.25)',
                        textTransform:'uppercase',letterSpacing:2,margin:'0 0 10px 4px',
                    }}>◆ Equipped Armory Items</p>

                    <div style={{
                        background:'rgba(255,255,255,0.02)',
                        border:'1px solid rgba(255,255,255,0.05)',
                        borderRadius:14,overflow:'hidden',
                    }}>
                        {[
                            { label: 'Avatar', key: 'avatar', defaultIcon: '👤', defaultName: 'Default Avatar' },
                            { label: 'Title', key: 'title', defaultIcon: '🎖️', defaultName: 'Default Title' },
                            { label: 'Frame', key: 'frame', defaultIcon: '🖼️', defaultName: 'Default Frame' },
                            { label: 'Badge', key: 'badge', defaultIcon: '🏅', defaultName: 'Default Badge' },
                            { label: 'Lab Coat', key: 'coat', defaultIcon: '🧥', defaultName: 'Default Coat' },
                        ].map((category, i, arr) => {
                            const itemId = equipped?.[category.key];
                            const item = itemId ? ITEMS_MAP[itemId] : null;
                            const displayName = item?.name || category.defaultName;
                            const displayIcon = item?.icon || category.defaultIcon;
                            const displayRarity = item?.rarity || 'Common';
                            
                            const rarityColors = {
                                Common: '#94A3B8',
                                Rare: '#3B82F6',
                                Epic: '#A855F7',
                                Legendary: '#F59E0B'
                            };
                            const color = rarityColors[displayRarity] || '#94A3B8';

                            return (
                                <div key={category.key} style={{
                                    display:'flex',alignItems:'center',gap:12,
                                    padding:'12px 16px',
                                    borderBottom: i < arr.length-1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                                }}>
                                    <div style={{
                                        width:36,height:36,borderRadius:10,
                                        background:`${color}12`,
                                        border:`1px solid ${color}25`,
                                        display:'flex',alignItems:'center',justifyContent:'center',
                                        fontSize:18,flexShrink:0,
                                    }}>{displayIcon}</div>
                                    <div style={{flex:1,minWidth:0}}>
                                        <p style={{margin:0,fontSize:9,color:'rgba(255,255,255,0.3)',textTransform:'uppercase',letterSpacing:0.5}}>{category.label}</p>
                                        <p style={{margin:0,fontSize:13,fontWeight:600,color:'#F0F9FF',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{displayName}</p>
                                    </div>
                                    <span style={{
                                        fontSize:8,fontWeight:700,letterSpacing:0.8,
                                        padding:'2px 6px',borderRadius:4,
                                        background:`${color}18`,
                                        color:color,
                                        border:`1px solid ${color}30`,
                                        textTransform:'uppercase',
                                        fontFamily:"'JetBrains Mono',monospace",
                                    }}>{displayRarity}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* ══════════ QUICK ACTIONS ══════════ */}
                <div style={{marginBottom:24}}>
                    <p style={{
                        fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.25)',
                        textTransform:'uppercase',letterSpacing:2,margin:'0 0 10px 4px',
                    }}>◆ Quick Actions</p>

                    <div style={{
                        background:'rgba(255,255,255,0.03)',
                        border:'1px solid rgba(255,255,255,0.07)',
                        borderRadius:14,overflow:'hidden',
                    }}>
                        {[
                            {icon:'📋', label:'My Reports', sub:'View generated reports', action: () => navigate('my-reports'), color:'rgba(59,130,246,0.1)', borderColor:'rgba(59,130,246,0.2)'},
                            {icon:'🛒', label:'Store', sub:'Browse lab items & upgrades', action: () => navigate('store'), color:'rgba(245,158,11,0.1)', borderColor:'rgba(245,158,11,0.2)'},
                            {icon:'📁', label:'Patient Archive', sub:'Manage patient records', action: () => navigate('archive'), color:'rgba(139,92,246,0.1)', borderColor:'rgba(139,92,246,0.2)'},
                        ].map((item, i, arr) => (
                            <div
                                key={i}
                                onClick={item.action}
                                style={{
                                    display:'flex',alignItems:'center',gap:12,
                                    padding:'14px 16px',
                                    borderBottom: i < arr.length-1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                                    cursor:'pointer',transition:'background 0.15s',
                                }}
                                onMouseEnter={e => e.currentTarget.style.background='rgba(255,255,255,0.03)'}
                                onMouseLeave={e => e.currentTarget.style.background='transparent'}
                            >
                                <div style={{
                                    width:36,height:36,borderRadius:10,
                                    background:item.color,
                                    border:`1px solid ${item.borderColor}`,
                                    display:'flex',alignItems:'center',justifyContent:'center',
                                    fontSize:16,flexShrink:0,
                                }}>{item.icon}</div>
                                <div style={{flex:1}}>
                                    <p style={{margin:0,fontSize:13,fontWeight:600,color:'#F0F9FF'}}>{item.label}</p>
                                    <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)'}}>{item.sub}</p>
                                </div>
                                <span style={{color:'rgba(255,255,255,0.2)',fontSize:16}}>›</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* ══════════ LOGOUT ══════════ */}
                <div
                    onClick={handleLogout}
                    style={{
                        display:'flex',alignItems:'center',gap:12,
                        padding:'14px 16px',
                        background:'rgba(239,68,68,0.03)',
                        border:'1px solid rgba(239,68,68,0.1)',
                        borderRadius:14,cursor:'pointer',
                        transition:'background 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background='rgba(239,68,68,0.06)'}
                    onMouseLeave={e => e.currentTarget.style.background='rgba(239,68,68,0.03)'}
                >
                    <div style={{
                        width:36,height:36,borderRadius:10,
                        background:'rgba(239,68,68,0.1)',
                        border:'1px solid rgba(239,68,68,0.2)',
                        display:'flex',alignItems:'center',justifyContent:'center',
                        fontSize:16,flexShrink:0,
                    }}>🚪</div>
                    <div style={{flex:1}}>
                        <p style={{margin:0,fontSize:13,fontWeight:600,color:'#EF4444'}}>Log Out</p>
                        <p style={{margin:0,fontSize:10,color:'rgba(239,68,68,0.4)'}}>Sign out of your account</p>
                    </div>
                </div>

            </div>
        </div>
    );
}
