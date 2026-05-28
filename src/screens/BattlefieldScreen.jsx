import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigation } from '../context/NavigationContext';

/* ═══════════════════════════════════════════════════════════════
   BATTLEFIELD — BioForge Dark Design Language
   Font: Plus Jakarta Sans | Primary: #EC4899 (Pink/Magenta)
   ═══════════════════════════════════════════════════════════════ */

const MOCK_QUESTIONS = [
  { text: "What shape is an Ascaris lumbricoides egg?", options: ["Round", "Barrel", "Oval with mammillated shell", "Crescent"], correct: 2 },
  { text: "Gram-positive cocci in clusters suggest:", options: ["E.coli", "Staphylococcus", "Neisseria", "Proteus"], correct: 1 },
  { text: "Sickle cells are seen in:", options: ["Thalassemia", "Sickle cell disease", "Iron deficiency", "G6PD deficiency"], correct: 1 },
  { text: "Many WBCs in urine suggests:", options: ["Diabetes", "UTI", "Kidney stones", "Dehydration"], correct: 1 },
  { text: "Which crystal is described as 'coffin lid' shaped?", options: ["Calcium oxalate", "Uric acid", "Triple phosphate", "Cystine"], correct: 2 },
  { text: "Plasmodium falciparum rings often appear:", options: ["Single and large", "Multiple and delicate", "Outside RBCs", "As crescents"], correct: 1 },
  { text: "What color do Gram-negative bacteria stain?", options: ["Purple", "Blue", "Pink/Red", "Green"], correct: 2 },
  { text: "A 'shift to the left' in a WBC differential indicates:", options: ["Viral infection", "Increase in immature neutrophils", "Allergic reaction", "Parasitic infection"], correct: 1 },
  { text: "Which objective lens is used with immersion oil?", options: ["10x", "40x", "100x", "400x"], correct: 2 },
  { text: "Which parasite causes malaria?", options: ["Trypanosoma", "Leishmania", "Plasmodium", "Toxoplasma"], correct: 2 }
];

