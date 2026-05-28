import { useState, useRef, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronLeft, ChevronDown, CloudUpload, File, Archive, Loader2 } from 'lucide-react';
import { useNavigation } from '../context/NavigationContext';
import { HoloFileCard } from '../components/HoloFileCard';
import { saveDocument, loadAllDocuments, deleteDocument, togglePinStatus } from '../utils/vaultDB';

/* ═══════════════════════════════════════════════════════════════
   CURRICULUM VAULT — Student Document Management
   Upload, organize, and read PDFs & study materials
   Persisted in IndexedDB via vaultDB utility
   ═══════════════════════════════════════════════════════════════ */

const STAGE_LABELS = { 1: 'STAGE 01', 2: 'STAGE 02', 3: 'STAGE 03', 4: 'STAGE 04' };

export default function CurriculumVaultScreen() {
    const { goBack } = useNavigation();

    // ── Vault state ──
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const [vaultLoading, setVaultLoading] = useState(true);
    const [activeStage, setActiveStage] = useState(1);
    const [stageDropdownOpen, setStageDropdownOpen] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    const [moduleName, setModuleName] = useState('');
    const [isDragging, setIsDragging] = useState(false);
    const [activeMenu, setActiveMenu] = useState(null);

    // ── PDF Reader state ──
    const [pdfUrl, setPdfUrl] = useState(null);
    const [activeSubject, setActiveSubject] = useState(null);

    const fileInputRef = useRef(null);
    const dropdownRef = useRef(null);

    // ── Load persisted documents from IndexedDB on mount ──
    useEffect(() => {
        loadAllDocuments()
            .then(docs => {
                setUploadedFiles(docs);
                setVaultLoading(false);
            })
            .catch(err => {
                console.error('Vault DB load error:', err);
                setVaultLoading(false);
            });
    }, []);

    // ── PDF reader: open/close ──
    useEffect(() => {
        if (activeSubject?.file) {
            const url = URL.createObjectURL(activeSubject.file);
            setPdfUrl(url);
            return () => URL.revokeObjectURL(url);
        } else {
            setPdfUrl(null);
        }
    }, [activeSubject]);

    // ── Close dropdown on outside click ──
    useEffect(() => {
        const handler = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setStageDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    // ── Drag & Drop handlers ──
    const handleDragOver = useCallback((e) => { e.preventDefault(); setIsDragging(true); }, []);
    const handleDragLeave = useCallback(() => setIsDragging(false), []);
    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file) setSelectedFile(file);
    }, []);
    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) setSelectedFile(file);
    };

    // ── Upload handler ──
    const handleUpload = async () => {
        if (!selectedFile || !moduleName.trim()) return;

        const newEntry = {
            id: `upload-${Date.now()}`,
            name: moduleName.trim(),
            fileName: selectedFile.name,
            fileSize: `${(selectedFile.size / 1024).toFixed(1)} KB`,
            stage: activeStage,
            stageId: activeStage,
            timestamp: new Date().toISOString(),
            file: selectedFile,
            isPinned: false,
        };

        setUploadedFiles(prev => [newEntry, ...prev]);
        setSelectedFile(null);
        setModuleName('');
        if (fileInputRef.current) fileInputRef.current.value = '';

        try {
            await saveDocument(newEntry);
        } catch (err) {
            console.error('Vault DB save error:', err);
        }
    };

    // ── Delete handler ──
    const handleDeleteFile = async (id) => {
        setUploadedFiles(prev => prev.filter(f => f.id !== id));
        try {
            await deleteDocument(id);
        } catch (err) {
            console.error('Vault DB delete error:', err);
        }
    };

    // ── Pin toggle ──
    const handleTogglePin = async (id, currentPinState) => {
        setUploadedFiles(prev => prev.map(f => f.id === id ? { ...f, isPinned: !currentPinState } : f));
        try {
            await togglePinStatus(id, !currentPinState);
        } catch (err) {
            console.error('Vault DB pin error:', err);
        }
    };

    // ── Filtered files for current stage ──
    const filesForStage = uploadedFiles
        .filter(f => f.stage === activeStage)
        .sort((a, b) => (b.isPinned ? 1 : 0) - (a.isPinned ? 1 : 0));

    // ═══════════════════════════════════════════
    //  PDF READER VIEW
    // ═══════════════════════════════════════════
    if (activeSubject && pdfUrl) {
        return (
            <div className="min-h-dvh w-full bg-[#0A0E17] flex flex-col pb-20">
                {/* Reader Header */}
                <header className="px-6 pt-12 pb-4 flex items-center gap-4 sticky top-0 bg-[#0A0E17]/90 backdrop-blur-xl z-40 border-b border-white/5">
                    <button
                        onClick={() => { setActiveSubject(null); setPdfUrl(null); }}
                        className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 transition-colors shrink-0"
                    >
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <div className="min-w-0 flex-1">
                        <h1 className="text-base font-bold text-white truncate">{activeSubject.name}</h1>
                        <p className="text-[11px] text-cyan-400/70 font-mono tracking-wider uppercase">PDF Reader</p>
                    </div>
                </header>

                {/* PDF Iframe */}
                <div className="flex-1 px-4 pt-4 pb-24">
                    <div className="w-full h-[calc(100dvh-200px)] rounded-2xl overflow-hidden border border-cyan-500/20 shadow-[0_0_40px_rgba(0,0,0,0.5)]">
                        <iframe
                            src={`${pdfUrl}#toolbar=0&navpanes=0&scrollbar=0`}
                            title="PDF Reader"
                            className="w-full h-full bg-white"
                            style={{ border: 'none' }}
                        />
                    </div>
                </div>
            </div>
        );
    }

    // ═══════════════════════════════════════════
    //  VAULT MAIN VIEW
    // ═══════════════════════════════════════════
    return (
        <div className="min-h-dvh w-full bg-[#0A0E17] flex flex-col pb-32 overflow-y-auto no-scrollbar">

            {/* Header */}
            <header className="px-6 pt-12 pb-4 flex items-center gap-4 sticky top-0 bg-[#0A0E17]/80 backdrop-blur-xl z-40 border-b border-white/5">
                <button
                    onClick={goBack}
                    className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 transition-colors shrink-0"
                >
                    <ChevronLeft className="w-5 h-5" />
                </button>
                <div className="flex-1">
                    <h1 className="text-xl font-bold text-white tracking-wide flex items-center gap-2">
                        <Archive className="w-5 h-5 text-amber-400" />
                        Curriculum Vault
                    </h1>
                    <p className="text-[11px] text-slate-400 font-medium mt-0.5">Upload & organize your study materials</p>
                </div>

                {/* Stage Selector */}
                <div className="relative" ref={dropdownRef}>
                    <button
                        onClick={() => setStageDropdownOpen(!stageDropdownOpen)}
                        className="flex items-center gap-2 px-3 py-2 bg-white/5 border border-white/10 rounded-xl text-xs font-mono font-bold text-cyan-300 tracking-wider uppercase hover:bg-white/10 transition-colors"
                    >
                        {STAGE_LABELS[activeStage]}
                        <ChevronDown size={14} className={`transition-transform ${stageDropdownOpen ? 'rotate-180' : ''}`} />
                    </button>

                    <AnimatePresence>
                        {stageDropdownOpen && (
                            <motion.div
                                initial={{ opacity: 0, y: -8, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: -8, scale: 0.95 }}
                                transition={{ duration: 0.2 }}
                                className="absolute right-0 top-12 bg-[#0f172a]/95 backdrop-blur-2xl border border-cyan-500/30 rounded-xl shadow-[0_0_30px_rgba(0,0,0,0.5)] overflow-hidden z-50"
                            >
                                {Object.entries(STAGE_LABELS).map(([key, label]) => (
                                    <button
                                        key={key}
                                        onClick={() => { setActiveStage(Number(key)); setStageDropdownOpen(false); }}
                                        className={`w-full px-5 py-3 text-left text-xs font-mono font-bold tracking-wider uppercase transition-colors ${
                                            activeStage === Number(key)
                                                ? 'text-cyan-300 bg-cyan-500/15'
                                                : 'text-slate-400 hover:text-white hover:bg-white/5'
                                        }`}
                                    >
                                        {label}
                                    </button>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </header>

            <div className="px-6 pt-6 max-w-2xl mx-auto w-full flex flex-col gap-6">

                {/* ── 1. DROP-ZONE ── */}
                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`relative overflow-hidden cursor-pointer transition-all duration-300 flex flex-col items-center justify-center py-12 px-6 text-center group rounded-2xl ${
                        isDragging
                            ? 'bg-cyan-500/10 border-2 border-dashed border-cyan-400 scale-[1.01] shadow-[0_0_40px_rgba(34,211,238,0.15)]'
                            : 'bg-white/5 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.3)] hover:border-cyan-400/40 hover:shadow-[0_0_15px_rgba(34,211,238,0.1)]'
                    }`}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.docx,.doc,.pptx,.txt"
                        className="hidden"
                        onChange={handleFileSelect}
                    />

                    <div className="bg-amber-500/10 p-4 rounded-full mb-4 group-hover:bg-amber-500/20 transition-all duration-300 border border-amber-500/20">
                        <CloudUpload size={32} className="text-amber-400 group-hover:scale-110 transition-transform duration-300" />
                    </div>

                    {selectedFile ? (
                        <>
                            <p className="text-sm font-mono text-cyan-300 uppercase tracking-wider mb-3">File Selected</p>
                            <div className="flex items-center gap-3 bg-black/40 border border-cyan-500/30 rounded-lg px-4 py-3">
                                <File size={16} className="text-cyan-400 shrink-0" />
                                <span className="text-sm font-medium text-cyan-50 truncate max-w-[200px]">{selectedFile.name}</span>
                                <span className="text-xs font-mono text-cyan-500/70 shrink-0">{(selectedFile.size / 1024).toFixed(1)} KB</span>
                            </div>
                            <p className="text-[10px] font-mono text-slate-500 mt-3 uppercase tracking-wider">Tap to change file</p>
                        </>
                    ) : (
                        <>
                            <p className="text-sm font-semibold text-white mb-1">Drag & Drop or Tap to Upload</p>
                            <p className="text-xs text-slate-500 mb-4">PDF, DOCX, PPTX, TXT</p>
                            <div className="px-5 py-2 bg-transparent text-amber-400 font-mono text-xs uppercase tracking-wider rounded-lg border border-amber-500/30 group-hover:border-amber-400/60 transition-all">
                                Browse Files
                            </div>
                        </>
                    )}
                </div>

                {/* ── 2. DOCUMENT TITLE + UPLOAD BUTTON ── */}
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-5">
                    <label className="text-xs font-mono text-slate-400 mb-2 block uppercase tracking-wider">Document Title</label>
                    <input
                        type="text"
                        value={moduleName}
                        onChange={(e) => setModuleName(e.target.value)}
                        placeholder="e.g. Hematology Chapter 3 Notes..."
                        className="w-full bg-black/30 border border-white/10 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/30 text-white rounded-xl placeholder-slate-500 transition-all py-3 px-4 outline-none text-sm mb-4"
                    />
                    <button
                        onClick={handleUpload}
                        disabled={!selectedFile || !moduleName.trim()}
                        className={`w-full py-3 rounded-xl font-bold text-sm tracking-wider uppercase transition-all flex items-center justify-center gap-3 ${
                            selectedFile && moduleName.trim()
                                ? 'bg-amber-500/15 border border-amber-400/40 hover:bg-amber-500/30 text-amber-300 cursor-pointer active:scale-[0.98]'
                                : 'bg-white/5 text-slate-600 border border-white/5 cursor-not-allowed'
                        }`}
                    >
                        <CloudUpload size={18} />
                        Save to Vault
                    </button>
                </div>

                {/* ── 3. STORED FILES ── */}
                <div>
                    <p className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider mb-4 border-b border-white/5 pb-3">
                        Secured Databanks — {STAGE_LABELS[activeStage]}
                        <span className="ml-2 text-cyan-400/60">{filesForStage.length} file{filesForStage.length !== 1 ? 's' : ''}</span>
                    </p>

                    {vaultLoading ? (
                        <div className="flex flex-col items-center justify-center py-20 gap-3">
                            <Loader2 size={24} className="text-cyan-400 animate-spin" />
                            <p className="text-cyan-400/60 text-xs font-mono tracking-wider uppercase">Loading vault...</p>
                        </div>
                    ) : filesForStage.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-16 bg-white/5 backdrop-blur-md rounded-2xl border border-white/5 border-dashed">
                            <Archive size={32} className="text-slate-600 mb-3" />
                            <p className="text-slate-500 text-sm">No files in {STAGE_LABELS[activeStage]}</p>
                            <p className="text-slate-600 text-xs mt-1">Upload your first document above</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 gap-4">
                            {filesForStage.map((file, idx) => (
                                <HoloFileCard
                                    key={file.id}
                                    file={file}
                                    idx={idx}
                                    onClick={() => {
                                        if (activeMenu === file.id) return;
                                        setActiveSubject({ title: file.name, name: file.name, file: file.file });
                                    }}
                                    onDelete={handleDeleteFile}
                                    activeMenu={activeMenu}
                                    setActiveMenu={setActiveMenu}
                                    onTogglePin={handleTogglePin}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
