import { useState, useEffect, useContext, useRef } from 'react'
import HTMLFlipBook from 'react-pageflip'
import { useAppState } from '../../context/AppStateContext'

function StarRating({ rating, bookId, editable, onRate, size }) {
  const [hover, setHover] = useState(0)
  const starSize = size || 16
  const display = hover || rating

  return (
    <div style={{ 
      display: 'flex', 
      gap: 3, 
      alignItems: 'center'
    }}>
      {[1,2,3,4,5].map(i => (
        <span
          key={i}
          onClick={editable ? () => onRate(i) : undefined}
          onMouseEnter={editable ? () => setHover(i) : undefined}
          onMouseLeave={editable ? () => setHover(0) : undefined}
          style={{
            fontSize: starSize,
            lineHeight: 1,
            color: i <= Math.round(display) ? '#f0b429' : '#3a3631',
            cursor: editable ? 'pointer' : 'default',
            transition: 'color 0.15s, transform 0.15s',
            transform: (editable && hover === i) ? 'scale(1.2)' : 'scale(1)',
            userSelect: 'none'
          }}
        >★</span>
      ))}
      {!editable && (
        <span style={{ 
          fontSize: starSize * 0.7, 
          color: '#888', 
          marginRight: 5,
          fontWeight: 600
        }}>
          {rating.toFixed(1)}
        </span>
      )}
    </div>
  )
}

