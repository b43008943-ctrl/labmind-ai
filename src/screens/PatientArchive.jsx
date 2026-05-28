import { useState, useEffect, useCallback } from 'react';
import { Search, Filter, Activity, CheckCircle, Clock, FileText, Loader2, AlertTriangle, Plus, X } from 'lucide-react';
import { listPatients, createPatient } from '../services/apiClient';

export default function PatientArchive({ onNavigate }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [patients, setPatients] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showAddForm, setShowAddForm] = useState(false);
    const [newPatient, setNewPatient] = useState({ patient_code: '', full_name: '', gender: '', blood_type: '', notes: '' });
    const [creating, setCreating] = useState(false);

    // Debounced backend search
    const fetchPatients = useCallback(async (query) => {
        setLoading(true);
        setError(null);
        try {
            const data = await listPatients({ search: query || null, limit: 50 });
            setPatients(data);
        } catch (err) {
            setError(err.message || 'Failed to load patients.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchPatients('');
    }, [fetchPatients]);

    // Debounced search — 400ms after typing stops
    useEffect(() => {
        const t = setTimeout(() => fetchPatients(searchQuery), 400);
        return () => clearTimeout(t);
    }, [searchQuery, fetchPatients]);

    const handleCreate = async (e) => {
        e.preventDefault();
        if (!newPatient.patient_code.trim() || !newPatient.full_name.trim()) return;
        setCreating(true);
        try {
            const created = await createPatient({
                patient_code: newPatient.patient_code.trim(),
                full_name: newPatient.full_name.trim(),
                gender: newPatient.gender || undefined,
                blood_type: newPatient.blood_type || undefined,
                notes: newPatient.notes || undefined,
            });
            setPatients(prev => [created, ...prev]);
            setNewPatient({ patient_code: '', full_name: '', gender: '', blood_type: '', notes: '' });
            setShowAddForm(false);
        } catch (err) {
            setError(err.message);
        } finally {
            setCreating(false);
        }
    };

    const formatDate = (iso) => {
        if (!iso) return '—';
        return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    };

    return (
        <div className="fixed inset-0 z-9999 overflow-y-auto flex flex-col justify-start w-full h-dvh font-rajdhani text-white" style={{ animation: 'fadeIn 0.5s ease-out forwards' }}>

            {/* SOLID STICKY HEADER */}
            <div className="sticky top-0 left-0 w-full bg-[#050505]/95 backdrop-blur-xl border-b border-cyan-500/30 px-4 py-5 sm:px-6 flex items-center justify-between z-10000 shrink-0">
                <h2 className="text-xl font-black text-white tracking-widest uppercase">Clinical Archive</h2>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setShowAddForm(v => !v)}
                        className="flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-600/25 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-500/40 transition-all text-xs font-bold tracking-wider uppercase"
                    >
                        <Plus size={14} />{showAddForm ? 'Cancel' : 'Add Patient'}
                    </button>
                    <button onClick={() => onNavigate('dashboard')} className="flex items-center justify-center w-10 h-10 rounded-full bg-slate-800 text-cyan-400 border border-cyan-500/50 hover:bg-slate-700 transition-all cursor-pointer">
                        <X size={22} />
                    </button>
                </div>
            </div>

            {/* SCROLLABLE CONTENT */}
            <div className="w-full max-w-5xl mx-auto p-4 sm:p-6 pb-32">

                {/* Add Patient Form */}
                {showAddForm && (
                    <form onSubmit={handleCreate} className="w-full mb-8 bg-indigo-900/15 backdrop-blur-xl border border-indigo-500/25 rounded-2xl p-4 sm:p-6 shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
                        <h3 className="text-sm font-bold text-indigo-300 tracking-wider uppercase mb-4">Register New Patient</h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <input value={newPatient.patient_code} onChange={e => setNewPatient(p => ({ ...p, patient_code: e.target.value }))} placeholder="Patient Code *" required className="bg-black/40 border border-white/10 rounded-xl py-3 px-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all font-sans" />
                            <input value={newPatient.full_name} onChange={e => setNewPatient(p => ({ ...p, full_name: e.target.value }))} placeholder="Full Name *" required className="bg-black/40 border border-white/10 rounded-xl py-3 px-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all font-sans" />
                            <select value={newPatient.gender} onChange={e => setNewPatient(p => ({ ...p, gender: e.target.value }))} className="bg-black/40 border border-white/10 rounded-xl py-3 px-4 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all font-sans appearance-none cursor-pointer">
                                <option value="">Gender (optional)</option>
                                <option value="male">Male</option>
                                <option value="female">Female</option>
                                <option value="other">Other</option>
                            </select>
                            <input value={newPatient.blood_type} onChange={e => setNewPatient(p => ({ ...p, blood_type: e.target.value }))} placeholder="Blood Type (optional)" className="bg-black/40 border border-white/10 rounded-xl py-3 px-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all font-sans" />
                        </div>
                        <textarea value={newPatient.notes} onChange={e => setNewPatient(p => ({ ...p, notes: e.target.value }))} placeholder="Notes (optional)" rows={2} className="w-full mt-3 bg-black/40 border border-white/10 rounded-xl py-3 px-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all font-sans resize-none" />
                        <div className="flex justify-end mt-4">
                            <button type="submit" disabled={creating} className="px-6 py-2.5 rounded-full bg-indigo-600/30 text-indigo-200 border border-indigo-500/40 hover:bg-indigo-500/50 transition-all text-xs font-bold tracking-wider uppercase disabled:opacity-50">
                                {creating ? 'Creating...' : 'Create Patient'}
                            </button>
                        </div>
                    </form>
                )}

                {/* Search Section */}
                <div className="flex flex-col md:flex-row gap-3 md:gap-4 w-full mb-8 bg-white/3 backdrop-blur-xl border border-white/10 rounded-2xl p-4 sm:p-6 justify-between items-center shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
                    <div className="relative w-full">
                        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-500" size={18} />
                        <input
                            type="text"
                            placeholder="Search Patient Code or Name..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-black/40 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-sans"
                        />
                    </div>
                </div>

                {/* Loading / Error */}
                {loading && (
                    <div className="w-full py-16 flex flex-col items-center justify-center text-slate-400">
                        <Loader2 size={36} className="animate-spin mb-4 text-indigo-400" />
                        <p className="text-sm">Loading patients...</p>
                    </div>
                )}
                {error && !loading && (
                    <div className="w-full py-6 flex items-center gap-3 justify-center text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl mb-6">
                        <AlertTriangle size={18} />
                        <p className="text-sm">{error}</p>
                    </div>
                )}

                {/* Records List */}
                {!loading && (
                    <div className="w-full flex flex-col gap-4">
                        {patients.length > 0 ? (
                            patients.map((patient) => (
                                <div key={patient.id} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4 md:p-6 rounded-xl border border-indigo-500/20 bg-slate-900/40 backdrop-blur-md hover:bg-indigo-900/30 transition-all group overflow-hidden relative">

                                    {/* Accent Glow Line */}
                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-linear-to-b from-transparent via-indigo-500 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>

                                    {/* Patient Info */}
                                    <div className="flex flex-col mb-4 sm:mb-0">
                                        <div className="flex items-center gap-3 mb-1">
                                            <div className="w-8 h-8 rounded-lg bg-indigo-500/15 border border-indigo-500/25 flex items-center justify-center shrink-0">
                                                <FileText size={16} className="text-indigo-400" />
                                            </div>
                                            <h3 className="text-lg font-bold text-white tracking-wide">{patient.full_name}</h3>
                                            <span className="text-xs font-mono text-slate-400 bg-white/5 px-2 py-0.5 rounded border border-white/10">ID: {patient.patient_code}</span>
                                        </div>
                                        <p className="text-sm text-slate-400 font-sans pl-11">
                                            {patient.gender && <span className="capitalize">{patient.gender}</span>}
                                            {patient.blood_type && <> &bull; <span className="text-slate-300">{patient.blood_type}</span></>}
                                            {patient.notes && <> &bull; <span className="text-slate-500 italic">{patient.notes}</span></>}
                                        </p>
                                    </div>

                                    {/* Date & Actions */}
                                    <div className="flex flex-col sm:flex-row items-end sm:items-center gap-4 sm:gap-6 w-full sm:w-auto">
                                        <div className="flex flex-col items-end sm:items-start text-right sm:text-left">
                                            <div className="text-[10px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-full border text-emerald-400 bg-emerald-400/10 border-emerald-400/20 flex items-center gap-1.5 mb-1">
                                                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)] inline-block"></span>
                                                <CheckCircle size={10} />
                                                Registered
                                            </div>
                                            <span className="text-xs text-slate-500">{formatDate(patient.created_at)}</span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="w-full py-16 flex flex-col items-center justify-center text-slate-500 border border-dashed border-white/10 rounded-2xl bg-white/2">
                                <Search size={48} className="mb-4 opacity-50" />
                                <p className="text-lg">No patients found.</p>
                                <p className="text-sm opacity-70">Try adjusting your search or register a new patient.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
