import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, Camera, FileText, AlertTriangle, CheckCircle2, Loader2, ChevronDown, ChevronUp, ArrowUp, ArrowDown, Minus, Info, ImagePlus, ShieldAlert, RotateCcw } from 'lucide-react';
import { useNavigation } from '../context/NavigationContext';

/* ═══════════════════════════════════════════════════════════════
   LAB RESULTS ANALYZER — AI-Powered Lab Report Reader
   Upload/photograph → Gemini Vision → structured clinical analysis
   ═══════════════════════════════════════════════════════════════ */

import { API_BASE_URL as API_BASE } from '../services/apiClient';

export default function LabResultsAnalyzerScreen() {
    const { goBack } = useNavigation();

    const [phase, setPhase] = useState('upload'); // upload | analyzing | results
    const [imageFile, setImageFile] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);
    const [analysisData, setAnalysisData] = useState(null);
    const [errorMessage, setErrorMessage] = useState(null);
    const [expandedIdx, setExpandedIdx] = useState(null);

    const fileInputRef = useRef(null);
    const cameraInputRef = useRef(null);

    // ── Handle file selection ──
    const handleFile = useCallback((file) => {
        if (!file) return;
        if (!file.type.startsWith('image/')) {
            setErrorMessage('Please select an image file (JPG, PNG).');
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            setErrorMessage('File exceeds 10 MB limit.');
            return;
        }
        setErrorMessage(null);
        setImageFile(file);
        setImagePreview(URL.createObjectURL(file));
    }, []);

    const handleDrop = useCallback((e) => {
        e.preventDefault();
        handleFile(e.dataTransfer.files[0]);
    }, [handleFile]);

    // ── Analyze ──
    const handleAnalyze = async () => {
        if (!imageFile) return;
        setPhase('analyzing');
        setErrorMessage(null);

        const token = localStorage.getItem('labmind_token');
        const formData = new FormData();
        formData.append('file', imageFile);

        try {
            const resp = await fetch(`${API_BASE}/api/lab-results/analyze`, {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
                body: formData,
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({}));
                throw new Error(err.detail || `Server error (${resp.status})`);
            }

            const data = await resp.json();
            if (data.success && data.data) {
                setAnalysisData(data.data);
                setPhase('results');
            } else {
                throw new Error('Unexpected server response.');
            }
        } catch (err) {
            setErrorMessage(err.message || 'Failed to analyze. Check your connection.');
            setPhase('upload');
        }
    };

    const resetAll = () => {
        setPhase('upload');
        setImageFile(null);
        setImagePreview(null);
        setAnalysisData(null);
        setErrorMessage(null);
        setExpandedIdx(null);
    };

    const statusColor = (s) => s === 'high' ? '#EF4444' : s === 'low' ? '#F59E0B' : '#22C55E';
    const statusIcon = (s) => s === 'high' ? <ArrowUp size={12} /> : s === 'low' ? <ArrowDown size={12} /> : <Minus size={12} />;
    const statusLabel = (s) => s === 'high' ? 'HIGH' : s === 'low' ? 'LOW' : 'NORMAL';

    return (
        <div className="min-h-dvh w-full bg-[#0A0E17] flex flex-col pb-24 overflow-y-auto no-scrollbar">
            {/* Header */}
            <header className="px-6 pt-12 pb-4 flex items-center gap-4 sticky top-0 bg-[#0A0E17]/80 backdrop-blur-xl z-40 border-b border-white/5">
                <button onClick={goBack} className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 transition-colors shrink-0">
                    <ChevronLeft className="w-5 h-5" />
                </button>
                <div className="flex-1">
                    <h1 className="text-lg font-bold text-white tracking-wide flex items-center gap-2">
                        <FileText className="w-5 h-5 text-amber-400" /> Lab Results Analyzer
                    </h1>
                    <p className="text-[11px] text-slate-400 font-medium mt-0.5">AI-powered lab report interpretation</p>
                </div>
            </header>

            <div className="flex-1 px-6 pt-6 max-w-2xl mx-auto w-full">
                <AnimatePresence mode="wait">

                    {/* ═══ UPLOAD ═══ */}
                    {phase === 'upload' && (
                        <motion.div key="upload" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="flex flex-col gap-5">

                            {errorMessage && (
                                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3">
                                    <AlertTriangle size={18} className="text-red-400 shrink-0 mt-0.5" />
                                    <p className="text-sm text-red-300">{errorMessage}</p>
                                </div>
                            )}

                            {/* Image preview or drop zone */}
                            {imagePreview ? (
                                <div className="flex flex-col gap-4">
                                    <div className="relative rounded-2xl overflow-hidden border border-white/10 shadow-[0_0_30px_rgba(0,0,0,0.5)]">
                                        <img src={imagePreview} alt="Lab report" className="w-full max-h-[400px] object-contain bg-black/50" />
                                        <button onClick={resetAll} className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/60 border border-white/10 flex items-center justify-center text-white/70 hover:text-white hover:bg-black/80 transition-colors">✕</button>
                                    </div>
                                    <button onClick={handleAnalyze} className="w-full py-4 rounded-2xl font-bold text-sm tracking-wider uppercase flex items-center justify-center gap-3 bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 text-amber-300 hover:from-amber-500/30 hover:to-orange-500/30 cursor-pointer active:scale-[0.98] transition-all">
                                        <FileText size={18} /> Analyze Report
                                    </button>
                                </div>
                            ) : (
                                <div onDragOver={(e) => e.preventDefault()} onDrop={handleDrop}
                                    className="flex flex-col items-center justify-center py-16 px-6 rounded-2xl bg-white/[0.03] border-2 border-dashed border-white/10 hover:border-amber-500/30 hover:bg-white/[0.05] transition-all text-center">
                                    <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mb-5">
                                        <FileText size={32} className="text-amber-400" />
                                    </div>
                                    <h2 className="text-base font-bold text-white mb-1">Upload Lab Report Photo</h2>
                                    <p className="text-xs text-slate-500 mb-6 max-w-xs">Take a clear photo of your printed lab report or upload from your gallery</p>

                                    <div className="flex gap-3 w-full max-w-xs">
                                        <button onClick={() => cameraInputRef.current?.click()}
                                            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-bold uppercase tracking-wider bg-amber-500/10 border border-amber-500/25 text-amber-300 hover:bg-amber-500/20 transition-all cursor-pointer">
                                            <Camera size={16} /> Take Photo
                                        </button>
                                        <button onClick={() => fileInputRef.current?.click()}
                                            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-xs font-bold uppercase tracking-wider bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 transition-all cursor-pointer">
                                            <ImagePlus size={16} /> Gallery
                                        </button>
                                    </div>

                                    <input ref={cameraInputRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />
                                    <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(e) => handleFile(e.target.files[0])} />

                                    <p className="text-[10px] text-slate-600 mt-5">JPG, PNG • Max 10 MB</p>
                                </div>
                            )}

                            {/* Tips */}
                            <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5">
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2"><Info size={12} /> Tips for best results</h3>
                                <ul className="text-xs text-slate-500 space-y-1">
                                    <li>• Good lighting, avoid shadows</li>
                                    <li>• Place report on a flat surface</li>
                                    <li>• Ensure all values are visible and in focus</li>
                                    <li>• Avoid glare from laminated reports</li>
                                </ul>
                            </div>
                        </motion.div>
                    )}

                    {/* ═══ ANALYZING ═══ */}
                    {phase === 'analyzing' && (
                        <motion.div key="analyzing" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center gap-6 py-16 text-center">
                            {imagePreview && (
                                <div className="w-48 h-32 rounded-xl overflow-hidden border border-white/10 shadow-lg opacity-60">
                                    <img src={imagePreview} alt="Report" className="w-full h-full object-cover" />
                                </div>
                            )}
                            <div className="relative">
                                <div className="absolute inset-[-25px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(245,158,11,0.2) 0%, transparent 60%)', filter: 'blur(20px)' }} />
                                <Loader2 size={48} className="text-amber-400 animate-spin" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white mb-1">Analyzing your lab report...</h3>
                                <p className="text-xs text-slate-500">AI is reading values and interpreting results</p>
                                <p className="text-[10px] text-slate-600 mt-2">This may take 10-20 seconds</p>
                            </div>
                        </motion.div>
                    )}

                    {/* ═══ RESULTS ═══ */}
                    {phase === 'results' && analysisData && (
                        <motion.div key="results" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col gap-5 pb-8">

                            {/* Report type badge */}
                            <div className="flex items-center gap-3">
                                <div className="px-3 py-1.5 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                                    <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">{analysisData.report_type || 'Lab Report'}</span>
                                </div>
                                {analysisData.patient_info && (
                                    <span className="text-xs text-slate-500 truncate">{analysisData.patient_info}</span>
                                )}
                            </div>

                            {/* Urgent findings */}
                            {analysisData.urgent_findings?.length > 0 && (
                                <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20">
                                    <h3 className="text-xs font-bold text-red-400 uppercase tracking-wider mb-2 flex items-center gap-2"><ShieldAlert size={14} /> Urgent Findings</h3>
                                    <ul className="space-y-1">
                                        {analysisData.urgent_findings.map((f, i) => (
                                            <li key={i} className="text-sm text-red-300">• {f}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Results cards */}
                            <div>
                                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Test Results ({analysisData.results?.length || 0})</h3>
                                <div className="flex flex-col gap-2">
                                    {analysisData.results?.map((r, idx) => {
                                        const color = statusColor(r.status);
                                        const isExpanded = expandedIdx === idx;
                                        return (
                                            <button key={idx} onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                                                className="w-full text-left p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.05] transition-all">
                                                <div className="flex items-center justify-between gap-3">
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-bold text-white truncate">{r.test_name}</p>
                                                        <p className="text-xs text-slate-500 mt-0.5">Ref: {r.reference_range}</p>
                                                    </div>
                                                    <div className="flex items-center gap-3 shrink-0">
                                                        <span className="text-base font-bold" style={{ color }}>{r.value} <span className="text-xs font-normal text-slate-500">{r.unit}</span></span>
                                                        <div className="flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider" style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}>
                                                            {statusIcon(r.status)} {statusLabel(r.status)}
                                                        </div>
                                                        {isExpanded ? <ChevronUp size={14} className="text-slate-500" /> : <ChevronDown size={14} className="text-slate-500" />}
                                                    </div>
                                                </div>
                                                {isExpanded && (
                                                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-3 pt-3 border-t border-white/5">
                                                        <p className="text-xs text-slate-400 leading-relaxed mb-2"><span className="text-slate-300 font-semibold">Interpretation: </span>{r.interpretation}</p>
                                                        <p className="text-xs text-cyan-400/80 leading-relaxed"><span className="text-cyan-300 font-semibold">Advice: </span>{r.advice}</p>
                                                    </motion.div>
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Overall Summary */}
                            {analysisData.overall_summary && (
                                <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/5">
                                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Overall Summary</h3>
                                    <p className="text-sm text-slate-300 leading-relaxed">{analysisData.overall_summary}</p>
                                </div>
                            )}

                            {/* Recommendations */}
                            {analysisData.recommendations?.length > 0 && (
                                <div className="p-4 rounded-2xl bg-cyan-500/5 border border-cyan-500/10">
                                    <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-2 flex items-center gap-2"><CheckCircle2 size={12} /> Recommendations</h3>
                                    <ol className="space-y-1.5">
                                        {analysisData.recommendations.map((rec, i) => (
                                            <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                                                <span className="text-cyan-500/60 font-bold text-xs mt-0.5 shrink-0">{i + 1}.</span>
                                                <span>{rec}</span>
                                            </li>
                                        ))}
                                    </ol>
                                </div>
                            )}

                            {/* Disclaimer */}
                            <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/15">
                                <p className="text-xs text-amber-400/80 text-center font-medium">
                                    ⚠️ {analysisData.disclaimer || 'This analysis is for educational purposes only. Please consult your healthcare provider for medical advice.'}
                                </p>
                            </div>

                            {/* Actions */}
                            <button onClick={resetAll} className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl text-sm font-bold tracking-wider uppercase bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 transition-all">
                                <RotateCcw size={16} /> Analyze Another Report
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
