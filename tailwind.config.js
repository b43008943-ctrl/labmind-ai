/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Montserrat', 'sans-serif'],
                orbitron: ['Orbitron', 'sans-serif'],
                rajdhani: ['Rajdhani', 'sans-serif'],
            },
            colors: {
                obsidian: '#030510',
                'neon-blue': '#0ea5e9',
                'neon-purple': '#a855f7',
                'neon-magenta': '#d946ef',
                'neon-green': '#10b981',
                'neon-orange': '#f97316',
                'neon-red': '#ef4444'
            },
            animation: {
                'spin-slow': 'spin 15s linear infinite',
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'float': 'float 6s ease-in-out infinite',
                'core-1': 'spin 10s linear infinite',
                'core-2': 'spin 8s linear infinite reverse',
                'scan-laser': 'scan-laser 3s ease-in-out infinite',
                'scan': 'scan 3s linear infinite',
                'hologram-flicker': 'hologram-flicker 2s infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                'scan-laser': {
                    '0%, 100%': { top: '0', opacity: '0' },
                    '10%': { opacity: '1' },
                    '50%': { top: '100%' },
                    '90%': { opacity: '1' },
                },
                'scan': {
                    '0%': { backgroundPosition: '0 -200%' },
                    '100%': { backgroundPosition: '0 200%' },
                },
                'hologram-flicker': {
                    '0%, 100%': { opacity: '1' },
                    '33%': { opacity: '0.85' },
                    '66%': { opacity: '0.95' },
                    '77%': { opacity: '0.8' },
                    '88%': { opacity: '0.9' },
                }
            }
        },
    },
    plugins: [],
}
