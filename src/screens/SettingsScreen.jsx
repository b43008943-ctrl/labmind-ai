import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { User, Lock, LogOut, Trash2, Globe, Moon, Bell, Cpu, Sparkles, Info, FileText, Shield, Key, Mail, ChevronLeft, ChevronRight, X, Check, AlertTriangle, SlidersHorizontal } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNavigation } from '../context/NavigationContext';
import { useAppSettings } from '../context/AppSettingsContext';
import { api } from '../services/apiClient';

// ─── REUSABLE UI COMPONENTS ───



const ModalOverlay = ({ isOpen, onClose, title, children }) => (
    <AnimatePresence>
        {isOpen && (
            <motion.div 
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
                onClick={onClose}
            >
                <motion.div 
                    initial={{ scale: 0.95, opacity: 0, y: 10 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0, y: 10 }}
                    onClick={e => e.stopPropagation()}
                    className="w-full max-w-sm bg-[#0A0E17] border border-white/10 rounded-2xl shadow-2xl overflow-hidden"
                >
                    <div className="flex items-center justify-between p-4 border-b border-white/10 bg-white/5">
                        <h3 className="text-base font-bold text-white tracking-wide">{title}</h3>
                        <button onClick={onClose} className="w-8 h-8 rounded-full flex items-center justify-center bg-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition-colors">
                            <X size={16} />
                        </button>
                    </div>
                    <div className="p-5">
                        {children}
                    </div>
                </motion.div>
            </motion.div>
        )}
    </AnimatePresence>
);

// ─── MAIN SCREEN ───

