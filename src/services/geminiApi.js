/* ═══════════════════════════════════════════════════════════════
   GEMINI API SERVICE — Secure Backend Proxy
   ═══════════════════════════════════════════════════════════════
   
   All AI calls are proxied through the LabMind backend.
   The Gemini API key NEVER reaches the browser.
   
   Migrated from direct Gemini calls on 2026-04-09 (security fix).
   ═══════════════════════════════════════════════════════════════ */

import { API_BASE_URL as API_BASE } from './apiClient';

/**
 * Internal helper — authenticated POST to backend AI proxy.
 */
async function aiRequest(endpoint, body) {
    const token = localStorage.getItem('labmind_token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE}/api/ai${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message = errorData?.detail || errorData?.error || `Request failed (${response.status})`;
        throw new Error(message);
    }

    return response.json();
}

/**
 * Reads a File object and returns its text content.
 */
async function extractFileText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

/**
 * Generates an AI video script/content using the backend Gemini proxy.
 *
 * @param {File}   file        — The uploaded research file
 * @param {Object} parameters  — User-selected synthesis parameters (preserved for UI compat)
 * @param {Function} onStatusUpdate — Callback to update UI status text
 *
 * @returns {Promise<{ success: boolean, content: string, error?: string }>}
 */
export async function generateAiVideo(file, parameters, onStatusUpdate) {
    try {
        // ── Step 1: Extract text from uploaded file ──
        onStatusUpdate?.('PARSING DATA CORE...');
        const fileText = await extractFileText(file);

        if (!fileText || fileText.trim().length === 0) {
            return { success: false, content: null, error: 'File appears to be empty or unreadable.' };
        }

        // ── Step 2: Send to backend proxy ──
        onStatusUpdate?.('TRANSMITTING TO NEURAL CORE...');
        await new Promise(resolve => setTimeout(resolve, 500)); // Brief UI delay

        onStatusUpdate?.('RENDERING VISUAL SEQUENCE...');
        const data = await aiRequest('/generate-video-script', {
            file_text: fileText.substring(0, 50000),
        });

        if (!data.success) {
            return { success: false, content: null, error: data.error || 'Server returned an error.' };
        }

        if (!data.content) {
            return { success: false, content: null, error: 'AI returned an empty response.' };
        }

        onStatusUpdate?.('FINALIZING OUTPUT...');
        return { success: true, content: data.content };

    } catch (error) {
        return { success: false, content: null, error: `Network Error: ${error.message}` };
    }
}

/**
 * Generates an interactive multiple-choice quiz based on the provided text.
 *
 * @param {string} text - The input text for which the quiz should be generated.
 * @returns {Promise<{ success: boolean, data: Array, error?: string }>}
 */
export async function generateSmartQuiz(text) {
    try {
        const data = await aiRequest('/generate-smart-quiz', { text });

        if (!data.success) {
            return { success: false, data: null, error: data.error || 'Server returned an error.' };
        }

        return { success: true, data: data.data };

    } catch (error) {
        return { success: false, data: null, error: `Network Error: ${error.message}` };
    }
}

/**
 * Dynamically generates an image using the backend Gemini/Imagen proxy.
 * Falls back to Pollinations.ai on the server side.
 */
export async function generateHoloImage(prompt, onStatusUpdate) {
    try {
        onStatusUpdate?.('TRANSMITTING TO NEURAL RENDERING ENGINE...');

        const data = await aiRequest('/generate-holo-image', { prompt });

        if (!data.success) {
            return { success: false, url: null, error: data.error || 'Server returned an error.' };
        }

        onStatusUpdate?.('HOLOGRAPHIC RENDER COMPLETE');
        return { success: true, url: data.url };

    } catch (error) {
        return { success: false, url: null, error: `Network Error: ${error.message}` };
    }
}
