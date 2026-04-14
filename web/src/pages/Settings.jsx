/**
 * Settings page — dietary preferences + Todoist integration.
 */
import { useEffect, useState } from 'react'
import {
  getPreferences, updatePreferences,
  getTodoist, saveTodoistToken, deleteTodoist,
  getTodoistProjects, selectTodoistProject, createTodoistProject,
  getEmailPreferences, updateEmailPreferences,
  exportAccountData, deleteAccount,
} from '../api/client'
import { useOnboarding } from '../context/OnboardingContext'
import { useAuth } from '../context/AuthContext'

export default function Settings() {
  const { refresh: refreshOnboarding } = useOnboarding()
  const { logout } = useAuth()

  // ── Preferences ─────────────────────────────────────────────────────────────
  const [prefs, setPrefs]           = useState('')
  const [prefsSaved, setPrefsSaved] = useState(false)
  const [prefsLoading, setPrefsLoading] = useState(true)

  useEffect(() => {
    getPreferences().then((r) => {
      setPrefs(r.data.dietary_preferences || '')
      setPrefsLoading(false)
    })
  }, [])

  const savePrefs = async () => {
    await updatePreferences(prefs)
    setPrefsSaved(true)
    refreshOnboarding()
    setTimeout(() => setPrefsSaved(false), 3000)
  }

  // ── Todoist ──────────────────────────────────────────────────────────────────
  const [todoist, setTodoist]               = useState(null)
  const [todoistLoading, setTodoistLoading] = useState(true)
  const [tokenInput, setTokenInput]         = useState('')
  const [tokenError, setTokenError]         = useState('')
  const [tokenSaving, setTokenSaving]       = useState(false)

  const [projects, setProjects]             = useState([])
  const [projectsLoading, setProjectsLoading] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [creatingProject, setCreatingProject] = useState(false)

  useEffect(() => {
    getTodoist()
      .then((r) => { setTodoist(r.data); setTodoistLoading(false) })
      .catch(() => { setTodoist({ connected: false }); setTodoistLoading(false) })
  }, [])

  useEffect(() => {
    if (todoist?.connected) {
      setProjectsLoading(true)
      getTodoistProjects()
        .then((r) => { setProjects(r.data); setProjectsLoading(false) })
        .catch(() => setProjectsLoading(false))
    }
  }, [todoist?.connected])

  const saveToken = async () => {
    setTokenError('')
    setTokenSaving(true)
    try {
      await saveTodoistToken(tokenInput)
      const r = await getTodoist()
      setTodoist(r.data)
      setTokenInput('')
    } catch (err) {
      setTokenError(err.response?.data?.detail || 'Invalid token')
    } finally {
      setTokenSaving(false)
    }
  }

  const disconnectTodoist = async () => {
    await deleteTodoist()
    setTodoist({ connected: false })
    setProjects([])
  }

  const selectProject = async (proj) => {
    await selectTodoistProject(proj.id, proj.name)
    setTodoist({ ...todoist, target_list_id: proj.id, target_list_name: proj.name })
  }

  const createProject = async () => {
    if (!newProjectName.trim()) return
    setCreatingProject(true)
    try {
      const r = await createTodoistProject(newProjectName.trim())
      setTodoist({ ...todoist, target_list_id: r.data.project_id, target_list_name: r.data.name })
      const pr = await getTodoistProjects()
      setProjects(pr.data)
      setNewProjectName('')
    } finally {
      setCreatingProject(false)
    }
  }

  // ── Email preferences ───────────────────────────────────────────────────────
  const [emailConsent, setEmailConsent] = useState(false)
  const [emailLoading, setEmailLoading] = useState(true)
  const [emailSaving, setEmailSaving]   = useState(false)

  useEffect(() => {
    getEmailPreferences()
      .then((r) => { setEmailConsent(r.data.email_consent); setEmailLoading(false) })
      .catch(() => setEmailLoading(false))
  }, [])

  const toggleEmailConsent = async () => {
    setEmailSaving(true)
    try {
      const next = !emailConsent
      await updateEmailPreferences(next)
      setEmailConsent(next)
    } finally {
      setEmailSaving(false)
    }
  }

  // ── Account actions ─────────────────────────────────────────────────────────
  const [exporting, setExporting]       = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting]         = useState(false)

  const handleExport = async () => {
    setExporting(true)
    try {
      const r = await exportAccountData()
      const blob = new Blob([r.data], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'ironskillet_data.json'
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setExporting(false)
    }
  }

  const handleDelete = async () => {
    setDeleting(true)
    try {
      await deleteAccount()
      logout()
    } catch {
      setDeleting(false)
      setShowDeleteConfirm(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-black text-brand-text tracking-wide mb-8">⚙️ Settings</h1>

      {/* ── Dietary Preferences ───────────────────────────────────────────── */}
      <section className="forge-card p-6 mb-4">
        <h2 className="font-bold text-brand-text text-sm uppercase tracking-widest mb-1">
          Dietary Preferences
        </h2>
        <p className="text-sm text-brand-muted mb-4">
          Shared with the AI when generating meal ideas and email plans.
        </p>

        {prefsLoading ? (
          <p className="text-brand-muted text-sm animate-pulse">Loading…</p>
        ) : (
          <>
            <textarea
              rows={4}
              value={prefs}
              onChange={(e) => setPrefs(e.target.value)}
              placeholder="e.g. vegetarian, nut-free, no shellfish, low-carb…"
              className="forge-input resize-none"
            />
            <button
              onClick={savePrefs}
              className="btn-steel mt-3 px-5 py-2 text-sm"
            >
              {prefsSaved ? '✅ Saved!' : 'Save Preferences'}
            </button>
          </>
        )}
      </section>

      {/* ── Todoist ───────────────────────────────────────────────────────── */}
      <section className="forge-card p-6">
        <div className="flex items-center gap-3 mb-1">
          <h2 className="font-bold text-brand-text text-sm uppercase tracking-widest">
            Todoist Integration
          </h2>
          <img src="/small-todoist.png" alt="Todoist" className="h-4 opacity-70" />
        </div>
        <p className="text-sm text-brand-muted mb-5">
          Automatically sync recipe ingredients to your grocery list when you cook via Instant Chef
          or select a recipe from your meal plan email.
        </p>

        {todoistLoading ? (
          <p className="text-brand-muted text-sm animate-pulse">Loading…</p>

        ) : !todoist?.connected ? (
          /* Not connected */
          <div>
            <p className="text-sm text-brand-silver mb-3">
              Find your API token at{' '}
              <a
                href="https://todoist.com/app/settings/integrations/developer"
                target="_blank"
                rel="noreferrer"
                className="text-brand-blue hover:text-brand-blue-light transition-colors"
              >
                Todoist → Settings → Integrations → Developer
              </a>
            </p>
            <input
              type="password"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              placeholder="Paste your Todoist API token"
              className="forge-input"
            />
            {tokenError && (
              <p className="text-red-400 text-sm mt-2">{tokenError}</p>
            )}
            <button
              onClick={saveToken}
              disabled={tokenSaving || !tokenInput}
              className="btn-steel mt-3 px-5 py-2 text-sm"
            >
              {tokenSaving ? '⏳ Verifying…' : 'Connect Todoist'}
            </button>
          </div>

        ) : (
          /* Connected */
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-brand-green">✅</span>
              <span className="text-sm font-medium text-brand-text">Todoist connected</span>
              <button
                onClick={disconnectTodoist}
                className="ml-auto text-xs text-red-500 hover:text-red-400 underline transition-colors"
              >
                Disconnect
              </button>
            </div>

            {/* Active project banner */}
            {todoist.target_list_name && (
              <div className="bg-brand-blue/10 border border-brand-blue/30 rounded-lg px-4 py-2.5 mb-4">
                <p className="text-sm text-brand-silver">
                  Active grocery list:{' '}
                  <strong className="text-brand-text">{todoist.target_list_name}</strong>
                </p>
              </div>
            )}

            {/* Project list */}
            {projectsLoading ? (
              <p className="text-brand-muted text-sm animate-pulse">Loading projects…</p>
            ) : (
              <div>
                <p className="text-xs font-bold text-brand-muted uppercase tracking-widest mb-2">
                  Select grocery list
                </p>
                <div className="space-y-1 max-h-48 overflow-y-auto mb-4">
                  {projects.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => selectProject(p)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        todoist.target_list_id === p.id
                          ? 'bg-brand-blue text-white font-semibold'
                          : 'bg-brand-raised text-brand-silver hover:bg-brand-border hover:text-brand-text'
                      }`}
                    >
                      {p.name}
                      {todoist.target_list_id === p.id && ' ✓'}
                    </button>
                  ))}
                </div>

                {/* Create new project */}
                <div className="flex gap-2">
                  <input
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    placeholder="New list name…"
                    className="forge-input"
                  />
                  <button
                    onClick={createProject}
                    disabled={creatingProject || !newProjectName.trim()}
                    className="btn-steel px-4 py-2 text-sm whitespace-nowrap"
                  >
                    {creatingProject ? '…' : '+ Create'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* ── Email Preferences ────────────────────────────────────────── */}
      <section className="forge-card p-6 mb-4">
        <h2 className="font-bold text-brand-text text-sm uppercase tracking-widest mb-1">
          Email Preferences
        </h2>
        <p className="text-sm text-brand-muted mb-4">
          Control which emails you receive from Iron Skillet.
        </p>

        {emailLoading ? (
          <p className="text-brand-muted text-sm animate-pulse">Loading...</p>
        ) : (
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={emailConsent}
              onChange={toggleEmailConsent}
              disabled={emailSaving}
              className="accent-brand-gold w-4 h-4"
            />
            <span className="text-sm text-brand-silver">
              Receive weekly meal plan emails (Tue &amp; Sat)
            </span>
            {emailSaving && <span className="text-brand-muted text-xs animate-pulse">Saving...</span>}
          </label>
        )}
      </section>

      {/* ── Account ──────────────────────────────────────────────────── */}
      <section className="forge-card p-6 mb-4">
        <h2 className="font-bold text-brand-text text-sm uppercase tracking-widest mb-1">
          Account
        </h2>
        <p className="text-sm text-brand-muted mb-5">
          Manage your data and account.
          See our <a href="/privacy" target="_blank" className="text-brand-blue hover:text-brand-blue-light underline transition-colors">privacy policy</a>.
        </p>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="btn-steel px-5 py-2 text-sm"
          >
            {exporting ? 'Exporting...' : 'Export My Data'}
          </button>

          {!showDeleteConfirm ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-5 py-2 text-sm rounded-lg border border-red-800/40 text-red-400
                         hover:bg-red-900/20 hover:text-red-300 transition-colors"
            >
              Delete Account
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-red-400 text-sm">Are you sure? This is permanent.</span>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-4 py-2 text-sm rounded-lg bg-red-700 text-white
                           hover:bg-red-600 transition-colors font-semibold"
              >
                {deleting ? 'Deleting...' : 'Yes, delete everything'}
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-sm text-brand-muted hover:text-brand-silver transition-colors"
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
