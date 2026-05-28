/* ═══════════════════════════════════════════════════════════════
   LABMIND AI — Navigation Context (Phase 2 — React Router Active)
   ═══════════════════════════════════════════════════════════════
   The bridge layer is now LIVE. It translates legacy view-key
   navigation calls (e.g. onNavigate('hematology-lab')) into
   React Router URL navigation (e.g. navigate('/lab/hematology')).

   Screens still call onNavigate(viewKey) — this context maps
   viewKey → URL path and calls React Router's navigate().

   The `currentView` is now DERIVED from the URL via useLocation(),
   not from a useState. This means:
   - Browser back/forward buttons work
   - Direct URL access works
   - Page refresh preserves the current screen
   ═══════════════════════════════════════════════════════════════ */

import { createContext, useContext, useState, useCallback, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { viewKeyToPath, pathToViewKey } from '../routes';

const NavigationContext = createContext(null);

export function NavigationProvider({ children }) {
    const routerNavigate = useNavigate();
    const location = useLocation();

    // ─── Derive currentView from the current URL path ───
    // This replaces the old useState('splash') entirely.
    // We match progressively: try exact path first, then try parent segments.
    const currentView = useMemo(() => {
        const path = location.pathname;

        // Exact match
        if (pathToViewKey[path]) return pathToViewKey[path];

        // Try parent path for nested routes (e.g. /lab/hematology → check /lab)
        const segments = path.split('/').filter(Boolean);
        while (segments.length > 0) {
            const parentPath = '/' + segments.join('/');
            if (pathToViewKey[parentPath]) return pathToViewKey[parentPath];
            segments.pop();
        }

        // Fallback: root path → splash
        return pathToViewKey['/'] || 'splash';
    }, [location.pathname]);

    // ─── Alerts overlay state (intercepted navigation target) ───
    const [alertsOpen, setAlertsOpen] = useState(false);

    // ─── Navigation data — passed alongside view transitions ───
    const [navData, setNavData] = useState(null);

    /**
     * Navigate to a view by legacy view key.
     * Translates viewKey → URL path and calls React Router navigate().
     *
     * Screens call: onNavigate('hematology-lab')
     * This translates to: navigate('/lab/hematology')
     *
     * Exit animations are handled by the SCREEN COMPONENT itself
     * (they setTimeout 600ms before calling onNavigate), so we
     * navigate immediately here.
     *
     * @param {string} target — legacy view key (e.g. 'dashboard', 'hematology-lab')
     * @param {object} [data] — optional data to pass via React Router state
     */
    const navigate = useCallback((target, data = null) => {
        // Intercept 'alerts' — open overlay instead of changing URL
        if (target === 'alerts') {
            setAlertsOpen(true);
            return;
        }

        // Look up the URL for this view key
        let path = viewKeyToPath[target];

        if (!path) {
            // If it's already a known path (e.g., 'battle' -> '/battle') or starts with '/'
            if (pathToViewKey[target] || pathToViewKey['/' + target]) {
                path = target.startsWith('/') ? target : '/' + target;
            } else if (target.startsWith('/')) {
                path = target;
            }
        }

        if (path) {
            routerNavigate(path, data ? { state: data } : undefined);
        } else {
            // Unknown view key — try navigating as a raw path, fallback to dashboard
            console.warn(`[NavigationContext] Unknown view key or path: "${target}", falling back to /dashboard`);
            routerNavigate('/dashboard');
        }

        if (data) setNavData(data);
    }, [routerNavigate]);

    /**
     * Go back to the previous page using browser history.
     */
    const goBack = useCallback(() => {
        routerNavigate(-1);
        setNavData(null);
    }, [routerNavigate]);

    /**
     * Get the URL path for a view key.
     * @param {string} viewKey
     * @returns {string} URL path
     */
    const getPathForView = useCallback((viewKey) => {
        return viewKeyToPath[viewKey] || '/dashboard';
    }, []);

    /**
     * Direct navigation for non-user-initiated transitions
     * (e.g. JWT session restore that skips splash → dashboard).
     * Uses `replace: true` to avoid polluting browser history.
     */
    const setView = useCallback((viewKey) => {
        const path = viewKeyToPath[viewKey];
        if (path) {
            routerNavigate(path, { replace: true });
        }
    }, [routerNavigate]);

    const value = useMemo(() => ({
        currentView,
        navigate,
        goBack,
        setView,
        getPathForView,
        navData,
        setNavData,
        alertsOpen,
        setAlertsOpen,
    }), [currentView, navigate, goBack, setView, getPathForView, navData, alertsOpen]);

    return (
        <NavigationContext.Provider value={value}>
            {children}
        </NavigationContext.Provider>
    );
}

export function useNavigation() {
    const ctx = useContext(NavigationContext);
    if (!ctx) throw new Error('useNavigation must be used within a NavigationProvider');
    return ctx;
}
