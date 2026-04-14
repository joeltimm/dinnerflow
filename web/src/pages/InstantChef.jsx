/**
 * Instant Chef page.
 *
 * 1. "Generate Ideas" → POST /api/chef/instant-ideas (LLM + Tavily)
 * 2. User picks one idea
 * 3. "Cook This" → POST /api/chef/cook (scrape + extract + save to DB)
 * 4. Redirect to Tonight
 *
 * Generation state lives in ChefContext so navigating away and back
 * preserves both the loading indicator and the returned ideas.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { cookRecipe } from '../api/client'
import { useChef } from '../context/ChefContext'
import OgreLoading from '../components/OgreLoading'

export default function InstantChef() {
  const navigate = useNavigate()
  const { ideas, generating, error, generate, clearIdeas } = useChef()
  const [selected, setSelected] = useState(null)
  const [cooking, setCooking]   = useState(false)
  const [cookError, setCookError] = useState('')

  const cook = async () => {
    if (!selected) return
    setCooking(true)
    setCookError('')
    try {
      const res = await cookRecipe(selected.url, selected.title)
      clearIdeas()
      if (res.data?.todoist_error) {
        navigate('/tonight', { state: { warning: 'Recipe saved, but Todoist sync failed. Check your integration in Settings.' } })
      } else {
        navigate('/tonight')
      }
    } catch (err) {
      setCookError(err.response?.data?.detail || 'Failed to fetch/parse recipe.')
    } finally {
      setCooking(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto">

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-black text-brand-text tracking-wide">⚡ Instant Chef</h1>
        <button
          onClick={generate}
          disabled={generating}
          className="btn-fire px-5 py-2.5 text-sm"
        >
          {generating ? '⏳ Generating…' : '✨ Generate Ideas'}
        </button>
      </div>

      {/* ── Generating state ────────────────────────────────────────────── */}
      {generating && (
        <OgreLoading
          message="Consulting the ancient recipe tomes…"
          hint="This can take a few minutes — feel free to check back shortly"
        />
      )}

      {/* ── Error ───────────────────────────────────────────────────────── */}
      {error && (
        <div className="bg-red-900/20 border border-red-800/40 text-red-400 px-4 py-3 rounded-lg text-sm mb-4">
          {error}
        </div>
      )}

      {/* ── Idea list ───────────────────────────────────────────────────── */}
      {!generating && ideas.length > 0 && (
        <>
          <p className="text-sm text-brand-muted mb-4">
            Select a recipe, then click <span className="text-brand-text font-semibold">Cook This</span>.
          </p>

          <div className="space-y-2 mb-6">
            {ideas.map((idea, i) => {
              const isSelected = selected?.title === idea.title
              return (
                <div
                  key={i}
                  onClick={() => setSelected(idea)}
                  className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-brand-fire bg-brand-fire/5'
                      : 'border-brand-border bg-brand-surface hover:border-brand-blue/50 hover:bg-brand-raised/50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {/* Radio dot */}
                    <div className={`w-4 h-4 rounded-full border-2 mt-0.5 shrink-0 flex items-center justify-center ${
                      isSelected ? 'border-brand-fire bg-brand-fire' : 'border-brand-border'
                    }`}>
                      {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-brand-text text-sm">{idea.title}</p>
                      {idea.description && (
                        <p className="text-xs text-brand-muted mt-0.5 line-clamp-2">{idea.description}</p>
                      )}
                      {idea.url && (
                        <a
                          href={idea.url}
                          target="_blank"
                          rel="noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-xs text-brand-blue hover:text-brand-blue-light mt-1 inline-block transition-colors"
                        >
                          Preview recipe ↗
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* ── Cook loading / sticky button ──────────────────────────────── */}
          {selected && (
            <div>
              {cooking && (
                <OgreLoading
                  message={`Extracting recipe: ${selected.title}`}
                  hint="Scraping and parsing with AI… up to 90 seconds"
                />
              )}
              <div className="sticky bottom-4">
                <button
                  onClick={cook}
                  disabled={cooking || !selected.url}
                  className="btn-fire w-full py-3.5 text-sm shadow-forge-lg"
                >
                  {cooking
                    ? '⏳ Fetching & parsing recipe…'
                    : !selected.url
                    ? '⚠️ No URL — pick another'
                    : `🍳 Cook: ${selected.title}`}
                </button>
                {cookError && (
                  <p className="text-red-400 text-sm mt-2 text-center">{cookError}</p>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {/* ── Empty state ─────────────────────────────────────────────────── */}
      {!generating && ideas.length === 0 && !error && (
        <div className="text-center py-16 text-brand-muted max-w-md mx-auto">
          <p className="text-3xl mb-4">⚡</p>
          <p className="font-semibold text-brand-silver mb-2">AI-powered dinner ideas</p>
          <p className="text-sm mb-4">
            Hit <span className="text-brand-text font-semibold">Generate Ideas</span> and the AI
            will search the web for recipes tailored to your tastes. No setup
            required — it works right away and gets smarter as you add favourites
            and dietary preferences.
          </p>
          <p className="text-xs text-brand-muted">
            Tip: set your{' '}
            <a href="/settings" className="text-brand-blue hover:text-brand-blue-light underline transition-colors">
              dietary preferences
            </a>{' '}
            for more personalised suggestions.
          </p>
        </div>
      )}
    </div>
  )
}
