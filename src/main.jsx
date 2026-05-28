// ── Local font bundles (no Google Fonts CDN needed) ──
import '@fontsource/plus-jakarta-sans/300.css'
import '@fontsource/plus-jakarta-sans/400.css'
import '@fontsource/plus-jakarta-sans/500.css'
import '@fontsource/plus-jakarta-sans/600.css'
import '@fontsource/plus-jakarta-sans/700.css'
import '@fontsource/plus-jakarta-sans/800.css'
import '@fontsource/jetbrains-mono/400.css'
import '@fontsource/jetbrains-mono/500.css'

import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import GlobalErrorBoundary from './components/GlobalErrorBoundary'
import { AppSettingsProvider } from './context/AppSettingsContext'
import { ProfileProvider } from './context/ProfileContext'
import { LearningProvider } from './context/LearningContext'
import { AuthProvider } from './context/AuthContext'
import { NavigationProvider } from './context/NavigationContext'
import { AppStateProvider } from './context/AppStateContext'
import ApiErrorHandler from './components/ApiErrorHandler'

// ── PWA Service Worker Registration ──
import { registerSW } from 'virtual:pwa-register'

const updateSW = registerSW({
  onNeedRefresh() {
    if (confirm('New version available! Update now?')) {
      updateSW(true)
    }
  },
  onOfflineReady() {
    console.log('LabMind AI is ready to work offline!')
  },
  onRegistered(registration) {
    console.log('Service worker registered:', registration)
  },
  onRegisterError(error) {
    console.error('Service worker registration error:', error)
  }
})


/* ═══════════════════════════════════════════════════════════════
   Provider Wrapping Order (outermost → innermost):

   1. BrowserRouter         — React Router (useNavigate/useLocation)
   2. AppSettingsProvider    — theme, language (pure UI, no deps)
   3. ProfileProvider        — user profile form state (no deps)
   4. LearningProvider       — learning mode toggles (no deps)
   5. AuthProvider           — JWT auth, currentUser (no deps)
   6. GlobalErrorBoundary   — catches errors BELOW auth (preserves context)
   7. NavigationProvider     — useNavigate/useLocation bridge (needs Router)
   8. AppStateProvider       — user, alerts, records (needs Navigation)
   9. ApiErrorHandler        — network/server error banner (needs nothing)
  10. <App />                — consumes all contexts, renders <Routes>
   ═══════════════════════════════════════════════════════════════ */

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AppSettingsProvider>
        <ProfileProvider>
          <LearningProvider>
            <AuthProvider>
              <GlobalErrorBoundary>
                <NavigationProvider>
                  <AppStateProvider>
                    <ApiErrorHandler>
                      <App />
                    </ApiErrorHandler>
                  </AppStateProvider>
                </NavigationProvider>
              </GlobalErrorBoundary>
            </AuthProvider>
          </LearningProvider>
        </ProfileProvider>
      </AppSettingsProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
