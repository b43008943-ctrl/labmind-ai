/* ═══════════════════════════════════════════════════════════════
   LABMIND AI — Global Error Boundary
   ═══════════════════════════════════════════════════════════════
   Catches ANY unhandled error in the component tree below it.
   Shows a full-screen recovery page styled to match the app's
   dark holographic theme.

   Must be a class component — React limitation for error
   boundary lifecycle methods (componentDidCatch).
   ═══════════════════════════════════════════════════════════════ */

import React from 'react';

export default class GlobalErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('[GlobalErrorBoundary] Unhandled error caught:');
        console.error('Error:', error);
        console.error('Component stack:', errorInfo?.componentStack);
    }

    handleReload = () => {
        window.location.reload();
    };

    handleGoHome = () => {
        window.location.href = '/dashboard';
    };

    render() {
        if (!this.state.hasError) {
            return this.props.children;
        }

        const errorMessage = this.state.error?.message || 'An unexpected error occurred';

        return (
            <div className="min-h-screen bg-[#020617] flex items-center justify-center p-6 relative overflow-hidden">
                {/* Background Effects */}
                <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-red-500/5 rounded-full blur-3xl animate-pulse" />
                    <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-cyan-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
                    <div className="absolute inset-0" style={{
                        backgroundImage: 'linear-gradient(rgba(6,182,212,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(6,182,212,0.03) 1px, transparent 1px)',
                        backgroundSize: '60px 60px'
                    }} />
                </div>

                <div className="relative z-10 max-w-lg w-full">
                    {/* Error Card */}
                    <div className="bg-slate-900/80 backdrop-blur-2xl border border-red-500/20 rounded-3xl p-10 shadow-[0_0_60px_rgba(239,68,68,0.1)] text-center">

                        {/* Animated Error Icon */}
                        <div className="relative mx-auto w-24 h-24 mb-8">
                            <div className="absolute inset-0 bg-red-500/20 rounded-full animate-ping" style={{ animationDuration: '2s' }} />
                            <div className="relative w-24 h-24 bg-red-500/10 border-2 border-red-500/40 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(239,68,68,0.3)]">
                                <svg className="w-12 h-12 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
                                </svg>
                            </div>
                        </div>

                        {/* Error Title */}
                        <h1 className="text-2xl font-bold text-white mb-2 tracking-wide">
                            Something went wrong
                        </h1>
                        <p className="text-lg text-red-300/80 mb-6 font-medium" dir="rtl">
                            حدث خطأ ما
                        </p>

                        {/* Error Detail */}
                        <div className="bg-slate-950/60 border border-white/5 rounded-xl p-4 mb-8">
                            <p className="text-sm text-slate-400 font-mono leading-relaxed break-words">
                                {errorMessage}
                            </p>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex flex-col sm:flex-row gap-3 justify-center">
                            <button
                                onClick={this.handleReload}
                                className="px-6 py-3 bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 rounded-xl font-semibold text-sm tracking-wide hover:bg-cyan-500/30 hover:border-cyan-400/60 hover:shadow-[0_0_20px_rgba(6,182,212,0.3)] transition-all duration-300 cursor-pointer"
                            >
                                ↻ Reload App
                            </button>
                            <button
                                onClick={this.handleGoHome}
                                className="px-6 py-3 bg-slate-700/40 border border-white/10 text-slate-300 rounded-xl font-semibold text-sm tracking-wide hover:bg-slate-700/60 hover:border-white/20 transition-all duration-300 cursor-pointer"
                            >
                                ⌂ Go to Dashboard
                            </button>
                        </div>
                    </div>

                    {/* Footer */}
                    <p className="text-center text-xs text-slate-600 mt-6 font-mono tracking-widest">
                        LABMIND AI — ERROR RECOVERY
                    </p>
                </div>
            </div>
        );
    }
}
