import { useState, useEffect } from 'react'

export default function PWAInstallButton() {
  const [deferredPrompt, setDeferredPrompt] = useState(null)
  const [showButton, setShowButton] = useState(false)
  const [installed, setInstalled] = useState(false)

  useEffect(() => {
    // check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setInstalled(true)
      return
    }

    const handler = (e) => {
      e.preventDefault()
      setDeferredPrompt(e)
      setShowButton(true)
    }

    window.addEventListener('beforeinstallprompt', handler)
    window.addEventListener('appinstalled', () => {
      setInstalled(true)
      setShowButton(false)
    })

    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const handleInstall = async () => {
    if (!deferredPrompt) return
    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') {
      setShowButton(false)
      setInstalled(true)
    }
    setDeferredPrompt(null)
  }

  if (installed || !showButton) return null

  return (
    <button
      onClick={handleInstall}
      style={{
        position: 'fixed',
        bottom: 80,
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'linear-gradient(135deg, #c8860a, #e8a020)',
        color: '#0d0b08',
        border: 'none',
        borderRadius: 12,
        padding: '12px 24px',
        fontSize: 14,
        fontWeight: 700,
        cursor: 'pointer',
        zIndex: 9999,
        boxShadow: '0 8px 24px rgba(200,134,10,0.4)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        whiteSpace: 'nowrap'
      }}
    >
      📲 Install LabMind AI
    </button>
  )
}
