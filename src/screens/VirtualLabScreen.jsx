import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const LABS = [
  { id:'hematology-lab', emoji:'🩸', title:'Hematology', sub:'Blood Cell Analysis', tag:'V1 ASYNC', color:'#EF4444', glow:'rgba(239,68,68,0.12)', bg:'radial-gradient(ellipse at top right,rgba(239,68,68,0.07),transparent 70%),linear-gradient(135deg,rgba(40,5,5,0.95),rgba(20,3,3,0.98))', border:'rgba(239,68,68,0.18)', accuracy:'82%', live:true },
  { id:'urinalysis', emoji:'💧', title:'Urinalysis', sub:'Sediment Analysis', tag:'3 CLASSES', color:'#F59E0B', glow:'rgba(245,158,11,0.12)', bg:'radial-gradient(ellipse at top right,rgba(245,158,11,0.07),transparent 70%),linear-gradient(135deg,rgba(40,25,0,0.95),rgba(20,12,0,0.98))', border:'rgba(245,158,11,0.18)', accuracy:'79.4%', live:true },
  { id:'parasitology-lab', emoji:'🦠', title:'Parasitology', sub:'11 Species Detection', tag:'98.8% ACC', color:'#10B981', glow:'rgba(16,185,129,0.12)', bg:'radial-gradient(ellipse at top right,rgba(16,185,129,0.07),transparent 70%),linear-gradient(135deg,rgba(0,25,15,0.95),rgba(0,12,8,0.98))', border:'rgba(16,185,129,0.18)', accuracy:'98.8%', live:true },
  { id:'microbiology-lab', emoji:'🧫', title:'Microbiology', sub:'Gram Classification', tag:'4 CLASSES', color:'#8B5CF6', glow:'rgba(139,92,246,0.12)', bg:'radial-gradient(ellipse at top right,rgba(139,92,246,0.07),transparent 70%),linear-gradient(135deg,rgba(25,8,50,0.95),rgba(12,4,28,0.98))', border:'rgba(139,92,246,0.18)', accuracy:'88.6%', live:true },
  { id:'clinical', emoji:'⚗️', title:'Biochemistry', sub:'Metabolic Panels', tag:'COMING SOON', color:'#06B6D4', glow:'rgba(6,182,212,0.06)', bg:'radial-gradient(ellipse at top right,rgba(6,182,212,0.03),transparent 70%),linear-gradient(135deg,rgba(0,20,25,0.95),rgba(0,10,15,0.98))', border:'rgba(6,182,212,0.1)', accuracy:'—', live:false },
  { id:'bloodbank-lab', emoji:'🩹', title:'Blood Bank', sub:'Transfusion System', tag:'COMING SOON', color:'#F43F5E', glow:'rgba(244,63,94,0.06)', bg:'radial-gradient(ellipse at top right,rgba(244,63,94,0.03),transparent 70%),linear-gradient(135deg,rgba(35,3,10,0.95),rgba(18,2,8,0.98))', border:'rgba(244,63,94,0.1)', accuracy:'—', live:false },
]

