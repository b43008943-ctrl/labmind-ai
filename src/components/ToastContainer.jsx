import { CheckCircle2 } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function ToastContainer({ toastEvent }) {
    const [toasts, setToasts] = useState([]);

    useEffect(() => {
        if (toastEvent) {
            const id = Date.now();
            setToasts(prev => [...prev, { id, message: toastEvent.message }]);
            setTimeout(() => {
                setToasts(prev => prev.filter(t => t.id !== id));
            }, 3000);
        }
    }, [toastEvent]);

    return (
        <div id="toast-container" className="fixed top-6 left-1/2 transform -translate-x-1/2 z-200 flex flex-col gap-2 pointer-events-none">
            {toasts.map(t => (
                <div key={t.id} className="bg-slate-800/90 backdrop-blur-md border border-cyan-500/30 text-white px-4 py-3 rounded-lg shadow-[0_5px_15px_rgba(0,0,0,0.5)] text-sm font-medium flex items-center gap-2 animate-in slide-in-from-top-4 fade-in duration-300">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                    {t.message}
                </div>
            ))}
        </div>
    );
}
