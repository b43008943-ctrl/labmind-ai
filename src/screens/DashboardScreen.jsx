import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAppSettings } from '../context/AppSettingsContext';
import { useAuth } from '../context/AuthContext';
import { useAppState } from '../context/AppStateContext';
// Navigation is now rendered in DashboardPager (persistent across views)
import { HoloFileHeart, HoloDna, HoloBookOpen, HoloGauge } from '../components/HoloIcons';
import { Database, FileText } from 'lucide-react';
import { AlertBellBadge } from '../components/AlertsPanel';

/* ═══════════════════════════════════════════════════════════════
   DASHBOARD — BioForge Dark Design Language
   Font: Plus Jakarta Sans | Theme: Deep Space
   ═══════════════════════════════════════════════════════════════ */

const CARDS = [
  {
    id: 'virtual-lab',
    emoji: '🔬',
    title: 'Virtual Lab',
    sub: 'AI Microscopy',
    desc: '4 models • 98.8% accuracy',
    tag: 'LIVE AI',
    target: 'virtual-lab',
    color: '#00D4FF',
    glow: 'rgba(0,212,255,0.12)',
    bg: 'radial-gradient(ellipse at top right, rgba(0,212,255,0.07), transparent 70%), linear-gradient(135deg,rgba(0,30,50,0.95),rgba(0,10,25,0.98))',
    border: 'rgba(0,212,255,0.18)',
  },
  {
    id: 'academic',
    emoji: '🎓',
    title: 'Academic Hub',
    sub: 'Research & Learning',
    desc: 'Quizzes • Library • Videos',
    tag: 'LEARN',
    target: 'academic-hub',
    color: '#A78BFA',
    glow: 'rgba(139,92,246,0.12)',
    bg: 'radial-gradient(ellipse at top right, rgba(139,92,246,0.07), transparent 70%), linear-gradient(135deg,rgba(25,10,55,0.95),rgba(10,5,30,0.98))',
    border: 'rgba(139,92,246,0.18)',
  },
  {
    id: 'rasha',
    emoji: '🤖',
    title: 'Rasha AI',
    sub: 'Intelligent Assistant',
    desc: 'Ask • Learn • Discover',
    tag: 'AI',
    target: 'ai-assistant',
    color: '#F59E0B',
    glow: 'rgba(245,158,11,0.12)',
    bg: 'radial-gradient(ellipse at top right, rgba(245,158,11,0.07), transparent 70%), linear-gradient(135deg,rgba(40,20,0,0.95),rgba(20,8,0,0.98))',
    border: 'rgba(245,158,11,0.18)',
  },
  {
    id: 'results',
    emoji: '📊',
    title: 'Lab Results',
    sub: 'Document Analyzer',
    desc: 'Upload • Analyze • Report',
    tag: 'ANALYZE',
    target: 'lab-results-analyzer',
    color: '#10B981',
    glow: 'rgba(16,185,129,0.12)',
    bg: 'radial-gradient(ellipse at top right, rgba(16,185,129,0.07), transparent 70%), linear-gradient(135deg,rgba(0,25,15,0.95),rgba(0,10,8,0.98))',
    border: 'rgba(16,185,129,0.18)',
  },
];

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return { text: 'Good Morning', icon: '🌅' };
  if (h < 17) return { text: 'Good Afternoon', icon: '☀️' };
  return { text: 'Good Evening', icon: '🌙' };
}

