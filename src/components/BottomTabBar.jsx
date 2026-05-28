import { Home, Bot, Users, User, Settings } from 'lucide-react';
import { useNavigation } from '../context/NavigationContext';

export default function BottomTabBar() {
    const { currentView, navigate } = useNavigation();

    const tabs = [
        { id: 'dashboard', label: 'Home', icon: Home, color: 'text-cyan-400', shadow: 'drop-shadow-[0_0_8px_rgba(34,211,238,0.8)]' },
        { id: 'ai-assistant', label: 'Rasha AI', icon: Bot, color: 'text-purple-400', shadow: 'drop-shadow-[0_0_8px_rgba(168,85,247,0.8)]' },
        { id: 'community', label: 'Community', icon: Users, color: 'text-blue-400', shadow: 'drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]' },
        { id: 'profile', label: 'Profile', icon: User, color: 'text-green-400', shadow: 'drop-shadow-[0_0_8px_rgba(34,197,94,0.8)]' },
        { id: 'settings', label: 'Settings', icon: Settings, color: 'text-slate-300', shadow: 'drop-shadow-[0_0_8px_rgba(203,213,225,0.8)]' },
    ];

    return (
        <div className="fixed bottom-0 left-0 right-0 z-50 flex justify-center pb-4 px-4 pointer-events-none">
            <nav className="flex items-center justify-between w-full max-w-md h-16 px-2 bg-[#0A0E17]/80 backdrop-blur-xl border border-white/10 shadow-[0_-10px_40px_rgba(0,0,0,0.5)] rounded-2xl pointer-events-auto">
                {tabs.map((tab) => {
                    const isActive = currentView === tab.id;
                    const Icon = tab.icon;

                    return (
                        <button
                            key={tab.id}
                            onClick={() => navigate(tab.id)}
                            className={`flex flex-col items-center justify-center w-16 h-full transition-all duration-300 outline-none ${isActive ? 'translate-y-[-4px]' : 'hover:bg-white/5 rounded-xl'}`}
                        >
                            <div className={`flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-300 ${isActive ? `bg-white/5 border border-white/10 shadow-[0_0_15px_rgba(255,255,255,0.05)]` : ''}`}>
                                <Icon 
                                    className={`w-5 h-5 transition-colors duration-300 ${isActive ? `${tab.color} ${tab.shadow}` : 'text-gray-500'}`} 
                                    strokeWidth={isActive ? 2.5 : 2} 
                                />
                            </div>
                            {/* Label only visible when active */}
                            <span className={`text-[10px] font-bold tracking-wide mt-1 transition-all duration-300 ${isActive ? `opacity-100 ${tab.color}` : 'opacity-0 h-0 overflow-hidden'}`}>
                                {tab.label}
                            </span>
                        </button>
                    );
                })}
            </nav>
        </div>
    );
}
