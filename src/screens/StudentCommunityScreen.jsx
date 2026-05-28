import { useState } from 'react';
import { createPortal } from 'react-dom';
import { Swords, Microscope, CheckCircle2, XCircle, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigation } from '../context/NavigationContext';
import { useAppState } from '../context/AppStateContext';
import {
    INITIAL_STUDY_GROUPS,
    FeedTab,
    LeaderboardTab,
    WarMapTab,
    ChatRoom,
    BattleAlert,
} from '../components/community';

/* ═══════════════════════════════════════════════════════════════
   STUDENT COMMUNITY — BioForge Dark Design Language
   Font: Plus Jakarta Sans | Primary: #3B82F6 (Blue)
   ═══════════════════════════════════════════════════════════════ */

const TABS = [
  { id:'feed', label:'Feed', icon:'📰' },
  { id:'chat', label:'Chat', icon:'💬' },
  { id:'leaderboard', label:'Top', icon:'🏆' },
  { id:'challenges', label:'Battles', icon:'⚔️' },
  { id:'warmap', label:'War', icon:'🗺️' },
  { id:'quiz', label:'Quiz', icon:'🧪' },
];

// ── Chat rooms mock ──
const CHAT_ROOMS = [
    { id: 'general', name: 'General Discussion', icon: '💬', lastMsg: 'Has anyone seen the new module?', unread: 3, color: '#22D3EE' },
    { id: 'hema', name: 'Hematology Help', icon: '🩸', lastMsg: 'Can someone explain reticulocyte count?', unread: 7, color: '#EF4444' },
    { id: 'para', name: 'Parasitology Corner', icon: '🔬', lastMsg: 'Check this Ascaris egg photo...', unread: 0, color: '#22C55E' },
    { id: 'micro', name: 'Microbiology Lab', icon: '🧫', lastMsg: 'Gram stain results discussion', unread: 2, color: '#A855F7' },
    { id: 'exam', name: 'Exam Prep', icon: '📝', lastMsg: 'Final exam topics leaked!', unread: 12, color: '#F59E0B' },
];

// ── Challenges mock ──
const MOCK_CHALLENGES = [
    { id: 1, opponent: 'Ahmad M.', topic: 'Hematology', status: 'live', score: '3-2', mode: '1v1' },
    { id: 2, opponent: 'Team Alpha', topic: 'Microbiology', status: 'pending', score: null, mode: 'team' },
];
const PAST_RESULTS = [
    { opponent: 'Fatima Z.', topic: 'Parasitology', won: true, score: '5-3' },
    { opponent: 'Dr. Nora', topic: 'Hematology', won: false, score: '2-5' },
    { opponent: 'Team Beta', topic: 'Urinalysis', won: true, score: '8-4' },
];

