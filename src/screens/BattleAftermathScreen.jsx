import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigation } from '../context/NavigationContext';
import { useAppState } from '../context/AppStateContext';

/* ═══════════════════════════════════════════════════════════════
   BATTLE AFTERMATH — BioForge Dark Design Language
   Font: Plus Jakarta Sans | Primary: #EC4899 (Pink/Magenta)
   ═══════════════════════════════════════════════════════════════ */

export default function BattleAftermathScreen() {
    const { navigate } = useNavigation();
    const { addXp } = useAppState();
    const [results, setResults] = useState(null);
    const [expandedQ, setExpandedQ] = useState(null);

    useEffect(() => {
        const data = sessionStorage.getItem('battle_results');
        let parsed = null;
        if (data) {
            parsed = JSON.parse(data);
        } else {
            // Fallback mock if accessed directly
            parsed = {
                myScore: 4500, oppScore: 3200,
                myCorrect: 8, oppCorrect: 6,
                myAvgTime: 4.2, oppAvgTime: 6.8,
                myMaxCombo: 4, oppMaxCombo: 2,
                totalQ: 10,
                history: [
                    { question: 'What shape is an Ascaris lumbricoides egg?', myCorrect: true, oppCorrect: false, correctAnswer: 'Oval with mammillated shell' },
                    { question: 'Gram-positive cocci in clusters suggest:', myCorrect: true, oppCorrect: true, correctAnswer: 'Staphylococcus' },
                ]
            };
        }
        setResults(parsed);

        const isWin = parsed.myScore > parsed.oppScore;
        const isDraw = parsed.myScore === parsed.oppScore;
        const earned = isWin ? 250 : isDraw ? 100 : 50;
        addXp(earned);
    }, []);

    if (!results) return <div style={{minHeight:'100vh',background:'#0C060F'}} />;

    const isWin = results.myScore > results.oppScore;
    const isDraw = results.myScore === results.oppScore;
    const outcomeStr = isWin ? 'VICTORY!' : isDraw ? 'DRAW' : 'DEFEAT';
    const outColor = isWin ? '#10B981' : isDraw ? '#F59E0B' : '#EF4444';
    const xpEarned = isWin ? 250 : isDraw ? 100 : 50;
    
    const myAcc = Math.round((results.myCorrect / results.totalQ) * 100);
    const oppAcc = Math.round((results.oppCorrect / results.totalQ) * 100);

    return (
      <div style={{
        minHeight:'100vh',
        background:'linear-gradient(180deg,#0C060F 0%,#080510 100%)',
        fontFamily:"'Plus Jakarta Sans',sans-serif",
        color:'#E8F4FF',
        display:'flex',flexDirection:'column',
        overflowY:'auto',
        WebkitOverflowScrolling:'touch',
        paddingBottom:32,
      }}>


        {/* BACKGROUND GLOW */}
        <div style={{position:'fixed',top:0,left:0,width:'100%',height:400,pointerEvents:'none',background:`radial-gradient(ellipse at top, ${outColor}18 0%, transparent 70%)`,zIndex:0}} />

        {/* ═══ BANNER ═══ */}
        <div style={{paddingTop:56,paddingBottom:24,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',position:'relative',zIndex:1}}>
          <motion.div initial={{scale:0.5,opacity:0}} animate={{scale:1,opacity:1}} transition={{type:'spring',bounce:0.5}}>
            <div style={{
              width:100,height:100,borderRadius:'50%',
              background: isWin
                ? 'radial-gradient(circle at 35% 35%, rgba(16,185,129,0.9), rgba(0,80,60,0.9))'
                : isDraw
                  ? 'radial-gradient(circle at 35% 35%, rgba(245,158,11,0.9), rgba(120,70,0,0.9))'
                  : 'radial-gradient(circle at 35% 35%, rgba(239,68,68,0.8), rgba(120,20,20,0.9))',
              boxShadow: `0 0 40px ${outColor}66, 0 0 80px ${outColor}22`,
              display:'flex',alignItems:'center',justifyContent:'center',
              fontSize:40,marginBottom:12,
            }}>
              {isWin ? '🏆' : isDraw ? '🤝' : '💀'}
            </div>
          </motion.div>

          <motion.h1 initial={{y:20,opacity:0}} animate={{y:0,opacity:1}} transition={{delay:0.2}}
            style={{margin:'0 0 4px',fontSize:36,fontWeight:900,letterSpacing:2,color:outColor,textShadow:`0 0 15px ${outColor}`,textTransform:'uppercase'}}>
            {outcomeStr}
          </motion.h1>
          <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)',fontWeight:700,letterSpacing:3,textTransform:'uppercase',fontFamily:"'JetBrains Mono',monospace"}}>
            BATTLE RESOLVED
          </p>
        </div>

        {/* ═══ SCORE COMPARISON ═══ */}
        <div style={{padding:'0 20px',marginBottom:20,position:'relative',zIndex:1}}>
          <div style={{
            display:'flex',alignItems:'center',justifyContent:'space-between',
            background:'rgba(0,0,0,0.3)',backdropFilter:'blur(12px)',
            borderRadius:20,padding:20,
            border:'1px solid rgba(255,255,255,0.05)',
            position:'relative',overflow:'hidden',
          }}>
            {/* You */}
            <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:6,zIndex:1}}>
              <div style={{
                width:56,height:56,borderRadius:14,display:'flex',alignItems:'center',justifyContent:'center',fontSize:24,
                background: isWin ? 'rgba(16,185,129,0.12)' : 'rgba(0,212,255,0.08)',
                border: isWin ? '2px solid rgba(16,185,129,0.4)' : '2px solid rgba(0,212,255,0.2)',
                boxShadow: isWin ? '0 0 20px rgba(16,185,129,0.3)' : 'none',
              }}>👤</div>
              <span style={{fontSize:9,fontWeight:800,color:'#F0F9FF',letterSpacing:3}}>YOU</span>
              <span style={{fontSize:22,fontWeight:900,color:'#F0F9FF',fontFamily:"'JetBrains Mono',monospace"}}>{results.myScore.toLocaleString()}</span>
            </div>

            <span style={{fontSize:20,fontWeight:900,color:'rgba(255,255,255,0.15)',fontStyle:'italic',zIndex:1}}>VS</span>

            {/* Opponent */}
            <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:6,zIndex:1}}>
              <div style={{
                width:56,height:56,borderRadius:14,display:'flex',alignItems:'center',justifyContent:'center',fontSize:24,
                background: !isWin && !isDraw ? 'rgba(16,185,129,0.12)' : 'rgba(236,72,153,0.08)',
                border: !isWin && !isDraw ? '2px solid rgba(16,185,129,0.4)' : '2px solid rgba(236,72,153,0.2)',
                boxShadow: !isWin && !isDraw ? '0 0 20px rgba(16,185,129,0.3)' : 'none',
              }}>👤</div>
              <span style={{fontSize:9,fontWeight:800,color:'#F0F9FF',letterSpacing:3}}>SHADOW K.</span>
              <span style={{fontSize:22,fontWeight:900,color:'#F0F9FF',fontFamily:"'JetBrains Mono',monospace"}}>{results.oppScore.toLocaleString()}</span>
            </div>

            {/* Score bar */}
            <div style={{position:'absolute',bottom:0,left:0,height:4,display:'flex',width:'100%'}}>
              <div style={{height:'100%',background:'#22D3EE',width:`${(results.myScore / Math.max(results.myScore + results.oppScore, 1)) * 100}%`}} />
              <div style={{height:'100%',background:'#EC4899',flex:1}} />
            </div>
          </div>
        </div>

        {/* ═══ REWARDS ═══ */}
        <div style={{padding:'0 20px',marginBottom:20,position:'relative',zIndex:1}}>
          <div style={{
            background:'rgba(245,158,11,0.06)',border:'1px solid rgba(245,158,11,0.15)',
            borderRadius:16,padding:'14px 16px',
            display:'flex',alignItems:'center',justifyContent:'space-between',
          }}>
            <div style={{display:'flex',alignItems:'center',gap:10}}>
              <span style={{fontSize:22}}>⭐</span>
              <div>
                <p style={{margin:0,fontSize:12,fontWeight:700,color:'#F59E0B',textTransform:'uppercase',letterSpacing:1}}>Rewards Earned</p>
                <p style={{margin:'2px 0 0',fontSize:10,color:'rgba(245,158,11,0.5)'}}>Added to your armory balance</p>
              </div>
            </div>
            <span style={{fontSize:18,fontWeight:900,color:'#F59E0B',fontFamily:"'JetBrains Mono',monospace"}}>+{xpEarned} XP</span>
          </div>
        </div>

        {/* ═══ PERFORMANCE STATS ═══ */}
        <div style={{padding:'0 20px',marginBottom:20,position:'relative',zIndex:1}}>
          <h3 style={{margin:'0 0 12px 4px',fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',textTransform:'uppercase',letterSpacing:2}}>◆ Performance Specs</h3>
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
            {[
              {icon:'🎯',label:'Accuracy',mine:`${myAcc}%`,opp:`vs ${oppAcc}%`},
              {icon:'⏱',label:'Avg Time',mine:`${results.myAvgTime.toFixed(1)}s`,opp:`vs ${results.oppAvgTime.toFixed(1)}s`},
              {icon:'🔥',label:'Best Combo',mine:`${results.myMaxCombo}x`,opp:`vs ${results.oppMaxCombo}x`},
              {icon:'✅',label:'Correct Hits',mine:`${results.myCorrect}/${results.totalQ}`,opp:`vs ${results.oppCorrect}`},
            ].map((s,i) => (
              <div key={i} style={{
                padding:'12px 14px',borderRadius:14,
                background:'rgba(255,255,255,0.025)',
                border:'1px solid rgba(255,255,255,0.06)',
                display:'flex',flexDirection:'column',gap:4,
              }}>
                <span style={{fontSize:14}}>{s.icon}</span>
                <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',textTransform:'uppercase',letterSpacing:1}}>{s.label}</span>
                <div style={{display:'flex',alignItems:'flex-end',justifyContent:'space-between'}}>
                  <span style={{fontSize:16,fontWeight:900,color:'#F0F9FF',fontFamily:"'JetBrains Mono',monospace"}}>{s.mine}</span>
                  <span style={{fontSize:10,color:'rgba(255,255,255,0.2)',fontFamily:"'JetBrains Mono',monospace"}}>{s.opp}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ═══ BATTLE LOG ═══ */}
        <div style={{padding:'0 20px',marginBottom:20,position:'relative',zIndex:1}}>
          <h3 style={{margin:'0 0 12px 4px',fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',textTransform:'uppercase',letterSpacing:2}}>◆ Battle Log Review</h3>
          <div style={{display:'flex',flexDirection:'column',gap:6}}>
            {results.history.map((q, i) => (
              <div key={i} style={{background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.05)',borderRadius:12,overflow:'hidden'}}>
                <div onClick={() => setExpandedQ(expandedQ === i ? null : i)}
                  style={{padding:'12px 14px',display:'flex',alignItems:'flex-start',justifyContent:'space-between',cursor:'pointer'}}>
                  <div style={{flex:1,paddingRight:12}}>
                    <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',fontFamily:"'JetBrains Mono',monospace"}}>Q{i + 1}</span>
                    <p style={{margin:'4px 0 0',fontSize:12,fontWeight:600,color:'#F0F9FF',lineHeight:1.4}}>{q.question}</p>
                  </div>
                  <div style={{display:'flex',alignItems:'center',gap:6,flexShrink:0}}>
                    {/* You indicator */}
                    <div style={{
                      width:22,height:22,borderRadius:4,display:'flex',alignItems:'center',justifyContent:'center',fontSize:10,
                      background: q.myCorrect ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                      color: q.myCorrect ? '#34D399' : '#EF4444',
                    }}>{q.myCorrect ? '✓' : '✗'}</div>
                    {/* Opp indicator */}
                    <div style={{
                      width:22,height:22,borderRadius:4,display:'flex',alignItems:'center',justifyContent:'center',fontSize:10,
                      background: q.oppCorrect ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                      color: q.oppCorrect ? '#34D399' : '#EF4444',
                    }}>{q.oppCorrect ? '✓' : '✗'}</div>
                    <span style={{fontSize:14,color:'rgba(255,255,255,0.2)',marginLeft:4,transition:'transform 0.2s',transform:expandedQ===i?'rotate(180deg)':'rotate(0)'}}>▾</span>
                  </div>
                </div>
                
                <AnimatePresence>
                  {expandedQ === i && (
                    <motion.div initial={{height:0}} animate={{height:'auto'}} exit={{height:0}} style={{overflow:'hidden'}}>
                      <div style={{padding:'12px 14px',background:'rgba(0,0,0,0.2)',borderTop:'1px solid rgba(255,255,255,0.04)',display:'flex',flexDirection:'column',gap:6}}>
                        <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',textTransform:'uppercase',letterSpacing:1}}>Correct Answer</span>
                        <div style={{padding:'8px 12px',borderRadius:8,background:'rgba(16,185,129,0.08)',border:'1px solid rgba(16,185,129,0.15)',display:'flex',alignItems:'center',gap:8}}>
                          <span style={{color:'#34D399',fontSize:12}}>✓</span>
                          <span style={{fontSize:12,fontWeight:600,color:'#34D399'}}>{q.correctAnswer}</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>

        {/* ═══ ACTION BUTTONS ═══ */}
        <div style={{padding:'0 20px',display:'flex',flexDirection:'column',gap:10,position:'relative',zIndex:1}}>
          <button onClick={() => navigate('battle')}
            style={{
              width:'100%',padding:'14px',borderRadius:14,border:'none',
              background:'linear-gradient(135deg,#BE185D,#EC4899)',
              color:'#fff',fontSize:13,fontWeight:700,cursor:'pointer',
              fontFamily:"'Plus Jakarta Sans',sans-serif",
              boxShadow:'0 0 20px rgba(236,72,153,0.3)',
              display:'flex',alignItems:'center',justifyContent:'center',gap:8,
            }}>
            ⚔️ Rematch
          </button>
          <div style={{display:'flex',gap:10}}>
            <button onClick={() => navigate('community')}
              style={{
                flex:1,padding:'14px',borderRadius:14,
                background:'rgba(255,255,255,0.04)',
                border:'1px solid rgba(255,255,255,0.08)',
                color:'rgba(255,255,255,0.6)',fontSize:12,fontWeight:600,cursor:'pointer',
                fontFamily:"'Plus Jakarta Sans',sans-serif",
              }}>
              ← Community
            </button>
            <button onClick={() => navigate('armory')}
              style={{
                flex:1,padding:'14px',borderRadius:14,
                background:'rgba(168,85,247,0.06)',
                border:'1px solid rgba(168,85,247,0.15)',
                color:'#A855F7',fontSize:12,fontWeight:600,cursor:'pointer',
                fontFamily:"'Plus Jakarta Sans',sans-serif",
                display:'flex',alignItems:'center',justifyContent:'center',gap:6,
              }}>
              📊 Share
            </button>
          </div>
        </div>

      </div>
    );
}
