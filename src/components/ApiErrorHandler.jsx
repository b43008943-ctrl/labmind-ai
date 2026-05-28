/* ═══════════════════════════════════════════════════════════════
   LABMIND AI — API Error Handler
   ═══════════════════════════════════════════════════════════════
   Functional component that:
   1. Listens for unhandled promise rejections
   2. Monitors backend connectivity
   3. Shows a non-intrusive banner when backend is unreachable
   4. Auto-retries every 30s and hides when connection restores

   This does NOT crash the app — it just notifies the user.
   ═══════════════════════════════════════════════════════════════ */

import { useState, useEffect, useCallback, useRef } from 'react';

import { API_BASE_URL as API_BASE } from '../services/apiClient';
const HEALTH_ENDPOINT = `${API_BASE}/docs`;
const RETRY_INTERVAL = 30000; // 30 seconds

export default function ApiErrorHandler({ children }) {
    const [isOffline, setIsOffline] = useState(false);
    const [lastError, setLastError] = useState('');
    const [isRetrying, setIsRetrying] = useState(false);
    const retryTimerRef = useRef(null);
    const isOfflineRef = useRef(false);

    // ─── Health check — try to reach the backend ───
    const checkHealth = useCallback(async () => {
        try {
            setIsRetrying(true);
            const res = await fetch(HEALTH_ENDPOINT, {
                method: 'HEAD',
                mode: 'no-cors',
                cache: 'no-store',
                signal: AbortSignal.timeout(8000),
            });
            // no-cors won't give us status, but if fetch resolves the server is reachable
            setIsOffline(false);
            isOfflineRef.current = false;
            setLastError('');
        } catch {
            // Server still unreachable
            setIsOffline(true);
            isOfflineRef.current = true;
        } finally {
            setIsRetrying(false);
        }
    }, []);

    // ─── Start/stop auto-retry loop ───
    useEffect(() => {
        if (isOffline) {
            retryTimerRef.current = setInterval(checkHealth, RETRY_INTERVAL);
        } else {
            if (retryTimerRef.current) {
                clearInterval(retryTimerRef.current);
                retryTimerRef.current = null;
            }
        }
        return () => {
            if (retryTimerRef.current) clearInterval(retryTimerRef.current);
        };
    }, [isOffline, checkHealth]);

    // ─── Listen for unhandled promise rejections ───
    useEffect(() => {
        const handleRejection = (event) => {
            const error = event.reason;

            // Detect network/server errors
            const isNetworkError =
                error instanceof TypeError && error.message?.includes('fetch') ||
                error?.message?.includes('NetworkError') ||
                error?.message?.includes('Failed to fetch') ||
                error?.status === 500 ||
                error?.status === 502 ||
                error?.status === 503;

            if (isNetworkError) {
                console.warn('[ApiErrorHandler] Network/server error detected:', error?.message || error);
                setIsOffline(true);
                isOfflineRef.current = true;
                setLastError(error?.message || 'Server connection lost');
                // Prevent the default browser error handling
                event.preventDefault();
            }
            // Non-network errors: log but don't show banner
            // (they'll be caught by React error boundaries if they're render errors)
        };

        window.addEventListener('unhandledrejection', handleRejection);
        return () => window.removeEventListener('unhandledrejection', handleRejection);
    }, []);

    // ─── Listen for browser online/offline events ───
    useEffect(() => {
        const handleOffline = () => {
            setIsOffline(true);
            isOfflineRef.current = true;
            setLastError('No internet connection');
        };
        const handleOnline = () => {
            // Browser says we're online — verify by pinging backend
            checkHealth();
        };

        window.addEventListener('offline', handleOffline);
        window.addEventListener('online', handleOnline);
        return () => {
            window.removeEventListener('offline', handleOffline);
            window.removeEventListener('online', handleOnline);
        };
    }, [checkHealth]);

    return (
        <>
            {children}

            {/* ─── Connection Lost Banner ─── */}
            {isOffline && (
                <div
                    className="fixed top-0 left-0 right-0 z-[9999] flex items-center justify-center transition-all duration-500"
                    style={{ animation: 'slideDownBanner 0.4s ease-out' }}
                >
                    <div className="mx-4 mt-3 max-w-2xl w-full bg-amber-950/90 backdrop-blur-xl border border-amber-500/30 rounded-2xl px-5 py-3 shadow-[0_8px_40px_rgba(245,158,11,0.15)] flex items-center gap-4">
                        {/* Pulsing Indicator */}
                        <div className="relative shrink-0">
                            <div className="w-3 h-3 bg-amber-500 rounded-full animate-pulse" />
                            <div className="absolute inset-0 w-3 h-3 bg-amber-500/50 rounded-full animate-ping" />
                        </div>

                        {/* Message */}
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-amber-200 tracking-wide">
                                Server connection lost
                            </p>
                            <p className="text-xs text-amber-300/60 mt-0.5 truncate">
                                {lastError || 'Some features may not work'} • {isRetrying ? 'Retrying...' : 'Auto-retry in 30s'}
                            </p>
                        </div>

                        {/* Manual Retry Button */}
                        <button
                            onClick={checkHealth}
                            disabled={isRetrying}
                            className="shrink-0 px-3 py-1.5 bg-amber-500/15 border border-amber-500/25 text-amber-300 rounded-lg text-xs font-semibold hover:bg-amber-500/25 transition-all disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
                        >
                            {isRetrying ? '...' : 'Retry'}
                        </button>

                        {/* Dismiss */}
                        <button
                            onClick={() => { setIsOffline(false); isOfflineRef.current = false; }}
                            className="shrink-0 text-amber-400/50 hover:text-amber-300 transition-colors cursor-pointer"
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>
            )}

            {/* Banner animation keyframe */}
            {isOffline && (
                <style>{`
                    @keyframes slideDownBanner {
                        from { transform: translateY(-100%); opacity: 0; }
                        to { transform: translateY(0); opacity: 1; }
                    }
                `}</style>
            )}
        </>
    );
}
