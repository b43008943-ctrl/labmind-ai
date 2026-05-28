/* ═══════════════════════════════════════════════════════════════
   LABMIND AI — Screen Error Boundary
   ═══════════════════════════════════════════════════════════════
   Wraps individual screen routes to isolate errors. If one
   screen crashes, the rest of the app continues working —
   only the broken screen shows an in-place error card.

   Props:
   - screenName (string) — for better error logging
   - children — the screen component to render

   Must be a class component — React limitation.
   ═══════════════════════════════════════════════════════════════ */

import React from 'react';

export default class ScreenErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        const screenName = this.props.screenName || 'Unknown';
        console.error(`[ScreenErrorBoundary] Error in "${screenName}":`);
        console.error('Error:', error);
        console.error('Component stack:', errorInfo?.componentStack);
    }

    handleRetry = () => {
        this.setState({ hasError: false, error: null });
    };

    handleGoBack = () => {
        // Use browser history to go back — works with React Router
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = '/dashboard';
        }
    };

    render() {
        if (!this.state.hasError) {
            return this.props.children;
        }

        const screenName = this.props.screenName || 'Screen';
        const errorMessage = this.state.error?.message || 'An unexpected error occurred';

        return (
            <div className="flex-1 flex items-center justify-center p-6 min-h-[60vh]">
                <div className="max-w-md w-full bg-slate-900/70 backdrop-blur-xl border border-amber-500/20 rounded-2xl p-8 shadow-[0_0_40px_rgba(245,158,11,0.08)]">

                    {/* Warning Icon */}
                    <div className="flex justify-center mb-6">
                        <div className="w-16 h-16 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(245,158,11,0.15)]">
                            <svg className="w-8 h-8 text-amber-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                            </svg>
                        </div>
                    </div>

                    {/* Title */}
                    <h2 className="text-lg font-bold text-white text-center mb-1 tracking-wide">
                        This screen encountered an error
                    </h2>
                    <p className="text-sm text-amber-300/70 text-center mb-5 font-medium" dir="rtl">
                        حدثت مشكلة في هذه الشاشة
                    </p>

                    {/* Screen Name Badge */}
                    <div className="flex justify-center mb-4">
                        <span className="px-3 py-1 bg-slate-800/80 border border-white/5 rounded-lg text-[11px] font-mono text-slate-500 tracking-wider uppercase">
                            {screenName}
                        </span>
                    </div>

                    {/* Error Detail */}
                    <div className="bg-slate-950/50 border border-white/5 rounded-xl p-3 mb-6">
                        <p className="text-xs text-slate-400 font-mono leading-relaxed break-words">
                            {errorMessage}
                        </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 justify-center">
                        <button
                            onClick={this.handleRetry}
                            className="px-5 py-2.5 bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 rounded-xl font-semibold text-xs tracking-wide hover:bg-cyan-500/25 hover:border-cyan-400/50 hover:shadow-[0_0_15px_rgba(6,182,212,0.2)] transition-all duration-300 cursor-pointer"
                        >
                            ↻ Try Again
                        </button>
                        <button
                            onClick={this.handleGoBack}
                            className="px-5 py-2.5 bg-slate-700/30 border border-white/10 text-slate-300 rounded-xl font-semibold text-xs tracking-wide hover:bg-slate-700/50 hover:border-white/15 transition-all duration-300 cursor-pointer"
                        >
                            ← Go Back
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}
