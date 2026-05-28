/* GroupIcon — Renders a faction hologram icon with energy orb rings */

import { ICON_THEMES, resolveThemeKey } from './communityData';

export default function GroupIcon({ type }) {
    const themeKey = resolveThemeKey(type);
    const theme = ICON_THEMES[themeKey] || ICON_THEMES.dragon;

    return (
        <div className="relative w-full h-full flex items-center justify-center aspect-square max-h-[160px] mx-auto">
            {/* 1. THE ENERGY ORB (Rotating High Detail HUD Reactors) */}
            <div className="absolute inset-0 flex items-center justify-center">
                <div className="absolute w-[95%] h-[95%] border border-dashed rounded-full animate-[spin_10s_linear_infinite] opacity-30" style={{ borderColor: theme.color }} />
                <div className="absolute w-[80%] h-[80%] border-t-[3px] border-r border-dotted rounded-full animate-[spin_6s_linear_infinite_reverse] opacity-50" style={{ borderColor: theme.color, boxShadow: `0 0 10px ${theme.color}40` }} />
                <div className="absolute inset-0 blur-[60px] rounded-full opacity-10" style={{ backgroundColor: theme.color }} />
            </div>

            {/* 2. CIRCULAR SYMMETRY FOR IMAGE OR SVG */}
            <div
                className="relative z-10 w-[68%] h-[68%] rounded-full overflow-hidden flex items-center justify-center"
                style={{ boxShadow: theme.image ? `0 0 25px 5px ${theme.color}99` : 'none', border: theme.image ? `1px solid ${theme.color}60` : 'none' }}
            >
                {theme.image ? (
                    <img src={theme.image} alt="epic avatar" className="w-full h-full object-cover" />
                ) : (
                    <svg viewBox="0 0 24 24" className="w-[80%] h-[80%] animate-[pulse_5s_ease-in-out_infinite]"
                        style={{ filter: `drop-shadow(0 0 2px #fff) drop-shadow(0 0 10px ${theme.color}) drop-shadow(0 0 30px ${theme.color})` }}>
                        <path d={theme.path} fill="none" stroke={theme.color} strokeWidth="1" strokeLinecap="round" />
                    </svg>
                )}
            </div>
        </div>
    );
}
