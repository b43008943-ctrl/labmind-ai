import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, UploadCloud, PlayCircle, Sparkles, BrainCircuit, Zap, Volume2, VolumeX, Film, Clock, Maximize2, Minimize2, ChevronDown, Trash2, FolderPlus, X } from 'lucide-react';
import { summarizeText } from '../services/apiClient';
import AITestingCenterScreen from './AITestingCenterScreen';

/* ═══════════════════════════════════════════════════════════════
   AI GENERATIVE LAB — INTERIOR SCREEN
   Premium "Apple VisionOS" Control Room with Gold/Cyan/Deep Blue
   ═══════════════════════════════════════════════════════════════ */

export default function AIGenerativeLabScreen({ onNavigate }) {
    const [outputStyle, setOutputStyle] = useState('clinical');
    const [voiceEngine, setVoiceEngine] = useState('neural-female');
    const [duration, setDuration] = useState('2min');
    const [isDragOver, setIsDragOver] = useState(false);
    const [uploadedFile, setUploadedFile] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [isSynthesizing, setIsSynthesizing] = useState(false);
    const [isReady, setIsReady] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [narrationPreview, setNarrationPreview] = useState('');
    const [progress, setProgress] = useState(0);
    const [statusText, setStatusText] = useState('');
    const [activeDropdown, setActiveDropdown] = useState(null);
    const [generatedContent, setGeneratedContent] = useState(null);
    const [showHologram, setShowHologram] = useState(false);
    const fileInputRef = useRef(null);
    const progressIntervalRef = useRef(null);
    const speechUtteranceRef = useRef(null);
    const ambientAudioRef = useRef(null);
    const generatedContentRef = useRef(null);

    // Keep the ref in sync with state so setTimeout/closures always get the latest value
    useEffect(() => {
        generatedContentRef.current = generatedContent;
    }, [generatedContent]);



    /* Escape key exits fullscreen */
    useEffect(() => {
        const handler = (e) => { if (e.key === 'Escape') setIsFullscreen(false); };
        document.addEventListener('keydown', handler);
        return () => document.removeEventListener('keydown', handler);
    }, []);

    const handleDragOver = useCallback((e) => { e.preventDefault(); setIsDragOver(true); }, []);
    const handleDragLeave = useCallback(() => setIsDragOver(false), []);
    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) setUploadedFile(file);
    }, []);
    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) setUploadedFile(file);
    };

    const handleSynthesize = async () => {
        if (!uploadedFile) return;

        // Reset if already finished
        if (isReady) {
            setIsReady(false);
            setProgress(0);
            setGeneratedContent(null);
            generatedContentRef.current = null;
        }

        setIsProcessing(true);
        setIsSynthesizing(true);
        setIsReady(false);
        setProgress(0);
        setStatusText('INITIALIZING NEURAL PIPELINE...');

        // Nymph dialog
        const event = new CustomEvent('nymph-dialog-event', { detail: 'synthesizing' });
        window.dispatchEvent(event);

        // Indeterminate pulsing progress while waiting for API
        let pulseDir = 1;
        let currentProgress = 0;
        progressIntervalRef.current = setInterval(() => {
            currentProgress += pulseDir * 0.5;
            if (currentProgress >= 85) pulseDir = -1;
            if (currentProgress <= 10) pulseDir = 1;
            setProgress(Math.round(currentProgress));
        }, 60);

        // ── BACKEND PROXY CALL (no API key in frontend) ──
        let result;
        try {
            onStatusUpdate_('PARSING DATA CORE...');
            // Read file text client-side
            const fileText = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result);
                reader.onerror = () => reject(new Error('Failed to read file'));
                reader.readAsText(uploadedFile);
            });

            if (!fileText || fileText.trim().length === 0) {
                result = { success: false, error: 'File appears to be empty or unreadable.' };
            } else {
                onStatusUpdate_('TRANSMITTING TO NEURAL CORE...');
                const apiResult = await summarizeText(fileText.substring(0, 15000));
                const content = apiResult?.reply || '';
                result = content ? { success: true, content } : { success: false, error: 'AI returned an empty response.' };
            }
        } catch (err) {
            result = {
                success: false,
                error: err?.status === 401
                    ? 'Session expired. Please log in again.'
                    : `Error: ${err.message}`,
            };
        }

        function onStatusUpdate_(msg) { setStatusText(msg); }

        // Stop the pulsing progress
        clearInterval(progressIntervalRef.current);
        progressIntervalRef.current = null;

        if (result.success) {
            setProgress(100);
            setStatusText('SYNTHESIS COMPLETE. VIDEO READY FOR PROJECTION.');
            setGeneratedContent(result.content);
            generatedContentRef.current = result.content; // Immediate ref update (belt-and-suspenders)

            // Save to LocalStorage for the Holographic Testing Center to access
            if (result.content && typeof result.content === 'string') {
                localStorage.setItem('latestAiText', result.content);
                console.log('✅ latestAiText saved to localStorage.');
            } else if (result.content?.text) {
                localStorage.setItem('latestAiText', result.content.text);
                console.log('✅ latestAiText saved to localStorage.');
            }

            console.log('✅ Gemini API response stored. Length:', result.content?.length, 'First 200 chars:', result.content?.substring(0, 200));

            setTimeout(() => {
                setIsSynthesizing(false);
                setIsProcessing(false);
                setIsReady(true);

                const completeEvent = new CustomEvent('nymph-dialog-event', { detail: 'synthesis-complete' });
                window.dispatchEvent(completeEvent);
            }, 500);
        } else {
            // Handle API error gracefully
            setProgress(0);
            setIsSynthesizing(false);
            setIsProcessing(false);
            setStatusText(`ERROR: ${result.error}`);

            const errorEvent = new CustomEvent('nymph-dialog-event', { detail: 'purged' });
            window.dispatchEvent(errorEvent);
        }
    };

    /* ─── Arabic Detection Helper ─── */
    const detectArabic = (text) => {
        if (!text) return false;
        const arabicRegex = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]/;
        const sample = text.substring(0, 500);
        const arabicChars = (sample.match(/[\u0600-\u06FF]/g) || []).length;
        return arabicChars / sample.length > 0.15;
    };

    /* ─── Extract Narration Text from Gemini Script ─── */
    const extractNarrationText = (rawScript) => {
        if (!rawScript) return '';

        let text = rawScript;

        // 1. Remove [VISUAL CUE] lines entirely
        text = text.replace(/\[VISUAL CUE\].*$/gm, '');

        // 2. Remove bracketed markers: [00:00-00:15], [INTRO], [Scene 1], etc.
        text = text.replace(/\[.*?\]/g, '');

        // 3. Remove timestamp patterns: 00:00 - 00:30, 0:00-0:30, (00:15), etc.
        text = text.replace(/\(?\d{1,2}:\d{2}\s*[-–—]\s*\d{1,2}:\d{2}\)?/g, '');
        text = text.replace(/\(?\d{1,2}:\d{2}\)?/g, '');

        // 4. Remove section headers / structural labels
        text = text.replace(/^(INTRO|OUTRO|KEY CONCEPTS?|DETAILED EXPLANATION|SUMMARY|SCENE\s*\d*|ACT\s*\d*|SECTION\s*\d*)\s*[:→\-—]?\s*$/gim, '');

        // 5. Remove narration/script labels: "NARRATION:", "NARRATOR:", "VOICE OVER:", "VO:"
        text = text.replace(/^(NARRATION|NARRATOR|VOICE\s*OVER|VO|HOST|SPEAKER)\s*[:]\s*/gim, '');

        // 6. Remove stage directions in parentheses: (Camera zooms in), (Fade to black)
        text = text.replace(/\((?:camera|fade|cut|zoom|pan|transition|animation|music|sound|sfx|graphic|overlay|title|text on screen|b-roll|montage)[^)]*\)/gi, '');

        // 7. Remove markdown formatting characters
        text = text.replace(/[#*_~`>]/g, '');

        // 8. Remove lines that are purely dashes, equals, or decorative
        text = text.replace(/^[-=─═•●◆▸▹►▶]+\s*$/gm, '');

        // 9. Remove "Scene Description:" or "Visual:" labels
        text = text.replace(/^(Scene Description|Visual|Graphics?|Animation|Transition|B-Roll|On[- ]Screen Text)\s*[:]\s*.*$/gim, '');

        // 10. Remove hallucinatory metadata generation (e.g., "Project Title: Protocol 1.7", "Agent: Neural Synthesis")
        text = text.replace(/^(Project Title|Title|Agent|Voice Engine|Protocol|Output Style|Target Duration)\s*[:]\s*.*$/gim, '');

        // 11. Collapse multiple newlines and whitespace
        text = text.replace(/\n{2,}/g, '\n').replace(/[ \t]+/g, ' ').trim();

        // 11. Remove any remaining very short lines (likely labels/headers, < 5 chars)
        text = text.split('\n')
            .filter(line => line.trim().length > 5)
            .join('\n');

        return text.trim();
    };

    /* ─── Start Speech Synthesis ─── */
    const startNarration = (text) => {
        if (!text || !window.speechSynthesis) return;

        // Cancel any previous speech
        window.speechSynthesis.cancel();

        // Extract only the narration content from the video script
        const cleanText = extractNarrationText(text);
        console.log('🎙️ Narration text (first 300 chars):', cleanText.substring(0, 300));

        if (!cleanText || cleanText.length < 10) {
            console.warn('⚠️ Narration text too short or empty after cleaning');
            return;
        }

        const utterance = new SpeechSynthesisUtterance(cleanText);

        // Force Arabic language as requested
        utterance.lang = 'ar-SA';

        // Try to find and set an Arabic voice from the system
        const voices = window.speechSynthesis.getVoices();
        const arabicVoice = voices.find(voice => voice.lang.includes('ar'));
        if (arabicVoice) {
            utterance.voice = arabicVoice;
            console.log('🎙️ Selected Arabic Voice:', arabicVoice.name);
        } else {
            console.log('⚠️ No specific Arabic voice found on system, falling back to default.');
        }
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        // Chrome workaround: speechSynthesis pauses after ~15s; resume it
        const keepAlive = setInterval(() => {
            if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
                // no-op keep-alive
            } else if (window.speechSynthesis.paused) {
                window.speechSynthesis.resume();
            } else {
                clearInterval(keepAlive);
            }
        }, 5000);

        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => {
            setIsSpeaking(false);
            clearInterval(keepAlive);
        };
        utterance.onerror = () => {
            setIsSpeaking(false);
            clearInterval(keepAlive);
        };

        speechUtteranceRef.current = utterance;
        window.speechSynthesis.speak(utterance);
    };

    /* ─── Start Ambient Background Audio ─── */
    const startAmbientAudio = () => {
        if (ambientAudioRef.current) return; // already playing

        // Create a soft ambient drone using Web Audio API
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const gainNode = ctx.createGain();
            gainNode.gain.value = 0.10; // 10% volume

            // Create a warm pad-like drone
            const osc1 = ctx.createOscillator();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(80, ctx.currentTime);

            const osc2 = ctx.createOscillator();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(120, ctx.currentTime);

            // Slow LFO for movement
            const lfo = ctx.createOscillator();
            lfo.type = 'sine';
            lfo.frequency.setValueAtTime(0.3, ctx.currentTime);
            const lfoGain = ctx.createGain();
            lfoGain.gain.value = 5;
            lfo.connect(lfoGain);
            lfoGain.connect(osc1.frequency);

            // Low-pass filter for warmth
            const filter = ctx.createBiquadFilter();
            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(200, ctx.currentTime);
            filter.Q.setValueAtTime(1, ctx.currentTime);

            osc1.connect(filter);
            osc2.connect(filter);
            filter.connect(gainNode);
            gainNode.connect(ctx.destination);

            osc1.start();
            osc2.start();
            lfo.start();

            ambientAudioRef.current = { ctx, oscillators: [osc1, osc2, lfo], gainNode };
        } catch (e) {
            console.warn('Ambient audio not supported:', e);
        }
    };

    /* ─── Stop All Audio ─── */
    const stopAllAudio = () => {
        // Stop speech
        window.speechSynthesis?.cancel();
        setIsSpeaking(false);
        speechUtteranceRef.current = null;

        // Stop ambient
        if (ambientAudioRef.current) {
            const { ctx, oscillators } = ambientAudioRef.current;
            oscillators.forEach(osc => { try { osc.stop(); } catch (e) { } });
            try { ctx.close(); } catch (e) { }
            ambientAudioRef.current = null;
        }
    };

    /* ─── Toggle Mute ─── */
    const toggleMute = () => {
        if (isMuted) {
            // Unmute
            if (window.speechSynthesis?.paused) window.speechSynthesis.resume();
            if (ambientAudioRef.current?.gainNode) ambientAudioRef.current.gainNode.gain.value = 0.10;
            setIsMuted(false);
        } else {
            // Mute
            if (window.speechSynthesis?.speaking) window.speechSynthesis.pause();
            if (ambientAudioRef.current?.gainNode) ambientAudioRef.current.gainNode.gain.value = 0;
            setIsMuted(true);
        }
    };

    const handleLaunchProjection = () => {
        // IMMEDIATELY kill any speech from any source
        window.speechSynthesis.cancel();

        setIsPlaying(true);
        setIsReady(false);
        setIsMuted(false);
        setNarrationPreview('');
        const event = new CustomEvent('nymph-dialog-event', { detail: 'projection-started' });
        window.dispatchEvent(event);

        // Start narration after the zoom-blur animation completes
        // Read from REF to avoid stale closure
        setTimeout(() => {
            // Kill speech again just to be safe
            window.speechSynthesis.cancel();

            startAmbientAudio();

            // Get the ACTUAL Gemini API response from the ref
            // Using apiResponse?.text || apiResponse to handle both object and string returns
            const apiResponse = generatedContentRef.current;
            const finalScript = typeof apiResponse === 'object' && apiResponse !== null
                ? (apiResponse.text || apiResponse.content || '')
                : apiResponse;

            // === DEBUG PROOF ===
            console.log('='.repeat(60));
            console.log("Narrator Source:", finalScript);
            console.log('Length:', finalScript ? finalScript.length : 'NULL');
            console.log('First 500 chars:', finalScript ? finalScript.substring(0, 500) : 'EMPTY - NO GEMINI RESPONSE STORED');
            console.log('='.repeat(60));

            // MANDATORY: Ignore file name/type, only use finalScript
            if (finalScript && finalScript.length > 10) {
                // Show preview of what's being narrated on screen
                setNarrationPreview(finalScript.substring(0, 200));
                startNarration(finalScript);
            } else {
                console.error('❌ NARRATOR: No content to read. generatedContentRef is empty.');
                setNarrationPreview('⚠️ No AI content available to narrate.');
            }
        }, 1400);
    };

    const handleStopProjection = () => {
        stopAllAudio();
        setIsPlaying(false);
        setIsReady(true);
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => stopAllAudio();
    }, []);

    const handlePurge = () => {
        stopAllAudio();
        setIsReady(false);
        setIsPlaying(false);
        setIsSynthesizing(false);
        setProgress(0);
        setStatusText('ENGINE STANDBY... WAITING FOR DATA INPUT.');
        setUploadedFile(null);
        setGeneratedContent(null);
        generatedContentRef.current = null;
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }

        const purgeEvent = new CustomEvent('nymph-dialog-event', { detail: 'purged' });
        window.dispatchEvent(purgeEvent);
    };

    const handleSave = () => {
        const saveEvent = new CustomEvent('nymph-dialog-event', { detail: 'saved' });
        window.dispatchEvent(saveEvent);
        setTimeout(() => onNavigate('ai-archive'), 1500); // Navigate to archive after a brief pause
    };

    const CustomDropdown = ({ id, value, options, onChange, icon: Icon, label }) => {
        const isOpen = activeDropdown === id;
        const selectedOption = (options || []).find(opt => opt.value === value);

        return (
            <div className="relative w-full">
                <label className="text-[10px] font-bold tracking-[0.12em] uppercase text-white/40 mb-1 flex items-center gap-1.5">
                    <Icon size={11} /> {label}
                </label>
                <div
                    onClick={() => setActiveDropdown(isOpen ? null : id)}
                    className="custom-dropdown-btn"
                >
                    <span className="text-[12px] font-semibold tracking-[0.05em]">{selectedOption?.label}</span>
                    <ChevronDown size={14} className="text-white/50" style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s ease' }} />
                </div>

                <AnimatePresence>
                    {isOpen && (
                        <motion.ul
                            initial={{ opacity: 0, y: -10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -10, scale: 0.95 }}
                            transition={{ duration: 0.2, ease: "easeOut" }}
                            className="custom-dropdown-menu"
                        >
                            {(options || []).map((opt) => (
                                <li
                                    key={opt.value}
                                    className="custom-dropdown-item"
                                    onClick={() => { onChange(opt.value); setActiveDropdown(null); }}
                                >
                                    {opt.label}
                                </li>
                            ))}
                        </motion.ul>
                    )}
                </AnimatePresence>
            </div>
        );
    };

    /* ─── The Preview Stage (Video Player + Status Bar) ─── */
    const previewStage = (
        <div className="ai-lab-preview flex flex-col gap-5" style={{ width: '100%', minWidth: 0 }}>
            <div className={isFullscreen ? 'fullscreen-overlay' : ''} style={{
                background: isFullscreen ? '#05050A' : 'rgba(255,255,255,0.03)',
                backdropFilter: isFullscreen ? 'none' : 'blur(20px)',
                border: isFullscreen ? 'none' : '1px solid rgba(0,240,255,0.1)',
                borderRadius: isFullscreen ? '0px' : '20px',
                padding: '16px',
                display: 'flex', flexDirection: 'column',
                transition: 'all 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
                transformOrigin: 'center center',
                ...(isFullscreen ? { position: 'fixed', inset: 0, width: '100vw', height: '100vh', zIndex: 9999, alignItems: 'center', justifyContent: 'center' } : {})
            }}>
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-[11px] font-bold tracking-[0.12em] uppercase text-[#00F0FF] flex items-center gap-2">
                        <PlayCircle size={14} /> Preview Stage
                    </h3>
                </div>

                {/* ─── THE VIDEO HOLOGRAM SCREEN ─── */}
                <div className="relative flex items-center justify-center overflow-hidden" style={{
                    background: '#05050A', borderRadius: isFullscreen ? '0px' : '16px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    boxShadow: 'inset 0 0 50px rgba(0,0,0,0.8), 0 4px 30px rgba(0,0,0,0.4)',
                    minHeight: isFullscreen ? 'calc(100vh - 140px)' : '220px',
                    width: '100%',
                    aspectRatio: isFullscreen ? 'auto' : '16 / 9',
                    flex: isFullscreen ? 1 : 'none',
                    transition: 'all 0.5s cubic-bezier(0.16, 1, 0.3, 1)'
                }}>

                    {/* Scanning Laser Effect while synthesizing */}
                    {isSynthesizing && <div className="scanning-light" />}

                    {/* Standby State */}
                    {!isProcessing && !isReady && !isPlaying && (
                        <div className="flex flex-col items-center gap-4 text-center z-10">
                            <PlayCircle size={64} strokeWidth={1} className="text-white/15" style={{ filter: 'drop-shadow(0 0 20px rgba(0,240,255,0.2))' }} />
                            <p className="text-[11px] text-white/20 font-bold tracking-[0.15em] uppercase">Awaiting Synthesis</p>
                        </div>
                    )}

                    {/* Processing State */}
                    {isProcessing && (
                        <div className="flex flex-col items-center gap-5 text-center px-8">
                            <div style={{ animation: 'spin 3s linear infinite' }}>
                                <BrainCircuit size={56} strokeWidth={1.5} color="#FFD700" style={{ filter: 'drop-shadow(0 0 20px #FFD700) drop-shadow(0 0 40px rgba(255,215,0,0.4))' }} />
                            </div>
                            <p className="text-[11px] text-[#FFD700] font-bold tracking-[0.15em] uppercase">{statusText}</p>
                            <span className="text-[28px] font-black text-white/90" style={{ fontFamily: "'Inter', sans-serif" }}>{progress}%</span>
                        </div>
                    )}

                    {/* Synthesis Complete (READY) */}
                    {isReady && (
                        <div className="flex flex-col items-center gap-6 text-center z-10">
                            <button onClick={handleLaunchProjection} className="relative group cursor-pointer border-none bg-transparent outline-none">
                                {/* Intense glow behind button */}
                                <div className="absolute inset-0 rounded-full bg-[#FFD700] blur-2xl opacity-30 group-hover:opacity-50 transition-opacity duration-300 pointer-events-none" />

                                <PlayCircle
                                    size={80}
                                    strokeWidth={1.5}
                                    className="text-[#FFD700] relative z-20 group-hover:scale-110 transition-transform duration-300"
                                    style={{ filter: 'drop-shadow(0 0 25px rgba(255,215,0,0.6))' }}
                                />
                            </button>
                            <div className="flex flex-col gap-1 items-center">
                                <p className="text-[12px] text-[#FFD700] font-bold tracking-[0.2em] uppercase">AI Masterpiece Ready</p>
                                <p className="text-[10px] text-white/40 tracking-widest uppercase">Click to Initialize Projection</p>
                            </div>
                        </div>
                    )}

                    {/* ─── CINEMATIC PROJECTION VIEW ─── */}
                    <AnimatePresence>
                        {isPlaying && (
                            <motion.div
                                initial={{ scale: 1.3, opacity: 0, filter: 'blur(20px)' }}
                                animate={{ scale: 1, opacity: 1, filter: 'blur(0px)' }}
                                exit={{ scale: 0.9, opacity: 0, filter: 'blur(10px)' }}
                                transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
                                className="absolute inset-0 z-30 flex flex-col items-center justify-center overflow-hidden"
                                style={{ borderRadius: isFullscreen ? '0px' : '16px' }}
                            >
                                {/* Aurora Gradient Background */}
                                <div className="projection-aurora" />

                                {/* Floating Particles */}
                                <div className="projection-particles">
                                    {[...Array(12)].map((_, i) => (
                                        <div
                                            key={i}
                                            className="projection-particle"
                                            style={{
                                                left: `${8 + Math.random() * 84}%`,
                                                top: `${8 + Math.random() * 84}%`,
                                                width: `${2 + Math.random() * 4}px`,
                                                height: `${2 + Math.random() * 4}px`,
                                                animationDelay: `${Math.random() * 5}s`,
                                                animationDuration: `${4 + Math.random() * 6}s`,
                                            }}
                                        />
                                    ))}
                                </div>

                                {/* Cinematic Title Overlay */}
                                <motion.div
                                    initial={{ y: 30, opacity: 0 }}
                                    animate={{ y: 0, opacity: 1 }}
                                    transition={{ delay: 0.6, duration: 0.8, ease: 'easeOut' }}
                                    className="relative z-40 flex flex-col items-center gap-4 px-6 text-center"
                                >
                                    {/* Glowing accent line */}
                                    <div style={{
                                        width: '60px', height: '2px', borderRadius: '1px',
                                        background: 'linear-gradient(90deg, transparent, #FFD700, transparent)',
                                        boxShadow: '0 0 15px rgba(255,215,0,0.6)',
                                        marginBottom: '8px'
                                    }} />

                                    <h2 style={{
                                        fontFamily: "'Montserrat', sans-serif",
                                        fontSize: 'clamp(18px, 4vw, 36px)',
                                        fontWeight: 700,
                                        letterSpacing: '0.06em',
                                        color: '#FFFFFF',
                                        textShadow: '0 0 30px rgba(255,215,0,0.5), 0 0 60px rgba(255,215,0,0.2), 0 2px 10px rgba(0,0,0,0.8)',
                                        lineHeight: 1.3,
                                        maxWidth: '80%',
                                    }}>
                                        {uploadedFile?.name?.replace(/\.[^/.]+$/, '') || 'Untitled Project'}
                                    </h2>

                                    <p style={{
                                        fontSize: '10px',
                                        fontWeight: 600,
                                        letterSpacing: '0.25em',
                                        textTransform: 'uppercase',
                                        color: 'rgba(0,240,255,0.7)',
                                        textShadow: '0 0 10px rgba(0,240,255,0.4)',
                                    }}>
                                        AI Generated &bull; Neural Synthesis V4
                                    </p>

                                    {/* Animated equalizer bars — synced with speech */}
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 1.2 }}
                                        className="flex items-end gap-[3px] mt-4"
                                        style={{ height: '20px' }}
                                    >
                                        {[...Array(7)].map((_, i) => (
                                            <div
                                                key={i}
                                                className={`projection-eq-bar ${isSpeaking ? 'eq-active' : 'eq-idle'}`}
                                                style={{
                                                    animationDelay: `${i * 0.15}s`,
                                                    width: '3px',
                                                    borderRadius: '1.5px',
                                                }}
                                            />
                                        ))}
                                    </motion.div>

                                    {/* Visible Narration Subtitle (shows WHAT is being read) */}
                                    {narrationPreview && (
                                        <motion.div
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: 1.8, duration: 0.6 }}
                                            style={{
                                                maxWidth: '85%',
                                                marginTop: '16px',
                                                padding: '10px 16px',
                                                background: 'rgba(0,0,0,0.5)',
                                                backdropFilter: 'blur(8px)',
                                                borderRadius: '10px',
                                                border: '1px solid rgba(255,255,255,0.08)',
                                            }}
                                        >
                                            <p style={{
                                                fontSize: '11px',
                                                lineHeight: 1.6,
                                                color: 'rgba(255,255,255,0.6)',
                                                fontFamily: "'Inter', sans-serif",
                                                fontStyle: 'italic',
                                                textAlign: 'center',
                                                direction: narrationPreview.match(/[\u0600-\u06FF]/) ? 'rtl' : 'ltr',
                                            }}>
                                                "{narrationPreview}..."
                                            </p>
                                        </motion.div>
                                    )}
                                </motion.div>

                                {/* Top Control Bar: Mute + Close */}
                                <div className="absolute top-4 right-4 z-50 flex items-center gap-2">
                                    {/* Mute / Unmute Toggle */}
                                    <button
                                        onClick={toggleMute}
                                        className="cursor-pointer"
                                        style={{
                                            background: 'rgba(255,255,255,0.1)',
                                            backdropFilter: 'blur(8px)',
                                            WebkitBackdropFilter: 'blur(8px)',
                                            border: '1px solid rgba(255,255,255,0.15)',
                                            borderRadius: '12px',
                                            padding: '8px',
                                            color: isMuted ? 'rgba(255,100,100,0.8)' : 'rgba(255,255,255,0.7)',
                                            transition: 'all 0.3s ease',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                        }}
                                        onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.2)'; }}
                                        onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; }}
                                        title={isMuted ? 'Unmute' : 'Mute'}
                                    >
                                        {isMuted ? <VolumeX size={18} strokeWidth={2} /> : <Volume2 size={18} strokeWidth={2} />}
                                    </button>

                                    {/* Close / Stop Button */}
                                    <button
                                        onClick={handleStopProjection}
                                        className="cursor-pointer"
                                        style={{
                                            background: 'rgba(255,255,255,0.1)',
                                            backdropFilter: 'blur(8px)',
                                            WebkitBackdropFilter: 'blur(8px)',
                                            border: '1px solid rgba(255,255,255,0.15)',
                                            borderRadius: '12px',
                                            padding: '8px',
                                            color: 'rgba(255,255,255,0.7)',
                                            transition: 'all 0.3s ease',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                        }}
                                        onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.2)'; e.currentTarget.style.color = '#fff'; }}
                                        onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.1)'; e.currentTarget.style.color = 'rgba(255,255,255,0.7)'; }}
                                        title="Stop Projection"
                                    >
                                        <X size={18} strokeWidth={2} />
                                    </button>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Corner Scan Lines */}
                    <div className="absolute top-3 left-3 w-6 h-6 border-t border-l border-white/10 rounded-tl-md" />
                    <div className="absolute top-3 right-3 w-6 h-6 border-t border-r border-white/10 rounded-tr-md" />
                    <div className="absolute bottom-3 left-3 w-6 h-6 border-b border-l border-white/10 rounded-bl-md" />
                    <div className="absolute bottom-3 right-3 w-6 h-6 border-b border-r border-white/10 rounded-br-md" />

                    {/* Fullscreen Smart Toggle Button */}
                    <button onClick={() => setIsFullscreen(!isFullscreen)}
                        className="absolute bottom-4 right-4 text-white/50 hover:text-white transition-colors cursor-pointer p-2 rounded-xl"
                        style={{
                            background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)',
                            border: '1px solid rgba(255,255,255,0.1)', boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                            zIndex: 10000
                        }}
                        title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}>
                        {isFullscreen ? <Minimize2 size={18} strokeWidth={2} /> : <Maximize2 size={18} strokeWidth={2} />}
                    </button>

                </div>

                {/* ─── PROCESSING ENGINE STATUS BAR ─── */}
                <div className="mt-4" style={{
                    background: 'rgba(0,0,0,0.4)', borderRadius: '12px', padding: '12px 16px',
                    border: '1px solid rgba(255,255,255,0.06)',
                }}>
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-[9px] font-bold tracking-widest uppercase text-white/40">Processing Engine</span>
                        <span className="text-[9px] font-bold tracking-widest uppercase" style={{ color: isProcessing ? '#FFD700' : '#00F0FF' }}>
                            {isProcessing ? 'ACTIVE' : 'STANDBY'}
                        </span>
                    </div>
                    <div style={{
                        height: '6px', borderRadius: '3px', overflow: 'hidden',
                        background: 'rgba(255,255,255,0.05)',
                        boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.5)',
                        position: 'relative'
                    }}>
                        <div style={{
                            width: `${progress}%`, height: '100%', borderRadius: '3px',
                            background: isProcessing || isReady ? 'linear-gradient(90deg, #FFD700, #00F0FF, #FFD700)' : 'transparent',
                            backgroundSize: '200% 100%',
                            boxShadow: isProcessing || isReady ? '0 0 10px #FFD700, 0 0 20px rgba(255,215,0,0.5)' : 'none',
                            transition: 'width 0.2s linear',
                            animation: isProcessing ? 'progressLiquid 2s linear infinite' : 'none'
                        }} />
                    </div>
                    <p className="text-[9px] font-bold tracking-widest uppercase text-white/25 mt-2" style={{ fontFamily: "'Inter', monospace" }}>
                        {statusText}
                    </p>
                </div>

                {/* ─── ACTION BAR (Trash & Archive) ─── */}
                {(isReady || isPlaying) && (
                    <div className="flex justify-center mt-4 animate-fade-in-up">
                        <div style={{
                            background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(10px)', WebkitBackdropFilter: 'blur(10px)',
                            border: '1px solid rgba(255,255,255,0.1)', borderRadius: '30px', padding: '8px 20px',
                            display: 'flex', gap: '16px'
                        }}>
                            <button onClick={handlePurge} className="action-btn-purge p-2 rounded-full flex items-center justify-center bg-transparent border-none cursor-pointer outline-none">
                                <Trash2 size={20} strokeWidth={1.5} />
                            </button>
                            <button onClick={handleSave} className="action-btn-save p-2 rounded-full flex items-center justify-center bg-transparent border-none cursor-pointer outline-none">
                                <FolderPlus size={20} strokeWidth={1.5} />
                            </button>
                            {/* ─── NEURAL EXAM TRIGGER ─── */}
                            <div style={{ width: '1px', height: '24px', background: 'rgba(255,255,255,0.1)', alignSelf: 'center' }} />
                            <button
                                onClick={() => setShowHologram(true)}
                                className="p-2 rounded-full flex items-center justify-center bg-transparent border-none cursor-pointer outline-none"
                                style={{
                                    color: '#00F0FF',
                                    filter: 'drop-shadow(0 0 6px rgba(0,240,255,0.5))',
                                    animation: 'portalPulse 2.5s ease-in-out infinite',
                                    transition: 'all 0.3s ease'
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.filter = 'drop-shadow(0 0 12px rgba(0,240,255,0.8))';
                                    e.currentTarget.style.transform = 'scale(1.15)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.filter = 'drop-shadow(0 0 6px rgba(0,240,255,0.5))';
                                    e.currentTarget.style.transform = 'scale(1)';
                                }}
                                title="Activate Neural Test"
                            >
                                <BrainCircuit size={20} strokeWidth={1.5} />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );

    /* ─── The Input Console (Upload + Parameters + Button) ─── */
    const inputConsole = (
        <div className="ai-lab-console" style={{ width: '100%' }}>
            <div style={{
                background: 'rgba(255,255,255,0.03)', backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255,215,0,0.2)', borderRadius: '20px', padding: '16px'
            }}>
                <h3 className="text-[11px] font-bold tracking-[0.12em] uppercase text-[#FFD700] mb-4 flex items-center gap-2">
                    <Zap size={14} /> Input Console
                </h3>

                {/* ─── HOLOGRAPHIC DROPZONE ─── */}
                <div
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className="relative cursor-pointer"
                    style={{
                        border: `2px dashed ${isDragOver ? '#FFD700' : 'rgba(255,215,0,0.3)'}`,
                        borderRadius: '16px', padding: '24px 16px', textAlign: 'center',
                        background: isDragOver ? 'rgba(255,215,0,0.08)' : 'rgba(255,215,0,0.02)',
                        boxShadow: isDragOver ? '0 0 30px rgba(255,215,0,0.15), inset 0 0 20px rgba(255,215,0,0.05)' : 'none',
                        transition: 'all 0.4s ease',
                    }}
                >
                    <input ref={fileInputRef} type="file" accept=".pdf,.txt,.doc,.docx" className="hidden" onChange={handleFileSelect} />
                    <UploadCloud size={32} strokeWidth={1.5} className="mx-auto mb-2" style={{ color: isDragOver ? '#FFD700' : 'rgba(255,215,0,0.6)', filter: isDragOver ? 'drop-shadow(0 0 15px #FFD700)' : 'none', transition: 'all 0.4s ease' }} />
                    {uploadedFile ? (
                        <div>
                            <p className="text-[11px] font-bold text-[#FFD700] tracking-wide break-all">{uploadedFile.name}</p>
                            <p className="text-[10px] text-white/40 mt-1">Data Core Initialized</p>
                        </div>
                    ) : (
                        <div>
                            <p className="text-[11px] font-bold text-white/60 tracking-wide">Initialize Data Core</p>
                            <p className="text-[10px] text-white/30 mt-1">Drop PDF / Text file here</p>
                        </div>
                    )}
                </div>

                {/* ─── SYNTHESIS PARAMETERS ─── */}
                <div className="mt-5 flex flex-col gap-3">
                    <CustomDropdown
                        id="outputStyle"
                        label="Output Style"
                        icon={Film}
                        value={outputStyle}
                        onChange={setOutputStyle}
                        options={[
                            { value: 'clinical', label: 'Clinical Presentation' },
                            { value: 'academic', label: 'Academic Lecture' },
                            { value: '3d-animation', label: '3D Animation' },
                            { value: 'explainer', label: 'Explainer Video' }
                        ]}
                    />

                    <CustomDropdown
                        id="voiceEngine"
                        label="Voice Engine"
                        icon={Volume2}
                        value={voiceEngine}
                        onChange={setVoiceEngine}
                        options={[
                            { value: 'neural-female', label: 'Neural Female' },
                            { value: 'neural-male', label: 'Neural Male' },
                            { value: 'synthetic', label: 'Synthetic Neutral' }
                        ]}
                    />

                    <CustomDropdown
                        id="duration"
                        label="Duration"
                        icon={Clock}
                        value={duration}
                        onChange={setDuration}
                        options={[
                            { value: '2min', label: '2 Min Summary' },
                            { value: '5min', label: '5 Min Overview' },
                            { value: '10min', label: '10 Min Deep Dive' }
                        ]}
                    />
                </div>

                {/* ─── THE REACTOR BUTTON ─── */}
                <button
                    onClick={handleSynthesize}
                    disabled={!uploadedFile || isProcessing}
                    className="w-full mt-5 relative overflow-hidden transition-all duration-500 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{
                        padding: '14px 20px', borderRadius: '16px',
                        background: uploadedFile ? 'linear-gradient(135deg, #FFD700 0%, #FF8C00 100%)' : 'rgba(255,215,0,0.15)',
                        border: uploadedFile ? '1px solid rgba(255,215,0,0.8)' : '1px solid rgba(255,215,0,0.2)',
                        boxShadow: uploadedFile && !isProcessing ? '0 0 25px rgba(255,215,0,0.4), 0 0 60px rgba(255,215,0,0.15), inset 0 1px 0 rgba(255,255,255,0.3)' : 'none',
                        animation: uploadedFile && !isProcessing ? 'reactorPulse 2s ease-in-out infinite' : 'none',
                    }}
                >
                    <div className="flex items-center justify-center gap-2">
                        <Sparkles size={16} strokeWidth={2} color={uploadedFile && !isSynthesizing ? '#1a0a00' : '#FFD700'} />
                        <span className="text-[12px] font-black tracking-[0.15em] uppercase" style={{ color: uploadedFile && !isSynthesizing ? '#1a0a00' : '#FFD700' }}>
                            {isSynthesizing ? 'SYNTHESIZING...' : isReady ? 'RE-SYNTHESIZE' : 'SYNTHESIZE VIDEO'}
                        </span>
                    </div>
                </button>
            </div>
        </div>
    );

    return (
        <motion.div
            initial={{ scale: 0.92, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 z-50 overflow-y-auto overflow-x-hidden w-full h-dvh text-white"
            style={{ fontFamily: "'Montserrat', sans-serif" }}
        >
            {/* ─── AMBIENT BACKGROUND ─── */}
            <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
                <div className="absolute top-[-25%] left-[-10%] w-[55%] h-[55%] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255,215,0,0.12) 0%, transparent 70%)', filter: 'blur(150px)' }} />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full" style={{ background: 'radial-gradient(circle, rgba(0,240,255,0.1) 0%, transparent 70%)', filter: 'blur(150px)' }} />
                <div className="absolute top-[50%] left-[50%] -translate-x-1/2 -translate-y-1/2 w-[35%] h-[35%] rounded-full" style={{ background: 'radial-gradient(circle, rgba(255,215,0,0.06) 0%, transparent 70%)', filter: 'blur(120px)' }} />
            </div>

            {/* ─── TOP BAR ─── */}
            <div className="sticky top-0 left-0 w-full px-4 md:px-8 py-3 flex items-center justify-between z-100 border-b border-white/5"
                style={{ background: 'rgba(5,5,16,0.5)', backdropFilter: 'blur(30px)', WebkitBackdropFilter: 'blur(30px)' }}>
                <div className="flex items-center gap-3">
                    <button onClick={() => onNavigate('academic-hub')}
                        className="flex items-center gap-2 px-3 py-2 rounded-full border border-white/10 text-white/70 hover:text-white hover:bg-white/5 hover:border-[#FFD700]/30 transition-all cursor-pointer"
                        style={{ background: 'rgba(255,255,255,0.03)' }}>
                        <ChevronLeft size={16} strokeWidth={2} />
                        <span className="text-[10px] font-bold tracking-[0.12em] uppercase">Back</span>
                    </button>
                    <div className="hidden md:block ml-1">
                        <h2 className="text-[18px] font-bold tracking-tight text-white flex items-center gap-2">
                            <BrainCircuit size={20} strokeWidth={1.5} className="text-[#FFD700]" style={{ filter: 'drop-shadow(0 0 8px rgba(255,215,0,0.6))' }} />
                            AI Generative Lab
                        </h2>
                        <p className="text-[9px] text-[#FFD700] font-semibold tracking-[0.2em] uppercase">Neural Synthesis Engine V4</p>
                    </div>
                    {/* Mobile title */}
                    <h2 className="md:hidden text-[14px] font-bold tracking-tight text-white flex items-center gap-2">
                        <BrainCircuit size={16} strokeWidth={1.5} className="text-[#FFD700]" />
                        AI Lab
                    </h2>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 rounded-full bg-[#00FF9D] animate-pulse" style={{ boxShadow: '0 0 8px #00FF9D' }} />
                    <span className="text-[9px] font-bold tracking-widest uppercase text-[#00FF9D] hidden sm:inline">Online</span>
                </div>
            </div>

            {/* ─── CONTROL ROOM LAYOUT ─── */}
            <div className="relative z-10 w-full max-w-7xl mx-auto p-4 md:p-8">
                <div className="ai-lab-grid" style={{ display: 'flex', flexDirection: 'column', gap: '20px', width: '100%', boxSizing: 'border-box' }}>
                    {/* Mobile: Preview on top, Console below. Desktop: CSS order flips them */}
                    {previewStage}
                    {inputConsole}
                </div>
            </div>

            {/* ─── HOLOGRAPHIC PORTAL OVERLAY ─── */}
            <AnimatePresence>
                {showHologram && (
                    <motion.div
                        initial={{ scale: 1.3, opacity: 0, filter: 'blur(30px)' }}
                        animate={{ scale: 1, opacity: 1, filter: 'blur(0px)' }}
                        exit={{ scale: 0.8, opacity: 0, filter: 'blur(20px)' }}
                        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                        className="fixed inset-0 z-50"
                    >
                        <AITestingCenterScreen
                            directText={generatedContent}
                            onExitPortal={() => setShowHologram(false)}
                            onNavigate={onNavigate}
                        />
                    </motion.div>
                )}
            </AnimatePresence>

            {/* ─── KEYFRAMES ─── */}
            <style>{`
                @keyframes reactorPulse {
                    0%, 100% { box-shadow: 0 0 25px rgba(255,215,0,0.4), 0 0 60px rgba(255,215,0,0.15), inset 0 1px 0 rgba(255,255,255,0.3); }
                    50% { box-shadow: 0 0 40px rgba(255,215,0,0.6), 0 0 80px rgba(255,215,0,0.25), inset 0 1px 0 rgba(255,255,255,0.4); }
                }
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                
                /* ─── Scanning Light & Liquid Energy Animations ─── */
                @keyframes scanMove {
                    0% { left: -100%; opacity: 0; }
                    10% { opacity: 0.5; }
                    50% { opacity: 1; }
                    90% { opacity: 0.5; }
                    100% { left: 100%; opacity: 0; }
                }
                .scanning-light {
                    position: absolute;
                    top: 0; bottom: 0;
                    width: 30%;
                    background: linear-gradient(90deg, transparent, rgba(0, 240, 255, 0.1) 40%, rgba(255, 215, 0, 0.3) 50%, rgba(0, 240, 255, 0.1) 60%, transparent);
                    animation: scanMove 3s cubic-bezier(0.25, 1, 0.5, 1) infinite;
                    pointer-events: none;
                    z-index: 5;
                }
                
                @keyframes progressLiquid {
                    0% { background-position: 100% 0; }
                    100% { background-position: -100% 0; }
                }

                /* ─── Action Bar Animations & Styles ─── */
                @keyframes fadeInUp {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .animate-fade-in-up {
                    animation: fadeInUp 0.4s ease-out forwards;
                }

                /* ─── Cinematic Projection Styles ─── */
                .projection-aurora {
                    position: absolute;
                    inset: 0;
                    background: linear-gradient(
                        135deg,
                        #050510 0%,
                        #0a0a2e 15%,
                        #0d1b3e 30%,
                        #1a0a2e 45%,
                        #050520 60%,
                        #0a1628 75%,
                        #050510 100%
                    );
                    background-size: 400% 400%;
                    animation: auroraShift 12s ease-in-out infinite;
                }
                .projection-aurora::after {
                    content: '';
                    position: absolute;
                    inset: 0;
                    background:
                        radial-gradient(ellipse at 20% 50%, rgba(255,215,0,0.08) 0%, transparent 50%),
                        radial-gradient(ellipse at 80% 30%, rgba(0,240,255,0.06) 0%, transparent 50%),
                        radial-gradient(ellipse at 50% 80%, rgba(138,43,226,0.05) 0%, transparent 50%);
                    animation: auroraShift 8s ease-in-out infinite reverse;
                }
                @keyframes auroraShift {
                    0%, 100% { background-position: 0% 50%; }
                    25% { background-position: 100% 25%; }
                    50% { background-position: 100% 50%; }
                    75% { background-position: 0% 75%; }
                }

                .projection-particles {
                    position: absolute;
                    inset: 0;
                    z-index: 35;
                    pointer-events: none;
                }
                .projection-particle {
                    position: absolute;
                    border-radius: 50%;
                    background: radial-gradient(circle, rgba(255,215,0,0.8), rgba(0,240,255,0.4));
                    box-shadow: 0 0 6px rgba(255,215,0,0.5);
                    animation: particleFloat 5s ease-in-out infinite;
                    opacity: 0.6;
                }
                @keyframes particleFloat {
                    0%, 100% { transform: translateY(0px) scale(1); opacity: 0.4; }
                    25% { transform: translateY(-15px) scale(1.2); opacity: 0.8; }
                    50% { transform: translateY(-8px) scale(0.9); opacity: 0.6; }
                    75% { transform: translateY(-20px) scale(1.1); opacity: 0.7; }
                }

                .projection-eq-bar {
                    background: linear-gradient(to top, #FFD700, #00F0FF);
                    box-shadow: 0 0 4px rgba(255,215,0,0.5);
                    transition: height 0.3s ease;
                }
                .projection-eq-bar.eq-active {
                    animation: eqBounce 0.8s ease-in-out infinite alternate;
                }
                .projection-eq-bar.eq-idle {
                    animation: none;
                    height: 4px !important;
                    opacity: 0.4;
                }
                @keyframes eqBounce {
                    0% { height: 4px; }
                    100% { height: 18px; }
                }
                .action-btn-purge {
                    filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.4));
                    color: #FFFFFF;
                    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                }
                .action-btn-purge:hover {
                    transform: scale(1.2);
                    filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.8));
                }
                .action-btn-save {
                    filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.4));
                    color: #FFFFFF;
                    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                }
                .action-btn-save:hover {
                    transform: scale(1.2);
                    filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.8));
                }

                /* ─── Custom Dropdown Styles ─── */
                .custom-dropdown-btn {
                    background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); 
                    border-radius: 10px; padding: 14px 16px; color: white; display: flex; 
                    justify-content: space-between; align-items: center; cursor: pointer; 
                    transition: all 0.3s ease;
                }
                .custom-dropdown-btn:hover {
                    border-color: rgba(0,240,255,0.3);
                    box-shadow: 0 0 15px rgba(0,240,255,0.1);
                }
                .custom-dropdown-menu {
                    position: absolute; width: 100%; top: 100%; left: 0;
                    background: rgba(10, 15, 25, 0.95); backdrop-filter: blur(20px); 
                    border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; 
                    margin-top: 8px; z-index: 100; overflow: hidden; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.8);
                }
                .custom-dropdown-item {
                    padding: 12px 16px; cursor: pointer; color: rgba(255,255,255,0.8); 
                    transition: all 0.2s ease; font-size: 12px; font-weight: 600;
                }
                .custom-dropdown-item:hover {
                    background: rgba(0, 240, 255, 0.15); color: #fff;
                    text-shadow: 0 0 8px rgba(0, 240, 255, 0.5);
                }
                
                /* Desktop: side-by-side with Input Console on left */
                @media (min-width: 768px) {
                    .ai-lab-grid {
                        flex-direction: row !important;
                        gap: 24px !important;
                    }
                    .ai-lab-console {
                        order: -1;
                        width: 350px !important;
                        flex-shrink: 0;
                    }
                    .ai-lab-preview {
                        flex: 1;
                        min-width: 0;
                    }
                }

                /* ─── Holographic Portal Pulse ─── */
                @keyframes portalPulse {
                    0%, 100% { box-shadow: 0 0 20px rgba(0,240,255,0.25), inset 0 0 12px rgba(168,85,247,0.15); }
                    50% { box-shadow: 0 0 30px rgba(0,240,255,0.45), inset 0 0 18px rgba(168,85,247,0.3); border-color: rgba(0,240,255,0.7); }
                }
            `}</style>
        </motion.div>
    );
}
