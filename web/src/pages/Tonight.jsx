/**
 * Tonight page — smart recipe picker.
 * Shows a recipe from the least-recently-cooked pool.
 * User can re-roll or log that they cooked it.
 */
import { useEffect, useState, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { getTonightRecipes, logCook } from '../api/client'
import { useOnboarding } from '../context/OnboardingContext'
import { useAuth } from '../context/AuthContext'
import StarRating from '../components/StarRating'

export default function Tonight() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const { user } = useAuth()
  const { hasRecipes, refresh: refreshOnboarding } = useOnboarding()
  const [pool, setPool]       = useState([])
  const [current, setCurrent] = useState(null)
  const [rating, setRating]   = useState(3)
  const [notes, setNotes]     = useState('')
  const [logged, setLogged]   = useState(false)
  const [loading, setLoading] = useState(true)
  const [cooking, setCooking] = useState(false)

  const fetchPool = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getTonightRecipes()
      const recipes = res.data
      setPool(recipes)
      if (recipes.length) {
        setCurrent(recipes[Math.floor(Math.random() * recipes.length)])
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchPool() }, [fetchPool])

  const reroll = () => {
    if (!pool.length) return
    const others = pool.filter((r) => r.id !== current?.id)
    const next = others.length ? others : pool
    setCurrent(next[Math.floor(Math.random() * next.length)])
    setLogged(false)
    setRating(3)
    setNotes('')
  }

  const handleCook = async () => {
    if (!current) return
    setCooking(true)
    try {
      await logCook(current.id, { rating, notes })
      setLogged(true)
      refreshOnboarding()
    } finally {
      setCooking(false)
    }
  }

  if (loading) {
    return (
      <p className="text-brand-muted animate-pulse text-sm">Picking tonight's recipe…</p>
    )
  }

  if (!current) {
    const firstName = user?.full_name?.split(' ')[0] || 'Chef'
    return (
      <div className="max-w-2xl mx-auto py-8">
        {/* Welcome hero */}
        <div className="forge-card overflow-hidden">
          <div className="p-8 text-center">
            <img
              src="/small-ogre.png"
              alt="Iron Skillet"
              className="w-20 h-20 rounded-full ring-2 ring-brand-border mx-auto mb-5"
            />
            <h1 className="text-2xl font-black text-brand-text mb-2">
              Welcome to Iron Skillet, {firstName}!
            </h1>
            <p className="text-brand-silver text-sm max-w-md mx-auto mb-8">
              Your personal AI-powered dinner planner. Add some recipes and we'll
              pick what to cook tonight, track your history, and build meal plans for you.
            </p>

            {/* How it works */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
              {[
                { icon: '📚', title: 'Add recipes', desc: 'Import from any URL or enter manually' },
                { icon: '🌙', title: 'Get picked', desc: "We'll suggest what to cook tonight" },
                { icon: '📊', title: 'Track & plan', desc: 'Log cooks, get email meal plans' },
              ].map((step) => (
                <div key={step.icon} className="bg-brand-bg rounded-xl p-4">
                  <p className="text-2xl mb-2">{step.icon}</p>
                  <p className="text-sm font-bold text-brand-text">{step.title}</p>
                  <p className="text-xs text-brand-muted mt-1">{step.desc}</p>
                </div>
              ))}
            </div>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => navigate('/recipes')}
                className="btn-fire px-6 py-3 text-sm font-bold"
              >
                📚 Import Your First Recipe
              </button>
              <button
                onClick={() => navigate('/instant')}
                className="btn-steel px-6 py-3 text-sm font-bold"
              >
                ⚡ Try Instant Chef
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const ingredients  = Array.isArray(current.ingredients)  ? current.ingredients  : JSON.parse(current.ingredients  || '[]')
  const instructions = Array.isArray(current.instructions) ? current.instructions : JSON.parse(current.instructions || '[]')

  return (
    <div className="max-w-3xl mx-auto">

      {/* ── Todoist sync warning (passed via navigation state) ──────────── */}
      {state?.warning && (
        <div className="bg-yellow-900/20 border border-yellow-700/40 text-yellow-400 px-4 py-3 rounded-lg text-sm mb-4">
          {state.warning}
        </div>
      )}

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-black text-brand-text tracking-wide">🌙 Tonight</h1>
        {!logged && (
          <button
            onClick={reroll}
            className="btn-ghost px-4 py-2 text-sm font-medium"
          >
            🎲 Not tonight
          </button>
        )}
      </div>

      {/* ── Recipe card ─────────────────────────────────────────────────── */}
      <div className="forge-card overflow-hidden">
        {current.local_image_path && (
          <img
            src={current.local_image_path}
            alt={current.title}
            className="w-full h-56 object-cover opacity-90"
          />
        )}

        <div className="p-6">
          {/* Title row */}
          <div className="flex items-start justify-between gap-4 mb-5">
            <div>
              <h2 className="text-xl font-bold text-brand-text">{current.title}</h2>
              {current.source_url && (
                <a
                  href={current.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs text-brand-blue hover:text-brand-blue-light mt-1 inline-block transition-colors"
                >
                  View source ↗
                </a>
              )}
            </div>
            {current.is_favorite && (
              <span className="text-2xl text-brand-gold shrink-0" title="Favourite">⭐</span>
            )}
          </div>

          {/* Ingredients + instructions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {ingredients.length > 0 && (
              <div>
                <h3 className="text-xs font-bold text-brand-silver uppercase tracking-widest mb-3">
                  Ingredients
                </h3>
                <ul className="space-y-1.5">
                  {ingredients.map((ing, i) => (
                    <li key={i} className="text-sm text-brand-text flex gap-2">
                      <span className="text-brand-fire mt-0.5 shrink-0">▸</span>
                      <span>{ing}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {instructions.length > 0 && (
              <div>
                <h3 className="text-xs font-bold text-brand-silver uppercase tracking-widest mb-3">
                  Instructions
                </h3>
                <ol className="space-y-2">
                  {instructions.map((step, i) => (
                    <li key={i} className="text-sm text-brand-text flex gap-2">
                      <span className="font-black text-brand-fire shrink-0">{i + 1}.</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>

          {/* ── Cook log section ──────────────────────────────────────────── */}
          {!logged ? (
            <div className="mt-6 pt-6 border-t border-brand-border">
              <p className="text-xs font-bold text-brand-silver uppercase tracking-widest mb-3">
                Rate it
              </p>
              <StarRating value={rating} onChange={setRating} />
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Optional notes…"
                rows={2}
                className="forge-input mt-3 resize-none"
              />
              <button
                onClick={handleCook}
                disabled={cooking}
                className="btn-fire mt-3 px-6 py-2.5 text-sm"
              >
                {cooking ? '…' : '🔥 Cooked. Log it.'}
              </button>
            </div>
          ) : (
            <div className="mt-6 pt-6 border-t border-brand-border text-center">
              <p className="text-brand-green font-bold">✅ Cook logged!</p>
              <button
                onClick={() => { fetchPool(); setLogged(false) }}
                className="mt-2 text-sm text-brand-muted hover:text-brand-silver underline transition-colors"
              >
                Pick another recipe
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
