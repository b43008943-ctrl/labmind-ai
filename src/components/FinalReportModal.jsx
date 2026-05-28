import { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Printer, Download, Send, Activity, Brain, Server, ShieldCheck, Award, Microscope } from 'lucide-react';

// Fisher-Yates shuffle utility
const shuffleArray = (arr) => {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
};

export default function FinalReportModal({ isOpen, onClose, reportData, activeSample, sampleType, date, labTechName = "Dr. A. Vance", patientId = "894-XX-A9" }) {

    // Challenge state
    const [selectedAnswer, setSelectedAnswer] = useState(null);
    const [isAnswered, setIsAnswered] = useState(false);
    const [challengeKey, setChallengeKey] = useState(0); // bump to force re-pick

    // Typewriter effect state
    const [displayedInsight, setDisplayedInsight] = useState("");

    useEffect(() => {
        if (!isOpen) return;
        const fullText = reportData?.insight || "Analyzing Morphology...";
        setDisplayedInsight("");
        let i = 0;
        const interval = setInterval(() => {
            setDisplayedInsight(fullText.slice(0, i + 1));
            i++;
            if (i >= fullText.length) clearInterval(interval);
        }, 15);
        return () => clearInterval(interval);
    }, [reportData?.insight, isOpen]);

    // Pick a random challenge from the bank + shuffle options on each open
    const { challenge, shuffledOptions } = useMemo(() => {
        const bank = reportData?.challengeBank;
        if (!bank || bank.length === 0) return { challenge: null, shuffledOptions: [] };
        const picked = bank[Math.floor(Math.random() * bank.length)];
        return { challenge: picked, shuffledOptions: shuffleArray(picked.options) };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [reportData, challengeKey]);

    const isCorrect = selectedAnswer === challenge?.correctAnswer;

    // Reset challenge state when report is closed
    const handleClose = () => {
        setSelectedAnswer(null);
        setIsAnswered(false);
        setChallengeKey(k => k + 1); // force new random question next open
        onClose();
    };
    // Normalize metrics based on sample type
    let metrics = [];
    if (sampleType === 'blood' && reportData) {
        metrics = [
            { label: 'RBC Count', value: reportData.rbc, unit: 'M/mcL', status: reportData.rbcStatus },
            { label: 'WBC Count', value: reportData.wbc, unit: 'K/mcL', status: reportData.wbcStatus },
            { label: 'Hemoglobin', value: reportData.hgb, unit: 'g/dL', status: reportData.hgbStatus },
        ];
    } else if (sampleType === 'urine' && reportData) {
        metrics = [
            { label: 'Appearance', value: reportData.appearance, unit: '', status: reportData.appearance === 'Clear/Pale Yellow' ? 'NORMAL' : 'ABNORMAL' },
            { label: 'pH Level', value: reportData.ph, unit: '', status: reportData.ph === '6.0' ? 'NORMAL' : (reportData.ph === '7.5' ? 'HIGH' : 'LOW') },
            { label: 'Protein', value: reportData.protein, unit: '', status: reportData.protein === 'Negative' ? 'NORMAL' : 'ELEVATED' },
            { label: reportData.findingLabel || 'Finding', value: reportData.finding, unit: '', status: reportData.findingStatus || 'ABNORMAL' },
        ];
    } else if (sampleType === 'parasitology' && reportData) {
        metrics = [
            { label: 'Parasite ID', value: reportData.parasiteId, unit: '', status: reportData.parasiteStatus },
            { label: 'Life Cycle Stage', value: reportData.stage, unit: '', status: reportData.stageStatus },
            { label: 'Pathogenic Status', value: reportData.pathogenic, unit: '', status: reportData.pathogenicStatus },
            { label: 'Density', value: reportData.density, unit: '/HPF', status: reportData.densityStatus },
        ];
    } else if (sampleType === 'biochemistry' && reportData) {
        metrics = [
            { label: reportData.name || 'Analyte', value: reportData.value, unit: reportData.unit || '', range: reportData.range || '', status: reportData.status || 'NORMAL' },
        ];
    } else if (sampleType === 'microbiology' && reportData) {
        metrics = [
            { label: 'Appearance', value: reportData.appearance, unit: '', status: 'OBSERVED' },
            { label: 'Gram Stain', value: reportData.gramStain, unit: '', status: 'OBSERVED' },
            { label: reportData.findingLabel || 'Organism', value: reportData.finding, unit: '', status: reportData.findingStatus || 'CRITICAL' },
        ];
    } else if (sampleType === 'bloodbank' && reportData) {
        metrics = [
            { label: 'ABO/Rh Blood Group', value: reportData.bloodType, unit: '', status: reportData.status }
        ];
    }

    // High res image logic: Use activeSample.microscopeImageUrl if available, else a default
    const imageUrl = activeSample?.microscopeImageUrl || '/4.jpg';

    // Theme logic
    const isViolet = sampleType === 'microbiology';
    const isPink = sampleType === 'bloodbank';
    const isEmerald = sampleType === 'parasitology';
    const isAmber = sampleType === 'urine';
    const isBlue = sampleType === 'biochemistry';
    const isRed = sampleType === 'blood';

    const themeColor = isPink ? 'pink' : (isViolet ? 'violet' : (isRed ? 'red' : (isBlue ? 'blue' : (isAmber ? 'amber' : (isEmerald ? 'emerald' : 'cyan')))));
    const borderColor = isPink ? 'border-pink-500/30' : (isViolet ? 'border-violet-500/30' : (isRed ? 'border-red-500/30' : (isBlue ? 'border-blue-500/30' : (isAmber ? 'border-amber-500/30' : (isEmerald ? 'border-emerald-500/30' : 'border-cyan-500/30')))));
    const textColor = isPink ? 'text-pink-400' : (isViolet ? 'text-violet-400' : (isRed ? 'text-red-400' : (isBlue ? 'text-blue-400' : (isAmber ? 'text-amber-400' : (isEmerald ? 'text-emerald-400' : 'text-cyan-400')))));
    const glowShadow = isPink ? 'shadow-[0_0_15px_rgba(219,39,119,0.5)]' : (isViolet ? 'shadow-[0_0_15px_rgba(139,92,246,0.5)]' : (isRed ? 'shadow-[0_0_15px_rgba(239,68,68,0.5)]' : (isBlue ? 'shadow-[0_0_15px_rgba(59,130,246,0.5)]' : (isAmber ? 'shadow-[0_0_15px_rgba(245,158,11,0.5)]' : (isEmerald ? 'shadow-[0_0_15px_rgba(52,211,153,0.5)]' : 'shadow-[0_0_15px_rgba(34,211,238,0.5)]')))));

    const handleShare = async () => {
        try {
            if (navigator.share) {
                await navigator.share({
                    title: 'Diagnostic Report',
                    text: `Diagnostic Report for Patient ${patientId}`,
                    // Provide a url or file here if supported
                    url: window.location.href,
                });
            } else {
                alert("Sharing is not supported on this device/browser.");
            }
        } catch (error) {
            console.error('Error sharing:', error);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ y: "100%", opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: "100%", opacity: 0 }}
                    transition={{ type: "spring", damping: 30, stiffness: 200, opacity: { duration: 0.2 } }}
                    className="fixed inset-0 z-999 w-screen h-screen bg-slate-950/98 backdrop-blur-3xl flex flex-col font-rajdhani overflow-y-auto no-scrollbar pointer-events-auto"
                >
                    {/* Header */}
                    <header className={`pt-8 pb-6 px-6 md:px-12 border-b ${borderColor} bg-slate-900/50 shrink-0 flex items-center justify-between`}>
                        <div className="flex flex-col">
                            <h1 className="text-2xl md:text-3xl font-black uppercase tracking-widest bg-linear-to-r from-white to-slate-400 bg-clip-text text-transparent flex items-center gap-3">
                                <Activity className={`w-6 h-6 ${textColor} animate-pulse`} />
                                Final Diagnostic Report
                            </h1>
                            <div className="flex gap-6 mt-2 text-xs md:text-sm text-slate-400 font-mono tracking-widest">
                                <span><strong className="text-slate-300">PATIENT ID:</strong> {patientId}</span>
                                <span><strong className="text-slate-300">DATE:</strong> {date || new Date().toLocaleDateString()}</span>
                                <span><strong className="text-slate-300">TECH:</strong> {labTechName}</span>
                            </div>
                        </div>
                        <button
                            onClick={handleClose}
                            className={`w-12 h-12 rounded-full bg-slate-800/80 border border-white/10 flex items-center justify-center text-slate-400 hover:${textColor} hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.5)] hover:bg-slate-700 hover:scale-105 transition-all print:hidden`}
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </header>

                    {/* Main Content Grid */}
                    <main className="w-full max-w-[1400px] mx-auto p-6 md:p-12 pb-24 grid grid-cols-1 lg:grid-cols-12 gap-8">

                        {/* LEFT COLUMN: Microscope View OR Biochemistry Results Table */}
                        <div className="lg:col-span-5 flex flex-col gap-4">
                            {sampleType === 'biochemistry' ? (
                                <>
                                    <h3 className={`text-sm font-bold ${textColor} uppercase tracking-widest flex items-center gap-2`}>
                                        <Server className="w-4 h-4" /> Chemical Analysis Results
                                    </h3>
                                    <div className={`w-full rounded-2xl overflow-hidden border ${borderColor} ${glowShadow} bg-slate-900/80`}>
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-slate-950/50 border-b border-white/10">
                                                    <th className="p-4 text-xs font-bold text-slate-400 uppercase tracking-widest font-mono">Parameter</th>
                                                    <th className="p-4 text-xs font-bold text-slate-400 uppercase tracking-widest font-mono">Patient Value</th>
                                                    <th className="p-4 text-xs font-bold text-slate-400 uppercase tracking-widest font-mono">Ref. Range</th>
                                                    <th className="p-4 text-xs font-bold text-slate-400 uppercase tracking-widest font-mono">Flag</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {metrics.map((m, idx) => {
                                                    const isHigh = m.status === 'HIGH';
                                                    const isBorderline = m.status === 'BORDERLINE';
                                                    const isNormal = m.status === 'NORMAL';
                                                    return (
                                                        <tr key={idx} className="border-b border-white/5 last:border-0 hover:bg-slate-800/30 transition-colors">
                                                            <td className="p-4 text-sm text-white font-medium uppercase tracking-wide">{m.label}</td>
                                                            <td className="p-4 font-mono text-lg">
                                                                <span className={isNormal ? 'text-slate-300' : 'text-white font-bold'}>{m.value}</span>
                                                                {m.unit && <span className="text-xs text-slate-500 ml-1">{m.unit}</span>}
                                                            </td>
                                                            <td className="p-4 font-mono text-sm text-slate-400">{m.range || '—'}</td>
                                                            <td className="p-4">
                                                                <span className={`px-2 py-1 rounded text-[10px] font-bold tracking-widest uppercase ${isHigh ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                                                                    isBorderline ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                                                                        'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                                                    }`}>
                                                                    {m.status}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                        {/* Formula display */}
                                        <div className="p-4 border-t border-white/10 flex items-center justify-center">
                                            <div className="text-[11px] text-blue-300 font-mono tracking-wider bg-black/40 px-4 py-2 rounded-lg border border-blue-500/20">
                                                C = (A<sub>sample</sub> / A<sub>standard</sub>) × C<sub>standard</sub>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : sampleType === 'bloodbank' && reportData ? (
                                <>
                                    <h3 className={`text-sm font-bold ${textColor} uppercase tracking-widest flex items-center gap-2`}>
                                        <ShieldCheck className="w-4 h-4" /> Blood Group Result & Compatibility
                                    </h3>
                                    <div className="flex flex-col gap-4 w-full">
                                        {/* Blood Type Display */}
                                        <div className={`w-full rounded-2xl overflow-hidden border ${borderColor} ${glowShadow} bg-slate-900/80 flex flex-col items-center justify-center p-6 md:p-8 text-center`}>
                                            <span className={`text-xs font-bold ${textColor} uppercase tracking-widest mb-1 opacity-80`}>Determined Type</span>
                                            <span className={`text-4xl md:text-5xl font-bold ${textColor} font-mono drop-shadow-[0_0_15px_rgba(219,39,119,0.5)]`}>
                                                {reportData.bloodType}
                                            </span>
                                        </div>

                                        {/* Compatibility Chart */}
                                        {reportData.compatibility && (
                                            <div className="bg-slate-900/60 border border-pink-500/20 rounded-2xl overflow-hidden shadow-[0_0_15px_rgba(219,39,119,0.1)] flex flex-col pt-2">
                                                <div className="p-4 border-b border-pink-500/10">
                                                    <span className="text-[10px] font-bold text-pink-300 uppercase tracking-widest font-mono block mb-3 opacity-80">Safe to Receive From</span>
                                                    <div className="flex flex-wrap gap-2">
                                                        {reportData.compatibility.receive.map((type, i) => (
                                                            <span key={i} className="px-3 py-1.5 bg-pink-900/40 border border-pink-500/40 text-pink-100 rounded-lg text-xs font-bold tracking-widest shadow-[0_0_10px_rgba(219,39,119,0.2)]">{type}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                                <div className="p-4">
                                                    <span className="text-[10px] font-bold text-pink-300 uppercase tracking-widest font-mono block mb-3 opacity-80">Safe to Donate To</span>
                                                    <div className="flex flex-wrap gap-2">
                                                        {reportData.compatibility.donate.map((type, i) => (
                                                            <span key={i} className="px-3 py-1.5 bg-slate-800 border border-white/10 text-slate-300 rounded-lg text-xs font-bold tracking-widest">{type}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </>
                            ) : sampleType === 'microbiology' && reportData?.antibiogram ? (
                                <div className="flex flex-col w-full">
                                    <h3 className={`text-sm font-bold ${textColor} uppercase tracking-widest flex items-center gap-2 mb-4`}>
                                        <ShieldCheck className="w-4 h-4" /> Antimicrobial Susceptibility Testing (AST)
                                    </h3>
                                    {/* Organism ID banner */}
                                    <div className="bg-violet-950/40 border border-violet-500/20 rounded-xl px-4 py-3 mb-4 flex items-center gap-3">
                                        <span className="w-2.5 h-2.5 rounded-full bg-violet-400 shadow-[0_0_10px_rgba(139,92,246,0.8)]" />
                                        <div>
                                            <span className="text-[9px] text-violet-400/60 uppercase tracking-widest font-mono block">Pathogen Identified</span>
                                            <span className="text-sm font-bold text-white tracking-wide">{reportData.finding || reportData.organism}</span>
                                        </div>
                                        {reportData.gramStain && (
                                            <span className="ml-auto text-[10px] font-mono text-violet-300/70 tracking-wider hidden md:block">{reportData.gramStain}</span>
                                        )}
                                    </div>
                                    <div className="bg-slate-900/60 border border-violet-500/20 rounded-2xl overflow-hidden shadow-[0_0_15px_rgba(139,92,246,0.1)]">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="bg-violet-950/40 border-b border-violet-500/20">
                                                    <th className="p-3 text-[10px] font-bold text-violet-300 uppercase tracking-widest font-mono">Antibiotic Agent</th>
                                                    <th className="p-3 text-[10px] font-bold text-violet-300 uppercase tracking-widest font-mono border-l border-violet-500/10 text-center w-28">MIC (µg/mL)</th>
                                                    <th className="p-3 text-[10px] font-bold text-violet-300 uppercase tracking-widest font-mono border-l border-violet-500/10 text-center w-32">Interpretation</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {reportData.antibiogram.map((drug, idx) => {
                                                    const interp = drug.interpretation || drug.result;
                                                    const isSensitive = interp === 'S';
                                                    const isResistant = interp === 'R';

                                                    return (
                                                        <tr key={idx} className="border-b border-white/5 last:border-0 hover:bg-violet-900/20 transition-colors">
                                                            <td className="p-3 text-sm text-slate-300 font-medium tracking-wide">
                                                                <div className="flex items-center gap-3">
                                                                    {isResistant && <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.8)] shrink-0" />}
                                                                    {isSensitive && <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] shrink-0" />}
                                                                    {!isResistant && !isSensitive && <span className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)] shrink-0" />}
                                                                    {drug.antibiotic}
                                                                </div>
                                                            </td>
                                                            <td className="p-3 border-l border-white/5 text-center">
                                                                <span className="font-mono text-sm text-white font-bold">{drug.mic || '—'}</span>
                                                            </td>
                                                            <td className="p-3 border-l border-white/5 text-center">
                                                                <span className={`inline-block px-2.5 py-1 rounded text-[10px] font-bold tracking-widest uppercase ${isResistant ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                                                                    (isSensitive ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30')
                                                                    }`}>
                                                                    {isResistant ? 'Resistant (R)' : (isSensitive ? 'Sensitive (S)' : 'Intermediate (I)')}
                                                                </span>
                                                            </td>
                                                        </tr>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <h3 className={`text-sm font-bold ${textColor} uppercase tracking-widest flex items-center gap-2`}>
                                        <Server className="w-4 h-4" /> Analyzed Sample Matrix
                                    </h3>
                                    <div className={`relative w-full aspect-square rounded-2xl overflow-hidden border ${borderColor} ${glowShadow} bg-black`}>
                                        <img src={imageUrl} alt="Sample view" className="absolute inset-0 w-full h-full object-cover" />
                                        {/* Scanning Reticle Overlay */}
                                        <div className="absolute inset-0 border border-white/10 pointer-events-none">
                                            <div className="absolute top-4 left-4 w-8 h-8 border-t-2 border-l-2 border-white/50" />
                                            <div className="absolute top-4 right-4 w-8 h-8 border-t-2 border-r-2 border-white/50" />
                                            <div className="absolute bottom-4 left-4 w-8 h-8 border-b-2 border-l-2 border-white/50" />
                                            <div className="absolute bottom-4 right-4 w-8 h-8 border-b-2 border-r-2 border-white/50" />
                                        </div>
                                        {/* Tag */}
                                        <div className="absolute bottom-4 left-4 bg-black/60 backdrop-blur-md px-3 py-1 rounded border border-white/10">
                                            <span className="text-[10px] text-white font-mono tracking-widest uppercase">
                                                ID: {activeSample?.id} | MAG: 100x
                                            </span>
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* RIGHT COLUMN: Results & AI */}
                        <div className="lg:col-span-7 flex flex-col gap-8">

                            {/* Detailed Results Table */}
                            <section>
                                <h3 className={`text-sm font-bold ${textColor} uppercase tracking-widest flex items-center gap-2 mb-4`}>
                                    <Activity className="w-4 h-4" /> Telemetry Results
                                </h3>
                                <div className="bg-slate-900/60 border border-white/5 rounded-2xl overflow-hidden">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="bg-slate-950/50 border-b border-white/10">
                                                <th className="p-4 text-xs font-bold text-slate-400 uppercase tracking-widest font-mono">Parameter</th>
                                                <th className="p-4 text-xs font-bold text-slate-400 uppercase tracking-widest font-mono">Value</th>
                                                <th className="p-4 text-xs font-bold text-slate-400 uppercase tracking-widest font-mono">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {metrics.map((m, idx) => {
                                                const isAbnormal = m.status !== 'NORMAL';
                                                const isCritical = m.status === 'CRITICAL' || m.status === 'WARNING' || m.status === 'LOW' || m.status === 'HIGH';

                                                return (
                                                    <tr key={idx} className="border-b border-white/5 last:border-0 hover:bg-slate-800/30 transition-colors">
                                                        <td className="p-4 text-sm text-slate-300 font-medium uppercase tracking-wide">{m.label}</td>
                                                        <td className="p-4 font-mono text-lg">
                                                            <span className={isAbnormal ? 'text-white font-bold' : 'text-slate-300'}>{m.value}</span>
                                                            {m.unit && <span className="text-xs text-slate-500 ml-1">{m.unit}</span>}
                                                        </td>
                                                        <td className="p-4">
                                                            <span className={`px-2 py-1 rounded text-[10px] font-bold tracking-widest uppercase ${isCritical ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                                                                isAbnormal ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                                                                    'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                                                }`}>
                                                                {m.status}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </section>

                            {/* AI Diagnosis Section */}
                            <section className="flex flex-col md:flex-row gap-6">
                                {/* Insight Box */}
                                <div className={`flex-1 bg-slate-900/80 border ${borderColor} rounded-2xl p-6 relative overflow-hidden group`}>
                                    <div className={`absolute inset-0 bg-linear-to-br from-${themeColor}-900/10 to-transparent opacity-50 pointer-events-none`}></div>
                                    <h4 className={`text-xs font-bold ${textColor} uppercase tracking-widest mb-3 flex items-center gap-2 drop-shadow-[0_0_8px_rgba(255,255,255,0.2)]`}>
                                        <Brain className="w-4 h-4" /> Smart Insight
                                    </h4>
                                    <p className={`font-mono text-sm text-${themeColor}-50 leading-relaxed tracking-wide relative z-10`}>
                                        {displayedInsight}
                                        <span className="animate-pulse">_</span>
                                    </p>
                                </div>

                                {/* Confidence Score Gauge */}
                                <div className="w-full md:w-48 shrink-0 bg-slate-900/60 border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center relative">
                                    <ShieldCheck className={`w-6 h-6 ${textColor} absolute top-4 right-4 opacity-50`} />
                                    <div className="text-4xl font-light text-white font-mono drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]">
                                        {reportData?.confidence ? (
                                            <>
                                                {reportData.confidence.split('.')[0]}
                                                <span className="text-2xl text-slate-400">.{reportData.confidence.split('.')[1]}</span>
                                            </>
                                        ) : (
                                            <>98<span className="text-2xl text-slate-400">.4%</span></>
                                        )}
                                    </div>
                                    <div className="text-[10px] font-bold text-slate-500 tracking-widest uppercase mt-2 text-center">
                                        AI Confidence<br />Score
                                    </div>
                                </div>
                            </section>


                            {/* 🔬 AI DIAGNOSIS CHALLENGE — All Lab Types */}
                            {challenge && (
                                <section className={`bg-slate-900/80 border ${borderColor} rounded-2xl p-6 relative overflow-hidden`}>
                                    <div className={`absolute inset-0 bg-linear-to-br from-${themeColor}-900/10 to-transparent opacity-50 pointer-events-none`}></div>
                                    <h4 className={`text-xs font-bold ${textColor} uppercase tracking-widest mb-4 flex items-center gap-2 drop-shadow-[0_0_8px_rgba(255,255,255,0.3)] relative z-10`}>
                                        <Microscope className="w-4 h-4" /> 🔬 AI Diagnosis Challenge
                                    </h4>
                                    <p className="font-mono text-sm text-blue-50 leading-relaxed tracking-wide mb-5 relative z-10">
                                        {challenge.question}
                                    </p>

                                    <div className="flex flex-col gap-2 relative z-10">
                                        {shuffledOptions.map((option, idx) => {
                                            let btnStyle = `bg-slate-800/60 border-white/10 text-white hover:bg-${themeColor}-500/20 hover:border-${themeColor}-500/40`;
                                            if (isAnswered) {
                                                if (option === challenge.correctAnswer) {
                                                    btnStyle = 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.4)]';
                                                } else if (option === selectedAnswer && !isCorrect) {
                                                    btnStyle = 'bg-red-500/20 border-red-500/50 text-red-300 shadow-[0_0_15px_rgba(239,68,68,0.4)]';
                                                } else {
                                                    btnStyle = 'bg-slate-800/30 border-white/5 text-slate-500';
                                                }
                                            }
                                            return (
                                                <button
                                                    key={idx}
                                                    disabled={isAnswered}
                                                    onClick={() => { setSelectedAnswer(option); setIsAnswered(true); }}
                                                    className={`w-full text-left px-4 py-3 rounded-xl border font-mono text-sm tracking-wide transition-all duration-300 ${btnStyle} ${isAnswered ? 'cursor-default' : 'cursor-pointer'}`}
                                                >
                                                    <span className="text-[10px] text-slate-500 mr-2 font-bold">{String.fromCharCode(65 + idx)}.</span>
                                                    {option}
                                                </button>
                                            );
                                        })}
                                    </div>

                                    {/* Result Feedback */}
                                    <AnimatePresence>
                                        {isAnswered && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 20 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ duration: 0.4, ease: 'easeOut' }}
                                                className={`mt-5 p-4 rounded-xl border relative z-10 ${isCorrect
                                                    ? 'bg-emerald-500/10 border-emerald-500/30'
                                                    : 'bg-red-500/10 border-red-500/30'
                                                    }`}
                                            >
                                                {isCorrect ? (
                                                    <div className="flex items-start gap-3">
                                                        <motion.div
                                                            initial={{ scale: 0, rotate: -30 }}
                                                            animate={{ scale: 1, rotate: 0 }}
                                                            transition={{ type: 'spring', stiffness: 300, damping: 15, delay: 0.2 }}
                                                            className="shrink-0"
                                                        >
                                                            <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/50 flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.5)]">
                                                                <Award className="w-5 h-5 text-emerald-400" />
                                                            </div>
                                                        </motion.div>
                                                        <div>
                                                            <p className="text-emerald-400 font-bold text-xs uppercase tracking-widest mb-1">✓ Correct — Diagnosis Confirmed</p>
                                                            <p className="text-emerald-200/80 text-xs font-mono leading-relaxed">{challenge.explanation}</p>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <div>
                                                        <p className="text-red-400 font-bold text-xs uppercase tracking-widest mb-1">✗ Incorrect — Review Required</p>
                                                        <p className="text-red-200/80 text-xs font-mono leading-relaxed mb-2">
                                                            Correct answer: <span className="text-emerald-400 font-bold">{challenge.correctAnswer}</span>
                                                        </p>
                                                        <p className="text-slate-300/80 text-xs font-mono leading-relaxed">{challenge.explanation}</p>
                                                    </div>
                                                )}
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </section>
                            )}
                        </div>

                        {/* Action Buttons */}
                        <section className="col-span-1 lg:col-span-12 flex flex-wrap items-center justify-start gap-4 mt-6 pt-4 print:hidden">
                            <button onClick={() => window.print()} className={`min-w-[160px] h-12 rounded-xl bg-slate-800 border ${borderColor} flex items-center justify-center gap-2 text-white font-bold tracking-widest uppercase text-xs hover:bg-slate-700 ${glowShadow} transition-all`}>
                                <Printer className={`w-4 h-4 ${textColor}`} /> Print Report
                            </button>
                            <button onClick={() => window.print()} className={`min-w-[160px] h-12 rounded-xl bg-slate-800 border ${borderColor} flex items-center justify-center gap-2 text-white font-bold tracking-widest uppercase text-xs hover:bg-slate-700 transition-all`}>
                                <Download className={`w-4 h-4 ${textColor}`} /> Export PDF
                            </button>
                            <button onClick={handleShare} className={`min-w-[160px] h-12 rounded-xl bg-slate-800 border ${borderColor} flex items-center justify-center gap-2 text-white font-bold tracking-widest uppercase text-xs hover:bg-slate-700 transition-all`}>
                                <Send className={`w-4 h-4 ${textColor}`} /> Share to Physician
                            </button>
                        </section>

                        {/* Footer / Signature Pad (Now inside normal scroll flow) */}
                        <footer className="col-span-1 lg:col-span-12 mt-16 pb-10 border-t border-white/10 pt-6 flex flex-col md:flex-row justify-between items-center gap-6">
                            <div className="text-[10px] text-slate-500 font-mono tracking-widest uppercase">
                                <p>POWERED BY CHANGE INTELLIGENCE</p>
                                <p className="mt-1">SYS-ID: 9942-A | REPORT GENERATED SECURELY</p>
                            </div>

                            <div className="flex flex-col items-end">
                                <div className="w-48 h-10 border-b border-slate-600 relative overflow-hidden">
                                    {/* Animated signature path */}
                                    <svg viewBox="0 0 100 30" className="absolute bottom-1 w-full h-full opacity-80">
                                        <motion.path
                                            initial={{ pathLength: 0 }}
                                            animate={{ pathLength: 1 }}
                                            transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
                                            d="M 10 20 C 20 10, 30 30, 40 15 S 60 25, 70 10 S 80 20, 90 15"
                                            fill="transparent"
                                            stroke={themeColor === 'red' ? '#ef4444' : (themeColor === 'blue' ? '#3b82f6' : (themeColor === 'amber' ? '#f59e0b' : (themeColor === 'emerald' ? '#10b981' : '#00f2ff')))}
                                            strokeWidth="1.5"
                                            className={glowShadow}
                                        />
                                    </svg>
                                </div>
                                <span className="text-[10px] text-slate-400 font-bold tracking-widest uppercase mt-2">
                                    Attending Technician Signature
                                </span>
                            </div>
                        </footer>

                    </main>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
