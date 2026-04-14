/**
 * Lightweight cookie notice banner.
 * Only shown once — dismissed state is stored in localStorage.
 * Since Iron Skillet only uses a functional session cookie (no tracking),
 * this is an informational notice rather than a consent gate.
 */
import { useState, useEffect } from 'react'

const STORAGE_KEY = 'cookie_notice_dismissed'

export default function CookieBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      setVisible(true)
    }
  }, [])

  const dismiss = () => {
    localStorage.setItem(STORAGE_KEY, '1')
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className="fixed bottom-0 inset-x-0 z-50 p-4 pointer-events-none">
      <div className="max-w-lg mx-auto bg-brand-raised border border-brand-border rounded-xl
                      shadow-xl px-5 py-4 flex items-center gap-4 pointer-events-auto">
        <p className="text-xs text-brand-silver leading-relaxed flex-1">
          This site uses a single session cookie to keep you logged in. No tracking or analytics cookies.{' '}
          <a href="/privacy" className="text-brand-blue underline hover:text-brand-blue-light transition-colors">
            Privacy policy
          </a>
        </p>
        <button
          onClick={dismiss}
          className="btn-steel px-4 py-1.5 text-xs whitespace-nowrap"
        >
          Got it
        </button>
      </div>
    </div>
  )
}
