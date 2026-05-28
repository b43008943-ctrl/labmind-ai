/* ═══════════════════════════════════════════════════════════════
   LABMIND AI — App State Context
   ═══════════════════════════════════════════════════════════════
   Holds non-navigation application state that was previously
   lifted in App.jsx. Moving this to context decouples it from
   the view-rendering logic, which is a prerequisite for the
   React Router migration.

   State moved here:
   - user (display profile data)
   - analystName
   - alerts (lab department alert badges)
   - pastRecords (analysis history)
   - nymphState (AI assistant animation state)
   - readingContext (for FloatingAIAssistant)
   - toast events
   - modal state
   ═══════════════════════════════════════════════════════════════ */

import { createContext, useContext, useState, useCallback, useMemo, useEffect } from 'react';
import { useNavigation } from './NavigationContext';

const AppStateContext = createContext(null);

const DEFAULT_USER = {
    name: 'DR. COMMANDER ALPHA',
    level: 42,
    avatar: 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=256&h=256&q=80',
    rank: 'Verified Specialist',
    email: 'alpha.cmd@neural-link.gov',
    xp: '84,300',
    ip: '192.168.x.x (Secure)',
    password: '********',
    push: 'Active',
    sound: 'Enabled',
    lang: 'EN-US',
    time: 'GMT+3'
};

const DEFAULT_PAST_RECORDS = [
    { id: 'rec-1', type: 'urine', sampleId: 'sample-b', label: 'Urinalysis - Sample B', date: '2026-02-23 14:32', status: 'Critical', statusColor: 'text-red-400', glowColor: 'shadow-[0_0_12px_rgba(248,113,113,0.7)]', iconColor: 'text-amber-400', iconBg: 'bg-amber-500/20' },
    { id: 'rec-2', type: 'blood', sampleId: null, label: 'Hematology - Sample A', date: '2026-02-23 11:05', status: 'Normal', statusColor: 'text-cyan-400', glowColor: 'shadow-[0_0_12px_rgba(34,211,238,0.6)]', iconColor: 'text-red-400', iconBg: 'bg-red-500/20' },
    { id: 'rec-3', type: 'urine', sampleId: 'sample-a', label: 'Urinalysis - Sample A', date: '2026-02-22 16:48', status: 'Optimal', statusColor: 'text-cyan-400', glowColor: 'shadow-[0_0_12px_rgba(34,211,238,0.6)]', iconColor: 'text-amber-400', iconBg: 'bg-amber-500/20' },
];

const CATEGORIES = [
    { id: 'hematology', name: 'Hematology Lab' },
    { id: 'urinalysis', name: 'Urinalysis Lab' },
    { id: 'microbiology', name: 'Microbiology Lab' },
    { id: 'clinical', name: 'Clinical Biochemistry' },
    { id: 'parasitology', name: 'Parasitology Lab' },
    { id: 'bloodbank', name: 'Blood Bank & Serology' }
];

export function AppStateProvider({ children }) {
    // ─── User display state ───
    const [user, setUser] = useState(DEFAULT_USER);
    const [analystName, setAnalystName] = useState('');

    // ─── Lab alerts ───
    const [alerts, setAlerts] = useState({
        hematology: false,
        urinalysis: false,
        microbiology: false,
        clinical: false,
        parasitology: false,
        bloodbank: false
    });

    // ─── Past records ───
    const [pastRecords, setPastRecords] = useState(DEFAULT_PAST_RECORDS);

    // ─── AI Assistant state ───
    const [nymphState, setNymphState] = useState('welcome');

    // ─── Reading context (for FloatingAIAssistant) ───
    const [readingContext, setReadingContext] = useState(null);

    // ─── Modal & Toast ───
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [toastEvent, setToastEvent] = useState(null);

    // ─── Derived from NavigationContext ───
    const { currentView } = useNavigation();

    // ─── Nymph state sync (mirrors old App.jsx useEffect) ───
    useEffect(() => {
        if (currentView === 'splash' || currentView === 'login') return;

        if (currentView === 'dashboard') {
            setNymphState(prev => prev === 'welcome' ? 'welcome' : 'idle');
        } else if (['archive', 'academic-hub', 'ailab', 'ai-archive', 'ai-testing-center'].includes(currentView)) {
            setNymphState('talking');
        } else if (['hematology-lab', 'urinalysis', 'parasitology-lab', 'clinical', 'microbiology-lab', 'bloodbank-lab'].includes(currentView)) {
            setNymphState('analyzing');
        } else {
            setNymphState('idle');
        }
    }, [currentView]);

    // ─── Actions ───
    const handleAddRecord = useCallback((record) => {
        setPastRecords(prev => [record, ...prev]);
    }, []);

    const handleImportData = useCallback(() => {
        const randomCategory = CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)];
        setAlerts(prev => ({ ...prev, [randomCategory.id]: true }));
        setToastEvent({ message: `Sample identified. Routed to ${randomCategory.name}`, time: Date.now() });
    }, []);

    const clearAlert = useCallback((id) => {
        setAlerts(prev => ({ ...prev, [id]: false }));
    }, []);

    // ─── XP & Level system ───
    const [xp, setXp] = useState(() => 
      parseInt(localStorage.getItem('labmind_xp') || '4250')
    )
    const level = 1 + Math.floor(xp / 1000)

    const addXp = (amount) => {
      setXp(prev => {
        const newXp = prev + amount
        localStorage.setItem('labmind_xp', String(newXp))
        return newXp
      })
    }

    // Owned items
    const [ownedItems, setOwnedItems] = useState(() => {
      try {
        return JSON.parse(localStorage.getItem('labmind_owned_items') || '[]')
      } catch { return [] }
    })

    // Equipped items
    const [equipped, setEquipped] = useState(() => {
      try {
        return JSON.parse(localStorage.getItem('labmind_equipped') || '{}')
      } catch { return {} }
    })

    const equipItem = (item) => {
      setEquipped(prev => {
        const next = { ...prev, [item.category]: item.id }
        localStorage.setItem('labmind_equipped', JSON.stringify(next))
        return next
      })
    }

    const buyItem = (item, cost) => {
      setXp(prev => {
        const newXp = prev - cost
        localStorage.setItem('labmind_xp', String(newXp))
        return newXp
      })
      setOwnedItems(prev => {
        const next = [...prev, item.id]
        localStorage.setItem('labmind_owned_items', JSON.stringify(next))
        return next
      })
    }

    const value = useMemo(() => ({
        // User
        user,
        setUser,
        analystName,
        setAnalystName,
        // Alerts
        alerts,
        setAlerts,
        clearAlert,
        // Records
        pastRecords,
        handleAddRecord,
        // AI Assistant
        nymphState,
        setNymphState,
        // Reading
        readingContext,
        setReadingContext,
        // Modal & Toast
        isModalOpen,
        setIsModalOpen,
        toastEvent,
        setToastEvent,
        // Import action
        handleImportData,
        // XP & Gamification
        xp,
        level,
        addXp,
        ownedItems,
        equipped,
        equipItem,
        buyItem,
    }), [
        user, analystName, alerts, pastRecords, nymphState,
        readingContext, isModalOpen, toastEvent,
        clearAlert, handleAddRecord, handleImportData,
        xp, level, ownedItems, equipped,
    ]);

    return (
        <AppStateContext.Provider value={value}>
            {children}
        </AppStateContext.Provider>
    );
}

export function useAppState() {
    const ctx = useContext(AppStateContext);
    if (!ctx) throw new Error('useAppState must be used within an AppStateProvider');
    return ctx;
}