export default function VirtualLabScreen({ onNavigate, alerts }) {
    const [screenState, setScreenState] = useState('screen-transition-hidden');

    useEffect(() => {
        const t = setTimeout(() => setScreenState('screen-visible'), 50);
        return () => clearTimeout(t);
    }, []);

    const handleNavigation = (target) => {
        setScreenState('screen-exit');
        setTimeout(() => onNavigate(target), 600);
    };

    return (
      <div style={{
        minHeight:'100vh',
        background:'radial-gradient(ellipse at 30% 20%, rgba(245,158,11,0.06) 0%, transparent 50%), linear-gradient(180deg,#070C1A 0%,#050810 100%)',
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
          borderBottom:'1px solid rgba(255,255,255,0.05)',
          display:'flex',alignItems:'center',gap:12,
        }}>
          <button
            onClick={() => onNavigate('dashboard')}
            style={{width:36,height:36,borderRadius:10,background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)',display:'flex',alignItems:'center',justifyContent:'center',cursor:'pointer',color:'rgba(255,255,255,0.6)',fontSize:16,flexShrink:0}}>
            ←
          </button>
          <div style={{flex:1}}>
            <h1 style={{margin:0,fontSize:17,fontWeight:800,color:'#F0F9FF',letterSpacing:-0.3}}>
              🔬 Virtual Lab
            </h1>
            <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)',letterSpacing:1,fontFamily:"'JetBrains Mono',monospace"}}>
              SELECT ANALYSIS PROTOCOL
            </p>
          </div>
          <div style={{display:'flex',alignItems:'center',gap:5,padding:'4px 10px',background:'rgba(16,185,129,0.08)',border:'1px solid rgba(16,185,129,0.2)',borderRadius:20}}>
            <div style={{width:5,height:5,borderRadius:'50%',background:'#10B981'}}/>
            <span style={{fontSize:9,fontWeight:700,color:'#10B981',fontFamily:"'JetBrains Mono',monospace"}}>4 LIVE</span>
          </div>
        </div>
    
        <div style={{padding:'16px 16px 32px'}}>
    
          {/* HERO STATS */}
          <div style={{display:'flex',gap:8,marginBottom:20}}>
            {[
              {v:'6',l:'Total Labs',c:'#E8F4FF'},
              {v:'4',l:'AI Active',c:'#10B981'},
              {v:'YOLOv8',l:'Model',c:'#00D4FF'},
              {v:'82-98%',l:'Accuracy',c:'#A78BFA'},
            ].map((s,i) => (
              <div key={i} style={{flex:1,textAlign:'center',padding:'8px 4px',background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.05)',borderRadius:10}}>
                <p style={{margin:0,fontSize:12,fontWeight:800,color:s.c,lineHeight:1}}>{s.v}</p>
                <p style={{margin:'3px 0 0',fontSize:8,color:'rgba(255,255,255,0.25)',textTransform:'uppercase',letterSpacing:0.5}}>{s.l}</p>
              </div>
            ))}
          </div>
    
          {/* SECTION LABEL */}
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:12}}>
            <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',textTransform:'uppercase',letterSpacing:2}}>◆ Laboratories</span>
            <div style={{flex:1,height:1,background:'rgba(255,255,255,0.04)'}}/>
          </div>
    
          {/* LAB CARDS GRID */}
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
            {LABS.map((lab, i) => (
              <motion.div
                key={lab.id}
                initial={{opacity:0,y:20,scale:0.97}}
                animate={{opacity:1,y:0,scale:1}}
                transition={{delay:i*0.07,duration:0.4,ease:[0.22,1,0.36,1]}}
                whileTap={lab.live ? {scale:0.93,transition:{duration:0.1}} : {}}
                onClick={() => lab.live && onNavigate(lab.id)}
                style={{
                  background:lab.bg,
                  border:`1px solid ${lab.border}`,
                  borderRadius:16,
                  padding:'14px 12px',
                  cursor:lab.live ? 'pointer' : 'default',
                  position:'relative',
                  overflow:'hidden',
                  minHeight:130,
                  display:'flex',
                  flexDirection:'column',
                  justifyContent:'space-between',
                  opacity:lab.live ? 1 : 0.5,
                  boxShadow:lab.live ? `0 0 20px ${lab.glow}, inset 0 1px 0 rgba(255,255,255,0.04)` : 'none',
                }}
              >
                {/* HUD CORNER */}
                <div style={{position:'absolute',top:8,right:8,width:14,height:14,borderTop:`2px solid ${lab.color}55`,borderRight:`2px solid ${lab.color}55`,borderRadius:'0 3px 0 0'}}/>
                <div style={{position:'absolute',bottom:8,left:8,width:10,height:10,borderBottom:`2px solid ${lab.color}35`,borderLeft:`2px solid ${lab.color}35`}}/>
    
                {/* COMING SOON OVERLAY */}
                {!lab.live && (
                  <div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',background:'rgba(5,8,16,0.4)',borderRadius:16,zIndex:2}}>
                    <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.3)',letterSpacing:2,fontFamily:"'JetBrains Mono',monospace"}}>COMING SOON</span>
                  </div>
                )}
    
                {/* TOP */}
                <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}>
                  <span style={{fontSize:26,fontFamily:'Apple Color Emoji,Segoe UI Emoji,sans-serif',filter:lab.live?`drop-shadow(0 0 8px ${lab.color}70)`:'none',lineHeight:1}}>{lab.emoji}</span>
                  <span style={{fontSize:8,fontWeight:700,letterSpacing:1,padding:'2px 6px',borderRadius:4,background:`${lab.color}18`,color:lab.live?lab.color:'rgba(255,255,255,0.2)',border:`1px solid ${lab.color}30`,fontFamily:"'JetBrains Mono',monospace"}}>{lab.tag}</span>
                </div>
    
                {/* BOTTOM */}
                <div>
                  <h2 style={{margin:'0 0 2px',fontSize:13,fontWeight:800,color:lab.live?'#F0F9FF':'rgba(255,255,255,0.4)',letterSpacing:-0.2}}>{lab.title}</h2>
                  <p style={{margin:'0 0 6px',fontSize:10,color:'rgba(255,255,255,0.3)',fontWeight:500}}>{lab.sub}</p>
                  {lab.live && (
                    <div style={{display:'flex',alignItems:'center',gap:4}}>
                      <div style={{width:4,height:4,borderRadius:'50%',background:lab.color}}/>
                      <span style={{fontSize:9,color:lab.color,fontWeight:700,fontFamily:"'JetBrains Mono',monospace"}}>{lab.accuracy} mAP</span>
                    </div>
                  )}
                </div>
    
                {/* BOTTOM GLOW LINE */}
                {lab.live && <div style={{position:'absolute',bottom:0,left:'12%',right:'12%',height:1,background:`linear-gradient(90deg,transparent,${lab.color}50,transparent)`}}/>}
              </motion.div>
            ))}
          </div>
    
        </div>
      </div>
    )
}
