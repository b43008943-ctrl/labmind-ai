import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppState } from '../context/AppStateContext';
import { api } from '../services/apiClient';
import { useNavigation } from '../context/NavigationContext';

/* ═══════════════════════════════════════════════════════════════
   ARMORY STORE — BioForge Dark Design Language
   Font: Plus Jakarta Sans | Primary: #F59E0B (Amber/Gold)
   ═══════════════════════════════════════════════════════════════ */

const CATEGORIES = ['All', 'Avatars', 'Titles', 'Frames', 'Badges', 'Lab Coats'];

const RARITY = {
    Common:    { color: '#94A3B8', bg: 'rgba(148,163,184,0.08)', border: 'rgba(148,163,184,0.18)' },
    Rare:      { color: '#3B82F6', bg: 'rgba(59,130,246,0.08)',  border: 'rgba(59,130,246,0.22)' },
    Epic:      { color: '#A855F7', bg: 'rgba(168,85,247,0.08)',  border: 'rgba(168,85,247,0.22)' },
    Legendary: { color: '#F59E0B', bg: 'rgba(245,158,11,0.08)',  border: 'rgba(245,158,11,0.22)' },
};

const ITEMS = [
    // Avatars
    { id: 'a1', name: 'Lab Scientist',      cat: 'Avatars',   rarity: 'Common',    price: 200,  icon: '🥼', owned: false },
    { id: 'a2', name: 'Microscope Master',   cat: 'Avatars',   rarity: 'Rare',      price: 500,  icon: '🔬', owned: false },
    { id: 'a3', name: 'Cell Hunter',         cat: 'Avatars',   rarity: 'Epic',      price: 1000, icon: '🧬', owned: true },
    { id: 'a4', name: 'DNA Decoder',         cat: 'Avatars',   rarity: 'Legendary', price: 2500, icon: '🧪', owned: false },
    // Titles
    { id: 't1', name: 'Junior Analyst',      cat: 'Titles',    rarity: 'Common',    price: 100,  icon: '📋', owned: true },
    { id: 't2', name: 'Senior Technician',   cat: 'Titles',    rarity: 'Rare',      price: 400,  icon: '🏷️', owned: false },
    { id: 't3', name: 'Chief Pathologist',   cat: 'Titles',    rarity: 'Epic',      price: 800,  icon: '🎖️', owned: false },
    { id: 't4', name: 'Laboratory Director', cat: 'Titles',    rarity: 'Legendary', price: 2000, icon: '👑', owned: false },
    // Frames
    { id: 'f1', name: 'Bronze Frame',        cat: 'Frames',    rarity: 'Common',    price: 150,  icon: '🟤', owned: true },
    { id: 'f2', name: 'Silver Frame',        cat: 'Frames',    rarity: 'Rare',      price: 350,  icon: '⚪', owned: false },
    { id: 'f3', name: 'Gold Frame',          cat: 'Frames',    rarity: 'Epic',      price: 700,  icon: '🟡', owned: false },
    { id: 'f4', name: 'Diamond Frame',       cat: 'Frames',    rarity: 'Legendary', price: 1500, icon: '💎', owned: false },
    // Badges
    { id: 'b1', name: 'First Analysis',      cat: 'Badges',    rarity: 'Common',    price: 50,   icon: '🏅', owned: true },
    { id: 'b2', name: '100 Scans Club',      cat: 'Badges',    rarity: 'Rare',      price: 300,  icon: '💯', owned: false },
    { id: 'b3', name: 'Perfect Score',       cat: 'Badges',    rarity: 'Epic',      price: 600,  icon: '⭐', owned: false },
    { id: 'b4', name: 'AI Master',           cat: 'Badges',    rarity: 'Legendary', price: 1200, icon: '🤖', owned: false },
    // Lab Coats
    { id: 'l1', name: 'Standard White',      cat: 'Lab Coats', rarity: 'Common',    price: 100,  icon: '🧥', owned: true },
    { id: 'l2', name: 'Blue Scrubs',         cat: 'Lab Coats', rarity: 'Rare',      price: 450,  icon: '👔', owned: false },
    { id: 'l3', name: 'Neon Lab Coat',       cat: 'Lab Coats', rarity: 'Epic',      price: 900,  icon: '✨', owned: false },
    { id: 'l4', name: 'Holographic Coat',    cat: 'Lab Coats', rarity: 'Legendary', price: 3000, icon: '🌈', owned: false },
];

