import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Hexagon, Activity, RefreshCw, FileText, Play } from 'lucide-react';
import FinalReportModal from '../components/FinalReportModal';
import SidebarNavigation from '../components/SidebarNavigation';
import DigitalAnalyzerView from '../components/DigitalAnalyzerView';
import { motion, AnimatePresence } from 'framer-motion';


const samples = [
    {
        id: 'bio-fbs', name: 'Fasting Blood Sugar', desc: 'FBS — Glucose Oxidase Method',
        colorClass: 'bg-blue-400/60', absorbance: 0.452, wavelength: 505,
        value: '126', unit: 'mg/dL', range: '70–100', status: 'HIGH',
        reagentAbs: '0.452', curveType: 'Linear',
        finding: 'Elevated fasting glucose — pre-diabetic range',
        insight: 'Fasting blood sugar of 126 mg/dL exceeds the normal threshold of 100 mg/dL. This falls in the pre-diabetic range (100–125 mg/dL is impaired fasting glucose, ≥126 mg/dL suggests diabetes). Recommend HbA1c and oral glucose tolerance test for confirmation.',
        challengeBank: [
            { question: 'Based on a fasting glucose of 126 mg/dL, what is the clinical classification?', options: ['Normal', 'Prediabetic', 'Diabetic'], correctAnswer: 'Diabetic', explanation: 'Fasting glucose ≥ 126 mg/dL on two separate tests indicates Diabetes Mellitus, per ADA diagnostic criteria.' },
            { question: 'What is the primary hormone responsible for lowering blood glucose levels?', options: ['Glucagon', 'Insulin', 'Cortisol'], correctAnswer: 'Insulin', explanation: 'Insulin, produced by pancreatic beta cells, facilitates cellular uptake of glucose and lowers blood sugar.' },
            { question: 'Which test reflects the average blood glucose over the past 3 months?', options: ['HbA1c', 'Fasting Glucose', 'Oral Glucose Tolerance'], correctAnswer: 'HbA1c', explanation: 'HbA1c measures glycated hemoglobin over the RBC lifespan (~120 days), reflecting average glycemic control.' }
        ]
    },
    {
        id: 'bio-chol', name: 'Cholesterol', desc: 'Lipid Profile — CHOD-PAP Method',
        colorClass: 'bg-cyan-400/60', absorbance: 0.318, wavelength: 500,
        value: '185', unit: 'mg/dL', range: '<200', status: 'NORMAL',
        reagentAbs: '0.318', curveType: 'Linear',
        finding: 'Within desirable total cholesterol range',
        insight: 'Total cholesterol at 185 mg/dL is within the desirable range (<200 mg/dL). No immediate intervention required. Recommend full lipid panel (HDL, LDL, TG) for comprehensive cardiovascular risk assessment.',
        challengeBank: [
            { question: 'A total cholesterol of 185 mg/dL is classified under which category?', options: ['Desirable', 'Borderline High', 'High'], correctAnswer: 'Desirable', explanation: 'Total cholesterol < 200 mg/dL is classified as "Desirable" per NCEP ATP III guidelines.' },
            { question: 'Which lipoprotein is known as "bad cholesterol"?', options: ['HDL', 'LDL', 'VLDL'], correctAnswer: 'LDL', explanation: 'LDL (low-density lipoprotein) deposits cholesterol in arterial walls, increasing atherosclerosis risk.' },
            { question: 'What is the recommended first-line treatment for high cholesterol?', options: ['Statins', 'Aspirin', 'ACE Inhibitors'], correctAnswer: 'Statins', explanation: 'Statins (HMG-CoA reductase inhibitors) are the gold standard for lowering LDL cholesterol and reducing cardiovascular risk.' }
        ]
    },
    {
        id: 'bio-creat', name: 'Creatinine', desc: 'Renal Function — Jaffé Kinetic Method',
        colorClass: 'bg-blue-300/60', absorbance: 0.287, wavelength: 510,
        value: '1.1', unit: 'mg/dL', range: '0.7–1.3', status: 'NORMAL',
        reagentAbs: '0.287', curveType: 'Kinetic',
        finding: 'Normal renal clearance indicated',
        insight: 'Serum creatinine of 1.1 mg/dL is within normal reference range (0.7–1.3 mg/dL). Estimated GFR is adequate. No evidence of renal impairment at this time.',
        challengeBank: [
            { question: 'Serum creatinine of 1.1 mg/dL in an adult male most likely indicates:', options: ['Renal Failure', 'Normal Kidney Function', 'Dehydration'], correctAnswer: 'Normal Kidney Function', explanation: 'Serum creatinine of 0.7–1.3 mg/dL is within the normal adult male range, indicating adequate glomerular filtration.' },
            { question: 'What does GFR (Glomerular Filtration Rate) directly measure?', options: ['Blood pressure in the kidneys', 'Volume of filtrate per minute', 'Urine concentration'], correctAnswer: 'Volume of filtrate per minute', explanation: 'GFR measures the volume of plasma filtered by the glomeruli per minute, indicating overall kidney function.' },
            { question: 'Creatinine is a byproduct of which metabolic process?', options: ['Protein digestion', 'Muscle creatine phosphate metabolism', 'Fat oxidation'], correctAnswer: 'Muscle creatine phosphate metabolism', explanation: 'Creatinine is produced from the spontaneous, non-enzymatic breakdown of creatine phosphate in muscle tissue.' }
        ]
    },
    {
        id: 'bio-alt', name: 'ALT (SGPT)', desc: 'Liver Function — IFCC Kinetic UV',
        colorClass: 'bg-cyan-300/60', absorbance: 0.534, wavelength: 340,
        value: '55', unit: 'U/L', range: '7–56', status: 'BORDERLINE',
        reagentAbs: '0.534', curveType: 'Kinetic',
        finding: 'Upper limit of normal — monitor hepatic function',
        insight: 'ALT at 55 U/L is at the high end of the reference range (7–56 U/L). While not overtly pathological, serial monitoring is recommended. Consider hepatic panel and rule out fatty liver disease or medication-related hepatotoxicity.',
        challengeBank: [
            { question: 'An ALT of 55 U/L (range 7–56) should prompt which action?', options: ['No action needed', 'Serial monitoring & hepatic panel', 'Immediate liver biopsy'], correctAnswer: 'Serial monitoring & hepatic panel', explanation: 'ALT at the upper limit warrants serial monitoring and a full hepatic panel to rule out fatty liver or drug-induced hepatotoxicity.' },
            { question: 'ALT is most specific for damage to which organ?', options: ['Heart', 'Liver', 'Kidney'], correctAnswer: 'Liver', explanation: 'ALT (alanine aminotransferase) is found predominantly in hepatocytes and is the most liver-specific enzyme marker.' },
            { question: 'Which condition is the most common cause of mildly elevated ALT worldwide?', options: ['Hepatitis C', 'Non-Alcoholic Fatty Liver Disease (NAFLD)', 'Gallstones'], correctAnswer: 'Non-Alcoholic Fatty Liver Disease (NAFLD)', explanation: 'NAFLD is the most prevalent liver disease globally and the leading cause of mild-to-moderate ALT elevation.' }
        ]
    }
];

