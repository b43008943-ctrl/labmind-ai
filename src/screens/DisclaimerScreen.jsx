import { useState } from 'react';
import { motion } from 'framer-motion';

export default function DisclaimerScreen({ onAccept }) {
  const [checked1, setChecked1] = useState(false);
  const [checked2, setChecked2] = useState(false);
  const canProceed = checked1 && checked2;

  const handleAccept = () => {
    if (!canProceed) return;
    localStorage.setItem('labmind_disclaimer_accepted', 'true');
    onAccept();
  };

  return (
    <div style={{
      minHeight:'100vh',
      background:'radial-gradient(ellipse at 30% 20%, rgba(0,212,255,0.07), transparent 50%), linear-gradient(180deg,#070C1A,#050810)',
      fontFamily:"'Plus Jakarta Sans',sans-serif",
      color:'#E8F4FF',
      display:'flex',flexDirection:'column',
      alignItems:'center',justifyContent:'center',
      padding:'24px 20px',
      overflowY:'auto',
    }}>


      {/* LOGO */}
      <motion.div
        initial={{opacity:0,y:-20}}
        animate={{opacity:1,y:0}}
        transition={{duration:0.5}}
        style={{textAlign:'center',marginBottom:28}}
      >
        <div style={{fontSize:48,marginBottom:8}}>🔬</div>
        <h1 style={{margin:0,fontSize:22,fontWeight:900,color:'#F0F9FF',letterSpacing:-0.5}}>
          LabMind AI
        </h1>
        <p style={{margin:'4px 0 0',fontSize:11,color:'rgba(0,212,255,0.6)',letterSpacing:2,fontWeight:600}}>
          SMART ANALYST SYSTEM
        </p>
      </motion.div>

      {/* DISCLAIMER CARD */}
      <motion.div
        initial={{opacity:0,y:20}}
        animate={{opacity:1,y:0}}
        transition={{delay:0.2,duration:0.5}}
        style={{
          width:'100%',maxWidth:400,
          background:'rgba(255,255,255,0.03)',
          border:'1px solid rgba(255,255,255,0.08)',
          borderRadius:20,padding:'24px 20px',marginBottom:16,
        }}
      >
        {/* WARNING */}
        <div style={{
          display:'flex',alignItems:'center',gap:10,
          padding:'10px 14px',
          background:'rgba(245,158,11,0.08)',
          border:'1px solid rgba(245,158,11,0.2)',
          borderRadius:10,marginBottom:20,
        }}>
          <span style={{fontSize:20}}>⚠️</span>
          <div>
            <p style={{margin:0,fontSize:12,fontWeight:800,color:'#F59E0B'}}>Important Disclaimer</p>
            <p style={{margin:0,fontSize:10,color:'rgba(245,158,11,0.7)'}}>Please read before continuing</p>
          </div>
        </div>

        {/* TEXT */}
        <div style={{marginBottom:20}}>
          <p style={{fontSize:12,color:'rgba(255,255,255,0.7)',lineHeight:1.7,margin:'0 0 10px'}}>
            🎓 <strong style={{color:'#F0F9FF'}}>Educational Purpose Only</strong><br/>
            LabMind AI is designed as an educational and training tool for medical students and laboratory professionals.
          </p>
          <p style={{fontSize:12,color:'rgba(255,255,255,0.7)',lineHeight:1.7,margin:'0 0 10px'}}>
            🩺 <strong style={{color:'#F0F9FF'}}>Not a Medical Device</strong><br/>
            Results are NOT a substitute for professional medical diagnosis. Always consult a licensed healthcare professional.
          </p>
          <p style={{fontSize:12,color:'rgba(255,255,255,0.7)',lineHeight:1.7,margin:0}}>
            📊 <strong style={{color:'#F0F9FF'}}>AI Accuracy</strong><br/>
            Model accuracy ranges from 79–98%. Results may vary based on image quality.
          </p>
        </div>

        {/* CHECKBOXES */}
        <div style={{display:'flex',flexDirection:'column',gap:10}}>

          <div
            onClick={() => setChecked1(!checked1)}
            style={{
              display:'flex',alignItems:'flex-start',gap:10,
              padding:'12px',cursor:'pointer',borderRadius:10,
              background: checked1 ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.02)',
              border: checked1 ? '1px solid rgba(16,185,129,0.25)' : '1px solid rgba(255,255,255,0.06)',
              transition:'all 0.2s',
            }}
          >
            <div style={{
              width:20,height:20,borderRadius:5,flexShrink:0,marginTop:1,
              background: checked1 ? '#10B981' : 'transparent',
              border: checked1 ? '2px solid #10B981' : '2px solid rgba(255,255,255,0.2)',
              display:'flex',alignItems:'center',justifyContent:'center',
              transition:'all 0.2s',
            }}>
              {checked1 && <span style={{fontSize:11,color:'#fff',fontWeight:700}}>✓</span>}
            </div>
            <p style={{margin:0,fontSize:11,color:'rgba(255,255,255,0.7)',lineHeight:1.5}}>
              I understand this app is for <strong style={{color:'#F0F9FF'}}>educational purposes only</strong> and results are not a substitute for professional medical advice.
            </p>
          </div>

          <div
            onClick={() => setChecked2(!checked2)}
            style={{
              display:'flex',alignItems:'flex-start',gap:10,
              padding:'12px',cursor:'pointer',borderRadius:10,
              background: checked2 ? 'rgba(0,212,255,0.06)' : 'rgba(255,255,255,0.02)',
              border: checked2 ? '1px solid rgba(0,212,255,0.2)' : '1px solid rgba(255,255,255,0.06)',
              transition:'all 0.2s',
            }}
          >
            <div style={{
              width:20,height:20,borderRadius:5,flexShrink:0,marginTop:1,
              background: checked2 ? '#00D4FF' : 'transparent',
              border: checked2 ? '2px solid #00D4FF' : '2px solid rgba(255,255,255,0.2)',
              display:'flex',alignItems:'center',justifyContent:'center',
              transition:'all 0.2s',
            }}>
              {checked2 && <span style={{fontSize:11,color:'#fff',fontWeight:700}}>✓</span>}
            </div>
            <p style={{margin:0,fontSize:11,color:'rgba(255,255,255,0.7)',lineHeight:1.5}}>
              I consent to clinical reports being enhanced by <strong style={{color:'#F0F9FF'}}>Google Gemini AI</strong>. Analysis data may be processed by Google's servers.
            </p>
          </div>
        </div>
      </motion.div>

      {/* BUTTON */}
      <motion.button
        initial={{opacity:0}}
        animate={{opacity:1}}
        transition={{delay:0.4}}
        onClick={handleAccept}
        disabled={!canProceed}
        style={{
          width:'100%',maxWidth:400,
          padding:'14px',borderRadius:14,border:'none',
          background: canProceed
            ? 'linear-gradient(135deg,#0077AA,#00D4FF)'
            : 'rgba(255,255,255,0.06)',
          color: canProceed ? '#fff' : 'rgba(255,255,255,0.2)',
          fontSize:14,fontWeight:800,
          cursor: canProceed ? 'pointer' : 'default',
          fontFamily:"'Plus Jakarta Sans',sans-serif",
          boxShadow: canProceed ? '0 0 24px rgba(0,180,255,0.3)' : 'none',
          transition:'all 0.2s',
          letterSpacing:0.3,
        }}
      >
        {canProceed ? '✓ I Agree — Enter LabMind AI' : 'Please accept both terms above'}
      </motion.button>

      <p style={{margin:'12px 0 0',fontSize:10,color:'rgba(255,255,255,0.15)',textAlign:'center'}}>
        This agreement is stored locally and will not be shown again.
      </p>

    </div>
  );
}