export default function ArmoryStoreScreen() {
    const { goBack } = useNavigation();
    const [activeCat, setActiveCat] = useState('All');
    const { xp, ownedItems, equipped, equipItem, buyItem } = useAppState();
    const [confirmItem, setConfirmItem] = useState(null);
    const [purchaseSuccess, setPurchaseSuccess] = useState(null);

    const getCategoryKey = (cat) => {
        if (cat === 'Avatars') return 'avatar';
        if (cat === 'Titles') return 'title';
        if (cat === 'Frames') return 'frame';
        if (cat === 'Badges') return 'badge';
        if (cat === 'Lab Coats') return 'coat';
        return cat.toLowerCase();
    };

    const handleEquip = async (item) => {
        const catKey = getCategoryKey(item.cat);
        equipItem({ ...item, category: catKey });
        if (catKey === 'title') {
            try {
                await api.auth.updateProfile({ rank_title: item.name });
            } catch (err) {
                console.error('Failed to update title on backend profile:', err);
            }
        }
    };

    const filtered = activeCat === 'All' ? ITEMS : ITEMS.filter(i => i.cat === activeCat);

    const handleBuy = (item) => {
        const isOwned = item.owned || ownedItems.includes(item.id);
        if (isOwned || xp < item.price) return;
        setConfirmItem(item);
    };

    const confirmPurchase = () => {
        if (!confirmItem) return;
        buyItem(confirmItem, confirmItem.price);
        setPurchaseSuccess(confirmItem.name);
        setConfirmItem(null);
        setTimeout(() => setPurchaseSuccess(null), 2000);
    };

    return (
      <div style={{
        minHeight:'100vh',
        background:'radial-gradient(ellipse at 25% 20%, rgba(245,158,11,0.07) 0%, transparent 50%), linear-gradient(180deg,#0C0A05 0%,#080700 100%)',
        fontFamily:"'Plus Jakarta Sans',sans-serif",
        color:'#E8F4FF',
        overflowX:'hidden',
        overflowY:'auto',
        WebkitOverflowScrolling:'touch',
      }}>


        {/* ═══ HEADER ═══ */}
        <div style={{
          position:'sticky',top:0,zIndex:20,
          padding:'14px 20px',
          background:'rgba(8,7,0,0.9)',
          backdropFilter:'blur(24px)',
          WebkitBackdropFilter:'blur(24px)',
          borderBottom:'1px solid rgba(245,158,11,0.1)',
          display:'flex',alignItems:'center',justifyContent:'space-between',
        }}>
          <div style={{display:'flex',alignItems:'center',gap:12}}>
            <button onClick={goBack}
              style={{width:36,height:36,borderRadius:10,background:'rgba(245,158,11,0.08)',border:'1px solid rgba(245,158,11,0.2)',display:'flex',alignItems:'center',justifyContent:'center',cursor:'pointer',color:'#FBBF24',fontSize:16,flexShrink:0}}>
              ←
            </button>
            <div>
              <h1 style={{margin:0,fontSize:17,fontWeight:800,color:'#F59E0B',letterSpacing:-0.3}}>
                🏪 Armory Store
              </h1>
              <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.3)',letterSpacing:1,fontFamily:"'JetBrains Mono',monospace"}}>
                SPEND YOUR BATTLE XP
              </p>
            </div>
          </div>

          {/* XP BALANCE */}
          <div style={{
            display:'flex',alignItems:'center',gap:7,
            padding:'7px 14px',
            background:'rgba(245,158,11,0.08)',
            border:'1px solid rgba(245,158,11,0.2)',
            borderRadius:20,
          }}>
            <span style={{fontSize:14,fontFamily:'Apple Color Emoji,Segoe UI Emoji,sans-serif'}}>🪙</span>
            <span style={{fontSize:15,fontWeight:800,color:'#F59E0B',fontFamily:"'JetBrains Mono',monospace"}}>
              {xp.toLocaleString()}
            </span>
            <span style={{fontSize:8,fontWeight:700,color:'rgba(245,158,11,0.5)',letterSpacing:1}}>XP</span>
          </div>
        </div>

        <div style={{padding:'12px 16px 32px'}}>

          {/* ═══ CATEGORY TABS ═══ */}
          <div style={{
            display:'flex',gap:6,
            overflowX:'auto',
            padding:'0 0 8px',
            marginBottom:14,
            scrollbarWidth:'none',
          }}>
            {CATEGORIES.map(cat => {
              const isActive = activeCat === cat;
              return (
                <button
                  key={cat}
                  onClick={() => setActiveCat(cat)}
                  style={{
                    flexShrink:0,
                    padding:'6px 14px',
                    borderRadius:20,
                    cursor:'pointer',
                    fontSize:11,fontWeight:700,
                    fontFamily:"'Plus Jakarta Sans',sans-serif",
                    background:isActive ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.04)',
                    color:isActive ? '#F59E0B' : 'rgba(255,255,255,0.3)',
                    border:isActive ? '1px solid rgba(245,158,11,0.3)' : '1px solid rgba(255,255,255,0.07)',
                    transition:'all 0.15s',
                  }}
                >
                  {cat}
                </button>
              );
            })}
          </div>

          {/* ═══ SUCCESS TOAST ═══ */}
          <AnimatePresence>
            {purchaseSuccess && (
              <motion.div initial={{opacity:0,y:-16}} animate={{opacity:1,y:0}} exit={{opacity:0,y:-16}}
                style={{
                  padding:'10px 14px',borderRadius:12,marginBottom:12,
                  background:'rgba(16,185,129,0.08)',border:'1px solid rgba(16,185,129,0.2)',
                  display:'flex',alignItems:'center',gap:8,
                }}>
                <span style={{fontSize:14}}>✅</span>
                <span style={{fontSize:12,fontWeight:600,color:'#34D399'}}>Purchased "{purchaseSuccess}"!</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ═══ FEATURED BANNER ═══ */}
          <div style={{
            padding:'14px 16px',
            background:'radial-gradient(ellipse at left, rgba(245,158,11,0.1), transparent 70%), rgba(255,255,255,0.02)',
            border:'1px solid rgba(245,158,11,0.15)',
            borderRadius:14,
            marginBottom:16,
            display:'flex',alignItems:'center',justifyContent:'space-between',
          }}>
            <div>
              <p style={{margin:'0 0 3px',fontSize:10,color:'#F59E0B',fontWeight:700,letterSpacing:1,fontFamily:"'JetBrains Mono',monospace"}}>⭐ FEATURED</p>
              <p style={{margin:'0 0 2px',fontSize:14,fontWeight:800,color:'#FFF'}}>Holographic Coat</p>
              <p style={{margin:0,fontSize:11,color:'rgba(255,255,255,0.4)'}}>Legendary rarity • Limited</p>
            </div>
            <div style={{textAlign:'right'}}>
              <p style={{margin:'0 0 6px',fontSize:16,fontWeight:900,color:'#F59E0B',fontFamily:"'JetBrains Mono',monospace"}}>🪙 3,000</p>
              <button onClick={() => handleBuy(ITEMS.find(i => i.id === 'l4'))}
                style={{
                  padding:'7px 16px',borderRadius:8,border:'none',
                  background:'linear-gradient(135deg,#D97706,#F59E0B)',
                  color:'#fff',fontSize:11,fontWeight:700,cursor:'pointer',
                  fontFamily:"'Plus Jakarta Sans',sans-serif",
                }}>Buy Now</button>
            </div>
          </div>

          {/* ═══ SECTION LABEL ═══ */}
          <div style={{display:'flex',alignItems:'center',gap:8,marginBottom:12}}>
            <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.2)',textTransform:'uppercase',letterSpacing:2}}>◆ {activeCat === 'All' ? 'All Items' : activeCat}</span>
            <div style={{flex:1,height:1,background:'rgba(255,255,255,0.04)'}}/>
            <span style={{fontSize:9,fontWeight:700,color:'rgba(255,255,255,0.15)',fontFamily:"'JetBrains Mono',monospace"}}>{filtered.length}</span>
          </div>

          {/* ═══ ITEMS GRID ═══ */}
          <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
            {filtered.map((item, idx) => {
              const r = RARITY[item.rarity] || RARITY.Common;
              const canAfford = xp >= item.price;

              return (
                <motion.div
                  key={item.id}
                  initial={{opacity:0,y:16,scale:0.97}}
                  animate={{opacity:1,y:0,scale:1}}
                  transition={{delay:idx*0.04,duration:0.35}}
                  style={{
                    background:r.bg,
                    border:`1px solid ${r.border}`,
                    borderRadius:14,
                    padding:'14px 12px',
                    position:'relative',
                    overflow:'hidden',
                    display:'flex',
                    flexDirection:'column',
                    gap:6,
                    minHeight:170,
                  }}
                >
                  {/* Rarity glow */}
                  <div style={{position:'absolute',top:-10,right:-10,width:60,height:60,borderRadius:'50%',background:`radial-gradient(circle, ${r.color}15, transparent 70%)`,pointerEvents:'none'}} />

                  {/* HUD CORNERS */}
                  <div style={{position:'absolute',top:8,right:8,width:12,height:12,borderTop:`2px solid ${r.color}55`,borderRight:`2px solid ${r.color}55`,borderRadius:'0 3px 0 0'}}/>
                  <div style={{position:'absolute',bottom:8,left:8,width:8,height:8,borderBottom:`2px solid ${r.color}35`,borderLeft:`2px solid ${r.color}35`}}/>

                  {/* RARITY BADGE */}
                  <span style={{
                    alignSelf:'flex-start',
                    fontSize:8,fontWeight:700,letterSpacing:0.8,
                    padding:'2px 6px',borderRadius:4,
                    background:`${r.color}18`,
                    color:r.color,
                    border:`1px solid ${r.color}30`,
                    textTransform:'uppercase',
                    fontFamily:"'JetBrains Mono',monospace",
                  }}>{item.rarity}</span>

                  {/* ITEM ICON */}
                  <div style={{textAlign:'center',padding:'8px 0'}}>
                    <span style={{fontSize:36,fontFamily:'Apple Color Emoji,Segoe UI Emoji,sans-serif',lineHeight:1,filter:`drop-shadow(0 0 10px ${r.color}60)`}}>
                      {item.icon}
                    </span>
                  </div>

                  {/* ITEM INFO */}
                  <div>
                    <p style={{margin:'0 0 1px',fontSize:12,fontWeight:700,color:'#F0F9FF',overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{item.name}</p>
                    <p style={{margin:0,fontSize:10,color:'rgba(255,255,255,0.25)'}}>{item.cat}</p>
                  </div>

                  {/* PRICE + BUY */}
                  <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginTop:'auto',paddingTop:6,borderTop:'1px solid rgba(255,255,255,0.04)'}}>
                    <span style={{fontSize:12,fontWeight:800,color:'#F59E0B',fontFamily:"'JetBrains Mono',monospace"}}>
                      🪙 {item.price.toLocaleString()}
                    </span>
                    {(item.owned || ownedItems.includes(item.id)) ? (
                      equipped && equipped[getCategoryKey(item.cat)] === item.id ? (
                        <span style={{
                          padding:'4px 10px',borderRadius:6,fontSize:9,fontWeight:700,
                          background:'rgba(16,185,129,0.2)',color:'#10B981',
                          border:'1px solid #10B981',boxShadow:'0 0 8px rgba(16,185,129,0.4)'
                        }}>✓ Equipped</span>
                      ) : (
                        <button
                          onClick={() => handleEquip(item)}
                          style={{
                            padding:'4px 12px',borderRadius:6,border:'1px solid rgba(245,158,11,0.4)',
                            background:'rgba(245,158,11,0.06)',color:'#F59E0B',
                            fontSize:10,fontWeight:700,cursor:'pointer',
                            fontFamily:"'Plus Jakarta Sans',sans-serif",
                          }}
                        >Equip</button>
                      )
                    ) : (
                      <button
                        onClick={() => handleBuy(item)}
                        disabled={!canAfford}
                        style={{
                          padding:'4px 12px',borderRadius:6,border:'none',
                          background: canAfford ? `linear-gradient(135deg,${r.color}CC,${r.color})` : 'rgba(255,255,255,0.06)',
                          color: canAfford ? '#fff' : 'rgba(255,255,255,0.25)',
                          fontSize:10,fontWeight:700,
                          cursor: canAfford ? 'pointer' : 'default',
                          fontFamily:"'Plus Jakarta Sans',sans-serif",
                        }}
                      >
                        {canAfford ? 'BUY' : 'Need more XP'}
                      </button>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>

        </div>

        {/* ═══ CONFIRM MODAL ═══ */}
        <AnimatePresence>
          {confirmItem && (
            <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}
              onClick={() => setConfirmItem(null)}
              style={{
                position:'fixed',inset:0,zIndex:50,
                display:'flex',alignItems:'center',justifyContent:'center',
                background:'rgba(0,0,0,0.75)',backdropFilter:'blur(8px)',
                padding:'0 32px',
              }}>
              <motion.div initial={{scale:0.9,opacity:0}} animate={{scale:1,opacity:1}} exit={{scale:0.9,opacity:0}}
                onClick={e => e.stopPropagation()}
                style={{
                  width:'100%',maxWidth:300,
                  background:'#0F0D08',
                  border:'1px solid rgba(245,158,11,0.2)',
                  borderRadius:18,padding:24,
                  display:'flex',flexDirection:'column',alignItems:'center',gap:14,
                  textAlign:'center',
                }}>
                <span style={{fontSize:48,fontFamily:'Apple Color Emoji,Segoe UI Emoji,sans-serif'}}>{confirmItem.icon}</span>
                <h3 style={{margin:0,fontSize:15,fontWeight:800,color:'#F0F9FF'}}>Buy "{confirmItem.name}"?</h3>
                <div style={{display:'flex',alignItems:'center',gap:6}}>
                  <span style={{fontSize:14}}>🪙</span>
                  <span style={{fontSize:14,fontWeight:800,color:'#F59E0B',fontFamily:"'JetBrains Mono',monospace"}}>{confirmItem.price.toLocaleString()} XP</span>
                </div>
                <p style={{margin:0,fontSize:11,color:'rgba(255,255,255,0.3)'}}>Balance after: {(xp - confirmItem.price).toLocaleString()} XP</p>

                <div style={{display:'flex',gap:10,width:'100%',marginTop:4}}>
                  <button onClick={() => setConfirmItem(null)}
                    style={{
                      flex:1,padding:'11px',borderRadius:10,
                      background:'rgba(255,255,255,0.04)',border:'1px solid rgba(255,255,255,0.08)',
                      color:'rgba(255,255,255,0.4)',fontSize:11,fontWeight:700,cursor:'pointer',
                      fontFamily:"'Plus Jakarta Sans',sans-serif",
                    }}>Cancel</button>
                  <button onClick={confirmPurchase}
                    style={{
                      flex:1,padding:'11px',borderRadius:10,border:'none',
                      background:'linear-gradient(135deg,#D97706,#F59E0B)',
                      color:'#fff',fontSize:11,fontWeight:700,cursor:'pointer',
                      fontFamily:"'Plus Jakarta Sans',sans-serif",
                      boxShadow:'0 0 16px rgba(245,158,11,0.3)',
                    }}>Confirm</button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    );
}
