import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api, tokenStore, API_BASE_URL } from '../services/apiClient';
import {
  Upload, Camera, Microscope, AlertTriangle, CheckCircle,
  X, FileText, Loader2, Activity, Info, ArrowLeft,
  RefreshCw, Heart, Clock
} from 'lucide-react';

// ═══════════════════════════════════════════════════════════
//  Constants
// ═══════════════════════════════════════════════════════════

const SEVERITY_COLORS = {
  low: '#22c55e', mild: '#f59e0b', moderate: '#f59e0b',
  high: '#ef4444', severe: '#dc2626', critical: '#dc2626',
};

function extractError(err) {
  if (!err) return 'Unknown error';
  if (typeof err === 'string') return err;
  const p = err.payload || err;
  if (typeof p?.detail === 'string') return p.detail;
  if (Array.isArray(p?.detail)) return p.detail.map(e => e.msg || '').join(', ');
  return err.message || 'An error occurred';
}

// ═══════════════════════════════════════════════════════════
//  Component
// ═══════════════════════════════════════════════════════════

export default function HematologyLabScreen({ onNavigate }) {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [annotatedUrl, setAnnotatedUrl] = useState(null);
  const [clinicalReport, setClinicalReport] = useState(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [showReport, setShowReport] = useState(false);
  const [error, setError] = useState(null);
  const [pollingStatus, setPollingStatus] = useState('');

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const pollingRef = useRef(null);

  useEffect(() => () => { if (pollingRef.current) clearInterval(pollingRef.current); }, []);

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImage(file); setImagePreview(URL.createObjectURL(file));
    setAnalysisResult(null); setAnnotatedUrl(null); setClinicalReport(null);
    setShowReport(false); setError(null);
    e.target.value = '';
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setImage(file); setImagePreview(URL.createObjectURL(file));
      setAnalysisResult(null); setAnnotatedUrl(null); setClinicalReport(null);
      setShowReport(false); setError(null);
    }
  };

  const handleNewSample = () => {
    setImage(null); setImagePreview(null); setAnalysisResult(null); setAnnotatedUrl(null);
    setClinicalReport(null); setShowReport(false); setError(null); setPollingStatus('');
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  // ── Async V1 pipeline ──
  const handleAnalyze = async () => {
    if (!image || isAnalyzing) return;
    setIsAnalyzing(true); setError(null); setAnalysisResult(null); setAnnotatedUrl(null);

    try {
      setPollingStatus('Creating patient record…');
      const patient = await api.patients.create({ patient_code: `AUTO-${Date.now()}`, full_name: 'Anonymous Patient', gender: 'other' });

      setPollingStatus('Creating case…');
      const caseRec = await api.cases.create({ patient_id: patient.id, department: 'hematology', test_type: 'blood_smear', notes: 'Automated hematology analysis' });

      setPollingStatus('Uploading specimen…');
      const asset = await api.cases.uploadAsset(caseRec.id, image);

      setPollingStatus('Triggering AI analysis…');
      const trigger = await api.analyses.trigger({ case_id: caseRec.id, asset_id: asset.id });
      const runId = trigger.run_id || trigger.id;

      setPollingStatus('AI analyzing blood cells…');
      let attempts = 0;
      const detail = await new Promise((resolve, reject) => {
        pollingRef.current = setInterval(async () => {
          attempts++;
          if (attempts > 30) { clearInterval(pollingRef.current); reject(new Error('Analysis timed out after 60s')); return; }
          try {
            const d = await api.analyses.getStatus(runId);
            const st = d.run?.status || d.status;
            setPollingStatus(`Processing… (${st})`);
            if (st === 'completed') { clearInterval(pollingRef.current); resolve(d); }
            else if (st === 'failed') { clearInterval(pollingRef.current); reject(new Error(d.run?.error_message || 'Analysis failed')); }
          } catch (_) { /* transient */ }
        }, 2000);
      });

      setAnalysisResult(detail.result);

      // Fetch annotated image as blob URL
      setPollingStatus('Fetching annotated image…');
      try {
        const imgResp = await fetch(`${API_BASE_URL}/api/analyses/runs/${runId}/annotated-image`, {
          headers: { 'Authorization': `Bearer ${tokenStore.get()}` }
        });
        if (imgResp.ok) {
          const blob = await imgResp.blob();
          setAnnotatedUrl(URL.createObjectURL(blob));
        }
      } catch (_) { /* annotated image optional */ }

    } catch (err) {
      setError(extractError(err));
    } finally {
      setIsAnalyzing(false); setPollingStatus('');
      if (pollingRef.current) clearInterval(pollingRef.current);
    }
  };

  const handleClinicalReport = async () => {
    if (!analysisResult || isLoadingReport) return;
    const aiEnabled = localStorage.getItem('labmind_ai_enhancement') !== 'false';
    setIsLoadingReport(true);
    try {
      const report = await api.hematology.clinicalReport({
        cell_counts: { total: analysisResult.total_cells, sickle: analysisResult.sickle_count, normal: analysisResult.normal_count },
        detections: analysisResult.cell_details?.detections || [],
        patient_context: {},
        use_ai: aiEnabled,
      });
      setClinicalReport(report); setShowReport(true);
    } catch (err) { setError(extractError(err)); }
    finally { setIsLoadingReport(false); }
  };

  const P = '#ef4444', G = '#f87171', BG = '#030712';
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  const sicklePct = analysisResult?.sickle_percentage ?? 0;

  return (
    <div style={{ minHeight:'100vh', background:'radial-gradient(ellipse at 30% 20%, rgba(239,68,68,0.08), transparent 50%), linear-gradient(180deg,#0F0505,#080305)', color:'#E8F4FF', fontFamily:"'Plus Jakarta Sans',sans-serif", display:'flex', flexDirection:'column', alignItems:'center', overflowX:'hidden', overflowY:'auto', WebkitOverflowScrolling:'touch' }}>
      <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFileSelect} style={{ display:'none' }} />
      <input ref={cameraInputRef} type="file" accept="image/*" capture="environment" onChange={handleFileSelect} style={{ display:'none' }} />

      {/* HEADER */}
      <div style={{ position:'sticky', top:0, zIndex:20, display:'flex', alignItems:'center', gap:12, padding:'14px 20px', width:'100%', background:'rgba(5,8,16,0.85)', backdropFilter:'blur(24px)', WebkitBackdropFilter:'blur(24px)', borderBottom:'1px solid rgba(239,68,68,0.13)' }}>
        <button onClick={() => onNavigate('virtual-lab')} style={{ width:36, height:36, borderRadius:10, background:'rgba(239,68,68,0.08)', border:'1px solid rgba(239,68,68,0.2)', display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer', color:'#F87171', flexShrink:0 }}><ArrowLeft size={16} /></button>
        <div style={{ flex:1 }}>
          <h1 style={{ margin:0, fontSize:17, fontWeight:800, color:'#F0F9FF', letterSpacing:-0.3, display:'flex', alignItems:'center', gap:8 }}>
            <Heart size={17} style={{ color:'#F87171' }} /> HEMATOLOGY LAB
          </h1>
          <p style={{ margin:0, fontSize:10, color:'rgba(255,255,255,0.3)', letterSpacing:1, fontFamily:"'JetBrains Mono',monospace" }}>BLOOD CELL ANALYSIS • SICKLE CELL DETECTION</p>
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:5, padding:'4px 10px', background:'rgba(239,68,68,0.08)', border:'1px solid rgba(239,68,68,0.22)', borderRadius:20 }}>
          <div style={{ width:5, height:5, borderRadius:'50%', background:'#EF4444' }} />
          <span style={{ fontSize:9, fontWeight:700, color:'#EF4444', fontFamily:"'JetBrains Mono',monospace" }}>82% mAP</span>
        </div>
      </div>

      {/* MAIN */}
      <div className="hema-main" style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:16, padding:16, width:'100%' }}>
        {/* LEFT */}
        <div style={{ width:'100%', display:'flex', flexDirection:'column', alignItems:'center', gap:16 }}>
          <div className="hema-circle" onDragOver={e=>e.preventDefault()} onDrop={handleDrop}
            style={{ width:'100%', maxWidth:'min(460px,85vw)', aspectRatio:'1/1', borderRadius:'50%', border:`2px solid ${P}40`, background:`${P}08`, display:'flex', alignItems:'center', justifyContent:'center', overflow:'hidden', position:'relative', margin:'0 auto' }}>
            {isAnalyzing && <div style={{ position:'absolute', inset:0, border:`3px solid transparent`, borderTopColor:P, borderRadius:'50%', animation:'labSpin 1s linear infinite', zIndex:5 }} />}
            {annotatedUrl
              ? <img src={annotatedUrl} alt="Annotated" style={{ width:'100%', height:'100%', objectFit:'cover', borderRadius:'50%' }} />
              : imagePreview
                ? <img src={imagePreview} alt="Preview" style={{ width:'100%', height:'100%', objectFit:'cover', borderRadius:'50%', opacity:isAnalyzing?0.5:1 }} />
                : <div style={{ textAlign:'center', color:`${P}66` }}><Microscope size={48} /><p style={{ fontSize:12, marginTop:8 }}>Drop blood smear or upload</p></div>}
            {isAnalyzing && <div style={{ position:'absolute', display:'flex', flexDirection:'column', alignItems:'center', gap:6, background:'rgba(0,0,0,0.5)', padding:'12px 20px', borderRadius:12 }}>
              <Loader2 size={28} style={{ color:G, animation:'labSpin 1s linear infinite' }} />
              <span style={{ fontSize:11, color:G }}>{pollingStatus || 'Processing…'}</span>
            </div>}
          </div>
          <div style={{ display:'flex', gap:10, flexWrap:'wrap', justifyContent:'center', width:'100%' }}>
            {(analysisResult||image) && <button onClick={handleNewSample} style={{ display:'flex', alignItems:'center', gap:4, padding:'8px 14px', borderRadius:12, border:'1px solid rgba(239,68,68,0.3)', background:'rgba(239,68,68,0.07)', color:'#F87171', cursor:'pointer', fontSize:12, fontFamily:"'Plus Jakarta Sans',sans-serif", fontWeight:700 }}><RefreshCw size={14} /> New Sample</button>}
            <button onClick={()=>fileInputRef.current?.click()} style={{ display:'flex', alignItems:'center', gap:4, padding:'8px 14px', borderRadius:12, border:'1px solid rgba(239,68,68,0.3)', background:'rgba(239,68,68,0.07)', color:'#F87171', cursor:'pointer', fontSize:12, fontFamily:"'Plus Jakarta Sans',sans-serif", fontWeight:700 }}><Upload size={14} /> Upload</button>
            <button onClick={()=>cameraInputRef.current?.click()} style={{ display:'flex', alignItems:'center', gap:4, padding:'8px 14px', borderRadius:12, border:'1px solid rgba(239,68,68,0.3)', background:'rgba(239,68,68,0.07)', color:'#F87171', cursor:'pointer', fontSize:12, fontFamily:"'Plus Jakarta Sans',sans-serif", fontWeight:700 }}><Camera size={14} /> Camera</button>
            {image && !analysisResult && !isAnalyzing && <button onClick={handleAnalyze} style={{ display:'flex', alignItems:'center', gap:4, padding:'8px 16px', borderRadius:12, background:'linear-gradient(135deg,#EF4444,#dc2626)', color:'#fff', fontWeight:700, cursor:'pointer', fontSize:12, fontFamily:"'Plus Jakarta Sans',sans-serif", border:'none' }}><Activity size={14} /> Analyze</button>}
          </div>
          {error && <div style={{ display:'flex', alignItems:'center', gap:8, padding:'10px 14px', background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.3)', borderRadius:8, color:'#fca5a5', fontSize:12, maxWidth:460 }}><AlertTriangle size={16} /> {error}</div>}
        </div>

        {/* RIGHT */}
        <div style={{ width:'100%', maxWidth:460, margin:'0 auto', display:'flex', flexDirection:'column', gap:16 }}>
          {!analysisResult && !isAnalyzing && (<>
            <div style={{ padding:16, background:'rgba(239,68,68,0.04)', border:'1px solid rgba(239,68,68,0.14)', borderRadius:14 }}>
              <h3 style={{ margin:'0 0 8px', color:'#F87171', fontSize:16, fontWeight:800 }}>🩸 Hematology Lab</h3>
              <p style={{ margin:0, fontSize:12, color:'rgba(255,255,255,0.4)' }}>Sickle cell & RBC morphology analysis via async Celery pipeline.</p>
              <div style={{ display:'flex', gap:16, marginTop:12 }}>
                {[['V1','Pipeline'],['Celery','Worker'],['SCD','Detection']].map(([v,l])=>(
                  <div key={l} style={{ textAlign:'center' }}><div style={{ fontSize:18, fontWeight:800, color:'#F87171', fontFamily:"'JetBrains Mono',monospace" }}>{v}</div><div style={{ fontSize:10, color:'rgba(255,255,255,0.3)' }}>{l}</div></div>
                ))}
              </div>
            </div>
            <div style={{ padding:12, background:'rgba(255,255,255,0.025)', border:'1px solid rgba(239,68,68,0.12)', borderRadius:14, display:'flex', alignItems:'center', gap:8 }}>
              <Clock size={16} style={{ color:'rgba(255,255,255,0.3)' }} />
              <span style={{ fontSize:11, color:'rgba(255,255,255,0.4)' }}>Async pipeline — results take 10-30 seconds</span>
            </div>
          </>)}

          {isAnalyzing && (
            <div style={{ padding:24, textAlign:'center', background:`${P}0a`, border:`1px solid ${P}26`, borderRadius:12 }}>
              <Loader2 size={28} style={{ color:G, animation:'labSpin 1s linear infinite', margin:'0 auto' }} />
              <p style={{ marginTop:12, fontSize:13, color:G }}>{pollingStatus || 'Processing…'}</p>
              <p style={{ margin:'6px 0 0', fontSize:10, color:'#6b7280' }}>Patient → Case → Asset → AI → Result</p>
            </div>
          )}

          {analysisResult && !isAnalyzing && (<>
            {/* Sickle assessment */}
            <div style={{ padding:14, borderRadius:12, background:`${P}0f`, border:`1px solid ${P}33`, textAlign:'center' }}>
              <div style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:6, marginBottom:6 }}>
                {sicklePct > 0 ? <AlertTriangle size={18} style={{ color:P }} /> : <CheckCircle size={18} style={{ color:'#22c55e' }} />}
                <span style={{ fontWeight:700, fontSize:14, color:sicklePct > 0 ? P : '#22c55e' }}>
                  {sicklePct > 0 ? `SICKLE CELLS DETECTED (${sicklePct.toFixed(1)}%)` : 'NO SICKLE CELLS DETECTED'}
                </span>
              </div>
            </div>

            {/* Cell counts — derive from detections for full breakdown */}
            {(() => {
              const dets = analysisResult.cell_details?.detections || [];
              const classCounts = {};
              dets.forEach(d => { const cn = d.class_name || d.label?.toLowerCase() || 'unknown'; classCounts[cn] = (classCounts[cn] || 0) + 1; });
              const cards = [
                { label:'Total', value:analysisResult.total_cells, color:G },
                { label:'RBC (Normal)', value:classCounts.rbc || analysisResult.normal_count || 0, color:'#22c55e' },
                { label:'Sickle', value:classCounts.sickle || analysisResult.sickle_count || 0, color:P },
                { label:'WBC', value:classCounts.wbc || 0, color:'#3b82f6' },
                { label:'Platelet', value:classCounts.plt || 0, color:'#a855f7' },
              ];
              if ((classCounts.target || 0) > 0) cards.push({ label:'Target', value:classCounts.target, color:'#f59e0b' });
              if ((classCounts.other_abnormal || 0) > 0) cards.push({ label:'Abnormal', value:classCounts.other_abnormal, color:'#ef4444' });
              return (
                <div style={{ display:'flex', gap:6, flexWrap:'wrap' }}>
                  {cards.map(c => (
                    <div key={c.label} style={{ flex:'1 1 28%', minWidth:80, padding:'8px 10px', borderRadius:10, background:'rgba(0,0,0,0.3)', border:`1px solid ${c.color}33`, textAlign:'center' }}>
                      <div style={{ fontSize:20, fontWeight:700, color:c.color }}>{c.value}</div>
                      <div style={{ fontSize:9, color:'#9ca3af' }}>{c.label}</div>
                    </div>
                  ))}
                </div>
              );
            })()}

            {/* Quality */}
            {analysisResult.quality_score != null && (
              <div style={{ padding:12, borderRadius:10, background:'rgba(255,255,255,0.02)', border:`1px solid ${P}1f`, display:'flex', justifyContent:'space-between', alignItems:'center' }}>
                <span style={{ fontSize:12, color:'#9ca3af' }}>Quality Score</span>
                <span style={{ fontSize:13, fontWeight:600, color: analysisResult.quality_score >= 70 ? '#22c55e' : '#f59e0b' }}>
                  {Math.round(analysisResult.quality_score)}% — {analysisResult.quality_status || 'N/A'}
                </span>
              </div>
            )}

            <button onClick={handleClinicalReport} disabled={isLoadingReport}
              style={{ width:'100%', padding:'12px 0', borderRadius:10, border:'none', cursor:'pointer', background:`linear-gradient(135deg,${P},#dc2626)`, color:'#fff', fontWeight:700, fontSize:13, display:'flex', alignItems:'center', justifyContent:'center', gap:8, opacity:isLoadingReport?0.6:1 }}>
              {isLoadingReport ? <Loader2 size={16} style={{ animation:'labSpin 1s linear infinite' }} /> : <FileText size={16} />}
              {isLoadingReport ? 'Generating Report…' : 'Clinical Report'}
            </button>
          </>)}
        </div>
      </div>

      {/* CLINICAL REPORT MODAL */}
      <AnimatePresence>
        {showReport && clinicalReport?.rule_based && (
          <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
            style={{ position:'fixed', inset:0, background:'rgba(0,0,0,0.85)', zIndex:50, display:'flex', alignItems:'center', justifyContent:'center', padding:16 }}>
            <motion.div initial={{ scale:0.9, opacity:0 }} animate={{ scale:1, opacity:1 }} exit={{ scale:0.9, opacity:0 }}
              style={{ background:'#0f172a', border:`1px solid ${P}40`, borderRadius:16, padding:24, maxWidth:560, width:'100%', maxHeight:'85vh', overflowY:'auto', position:'relative' }}>
              <button onClick={()=>setShowReport(false)} style={{ position:'absolute', top:12, right:12, background:'none', border:'none', color:'#9ca3af', cursor:'pointer' }}><X size={20} /></button>
              {(()=>{
                const rb = clinicalReport.rule_based;
                const sevColor = rb.severity_color || SEVERITY_COLORS[rb.severity] || P;
                return (<>
                  <div style={{ textAlign:'center', marginBottom:16 }}>
                    <span style={{ display:'inline-block', padding:'4px 16px', borderRadius:99, background:`${sevColor}22`, color:sevColor, fontWeight:700, fontSize:12, textTransform:'uppercase', border:`1px solid ${sevColor}44` }}>{rb.severity || rb.scenario}</span>
                  </div>
                  <h2 style={{ margin:'0 0 16px', fontSize:16, color:G, textAlign:'center', lineHeight:1.4 }}>{rb.primary_diagnosis || rb.scenario || 'Clinical Report'}</h2>

                  {rb.summary_for_clinician && <div style={{ padding:12, background:`${P}0f`, border:`1px solid ${P}26`, borderRadius:8, marginBottom:12, fontSize:12, color:'#d1d5db', lineHeight:1.6 }}>{rb.summary_for_clinician}</div>}

                  {rb.differential_diagnosis?.length > 0 && (
                    <div style={{ marginBottom:12 }}>
                      <h4 style={{ fontSize:12, color:G, margin:'0 0 6px', fontWeight:600 }}>Differential Diagnosis</h4>
                      {rb.differential_diagnosis.map((d,i)=>(<div key={i} style={{ padding:'6px 8px', borderBottom:'1px solid rgba(255,255,255,0.04)', fontSize:11, color:'#d1d5db' }}>{d.condition || d.organism || d}</div>))}
                    </div>
                  )}

                  {rb.recommended_investigations?.length > 0 && (
                    <div style={{ marginBottom:12 }}>
                      <h4 style={{ fontSize:12, color:G, margin:'0 0 6px', fontWeight:600 }}>Recommended Investigations</h4>
                      {rb.recommended_investigations.map((inv,i)=>(<div key={i} style={{ padding:'4px 8px', fontSize:11, color:'#d1d5db', borderBottom:'1px solid rgba(255,255,255,0.04)' }}>• {typeof inv==='string'?inv:inv.test}</div>))}
                    </div>
                  )}

                  {rb.red_flags?.length > 0 && (
                    <div style={{ marginBottom:12, padding:10, background:'rgba(239,68,68,0.08)', border:'1px solid rgba(239,68,68,0.2)', borderRadius:8 }}>
                      <h4 style={{ fontSize:12, color:'#ef4444', margin:'0 0 6px', fontWeight:600, display:'flex', alignItems:'center', gap:4 }}><AlertTriangle size={14} /> Red Flags</h4>
                      {rb.red_flags.map((rf,i)=>(<div key={i} style={{ fontSize:11, color:'#fca5a5', marginBottom:4 }}>⚠ {typeof rf==='string'?rf:rf.flag}</div>))}
                    </div>
                  )}

                  {rb.educational_note && (
                    <div style={{ padding:12, background:`${P}0a`, border:`1px solid ${P}1f`, borderRadius:8, marginBottom:12 }}>
                      <h4 style={{ fontSize:12, color:G, margin:'0 0 6px', fontWeight:600, display:'flex', alignItems:'center', gap:4 }}><Info size={14} /> Educational Note</h4>
                      <p style={{ fontSize:11, color:'#d1d5db', margin:0, lineHeight:1.6 }}>{typeof rb.educational_note==='string'?rb.educational_note:rb.educational_note?.english}</p>
                    </div>
                  )}

                  {rb.disclaimer && <p style={{ fontSize:10, color:'#4b5563', textAlign:'center', marginTop:12, fontStyle:'italic' }}>{rb.disclaimer}</p>}
                </>);
              })()}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @keyframes labSpin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        @keyframes labPulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        .hema-circle { max-width:85vw !important; }
      `}</style>
    </div>
  );
}