export default function BattlefieldScreen() {
    const { navigate } = useNavigation();
    
    const [phase, setPhase] = useState('matchmaking'); // matchmaking | battle
    const [matchCountdown, setMatchCountdown] = useState(3);
    
    // Battle state
    const [qIndex, setQIndex] = useState(0);
    const [timeLeft, setTimeLeft] = useState(15);
    const [myScore, setMyScore] = useState(0);
    const [oppScore, setOppScore] = useState(0);
    
    const [myAnswer, setMyAnswer] = useState(null);
    const [oppAnswer, setOppAnswer] = useState(null);
    const [myCombo, setMyCombo] = useState(0);
    const [oppCombo, setOppCombo] = useState(0);
    
    // Stats for aftermath
    const [stats, setStats] = useState({
        myCorrect: 0, oppCorrect: 0, 
        myTimes: [], oppTimes: [],
        myMaxCombo: 0, oppMaxCombo: 0,
        myAnswers: [], oppAnswers: [] // array of booleans
    });

    const timerRef = useRef(null);
    const oppTimerRef = useRef(null);
    const nextQTimerRef = useRef(null);

    // Phase 1: Matchmaking
    useEffect(() => {
        if (phase === 'matchmaking') {
            const int = setInterval(() => {
                setMatchCountdown(c => {
                    if (c <= 1) {
                        clearInterval(int);
                        setPhase('battle');
                        startQuestion();
                        return 0;
                    }
                    return c - 1;
                });
            }, 1000);
            return () => clearInterval(int);
        }
    }, [phase]);

    // Timer logic
    const startQuestion = () => {
        setMyAnswer(null);
        setOppAnswer(null);
        setTimeLeft(15);
        
        timerRef.current = setInterval(() => {
            setTimeLeft(t => {
                if (t <= 0.1) {
                    clearInterval(timerRef.current);
                    handleTimeOut();
                    return 0;
                }
                return t - 0.1;
            });
        }, 100);

        // Opponent logic
        const oppDelay = Math.random() * 6000 + 2000; // 2s to 8s
        oppTimerRef.current = setTimeout(() => {
            if (myAnswer === null && timeLeft > 0) {
                // Opponent answers
                const isCorrect = Math.random() < 0.6; // 60% accuracy
                handleOpponentAnswer(isCorrect);
            }
        }, oppDelay);
    };

    const handleOpponentAnswer = (isCorrect) => {
        const q = MOCK_QUESTIONS[qIndex];
        const ansIdx = isCorrect ? q.correct : (q.correct + 1) % 4; // fake wrong
        setOppAnswer(ansIdx);
        
        if (isCorrect) {
            setOppCombo(c => c + 1);
            setStats(s => ({ ...s, oppMaxCombo: Math.max(s.oppMaxCombo, oppCombo + 1) }));
            const pts = 100 * (1 + (oppCombo * 0.5));
            setOppScore(s => s + Math.round(pts));
        } else {
            setOppCombo(0);
        }
        
        setStats(s => ({ 
            ...s, 
            oppCorrect: s.oppCorrect + (isCorrect ? 1 : 0),
            oppTimes: [...s.oppTimes, 15 - timeLeft],
            oppAnswers: [...s.oppAnswers, isCorrect]
        }));
    };

    const handleMyAnswer = (idx) => {
        if (myAnswer !== null || timeLeft <= 0) return;
        
        clearInterval(timerRef.current);
        clearTimeout(oppTimerRef.current);
        
        setMyAnswer(idx);
        const q = MOCK_QUESTIONS[qIndex];
        const isCorrect = idx === q.correct;
        
        const timeTaken = 15 - timeLeft;
        
        if (isCorrect) {
            setMyCombo(c => c + 1);
            setStats(s => ({ ...s, myMaxCombo: Math.max(s.myMaxCombo, myCombo + 1) }));
            const pts = 100 * (1 + (myCombo * 0.5));
            setMyScore(s => s + Math.round(pts));
        } else {
            setMyCombo(0);
        }
        
        setStats(s => ({ 
            ...s, 
            myCorrect: s.myCorrect + (isCorrect ? 1 : 0),
            myTimes: [...s.myTimes, timeTaken],
            myAnswers: [...s.myAnswers, isCorrect]
        }));

        // If opponent hasn't answered, they answer now (simulated)
        if (oppAnswer === null) {
            handleOpponentAnswer(Math.random() < 0.6);
        }

        scheduleNextQuestion();
    };

    const handleTimeOut = () => {
        if (myAnswer === null) {
            setMyCombo(0);
            setStats(s => ({ 
                ...s, 
                myTimes: [...s.myTimes, 15],
                myAnswers: [...s.myAnswers, false]
            }));
            setMyAnswer(-1); // -1 means timeout
        }
        if (oppAnswer === null) {
            handleOpponentAnswer(false);
        }
        scheduleNextQuestion();
    };

    const scheduleNextQuestion = () => {
        nextQTimerRef.current = setTimeout(() => {
            if (qIndex + 1 < MOCK_QUESTIONS.length) {
                setQIndex(i => i + 1);
                startQuestion();
            } else {
                finishBattle();
            }
        }, 2000);
    };

    const finishBattle = () => {
        // Compute final stats and navigate
        const myAvgTime = stats.myTimes.reduce((a,b)=>a+b,0) / Math.max(1, stats.myTimes.length);
        const oppAvgTime = stats.oppTimes.reduce((a,b)=>a+b,0) / Math.max(1, stats.oppTimes.length);
        
        const finalData = {
            myScore, oppScore,
            myCorrect: stats.myCorrect, oppCorrect: stats.oppCorrect,
            myAvgTime, oppAvgTime,
            myMaxCombo: stats.myMaxCombo, oppMaxCombo: stats.oppMaxCombo,
            totalQ: MOCK_QUESTIONS.length,
            history: MOCK_QUESTIONS.map((q, i) => ({
                question: q.text,
                myCorrect: stats.myAnswers[i],
                oppCorrect: stats.oppAnswers[i],
                correctAnswer: q.options[q.correct]
            }))
        };
        
        sessionStorage.setItem('battle_results', JSON.stringify(finalData));
        navigate('battle/results');
    };

    useEffect(() => {
        return () => {
            clearInterval(timerRef.current);
            clearTimeout(oppTimerRef.current);
            clearTimeout(nextQTimerRef.current);
        };
    }, []);

    // ═══════════════════════════════════════════════════════
    //  MATCHMAKING PHASE
    // ═══════════════════════════════════════════════════════
    if (phase === 'matchmaking') {
        return (
          <div style={{
            minHeight:'100vh',
            background:'radial-gradient(ellipse at 50% 40%, rgba(236,72,153,0.15) 0%, transparent 60%), linear-gradient(180deg,#0C060F 0%,#080510 100%)',
            fontFamily:"'Plus Jakarta Sans',sans-serif",
            color:'#E8F4FF',
            display:'flex',flexDirection:'column',
            alignItems:'center',justifyContent:'center',
            position:'relative',overflow:'hidden',
          }}>
            <style>{`
              @keyframes matchPulse { 0%,100%{opacity:0.5;} 50%{opacity:1;} }
            `}</style>

            <motion.p
              animate={{opacity:[0.5,1,0.5]}}
              transition={{duration:2,repeat:Infinity}}
              style={{fontSize:11,fontWeight:700,color:'#EC4899',letterSpacing:4,textTransform:'uppercase',marginBottom:40,fontFamily:"'JetBrains Mono',monospace",textShadow:'0 0 8px rgba(236,72,153,0.8)'}}
            >
              Finding Opponent...
            </motion.p>

            <div style={{display:'flex',alignItems:'center',justifyContent:'center',gap:24,width:'100%',padding:'0 32px'}}>
              {/* You */}
              <motion.div initial={{x:-50,opacity:0}} animate={{x:0,opacity:1}} style={{display:'flex',flexDirection:'column',alignItems:'center',gap:10,flex:1}}>
                <div style={{width:72,height:72,borderRadius:16,background:'rgba(0,212,255,0.12)',border:'2px solid #22D3EE',boxShadow:'0 0 20px rgba(34,211,238,0.4)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:32}}>
                  👤
                </div>
                <span style={{fontSize:11,fontWeight:800,color:'#F0F9FF',letterSpacing:3,textTransform:'uppercase'}}>YOU</span>
              </motion.div>

              {/* VS */}
              <motion.div initial={{scale:0}} animate={{scale:1}} transition={{type:'spring',bounce:0.5}} style={{textAlign:'center'}}>
                <span style={{fontSize:40,fontWeight:900,color:'#fff',fontStyle:'italic',textShadow:'0 0 20px rgba(255,255,255,0.8)'}}>VS</span>
              </motion.div>

              {/* Opponent */}
              <motion.div initial={{x:50,opacity:0}} animate={{x:0,opacity:1}} style={{display:'flex',flexDirection:'column',alignItems:'center',gap:10,flex:1}}>
                <div style={{width:72,height:72,borderRadius:16,background:'rgba(236,72,153,0.12)',border:'2px solid #EC4899',boxShadow:'0 0 20px rgba(236,72,153,0.4)',display:'flex',alignItems:'center',justifyContent:'center',fontSize:32}}>
                  👤
                </div>
                <span style={{fontSize:11,fontWeight:800,color:'#F0F9FF',letterSpacing:3,textTransform:'uppercase'}}>Shadow Knight</span>
              </motion.div>
            </div>

            <div style={{marginTop:48,display:'flex',flexDirection:'column',alignItems:'center',gap:10}}>
              <span style={{padding:'5px 16px',borderRadius:20,background:'rgba(255,255,255,0.06)',border:'1px solid rgba(255,255,255,0.12)',fontSize:10,fontWeight:700,color:'#F0F9FF',letterSpacing:2}}>PARASITOLOGY</span>
              <span style={{padding:'5px 16px',borderRadius:20,background:'rgba(236,72,153,0.1)',border:'1px solid rgba(236,72,153,0.25)',fontSize:10,fontWeight:700,color:'#EC4899',letterSpacing:2}}>1 VS 1 BATTLE</span>
            </div>

            <motion.div
              key={matchCountdown}
              initial={{scale:1.5,opacity:0}}
              animate={{scale:1,opacity:1}}
              exit={{opacity:0}}
              style={{position:'absolute',bottom:80,fontSize:64,fontWeight:900,color:'#fff',textShadow:'0 0 15px rgba(255,255,255,0.8)'}}
            >
              {matchCountdown > 0 ? matchCountdown : 'GO!'}
            </motion.div>
          </div>
        );
    }

    // ═══════════════════════════════════════════════════════
    //  BATTLE PHASE
    // ═══════════════════════════════════════════════════════
    const currentQ = MOCK_QUESTIONS[qIndex];

    return (
      <div style={{
        minHeight:'100vh',
        background:'radial-gradient(ellipse at 50% 15%, rgba(236,72,153,0.12) 0%, transparent 55%), radial-gradient(ellipse at 20% 80%, rgba(139,92,246,0.06) 0%, transparent 40%), linear-gradient(180deg,#0C060F 0%,#080510 100%)',
        fontFamily:"'Plus Jakarta Sans',sans-serif",
        color:'#E8F4FF',
        overflowX:'hidden',
        overflowY:'auto',
        WebkitOverflowScrolling:'touch',
        display:'flex',
        flexDirection:'column',
      }}>

        <style>{`
          @keyframes timerPulse { 0%,100%{opacity:1;} 50%{opacity:0.6;} }
          @keyframes vsGlow { 0%,100%{text-shadow:0 0 20px rgba(236,72,153,0.5);} 50%{text-shadow:0 0 40px rgba(236,72,153,0.9);} }
        `}</style>

        {/* HEADER */}
        <div style={{
          padding:'14px 20px',
          background:'rgba(8,5,16,0.9)',
          backdropFilter:'blur(24px)',
          borderBottom:'1px solid rgba(236,72,153,0.1)',
          display:'flex',alignItems:'center',justifyContent:'space-between',
        }}>
          <div>
            <h1 style={{margin:0,fontSize:15,fontWeight:800,color:'#EC4899',letterSpacing:1,textTransform:'uppercase'}}>
              ⚔️ Battle Arena
            </h1>
            <p style={{margin:0,fontSize:9,color:'rgba(255,255,255,0.3)',fontFamily:"'JetBrains Mono',monospace",letterSpacing:1}}>
              PARASITOLOGY CHALLENGE
            </p>
          </div>
          <div style={{padding:'4px 10px',background:'rgba(236,72,153,0.08)',border:'1px solid rgba(236,72,153,0.2)',borderRadius:20}}>
            <span style={{fontSize:9,fontWeight:700,color:'#EC4899',fontFamily:"'JetBrains Mono',monospace"}}>
              ROUND {qIndex + 1}/{MOCK_QUESTIONS.length}
            </span>
          </div>
        </div>

        <div style={{padding:'16px',display:'flex',flexDirection:'column',gap:14,flex:1}}>

          {/* VS SECTION */}
          <div style={{
            display:'flex',alignItems:'center',gap:12,
            padding:'14px',
            background:'rgba(255,255,255,0.02)',
            border:'1px solid rgba(236,72,153,0.1)',
            borderRadius:16,
          }}>
            {/* PLAYER 1 — You */}
            <div style={{flex:1,textAlign:'center'}}>
              <div style={{
                width:48,height:48,borderRadius:'50%',
                background:'radial-gradient(circle at 35% 35%, rgba(0,212,255,0.9), rgba(0,80,150,0.9))',
                margin:'0 auto 6px',
                display:'flex',alignItems:'center',justifyContent:'center',
                fontSize:20,
                boxShadow:'0 0 20px rgba(0,180,255,0.4)',
              }}>👤</div>
              <p style={{margin:'0 0 2px',fontSize:10,color:'rgba(255,255,255,0.5)',fontWeight:600}}>You</p>
              <p style={{margin:0,fontSize:26,fontWeight:900,color:'#00D4FF',lineHeight:1,fontFamily:"'JetBrains Mono',monospace"}}>
                {myScore}
              </p>
              {myCombo > 1 && <p style={{margin:'4px 0 0',fontSize:9,color:'#F59E0B',fontWeight:700,fontFamily:"'JetBrains Mono',monospace"}}>{myCombo}x COMBO 🔥</p>}
            </div>

            {/* VS */}
            <div style={{
              fontSize:20,fontWeight:900,
              color:'#EC4899',
              animation:'vsGlow 2s ease-in-out infinite',
              letterSpacing:2,
            }}>VS</div>

            {/* PLAYER 2 — Opponent */}
            <div style={{flex:1,textAlign:'center'}}>
              <div style={{
                width:48,height:48,borderRadius:'50%',
                background:'radial-gradient(circle at 35% 35%, rgba(236,72,153,0.9), rgba(120,20,80,0.9))',
                margin:'0 auto 6px',
                display:'flex',alignItems:'center',justifyContent:'center',
                fontSize:20,
                boxShadow:'0 0 20px rgba(236,72,153,0.4)',
              }}>👤</div>
              <p style={{margin:'0 0 2px',fontSize:10,color:'rgba(255,255,255,0.5)',fontWeight:600}}>
                Shadow Knight
              </p>
              <p style={{margin:0,fontSize:26,fontWeight:900,color:'#EC4899',lineHeight:1,fontFamily:"'JetBrains Mono',monospace"}}>
                {oppScore}
              </p>
              {oppCombo > 1 && <p style={{margin:'4px 0 0',fontSize:9,color:'#F59E0B',fontWeight:700,fontFamily:"'JetBrains Mono',monospace"}}>🔥 {oppCombo}x COMBO</p>}
            </div>
          </div>

          {/* TIMER */}
          <div style={{textAlign:'center'}}>
            <div style={{
              display:'inline-flex',alignItems:'center',gap:8,
              padding:'6px 20px',
              background:'rgba(245,158,11,0.08)',
              border:'1px solid rgba(245,158,11,0.2)',
              borderRadius:20,
              animation: timeLeft <= 5 ? 'timerPulse 0.5s ease-in-out infinite' : 'none',
            }}>
              <span style={{fontSize:12}}>⏱</span>
              <span style={{
                fontSize:18,fontWeight:900,
                color: timeLeft <= 5 ? '#EF4444' : '#F59E0B',
                fontFamily:"'JetBrains Mono',monospace",
                letterSpacing:2,
              }}>
                {String(Math.ceil(timeLeft)).padStart(2,'0')}s
              </span>
            </div>
          </div>

          {/* TIMER BAR */}
          <div style={{width:'100%',height:4,background:'rgba(255,255,255,0.06)',borderRadius:2,overflow:'hidden'}}>
            <div style={{height:'100%',background:'linear-gradient(90deg,#22D3EE,#F59E0B,#EF4444)',width:`${(timeLeft/15)*100}%`,transition:'width 0.1s linear',borderRadius:2}} />
          </div>

          {/* QUESTION CARD */}
          <AnimatePresence mode="wait">
            <motion.div
              key={qIndex}
              initial={{opacity:0,y:16,scale:0.97}}
              animate={{opacity:1,y:0,scale:1}}
              exit={{opacity:0,y:-16,scale:0.97}}
              transition={{duration:0.25}}
              style={{
                background:'rgba(255,255,255,0.03)',
                border:'1px solid rgba(236,72,153,0.15)',
                borderRadius:16,
                padding:'16px',
              }}
            >
              <p style={{margin:'0 0 14px',fontSize:13,fontWeight:700,color:'#F0F9FF',lineHeight:1.5}}>
                {currentQ.text}
              </p>

              <div style={{display:'flex',flexDirection:'column',gap:8}}>
                {currentQ.options.map((opt, i) => {
                  let st = 'idle';
                  if (myAnswer !== null) {
                    if (i === currentQ.correct) st = 'correct';
                    else if (i === myAnswer) st = 'wrong';
                    else st = 'dim';
                  }
                  return (
                    <motion.button
                      key={i}
                      whileTap={{scale:0.98}}
                      onClick={() => handleMyAnswer(i)}
                      disabled={myAnswer !== null}
                      style={{
                        width:'100%',textAlign:'left',
                        padding:'10px 14px',
                        borderRadius:10,
                        cursor: myAnswer !== null ? 'default' : 'pointer',
                        fontSize:12,fontWeight:600,
                        fontFamily:"'Plus Jakarta Sans',sans-serif",
                        display:'flex',alignItems:'center',gap:10,
                        background: st === 'correct' ? 'rgba(16,185,129,0.15)' :
                                    st === 'wrong'   ? 'rgba(239,68,68,0.12)' :
                                                       'rgba(255,255,255,0.04)',
                        border: st === 'correct' ? '1px solid rgba(16,185,129,0.35)' :
                                st === 'wrong'   ? '1px solid rgba(239,68,68,0.3)' :
                                                   '1px solid rgba(255,255,255,0.07)',
                        color: st === 'correct' ? '#34D399' :
                               st === 'wrong'   ? '#FCA5A5' :
                               st === 'dim'     ? 'rgba(255,255,255,0.2)' :
                                                  'rgba(255,255,255,0.6)',
                        transition:'all 0.15s',
                      }}
                    >
                      <span style={{
                        width:22,height:22,borderRadius:6,
                        display:'flex',alignItems:'center',justifyContent:'center',
                        fontSize:10,fontWeight:800,flexShrink:0,
                        background: st === 'correct' ? 'rgba(16,185,129,0.2)' :
                                    st === 'wrong'   ? 'rgba(239,68,68,0.2)' :
                                                       'rgba(255,255,255,0.06)',
                        color: st === 'correct' ? '#34D399' : st === 'wrong' ? '#FCA5A5' : 'rgba(255,255,255,0.4)',
                      }}>
                        {st === 'correct' ? '✓' : st === 'wrong' ? '✗' : String.fromCharCode(65+i)}
                      </span>
                      <span style={{flex:1}}>{opt}</span>
                      {/* Opponent pick indicator */}
                      {oppAnswer === i && myAnswer !== null && (
                        <span style={{width:20,height:20,borderRadius:'50%',background:'rgba(236,72,153,0.15)',border:'1px solid #EC4899',display:'flex',alignItems:'center',justifyContent:'center',fontSize:10,flexShrink:0}}>👤</span>
                      )}
                    </motion.button>
                  );
                })}
              </div>
            </motion.div>
          </AnimatePresence>

          {/* STATUS FLOAT */}
          {myAnswer !== null && myAnswer !== -1 && (
            <motion.div initial={{opacity:0,y:20}} animate={{opacity:1,y:0}}
              style={{textAlign:'center',padding:'10px 20px',borderRadius:20,background:'rgba(0,0,0,0.6)',border:'1px solid rgba(255,255,255,0.08)',margin:'0 auto'}}>
              <span style={{fontSize:12,fontWeight:700,color:'#F0F9FF',letterSpacing:2,textTransform:'uppercase'}}>
                {myAnswer === currentQ.correct ? '🎯 Target Eliminated!' : '❌ Missed!'}
              </span>
            </motion.div>
          )}

          {/* PROGRESS DOTS */}
          <div style={{display:'flex',justifyContent:'center',gap:5,marginTop:'auto',paddingTop:8}}>
            {Array.from({length:MOCK_QUESTIONS.length}).map((_,i) => (
              <div key={i} style={{
                width: i === qIndex ? 16 : 6,
                height:6,borderRadius:3,
                background: i < qIndex ? '#EC4899' :
                            i === qIndex ? '#F9A8D4' :
                            'rgba(255,255,255,0.1)',
                transition:'all 0.3s',
              }}/>
            ))}
          </div>

        </div>
      </div>
    );
}
