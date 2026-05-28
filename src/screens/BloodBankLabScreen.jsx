import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Droplet, ClipboardList, Activity, FileText, Zap } from 'lucide-react';
import FinalReportModal from '../components/FinalReportModal';
import SidebarNavigation from '../components/SidebarNavigation';
import BloodTypingCard from '../components/BloodTypingCard';
import { motion, AnimatePresence } from 'framer-motion';

// ─── Blood Bank Samples Dataset ───
const samples = [
    {
        id: 'patient-x',
        name: 'Patient X',
        desc: 'Pre-op Screen',
        icon: '👤',
        reactions: { a: true, b: false, d: true } // A Positive
    },
    {
        id: 'patient-y',
        name: 'Patient Y',
        desc: 'Trauma Protocol',
        icon: '👤',
        reactions: { a: true, b: true, d: true } // AB Positive
    },
    {
        id: 'patient-z',
        name: 'Patient Z',
        desc: 'Routine Baseline',
        icon: '👤',
        reactions: { a: false, b: false, d: false } // O Negative
    },
];

const resultsData = {
    'patient-x': {
        organism: 'Patient X', // reused field
        bloodType: 'A POSITIVE',
        status: 'Critical',
        findingLabel: 'ABO/Rh Blood Group',
        finding: 'A Positive (A+)',
        findingStatus: 'NORMAL',
        insight: 'Patient possesses A antigens and Rh(D) antigens. Anti-B antibodies are present in plasma.',
        compatibility: {
            donate: ['A+', 'AB+'],
            receive: ['A+', 'A-', 'O+', 'O-']
        },
        challengeBank: [
            { question: 'Patient X is A Positive. Which blood type can they safely receive?', options: ['B Positive', 'AB Positive', 'O Negative'], correctAnswer: 'O Negative', explanation: 'O Negative is the universal donor type and lacks A, B, and Rh(D) antigens, making it safe for an A Positive recipient.' },
            { question: 'If Patient X (A+) donates plasma, who can safely receive it?', options: ['A and AB', 'O and B', 'Anyone'], correctAnswer: 'A and AB', explanation: 'A+ plasma contains anti-B antibodies. It can only be given to A or AB patients, who do not have B antigens on their red cells.' },
            { question: 'What causes the macroscopic agglutination seen in the Anti-A well?', options: ['Antigen-Antibody cross-linking', 'Fibrin clot formation', 'Hemolysis'], correctAnswer: 'Antigen-Antibody cross-linking', explanation: 'Agglutination occurs when specific antibodies (reagent) bind to multiple corresponding antigens on adjacent red blood cells, creating a visible lattice.' },
        ],
    },
    'patient-y': {
        organism: 'Patient Y',
        bloodType: 'AB POSITIVE',
        status: 'Critical',
        findingLabel: 'ABO/Rh Blood Group',
        finding: 'AB Positive (AB+)',
        findingStatus: 'WARNING',
        insight: 'Universal Recipient. Patient possesses both A and B antigens, plus Rh(D) antigens. No ABO antibodies in plasma.',
        compatibility: {
            donate: ['AB+'],
            receive: ['All Blood Types (Universal Recipient)']
        },
        challengeBank: [
            { question: 'Patient Y is AB Positive. What antibodies are naturally present in their plasma?', options: ['Anti-A', 'Anti-B and Anti-A', 'None'], correctAnswer: 'None', explanation: 'Because they have both A and B antigens on their red cells, they lack naturally occurring Anti-A and Anti-B antibodies in their plasma (to prevent self-destruction).' },
            { question: 'Why is Patient Y considered the "Universal Recipient" for packed RBCs?', options: ['They lack ABO antibodies', 'They have all antigens', 'They lack the Rh factor'], correctAnswer: 'They lack ABO antibodies', explanation: 'Having no Anti-A or Anti-B in plasma means they will not mount an acute hemolytic reaction against any transfused donor red blood cells.' },
            { question: 'If Patient Y needs a plasma transfusion, which type is the Universal Plasma Donor?', options: ['Type O', 'Type AB', 'Type A'], correctAnswer: 'Type AB', explanation: 'Type AB plasma lacks both Anti-A and Anti-B antibodies, making it safe to transfuse into any patient regardless of their blood type.' },
        ],
    },
    'patient-z': {
        organism: 'Patient Z',
        bloodType: 'O NEGATIVE',
        status: 'Normal',
        findingLabel: 'ABO/Rh Blood Group',
        finding: 'O Negative (O-)',
        findingStatus: 'CRITICAL',
        insight: 'Universal Donor. Patient lacks A, B, and Rh(D) antigens. Plasma contains Anti-A and Anti-B antibodies.',
        compatibility: {
            donate: ['All Blood Types (Universal Donor)'],
            receive: ['O- Only']
        },
        challengeBank: [
            { question: 'Patient Z is O Negative. Why are they considered the "Universal Donor" for red blood cells?', options: ['Their cells lack A, B, and Rh antigens', 'Their plasma lacks antibodies', 'Their cells have all antigens'], correctAnswer: 'Their cells lack A, B, and Rh antigens', explanation: 'Without A, B, or Rh antigens on the red cell surface, the cells will not be attacked by the recipient\'s immune system, regardless of the recipient\'s blood type.' },
            { question: 'If Patient Z (O-) needs a blood transfusion, what type can they receive?', options: ['O Positive or Negative', 'O Negative strictly', 'Any type'], correctAnswer: 'O Negative strictly', explanation: 'Because O- patients have Anti-A and Anti-B in their plasma and can develop Anti-D, they must only receive O- blood to prevent a transfusion reaction.' },
            { question: 'In an emergency trauma situation where the patient\'s blood type is unknown, what type is given?', options: ['O Positive', 'AB Negative', 'O Negative'], correctAnswer: 'O Negative', explanation: 'O Negative is the emergency release blood of choice, particularly for females of childbearing age, as it carries the lowest risk of hemolytic reaction and Rh sensitization.' },
        ],
    },
};

