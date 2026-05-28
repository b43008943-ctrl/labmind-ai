import { useState, useRef, useEffect } from 'react';
import { Sparkles,
    Dna, Bug, Droplets, Microscope, Heart, Brain, FlaskConical, TestTubes, Pill, Syringe, Eye, Bone, Thermometer, Stethoscope, Circle, Shell,
    ChevronLeft, ChevronRight, Film, Upload, Loader2, ArrowLeft, Pause, Play, Trophy, RotateCcw, CheckCircle2, XCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigation } from '../context/NavigationContext';

import { API_BASE_URL as API_BASE } from '../services/apiClient';

const ICON_MAP = {
    dna: Dna, cell: Circle, bacteria: Bug, virus: Bug, blood: Droplets, microscope: Microscope,
    petri_dish: Circle, syringe: Syringe, pill: Pill, heart: Heart, lungs: Circle, kidney: Circle,
    liver: Circle, brain: Brain, bone: Bone, muscle: Circle, eye: Eye, flask: FlaskConical,
    test_tube: TestTubes, thermometer: Thermometer, stethoscope: Stethoscope, chromosome: Dna,
    antibody: Sparkles, parasite: Bug, fungus: Shell, worm: Bug,
};

export default function VideoGeneratorScreen() {
    const { goBack } = useNavigation();

    const [phase, setPhase] = useState('upload'); // upload | generating | player | quiz
    const [textInput, setTextInput] = useState('');
    const [topicHint, setTopicHint] = useState('');
    const [fileName, setFileName] = useState('');
    const [fileRef, setFileRef] = useState(null);
    const [slideshow, setSlideshow] = useState(null);
    const [currentScene, setCurrentScene] = useState(0);
    const [isPlaying, setIsPlaying] = useState(true);
    const [errorMessage, setErrorMessage] = useState(null);
    // Quiz state
    const [quizIdx, setQuizIdx] = useState(0);
    const [quizAnswer, setQuizAnswer] = useState(null);
    const [quizScore, setQuizScore] = useState(0);
    const [quizDone, setQuizDone] = useState(false);

    const fileInputRef = useRef(null);
    const timerRef = useRef(null);

    // Auto-advance
    useEffect(() => {
        if (phase !== 'player' || !isPlaying || !slideshow) return;
        timerRef.current = setTimeout(() => {
            if (currentScene + 1 < slideshow.scenes.length) setCurrentScene(i => i + 1);
            else { setIsPlaying(false); setPhase('quiz'); setQuizIdx(0); setQuizAnswer(null); setQuizScore(0); setQuizDone(false); }
        }, 8000);
        return () => clearTimeout(timerRef.current);
    }, [phase, isPlaying, currentScene, slideshow]);

    const handleFileSelect = (e) => {
        const f = e.target.files[0];
        if (!f) return;
        setFileRef(f);
        setFileName(f.name);
    };

    const handleGenerate = async () => {
        setPhase('generating');
        setErrorMessage(null);

        const token = localStorage.getItem('labmind_token');
        const formData = new FormData();
        if (fileRef) formData.append('file', fileRef);
        else formData.append('text', textInput.slice(0, 5000));
        if (topicHint.trim()) formData.append('topic_hint', topicHint.trim());

        try {
            const resp = await fetch(`${API_BASE}/api/video-generator/generate`, {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
                body: formData,
            });
            if (!resp.ok) { const err = await resp.json().catch(() => ({})); throw new Error(err.detail || `Error ${resp.status}`); }
            const data = await resp.json();
            if (data.success && data.data?.scenes?.length) {
                setSlideshow(data.data);
                setCurrentScene(0);
                setIsPlaying(true);
                setPhase('player');
            } else throw new Error('AI returned no scenes.');
        } catch (err) {
            setErrorMessage(err.message);
            setPhase('upload');
        }
    };

    const resetAll = () => { setPhase('upload'); setSlideshow(null); setCurrentScene(0); setIsPlaying(true); setErrorMessage(null); setFileRef(null); setFileName(''); setTextInput(''); setTopicHint(''); };
    const canGenerate = !!(fileRef || textInput.trim().length > 20);
    const scene = slideshow?.scenes?.[currentScene];
    const SceneIcon = scene ? (ICON_MAP[scene.icon] || Sparkles) : Sparkles;

    // ═══ QUIZ HELPERS ═══
    const quizScenes = slideshow?.scenes?.filter(s => s.quiz_question) || [];
    const currentQuiz = quizScenes[quizIdx]?.quiz_question;

    const handleQuizAnswer = (idx) => {
        if (quizAnswer !== null) return;
        setQuizAnswer(idx);
        if (idx === currentQuiz.correct) setQuizScore(s => s + 1);
        setTimeout(() => {
            if (quizIdx + 1 < quizScenes.length) { setQuizIdx(i => i + 1); setQuizAnswer(null); }
            else setQuizDone(true);
        }, 1500);
    };

    // ═══ RENDER ═══
    return (
        <div className="min-h-dvh w-full bg-[#0A0E17] flex flex-col overflow-x-hidden overflow-y-auto" style={{ WebkitOverflowScrolling: 'touch' }}>

            {/* Header — hidden during player/quiz for immersion */}
            {(phase === 'upload' || phase === 'generating') && (
                <header className="px-6 pt-12 pb-4 flex items-center gap-4 sticky top-0 bg-[#0A0E17]/80 backdrop-blur-xl z-40 border-b border-white/5">
                    <button onClick={goBack} className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 transition-colors shrink-0">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <div className="flex-1">
                        <h1 className="text-lg font-bold text-white tracking-wide flex items-center gap-2"><Film className="w-5 h-5 text-purple-400" /> AI Slideshow Generator</h1>
                        <p className="text-[11px] text-slate-400 font-medium mt-0.5">Transform study materials into visual stories</p>
                    </div>
                </header>
            )}

            <div className={`flex-1 flex flex-col ${phase === 'player' || phase === 'quiz' ? '' : 'px-6 pt-6 pb-32 overflow-y-auto no-scrollbar'}`}>
                <AnimatePresence mode="wait">

                    {/* ═══ UPLOAD ═══ */}
                    {phase === 'upload' && (
                        <motion.div key="upload" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex flex-col gap-5 max-w-2xl mx-auto w-full">
                            {errorMessage && (
                                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl"><p className="text-sm text-red-300">{errorMessage}</p></div>
                            )}

                            {/* File upload */}
                            <div onClick={() => fileInputRef.current?.click()} onDragOver={(e) => e.preventDefault()}
                                onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) { setFileRef(f); setFileName(f.name); } }}
                                className="flex flex-col items-center justify-center py-14 px-6 rounded-2xl border-2 border-dashed border-white/10 bg-white/[0.03] hover:border-purple-500/30 hover:bg-white/[0.05] transition-all cursor-pointer text-center">
                                <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-4">
                                    <Upload size={28} className="text-purple-400" />
                                </div>
                                {fileName ? (
                                    <>
                                        <p className="text-sm font-bold text-white mb-1">{fileName}</p>
                                        <p className="text-xs text-slate-500">Tap to change file</p>
                                    </>
                                ) : (
                                    <>
                                        <p className="text-sm font-bold text-white mb-1">Upload Study Material</p>
                                        <p className="text-xs text-slate-500">PDF, TXT, or DOCX • Drag & drop or tap</p>
                                    </>
                                )}
                                <input ref={fileInputRef} type="file" accept=".pdf,.txt,.docx" className="hidden" onChange={handleFileSelect} />
                            </div>

                            <div className="flex items-center gap-3">
                                <div className="flex-1 h-px bg-white/5" /><span className="text-xs text-slate-600 font-bold uppercase tracking-wider">or paste text</span><div className="flex-1 h-px bg-white/5" />
                            </div>

                            {/* Text input */}
                            <textarea value={textInput} onChange={(e) => setTextInput(e.target.value)} placeholder="Paste your study notes here..."
                                className="w-full min-h-[120px] max-h-[250px] bg-white/[0.03] border border-white/10 rounded-xl text-sm text-white placeholder-slate-600 p-4 outline-none focus:border-purple-500/40 resize-y" maxLength={5000} />
                            <p className="text-[10px] text-slate-600 text-right -mt-3">{textInput.length}/5000</p>

                            {/* Topic hint */}
                            <input type="text" value={topicHint} onChange={(e) => setTopicHint(e.target.value)} placeholder="What is this about? (optional, e.g., Malaria life cycle)"
                                className="w-full bg-white/[0.03] border border-white/10 rounded-xl text-sm text-white placeholder-slate-600 p-3 outline-none focus:border-purple-500/40" />

                            {/* Generate */}
                            <button onClick={handleGenerate} disabled={!canGenerate}
                                className={`w-full py-4 rounded-2xl font-bold text-sm tracking-wider uppercase flex items-center justify-center gap-3 transition-all ${canGenerate ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-purple-500/30 text-white hover:from-purple-500/30 hover:to-pink-500/30 cursor-pointer active:scale-[0.98]' : 'bg-white/5 border border-white/5 text-slate-600 cursor-not-allowed'}`}>
                                <Sparkles size={18} /> Generate Slideshow
                            </button>
                        </motion.div>
                    )}

                    {/* ═══ GENERATING ═══ */}
                    {phase === 'generating' && (
                        <motion.div key="gen" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center justify-center gap-6 py-20 text-center max-w-md mx-auto">
                            <div className="relative">
                                <div className="absolute inset-[-30px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(168,85,247,0.2) 0%, transparent 60%)', filter: 'blur(25px)' }} />
                                <Loader2 size={48} className="text-purple-400 animate-spin" />
                            </div>
                            <h3 className="text-lg font-bold text-white">Creating your visual story...</h3>
                            <div className="flex flex-col gap-2 text-xs text-slate-500">
                                <p>📄 Reading your material...</p>
                                <p>🎬 Creating scenes...</p>
                                <p>🎨 Building visuals...</p>
                            </div>
                            <p className="text-[10px] text-slate-600">This may take 15-30 seconds</p>
                        </motion.div>
                    )}

                    {/* ═══ PLAYER ═══ */}
                    {phase === 'player' && slideshow && scene && (
                        <motion.div key={`scene-${currentScene}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            className="flex-1 flex flex-col relative" style={{ minHeight: '100dvh' }}>

                            {/* Background gradient from scene color */}
                            <div className="absolute inset-0 pointer-events-none" style={{ background: `radial-gradient(ellipse at center, ${scene.color_theme}12 0%, #0A0E17 70%)` }} />

                            {/* Top bar */}
                            <div className="relative z-20 flex items-center justify-between px-5 pt-12 pb-3">
                                <button onClick={() => { setIsPlaying(false); resetAll(); }} className="w-9 h-9 rounded-full bg-black/40 border border-white/10 flex items-center justify-center text-white/60 hover:text-white transition-colors">
                                    <ArrowLeft size={16} />
                                </button>
                                <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">{currentScene + 1} / {slideshow.scenes.length}</span>
                                <div className="w-9" />
                            </div>

                            {/* Progress bar */}
                            <div className="relative z-20 flex gap-1 px-5 mb-6">
                                {slideshow.scenes.map((_, i) => (
                                    <div key={i} className="flex-1 h-1 rounded-full overflow-hidden cursor-pointer" style={{ background: 'rgba(255,255,255,0.08)' }} onClick={() => { setCurrentScene(i); setIsPlaying(false); }}>
                                        <div style={{ width: i < currentScene ? '100%' : i === currentScene ? '100%' : '0%', height: '100%', background: i <= currentScene ? scene.color_theme : 'transparent', transition: 'width 0.4s ease', opacity: i === currentScene ? 1 : 0.4 }} />
                                    </div>
                                ))}
                            </div>

                            {/* Scene content */}
                            <div className="relative z-10 flex-1 flex flex-col items-center px-6 pb-6 overflow-y-auto no-scrollbar">
                                {/* Icon */}
                                <motion.div initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.2, type: 'spring' }}
                                    className="w-20 h-20 rounded-2xl flex items-center justify-center mb-5" style={{ background: `${scene.color_theme}18`, border: `1px solid ${scene.color_theme}30` }}>
                                    <SceneIcon size={40} style={{ color: scene.color_theme, filter: `drop-shadow(0 0 12px ${scene.color_theme})` }} />
                                </motion.div>

                                {/* Title */}
                                <motion.h2 initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}
                                    className="text-xl font-bold text-white text-center mb-4 tracking-wide">{scene.title}</motion.h2>

                                {/* Narration */}
                                <motion.p initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.5 }}
                                    className="text-sm text-slate-300 text-center leading-relaxed max-w-md mb-6">{scene.narration}</motion.p>

                                {/* Key facts */}
                                <div className="w-full max-w-md space-y-2">
                                    {scene.key_facts?.map((fact, i) => (
                                        <motion.div key={i} initial={{ x: -30, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.7 + i * 0.2 }}
                                            className="flex items-start gap-3 p-3 rounded-xl" style={{ background: `${scene.color_theme}08`, border: `1px solid ${scene.color_theme}15` }}>
                                            <span className="text-xs mt-0.5 shrink-0" style={{ color: scene.color_theme }}>●</span>
                                            <span className="text-xs text-slate-300 leading-relaxed">{fact}</span>
                                        </motion.div>
                                    ))}
                                </div>
                            </div>

                            {/* Controls */}
                            <div className="relative z-20 px-6 pb-10 pt-4 flex flex-col items-center gap-4" style={{ background: 'linear-gradient(to top, #0A0E17 60%, transparent)' }}>
                                <div className="flex items-center gap-5">
                                    <button onClick={() => { if (currentScene > 0) setCurrentScene(i => i - 1); setIsPlaying(false); }} disabled={currentScene === 0}
                                        className="w-11 h-11 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/50 hover:text-white disabled:opacity-20 transition-all">
                                        <ArrowLeft size={18} />
                                    </button>
                                    <button onClick={() => setIsPlaying(p => !p)}
                                        className="w-14 h-14 rounded-full flex items-center justify-center transition-all" style={{ background: `${scene.color_theme}20`, border: `1px solid ${scene.color_theme}40` }}>
                                        {isPlaying ? <Pause size={22} style={{ color: scene.color_theme }} /> : <Play size={22} style={{ color: scene.color_theme }} />}
                                    </button>
                                    <button onClick={() => { if (currentScene + 1 < slideshow.scenes.length) setCurrentScene(i => i + 1); else { setPhase('quiz'); setQuizIdx(0); setQuizAnswer(null); setQuizScore(0); setQuizDone(false); } setIsPlaying(false); }}
                                        className="w-11 h-11 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-white/50 hover:text-white transition-all">
                                        <ChevronRight size={18} />
                                    </button>
                                </div>
                                {/* Dot indicators */}
                                <div className="flex gap-2">
                                    {slideshow.scenes.map((_, i) => (
                                        <button key={i} onClick={() => { setCurrentScene(i); setIsPlaying(false); }}
                                            className="w-2 h-2 rounded-full transition-all" style={{ background: i === currentScene ? scene.color_theme : 'rgba(255,255,255,0.15)', boxShadow: i === currentScene ? `0 0 8px ${scene.color_theme}` : 'none' }} />
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* ═══ QUIZ ═══ */}
                    {phase === 'quiz' && slideshow && (
                        <motion.div key="quiz" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="flex-1 flex flex-col items-center px-6 pt-16 pb-10" style={{ minHeight: '100dvh' }}>
                            {quizDone ? (
                                /* Final score */
                                <div className="flex flex-col items-center gap-5 text-center">
                                    <Trophy size={48} className="text-amber-400" style={{ filter: 'drop-shadow(0 0 15px rgba(245,158,11,0.5))' }} />
                                    <div className="text-5xl font-black" style={{ background: 'linear-gradient(135deg, #FFD700, #FF8C00)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                                        {quizScore}/{quizScenes.length}
                                    </div>
                                    <h3 className="text-lg font-bold text-white">{quizScore === quizScenes.length ? 'Perfect!' : quizScore >= quizScenes.length / 2 ? 'Well Done!' : 'Keep Studying!'}</h3>
                                    <div className="flex gap-3 mt-4">
                                        <button onClick={() => { setCurrentScene(0); setIsPlaying(true); setPhase('player'); }} className="px-5 py-3 rounded-xl text-xs font-bold uppercase tracking-wider bg-purple-500/10 border border-purple-500/25 text-purple-300 hover:bg-purple-500/20 transition-all">
                                            <RotateCcw size={14} className="inline mr-2" />Replay
                                        </button>
                                        <button onClick={resetAll} className="px-5 py-3 rounded-xl text-xs font-bold uppercase tracking-wider bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10 transition-all">
                                            New Slideshow
                                        </button>
                                    </div>
                                </div>
                            ) : currentQuiz ? (
                                /* Quiz question */
                                <div className="w-full max-w-md flex flex-col gap-5">
                                    <div className="text-center">
                                        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Question {quizIdx + 1} of {quizScenes.length}</span>
                                        <h3 className="text-base font-bold text-white mt-2 leading-relaxed">{currentQuiz.question}</h3>
                                    </div>
                                    <div className="flex flex-col gap-2">
                                        {currentQuiz.options.map((opt, i) => {
                                            let st = 'idle';
                                            if (quizAnswer !== null) {
                                                if (i === currentQuiz.correct) st = 'correct';
                                                else if (i === quizAnswer) st = 'wrong';
                                                else st = 'dim';
                                            }
                                            const colors = { idle: { bg: 'rgba(255,255,255,0.03)', border: 'rgba(255,255,255,0.08)', text: 'rgba(255,255,255,0.8)' }, correct: { bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.5)', text: '#10B981' }, wrong: { bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.5)', text: '#EF4444' }, dim: { bg: 'transparent', border: 'rgba(255,255,255,0.03)', text: 'rgba(255,255,255,0.2)' } };
                                            const c = colors[st];
                                            return (
                                                <button key={i} onClick={() => handleQuizAnswer(i)} disabled={quizAnswer !== null}
                                                    className="w-full flex items-center gap-3 p-4 rounded-xl transition-all" style={{ background: c.bg, border: `1px solid ${c.border}`, cursor: quizAnswer !== null ? 'default' : 'pointer' }}>
                                                    <div className="w-7 h-7 shrink-0 rounded-lg flex items-center justify-center text-xs font-bold" style={{ background: `${c.border}`, color: c.text }}>
                                                        {st === 'correct' ? <CheckCircle2 size={14} /> : st === 'wrong' ? <XCircle size={14} /> : String.fromCharCode(65 + i)}
                                                    </div>
                                                    <span className="flex-1 text-sm text-left" style={{ color: c.text }}>{opt}</span>
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>
                            ) : null}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
