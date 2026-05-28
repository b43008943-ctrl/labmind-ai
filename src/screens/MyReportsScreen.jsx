import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { ChevronLeft, FileText, Archive, Clock, CheckCircle, XCircle, Send, Search, Loader2, AlertTriangle, ChevronRight } from 'lucide-react';
import { listMyReports, listMyArchive, submitForReview, archiveReport, getReport } from '../services/apiClient';

/* ═══════════════════════════════════════════════════════════════
   MY REPORTS SCREEN — Personal Reports & Archive
   Shows user's own reports with status badges and actions
   ═══════════════════════════════════════════════════════════════ */

const STATUS_STYLES = {
    draft: { color: 'text-slate-400', bg: 'bg-slate-500/10', border: 'border-slate-500/20', label: 'Draft', Icon: Clock },
    preliminary: { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/25', label: 'Preliminary', Icon: Clock },
    pending_review: { color: 'text-indigo-400', bg: 'bg-indigo-500/10', border: 'border-indigo-500/25', label: 'Pending Review', Icon: Send },
    approved: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/25', label: 'Approved', Icon: CheckCircle },
    rejected: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/25', label: 'Rejected', Icon: XCircle },
    archived: { color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/25', label: 'Archived', Icon: Archive },
};

export default function MyReportsScreen({ onNavigate }) {
    const [tab, setTab] = useState('reports'); // 'reports' | 'archive'
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [actionLoading, setActionLoading] = useState(null);
    const [selectedReport, setSelectedReport] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = tab === 'archive' ? await listMyArchive() : await listMyReports();
            setReports(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [tab]);

    useEffect(() => { fetchData(); }, [fetchData]);

    const handleSubmit = async (reportId) => {
        setActionLoading(reportId);
        try {
            const updated = await submitForReview(reportId);
            setReports(prev => prev.map(r => r.id === reportId ? { ...r, status: updated.status } : r));
        } catch (err) {
            setError(err.message);
        } finally {
            setActionLoading(null);
        }
    };

    const handleArchive = async (reportId) => {
        setActionLoading(reportId);
        try {
            await archiveReport(reportId);
            setReports(prev => prev.filter(r => r.id !== reportId));
        } catch (err) {
            setError(err.message);
        } finally {
            setActionLoading(null);
        }
    };

    const handleViewDetail = async (reportId) => {
        setDetailLoading(true);
        try {
            const detail = await getReport(reportId);
            setSelectedReport(detail);
        } catch (err) {
            setError(err.message);
        } finally {
            setDetailLoading(false);
        }
    };

    const formatDate = (iso) => {
        if (!iso) return '—';
        return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    };

    const filtered = reports.filter(r => r.title?.toLowerCase().includes(searchQuery.toLowerCase()));

    return (
        <motion.div
            initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="fixed inset-0 z-50 overflow-y-auto overflow-x-hidden w-full h-dvh text-white"
            style={{ fontFamily: "'Inter', sans-serif" }}
        >
            {/* Ambient background */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-20%] left-[-10%] w-[45%] h-[45%] rounded-full" style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)', filter: 'blur(120px)' }} />
                <div className="absolute bottom-[-15%] right-[-10%] w-[40%] h-[40%] rounded-full" style={{ background: 'radial-gradient(circle, rgba(34,211,238,0.06) 0%, transparent 70%)', filter: 'blur(100px)' }} />
            </div>

            {/* Header */}
            <div className="sticky top-0 w-full px-4 md:px-8 py-4 flex items-center justify-between z-40 border-b border-white/5"
                style={{ background: 'rgba(5,5,16,0.6)', backdropFilter: 'blur(30px)' }}>
                <div className="flex items-center gap-3">
                    <button onClick={() => onNavigate('dashboard')} className="flex items-center gap-2 px-3 py-2 rounded-full border border-white/10 text-white/70 hover:text-white hover:bg-white/5 transition-all cursor-pointer">
                        <ChevronLeft size={16} />
                        <span className="text-[10px] font-bold tracking-wider uppercase">Back</span>
                    </button>
                    <div className="ml-2">
                        <h2 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                            <FileText size={18} className="text-indigo-400" />My Reports
                        </h2>
                    </div>
                </div>
            </div>

            <div className="relative z-10 w-full max-w-5xl mx-auto p-4 md:p-8">

                {/* Tab Switcher */}
                <div className="flex gap-2 mb-6">
                    {[{ key: 'reports', label: 'My Reports', icon: FileText }, { key: 'archive', label: 'My Archive', icon: Archive }].map(t => (
                        <button key={t.key} onClick={() => { setTab(t.key); setSelectedReport(null); }}
                            className={`flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-bold tracking-wider uppercase transition-all border ${tab === t.key
                                ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40 shadow-[0_0_15px_rgba(99,102,241,0.15)]'
                                : 'bg-white/3 text-slate-400 border-white/10 hover:bg-white/5 hover:text-white'
                            }`}>
                            <t.icon size={14} />{t.label}
                        </button>
                    ))}
                </div>

                {/* Search */}
                <div className="relative w-full max-w-md mb-6">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                    <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search reports..."
                        className="w-full bg-black/30 border border-white/10 rounded-xl py-2.5 pl-11 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all" />
                </div>

                {/* Detail View */}
                {selectedReport && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                        className="mb-8 p-6 rounded-2xl border border-indigo-500/20 bg-slate-900/50 backdrop-blur-xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-base font-bold text-white">{selectedReport.report?.title}</h3>
                            <button onClick={() => setSelectedReport(null)} className="text-slate-400 hover:text-white text-xs font-bold">Close</button>
                        </div>
                        {selectedReport.report?.summary && (
                            <div className="mb-3"><span className="text-[10px] text-slate-500 uppercase tracking-wider">Summary</span><p className="text-sm text-slate-300 mt-1">{selectedReport.report.summary}</p></div>
                        )}
                        {selectedReport.report?.findings && (
                            <div className="mb-3"><span className="text-[10px] text-slate-500 uppercase tracking-wider">Findings</span><p className="text-sm text-slate-300 mt-1">{selectedReport.report.findings}</p></div>
                        )}
                        {selectedReport.report?.recommendations && (
                            <div className="mb-3"><span className="text-[10px] text-slate-500 uppercase tracking-wider">Recommendations</span><p className="text-sm text-slate-300 mt-1">{selectedReport.report.recommendations}</p></div>
                        )}
                        {selectedReport.reviews?.length > 0 && (
                            <div className="mt-4 border-t border-white/10 pt-4">
                                <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-2">Reviews</span>
                                {selectedReport.reviews.map(r => (
                                    <div key={r.id} className="mb-2 p-3 rounded-lg bg-white/3 border border-white/5 text-xs">
                                        <span className={`font-bold ${r.decision === 'approved' ? 'text-emerald-400' : r.decision === 'rejected' ? 'text-red-400' : 'text-amber-400'}`}>{r.decision?.toUpperCase()}</span>
                                        {r.comments && <p className="text-slate-400 mt-1">{r.comments}</p>}
                                        <span className="text-slate-500 text-[10px]">{formatDate(r.reviewed_at)}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </motion.div>
                )}

                {/* Loading / Error */}
                {loading && (
                    <div className="py-16 flex flex-col items-center text-slate-400">
                        <Loader2 size={32} className="animate-spin mb-3 text-indigo-400" /><span className="text-sm">Loading reports...</span>
                    </div>
                )}
                {error && !loading && (
                    <div className="py-4 flex items-center gap-2 text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 mb-4">
                        <AlertTriangle size={16} /><span className="text-sm">{error}</span>
                    </div>
                )}

                {/* Reports List */}
                {!loading && (
                    <div className="flex flex-col gap-3">
                        {filtered.length > 0 ? filtered.map(report => {
                            const s = STATUS_STYLES[report.status] || STATUS_STYLES.draft;
                            return (
                                <div key={report.id} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 p-4 rounded-xl border border-white/8 bg-slate-900/40 backdrop-blur-md hover:bg-indigo-900/15 transition-all group">
                                    <div className="flex-1 min-w-0">
                                        <h4 className="text-sm font-bold text-white mb-1 truncate">{report.title}</h4>
                                        <div className="flex items-center gap-3">
                                            <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${s.color} ${s.bg} ${s.border} flex items-center gap-1`}>
                                                <s.Icon size={10} />{s.label}
                                            </span>
                                            <span className="text-[10px] text-slate-500">{formatDate(report.updated_at)}</span>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2 w-full sm:w-auto">
                                        <button onClick={() => handleViewDetail(report.id)} disabled={detailLoading}
                                            className="flex-1 sm:flex-initial flex items-center justify-center gap-1 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-slate-300 hover:text-white hover:bg-white/10 transition-all text-[10px] font-bold tracking-wider uppercase">
                                            View <ChevronRight size={12} />
                                        </button>
                                        {(report.status === 'draft' || report.status === 'preliminary') && (
                                            <button onClick={() => handleSubmit(report.id)} disabled={actionLoading === report.id}
                                                className="flex-1 sm:flex-initial flex items-center justify-center gap-1 px-4 py-2 rounded-full bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/30 transition-all text-[10px] font-bold tracking-wider uppercase disabled:opacity-50">
                                                <Send size={10} />{actionLoading === report.id ? '...' : 'Submit'}
                                            </button>
                                        )}
                                        {report.status !== 'archived' && tab !== 'archive' && (
                                            <button onClick={() => handleArchive(report.id)} disabled={actionLoading === report.id}
                                                className="flex items-center justify-center p-2 rounded-lg border border-white/10 text-slate-400 hover:text-purple-400 hover:border-purple-500/30 transition-all" title="Archive">
                                                <Archive size={14} />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            );
                        }) : (
                            <div className="py-16 flex flex-col items-center text-slate-500 border border-dashed border-white/10 rounded-2xl">
                                <FileText size={40} className="mb-3 opacity-30" />
                                <p className="text-sm font-medium">{tab === 'archive' ? 'Your archive is empty.' : 'No reports yet.'}</p>
                                <p className="text-xs opacity-60 mt-1">Reports created from analysis results will appear here.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </motion.div>
    );
}
