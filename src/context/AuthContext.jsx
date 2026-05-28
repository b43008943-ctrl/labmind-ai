/* ═══════════════════════════════════════════════════════════════
   LABMIND AI — Auth Context
   ═══════════════════════════════════════════════════════════════
   Provides authenticated user state to the entire app tree.
   On mount, attempts to bootstrap from a stored JWT token.
   ═══════════════════════════════════════════════════════════════ */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { fetchCurrentUser, clearToken, getToken, API_BASE_URL } from '../services/apiClient';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [currentUser, setCurrentUser] = useState(null);
    const [isBootstrapping, setIsBootstrapping] = useState(true);
    const [authError, setAuthError] = useState(null);

    const logout = useCallback(() => {
        clearToken();
        setCurrentUser(null);
        setAuthError(null);
    }, []);

    // Bootstrap — try to restore session from stored token
    useEffect(() => {
        const token = getToken();
        if (!token) {
            setIsBootstrapping(false);
            return;
        }

        fetchCurrentUser()
            .then((user) => {
                setCurrentUser(user);
            })
            .catch(() => {
                // Token is invalid/expired — clear it
                clearToken();
            })
            .finally(() => {
                setIsBootstrapping(false);
            });
    }, []);

    // ── Silent JWT auto-refresh ──
    // Checks every 5 minutes; refreshes if < 10 min remain; logs out if expired.
    useEffect(() => {
        const INTERVAL = 5 * 60 * 1000;          // check every 5 minutes
        const REFRESH_BEFORE = 10 * 60 * 1000;    // refresh when < 10 min left

        // Use the same dynamic API base as apiClient
        const API_BASE = API_BASE_URL;

        const checkAndRefresh = async () => {
            const token = getToken();
            if (!token) return;

            try {
                // Decode JWT payload (base64url → JSON)
                const payload = JSON.parse(atob(token.split('.')[1]));
                const expiresAt = payload.exp * 1000; // seconds → ms
                const timeLeft = expiresAt - Date.now();

                // Token fully expired → force logout
                if (timeLeft <= 0) {
                    logout();
                    return;
                }

                // Less than 10 min left → silently refresh
                if (timeLeft < REFRESH_BEFORE) {
                    const response = await fetch(`${API_BASE}/api/auth/refresh`, {
                        method: 'POST',
                        headers: {
                            Authorization: `Bearer ${token}`,
                            'Content-Type': 'application/json',
                        },
                    });
                    if (response.ok) {
                        const data = await response.json();
                        if (data.access_token) {
                            // Use the apiClient tokenStore setter for consistency
                            localStorage.setItem('labmind_auth_token', data.access_token);
                            console.log('[Auth] Token refreshed silently');
                        }
                    }
                }
            } catch (err) {
                console.error('[Auth] Token refresh error:', err);
            }
        };

        // Run immediately on mount + every 5 minutes
        checkAndRefresh();
        const interval = setInterval(checkAndRefresh, INTERVAL);
        return () => clearInterval(interval);
    }, [currentUser, logout]);

    // ── Listen for 401 from apiClient's response interceptor ──
    useEffect(() => {
        const handleUnauthorized = () => {
            logout();
        };
        window.addEventListener('auth:unauthorized', handleUnauthorized);
        return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
    }, [logout]);

    return (
        <AuthContext.Provider
            value={{
                currentUser,
                setCurrentUser,
                isBootstrapping,
                authError,
                setAuthError,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
    return ctx;
}
