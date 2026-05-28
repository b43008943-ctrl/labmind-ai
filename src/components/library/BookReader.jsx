import { useState, useEffect, useRef } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import HTMLFlipBook from 'react-pageflip'
import { useAppState } from '../../context/AppStateContext'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

/* ═══════════════════════════════════════════════════════════════
   BookReader — Smart reader for local PDFs + info card for online books
   ═══════════════════════════════════════════════════════════════ */

function playPageSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.type = 'sine'
    osc.frequency.setValueAtTime(440, ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(220, ctx.currentTime + 0.15)
    gain.gain.setValueAtTime(0.06, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.2)
    osc.start()
    osc.stop(ctx.currentTime + 0.2)
  } catch (e) {}
}

/* ─── SECTION A: Local PDF Flipbook Reader ─── */
function LocalReader({ book, onClose }) {
  const [numPages, setNumPages] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [xpAwarded, setXpAwarded] = useState(false)
  const flipBookRef = useRef(null)
  const { addXp } = useAppState()

  const onDocumentLoadSuccess = ({ numPages: total }) => {
    setNumPages(total)
    setIsLoading(false)
    const saved = localStorage.getItem(`labmind_book_${book.id}_page`)
    if (saved) setCurrentPage(parseInt(saved))
  }

  // Save progress on every page change
  useEffect(() => {
    if (numPages === 0) return
    localStorage.setItem(`labmind_book_${book.id}_page`, currentPage)
    const pct = Math.round((currentPage / numPages) * 100)
    localStorage.setItem(`labmind_book_${book.id}_progress`, pct)

    // Award XP when reaching last page
    if (currentPage === numPages && numPages > 0 && !xpAwarded) {
      addXp(100)
      setXpAwarded(true)
      alert('📚 أتممت الكتاب! حصلت على +100 XP')
    }
  }, [currentPage, numPages])

  function goNext() {
    if (currentPage < numPages) {
      setCurrentPage(p => p + 1)
      flipBookRef.current?.pageFlip()?.flipNext()
      playPageSound()
    }
  }

  function goPrev() {
    if (currentPage > 1) {
      setCurrentPage(p => p - 1)
      flipBookRef.current?.pageFlip()?.flipPrev()
      playPageSound()
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: '#0d0b08',
      display: 'flex', flexDirection: 'column',
      fontFamily: "'Plus Jakarta Sans', sans-serif",
    }}>

      {/* ── TOP BAR ── */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 16px',
        background: 'rgba(13,11,8,0.97)',
        borderBottom: '1px solid rgba(200,134,10,0.2)',
        flexShrink: 0,
      }}>
        <button onClick={onClose} style={{
          width: 36, height: 36, borderRadius: 10,
          background: 'rgba(200,134,10,0.1)',
          border: '1px solid rgba(200,134,10,0.25)',
          color: '#c8860a', fontSize: 18, cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>←</button>
        <div style={{ flex: 1, marginLeft: 12, overflow: 'hidden' }}>
          <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#e8c87a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{book.title}</p>
          <p style={{ margin: 0, fontSize: 10, color: 'rgba(200,134,10,0.5)' }}>{book.author}</p>
        </div>
        <div style={{
          padding: '4px 10px', borderRadius: 20,
          background: 'rgba(200,134,10,0.1)',
          border: '1px solid rgba(200,134,10,0.2)',
          fontSize: 11, fontWeight: 700, color: '#c8860a',
          letterSpacing: 0.5, whiteSpace: 'nowrap',
        }}>
          {numPages > 0 ? `${currentPage} / ${numPages}` : '...'}
        </div>
      </div>

      {/* ── CENTER: PDF VIEWER ── */}
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: '20px 10px', overflow: 'hidden',
      }}>

        {/* Loading skeleton */}
        {isLoading && (
          <div style={{
            width: 350, height: 490,
            background: '#1a1610',
            borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexDirection: 'column',
            animation: 'bookPulse 1.5s ease-in-out infinite',
          }}>
            <style>{`
              @keyframes bookPulse {
                0%, 100% { opacity: 0.4; }
                50% { opacity: 0.8; }
              }
            `}</style>
            <span style={{ fontSize: 40, marginBottom: 12 }}>📖</span>
            <p style={{ margin: 0, fontSize: 14, color: 'rgba(200,134,10,0.5)' }}>جاري تحميل الكتاب...</p>
            <p style={{ margin: '4px 0 0', fontSize: 11, color: 'rgba(200,134,10,0.3)' }}>
              {book.source} • Free Resource
            </p>
          </div>
        )}

        <Document
          file={book.pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={() => { setIsLoading(false) }}
          loading=""
        >
          {!isLoading && numPages > 0 && (
            <HTMLFlipBook
              ref={flipBookRef}
              width={350}
              height={490}
              showCover={true}
              mobileScrollSupport={true}
              onFlip={(e) => {
                setCurrentPage(e.data + 1)
                playPageSound()
              }}
              style={{ boxShadow: '0 20px 60px rgba(0,0,0,0.8)' }}
            >
              {Array.from({ length: numPages }, (_, i) => (
                <div key={i} style={{
                  background: '#1a1610',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '100%',
                  height: '100%',
                }}>
                  <Page
                    pageNumber={i + 1}
                    width={340}
                    renderTextLayer={false}
                    renderAnnotationLayer={false}
                  />
                </div>
              ))}
            </HTMLFlipBook>
          )}
        </Document>
      </div>

      {/* ── BOTTOM CONTROLS ── */}
      {!isLoading && numPages > 0 && (
        <div style={{
          display: 'flex', alignItems: 'center',
          padding: '12px 16px',
          background: 'rgba(13,11,8,0.97)',
          borderTop: '1px solid rgba(200,134,10,0.2)',
          gap: 8, flexShrink: 0,
        }}>
          <button onClick={goPrev} disabled={currentPage <= 1} style={{
            width: 40, height: 40, borderRadius: 10,
            background: currentPage > 1 ? 'rgba(200,134,10,0.1)' : 'rgba(255,255,255,0.03)',
            border: currentPage > 1 ? '1px solid rgba(200,134,10,0.25)' : '1px solid rgba(255,255,255,0.06)',
            color: currentPage > 1 ? '#c8860a' : 'rgba(255,255,255,0.15)',
            fontSize: 18, cursor: currentPage > 1 ? 'pointer' : 'default',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>‹</button>

          <input
            type="range"
            min={1}
            max={numPages}
            value={currentPage}
            onChange={(e) => {
              const p = parseInt(e.target.value)
              setCurrentPage(p)
              playPageSound()
            }}
            style={{ flex: 1, accentColor: '#c8860a', margin: '0 4px' }}
          />

          <button onClick={goNext} disabled={currentPage >= numPages} style={{
            width: 40, height: 40, borderRadius: 10,
            background: currentPage < numPages ? 'rgba(200,134,10,0.1)' : 'rgba(255,255,255,0.03)',
            border: currentPage < numPages ? '1px solid rgba(200,134,10,0.25)' : '1px solid rgba(255,255,255,0.06)',
            color: currentPage < numPages ? '#c8860a' : 'rgba(255,255,255,0.15)',
            fontSize: 18, cursor: currentPage < numPages ? 'pointer' : 'default',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>›</button>
        </div>
      )}
    </div>
  )
}

/* ─── SECTION B: Online Book Info Card ─── */
function OnlineBookCard({ book, onClose }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(5,4,2,0.95)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: "'Plus Jakarta Sans', sans-serif",
      padding: 20,
    }}>
      <div style={{
        maxWidth: 340, width: '100%',
        background: '#110e08',
        border: '1px solid rgba(200,134,10,0.25)',
        borderRadius: 16,
        padding: '28px 24px',
        display: 'flex', flexDirection: 'column', alignItems: 'center',
      }}>
        {/* Icon */}
        <div style={{ fontSize: 48, marginBottom: 8 }}>
          {book.icon || '📚'}
        </div>

        {/* Category badge */}
        <div style={{
          background: 'rgba(200,134,10,0.12)',
          color: '#c8860a',
          fontSize: 11,
          padding: '4px 10px',
          borderRadius: 20,
          letterSpacing: 1,
          textTransform: 'uppercase',
          fontWeight: 700,
        }}>
          {book.category}
        </div>

        {/* Title */}
        <h2 style={{
          fontSize: 20, color: '#e8c87a', fontWeight: 700,
          textAlign: 'center', marginTop: 12, lineHeight: 1.3,
          margin: '12px 0 0',
        }}>
          {book.title}
        </h2>

        {/* Author */}
        <p style={{
          fontSize: 13, color: '#7a6a50', textAlign: 'center',
          marginTop: 4, margin: '4px 0 0',
        }}>
          {book.author}
        </p>

        {/* Divider */}
        <div style={{
          height: 1,
          background: 'rgba(200,134,10,0.15)',
          width: '100%',
          margin: '16px 0',
        }} />

        {/* Description */}
        <p style={{
          fontSize: 13, color: '#a09070', textAlign: 'center',
          lineHeight: 1.6, margin: 0,
        }}>
          {book.description}
        </p>

        {/* License */}
        <p style={{
          fontSize: 11, color: '#50c8a0', textAlign: 'center',
          marginTop: 8, margin: '8px 0 0',
        }}>
          🔓 {book.license || 'Open Access'}
        </p>

        {/* Source */}
        <p style={{
          fontSize: 11, color: '#7a6a50', textAlign: 'center',
          margin: '4px 0 0',
        }}>
          المصدر: Archive.org
        </p>

        {/* Buttons */}
        <div style={{
          display: 'flex', gap: 8, marginTop: 20, width: '100%',
          flexWrap: 'wrap',
        }}>
          <button
            onClick={() => window.open(book.url, '_blank')}
            style={{
              flex: 1, minWidth: '45%', background: '#c8860a', color: '#0d0b08',
              border: 'none', borderRadius: 8, padding: '11px 0',
              fontSize: 13, fontWeight: 700, cursor: 'pointer',
            }}
          >
            فتح الكتاب 🌐
          </button>
          {book.pdfUrl && (
            <button
              onClick={() => window.open(book.pdfUrl, '_blank')}
              style={{
                flex: 1, minWidth: '45%', background: 'transparent',
                border: '1px solid rgba(200,134,10,0.4)',
                borderRadius: 8, padding: '11px 0',
                color: '#c8860a', fontSize: 13, fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              تحميل PDF ↓
            </button>
          )}
          <button
            onClick={onClose}
            style={{
              width: '100%', background: 'transparent',
              border: '1px solid rgba(200,134,10,0.15)',
              color: '#7a6a50', borderRadius: 8, padding: '10px 0',
              fontSize: 12, cursor: 'pointer', marginTop: 4,
            }}
          >
            رجوع ←
          </button>
        </div>
      </div>
    </div>
  )
}

/* ─── Main Export ─── */
export default function BookReader({ book, onClose }) {
  if (book.isLocal) {
    return <LocalReader book={book} onClose={onClose} />
  }
  return <OnlineBookCard book={book} onClose={onClose} />
}
