import { motion } from 'framer-motion';
import { useNavigation } from '../context/NavigationContext';

/* ═══════════════════════════════════════════════════════════════
   ACADEMIC HUB — BioForge Dark Design Language
   Font: Plus Jakarta Sans | Primary: Violet #8B5CF6
   ═══════════════════════════════════════════════════════════════ */

const MODULES = [
  { id:'knowledge-library', emoji:'📚', title:'Digital Library', sub:'Textbooks & Research', tag:'LIBRARY', color:'#8B5CF6', glow:'rgba(139,92,246,0.12)', bg:'radial-gradient(ellipse at top right,rgba(139,92,246,0.07),transparent 70%),linear-gradient(135deg,rgba(25,10,55,0.95),rgba(10,5,30,0.98))', border:'rgba(139,92,246,0.18)' },
  { id:'ailab', emoji:'🤖', title:'AI Generative Lab', sub:'Create AI Content', tag:'GENERATE', color:'#00D4FF', glow:'rgba(0,212,255,0.12)', bg:'radial-gradient(ellipse at top right,rgba(0,212,255,0.07),transparent 70%),linear-gradient(135deg,rgba(0,30,50,0.95),rgba(0,10,25,0.98))', border:'rgba(0,212,255,0.18)' },
  { id:'ai-testing-center', emoji:'📝', title:'Testing Center', sub:'Quizzes & Exams', tag:'TEST', color:'#10B981', glow:'rgba(16,185,129,0.12)', bg:'radial-gradient(ellipse at top right,rgba(16,185,129,0.07),transparent 70%),linear-gradient(135deg,rgba(0,25,15,0.95),rgba(0,12,8,0.98))', border:'rgba(16,185,129,0.18)' },
  { id:'video-generator', emoji:'🎬', title:'Video Generator', sub:'AI Video Content', tag:'VIDEO', color:'#F59E0B', glow:'rgba(245,158,11,0.12)', bg:'radial-gradient(ellipse at top right,rgba(245,158,11,0.07),transparent 70%),linear-gradient(135deg,rgba(40,20,0,0.95),rgba(20,8,0,0.98))', border:'rgba(245,158,11,0.18)' },
  { id:'holo-lab', emoji:'🔮', title:'Holographic Lab', sub:'3D Exploration', tag:'HOLO', color:'#EC4899', glow:'rgba(236,72,153,0.12)', bg:'radial-gradient(ellipse at top right,rgba(236,72,153,0.07),transparent 70%),linear-gradient(135deg,rgba(35,5,20,0.95),rgba(18,3,12,0.98))', border:'rgba(236,72,153,0.18)' },
  { id:'curriculum-vault', emoji:'📖', title:'Curriculum Vault', sub:'Course Materials', tag:'VAULT', color:'#3B82F6', glow:'rgba(59,130,246,0.12)', bg:'radial-gradient(ellipse at top right,rgba(59,130,246,0.07),transparent 70%),linear-gradient(135deg,rgba(5,15,40,0.95),rgba(3,8,25,0.98))', border:'rgba(59,130,246,0.18)' },
  { id:'ai-archive', emoji:'🗃️', title:'AI Archive', sub:'Generated Content History', tag:'ARCHIVE', color:'#6B7280', glow:'rgba(107,114,128,0.08)', bg:'radial-gradient(ellipse at top right,rgba(107,114,128,0.04),transparent 70%),linear-gradient(135deg,rgba(15,15,20,0.95),rgba(8,8,12,0.98))', border:'rgba(107,114,128,0.12)' },
];