export default function SettingsScreen() {
    const { logout, currentUser } = useAuth();
    const { navigate, goBack } = useNavigation();
    const { language, setLanguage, theme, setTheme } = useAppSettings();

    // ── FIX 1: Dark Theme — derived from AppSettingsContext ──
    const themeEnabled = theme !== 'default';

    // ── FIX 2: Notifications — persisted to localStorage ──
    const [notificationsEnabled, setNotificationsEnabled] = useState(
        () => localStorage.getItem('labmind_notifications') !== 'false'
    );
    const handleNotificationsToggle = () => {
        const newVal = !notificationsEnabled;
        setNotificationsEnabled(newVal);
        localStorage.setItem('labmind_notifications', String(newVal));
    };

    // ── FIX 3: AI Enhancement — persisted to localStorage ──
    const [useAI, setUseAI] = useState(
        () => localStorage.getItem('labmind_ai_enhancement') !== 'false'
    );
    const handleAIToggle = () => {
        const newVal = !useAI;
        setUseAI(newVal);
        localStorage.setItem('labmind_ai_enhancement', String(newVal));
    };

    // ── FIX 4: Confidence Threshold — persisted to localStorage ──
    const [confidenceThreshold, setConfidenceThreshold] = useState(
        () => parseFloat(localStorage.getItem('labmind_confidence') || '0.3')
    );
    const handleThresholdChange = (e) => {
        const val = parseFloat(e.target.value);
        setConfidenceThreshold(val);
        localStorage.setItem('labmind_confidence', String(val));
    };

    // Modals state
    const [activeModal, setActiveModal] = useState(null); // 'password' | 'logout' | 'delete' | 'clear' | 'language' | 'tos' | 'privacy' | 'licenses'

    // ── FIX 5: Change Password — state + API handler ──
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [passwordError, setPasswordError] = useState('');
    const [passwordSuccess, setPasswordSuccess] = useState(false);
    const [passwordLoading, setPasswordLoading] = useState(false);

    const handleChangePassword = async () => {
        setPasswordError('');
        if (newPassword !== confirmPassword) {
            setPasswordError('Passwords do not match');
            return;
        }
        if (newPassword.length < 6) {
            setPasswordError('Password must be at least 6 characters');
            return;
        }
        setPasswordLoading(true);
        try {
            await api.auth.changePassword({
                current_password: currentPassword,
                new_password: newPassword,
                confirm_password: confirmPassword,
            });
            setPasswordSuccess(true);
            setPasswordError('');
            setTimeout(() => {
                setActiveModal(null);
                setPasswordSuccess(false);
                setCurrentPassword('');
                setNewPassword('');
                setConfirmPassword('');
            }, 1500);
        } catch (err) {
            setPasswordError(err?.payload?.detail || err?.message || 'Failed to change password');
        } finally {
            setPasswordLoading(false);
        }
    };

    // ── FIX 6: Delete Account — API handler ──
    const [deleteLoading, setDeleteLoading] = useState(false);

    const handleDeleteAccount = async () => {
        setDeleteLoading(true);
        try {
            await api.auth.deleteAccount();
            localStorage.clear();
            logout();
            navigate('login');
        } catch (err) {
            console.error('Delete account failed:', err);
            setDeleteLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('login');
    };

    return (
        <div style={{
            minHeight:'100vh',
            background:'radial-gradient(ellipse at 30% 10%, rgba(139,92,246,0.07), transparent 50%), linear-gradient(180deg,#070C1A,#050810)',
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
                    onClick={goBack}
                    style={{
                        width:36,height:36,borderRadius:10,
                        background:'rgba(255,255,255,0.05)',
                        border:'1px solid rgba(255,255,255,0.08)',
                        display:'flex',alignItems:'center',justifyContent:'center',
                        color:'rgba(255,255,255,0.5)',cursor:'pointer',
                        fontSize:18,lineHeight:1,
                    }}
                >‹</button>
                <h1 style={{
                    margin:0,fontSize:17,fontWeight:800,
                    color:'#F0F9FF',letterSpacing:-0.3,flex:1,
                }}>⚙️ Settings</h1>
                <span style={{
                    fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',
                    letterSpacing:2,fontFamily:"'JetBrains Mono',monospace",
                }}>CONFIGURATION</span>
            </div>

            <div style={{padding:'16px 16px 100px',maxWidth:600,margin:'0 auto'}}>

                {/* ══════════ ACCOUNT SECTION ══════════ */}
                <div style={{marginBottom:24}}>
                    <p style={{
                        fontSize:9,fontWeight:700,
                        color:'rgba(255,255,255,0.25)',
                        textTransform:'uppercase',letterSpacing:2,
                        margin:'0 0 10px 4px',
                    }}>◆ Account</p>

                    <div style={{
                        background:'rgba(255,255,255,0.03)',
                        border:'1px solid rgba(255,255,255,0.07)',
                        borderRadius:14,
                        overflow:'hidden',
                    }}>
                        {[
                            { icon:'👤', label:'Edit Profile', sub: currentUser?.full_name || 'Personalize your identity', action: () => navigate('profile'), arrow:true },
                            { icon:'🔒', label:'Change Password', sub:'Update your password', action: () => setActiveModal('password'), arrow:true },
                            { icon:'🚪', label:'Log Out', sub:'Sign out of your account', action: () => setActiveModal('logout'), arrow:false, danger:true },
                        ].map((item, i, arr) => (
                            <div
                                key={i}
                                onClick={item.action}
                                style={{
                                    display:'flex',alignItems:'center',gap:12,
                                    padding:'14px 16px',
                                    borderBottom: i < arr.length-1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                                    cursor:'pointer',
                                    transition:'background 0.15s',
                                }}
                                onMouseEnter={e => e.currentTarget.style.background='rgba(255,255,255,0.03)'}
                                onMouseLeave={e => e.currentTarget.style.background='transparent'}
                            >
                                <div style={{
                                    width:36,height:36,borderRadius:10,
                                    background: item.danger ? 'rgba(239,68,68,0.1)' : 'rgba(255,255,255,0.05)',
                                    border: item.danger ? '1px solid rgba(239,68,68,0.2)' : '1px solid rgba(255,255,255,0.08)',
                                    display:'flex',alignItems:'center',justifyContent:'center',
                                    fontSize:16,flexShrink:0,
                                }}>{item.icon}</div>
                                <div style={{flex:1}}>
                                    <p style={{
                                        margin:0,fontSize:13,fontWeight:600,
                                        color: item.danger ? '#EF4444' : '#F0F9FF',
                                    }}>{item.label}</p>
                                    <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)'}}>{item.sub}</p>
                                </div>
                                {item.arrow && <span style={{color:'rgba(255,255,255,0.2)',fontSize:16}}>›</span>}
                            </div>
                        ))}
                    </div>
                </div>

                {/* ══════════ PREFERENCES SECTION ══════════ */}
                <div style={{marginBottom:24}}>
                    <p style={{
                        fontSize:9,fontWeight:700,
                        color:'rgba(255,255,255,0.25)',
                        textTransform:'uppercase',letterSpacing:2,
                        margin:'0 0 10px 4px',
                    }}>◆ Preferences</p>

                    <div style={{
                        background:'rgba(255,255,255,0.03)',
                        border:'1px solid rgba(255,255,255,0.07)',
                        borderRadius:14,
                        overflow:'hidden',
                    }}>
                        {/* Language */}
                        <div
                            onClick={() => setActiveModal('language')}
                            style={{
                                display:'flex',alignItems:'center',gap:12,
                                padding:'14px 16px',
                                borderBottom:'1px solid rgba(255,255,255,0.05)',
                                cursor:'pointer',transition:'background 0.15s',
                            }}
                            onMouseEnter={e => e.currentTarget.style.background='rgba(255,255,255,0.03)'}
                            onMouseLeave={e => e.currentTarget.style.background='transparent'}
                        >
                            <div style={{
                                width:36,height:36,borderRadius:10,
                                background:'rgba(59,130,246,0.1)',
                                border:'1px solid rgba(59,130,246,0.2)',
                                display:'flex',alignItems:'center',justifyContent:'center',
                                fontSize:16,flexShrink:0,
                            }}>🌐</div>
                            <div style={{flex:1}}>
                                <p style={{margin:0,fontSize:13,fontWeight:600,color:'#F0F9FF'}}>Language</p>
                                <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)'}}>App display language</p>
                            </div>
                            <span style={{fontSize:12,color:'rgba(255,255,255,0.4)',fontWeight:500}}>{language === 'en' ? 'English' : 'العربية'}</span>
                            <span style={{color:'rgba(255,255,255,0.2)',fontSize:16}}>›</span>
                        </div>

                        {/* Dark Theme Toggle */}
                        <div style={{
                            display:'flex',alignItems:'center',gap:12,
                            padding:'14px 16px',
                            borderBottom:'1px solid rgba(255,255,255,0.05)',
                        }}>
                            <div style={{
                                width:36,height:36,borderRadius:10,
                                background:'rgba(139,92,246,0.1)',
                                border:'1px solid rgba(139,92,246,0.2)',
                                display:'flex',alignItems:'center',justifyContent:'center',
                                fontSize:16,flexShrink:0,
                            }}>🌙</div>
                            <div style={{flex:1}}>
                                <p style={{margin:0,fontSize:13,fontWeight:600,color:'#F0F9FF'}}>Dark Theme</p>
                                <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)'}}>{themeEnabled ? 'Aurora bio-theme active' : 'Default dark theme'}</p>
                            </div>
                            <div
                                onClick={() => setTheme(themeEnabled ? 'default' : 'aurora')}
                                style={{
                                    width:44,height:24,borderRadius:12,
                                    background: themeEnabled ? 'linear-gradient(135deg,#5B21B6,#8B5CF6)' : 'rgba(255,255,255,0.1)',
                                    position:'relative',cursor:'pointer',
                                    boxShadow: themeEnabled ? '0 0 10px rgba(139,92,246,0.4)' : 'none',
                                    transition:'all 0.2s',
                                }}>
                                <div style={{
                                    position:'absolute',top:2,
                                    left: themeEnabled ? 22 : 2,
                                    width:20,height:20,borderRadius:'50%',
                                    background:'#fff',
                                    transition:'left 0.2s',
                                }}/>
                            </div>
                        </div>

                        {/* Notifications Toggle */}
                        <div style={{
                            display:'flex',alignItems:'center',gap:12,
                            padding:'14px 16px',
                        }}>
                            <div style={{
                                width:36,height:36,borderRadius:10,
                                background:'rgba(16,185,129,0.1)',
                                border:'1px solid rgba(16,185,129,0.2)',
                                display:'flex',alignItems:'center',justifyContent:'center',
                                fontSize:16,flexShrink:0,
                            }}>🔔</div>
                            <div style={{flex:1}}>
                                <p style={{margin:0,fontSize:13,fontWeight:600,color:'#F0F9FF'}}>Notifications</p>
                                <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)'}}>Analysis results and alerts</p>
                            </div>
                            <div
                                onClick={handleNotificationsToggle}
                                style={{
                                    width:44,height:24,borderRadius:12,
                                    background: notificationsEnabled ? 'linear-gradient(135deg,#047857,#10B981)' : 'rgba(255,255,255,0.1)',
                                    position:'relative',cursor:'pointer',
                                    boxShadow: notificationsEnabled ? '0 0 10px rgba(16,185,129,0.4)' : 'none',
                                    transition:'all 0.2s',
                                }}>
                                <div style={{
                                    position:'absolute',top:2,
                                    left: notificationsEnabled ? 22 : 2,
                                    width:20,height:20,borderRadius:'50%',
                                    background:'#fff',
                                    transition:'left 0.2s',
                                }}/>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ══════════ AI DIAGNOSTICS SECTION ══════════ */}
                <div style={{marginBottom:24}}>
                    <p style={{
                        fontSize:9,fontWeight:700,
                        color:'rgba(255,255,255,0.25)',
                        textTransform:'uppercase',letterSpacing:2,
                        margin:'0 0 10px 4px',
                    }}>◆ AI Diagnostics</p>

                    <div style={{
                        background:'rgba(255,255,255,0.03)',
                        border:'1px solid rgba(255,255,255,0.07)',
                        borderRadius:14,
                        overflow:'hidden',
                    }}>
                        {/* Gemini API Status */}
                        <div style={{
                            display:'flex',alignItems:'center',gap:12,
                            padding:'14px 16px',
                            borderBottom:'1px solid rgba(255,255,255,0.05)',
                        }}>
                            <div style={{
                                width:36,height:36,borderRadius:10,
                                background:'rgba(245,158,11,0.1)',
                                border:'1px solid rgba(245,158,11,0.2)',
                                display:'flex',alignItems:'center',justifyContent:'center',
                                fontSize:16,flexShrink:0,
                            }}>🤖</div>
                            <div style={{flex:1}}>
                                <p style={{margin:0,fontSize:13,fontWeight:600,color:'#F0F9FF'}}>Gemini API Key</p>
                                <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)'}}>Configured securely on backend</p>
                            </div>
                            <span style={{
                                fontSize:9,fontWeight:700,
                                padding:'3px 8px',borderRadius:6,
                                background:'rgba(16,185,129,0.1)',
                                color:'#10B981',
                                border:'1px solid rgba(16,185,129,0.2)',
                                fontFamily:"'JetBrains Mono',monospace",
                            }}>ACTIVE</span>
                        </div>

                        {/* AI Enhancement Toggle */}
                        <div style={{
                            display:'flex',alignItems:'center',gap:12,
                            padding:'14px 16px',
                            borderBottom:'1px solid rgba(255,255,255,0.05)',
                        }}>
                            <div style={{
                                width:36,height:36,borderRadius:10,
                                background:'rgba(99,102,241,0.1)',
                                border:'1px solid rgba(99,102,241,0.2)',
                                display:'flex',alignItems:'center',justifyContent:'center',
                                fontSize:16,flexShrink:0,
                            }}>⚡</div>
                            <div style={{flex:1}}>
                                <p style={{margin:0,fontSize:13,fontWeight:600,color:'#F0F9FF'}}>AI Enhancement</p>
                                <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)'}}>Use Gemini for clinical reports</p>
                            </div>
                            <div
                                onClick={handleAIToggle}
                                style={{
                                    width:44,height:24,borderRadius:12,
                                    background: useAI ? 'linear-gradient(135deg,#4338CA,#6366F1)' : 'rgba(255,255,255,0.1)',
                                    position:'relative',cursor:'pointer',
                                    boxShadow: useAI ? '0 0 10px rgba(99,102,241,0.4)' : 'none',
                                    transition:'all 0.2s',
                                }}>
                                <div style={{
                                    position:'absolute',top:2,
                                    left: useAI ? 22 : 2,
                                    width:20,height:20,borderRadius:'50%',
                                    background:'#fff',
                                    transition:'left 0.2s',
                                }}/>
                            </div>
                        </div>

                        {/* Confidence Threshold Slider */}
                        <div style={{padding:'14px 16px'}}>
                            <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:12}}>
                                <div style={{
                                    width:36,height:36,borderRadius:10,
                                    background:'rgba(0,212,255,0.1)',
                                    border:'1px solid rgba(0,212,255,0.2)',
                                    display:'flex',alignItems:'center',justifyContent:'center',
                                    fontSize:16,flexShrink:0,
                                }}>🎯</div>
                                <div style={{flex:1}}>
                                    <p style={{margin:0,fontSize:13,fontWeight:600,color:'#F0F9FF'}}>Confidence Threshold</p>
                                    <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)'}}>Minimum detection confidence</p>
                                </div>
                                <span style={{
                                    fontSize:13,fontWeight:800,
                                    color:'#22D3EE',
                                    fontFamily:"'JetBrains Mono',monospace",
                                }}>{(confidenceThreshold * 100).toFixed(0)}%</span>
                            </div>
                            <input
                                type="range"
                                min="0.1" max="0.9" step="0.05"
                                value={confidenceThreshold}
                                onChange={handleThresholdChange}
                                style={{
                                    width:'100%',height:6,borderRadius:3,
                                    appearance:'none',WebkitAppearance:'none',
                                    background:`linear-gradient(to right, #22D3EE ${((confidenceThreshold - 0.1) / 0.8) * 100}%, rgba(255,255,255,0.08) ${((confidenceThreshold - 0.1) / 0.8) * 100}%)`,
                                    cursor:'pointer',outline:'none',
                                }}
                            />
                            <div style={{display:'flex',justifyContent:'space-between',marginTop:6}}>
                                <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',letterSpacing:1,fontFamily:"'JetBrains Mono',monospace"}}>HIGH SENSITIVITY</span>
                                <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',letterSpacing:1,fontFamily:"'JetBrains Mono',monospace"}}>HIGH SPECIFICITY</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ══════════ ABOUT SECTION ══════════ */}
                <div style={{marginBottom:24}}>
                    <p style={{
                        fontSize:9,fontWeight:700,
                        color:'rgba(255,255,255,0.25)',
                        textTransform:'uppercase',letterSpacing:2,
                        margin:'0 0 10px 4px',
                    }}>◆ About</p>

                    <div style={{
                        background:'rgba(255,255,255,0.03)',
                        border:'1px solid rgba(255,255,255,0.07)',
                        borderRadius:14,
                        overflow:'hidden',
                    }}>
                        {[
                            { icon:'ℹ️', label:'App Version', right: <span style={{fontSize:12,color:'rgba(255,255,255,0.4)',fontFamily:"'JetBrains Mono',monospace"}}>1.0.0 Beta</span> },
                            { icon:'📄', label:'Terms of Service', action: () => setActiveModal('tos'), arrow:true },
                            { icon:'🛡️', label:'Privacy Policy', action: () => setActiveModal('privacy'), arrow:true },
                            { icon:'💾', label:'Data & Licenses', action: () => setActiveModal('licenses'), arrow:true },
                            { icon:'✉️', label:'Contact Support', right: <span style={{fontSize:11,color:'#818CF8',fontWeight:600}}>support@labmind.ai</span>, action: () => window.location.href = 'mailto:support@labmind.ai' },
                        ].map((item, i, arr) => (
                            <div
                                key={i}
                                onClick={item.action}
                                style={{
                                    display:'flex',alignItems:'center',gap:12,
                                    padding:'14px 16px',
                                    borderBottom: i < arr.length-1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
                                    cursor: item.action ? 'pointer' : 'default',
                                    transition:'background 0.15s',
                                }}
                                onMouseEnter={e => { if(item.action) e.currentTarget.style.background='rgba(255,255,255,0.03)'; }}
                                onMouseLeave={e => e.currentTarget.style.background='transparent'}
                            >
                                <div style={{
                                    width:36,height:36,borderRadius:10,
                                    background:'rgba(255,255,255,0.05)',
                                    border:'1px solid rgba(255,255,255,0.08)',
                                    display:'flex',alignItems:'center',justifyContent:'center',
                                    fontSize:16,flexShrink:0,
                                }}>{item.icon}</div>
                                <div style={{flex:1}}>
                                    <p style={{margin:0,fontSize:13,fontWeight:600,color:'#F0F9FF'}}>{item.label}</p>
                                </div>
                                {item.right && item.right}
                                {item.arrow && <span style={{color:'rgba(255,255,255,0.2)',fontSize:16}}>›</span>}
                            </div>
                        ))}
                    </div>
                </div>

                {/* ══════════ DANGER ZONE ══════════ */}
                <div style={{marginBottom:24}}>
                    <p style={{
                        fontSize:9,fontWeight:700,
                        color:'rgba(239,68,68,0.5)',
                        textTransform:'uppercase',letterSpacing:2,
                        margin:'0 0 10px 4px',
                    }}>◆ Danger Zone</p>

                    <div style={{
                        background:'rgba(239,68,68,0.03)',
                        border:'1px solid rgba(239,68,68,0.1)',
                        borderRadius:14,
                        overflow:'hidden',
                    }}>
                        {[
                            { icon:'🗑️', label:'Clear Local Data', sub:'Reset cached data and settings', action: () => setActiveModal('clear') },
                            { icon:'⚠️', label:'Delete Account', sub:'Permanently remove your account', action: () => setActiveModal('delete') },
                        ].map((item, i, arr) => (
                            <div
                                key={i}
                                onClick={item.action}
                                style={{
                                    display:'flex',alignItems:'center',gap:12,
                                    padding:'14px 16px',
                                    borderBottom: i < arr.length-1 ? '1px solid rgba(239,68,68,0.08)' : 'none',
                                    cursor:'pointer',
                                    transition:'background 0.15s',
                                }}
                                onMouseEnter={e => e.currentTarget.style.background='rgba(239,68,68,0.05)'}
                                onMouseLeave={e => e.currentTarget.style.background='transparent'}
                            >
                                <div style={{
                                    width:36,height:36,borderRadius:10,
                                    background:'rgba(239,68,68,0.1)',
                                    border:'1px solid rgba(239,68,68,0.2)',
                                    display:'flex',alignItems:'center',justifyContent:'center',
                                    fontSize:16,flexShrink:0,
                                }}>{item.icon}</div>
                                <div style={{flex:1}}>
                                    <p style={{margin:0,fontSize:13,fontWeight:600,color:'#EF4444'}}>{item.label}</p>
                                    <p style={{margin:0,fontSize:10,color:'rgba(239,68,68,0.4)'}}>{item.sub}</p>
                                </div>
                                <span style={{color:'rgba(239,68,68,0.3)',fontSize:16}}>›</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* ══════════ APP INFO FOOTER ══════════ */}
                <div style={{
                    background:'rgba(255,255,255,0.02)',
                    border:'1px solid rgba(255,255,255,0.05)',
                    borderRadius:14,
                    padding:'20px 16px',
                    textAlign:'center',
                    marginBottom:24,
                }}>
                    <p style={{margin:'0 0 4px',fontSize:24}}>🔬</p>
                    <p style={{margin:'0 0 2px',fontSize:14,fontWeight:800,color:'#F0F9FF'}}>LabMind AI</p>
                    <p style={{margin:'0 0 8px',fontSize:10,color:'rgba(0,212,255,0.6)',letterSpacing:1,fontFamily:"'JetBrains Mono',monospace"}}>SMART ANALYST SYSTEM</p>
                    <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.2)'}}>Version 1.0.0 • Educational Use Only</p>
                </div>

            </div>

            {/* ══════════ MODALS (PRESERVED AS-IS) ══════════ */}

            {/* Password Modal */}
            <ModalOverlay isOpen={activeModal === 'password'} onClose={() => { setActiveModal(null); setPasswordError(''); setPasswordSuccess(false); setCurrentPassword(''); setNewPassword(''); setConfirmPassword(''); }} title="Change Password">
                <div className="flex flex-col gap-3">
                    <input type="password" placeholder="Current Password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:border-indigo-500 outline-none transition-colors" />
                    <input type="password" placeholder="New Password" value={newPassword} onChange={e => setNewPassword(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:border-indigo-500 outline-none transition-colors" />
                    <input type="password" placeholder="Confirm New Password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white focus:border-indigo-500 outline-none transition-colors" />
                    {passwordError && <p className="text-xs text-red-400 text-center mt-1">{passwordError}</p>}
                    {passwordSuccess && <p className="text-xs text-emerald-400 text-center mt-1">✓ Password changed successfully!</p>}
                    <button
                        onClick={handleChangePassword}
                        disabled={passwordLoading || passwordSuccess}
                        className="mt-2 w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold tracking-wider uppercase transition-colors"
                    >
                        {passwordLoading ? 'Saving...' : passwordSuccess ? 'Done ✓' : 'Save Password'}
                    </button>
                </div>
            </ModalOverlay>

            {/* Language Modal */}
            <ModalOverlay isOpen={activeModal === 'language'} onClose={() => setActiveModal(null)} title="App Language">
                <div className="flex flex-col gap-2">
                    <button onClick={() => { setLanguage('en'); setActiveModal(null); }} className={`flex items-center justify-between p-4 rounded-xl border ${language === 'en' ? 'bg-indigo-500/20 border-indigo-500/40' : 'bg-white/5 border-white/10'} hover:bg-white/10 transition-colors`}>
                        <span className="text-white font-medium">English</span>
                        {language === 'en' && <Check size={18} className="text-indigo-400" />}
                    </button>
                    <button onClick={() => { setLanguage('ar'); setActiveModal(null); }} className={`flex items-center justify-between p-4 rounded-xl border ${language === 'ar' ? 'bg-indigo-500/20 border-indigo-500/40' : 'bg-white/5 border-white/10'} hover:bg-white/10 transition-colors`}>
                        <span className="text-white font-medium" dir="rtl">العربية (Arabic)</span>
                        {language === 'ar' && <Check size={18} className="text-indigo-400" />}
                    </button>
                </div>
            </ModalOverlay>

            {/* Log Out Modal */}
            <ModalOverlay isOpen={activeModal === 'logout'} onClose={() => setActiveModal(null)} title="Log Out">
                <p className="text-slate-300 text-sm mb-6 text-center">Are you sure you want to log out of your session?</p>
                <div className="flex gap-3">
                    <button onClick={() => setActiveModal(null)} className="flex-1 py-3 rounded-xl bg-white/5 border border-white/10 text-white text-xs font-bold uppercase tracking-wider hover:bg-white/10 transition-colors">Cancel</button>
                    <button onClick={handleLogout} className="flex-1 py-3 rounded-xl bg-red-500/20 border border-red-500/40 text-red-400 text-xs font-bold uppercase tracking-wider hover:bg-red-500/30 transition-colors">Log Out</button>
                </div>
            </ModalOverlay>

            {/* Delete Account Modal */}
            <ModalOverlay isOpen={activeModal === 'delete'} onClose={() => setActiveModal(null)} title="Delete Account">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-500/10 text-red-400 mx-auto mb-4 border border-red-500/20">
                    <AlertTriangle size={24} />
                </div>
                <p className="text-slate-300 text-sm mb-6 text-center">This action is permanent and cannot be undone. All your patient records, analyses, and history will be securely erased from our servers.</p>
                <div className="flex flex-col gap-3">
                    <button onClick={handleDeleteAccount} disabled={deleteLoading} className="w-full py-3 rounded-xl bg-red-500/20 border border-red-500/40 text-red-400 text-xs font-bold uppercase tracking-wider hover:bg-red-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">{deleteLoading ? 'Deleting...' : 'Delete Permanently'}</button>
                    <button onClick={() => setActiveModal(null)} disabled={deleteLoading} className="w-full py-3 rounded-xl bg-white/5 border border-white/10 text-white text-xs font-bold uppercase tracking-wider hover:bg-white/10 disabled:opacity-50 transition-colors">Cancel</button>
                </div>
            </ModalOverlay>

            {/* Clear Data Modal */}
            <ModalOverlay isOpen={activeModal === 'clear'} onClose={() => setActiveModal(null)} title="Clear Local Data">
                <p className="text-slate-300 text-sm mb-6 text-center">This will clear all cached images, offline patient data, and reset your local settings. You will need to log in again.</p>
                <div className="flex flex-col gap-3">
                    <button onClick={() => { localStorage.clear(); handleLogout(); }} className="w-full py-3 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400 text-xs font-bold uppercase tracking-wider hover:bg-amber-500/30 transition-colors">Clear Data</button>
                    <button onClick={() => setActiveModal(null)} className="w-full py-3 rounded-xl bg-white/5 border border-white/10 text-white text-xs font-bold uppercase tracking-wider hover:bg-white/10 transition-colors">Cancel</button>
                </div>
            </ModalOverlay>

            {/* Legal / Licenses Placeholder Modals */}
            <ModalOverlay isOpen={['tos', 'privacy', 'licenses'].includes(activeModal)} onClose={() => setActiveModal(null)} title={activeModal === 'tos' ? 'Terms of Service' : activeModal === 'privacy' ? 'Privacy Policy' : 'Data & Licenses'}>
                <div className="bg-black/30 border border-white/5 rounded-xl p-4 h-48 overflow-y-auto">
                    <p className="text-xs text-slate-400 leading-relaxed">
                        {activeModal === 'licenses'
                            ? 'LabMind AI is powered by open-source computer vision models and diagnostic datasets.\n\n• Training data from UMID, Chula-ParasiteEgg-11, and Clinical Bacteria Dataset.\n• All models and data are licensed under Creative Commons or corresponding Open Source licenses.\n• The AI enhancer utilizes Google Gemini via secure API endpoints.'
                            : 'This is a placeholder for the official legal document. In a production environment, this would contain the full legal text.'
                        }
                    </p>
                </div>
                <button onClick={() => setActiveModal(null)} className="mt-4 w-full py-3 rounded-xl bg-white/10 text-white text-xs font-bold uppercase tracking-wider hover:bg-white/20 transition-colors">Close</button>
            </ModalOverlay>

        </div>
    );
}
