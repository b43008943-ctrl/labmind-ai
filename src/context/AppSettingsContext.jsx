import React, { createContext, useContext, useState } from 'react';

const AppSettingsContext = createContext();

/* ─── Global style map ─── */
const THEME_CONFIG = {
    aurora: {
        className: 'dark-bio-theme',
        style: {},
    },
    midnight: { className: 'bg-slate-900 text-white', style: {} },
    crimson: { className: 'bg-red-950 text-white', style: {} },
    default: { className: 'bg-[#0a0a0f] text-white', style: {} },
};

export function AppSettingsProvider({ children }) {
    // ── Theme — persisted to localStorage ──
    const [theme, setThemeState] = useState(
        () => localStorage.getItem('labmind_theme') || 'default'
    );
    const setTheme = (val) => {
        setThemeState(val);
        localStorage.setItem('labmind_theme', val);
    };

    // ── Language — persisted to localStorage ──
    const [language, setLanguageState] = useState(
        () => localStorage.getItem('labmind_language') || 'en'
    );
    const setLanguage = (val) => {
        setLanguageState(val);
        localStorage.setItem('labmind_language', val);
    };

    // No theme uses 'light' style anymore, they are all dark mode UIs with different backgrounds
    const isLight = false;
    const config = THEME_CONFIG[theme] || THEME_CONFIG.default;

    return (
        <AppSettingsContext.Provider value={{ theme, setTheme, language, setLanguage, isLight }}>
            <div
                className={`min-h-screen ${config.className}`}
                style={config.style}
            >
                {children}
            </div>
        </AppSettingsContext.Provider>
    );
}

export function useAppSettings() {
    return useContext(AppSettingsContext);
}
