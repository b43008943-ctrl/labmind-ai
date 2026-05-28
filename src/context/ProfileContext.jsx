/* ═══════════════════════════════════════════════════════════════
   LABMIND AI — Profile Context (Backend-Persisted)
   ═══════════════════════════════════════════════════════════════
   Manages the user profile form state. Changes are persisted to
   the backend via PUT /api/auth/profile.

   On initial load (if authenticated), hydrates from AuthContext.
   On save, writes to backend and syncs AuthContext.
   ═══════════════════════════════════════════════════════════════ */

import { createContext, useContext, useState, useCallback, useMemo } from 'react';
import { updateUserProfile } from '../services/apiClient';

const ProfileContext = createContext();

const DEFAULT_PROFILE = {
    userName: 'DR. COMMANDER ALPHA',
    userEmail: 'agent@elite-network.com',
    userPassword: '',
    specimenId: '9X-774A',
    clearance: 'ELITE',
    alias: 'CLASSIFIED',
    rank: 'COMMANDER',
    accessKey: '*****',
    syncFreq: '500ms',
    bioStatus: 'OPTIMAL',
    serverZone: 'US-EAST-1',
    coordinates: '40.7128 / -74.0060',
};

export function ProfileProvider({ children }) {
    const [profile, setProfile] = useState(DEFAULT_PROFILE);
    const [isSaving, setIsSaving] = useState(false);
    const [saveError, setSaveError] = useState(null);
    const [saveSuccess, setSaveSuccess] = useState(false);

    /**
     * Update profile fields in local state (immediate, no backend call).
     * Used for hydrating from AuthContext and local-only fields.
     */
    const updateProfile = useCallback((updates) => {
        setProfile((prev) => ({ ...prev, ...updates }));
    }, []);

    /**
     * Persist profile changes to the backend.
     * Only sends fields that the backend accepts (full_name, rank_title, avatar_url).
     *
     * @param {object} localUpdates — profile field updates (using frontend keys)
     * @param {function} [onAuthSync] — callback to sync AuthContext after success
     * @returns {{ success: boolean, error?: string }}
     */
    const saveProfile = useCallback(async (localUpdates, onAuthSync) => {
        setIsSaving(true);
        setSaveError(null);
        setSaveSuccess(false);

        try {
            // Map frontend profile keys → backend API field names
            const apiPayload = {};
            if (localUpdates.userName !== undefined) apiPayload.full_name = localUpdates.userName;
            if (localUpdates.rank !== undefined) apiPayload.rank_title = localUpdates.rank;
            if (localUpdates.avatarUrl !== undefined) apiPayload.avatar_url = localUpdates.avatarUrl;

            // Only call API if there are backend-persistable fields
            if (Object.keys(apiPayload).length > 0) {
                const updatedUser = await updateUserProfile(apiPayload);

                // Sync AuthContext with the fresh server data
                if (onAuthSync && updatedUser) {
                    onAuthSync(updatedUser);
                }
            }

            // Update local profile state
            setProfile((prev) => ({ ...prev, ...localUpdates }));
            setSaveSuccess(true);

            // Auto-clear success message after 3s
            setTimeout(() => setSaveSuccess(false), 3000);

            return { success: true };
        } catch (err) {
            const errorMessage = err?.message || 'Failed to save profile';
            setSaveError(errorMessage);
            console.error('[ProfileContext] Save failed:', err);

            // Auto-clear error after 5s
            setTimeout(() => setSaveError(null), 5000);

            return { success: false, error: errorMessage };
        } finally {
            setIsSaving(false);
        }
    }, []);

    /**
     * Clear save status messages.
     */
    const clearSaveStatus = useCallback(() => {
        setSaveError(null);
        setSaveSuccess(false);
    }, []);

    const value = useMemo(() => ({
        profile,
        updateProfile,
        saveProfile,
        isSaving,
        saveError,
        saveSuccess,
        clearSaveStatus,
    }), [profile, updateProfile, saveProfile, isSaving, saveError, saveSuccess, clearSaveStatus]);

    return (
        <ProfileContext.Provider value={value}>
            {children}
        </ProfileContext.Provider>
    );
}

export function useProfile() {
    return useContext(ProfileContext);
}