export default function ImageReader({ book, onClose, readerVisible, onRate }) {
  const [totalPages, setTotalPages] = useState(book.totalPages || 0)
  const [currentPage, setCurrentPage] = useState(() => {
    const saved = localStorage.getItem(`labmind_book_${book.id}_page`)
    return saved ? parseInt(saved) + 1 : 1
  })
  const [xpAwarded, setXpAwarded] = useState(false)
  const [userRating, setUserRating] = useState(() => {
    const saved = localStorage.getItem(`labmind_book_${book.id}_userrating`)
    return saved ? parseFloat(saved) : 0
  })
  const [zoom, setZoom] = useState(1.0)
  const [imgLoading, setImgLoading] = useState(false)
  const [loadedPages, setLoadedPages] = useState({})
  const [showHint, setShowHint] = useState(true)
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 500,
    height: typeof window !== 'undefined' ? window.innerHeight : 700
  })
  const flipRef = useRef(null)
  const { addXp } = useAppState()

  useEffect(() => {
    function handleResize() {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      })
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const zoomBtnStyle = {
    background: 'rgba(200,134,10,0.1)',
    border: '1px solid rgba(200,134,10,0.25)',
    borderRadius: 6,
    padding: '4px 10px',
    color: '#c8860a',
    fontSize: 16,
    cursor: 'pointer'
  }

  // GitHub CDN base URL for book pages
  const GITHUB_CDN = 'https://raw.githubusercontent.com/b43008943-ctrl/labmind-ai/main/public/book-pages'

  function isLocalDev() {
    return window.location.hostname === 'localhost' ||
           window.location.hostname.startsWith('192.168.')
  }

  function getPageUrl(pageNum) {
    const padded = String(pageNum).padStart(4, '0')
    if (isLocalDev()) {
      return `/book-pages/${book.pageFolder}/page-${padded}.webp`
    }
    return `${GITHUB_CDN}/${book.pageFolder}/page-${padded}.webp`
  }

  // ON MOUNT — load manifest to get total pages
  useEffect(() => {
    const manifestUrl = isLocalDev()
      ? `/book-pages/${book.pageFolder}/manifest.json`
      : `${GITHUB_CDN}/${book.pageFolder}/manifest.json`

    fetch(manifestUrl)
      .then(r => r.json())
      .then(data => {
        setTotalPages(data.pages)
      })
      .catch(() => {
        // Fallback to book's embedded page count
        if (book.totalPages) setTotalPages(book.totalPages)
      })
  }, [book.pageFolder])

  // PAPER FLIP SOUND (White noise paper rustle synthesis)
  function playFlipSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      const bufferSize = ctx.sampleRate * 0.25
      const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate)
      const data = buffer.getChannelData(0)
      for (let i = 0; i < bufferSize; i++) {
        // fading noise
        data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize) * 0.3
      }
      const noise = ctx.createBufferSource()
      noise.buffer = buffer
      
      // bandpass filter to make it sound like paper
      const filter = ctx.createBiquadFilter()
      filter.type = 'bandpass'
      filter.frequency.value = 2500
      filter.Q.value = 0.6
      
      const gain = ctx.createGain()
      gain.gain.setValueAtTime(0.4, ctx.currentTime)
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25)
      
      noise.connect(filter)
      filter.connect(gain)
      gain.connect(ctx.destination)
      noise.start()
      noise.stop(ctx.currentTime + 0.25)
    } catch (e) {}
  }

  // LAZY LOADING window (±4 pages of current view)
  function shouldLoadPage(pageIndex) {
    return Math.abs(pageIndex - (currentPage - 1)) <= 4
  }

  // Keyboard navigation (ArrowLeft → Prev, ArrowRight → Next)
  useEffect(() => {
    function handleKeyDown(e) {
      if (!flipRef.current || !flipRef.current.pageFlip()) return
      if (e.key === 'ArrowLeft') {
        flipRef.current.pageFlip().flipPrev()
      } else if (e.key === 'ArrowRight') {
        flipRef.current.pageFlip().flipNext()
      } else if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  // Fade out keyboard hint after 3 seconds
  useEffect(() => {
    const timer = setTimeout(() => setShowHint(false), 3000)
    return () => clearTimeout(timer)
  }, [])

  if (totalPages === 0) {
    return (
      <div style={{
        position: 'fixed',
        inset: 0,
        background: 'linear-gradient(135deg, #1a1410 0%, #0f0c09 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 2000,
        color: '#e8c87a',
        fontFamily: 'sans-serif',
        fontSize: 16
      }}>
        جاري تحميل الكتاب...
      </div>
    )
  }

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'linear-gradient(135deg, #1a1410 0%, #0f0c09 100%)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 2000,
      direction: 'ltr',
      opacity: readerVisible ? 1 : 0,
      transition: 'opacity 0.3s ease'
    }}>
      {/* SHIMMER STYLE */}
      <style>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%) }
          100% { transform: translateX(100%) }
        }
      `}</style>

      {/* PART 4 — PROGRESS BAR */}
      <div style={{
        height: 3,
        background: 'rgba(255,255,255,0.06)',
        position: 'relative'
      }}>
        <div style={{
          position: 'absolute',
          left: 0, top: 0, bottom: 0,
          width: `${(currentPage / totalPages) * 100}%`,
          background: 'linear-gradient(90deg, #c8860a, #e8a020)',
          borderRadius: '0 2px 2px 0',
          transition: 'width 0.3s ease'
        }} />
      </div>

      {/* PART 3 — BEAUTIFUL TOP BAR */}
      <div style={{
        background: 'linear-gradient(180deg, #1a1208 0%, #110e08 100%)',
        borderBottom: '1px solid rgba(200,134,10,0.2)',
        padding: '0 16px',
        height: 56,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 2px 20px rgba(0,0,0,0.5)',
        flexShrink: 0
      }}>
        {/* LEFT — back button */}
        <button onClick={onClose} style={{
          background: 'transparent',
          border: '1px solid rgba(200,134,10,0.25)',
          borderRadius: 8,
          padding: '6px 12px',
          color: '#c8860a',
          fontSize: 13,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 6
        }}>
          ← Back
        </button>

        {/* CENTER — book title + progress */}
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: 14, fontWeight: 700,
            color: '#e8c87a',
            maxWidth: 200,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {book.title}
          </div>
          <div style={{
            fontSize: 11, color: '#7a6a50', marginTop: 2
          }}>
            Page {currentPage} of {totalPages}
          </div>
        </div>

        {/* RIGHT — zoom controls */}
        <div style={{ display: 'flex', gap: 6 }}>
          <button onClick={() => setZoom(z => Math.max(0.6, z - 0.2))}
            style={zoomBtnStyle}>－</button>
          <button onClick={() => setZoom(z => Math.min(2.0, z + 0.2))}
            style={zoomBtnStyle}>＋</button>
        </div>
      </div>

      {/* FLIPBOOK VIEWPORT */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        overflowY: 'auto',
        overflowX: 'hidden',
        flex: 1,
        padding: '12px 8px',
        background: 'linear-gradient(135deg, #1a1410, #0f0c09)',
        position: 'relative'
      }}>
        {/* reading lamp vignette overlay */}
        <div style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background: 'radial-gradient(ellipse 80% 70% at 50% 30%, transparent 40%, rgba(0,0,0,0.4) 100%)',
          zIndex: 10
        }} />

        {/* keyboard shortcuts hint */}
        <div style={{
          position: 'absolute',
          bottom: 80, left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(0,0,0,0.8)',
          border: '1px solid rgba(200,134,10,0.2)',
          borderRadius: 8,
          padding: '8px 16px',
          fontSize: 11,
          color: '#7a6a50',
          whiteSpace: 'nowrap',
          transition: 'opacity 0.5s ease',
          pointerEvents: 'none',
          opacity: showHint ? 1 : 0,
          zIndex: 100
        }}>
          ← → Arrow keys to navigate · Esc to close
        </div>

        <HTMLFlipBook
          ref={flipRef}
          width={Math.min(windowSize.width - 16, 500)}
          height={Math.min(windowSize.height - 140, 700)}
          size="stretch"
          minWidth={250}
          maxWidth={500}
          minHeight={350}
          maxHeight={650}
          showCover={true}
          mobileScrollSupport={true}
          flippingTime={700}
          usePortrait={true}
          startPage={currentPage - 1}
          onFlip={(e) => {
            setCurrentPage(e.data + 1)
            playFlipSound()
            
            // save progress
            localStorage.setItem(`labmind_book_${book.id}_page`, e.data)
            const pct = Math.round((e.data / (totalPages - 1 || 1)) * 100)
            localStorage.setItem(`labmind_book_${book.id}_progress`, Math.min(100, pct))
            
            // XP at end
            if (e.data >= totalPages - 2 && !xpAwarded) {
              addXp(100)
              setXpAwarded(true)
            }
          }}
          style={{
            margin: '0 auto',
            transform: `scale(${zoom})`,
            transformOrigin: 'center center',
            transition: 'transform 0.2s ease'
          }}
        >
          {Array.from({ length: totalPages }, (_, i) => (
            <div key={i} style={{
              background: '#f5f0e6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              overflow: 'hidden',
              boxShadow: '0 2px 4px rgba(0,0,0,0.15) inset, 0 20px 60px rgba(0,0,0,0.8), 0 0 0 1px rgba(0,0,0,0.3)',
              position: 'relative'
            }}>
              {shouldLoadPage(i) ? (
                <>
                  {!loadedPages[i] && (
                    <div style={{
                      width: '90%',
                      maxWidth: 500,
                      aspectRatio: '0.707',  // A4 ratio
                      background: 'linear-gradient(135deg, #2a2218, #1e1a12)',
                      borderRadius: 4,
                      position: 'relative',
                      overflow: 'hidden',
                      boxShadow: '0 20px 60px rgba(0,0,0,0.8)'
                    }}>
                      {/* shimmer effect */}
                      <div style={{
                        position: 'absolute',
                        inset: 0,
                        background: 'linear-gradient(90deg, transparent 0%, rgba(200,134,10,0.08) 50%, transparent 100%)',
                        animation: 'shimmer 1.5s infinite'
                      }} />
                      {/* page lines decoration */}
                      {[...Array(8)].map((_, iLine) => (
                        <div key={iLine} style={{
                          position: 'absolute',
                          left: '10%', right: '10%',
                          top: `${20 + iLine * 10}%`,
                          height: 1,
                          background: 'rgba(200,134,10,0.06)',
                          borderRadius: 1
                        }} />
                      ))}
                    </div>
                  )}
                  <div style={{
                    position: 'relative',
                    display: loadedPages[i] ? 'inline-block' : 'none',
                    filter: 'drop-shadow(0 0 40px rgba(200,134,10,0.12))'
                  }}>
                    <img
                      src={getPageUrl(i + 1)}
                      alt={`Page ${i + 1}`}
                      onLoad={() => {
                        setLoadedPages(prev => ({ ...prev, [i]: true }))
                        setImgLoading(false)
                      }}
                      onError={() => {
                        setLoadedPages(prev => ({ ...prev, [i]: true }))
                        setImgLoading(false)
                      }}
                      style={{
                        width: `${100 * zoom}%`,
                        maxWidth: `${800 * zoom}px`,
                        minWidth: '280px',
                        height: 'auto',
                        borderRadius: '4px',
                        boxShadow: '0 20px 60px rgba(0,0,0,0.8)',
                        display: imgLoading ? 'none' : 'block',
                        margin: '0 auto'
                      }}
                    />
                  </div>
                </>
              ) : (
                <div style={{
                  width: '100%', height: '100%',
                  background: '#ece5d5',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#7a6a50',
                  fontSize: 12,
                  fontFamily: 'sans-serif'
                }}>
                  Page {i + 1}
                </div>
              )}
              {/* Subtle page curl effect */}
              <div style={{
                position: 'absolute',
                bottom: 0, right: 0,
                width: 40, height: 40,
                background: 'linear-gradient(225deg, #e8e0d0 45%, rgba(0,0,0,0.15) 50%, transparent 60%)',
                borderRadius: '0 0 4px 0',
                pointerEvents: 'none'
              }} />
            </div>
          ))}
        </HTMLFlipBook>
      </div>

      {/* PART 5 — BEAUTIFUL BOTTOM BAR */}
      <div style={{
        background: 'linear-gradient(0deg, #1a1208 0%, #110e08 100%)',
        borderTop: '1px solid rgba(200,134,10,0.2)',
        padding: '12px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        boxShadow: '0 -2px 20px rgba(0,0,0,0.5)',
        flexShrink: 0
      }}>
        {/* ROW 1 — navigation */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* PREV button */}
          <button
            disabled={currentPage === 1}
            onClick={() => flipRef.current && flipRef.current.pageFlip().flipPrev()}
            style={{
              background: 'rgba(200,134,10,0.12)',
              border: '1px solid rgba(200,134,10,0.3)',
              borderRadius: 8,
              padding: '8px 16px',
              color: '#c8860a',
              fontSize: 18,
              cursor: 'pointer',
              opacity: currentPage === 1 ? 0.3 : 1,
              transition: 'opacity 0.2s'
            }}
          >
            ←
          </button>

          {/* SLIDER */}
          <input
            type="range"
            min={1}
            max={totalPages}
            value={currentPage}
            onChange={e => {
              const val = parseInt(e.target.value)
              setCurrentPage(val)
              setImgLoading(true)
              if (flipRef.current && flipRef.current.pageFlip()) {
                flipRef.current.pageFlip().flip(val - 1)
              }
            }}
            style={{
              flex: 1,
              accentColor: '#c8860a',
              height: 4,
              cursor: 'pointer'
            }}
          />

          {/* NEXT button */}
          <button
            disabled={currentPage === totalPages}
            onClick={() => flipRef.current && flipRef.current.pageFlip().flipNext()}
            style={{
              background: 'rgba(200,134,10,0.12)',
              border: '1px solid rgba(200,134,10,0.3)',
              borderRadius: 8,
              padding: '8px 16px',
              color: '#c8860a',
              fontSize: 18,
              cursor: 'pointer',
              opacity: currentPage === totalPages ? 0.3 : 1,
              transition: 'opacity 0.2s'
            }}
          >
            →
          </button>
        </div>

        {/* ROW 2 — page info + rating */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {/* LEFT: page percentage */}
          <div style={{ fontSize: 11, color: '#7a6a50' }}>
            {Math.round((currentPage / totalPages) * 100)}% complete
          </div>

          {/* RIGHT: star rating */}
          <StarRating
            rating={userRating || book.rating || 0}
            editable={true}
            size={20}
            onRate={(stars) => {
              setUserRating(stars)
              localStorage.setItem(`labmind_book_${book.id}_userrating`, stars)
              if (onRate) onRate(stars)
            }}
          />
        </div>
      </div>
    </div>
  )
}