// ── Image Quiz mock ──
const QUIZ_IMAGES = [
    { id: 1, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Sickle_cell_anemia.jpg/1280px-Sickle_cell_anemia.jpg', question: 'What type of cells are prominently visible?', options: ['Sickle cells', 'Target cells', 'Spherocytes', 'Schistocytes'], correct: 0, explanation: 'The crescent/sickle-shaped RBCs are characteristic of Sickle Cell Disease (HbS).' },
    { id: 2, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2b/Gram_stain_01.jpg/640px-Gram_stain_01.jpg', question: 'What does this Gram stain show?', options: ['Gram-positive cocci in clusters', 'Gram-negative rods', 'Gram-positive rods', 'Acid-fast bacilli'], correct: 0, explanation: 'Purple/violet cocci in clusters are characteristic of Staphylococcus species (Gram-positive).' },
    { id: 3, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Ascaris_lumbricoides_egg.jpg/640px-Ascaris_lumbricoides_egg.jpg', question: 'Identify this parasitic structure:', options: ['Ascaris lumbricoides egg', 'Hookworm egg', 'Trichuris trichiura egg', 'Enterobius vermicularis egg'], correct: 0, explanation: 'The mammillated (bumpy) outer coat is characteristic of fertilized Ascaris lumbricoides eggs.' },
    { id: 4, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Neutrophils.jpg/640px-Neutrophils.jpg', question: 'What is the predominant WBC type here?', options: ['Neutrophil', 'Lymphocyte', 'Monocyte', 'Eosinophil'], correct: 0, explanation: 'Multi-lobed nucleus (3-5 lobes) and pale pink granules are characteristic of neutrophils.' },
    { id: 5, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/WBC_urine_microscopy.jpg/640px-WBC_urine_microscopy.jpg', question: 'What does this urine sediment show?', options: ['White blood cells (pyuria)', 'Red blood cells', 'Epithelial cells', 'Yeast cells'], correct: 0, explanation: 'Multiple WBCs in urine sediment (pyuria) suggest urinary tract infection.' },
];

export default function StudentCommunityScreen({ onNavigate }) {
    const { navigate } = useNavigation();
    const { addXp, setToastEvent } = useAppState();
    const [activeTab, setActiveTab] = useState('feed');
    const [groups, setGroups] = useState(INITIAL_STUDY_GROUPS);
    const [activeChat, setActiveChat] = useState(null);
    const [showBattleAlert, setShowBattleAlert] = useState(false);

    // Image quiz state
    const [quizIndex, setQuizIndex] = useState(0);
    const [quizAnswer, setQuizAnswer] = useState(null);
    const [quizScore, setQuizScore] = useState(0);
    const [quizFinished, setQuizFinished] = useState(false);

    const resetQuiz = () => { setQuizIndex(0); setQuizAnswer(null); setQuizScore(0); setQuizFinished(false); };
    const currentQuiz = QUIZ_IMAGES[quizIndex];

    const handleQuizPick = (idx) => {
        if (quizAnswer !== null) return;
        setQuizAnswer(idx);
        
        let isCorrect = idx === currentQuiz.correct;
        let nextScore = quizScore;
        if (isCorrect) {
            nextScore = quizScore + 1;
            setQuizScore(nextScore);
        }
        
        setTimeout(() => {
            if (quizIndex + 1 < QUIZ_IMAGES.length) { 
                setQuizIndex(i => i + 1); 
                setQuizAnswer(null); 
            } else { 
                const earned = nextScore * 50;
                if (earned > 0) {
                    addXp(earned);
                    setToastEvent({ message: `🏆 Quiz complete! Earned +${earned} XP!`, time: Date.now() });
                }
                setQuizFinished(true); 
            }
        }, 1800);
    };

    return (
      <>
        <div style={{
          minHeight:'100vh',
          background:'radial-gradient(ellipse at 60% 10%, rgba(59,130,246,0.08) 0%, transparent 50%), linear-gradient(180deg,#070C1A 0%,#050810 100%)',
          fontFamily:"'Plus Jakarta Sans',sans-serif",
          color:'#E8F4FF',
          overflowX:'hidden',
          overflowY:'auto',
          WebkitOverflowScrolling:'touch',
          display:'flex',
          flexDirection:'column',
        }}>


          {/* ═══ STICKY HEADER ═══ */}
          <div style={{
            position:'sticky',top:0,zIndex:20,
            padding:'14px 20px 10px',
            background:'rgba(5,8,16,0.9)',
            backdropFilter:'blur(24px)',
            WebkitBackdropFilter:'blur(24px)',
            borderBottom:'1px solid rgba(59,130,246,0.1)',
          }}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:10}}>
              <div style={{display:'flex',alignItems:'center',gap:12}}>
                <button
                  onClick={() => onNavigate ? onNavigate('dashboard') : navigate('dashboard')}
                  style={{
                    width:36,height:36,borderRadius:10,
                    background:'rgba(255,255,255,0.04)',
                    border:'1px solid rgba(255,255,255,0.08)',
                    display:'flex',alignItems:'center',justifyContent:'center',
                    cursor:'pointer',color:'rgba(255,255,255,0.6)',
                    fontSize:16,flexShrink:0,
                  }}
                >←</button>
                <div>
                  <h1 style={{margin:0,fontSize:17,fontWeight:800,color:'#F0F9FF',letterSpacing:-0.3}}>
                    👥 Community
                  </h1>
                  <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)',letterSpacing:1,fontFamily:"'JetBrains Mono',monospace"}}>
                    STUDENT NETWORK
                  </p>
                </div>
              </div>
              <div style={{display:'flex',gap:6}}>
                <div style={{padding:'4px 10px',background:'rgba(236,72,153,0.08)',border:'1px solid rgba(236,72,153,0.2)',borderRadius:20}}>
                  <span style={{fontSize:9,fontWeight:700,color:'#EC4899',fontFamily:"'JetBrains Mono',monospace"}}>⚔️ BATTLES</span>
                </div>
                <div style={{padding:'4px 10px',background:'rgba(59,130,246,0.08)',border:'1px solid rgba(59,130,246,0.2)',borderRadius:20}}>
                  <span style={{fontSize:9,fontWeight:700,color:'#60A5FA',fontFamily:"'JetBrains Mono',monospace"}}>ONLINE</span>
                </div>
              </div>
            </div>

            {/* TABS */}
            <div style={{display:'flex',gap:4,padding:'3px',background:'rgba(255,255,255,0.03)',border:'1px solid rgba(255,255,255,0.06)',borderRadius:10}}>
              {TABS.map(tab => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    style={{
                      flex:1,
                      padding:'6px 4px',
                      borderRadius:7,
                      border:'none',
                      cursor:'pointer',
                      fontSize:9,
                      fontWeight:700,
                      fontFamily:"'Plus Jakarta Sans',sans-serif",
                      letterSpacing:0.3,
                      display:'flex',
                      flexDirection:'column',
                      alignItems:'center',
                      gap:2,
                      background:isActive ? 'rgba(59,130,246,0.18)' : 'transparent',
                      color:isActive ? '#60A5FA' : 'rgba(255,255,255,0.25)',
                      borderTop:isActive ? '1px solid rgba(59,130,246,0.3)' : '1px solid transparent',
                      transition:'all 0.15s',
                    }}
                  >
                    <span style={{fontSize:12,fontFamily:'Apple Color Emoji,Segoe UI Emoji,sans-serif'}}>{tab.icon}</span>
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* ═══ TAB CONTENT ═══ */}
          <div style={{flex:1,overflow:'auto',WebkitOverflowScrolling:'touch'}}>
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{opacity:0,y:8}}
                animate={{opacity:1,y:0}}
                exit={{opacity:0,y:-8}}
                transition={{duration:0.2}}
                style={{minHeight:'100%',overflowY:'auto',paddingBottom:90}}
              >

                {/* ═══ FEED ═══ */}
                {activeTab === 'feed' && (
                  <div style={{padding:'8px 16px'}}>
                    <FeedTab groups={groups} setGroups={setGroups} setActiveChat={setActiveChat} />
                  </div>
                )}

                {/* ═══ CHAT ═══ */}
                {activeTab === 'chat' && (
                  <div style={{padding:'12px 16px',display:'flex',flexDirection:'column',gap:8}}>
                    {CHAT_ROOMS.map(room => (
                      <button key={room.id} onClick={() => setActiveChat({ id: room.id, name: room.name, color: room.color })}
                        style={{
                          width:'100%',display:'flex',alignItems:'center',gap:12,padding:'12px 14px',
                          borderRadius:14,background:'rgba(255,255,255,0.025)',border:'1px solid rgba(255,255,255,0.06)',
                          cursor:'pointer',textAlign:'left',transition:'background 0.15s',
                        }}
                      >
                        <div style={{width:40,height:40,borderRadius:10,display:'flex',alignItems:'center',justifyContent:'center',fontSize:18,flexShrink:0,
                          background:`${room.color}12`,border:`1px solid ${room.color}25`}}>
                          {room.icon}
                        </div>
                        <div style={{flex:1,minWidth:0}}>
                          <p style={{margin:0,fontSize:13,fontWeight:700,color:'#F0F9FF',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{room.name}</p>
                          <p style={{margin:'2px 0 0',fontSize:11,color:'rgba(255,255,255,0.25)',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{room.lastMsg}</p>
                        </div>
                        <div style={{display:'flex',flexDirection:'column',alignItems:'flex-end',gap:4,flexShrink:0}}>
                          {room.unread > 0 && (
                            <span style={{padding:'2px 7px',borderRadius:20,fontSize:10,fontWeight:700,color:'#fff',background:room.color}}>{room.unread}</span>
                          )}
                          <ChevronRight size={14} style={{color:'rgba(255,255,255,0.15)'}} />
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {/* ═══ LEADERBOARD ═══ */}
                {activeTab === 'leaderboard' && (
                  <div style={{padding:'4px'}}><LeaderboardTab /></div>
                )}

                {/* ═══ CHALLENGES ═══ */}
                {activeTab === 'challenges' && (
                  <div style={{padding:'12px 16px',display:'flex',flexDirection:'column',gap:16}}>
                    {/* Active */}
                    <div>
                      <h3 style={{margin:'0 0 10px',fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',textTransform:'uppercase',letterSpacing:2}}>◆ Active Challenges</h3>
                      {MOCK_CHALLENGES.map(c => (
                        <div key={c.id} style={{display:'flex',alignItems:'center',gap:12,padding:'12px 14px',borderRadius:14,background:'rgba(255,255,255,0.025)',border:'1px solid rgba(255,255,255,0.06)',marginBottom:8}}>
                          <div style={{width:38,height:38,borderRadius:10,display:'flex',alignItems:'center',justifyContent:'center',fontSize:16,flexShrink:0,
                            background:c.mode==='1v1'?'rgba(239,68,68,0.08)':'rgba(168,85,247,0.08)',
                            border:c.mode==='1v1'?'1px solid rgba(239,68,68,0.2)':'1px solid rgba(168,85,247,0.2)'}}>
                            {c.mode === '1v1' ? '⚔️' : '🏴'}
                          </div>
                          <div style={{flex:1,minWidth:0}}>
                            <p style={{margin:0,fontSize:13,fontWeight:700,color:'#F0F9FF'}}>{c.opponent}</p>
                            <p style={{margin:'2px 0 0',fontSize:10,color:'rgba(255,255,255,0.25)'}}>{c.topic} • {c.mode.toUpperCase()}</p>
                          </div>
                          <div style={{flexShrink:0}}>
                            {c.status === 'live' ? (
                              <span style={{padding:'3px 8px',borderRadius:6,fontSize:9,fontWeight:700,background:'rgba(239,68,68,0.12)',color:'#F87171',border:'1px solid rgba(239,68,68,0.2)',fontFamily:"'JetBrains Mono',monospace"}}>LIVE {c.score}</span>
                            ) : (
                              <span style={{padding:'3px 8px',borderRadius:6,fontSize:9,fontWeight:700,background:'rgba(245,158,11,0.12)',color:'#FBBF24',border:'1px solid rgba(245,158,11,0.2)',fontFamily:"'JetBrains Mono',monospace"}}>PENDING</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Create challenge */}
                    <button onClick={() => navigate('battle')}
                      style={{width:'100%',padding:'14px 0',borderRadius:14,border:'1px solid rgba(239,68,68,0.2)',background:'rgba(239,68,68,0.06)',
                        color:'#F87171',fontSize:12,fontWeight:700,letterSpacing:1,cursor:'pointer',display:'flex',alignItems:'center',justifyContent:'center',gap:8}}>
                      <Swords size={16} /> CREATE CHALLENGE
                    </button>

                    {/* Past results */}
                    <div>
                      <h3 style={{margin:'0 0 10px',fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',textTransform:'uppercase',letterSpacing:2}}>◆ Past Results</h3>
                      {PAST_RESULTS.map((r, i) => (
                        <div key={i} style={{display:'flex',alignItems:'center',gap:12,padding:'10px 14px',borderRadius:12,background:'rgba(255,255,255,0.02)',border:'1px solid rgba(255,255,255,0.05)',marginBottom:6}}>
                          <div style={{width:32,height:32,borderRadius:8,display:'flex',alignItems:'center',justifyContent:'center',fontSize:11,fontWeight:800,flexShrink:0,
                            background:r.won?'rgba(16,185,129,0.12)':'rgba(239,68,68,0.12)',
                            color:r.won?'#10B981':'#EF4444',
                            border:r.won?'1px solid rgba(16,185,129,0.25)':'1px solid rgba(239,68,68,0.25)'}}>
                            {r.won ? 'W' : 'L'}
                          </div>
                          <div style={{flex:1}}>
                            <p style={{margin:0,fontSize:12,fontWeight:600,color:'#F0F9FF'}}>{r.opponent}</p>
                            <p style={{margin:'1px 0 0',fontSize:10,color:'rgba(255,255,255,0.25)'}}>{r.topic}</p>
                          </div>
                          <span style={{fontSize:12,fontWeight:700,color:'rgba(255,255,255,0.3)',fontFamily:"'JetBrains Mono',monospace"}}>{r.score}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* ═══ WAR MAP ═══ */}
                {activeTab === 'warmap' && (
                  <div style={{padding:'4px'}}><WarMapTab /></div>
                )}

                {/* ═══ IMAGE QUIZ ═══ */}
                {activeTab === 'quiz' && (
                  <div style={{padding:'12px 16px',display:'flex',flexDirection:'column',gap:14}}>
                    {quizFinished ? (
                      <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:16,paddingTop:40,textAlign:'center'}}>
                        <Microscope size={48} style={{color:'#60A5FA'}} />
                        <div style={{fontSize:36,fontWeight:900,background:'linear-gradient(135deg,#3B82F6,#22D3EE)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent'}}>
                          {quizScore}/{QUIZ_IMAGES.length}
                        </div>
                        <h3 style={{margin:0,fontSize:16,fontWeight:800,color:'#F0F9FF'}}>{quizScore >= QUIZ_IMAGES.length / 2 ? 'Great Eye!' : 'Keep Practicing!'}</h3>
                        <p style={{margin:0,fontSize:12,color:'#10B981',fontWeight:700,fontFamily:"'JetBrains Mono',monospace"}}>+{(quizScore * 50).toLocaleString()} XP AWARDED</p>
                        <button onClick={resetQuiz}
                          style={{padding:'10px 24px',borderRadius:12,fontSize:11,fontWeight:700,letterSpacing:1,
                            background:'rgba(59,130,246,0.08)',border:'1px solid rgba(59,130,246,0.2)',color:'#60A5FA',cursor:'pointer'}}>
                          TRY AGAIN
                        </button>
                      </div>
                    ) : currentQuiz && (
                      <>
                        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>
                          <h3 style={{margin:0,fontSize:10,fontWeight:700,color:'#60A5FA',textTransform:'uppercase',letterSpacing:1,display:'flex',alignItems:'center',gap:6}}>
                            <Microscope size={14} /> Image Identification
                          </h3>
                          <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',fontFamily:"'JetBrains Mono',monospace"}}>{quizIndex + 1}/{QUIZ_IMAGES.length} • Score: {quizScore}</span>
                        </div>

                        {/* Image */}
                        <div style={{borderRadius:16,overflow:'hidden',border:'1px solid rgba(255,255,255,0.08)',background:'rgba(0,0,0,0.3)',aspectRatio:'16/9'}}>
                          <img src={currentQuiz.url} alt="Quiz" style={{width:'100%',height:'100%',objectFit:'cover'}} onError={(e) => { e.target.style.display = 'none'; }} />
                        </div>

                        {/* Question */}
                        <p style={{margin:0,fontSize:13,fontWeight:700,color:'#F0F9FF'}}>{currentQuiz.question}</p>

                        {/* Options */}
                        <div style={{display:'flex',flexDirection:'column',gap:8}}>
                          {currentQuiz.options.map((opt, i) => {
                            let st = 'idle';
                            if (quizAnswer !== null) {
                              if (i === currentQuiz.correct) st = 'correct';
                              else if (i === quizAnswer) st = 'wrong';
                              else st = 'dim';
                            }
                            const c = {
                              idle: { bg:'rgba(255,255,255,0.025)', border:'rgba(255,255,255,0.08)', text:'rgba(255,255,255,0.7)' },
                              correct: { bg:'rgba(16,185,129,0.1)', border:'rgba(16,185,129,0.4)', text:'#10B981' },
                              wrong: { bg:'rgba(239,68,68,0.1)', border:'rgba(239,68,68,0.4)', text:'#EF4444' },
                              dim: { bg:'transparent', border:'rgba(255,255,255,0.03)', text:'rgba(255,255,255,0.15)' },
                            }[st];
                            return (
                              <button key={i} onClick={() => handleQuizPick(i)} disabled={quizAnswer !== null}
                                style={{width:'100%',display:'flex',alignItems:'center',gap:10,padding:'10px 12px',borderRadius:12,
                                  background:c.bg,border:`1px solid ${c.border}`,cursor:quizAnswer!==null?'default':'pointer',transition:'all 0.15s'}}>
                                <div style={{width:28,height:28,borderRadius:8,display:'flex',alignItems:'center',justifyContent:'center',fontSize:11,fontWeight:700,flexShrink:0,
                                  background:c.border,color:c.text}}>
                                  {st === 'correct' ? <CheckCircle2 size={14} /> : st === 'wrong' ? <XCircle size={14} /> : String.fromCharCode(65 + i)}
                                </div>
                                <span style={{flex:1,fontSize:12,textAlign:'left',color:c.text}}>{opt}</span>
                              </button>
                            );
                          })}
                        </div>

                        {/* Explanation */}
                        {quizAnswer !== null && (
                          <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}}
                            style={{padding:'12px 14px',borderRadius:12,background:'rgba(59,130,246,0.04)',border:'1px solid rgba(59,130,246,0.12)'}}>
                            <p style={{margin:0,fontSize:11,color:'#93C5FD',lineHeight:1.6}}>{currentQuiz.explanation}</p>
                          </motion.div>
                        )}
                      </>
                    )}
                  </div>
                )}

              </motion.div>
            </AnimatePresence>
          </div>

        </div>

        {/* Chat portal */}
        {activeChat && typeof window !== 'undefined' && createPortal(
            <ChatRoom activeChat={activeChat} groups={groups} setGroups={setGroups} setActiveChat={setActiveChat} onClose={() => setActiveChat(null)} />,
            document.body
        )}

        {/* Battle alert portal */}
        {showBattleAlert && typeof window !== 'undefined' && createPortal(
            <BattleAlert showBattleAlert={showBattleAlert} setShowBattleAlert={setShowBattleAlert} onNavigate={(v) => navigate(v)} />,
            document.body
        )}
      </>
    );
}
