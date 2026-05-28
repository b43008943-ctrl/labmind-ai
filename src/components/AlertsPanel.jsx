import { useState, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Bell, X, Loader2, AlertTriangle, Check, Trash2 } from 'lucide-react';
import { listAlerts, getUnreadAlertCount, markAlertRead, dismissAlert, getToken } from '../services/apiClient';

/* ═══════════════════════════════════════════════════════════════
   ALERTS PANEL — Slide-down holographic alerts overlay
   Usage: <AlertsPanel isOpen={bool} onClose={fn} />
   ═══════════════════════════════════════════════════════════════ */

const PRIORITY_COLORS = {
    critical: { text: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', dot: 'bg-red-400' },
    high: { text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', dot: 'bg-amber-400' },
    medium: { text: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20', dot: 'bg-cyan-400' },
    low: { text: 'text-slate-400', bg: 'bg-slate-500/10', border: 'border-slate-500/20', dot: 'bg-slate-400' },
};

export default function AlertsPanel({ isOpen, onClose }) {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const loadAlerts = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await listAlerts(false);
            setAlerts(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (isOpen) loadAlerts();
    }, [isOpen, loadAlerts]);

    const handleMarkRead = async (alertId) => {
        try {
            await markAlertRead(alertId);
            setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, is_read: true } : a));
        } catch { /* silent */ }
    };

    const handleDismiss = async (alertId) => {
        try {
            await dismissAlert(alertId);
            setAlerts(prev => prev.filter(a => a.id !== alertId));
        } catch { /* silent */ }
    };

    const formatTime = (iso) => {
        if (!iso) return '';
        const d = new Date(iso);
        const now = new Date();
        const diffMs = now - d;
        const diffMin = Math.floor(diffMs / 60000);
        if (diffMin < 1) return 'just now';
        if (diffMin < 60) return `${diffMin}m ago`;
        const diffH = Math.floor(diffMin / 60);
        if (diffH < 24) return `${diffH}h ago`;
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[9998] bg-black/40 backdrop-blur-sm"
                        onClick={onClose}
                    />
                    {/* Panel */}
                    <motion.div
                        initial={{ opacity: 0, y: -30, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -20, scale: 0.97 }}
                        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                        className="fixed top-16 right-4 left-4 sm:left-auto sm:w-[420px] z-[9999] max-h-[70vh] overflow-y-auto rounded-2xl"
                        style={{
                            background: 'rgba(6,10,20,0.92)',
                            border: '1px solid rgba(34,211,238,0.2)',
                            backdropFilter: 'blur(30px)',
                            boxShadow: '0 20px 60px rgba(0,0,0,0.6), 0 0 40px rgba(34,211,238,0.08)',
                        }}
                    >
                        {/* Header */}
                        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
                            <div className="flex items-center gap-2.5">
                                <Bell size={16} className="text-cyan-400" />
                                <span className="text-sm font-bold text-white tracking-wider uppercase">Alerts</span>
                                {alerts.filter(a => !a.is_read).length > 0 && (
                                    <span className="ml-1 px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 text-[10px] font-bold">
                                        {alerts.filter(a => !a.is_read).length}
                                    </span>
                                )}
                            </div>
                            <button onClick={onClose} className="w-7 h-7 flex items-center justify-center rounded-lg border border-white/10 text-slate-400 hover:text-white hover:border-cyan-400/40 transition-all">
                                <X size={14} />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="px-4 py-3">
                            {loading && (
                                <div className="py-10 flex flex-col items-center text-slate-400">
                                    <Loader2 size={24} className="animate-spin mb-2 text-cyan-400" />
                                    <span className="text-xs">Loading alerts...</span>
                                </div>
                            )}
                            {error && (
                                <div className="py-4 flex items-center gap-2 text-red-400 text-xs">
                                    <AlertTriangle size={14} />{error}
                                </div>
                            )}
                            {!loading && !error && alerts.length === 0 && (
                                <div className="py-10 flex flex-col items-center text-slate-500">
                                    <Bell size={32} className="mb-3 opacity-30" />
                                    <p className="text-xs font-medium">No alerts</p>
                                </div>
                            )}
                            {!loading && alerts.map(alert => {
                                const colors = PRIORITY_COLORS[alert.priority] || PRIORITY_COLORS.medium;
                                return (
                                    <div key={alert.id} className={`relative flex items-start gap-3 p-3 mb-2 rounded-xl border ${colors.border} ${colors.bg} transition-all ${!alert.is_read ? 'ring-1 ring-cyan-400/20' : 'opacity-70'}`}>
                                        <div className={`mt-1 w-2 h-2 rounded-full ${colors.dot} shrink-0 ${!alert.is_read ? 'shadow-[0_0_6px_currentColor]' : ''}`} />
                                        <div className="flex-1 min-w-0">
                                            <p className={`text-xs font-bold ${colors.text} mb-0.5`}>{alert.title}</p>
                                            {alert.message && <p className="text-[11px] text-slate-400 leading-relaxed">{alert.message}</p>}
                                            <span className="text-[10px] text-slate-500 mt-1 block">{formatTime(alert.created_at)}</span>
                                        </div>
                                        <div className="flex gap-1 shrink-0">
                                            {!alert.is_read && (
                                                <button onClick={() => handleMarkRead(alert.id)} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-emerald-400 transition-colors" title="Mark read">
                                                    <Check size={12} />
                                                </button>
                                            )}
                                            <button onClick={() => handleDismiss(alert.id)} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-red-400 transition-colors" title="Dismiss">
                                                <Trash2 size={12} />
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}

/* ─── Bell Badge — Use anywhere for unread count ─── */
export function AlertBellBadge({ onClick }) {
    const [count, setCount] = useState(0);

    useEffect(() => {
        const load = async () => {
            if (!getToken()) return;          // ← auth guard
            try {
                const data = await getUnreadAlertCount();
                setCount(data?.count || 0);
            } catch { /* silent */ }
        };
        load();
        const interval = setInterval(load, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <button onClick={onClick} className="relative p-2 rounded-full hover:bg-white/5 transition-colors group">
            <Bell size={18} className="text-slate-400 group-hover:text-cyan-400 transition-colors" />
            {count > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 px-1 rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center shadow-[0_0_8px_rgba(239,68,68,0.6)] animate-pulse">
                    {count > 9 ? '9+' : count}
                </span>
            )}
        </button>
    );
}