export default function BloodBankLabScreen({ onNavigate }) {
    const [screenState, setScreenState] = useState('screen-transition-hidden');
    const [activeSample, setActiveSample] = useState(null);
    const [isMixing, setIsMixing] = useState(false);
    const [hasMixed, setHasMixed] = useState(false);
    const [isReportOpen, setIsReportOpen] = useState(false);

    // Telemetry log state
    const [logs, setLogs] = useState([]);
    const timeoutsRef = useRef([]);

    useEffect(() => {
        const t = setTimeout(() => setScreenState('screen-visible'), 50);
        return () => clearTimeout(t);
    }, []);

    // Cleanup timeouts
    useEffect(() => {
        return () => timeoutsRef.current.forEach(t => clearTimeout(t));
    }, []);

    const handleNavigation = (target) => {
        setScreenState('screen-exit');
        setTimeout(() => onNavigate(target), 600);
    };

    const selectSample = (sample) => {
        if (isMixing) return;
        setActiveSample(sample);
        setHasMixed(false);
        setIsReportOpen(false);
        setLogs([]);
        timeoutsRef.current.forEach(t => clearTimeout(t));
        timeoutsRef.current = [];
    };

    const addLog = (text, delayMs) => {
        const t = setTimeout(() => {
            setLogs(prev => [...prev, text]);
        }, delayMs);
        timeoutsRef.current.push(t);
    };

    const startMixing = () => {
        if (!activeSample || isMixing) return;

        setIsMixing(true);
        setHasMixed(false);
        setLogs([]);

        timeoutsRef.current.forEach(t => clearTimeout(t));
        timeoutsRef.current = [];

        // 6-second progressive timing logic
        addLog('> [0s] Adding Anti-A, Anti-B, and Anti-D reagents...', 0);
        addLog('> [2s] Rocking the slide to mix samples...', 2000);
        addLog('> [4s] Observing for gradual agglutination...', 4000);
        addLog('> [6s] Reaction complete. Results ready.', 6000);

        const doneTimer = setTimeout(() => {
            setIsMixing(false);
            setHasMixed(true);
        }, 6000);
        timeoutsRef.current.push(doneTimer);
    };

    return (
        <div id="blood-bank-lab-screen" className={`absolute inset-0 z-40 flex flex-col backdrop-blur-3xl min-h-dvh w-full overflow-y-auto overflow-x-hidden scroll-smooth pb-32 ${screenState}`}>
            <div className="w-full h-full max-w-[1400px] mx-auto flex flex-col relative">

                {/* ═══ Header ═══ */}
                <header className="pt-6 md:pt-8 pb-3 px-4 md:px-6 flex justify-between items-center border-b border-white/5 bg-linear-to-b from-pink-900/10 to-transparent shrink-0">
                    <div className="flex items-center gap-3">
                        <button onClick={() => handleNavigation('virtual-lab')} className="bg-slate-800/60 border border-white/10 w-8 h-8 rounded-lg flex items-center justify-center text-pink-300 hover:text-pink-400 hover:drop-shadow-[0_0_8px_rgba(219,39,119,0.8)] transition-all">
                            <ArrowLeft className="w-4 h-4" />
                        </button>
                        <div>
                            <h2 className="text-base md:text-lg font-bold text-white tracking-tight flex items-center gap-2">
                                <span className="text-pink-500 drop-shadow-[0_0_8px_rgba(219,39,119,0.8)]"><Droplet className="w-4 h-4 inline fill-pink-500" /></span>
                                <span className="text-pink-100">Blood Bank & Serology</span>
                            </h2>
                            <p className="text-[9px] text-pink-400/60 mt-0.5 uppercase tracking-widest font-mono">Immunohematology & Blood Typing</p>
                        </div>
                    </div>
                </header>

                <SidebarNavigation onNavigate={handleNavigation} />

                {/* ═══ Main Workspace ═══ */}
                <div className={`flex-1 flex flex-col md:flex-row overflow-visible p-4 md:p-6 gap-6 md:gap-8 ${isReportOpen ? 'hidden' : ''}`}>

                    {/* ═══ CENTER: Blood Typing Card Dashboard ═══ */}
                    <div className="flex-1 flex flex-col gap-5">
                        <div className="w-full bg-slate-900/60 border border-pink-500/20 rounded-3xl p-6 md:p-8 backdrop-blur-md shadow-[0_0_40px_rgba(219,39,119,0.06)] flex flex-col">

                            {/* Title Bar */}
                            <div className="flex items-center justify-between mb-8 pb-4 border-b border-pink-500/15">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-pink-500/10 border border-pink-500/30 flex items-center justify-center">
                                        <Droplet className="w-5 h-5 text-pink-400 fill-pink-400/20" />
                                    </div>
                                    <div>
                                        <span className="text-sm font-bold text-white tracking-wide">FORWARD/REVERSE TYPING TEST</span>
                                        <p className="text-[9px] text-pink-400/60 uppercase tracking-widest font-mono mt-0.5">
                                            {activeSample ? `Active Specimen: ${activeSample.name}` : 'Awaiting Specimen Selection'}
                                        </p>
                                    </div>
                                </div>
                                <div className={`w-3 h-3 rounded-full ${isMixing ? 'bg-pink-400 animate-pulse shadow-[0_0_12px_rgba(219,39,119,0.8)]' : (hasMixed ? 'bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,0.8)]' : 'bg-slate-600')}`} />
                            </div>

                            {/* The Interactive Blood Typing Card */}
                            <div className="flex-1 flex flex-col justify-center items-center py-8">
                                <BloodTypingCard
                                    sample={activeSample}
                                    isMixing={isMixing}
                                    hasMixed={hasMixed}
                                />
                            </div>

                            {/* ═══ Action Button Row ═══ */}
                            <div className="mt-8 flex gap-3">
                                {!hasMixed && activeSample && (
                                    <motion.button
                                        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                        onClick={startMixing}
                                        disabled={isMixing}
                                        className={`flex-1 h-12 rounded-xl flex items-center justify-center gap-2 tracking-widest uppercase text-xs font-bold transition-all shadow-[0_0_25px_rgba(219,39,119,0.4)] hover:shadow-[0_0_35px_rgba(219,39,119,0.6)] ${isMixing ? 'bg-slate-800 border-pink-500/30 text-pink-400 opacity-80 cursor-not-allowed' : 'bg-pink-600 border border-pink-400 text-white hover:bg-pink-500'
                                            }`}
                                    >
                                        <Activity className={`w-4 h-4 ${isMixing ? 'animate-spin' : ''}`} />
                                        {isMixing ? 'Reaction In Progress...' : 'Add Reagents & Mix'}
                                    </motion.button>
                                )}

                                <AnimatePresence>
                                    {hasMixed && (
                                        <motion.button
                                            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
                                            onClick={() => setIsReportOpen(true)}
                                            className="flex-1 h-12 rounded-xl border border-emerald-500/50 bg-emerald-600/20 text-emerald-400 hover:bg-emerald-500 hover:text-white flex items-center justify-center gap-2 tracking-widest uppercase text-xs font-bold transition-all shadow-[0_0_20px_rgba(16,185,129,0.3)]"
                                        >
                                            <FileText className="w-4 h-4" /> View Final Report
                                        </motion.button>
                                    )}
                                </AnimatePresence>
                            </div>

                        </div>
                    </div>

                    {/* ═══ RIGHT: Specimen Queue ═══ */}
                    <div className="w-full md:w-[320px] lg:w-[360px] flex flex-col gap-4 md:gap-6 shrink-0">
                        <div className="bg-slate-900/60 backdrop-blur-md rounded-3xl p-5 border border-white/5 shadow-[0_0_30px_rgba(219,39,119,0.05)]">
                            <h3 className="text-[10px] font-bold text-pink-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                <ClipboardList className="w-3 h-3" /> Specimen Queue
                            </h3>
                            <div className="flex flex-col gap-3">
                                {samples.map((s) => (
                                    <button
                                        key={s.id}
                                        onClick={() => selectSample(s)}
                                        disabled={isMixing}
                                        className={`group relative rounded-2xl p-3 w-full overflow-hidden text-left transition-all duration-300 border ${isMixing ? 'opacity-50 cursor-not-allowed border-white/5 bg-slate-800/30' :
                                            (activeSample?.id === s.id ? 'border-pink-500/50 bg-pink-900/20 scale-[1.02]' : 'border-white/10 bg-slate-800/40 hover:bg-slate-800 hover:border-pink-500/30')
                                            }`}
                                    >
                                        <div className="flex items-center gap-3 relative z-10">
                                            <div className="w-10 h-10 rounded-xl bg-black border border-white/10 flex items-center justify-center text-lg shadow-[inset_0_0_12px_rgba(219,39,119,0.2)]">
                                                {s.icon}
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="font-bold text-slate-200 text-sm">{s.name}</span>
                                                <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono">{s.desc}</span>
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Live Telemetry Card (Reused aesthetic for instructions/logs) */}
                        <div className="flex-1 min-h-[250px] bg-slate-900/60 backdrop-blur-md rounded-3xl p-5 border border-white/5 shadow-[0_0_30px_rgba(219,39,119,0.05)] flex flex-col">
                            <h3 className="text-[10px] font-bold text-pink-400 uppercase tracking-widest pb-3 border-b border-white/10 mb-3 flex items-center gap-2">
                                <Activity className="w-3 h-3" /> Reaction Telemetry
                            </h3>
                            <div className="flex flex-col gap-2 overflow-y-auto flex-1 no-scrollbar pb-2">
                                {!activeSample ? (
                                    <div className="m-auto text-center opacity-30">
                                        <Droplet className="w-8 h-8 text-pink-400 fill-pink-400/50 mx-auto mb-2 opacity-50" />
                                        <span className="text-[10px] uppercase tracking-widest font-mono text-slate-400">System Idle</span>
                                    </div>
                                ) : (
                                    <>
                                        <LogEntry visible={!isMixing && !hasMixed} text={`> Patient ${activeSample.name} blood sample loaded into testing wells. Ready for reagents.`} />
                                        {logs.map((log, i) => (
                                            <LogEntry key={i} visible={true} text={log} />
                                        ))}
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* ═══ Report Modal ═══ */}
                <FinalReportModal
                    isOpen={isReportOpen}
                    onClose={() => { setIsReportOpen(false); }}
                    reportData={activeSample ? resultsData[activeSample.id] : null}
                    activeSample={activeSample}
                    sampleType="bloodbank"
                    labTechName="Karl Landsteiner"
                />

            </div>
        </div>
    );
}

// ─── Tiny animated log line component ───
function LogEntry({ visible, text }) {
    if (!visible) return null;
    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4 }}
            className="text-[11px] font-mono text-pink-200/80 tracking-wider leading-relaxed bg-black/30 px-3 py-2 rounded-lg border-l-2 border-pink-500/50"
        >
            {text}
        </motion.div>
    );
}