export default function AcademicHubScreen() {
    const { navigate, goBack } = useNavigation();

    const onNavigate = navigate;

    return (
      <div style={{
        minHeight:'100vh',
        background:'radial-gradient(ellipse at 30% 15%, rgba(139,92,246,0.08) 0%, transparent 55%), linear-gradient(180deg,#070C1A 0%,#050810 100%)',
        fontFamily:"'Plus Jakarta Sans',sans-serif",
        color:'#E8F4FF',
        overflowX:'hidden',
        overflowY:'auto',
        WebkitOverflowScrolling:'touch',
      }}>


        {/* HEADER */}
        <div style={{
          position:'sticky',top:0,zIndex:20,
          padding:'14px 20px',
          background:'rgba(5,8,16,0.85)',
          backdropFilter:'blur(24px)',
          WebkitBackdropFilter:'blur(24px)',
          borderBottom:'1px solid rgba(139,92,246,0.1)',
          display:'flex',alignItems:'center',gap:12,
        }}>
          <button
            onClick={() => navigate('dashboard')}
            style={{width:36,height:36,borderRadius:10,background:'rgba(139,92,246,0.08)',border:'1px solid rgba(139,92,246,0.2)',display:'flex',alignItems:'center',justifyContent:'center',cursor:'pointer',color:'#A78BFA',fontSize:16,flexShrink:0}}>
            ←
          </button>
          <div style={{flex:1}}>
            <h1 style={{margin:0,fontSize:17,fontWeight:800,color:'#F0F9FF',letterSpacing:-0.3}}>
              🎓 Academic Hub
            </h1>
            <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)',letterSpacing:1,fontFamily:"'JetBrains Mono',monospace"}}>
              RESEARCH & LEARNING CENTER
            </p>
          </div>
          <div style={{display:'flex',alignItems:'center',gap:5,padding:'4px 10px',background:'rgba(139,92,246,0.08)',border:'1px solid rgba(139,92,246,0.2)',borderRadius:20}}>
            <span style={{fontSize:9,fontWeight:700,color:'#A78BFA',fontFamily:"'JetBrains Mono',monospace"}}>7 MODULES</span>
          </div>
        </div>

        <div style={{padding:'16px 16px 32px'}}>

          {/* HERO STATS */}
          <div style={{
            padding:'12px 16px',
            background:'rgba(139,92,246,0.05)',
            border:'1px solid rgba(139,92,246,0.12)',
            borderRadius:14,
            marginBottom:20,
            display:'flex',
            alignItems:'center',
            justifyContent:'space-between',
          }}>
            <div>
              <p style={{margin:0,fontSize:13,fontWeight:700,color:'#A78BFA'}}>Learning Center</p>
              <p style={{margin:'2px 0 0',fontSize:10,color:'rgba(255,255,255,0.3)'}}>AI-powered academic tools for medical students</p>
            </div>
            <span style={{fontSize:28,fontFamily:'Apple Color Emoji,Segoe UI Emoji,sans-serif'}}>🧬</span>
          </div>

          {/* SECTION LABEL */}
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:12}}>
            <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',textTransform:'uppercase',letterSpacing:2}}>◆ Modules</span>
            <div style={{flex:1,height:1,background:'rgba(255,255,255,0.04)'}}/>
          </div>

          {/* FIRST 6 MODULES — 2 column grid */}
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10,marginBottom:10}}>
            {MODULES.slice(0,6).map((mod, i) => (
              <motion.div
                key={mod.id}
                initial={{opacity:0,y:20,scale:0.97}}
                animate={{opacity:1,y:0,scale:1}}
                transition={{delay:i*0.07,duration:0.4,ease:[0.22,1,0.36,1]}}
                whileTap={{scale:0.93,transition:{duration:0.1}}}
                onClick={() => onNavigate(mod.id)}
                style={{
                  background:mod.bg,
                  border:`1px solid ${mod.border}`,
                  borderRadius:16,
                  padding:'14px 12px',
                  cursor:'pointer',
                  position:'relative',
                  overflow:'hidden',
                  minHeight:120,
                  display:'flex',
                  flexDirection:'column',
                  justifyContent:'space-between',
                  boxShadow:`0 0 20px ${mod.glow}, inset 0 1px 0 rgba(255,255,255,0.04)`,
                }}
              >
                {/* HUD CORNERS */}
                <div style={{position:'absolute',top:8,right:8,width:14,height:14,borderTop:`2px solid ${mod.color}55`,borderRight:`2px solid ${mod.color}55`,borderRadius:'0 3px 0 0'}}/>
                <div style={{position:'absolute',bottom:8,left:8,width:10,height:10,borderBottom:`2px solid ${mod.color}35`,borderLeft:`2px solid ${mod.color}35`}}/>

                {/* TOP */}
                <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}>
                  <span style={{fontSize:24,fontFamily:'Apple Color Emoji,Segoe UI Emoji,sans-serif',filter:`drop-shadow(0 0 8px ${mod.color}70)`,lineHeight:1}}>{mod.emoji}</span>
                  <span style={{fontSize:8,fontWeight:700,letterSpacing:1,padding:'2px 6px',borderRadius:4,background:`${mod.color}18`,color:mod.color,border:`1px solid ${mod.color}30`,fontFamily:"'JetBrains Mono',monospace"}}>{mod.tag}</span>
                </div>

                {/* BOTTOM */}
                <div>
                  <h2 style={{margin:'0 0 2px',fontSize:12,fontWeight:800,color:'#F0F9FF',letterSpacing:-0.2}}>{mod.title}</h2>
                  <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)',fontWeight:500}}>{mod.sub}</p>
                </div>

                {/* BOTTOM GLOW LINE */}
                <div style={{position:'absolute',bottom:0,left:'12%',right:'12%',height:1,background:`linear-gradient(90deg,transparent,${mod.color}50,transparent)`}}/>
              </motion.div>
            ))}
          </div>

          {/* 7TH MODULE — full width */}
          <motion.div
            initial={{opacity:0,y:20}}
            animate={{opacity:1,y:0}}
            transition={{delay:0.5,duration:0.4,ease:[0.22,1,0.36,1]}}
            whileTap={{scale:0.98,transition:{duration:0.1}}}
            onClick={() => onNavigate(MODULES[6].id)}
            style={{
              background:MODULES[6].bg,
              border:`1px solid ${MODULES[6].border}`,
              borderRadius:16,
              padding:'14px 16px',
              cursor:'pointer',
              position:'relative',
              overflow:'hidden',
              display:'flex',
              alignItems:'center',
              gap:16,
              boxShadow:`inset 0 1px 0 rgba(255,255,255,0.03)`,
            }}
          >
            <span style={{fontSize:28,fontFamily:'Apple Color Emoji,Segoe UI Emoji,sans-serif',opacity:0.6}}>{MODULES[6].emoji}</span>
            <div style={{flex:1}}>
              <h2 style={{margin:'0 0 2px',fontSize:13,fontWeight:700,color:'rgba(255,255,255,0.5)',letterSpacing:-0.2}}>{MODULES[6].title}</h2>
              <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.2)'}}>{MODULES[6].sub}</p>
            </div>
            <span style={{fontSize:8,fontWeight:700,letterSpacing:1,padding:'2px 7px',borderRadius:4,background:'rgba(107,114,128,0.12)',color:'rgba(255,255,255,0.25)',border:'1px solid rgba(107,114,128,0.15)',fontFamily:"'JetBrains Mono',monospace"}}>ARCHIVE</span>
            <span style={{color:'rgba(255,255,255,0.2)',fontSize:14}}>›</span>
          </motion.div>

        </div>
      </div>
    );
}
