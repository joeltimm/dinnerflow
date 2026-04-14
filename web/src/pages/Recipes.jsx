/**
 * Recipes page — recipe vault with gallery, detail view, add, and edit.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  listRecipes, getRecipe, createRecipe, updateRecipe, deleteRecipe,
  updateRating, toggleFavorite, uploadImage, getRecipeHistory,
  importRecipeFromUrl,
} from '../api/client'
import { useOnboarding } from '../context/OnboardingContext'
import RecipeCard from '../components/RecipeCard'
import StarRating from '../components/StarRating'

// ── URL import form ───────────────────────────────────────────────────────────
function UrlImportForm({ onImported, onCancel }) {
  const [url, setUrl]       = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await importRecipeFromUrl(url)
      const { recipe_id, todoist_error } = res.data
      const full = await getRecipe(recipe_id)
      onImported(full.data, todoist_error)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch or parse recipe. Try a different URL.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div>
        <label className="block text-xs font-bold text-brand-silver uppercase tracking-widest mb-1.5">
          Recipe URL
        </label>
        <input
          required
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://cooking.nytimes.com/recipes/…"
          className="forge-input"
        />
        <p className="text-xs text-brand-muted mt-1.5">
          The AI will scrape and extract the recipe automatically.
        </p>
      </div>
      {loading && (
        <p className="text-sm text-brand-muted animate-pulse">
          Fetching and extracting recipe — this can take up to 90 seconds…
        </p>
      )}
      {error && (
        <p className="text-red-400 text-sm bg-red-900/20 border border-red-800/40 px-4 py-2.5 rounded-lg">
          {error}
        </p>
      )}
      <div className="flex gap-3 pt-2">
        <button type="submit" disabled={loading} className="btn-fire px-6 py-2.5 text-sm">
          {loading ? '⏳ Extracting…' : '⚡ Import Recipe'}
        </button>
        <button type="button" onClick={onCancel}
          className="px-4 py-2 text-sm text-brand-muted hover:text-brand-silver transition-colors">
          Cancel
        </button>
      </div>
    </form>
  )
}

// ── Add / Edit form ───────────────────────────────────────────────────────────
function RecipeForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState({
    title: initial?.title || '',
    source_url: initial?.source_url || '',
    ingredients: Array.isArray(initial?.ingredients)
      ? initial.ingredients.join('\n')
      : (JSON.parse(initial?.ingredients || '[]')).join('\n'),
    instructions: Array.isArray(initial?.instructions)
      ? initial.instructions.join('\n')
      : (JSON.parse(initial?.instructions || '[]')).join('\n'),
  })
  const [imageFile, setImageFile] = useState(null)
  const [saving, setSaving]       = useState(false)
  const [error, setError]         = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      const payload = {
        title: form.title,
        source_url: form.source_url || null,
        ingredients:  form.ingredients.split('\n').map((s) => s.trim()).filter(Boolean),
        instructions: form.instructions.split('\n').map((s) => s.trim()).filter(Boolean),
      }
      await onSave(payload, imageFile)
    } catch (err) {
      setError(err.response?.data?.detail || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div>
        <label className="block text-xs font-bold text-brand-silver uppercase tracking-widest mb-1.5">
          Title *
        </label>
        <input required className="forge-input" value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })} />
      </div>
      <div>
        <label className="block text-xs font-bold text-brand-silver uppercase tracking-widest mb-1.5">
          Source URL
        </label>
        <input className="forge-input" value={form.source_url}
          onChange={(e) => setForm({ ...form, source_url: e.target.value })}
          placeholder="https://…" />
      </div>
      <div>
        <label className="block text-xs font-bold text-brand-silver uppercase tracking-widest mb-1.5">
          Ingredients <span className="text-brand-muted normal-case font-normal">(one per line)</span>
        </label>
        <textarea rows={6} className="forge-input resize-none" value={form.ingredients}
          onChange={(e) => setForm({ ...form, ingredients: e.target.value })} />
      </div>
      <div>
        <label className="block text-xs font-bold text-brand-silver uppercase tracking-widest mb-1.5">
          Instructions <span className="text-brand-muted normal-case font-normal">(one per line)</span>
        </label>
        <textarea rows={6} className="forge-input resize-none" value={form.instructions}
          onChange={(e) => setForm({ ...form, instructions: e.target.value })} />
      </div>
      <div>
        <label className="block text-xs font-bold text-brand-silver uppercase tracking-widest mb-1.5">
          Image
        </label>
        <input type="file" accept="image/*"
          onChange={(e) => setImageFile(e.target.files[0])}
          className="text-sm text-brand-muted
                     file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0
                     file:text-sm file:font-bold file:bg-brand-raised file:text-brand-silver
                     hover:file:text-brand-text" />
      </div>
      {error && (
        <p className="text-red-400 text-sm bg-red-900/20 border border-red-800/40 px-4 py-2.5 rounded-lg">
          {error}
        </p>
      )}
      <div className="flex gap-3 pt-2">
        <button type="submit" disabled={saving} className="btn-fire px-6 py-2.5 text-sm">
          {saving ? '…' : initial ? 'Save Changes' : 'Add Recipe'}
        </button>
        <button type="button" onClick={onCancel}
          className="px-4 py-2 text-sm text-brand-muted hover:text-brand-silver transition-colors">
          Cancel
        </button>
      </div>
    </form>
  )
}

// ── Detail view ───────────────────────────────────────────────────────────────
function RecipeDetail({ recipe: initial, onClose, onUpdate }) {
  const [recipe, setRecipe]             = useState(initial)
  const [editing, setEditing]           = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [history, setHistory]           = useState(null)

  useEffect(() => {
    getRecipeHistory(initial.id).then((r) => setHistory(r.data))
  }, [initial.id])

  const ingredients  = Array.isArray(recipe.ingredients)  ? recipe.ingredients  : JSON.parse(recipe.ingredients  || '[]')
  const instructions = Array.isArray(recipe.instructions) ? recipe.instructions : JSON.parse(recipe.instructions || '[]')

  const handleRating = async (r) => {
    await updateRating(recipe.id, r)
    const updated = { ...recipe, rating: r }
    setRecipe(updated)
    onUpdate(updated)
  }

  const handleFavorite = async () => {
    const res = await toggleFavorite(recipe.id)
    const updated = { ...recipe, is_favorite: res.data.is_favorite }
    setRecipe(updated)
    onUpdate(updated)
  }

  const handleDelete = async () => {
    await deleteRecipe(recipe.id)
    onClose(recipe.id)
  }

  const handleEditSave = async (payload, imageFile) => {
    const res = await updateRecipe(recipe.id, payload)
    let updated = res.data
    if (imageFile) {
      const imgRes = await uploadImage(recipe.id, imageFile)
      updated = { ...updated, local_image_path: imgRes.data.image_path }
    }
    setRecipe(updated)
    onUpdate(updated)
    setEditing(false)
  }

  if (editing) {
    return (
      <div className="max-w-2xl">
        <button onClick={() => setEditing(false)}
          className="text-sm text-brand-muted mb-4 hover:text-brand-silver transition-colors">
          ← Back
        </button>
        <h2 className="text-xl font-black text-brand-text mb-4">Edit Recipe</h2>
        <RecipeForm initial={recipe} onSave={handleEditSave} onCancel={() => setEditing(false)} />
      </div>
    )
  }

  return (
    <div className="max-w-2xl">
      <button onClick={() => onClose(null)}
        className="text-sm text-brand-muted mb-4 hover:text-brand-silver transition-colors">
        ← Back to recipes
      </button>

      <div className="forge-card overflow-hidden">
        {recipe.local_image_path && (
          <img src={recipe.local_image_path} alt={recipe.title}
            className="w-full h-64 object-cover opacity-90" />
        )}

        <div className="p-6">
          {/* Title row */}
          <div className="flex items-start justify-between gap-4 mb-2">
            <h2 className="text-2xl font-black text-brand-text">{recipe.title}</h2>
            <button onClick={handleFavorite}
              className="text-2xl hover:scale-110 transition-transform shrink-0"
              title="Toggle favourite">
              {recipe.is_favorite
                ? <span className="text-brand-gold">⭐</span>
                : <span className="text-brand-border">☆</span>}
            </button>
          </div>

          {recipe.source_url && (
            <a href={recipe.source_url} target="_blank" rel="noreferrer"
              className="text-sm text-brand-blue hover:text-brand-blue-light mb-4 inline-block transition-colors">
              View source ↗
            </a>
          )}

          {/* Rating */}
          <div className="flex items-center gap-3 mb-6">
            <StarRating value={recipe.rating || 0} onChange={handleRating} />
            {recipe.rating > 0 && (
              <span className="text-sm text-brand-muted">{recipe.rating.toFixed(1)} / 5</span>
            )}
          </div>

          {/* Ingredients + instructions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {ingredients.length > 0 && (
              <div>
                <h3 className="text-xs font-bold text-brand-silver uppercase tracking-widest mb-3">
                  Ingredients
                </h3>
                <ul className="space-y-1.5">
                  {ingredients.map((ing, i) => (
                    <li key={i} className="text-sm text-brand-text flex gap-2">
                      <span className="text-brand-fire mt-0.5 shrink-0">▸</span>{ing}
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
                      <span className="font-black text-brand-fire shrink-0">{i + 1}.</span>{step}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-brand-border">
            <button onClick={() => setEditing(true)}
              className="btn-steel px-4 py-2 text-sm">
              ✏️ Edit
            </button>
            {!confirmDelete ? (
              <button onClick={() => setConfirmDelete(true)}
                className="px-4 py-2 text-sm text-red-500 border border-red-800/40 rounded-lg hover:bg-red-900/20 transition-colors">
                Delete
              </button>
            ) : (
              <div className="flex gap-2 items-center">
                <span className="text-sm text-red-400">Are you sure?</span>
                <button onClick={handleDelete}
                  className="px-3 py-1.5 text-xs font-bold bg-red-700 hover:bg-red-600 text-white rounded-lg transition-colors">
                  Yes, delete
                </button>
                <button onClick={() => setConfirmDelete(false)}
                  className="px-3 py-1.5 text-xs text-brand-muted hover:text-brand-silver transition-colors">
                  Cancel
                </button>
              </div>
            )}
          </div>

          {/* Cook history */}
          {history && history.length > 0 && (
            <div className="mt-6 pt-6 border-t border-brand-border">
              <h3 className="text-xs font-bold text-brand-silver uppercase tracking-widest mb-3">
                Cook History
              </h3>
              <div className="space-y-0">
                {history.map((entry) => (
                  <div key={entry.id} className="flex items-start justify-between py-2.5 border-b border-brand-border last:border-0">
                    <div>
                      <p className="text-xs text-brand-silver">
                        {new Date(entry.date_cooked).toLocaleDateString()}
                      </p>
                      {entry.notes && (
                        <p className="text-xs text-brand-muted mt-0.5 italic">"{entry.notes}"</p>
                      )}
                    </div>
                    {entry.rating && (
                      <span className="text-brand-gold text-xs shrink-0">
                        {'★'.repeat(entry.rating)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Starter recipe suggestions ───────────────────────────────────────────────
const STARTER_RECIPES = [
  { title: 'Classic Chicken Stir-Fry', url: 'https://www.allrecipes.com/recipe/228823/quick-chicken-stir-fry/' },
  { title: 'One-Pot Pasta Primavera', url: 'https://www.budgetbytes.com/pasta-primavera/' },
  { title: 'Sheet Pan Salmon & Veggies', url: 'https://www.wellplated.com/sheet-pan-salmon/' },
  { title: 'Easy Black Bean Tacos', url: 'https://cookieandkate.com/black-bean-tacos-recipe/' },
]

// ── Inline quick-import (shown in empty state) ──────────────────────────────
function QuickImport({ onImported }) {
  const [url, setUrl]       = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await importRecipeFromUrl(url)
      const { recipe_id, todoist_error } = res.data
      const full = await getRecipe(recipe_id)
      onImported(full.data, todoist_error)
      setUrl('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch or parse recipe. Try a different URL.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <form onSubmit={submit} className="flex gap-2">
        <input
          required
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste any recipe URL..."
          className="forge-input flex-1"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !url.trim()} className="btn-fire px-5 py-2.5 text-sm whitespace-nowrap">
          {loading ? '⏳ Importing...' : '⚡ Import'}
        </button>
      </form>
      {loading && (
        <p className="text-sm text-brand-muted animate-pulse mt-2">
          Fetching and extracting recipe...
        </p>
      )}
      {error && (
        <p className="text-red-400 text-xs bg-red-900/20 border border-red-800/40 px-3 py-2 rounded-lg mt-2">
          {error}
        </p>
      )}
    </div>
  )
}

// ── Starter recipe one-click import list ─────────────────────────────────────
function StarterList({ onImported }) {
  const [importing, setImporting] = useState(null) // title of recipe being imported
  const [error, setError]         = useState('')

  const importStarter = async (starter) => {
    setError('')
    setImporting(starter.title)
    try {
      const res = await importRecipeFromUrl(starter.url, starter.title)
      const { recipe_id, todoist_error } = res.data
      const full = await getRecipe(recipe_id)
      onImported(full.data, todoist_error)
    } catch (err) {
      setError(err.response?.data?.detail || `Failed to import "${starter.title}". Try another.`)
    } finally {
      setImporting(null)
    }
  }

  return (
    <div className="space-y-2">
      {STARTER_RECIPES.map((s) => (
        <button
          key={s.url}
          onClick={() => importStarter(s)}
          disabled={!!importing}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-brand-bg
                     hover:bg-brand-raised/60 border border-brand-border hover:border-brand-blue/40
                     transition-all text-left group"
        >
          <span className="text-brand-fire shrink-0">▸</span>
          <span className="flex-1 text-sm text-brand-text group-hover:text-brand-blue-light transition-colors">
            {s.title}
          </span>
          {importing === s.title ? (
            <span className="text-xs text-brand-muted animate-pulse">Importing...</span>
          ) : (
            <span className="text-xs text-brand-muted opacity-0 group-hover:opacity-100 transition-opacity">
              + Import
            </span>
          )}
        </button>
      ))}
      {error && (
        <p className="text-red-400 text-xs bg-red-900/20 border border-red-800/40 px-3 py-2 rounded-lg">
          {error}
        </p>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function Recipes() {
  const navigate = useNavigate()
  const { refresh: refreshOnboarding } = useOnboarding()
  const [recipes, setRecipes]   = useState([])
  const [view, setView]         = useState('gallery') // 'gallery' | 'detail' | 'add'
  const [addTab, setAddTab]     = useState('manual')  // 'manual' | 'url'
  const [selected, setSelected] = useState(null)
  const [search, setSearch]     = useState('')
  const [loading, setLoading]   = useState(true)
  const [importWarning, setImportWarning] = useState('')

  useEffect(() => {
    listRecipes().then((r) => {
      setRecipes(r.data)
      setLoading(false)
    })
  }, [])

  const handleAdd = async (payload, imageFile) => {
    const res = await createRecipe(payload)
    let newRecipe = res.data
    if (imageFile) {
      const imgRes = await uploadImage(newRecipe.id, imageFile)
      newRecipe = { ...newRecipe, local_image_path: imgRes.data.image_path }
    }
    setRecipes([newRecipe, ...recipes])
    setView('gallery')
    refreshOnboarding()
  }

  const handleImported = (recipe, todoistError) => {
    setRecipes([recipe, ...recipes])
    setView('gallery')
    if (todoistError) setImportWarning('Recipe saved, but Todoist sync failed. Check your integration in Settings.')
    else setImportWarning('')
    refreshOnboarding()
  }

  const handleClose = (deletedId) => {
    if (deletedId) setRecipes(recipes.filter((r) => r.id !== deletedId))
    setView('gallery')
    setSelected(null)
  }

  const handleUpdate = (updated) => {
    setRecipes(recipes.map((r) => (r.id === updated.id ? updated : r)))
  }

  const filtered = recipes.filter((r) =>
    r.title.toLowerCase().includes(search.toLowerCase())
  )

  if (view === 'detail' && selected) {
    return <RecipeDetail recipe={selected} onClose={handleClose} onUpdate={handleUpdate} />
  }

  if (view === 'add') {
    return (
      <div className="max-w-2xl">
        <button onClick={() => setView('gallery')}
          className="text-sm text-brand-muted mb-4 hover:text-brand-silver transition-colors">
          ← Back
        </button>
        <h2 className="text-xl font-black text-brand-text mb-4">Add Recipe</h2>

        {/* Tab switcher */}
        <div className="flex rounded-lg bg-brand-bg border border-brand-border p-1 mb-6">
          {[['manual', '✏️ Manual'], ['url', '⚡ Import from URL']].map(([tab, label]) => (
            <button
              key={tab}
              onClick={() => setAddTab(tab)}
              className={`flex-1 py-2 text-sm font-semibold rounded-md transition-colors ${
                addTab === tab
                  ? 'bg-brand-raised text-brand-text shadow'
                  : 'text-brand-muted hover:text-brand-silver'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {addTab === 'manual'
          ? <RecipeForm onSave={handleAdd} onCancel={() => setView('gallery')} />
          : <UrlImportForm onImported={handleImported} onCancel={() => setView('gallery')} />
        }
      </div>
    )
  }

  return (
    <div>
      {importWarning && (
        <div className="bg-yellow-900/20 border border-yellow-700/40 text-yellow-400 px-4 py-3 rounded-lg text-sm mb-4">
          {importWarning}
        </div>
      )}
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-black text-brand-text tracking-wide">📚 Recipes</h1>
        <button
          onClick={() => setView('add')}
          className="btn-fire px-4 py-2 text-sm"
        >
          + Add Recipe
        </button>
      </div>

      {/* Search */}
      <input
        type="text"
        placeholder="Search recipes…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="forge-input max-w-sm mb-6"
      />

      {loading ? (
        <p className="text-brand-muted animate-pulse text-sm">Loading recipes…</p>
      ) : filtered.length === 0 && search ? (
        <div className="text-center py-20 text-brand-muted">
          <p className="text-4xl mb-3">🔍</p>
          <p>No recipes match your search.</p>
        </div>
      ) : recipes.length === 0 ? (
        <div className="max-w-xl mx-auto">
          {/* Quick import */}
          <div className="forge-card p-6 mb-5">
            <h2 className="font-bold text-brand-text text-sm uppercase tracking-widest mb-1">
              Import from URL
            </h2>
            <p className="text-sm text-brand-muted mb-4">
              Paste any recipe URL and the AI will extract ingredients and instructions automatically.
            </p>
            <QuickImport onImported={handleImported} />
          </div>

          {/* Starter suggestions */}
          <div className="forge-card p-6 mb-5">
            <h2 className="font-bold text-brand-text text-sm uppercase tracking-widest mb-1">
              Quick starters
            </h2>
            <p className="text-sm text-brand-muted mb-4">
              Not sure where to begin? Import one of these popular recipes with a single click.
            </p>
            <StarterList onImported={handleImported} />
          </div>

          {/* Manual entry & Instant Chef */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              onClick={() => { setView('add'); setAddTab('manual') }}
              className="forge-card p-5 text-left hover:border-brand-blue/40 transition-colors group"
            >
              <p className="text-lg mb-1">✏️</p>
              <p className="text-sm font-bold text-brand-text group-hover:text-brand-blue-light transition-colors">
                Enter manually
              </p>
              <p className="text-xs text-brand-muted mt-1">
                Type in your own recipe from scratch.
              </p>
            </button>
            <button
              onClick={() => navigate('/instant')}
              className="forge-card p-5 text-left hover:border-brand-fire/40 transition-colors group"
            >
              <p className="text-lg mb-1">⚡</p>
              <p className="text-sm font-bold text-brand-text group-hover:text-brand-fire-light transition-colors">
                Try Instant Chef
              </p>
              <p className="text-xs text-brand-muted mt-1">
                Let the AI suggest dinner ideas for you.
              </p>
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          {filtered.map((r) => (
            <RecipeCard
              key={r.id}
              recipe={r}
              onClick={() => { setSelected(r); setView('detail') }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
