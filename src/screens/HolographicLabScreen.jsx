import React, { useState, Suspense } from 'react';
import { ChevronLeft, AlertTriangle, Box, Loader2, RefreshCw } from 'lucide-react';
import { useNavigation } from '../context/NavigationContext';

/* ═══════════════════════════════════════════════════════════════
   HOLOGRAPHIC LAB — 3D Interactive Biology Models
   Robust wrapper with error/loading states for BioHoloExplorer
   ═══════════════════════════════════════════════════════════════ */

// Lazy-load the heavy Three.js component to avoid blocking the route
const BioHoloExplorer = React.lazy(() => import('../components/BioHoloExplorer'));

// Loading fallback while Three.js bundles & initializes
function LoadingFallback() {
    return (
        <div className="fixed inset-0 z-50 bg-[#050a19] flex flex-col items-center justify-center gap-6">
            <div className="w-20 h-20 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                <Box size={40} className="text-cyan-400 animate-pulse" />
            </div>
            <div className="flex flex-col items-center gap-2">
                <Loader2 size={24} className="text-cyan-400 animate-spin" />
                <p className="text-sm text-cyan-400 font-mono tracking-wider uppercase">Loading 3D Engine...</p>
                <p className="text-xs text-slate-500">Initializing WebGL context</p>
            </div>
        </div>
    );
}

// Error boundary specific to this screen
class HoloErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    componentDidCatch(error, errorInfo) {
        console.error('[HolographicLabScreen] 3D Render Error:', error, errorInfo?.componentStack);
    }
    render() {
        if (this.state.hasError) {
            return this.props.fallback(this.state.error, () => this.setState({ hasError: false, error: null }));
        }
        return this.props.children;
    }
}

export default function HolographicLabScreen() {
    const { goBack } = useNavigation();
    const [key, setKey] = useState(0); // Force remount on retry

    const errorFallback = (error, retry) => (
        <div className="fixed inset-0 z-50 bg-[#050a19] flex flex-col items-center justify-center gap-6 px-6 text-center">
            <div className="w-20 h-20 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                <Box size={40} className="text-red-400" />
            </div>
            <h2 className="text-lg font-bold text-white">3D Engine Error</h2>
            <p className="text-sm text-slate-400 max-w-sm leading-relaxed">
                The WebGL rendering engine encountered an error. This can happen if your browser or device doesn't fully support 3D rendering.
            </p>
            <div className="bg-black/40 border border-white/10 rounded-xl p-3 max-w-sm w-full">
                <p className="text-xs text-red-400 font-mono break-words">{error?.message || 'Unknown error'}</p>
            </div>
            <div className="flex gap-3">
                <button
                    onClick={() => { setKey(k => k + 1); retry(); }}
                    className="flex items-center gap-2 px-5 py-2.5 bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 rounded-xl font-semibold text-xs tracking-wide hover:bg-cyan-500/25 transition-all"
                >
                    <RefreshCw size={14} /> Retry
                </button>
                <button
                    onClick={goBack}
                    className="flex items-center gap-2 px-5 py-2.5 bg-slate-700/30 border border-white/10 text-slate-300 rounded-xl font-semibold text-xs tracking-wide hover:bg-slate-700/50 transition-all"
                >
                    <ChevronLeft size={14} /> Go Back
                </button>
            </div>
        </div>
    );

    return (
        <HoloErrorBoundary key={key} fallback={errorFallback}>
            <Suspense fallback={<LoadingFallback />}>
                <BioHoloExplorer onBack={goBack} />
            </Suspense>
        </HoloErrorBoundary>
    );
}
