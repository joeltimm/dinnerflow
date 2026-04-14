import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [form, setForm] = useState({ email: '', password: '', full_name: '', email_consent: false })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (field) => (e) =>
    setForm({ ...form, [field]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(form.email, form.password)
      } else {
        await register(form.email, form.password, form.full_name, form.email_consent)
      }
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-brand-bg flex items-center justify-center p-4">
      <div className="w-full max-w-sm">

        {/* ── Hero ──────────────────────────────────────────────────────── */}
        <div className="text-center mb-8">
          <img
            src="/small-ogre.png"
            alt="Iron Skillet"
            className="w-24 h-24 mx-auto mb-5 rounded-full ring-4 ring-brand-border drop-shadow-2xl"
          />
          <h1 className="text-brand-text text-3xl font-black tracking-[0.15em] uppercase">
            Iron Skillet
          </h1>
          <p className="text-brand-muted text-sm mt-1 tracking-wide">
            Self-hosted AI meal planning
          </p>
        </div>

        {/* ── Card ──────────────────────────────────────────────────────── */}
        <div className="forge-card p-7">

          {/* Tab switcher */}
          <div className="flex rounded-lg bg-brand-bg border border-brand-border p-1 mb-6">
            {['login', 'register'].map((m) => (
              <button
                key={m}
                onClick={() => { setMode(m); setError('') }}
                className={`flex-1 py-2 text-sm font-semibold rounded-md transition-colors capitalize ${
                  mode === m
                    ? 'bg-brand-raised text-brand-text shadow'
                    : 'text-brand-muted hover:text-brand-silver'
                }`}
              >
                {m === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="block text-xs font-semibold text-brand-silver mb-1.5 uppercase tracking-wide">
                  Full Name
                </label>
                <input
                  type="text"
                  value={form.full_name}
                  onChange={set('full_name')}
                  required
                  className="forge-input"
                  placeholder="Julia Child"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-brand-silver mb-1.5 uppercase tracking-wide">
                Email
              </label>
              <input
                type="email"
                value={form.email}
                onChange={set('email')}
                required
                className="forge-input"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-brand-silver mb-1.5 uppercase tracking-wide">
                Password
              </label>
              <input
                type="password"
                value={form.password}
                onChange={set('password')}
                required
                minLength={6}
                className="forge-input"
                placeholder="••••••••"
              />
            </div>

            {mode === 'register' && (
              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.email_consent}
                  onChange={set('email_consent')}
                  className="mt-0.5 accent-brand-gold"
                />
                <span className="text-xs text-brand-silver leading-relaxed">
                  Send me weekly meal plan emails with AI-powered recipe ideas.
                  You can unsubscribe anytime.
                </span>
              </label>
            )}

            {error && (
              <p className="text-red-400 text-sm bg-red-900/20 border border-red-800/40 px-4 py-2.5 rounded-lg">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-fire w-full py-3 text-sm mt-2"
            >
              {loading ? '…' : mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          {mode === 'register' && (
            <p className="text-center text-xs text-brand-muted mt-4">
              By creating an account you agree to our{' '}
              <a href="/privacy" target="_blank" className="text-brand-silver underline hover:text-brand-text transition-colors">
                privacy policy
              </a>.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