export default function DashboardScreen({ onNavigate, alerts = {}, onOpenModal, analystName, user, onSlideToCommunity, activeView }) {
    const { isLight } = useAppSettings();
    const { currentUser } = useAuth();
    const { xp, level, equipped } = useAppState();
    const [screenState, setScreenState] = useState('screen-transition-hidden');
    const [pushedCard, setPushedCard] = useState(null);
    const [dimmedCard, setDimmedCard] = useState(null);

    useEffect(() => {
        const t = setTimeout(() => setScreenState('screen-visible'), 50);
        return () => clearTimeout(t);
    }, []);

    const handleNavigation = (target) => {
        setScreenState('screen-exit');
        setTimeout(() => onNavigate(target), 600);
    };

    const handleCardClick = (cardId, action, targetPath) => {
        if (pushedCard) return; // Prevent double clicks

        // Phase 1: Heavy Push & Dim (starts immediately)
        setPushedCard(cardId);
        setDimmedCard(cardId);

        // Phase 2: Enter/Navigate (fluid 'one-touch' 400ms transition)
        setTimeout(() => {
            if (action === 'modal') {
                setPushedCard(null);
                setDimmedCard(null);
                onOpenModal();
            } else {
                handleNavigation(targetPath);
            }
        }, 400);
    };

    const hasAnyAlert = Object.values(alerts).some(v => v);
    const greeting = getGreeting();
    const displayName = currentUser?.full_name || currentUser?.name || user?.name || 'Scholar';

    const frameColors = {
      'f1': '#CD7F32', // Bronze Frame
      'f2': '#C0C0C0', // Silver Frame
      'f3': '#FFD700', // Gold Frame
      'f4': '#00D4FF', // Diamond Frame
    };
    const frameColor = frameColors[equipped?.frame] || null;

    return (
      <div style={{
        minHeight: '100vh',
        background: 'radial-gradient(ellipse at 25% 15%, rgba(0,180,220,0.07) 0%, transparent 55%), radial-gradient(ellipse at 80% 75%, rgba(100,60,200,0.06) 0%, transparent 50%), linear-gradient(180deg, #070C1A 0%, #050810 100%)',
        fontFamily: "'Plus Jakarta Sans', sans-serif",
        color: '#E8F4FF',
        overflowX: 'hidden',
        overflowY: 'auto',
        WebkitOverflowScrolling: 'touch',
        position: 'relative',
      }}>

        <style>{`
@keyframes statusPulse { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:0.4;transform:scale(1.5);} }
        `}</style>

        {/* AMBIENT ORBS */}
        <div style={{position:'fixed',inset:0,pointerEvents:'none',zIndex:0}}>
          <div style={{position:'absolute',top:'5%',left:'15%',width:260,height:260,borderRadius:'50%',background:'radial-gradient(circle, rgba(0,180,220,0.05) 0%, transparent 70%)'}} />
          <div style={{position:'absolute',bottom:'15%',right:'5%',width:200,height:200,borderRadius:'50%',background:'radial-gradient(circle, rgba(100,60,200,0.04) 0%, transparent 70%)'}} />
        </div>

        <div style={{position:'relative',zIndex:1,paddingBottom:16}}>

          {/* ═══ STICKY HEADER ═══ */}
          <div style={{
            position:'sticky',top:0,zIndex:20,
            padding:'12px 20px 10px',
            background:'rgba(5,8,16,0.85)',
            backdropFilter:'blur(24px)',
            WebkitBackdropFilter:'blur(24px)',
            borderBottom:'1px solid rgba(255,255,255,0.05)',
          }}>
            <div style={{display:'flex',alignItems:'center',gap:12}}>

              {/* Avatar (Crackling Energy Core) — PRESERVED */}
              <div className="relative flex items-center justify-center" style={{flexShrink:0}}>
                {/* Inner Lightning Ring (Clockwise) */}
                <div className="absolute inset-[-4px] rounded-full border-2 border-dashed border-cyan-400 shadow-[0_0_15px_#22d3ee] animate-[spin_3s_linear_infinite]"
                    style={{ borderRadius: '45% 55% 40% 60% / 55% 45% 60% 40%' }}
                />
                {/* Outer Electric Ring (Counter-Clockwise) */}
                <div className="absolute inset-[-8px] rounded-full border border-dashed border-cyan-500/60 shadow-[0_0_8px_rgba(34,211,238,0.4)]"
                    style={{ animation: 'spin 4s linear infinite reverse', borderRadius: '50% 40% 60% 45% / 45% 60% 40% 55%' }}
                />
                <img
                    src={user?.avatar || "https://api.dicebear.com/7.x/avataaars/svg?seed=Alpha"}
                    className="relative z-10 w-12 h-12 object-cover rounded-full ring-1 ring-cyan-500/40 ring-offset-4 ring-offset-transparent"
                    style={frameColor ? { boxShadow: `0 0 0 3px ${frameColor}, 0 0 16px ${frameColor}60` } : {}}
                    alt="User Avatar"
                />
                <div className="absolute z-20 bottom-0 right-0 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-[#0a0a0a]" />
              </div>

              {/* User Info */}
              <div style={{flex:1,minWidth:0}}>
                <div style={{display:'flex',alignItems:'center',gap:6,flexWrap:'wrap'}}>
                  <p style={{margin:0,fontSize:11,color:'rgba(0,200,255,0.55)',fontWeight:500,letterSpacing:0.5}}>
                    {greeting.icon} {greeting.text}
                  </p>
                  <span style={{fontSize:8,fontWeight:800,color:'#00D4FF',background:'rgba(0,212,255,0.1)',border:'1px solid rgba(0,212,255,0.25)',padding:'1px 5px',borderRadius:4,fontFamily:"'JetBrains Mono',monospace"}}>LVL {level}</span>
                  <span style={{fontSize:8,fontWeight:800,color:'#F59E0B',background:'rgba(245,158,11,0.1)',border:'1px solid rgba(245,158,11,0.25)',padding:'1px 5px',borderRadius:4,fontFamily:"'JetBrains Mono',monospace"}}>{xp.toLocaleString()} XP</span>
                </div>
                <h1 style={{margin:'3px 0 1px',fontSize:17,fontWeight:800,color:'#F0F9FF',letterSpacing:-0.3,lineHeight:1.1,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>
                  {displayName}
                </h1>
                <p style={{margin:0,fontSize:9,color:'rgba(255,255,255,0.2)',letterSpacing:2,fontWeight:600,fontFamily:"'JetBrains Mono',monospace"}}>
                  SMART ANALYST SYSTEM
                </p>
              </div>

              {/* Header Actions — PRESERVED */}
              <div style={{display:'flex',alignItems:'center',gap:6,flexShrink:0}}>
                <AlertBellBadge onClick={() => onNavigate('alerts')} />
                <button
                    onClick={() => onNavigate('my-reports')}
                    className="flex items-center gap-2 bg-transparent border border-indigo-500/30 text-indigo-400 px-3 py-2 rounded hover:bg-indigo-500/10 transition-colors cursor-pointer font-sans text-xs font-medium tracking-wide"
                >
                    <FileText size={14} className="text-indigo-400" />
                    REPORTS
                </button>
                <button
                    onClick={() => onNavigate('archive')}
                    className="flex items-center gap-2 bg-transparent border border-cyan-500/30 text-cyan-400 px-3 py-2 rounded hover:bg-cyan-500/10 transition-colors cursor-pointer font-sans text-xs font-medium tracking-wide"
                >
                    <Database size={14} className="text-cyan-400" />
                    ARCHIVE
                </button>
              </div>

            </div>
          </div>

          {/* ═══ STATS BAR ═══ */}
          <div style={{padding:'14px 16px 0'}}>
            <div style={{display:'flex',background:'rgba(255,255,255,0.025)',border:'1px solid rgba(255,255,255,0.06)',borderRadius:14,padding:'10px 4px',backdropFilter:'blur(12px)'}}>
              {[
                {v:'4',l:'Labs',c:'#00D4FF'},
                {v:'98.8%',l:'Accuracy',c:'#10B981'},
                {v:'AI',l:'Active',c:'#A78BFA'},
                {v:'54',l:'Endpoints',c:'#F59E0B'},
              ].map((s,i,arr) => (
                <div key={i} style={{flex:1,textAlign:'center',borderRight:i<arr.length-1?'1px solid rgba(255,255,255,0.05)':'none'}}>
                  <p style={{margin:0,fontSize:15,fontWeight:800,color:s.c,lineHeight:1}}>{s.v}</p>
                  <p style={{margin:'3px 0 0',fontSize:9,color:'rgba(255,255,255,0.25)',textTransform:'uppercase',letterSpacing:0.8,fontWeight:600}}>{s.l}</p>
                </div>
              ))}
            </div>
          </div>

          {/* ═══ SECTION LABEL ═══ */}
          <div style={{padding:'18px 20px 8px',display:'flex',alignItems:'center',gap:8}}>
            <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',textTransform:'uppercase',letterSpacing:2}}>◆ Main Modules</span>
            <div style={{flex:1,height:1,background:'rgba(255,255,255,0.04)'}}/>
          </div>

          {/* ═══ 4 CARDS GRID ═══ */}
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10,padding:'0 16px'}}>
            {CARDS.map((card, i) => (
              <motion.div
                key={card.id}
                initial={{opacity:0,y:20,scale:0.97}}
                animate={{opacity:1,y:0,scale:1}}
                transition={{delay:i*0.08,duration:0.4,ease:[0.22,1,0.36,1]}}
                whileTap={{scale:0.93,transition:{duration:0.1}}}
                onClick={() => onNavigate(card.target)}
                style={{
                  background:card.bg,
                  border:`1px solid ${card.border}`,
                  borderRadius:16,
                  padding:'14px 12px',
                  cursor:'pointer',
                  position:'relative',
                  overflow:'hidden',
                  minHeight:128,
                  display:'flex',
                  flexDirection:'column',
                  justifyContent:'space-between',
                  boxShadow:`0 0 20px ${card.glow}, inset 0 1px 0 rgba(255,255,255,0.04)`,
                  touchAction: 'manipulation',
                  WebkitTapHighlightColor: 'transparent',
                }}
              >
                {/* HUD CORNER TOP-RIGHT */}
                <div style={{position:'absolute',top:8,right:8,width:16,height:16,borderTop:`2px solid ${card.color}60`,borderRight:`2px solid ${card.color}60`,borderRadius:'0 3px 0 0'}}/>
                {/* HUD CORNER BOTTOM-LEFT */}
                <div style={{position:'absolute',bottom:8,left:8,width:12,height:12,borderBottom:`2px solid ${card.color}40`,borderLeft:`2px solid ${card.color}40`,borderRadius:'0 0 0 2px'}}/>

                {/* TOP: emoji + tag */}
                <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}>
                  <span style={{
                    fontSize:28,
                    fontFamily:'Apple Color Emoji, Segoe UI Emoji, Segoe UI Symbol, sans-serif',
                    filter:`drop-shadow(0 0 8px ${card.color}70)`,
                    lineHeight:1
                  }}>{card.emoji}</span>
                  <span style={{fontSize:8,fontWeight:700,letterSpacing:1.2,padding:'2px 6px',borderRadius:4,background:`${card.color}18`,color:card.color,border:`1px solid ${card.color}30`,fontFamily:"'JetBrains Mono',monospace"}}>{card.tag}</span>
                </div>

                {/* BOTTOM: text */}
                <div style={{position:'relative',zIndex:1}}>
                  <h2 style={{margin:'0 0 2px',fontSize:13,fontWeight:800,color:'#F0F9FF',letterSpacing:-0.2}}>{card.title}</h2>
                  <p style={{margin:'0 0 3px',fontSize:10,color:'rgba(255,255,255,0.35)',fontWeight:500}}>{card.sub}</p>
                  <p style={{margin:0,fontSize:9,color:card.color,opacity:0.7,fontWeight:500}}>{card.desc}</p>
                </div>

                {/* BOTTOM GLOW LINE */}
                <div style={{position:'absolute',bottom:0,left:'12%',right:'12%',height:1,background:`linear-gradient(90deg,transparent,${card.color}50,transparent)`}}/>
              </motion.div>
            ))}
          </div>

          {/* ═══ STATUS BAR ═══ */}
          <div style={{padding:'12px 16px 0'}}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'9px 14px',background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.05)',borderRadius:10}}>
              <div style={{display:'flex',alignItems:'center',gap:7}}>
                <div style={{width:6,height:6,borderRadius:'50%',background:'#10B981',animation:'statusPulse 2s ease-in-out infinite'}}/>
                <span style={{fontSize:10,color:'rgba(255,255,255,0.25)',letterSpacing:1,fontWeight:600,fontFamily:"'JetBrains Mono',monospace"}}>SYSTEM STATUS</span>
              </div>
              <span style={{fontSize:10,color:'#10B981',fontWeight:700,letterSpacing:0.5}}>ALL SYSTEMS OPTIMAL</span>
            </div>
          </div>

        </div>
      </div>
    );
}