export default function BiochemistryLabScreen({ onNavigate }) {
    const [screenState, setScreenState] = useState('screen-transition-hidden');
    const [activeSample, setActiveSample] = useState(null);
    const [isReportOpen, setIsReportOpen] = useState(false);
    const [report, setReport] = useState(null);
    const [reportStatus, setReportStatus] = useState(null);

    // Incubation timer state
    const [isRunning, setIsRunning] = useState(false);
    const [progress, setProgress] = useState(0);
    const [telemetryLog, setTelemetryLog] = useState([]);
    const timerRef = useRef(null);

    useEffect(() => {
        const t = setTimeout(() => setScreenState('screen-visible'), 50);
        return () => clearTimeout(t);
    }, []);

    const handleNavigation = (target) => {
        setScreenState('screen-exit');
        setTimeout(() => onNavigate(target), 600);
    };

    const selectSample = (sample) => {
        // Just select; don't run assay yet
        if (isRunning) return; // Block during run
        setActiveSample(sample);
        setReport(null);
        setReportStatus(null);
        setProgress(0);
        setTelemetryLog([]);
    };

    const runAssay = () => {
        if (!activeSample || isRunning) return;
        setIsRunning(true);
        setProgress(0);
        setReportStatus('scanning');
        setTelemetryLog([]);

        const startTime = Date.now();
        const duration = 3000; // 3 seconds

        // Telemetry log sequence
        setTimeout(() => setTelemetryLog(prev => [...prev, '> Photometer Calibration: OK.']), 300);
        setTimeout(() => setTelemetryLog(prev => [...prev, `> Reagent Absorbance: ${activeSample.reagentAbs} A.`]), 900);
        setTimeout(() => setTelemetryLog(prev => [...prev, `> Reaction Curve: ${activeSample.curveType}.`]), 1600);
        setTimeout(() => setTelemetryLog(prev => [...prev, `> Reading at ${activeSample.wavelength}nm...`]), 2200);

        timerRef.current = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const pct = Math.min(100, (elapsed / duration) * 100);
            setProgress(pct);

            if (elapsed >= duration) {
                clearInterval(timerRef.current);
                setIsRunning(false);
                setProgress(100);
                setTelemetryLog(prev => [...prev, `> Result: ${activeSample.value} ${activeSample.unit} — ${activeSample.status}.`]);
                setReport(activeSample);
                setReportStatus('ready');
            }
        }, 50);
    };

    useEffect(() => {
        return () => { if (timerRef.current) clearInterval(timerRef.current); };
    }, []);

    return (
        <div id="biochemistry-lab-screen" className={`absolute inset-0 z-40 flex flex-col backdrop-blur-3xl min-h-dvh w-full overflow-y-auto overflow-x-hidden scroll-smooth pb-32 ${screenState}`}>
            <div className="w-full h-full max-w-7xl mx-auto flex flex-col relative shadow-2xl ring-1 ring-white/5">

                {/* Header */}
                <header className="pt-6 md:pt-8 pb-3 px-4 md:px-6 flex justify-between items-center border-b border-white/5 bg-linear-to-b from-blue-900/10 to-transparent shrink-0">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => handleNavigation('virtual-lab')}
                            className="btn-back-glow w-8 h-8 rounded-lg flex items-center justify-center text-blue-300 hover:text-cyan-400 hover:drop-shadow-[0_0_8px_rgba(6,182,212,0.8)] transition-all"
                        >
                            <ArrowLeft className="w-4 h-4" />
                        </button>
                        <div>
                            <h2 className="text-base md:text-lg font-bold text-white tracking-tight flex items-center gap-2">
                                <span className="text-blue-400 drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]">
                                    <Hexagon className="w-4 h-4 inline" />
                                </span>
                                <span className="theme-text">Clinical Biochemistry</span>
                            </h2>
                            <p className="text-[9px] text-gray-400 mt-0.5 theme-text-muted">Digital Spectrometer — Photometric Enzyme Analysis</p>
                        </div>
                    </div>
                </header>

                <SidebarNavigation onNavigate={handleNavigation} />

                {/* Main Lab Workspace */}
                <div className={`flex-1 flex-col md:flex-row overflow-visible p-4 md:p-6 gap-6 md:gap-8 ${isReportOpen ? 'hidden' : 'flex'}`}>

                    {/* LEFT: Digital Analyzer */}
                    <div className="flex-1 flex flex-col items-center gap-4">
                        <DigitalAnalyzerView
                            activeSample={activeSample}
                            isRunning={isRunning}
                            progress={progress}
                        />

                        {/* Bottom Controls */}
                        <div className="shrink-0 h-12 rounded-2xl p-2 flex items-center justify-between mt-4 shadow-[0_10px_30px_rgba(0,0,0,0.8)] w-max max-w-full" style={{ background: 'rgba(10, 15, 25, 0.75)', backdropFilter: 'blur(16px)', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                            <div className="flex items-center gap-3">
                                <div className="flex flex-col">
                                    <span className="text-[6px] text-blue-500 uppercase tracking-widest font-bold mb-0.5">Mode</span>
                                    <span className="px-2.5 py-0.5 text-[8px] font-bold rounded tracking-widest text-cyan-300 bg-blue-500/20 border border-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.3)]">
                                        {activeSample?.curveType?.toUpperCase() || 'KINETIC'}
                                    </span>
                                </div>
                            </div>

                            <div className="mx-4 w-px h-6 bg-white/10"></div>

                            <div className="flex items-center gap-2 text-[9px] font-mono text-blue-400/60 tracking-widest">
                                <span className={`w-1.5 h-1.5 rounded-full ${isRunning ? 'bg-cyan-400 animate-pulse shadow-[0_0_6px_#06b6d4]' : 'bg-blue-600'}`}></span>
                                {isRunning ? 'INCUBATING @ 37°C...' : reportStatus === 'ready' ? 'ASSAY COMPLETE' : activeSample ? 'READY' : 'IDLE'}
                            </div>
                        </div>
                    </div>

                    {/* RIGHT: Sample List + Telemetry */}
                    <div className="w-full md:w-80 lg:w-96 flex flex-col gap-4 md:gap-6 shrink-0 pointer-events-auto">

                        {/* Biochemical Panels */}
                        <div className="rounded-3xl bg-slate-900/60 backdrop-blur-md border border-white/10 shadow-[0_0_20px_rgba(0,0,0,0.5)] flex flex-col overflow-hidden">
                            <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest p-4 flex items-center gap-2 border-b border-white/5 drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]">
                                <Hexagon className="w-3.5 h-3.5" /> BIOCHEMICAL PANELS
                            </h3>
                            <div className="flex flex-col gap-2 p-3">
                                {samples.map((sample) => (
                                    <div
                                        key={sample.id}
                                        onClick={() => selectSample(sample)}
                                        className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-300 border ${activeSample?.id === sample.id
                                            ? 'bg-blue-500/10 border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.3)]'
                                            : 'bg-slate-800/30 border-white/5 hover:bg-slate-800/50 hover:border-blue-500/20'
                                            }`}
                                    >
                                        <div className={`w-8 h-8 rounded-lg ${sample.colorClass} flex items-center justify-center text-white/80 text-[10px] font-bold shrink-0 shadow-inner`}>
                                            <Hexagon className="w-4 h-4" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-bold text-white truncate">{sample.name}</p>
                                            <p className="text-[9px] text-gray-500 font-mono truncate">{sample.desc}</p>
                                        </div>
                                        {/* RUN ASSAY button */}
                                        {activeSample?.id === sample.id && !isRunning && reportStatus !== 'ready' && (
                                            <button
                                                onClick={(e) => { e.stopPropagation(); runAssay(); }}
                                                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-blue-500/20 border border-blue-500/50 text-blue-300 text-[9px] font-bold tracking-widest uppercase hover:bg-blue-500/30 hover:shadow-[0_0_12px_rgba(59,130,246,0.5)] transition-all shrink-0"
                                            >
                                                <Play className="w-3 h-3" /> RUN
                                            </button>
                                        )}
                                        {/* Running indicator */}
                                        {activeSample?.id === sample.id && isRunning && (
                                            <span className="text-[9px] text-cyan-400 font-mono animate-pulse tracking-widest shrink-0">
                                                RUNNING...
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* BIOCHEMICAL TELEMETRY */}
                        <AnimatePresence>
                            {!isReportOpen && (
                                <motion.div
                                    initial={{ opacity: 0, y: 50 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 50 }}
                                    transition={{ duration: 0.5, ease: "easeInOut" }}
                                    className="rounded-3xl bg-slate-900/80 backdrop-blur-md border border-white/10 shadow-[0_0_20px_rgba(0,0,0,0.5)] p-4 flex flex-col shrink-0 cursor-default pointer-events-auto"
                                >
                                    <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-3 flex items-center justify-between border-b border-white/5 pb-3">
                                        <span className="flex items-center gap-2 drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]">
                                            <Activity className="w-3.5 h-3.5" /> BIOCHEMICAL TELEMETRY
                                        </span>
                                        <RefreshCw className={`w-3.5 h-3.5 text-blue-600 ${isRunning ? 'animate-spin text-cyan-400' : ''}`} />
                                    </h3>

                                    <div className="bg-black/50 rounded-xl p-3 border border-white/5 font-mono text-[10px] sm:text-[11px] text-blue-300 leading-relaxed min-h-[100px]">
                                        {telemetryLog.length > 0 ? (
                                            telemetryLog.map((line, i) => (
                                                <motion.div
                                                    key={i}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ duration: 0.3 }}
                                                    className={line.includes('Result:') ? (
                                                        report?.status === 'HIGH' ? 'text-red-400' :
                                                            report?.status === 'BORDERLINE' ? 'text-amber-400' :
                                                                'text-emerald-400'
                                                    ) : ''}
                                                >
                                                    {line}
                                                </motion.div>
                                            ))
                                        ) : activeSample ? (
                                            <span className="opacity-30 text-slate-500">&gt; PANEL SELECTED: {activeSample.name}<br />&gt; PRESS "RUN" TO START ASSAY</span>
                                        ) : (
                                            <span className="opacity-30 text-slate-500">&gt; SPECTROMETER IDLE<br />&gt; NO PANEL SELECTED</span>
                                        )}
                                    </div>

                                    {reportStatus === 'ready' && (
                                        <button
                                            onClick={() => setIsReportOpen(true)}
                                            className="mt-3 w-full border border-blue-500/50 bg-blue-950/30 hover:bg-blue-900/50 text-blue-400 font-bold tracking-widest uppercase text-[10px] py-2 rounded-lg transition-all flex items-center justify-center gap-2 hover:shadow-[0_0_15px_rgba(59,130,246,0.4)]"
                                        >
                                            <FileText className="w-3.5 h-3.5" /> View Final Report
                                        </button>
                                    )}

                                    <div className="mt-3 text-right">
                                        <p className="text-[8px] text-slate-500 font-bold tracking-widest uppercase">POWERED BY CHANGE INTELLIGENCE</p>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>

            {/* Full-Screen Final Report Modal */}
            <FinalReportModal
                isOpen={isReportOpen}
                onClose={() => setIsReportOpen(false)}
                reportData={report}
                activeSample={activeSample}
                sampleType="biochemistry"
            />
        </div>
    );
}
