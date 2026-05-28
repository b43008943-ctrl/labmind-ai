import { X, UploadCloud, Activity, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function ActionModal({ isOpen, onClose, onImportData }) {
    const [isProcessing, setIsProcessing] = useState(false);
    const [isRendered, setIsRendered] = useState(false);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setIsRendered(true);
            // Delay slightly to ensure DOM is painted before transition starts
            const t = setTimeout(() => setIsVisible(true), 10);
            return () => clearTimeout(t);
        } else {
            setIsVisible(false);
            setIsProcessing(false);
            // Wait for 300ms transition to finish before unmounting
            const t = setTimeout(() => setIsRendered(false), 300);
            return () => clearTimeout(t);
        }
    }, [isOpen]);

    const handleImport = () => {
        setIsProcessing(true);
        setTimeout(() => {
            onImportData();
            setIsProcessing(false);
            onClose();
        }, 1500);
    };

    if (!isRendered) return null;

    return (
        <div
            className={`absolute inset-0 z-100 flex items-center justify-center transition-opacity duration-300 ease-out ${isVisible ? 'opacity-100' : 'opacity-0'}`}
            style={{ background: 'rgba(0, 5, 10, 0.8)', backdropFilter: 'blur(16px)' }}
            onClick={onClose}
        >
            <div
                className={`w-[85%] max-w-[400px] flex flex-col p-6 transform transition-all duration-300 ease-out ${isVisible ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 translate-y-4'}`}
                style={{
                    background: 'rgba(10, 15, 25, 0.95)',
                    border: '1px solid rgba(0, 242, 255, 0.4)',
                    borderRadius: '24px',
                    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.8), 0 0 30px rgba(0, 242, 255, 0.2), inset 0 0 20px rgba(0, 242, 255, 0.1)'
                }}
                onClick={e => e.stopPropagation()}
            >
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-white text-lg font-bold tracking-wide">Initialize Analysis</h3>
                    <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors outline-none cursor-pointer">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="flex flex-col gap-3">
                    <button
                        type="button"
                        onClick={handleImport}
                        disabled={isProcessing}
                        className="w-full flex items-center p-4 group cursor-pointer transition-all hover:bg-cyan-900/40 hover:border-cyan-400/50 hover:shadow-[0_0_20px_rgba(0,255,255,0.15)] active:scale-[0.98]"
                        style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                    >
                        {isProcessing ? (
                            <>
                                <div className="w-10 h-10 rounded-lg flex items-center justify-center mr-4" style={{ background: 'rgba(0, 242, 255, 0.1)', border: '1px solid rgba(0, 242, 255, 0.3)', boxShadow: '0 0 15px rgba(0, 242, 255, 0.2)', color: '#00f2ff' }}>
                                    <Loader2 className="w-5 h-5 animate-spin" strokeWidth={2.5} />
                                </div>
                                <span className="text-white font-medium text-sm tracking-wide drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">AI Analyzing Sample...</span>
                            </>
                        ) : (
                            <>
                                <div className="w-10 h-10 rounded-lg flex items-center justify-center mr-4" style={{ background: 'rgba(0, 242, 255, 0.1)', border: '1px solid rgba(0, 242, 255, 0.3)', boxShadow: '0 0 15px rgba(0, 242, 255, 0.2)', color: '#00f2ff' }}>
                                    <UploadCloud className="w-5 h-5" strokeWidth={2.5} />
                                </div>
                                <span className="text-white font-medium text-sm tracking-wide group-hover:text-cyan-300 transition-colors">Import Biological Data</span>
                            </>
                        )}
                    </button>

                    <button
                        type="button"
                        className="w-full flex items-center p-4 group cursor-pointer transition-all hover:bg-cyan-900/40 hover:border-cyan-400/50 hover:shadow-[0_0_20px_rgba(0,255,255,0.15)] active:scale-[0.98]"
                        style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                    >
                        <div className="w-10 h-10 rounded-lg flex items-center justify-center mr-4" style={{ background: 'rgba(0, 242, 255, 0.1)', border: '1px solid rgba(0, 242, 255, 0.3)', boxShadow: '0 0 15px rgba(0, 242, 255, 0.2)', color: '#00f2ff' }}>
                            <Activity className="w-5 h-5" strokeWidth={2.5} />
                        </div>
                        <span className="text-white font-medium text-sm tracking-wide group-hover:text-cyan-300 transition-colors">Run Virtual Simulation</span>
                    </button>
                </div>
            </div>
        </div>
    );
}
