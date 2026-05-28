import { motion, AnimatePresence } from 'framer-motion';
import { X, Printer, Download, Send, Activity, Brain, Server, ShieldCheck } from 'lucide-react';

export default function DiagnosticReportScreen({ isOpen, onClose, reportData, activeSample, sampleType, date, labTechName = "Dr. A. Vance", patientId = "894-XX-A9" }) {

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
    }

    // High res image logic: Use activeSample.microscopeImageUrl if available, else a default
    const imageUrl = activeSample?.microscopeImageUrl || '/4.jpg';

    // Theme logic
    const themeColor = sampleType === 'blood' ? 'cyan' : (sampleType === 'parasitology' ? 'emerald' : 'amber');
    const borderColor = sampleType === 'blood' ? 'border-cyan-500/30' : (sampleType === 'parasitology' ? 'border-emerald-500/30' : 'border-amber-500/30');
    const textColor = sampleType === 'blood' ? 'text-cyan-400' : (sampleType === 'parasitology' ? 'text-emerald-400' : 'text-amber-400');
    const glowShadow = sampleType === 'blood' ? 'shadow-[0_0_15px_rgba(34,211,238,0.5)]' : (sampleType === 'parasitology' ? 'shadow-[0_0_15px_rgba(52,211,153,0.5)]' : 'shadow-[0_0_15px_rgba(245,158,11,0.5)]');

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ y: "100%", opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: "100%", opacity: 0 }}
                    transition={{ type: "spring", damping: 30, stiffness: 200, opacity: { duration: 0.2 } }}
                    className="fixed inset-0 z-999 w-screen h-screen bg-slate-950/95 backdrop-blur-3xl flex flex-col font-rajdhani overflow-y-auto no-scrollbar pointer-events-auto"
                >
                    {/* Header */}
                    <header className={`shrink-0 flex items-center justify-between p-6 md:px-12 border-b ${borderColor} bg-slate-900/50`}>
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
                            onClick={onClose}
                            className="w-12 h-12 rounded-full bg-slate-800/80 border border-white/10 flex items-center justify-center text-slate-400 hover:text-cyan-400 hover:drop-shadow-[0_0_8px_rgba(34,211,238,0.8)] hover:bg-slate-700 hover:scale-105 transition-all print:hidden"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </header>

                    {/* Main Content Grid */}
                    <main className="flex-1 p-6 md:p-12 w-full max-w-[1400px] mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">

                        {/* LEFT COLUMN: Microscope View */}
                        <div className="lg:col-span-5 flex flex-col gap-4">
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
                                    <div className="absolute inset-0 bg-linear-to-br from-cyan-900/10 to-transparent opacity-50 pointer-events-none"></div>
                                    <h4 className={`text-xs font-bold ${textColor} uppercase tracking-widest mb-3 flex items-center gap-2 drop-shadow-[0_0_8px_rgba(34,211,238,0.5)]`}>
                                        <Brain className="w-4 h-4" /> Smart Insight
                                    </h4>
                                    <p className="font-mono text-sm text-cyan-50 leading-relaxed tracking-wide relative z-10">
                                        {reportData?.insight || "Analysis complete. No critical insights generated."}
                                    </p>
                                </div>

                                {/* Confidence Score Gauge */}
                                <div className="w-full md:w-48 shrink-0 bg-slate-900/60 border border-white/10 rounded-2xl p-6 flex flex-col items-center justify-center relative">
                                    <ShieldCheck className="w-6 h-6 text-emerald-400 absolute top-4 right-4 opacity-50" />
                                    <div className="text-4xl font-light text-white font-mono drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]">
                                        98<span className="text-2xl text-slate-400">.4%</span>
                                    </div>
                                    <div className="text-[10px] font-bold text-slate-500 tracking-widest uppercase mt-2 text-center">
                                        AI Confidence<br />Score
                                    </div>
                                </div>
                            </section>

                            {/* Action Buttons */}
                            <section className="flex flex-wrap items-center gap-4 mt-auto pt-4 print:hidden">
                                <button onClick={() => window.print()} className={`flex-1 md:flex-none min-w-[160px] h-12 rounded-xl bg-slate-800 border ${borderColor} flex items-center justify-center gap-2 text-white font-bold tracking-widest uppercase text-xs hover:bg-slate-700 ${glowShadow} transition-all`}>
                                    <Printer className={`w-4 h-4 ${textColor}`} /> Print Report
                                </button>
                                <button onClick={() => window.print()} className={`flex-1 md:flex-none min-w-[160px] h-12 rounded-xl bg-slate-800 border ${borderColor} flex items-center justify-center gap-2 text-white font-bold tracking-widest uppercase text-xs hover:bg-slate-700 transition-all`}>
                                    <Download className={`w-4 h-4 ${textColor}`} /> Export PDF
                                </button>
                                <button className={`flex-1 md:flex-none min-w-[160px] h-12 rounded-xl bg-slate-800 border ${borderColor} flex items-center justify-center gap-2 text-white font-bold tracking-widest uppercase text-xs hover:bg-slate-700 transition-all`}>
                                    <Send className={`w-4 h-4 ${textColor}`} /> Share to Physician
                                </button>
                            </section>

                        </div>

                    </main>

                    {/* Footer / Signature Pad */}
                    <footer className="mt-auto shrink-0 p-6 md:px-12 border-t border-white/10 bg-black/40 flex flex-col md:flex-row justify-between items-center gap-6">
                        <div className="text-[10px] text-slate-500 font-mono tracking-widest uppercase">
                            <p>POWERED BY CHANGE INTELLIGENCE</p>
                            <p className="mt-1">SYS-ID: 9942-A | REPORT GENERATED SECURELY</p>
                        </div>

                        <div className="flex flex-col items-end">
                            <div className="w-48 h-10 border-b border-slate-600 relative">
                                {/* Faux signature path using simple SVG */}
                                <svg viewBox="0 0 100 30" className="absolute bottom-1 w-full h-full opacity-70">
                                    <path d="M 10 20 C 20 10, 30 30, 40 15 S 60 25, 70 10 S 80 20, 90 15" fill="transparent" stroke="cyan" strokeWidth="1" className="drop-shadow-[0_0_2px_rgba(34,211,238,0.8)]" />
                                </svg>
                            </div>
                            <span className="text-[10px] text-slate-400 font-bold tracking-widest uppercase mt-2">
                                Attending Technician Signature
                            </span>
                        </div>
                    </footer>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
