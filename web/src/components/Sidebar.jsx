/**
 * Sidebar navigation — dark forge theme.
 * Ogre logo, page links, Generate Email Plan action, logout.
 */
import { NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { useOnboarding } from '../context/OnboardingContext'
import { triggerEmailPlan } from '../api/client'
import OgreLoading from './OgreLoading'

const NAV = [
  { to: '/tonight',   label: 'Tonight',       icon: '🌙' },
  { to: '/recipes',   label: 'Recipes',        icon: '📚' },
  { to: '/instant',   label: 'Instant Chef',   icon: '⚡' },
  { to: '/shopping',  label: 'Shopping List',  icon: '🛒' },
  { to: '/dashboard', label: 'Dashboard',      icon: '📊' },
  { to: '/settings',  label: 'Settings',       icon: '⚙️' },
]

function OnboardingChecklist() {
  const navigate = useNavigate()
  const { hasRecipes, hasDietaryPrefs, hasCooked, allDone, loading, dismissed, dismiss } = useOnboarding()

  if (loading || dismissed || allDone) return null

  const items = [
    { done: hasRecipes,      label: 'Add your first recipe',   to: '/recipes' },
    { done: hasDietaryPrefs, label: 'Set dietary preferences',  to: '/settings' },
    { done: hasCooked,       label: 'Log a cook',              to: '/tonight' },
  ]

  const completed = items.filter((i) => i.done).length

  return (
    <div className="mx-3 mb-2 rounded-xl bg-brand-bg border border-brand-border p-3">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-bold text-brand-silver uppercase tracking-widest">
          Getting Started
        </p>
        <button
          onClick={dismiss}
          className="text-brand-muted hover:text-brand-silver text-xs transition-colors"
          title="Dismiss"
        >
          ✕
        </button>
      </div>

      {/* Progress bar */}
      <div className="w-full h-1.5 bg-brand-raised rounded-full mb-3 overflow-hidden">
        <div
          className="h-full bg-brand-fire rounded-full transition-all duration-500"
          style={{ width: `${(completed / items.length) * 100}%` }}
        />
      </div>

      <div className="space-y-1">
        {items.map((item) => (
          <button
            key={item.label}
            onClick={() => navigate(item.to)}
            className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left
                       hover:bg-brand-raised/60 transition-colors group"
          >
            <span className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 text-[10px]
              ${item.done
                ? 'border-brand-green bg-brand-green text-white'
                : 'border-brand-border group-hover:border-brand-fire'
              }`}>
              {item.done && '✓'}
            </span>
            <span className={`text-xs transition-colors ${
              item.done
                ? 'text-brand-muted line-through'
                : 'text-brand-silver group-hover:text-brand-text'
            }`}>
              {item.label}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [emailStatus, setEmailStatus] = useState(null) // null | 'sending' | 'sent' | 'error'

  const handleEmailPlan = async () => {
    setEmailStatus('sending')
    try {
      await triggerEmailPlan()
      setEmailStatus('sent')
      setTimeout(() => setEmailStatus(null), 4000)
    } catch {
      setEmailStatus('error')
      setTimeout(() => setEmailStatus(null), 4000)
    }
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside className="w-60 min-h-screen bg-brand-surface border-r border-brand-border flex flex-col shrink-0">

      {/* ── Logo ─────────────────────────────────────────────────────────── */}
      <div className="px-5 py-5 border-b border-brand-border flex items-center gap-3">
        <img
          src="/small-ogre.png"
          alt="Iron Skillet"
          className="w-11 h-11 rounded-full ring-2 ring-brand-border shrink-0"
        />
        <div className="min-w-0">
          <h1 className="text-brand-text text-sm font-black tracking-[0.12em] uppercase leading-tight">
            Iron Skillet
          </h1>
          <p className="text-brand-muted text-xs truncate mt-0.5">{user?.email}</p>
        </div>
      </div>

      {/* ── Nav links ─────────────────────────────────────────────────────── */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-brand-raised text-brand-text border-l-[3px] border-brand-fire pl-[9px]'
                  : 'text-brand-muted hover:bg-brand-raised/60 hover:text-brand-text border-l-[3px] border-transparent pl-[9px]'
              }`
            }
          >
            <span className="text-base w-5 text-center">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* ── Onboarding checklist ─────────────────────────────────────────── */}
      <OnboardingChecklist />

      {/* ── Bottom actions ────────────────────────────────────────────────── */}
      <div className="px-4 pb-5 border-t border-brand-border pt-4 space-y-2">
        {emailStatus === 'sending' && (
          <div className="mb-2">
            <img
              src="/ogre-cooking-loading.png"
              alt="Generating meal plan…"
              className="w-full rounded-xl shadow-forge opacity-90"
            />
            <p className="text-center text-xs text-brand-muted mt-2">
              Building your meal plan…
            </p>
          </div>
        )}
        <button
          onClick={handleEmailPlan}
          disabled={emailStatus === 'sending'}
          className="btn-fire w-full py-2.5 px-4 text-sm"
        >
          {emailStatus === 'sending' && '⏳ Sending…'}
          {emailStatus === 'sent'    && '✅ Plan sent!'}
          {emailStatus === 'error'   && '❌ Failed — try again'}
          {!emailStatus              && '🚀 Generate Email Plan'}
        </button>

        {user?.is_admin && (
          <p className="text-center text-xs text-brand-muted">Admin</p>
        )}

        <button
          onClick={handleLogout}
          className="w-full py-2 text-brand-muted text-xs hover:text-brand-silver transition-colors"
        >
          Sign out
        </button>
      </div>
    </aside>
  )
}
