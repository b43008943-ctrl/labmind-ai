import { useState, useRef, useEffect } from 'react';
import { ArrowLeft, Brain, CheckCircle2, CloudUpload, FileText, Activity, Cpu, BookOpen, BadgeCheck, ArrowUpRight, RotateCcw, Save, Share2 } from 'lucide-react';

export default function AnalysisHubScreen({ onNavigate }) {
    const [screenState, setScreenState] = useState('screen-transition-hidden');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [showResults, setShowResults] = useState(false);
    const [files, setFiles] = useState([]);
    const fileInputRef = useRef(null);

    useEffect(() => {
        const t = setTimeout(() => setScreenState('screen-visible'), 50);
        return () => clearTimeout(t);
    }, []);

    const handleNavigation = (target) => {
        setScreenState('screen-exit');
        setTimeout(() => onNavigate(target), 600);
    };

    const handleFileUpload = (selectedFiles) => {
        if (!selectedFiles || selectedFiles.length === 0) return;

        const newFiles = Array.from(selectedFiles).map(f => ({
            name: f.name,
            size: (f.size / 1024).toFixed(1) + ' KB',
            ext: f.name.split('.').pop().toUpperCase()
        }));
        setFiles(newFiles);

        setIsAnalyzing(true);
        setShowResults(false);

        setTimeout(() => {
            setIsAnalyzing(false);
            setShowResults(true);
        }, 3500);
    };

    const onDragOver = (e) => {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over', 'border-purple-500/70', 'bg-purple-500/10');
    };

    const onDragLeave = (e) => {
        e.currentTarget.classList.remove('drag-over', 'border-purple-500/70', 'bg-purple-500/10');
    };

    const onDrop = (e) => {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over', 'border-purple-500/70', 'bg-purple-500/10');
        if (e.dataTransfer.files) {
            handleFileUpload(e.dataTransfer.files);
        }
    };

    return (
        <div id="analysis-hub-screen" className={`absolute inset-0 z-30 flex flex-col bg-transparent backdrop-blur-sm overflow-y-auto ${screenState}`} style={{ WebkitOverflowScrolling: 'touch' }}>
            <div className="w-full h-full max-w-5xl mx-auto flex flex-col relative shadow-2xl ring-1 ring-white/5">

                {/* Header */}
                <header className="pt-10 pb-4 px-6 flex justify-between items-center border-b border-white/5 bg-linear-to-b from-cyan-900/10 to-transparent">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => handleNavigation('dashboard')}
                            className="btn-back-glow w-10 h-10 rounded-xl flex items-center justify-center text-cyan-300 hover:text-white transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2 theme-text">
                                <span className="text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]">
                                    <Brain className="w-5 h-5 inline" />
                                </span>
                                Change Intelligence Center
                                <CheckCircle2 className={`w-5 h-5 text-green-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.8)] transition-opacity duration-300 ml-2 ${showResults ? 'opacity-100' : 'opacity-0 hidden'}`} />
                            </h2>
                            <p className="text-[10px] text-gray-400 mt-0.5 theme-text-muted">Advanced AI-driven analysis for tracking biological change</p>
                        </div>
                    </div>
                </header>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto no-scrollbar p-6 flex flex-col gap-6">

                    {!isAnalyzing && !showResults && (
                        <div
                            id="upload-drop-zone"
                            onClick={() => fileInputRef.current?.click()}
                            onDragOver={onDragOver}
                            onDragLeave={onDragLeave}
                            onDrop={onDrop}
                            className="drop-zone rounded-2xl p-8 flex flex-col items-center justify-center text-center min-h-[220px]"
                        >
                            <div className="upload-icon w-16 h-16 rounded-2xl bg-purple-500/10 flex items-center justify-center mb-4">
                                <CloudUpload className="w-8 h-8 text-purple-400 drop-shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
                            </div>
                            <h3 className="text-sm font-bold text-white mb-1">Drop your data files here</h3>
                            <p className="text-[11px] text-gray-400 mb-4">Supports Images (PNG, JPG), CSV, JSON, XLSX &bull; Max 50 MB</p>
                            <button className="px-5 py-2 rounded-xl text-xs font-semibold text-purple-300 border border-purple-500/30 bg-purple-500/5 hover:bg-purple-500/15 hover:border-purple-400 transition-all duration-200 shadow-[0_0_15px_rgba(168,85,247,0.1)] hover:shadow-[0_0_20px_rgba(168,85,247,0.25)]">
                                Browse Files
                            </button>
                            <input
                                type="file"
                                ref={fileInputRef}
                                className="hidden"
                                accept=".csv,.json,.xlsx,.xls,.png,.jpg,.jpeg"
                                multiple
                                onChange={e => handleFileUpload(e.target.files)}
                            />
                        </div>
                    )}

                    {isAnalyzing && (
                        <div
                            className="flex flex-col items-center justify-center min-h-[300px] opacity-0"
                            style={{ animation: 'fadeIn 0.8s ease-out forwards' }}
                        >
                            <div className="relative w-48 h-48 rounded-full border border-cyan-500/30 bg-cyan-900/10 flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(0,242,255,0.2)]">
                                <div className="absolute inset-0 rounded-full border-4 border-t-cyan-400 border-r-cyan-400 border-b-transparent border-l-transparent animate-spin"></div>
                                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,242,255,0.1)_0,transparent_70%)] rounded-full animate-pulse"></div>
                                <div className="relative w-20 h-20 bg-cyan-500/20 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(0,242,255,0.5)]">
                                    <div className="w-10 h-10 bg-cyan-400 animate-pulse drop-shadow-[0_0_10px_#00f2ff]" style={{ clipPath: 'polygon(35% 0, 65% 0, 65% 35%, 100% 35%, 100% 65%, 65% 65%, 65% 100%, 35% 100%, 35% 65%, 0 65%, 0 35%, 35% 35%)' }}></div>
                                </div>
                            </div>
                            <h3 className="text-sm font-bold text-cyan-300 tracking-widest uppercase animate-pulse mb-2 text-center">LabMind AI is scanning documents</h3>
                            <p className="text-xs text-cyan-400/80 font-mono text-center animate-pulse">and cross-referencing global databases...</p>
                        </div>
                    )}

                    {(isAnalyzing || showResults) && (
                        <div className="opacity-0" style={{ animation: 'fadeIn 0.8s ease-out forwards' }}>
                            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3">Uploaded Files</p>
                            <div className="flex flex-col gap-2">
                                {files.map((file, i) => (
                                    <div key={i} className="file-item px-4 py-3 flex items-center gap-3 bg-white/5 border border-white/10 rounded-xl">
                                        <div className="w-8 h-8 rounded-lg bg-neon-blue/15 flex items-center justify-center">
                                            <FileText className="w-4 h-4 text-neon-blue" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-semibold text-white truncate">{file.name}</p>
                                            <p className="text-[10px] text-gray-500">{file.ext} &bull; {file.size}</p>
                                        </div>
                                        <div className="w-5 h-5 rounded-full bg-green-500/15 flex items-center justify-center">
                                            <CheckCircle2 className="w-3 h-3 text-green-400" />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {showResults && (
                        <div
                            className="flex flex-col gap-6 opacity-0"
                            style={{ animation: 'fadeInUp 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards' }}
                        >
                            <h3 className="text-lg font-bold text-white flex items-center gap-2 mt-4">
                                <Activity className="w-5 h-5 text-neon-blue" />
                                Change Results
                            </h3>

                            {/* Chart */}
                            <div className="glass-panel p-6 rounded-2xl flex flex-col border-t border-green-500/30">
                                <div className="flex justify-between items-end mb-4">
                                    <h4 className="text-base font-bold text-white">Biological Change Tracking</h4>
                                    <span className="text-xs font-bold text-green-400 drop-shadow-[0_0_5px_rgba(16,185,129,0.8)] px-2 py-1 bg-green-500/10 rounded-md border border-green-500/20">TREND: STABLE</span>
                                </div>
                                <div className="w-full h-32 flex items-end justify-center relative bg-obsidian/40 rounded-xl border border-white/5 p-4 overflow-hidden">
                                    <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-size-[20px_20px]"></div>
                                    <svg className="w-full h-full relative z-10" preserveAspectRatio="none" viewBox="0 0 100 40">
                                        <path d="M0 35 Q 20 38 40 25 T 60 28 T 80 15 T 100 10" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="drop-shadow-[0_0_8px_rgba(16,185,129,0.8)]" />
                                        <circle cx="40" cy="25" r="1.5" fill="#fff" className="drop-shadow-[0_0_5px_#fff]" />
                                        <circle cx="60" cy="28" r="1.5" fill="#fff" className="drop-shadow-[0_0_5px_#fff]" />
                                        <circle cx="80" cy="15" r="1.5" fill="#fff" className="drop-shadow-[0_0_5px_#fff]" />
                                        <circle cx="100" cy="10" r="2.5" fill="#10b981" stroke="#fff" strokeWidth="0.5" className="drop-shadow-[0_0_8px_rgba(16,185,129,1)]" />
                                    </svg>
                                </div>
                                <p className="text-[10px] text-gray-400 uppercase tracking-widest font-bold mt-3 text-right">Biological Change Baseline: Nominal</p>
                            </div>

                            {/* AI Insight */}
                            <div className="glass-panel p-6 rounded-2xl flex flex-col border-t border-cyan-500/30">
                                <h4 className="text-xs font-bold text-cyan-300 uppercase tracking-widest mb-3 flex items-center gap-2">
                                    <Cpu className="w-4 h-4" /> AI Diagnosis Summary
                                </h4>
                                <p className="text-sm text-gray-300 leading-relaxed font-mono">
                                    &gt; Analyzing full-spectrum biological ledger...<br />
                                    &gt; Cellular structure integrity verified.<br />
                                    &gt; No abnormal deviations detected in <span className="text-white font-bold bg-cyan-900/40 px-1 rounded">Change</span> metrics over the last 72 hours.<br />
                                    &gt; <span className="text-green-400 font-bold drop-shadow-[0_0_5px_rgba(16,185,129,0.6)]">STATUS: PATIENT CLEARED.</span>
                                </p>
                            </div>

                            {/* Scientific Evidence */}
                            <div className="glass-panel p-6 rounded-2xl flex flex-col border-t border-blue-500/30">
                                <h4 className="text-xs font-bold text-blue-300 uppercase tracking-widest mb-4 flex items-center gap-2">
                                    <BookOpen className="w-4 h-4" /> Scientific Evidence
                                </h4>
                                <div className="bg-obsidian/60 border border-white/5 rounded-xl p-4 relative overflow-hidden group hover:border-blue-500/30 transition-colors duration-300">
                                    <div className="absolute right-4 top-4">
                                        <BadgeCheck className="w-5 h-5 text-blue-400 drop-shadow-[0_0_5px_rgba(59,130,246,0.8)]" />
                                    </div>
                                    <h5 className="text-sm font-bold text-white mb-1 pr-8 group-hover:text-blue-200 transition-colors">The Lancet Oncology: Patterns of Cellular Change</h5>
                                    <p className="text-[10px] text-gray-500 font-mono mb-3">Ref: DOI 10.1016/S1470-2045</p>
                                    <p className="text-xs text-gray-300 leading-relaxed border-l-2 border-blue-500/50 pl-3">
                                        Validation Note: The detected <span className="text-white font-bold bg-blue-900/40 px-1 rounded">Change</span> in baseline cellular structure perfectly aligns with established medical benchmarks for stability. No anomalous bio-signatures present.
                                    </p>
                                    <div className="mt-4 pt-4 border-t border-white/5 flex justify-end">
                                        <button className="text-xs font-bold text-blue-400 hover:text-white flex items-center gap-1 transition-colors drop-shadow-[0_0_5px_rgba(59,130,246,0.3)] hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">
                                            READ FULL STUDY <ArrowUpRight className="w-3 h-3" />
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex justify-between items-center mt-2 border-t border-white/5 pt-6 pb-2">
                                <button
                                    onClick={() => { setIsAnalyzing(false); setShowResults(false); setFiles([]); }}
                                    className="px-5 py-2.5 rounded-xl text-sm font-semibold text-gray-400 border border-white/10 bg-white/5 hover:bg-white/10 hover:text-white transition-all duration-300 group flex items-center gap-2"
                                >
                                    <RotateCcw className="w-4 h-4 group-hover:-rotate-180 transition-transform duration-500" /> New File
                                </button>

                                <div className="flex gap-4">
                                    <button className="hidden sm:flex px-6 py-2.5 rounded-xl text-sm font-semibold text-cyan-300 border border-cyan-500/40 bg-cyan-500/10 hover:bg-cyan-500/20 hover:border-cyan-400 transition-all duration-300 shadow-[0_0_15px_rgba(0,242,255,0.15)] items-center gap-2">
                                        <Save className="w-4 h-4" /> SAVE REPORT
                                    </button>
                                    <button className="px-6 py-2.5 rounded-xl text-sm font-bold text-white border border-purple-500/60 bg-linear-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 transition-all duration-300 shadow-[0_0_20px_rgba(124,58,237,0.4)] flex items-center gap-2">
                                        <Share2 className="w-4 h-4" /> SHARE DATA
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
}
