/**
 * Shopping list page — add, check off, and clear grocery items.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  getShoppingList, addShoppingItem, toggleShoppingItem,
  deleteShoppingItem, clearCheckedItems,
} from '../api/client'

export default function ShoppingList() {
  const navigate = useNavigate()
  const [items, setItems]       = useState([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(true)
  const [adding, setAdding]     = useState(false)

  useEffect(() => {
    getShoppingList().then((r) => {
      setItems(r.data)
      setLoading(false)
    })
  }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!input.trim()) return
    setAdding(true)
    try {
      const res = await addShoppingItem(input.trim())
      setItems([res.data, ...items])
      setInput('')
    } finally {
      setAdding(false)
    }
  }

  const handleToggle = async (id) => {
    const res = await toggleShoppingItem(id)
    setItems(items.map((i) => (i.id === id ? res.data : i)))
  }

  const handleDelete = async (id) => {
    await deleteShoppingItem(id)
    setItems(items.filter((i) => i.id !== id))
  }

  const handleClearChecked = async () => {
    await clearCheckedItems()
    setItems(items.filter((i) => !i.is_checked))
  }

  const unchecked = items.filter((i) => !i.is_checked)
  const checked   = items.filter((i) => i.is_checked)

  return (
    <div className="max-w-xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-black text-brand-text tracking-wide">🛒 Shopping List</h1>
        {checked.length > 0 && (
          <button
            onClick={handleClearChecked}
            className="text-xs text-red-500 hover:text-red-400 underline transition-colors"
          >
            Clear {checked.length} checked
          </button>
        )}
      </div>

      {/* Add item */}
      <form onSubmit={handleAdd} className="flex gap-2 mb-6">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Add an item…"
          className="forge-input flex-1"
        />
        <button
          type="submit"
          disabled={adding || !input.trim()}
          className="btn-fire px-4 py-2 text-sm whitespace-nowrap"
        >
          {adding ? '…' : '+ Add'}
        </button>
      </form>

      {loading ? (
        <p className="text-brand-muted animate-pulse text-sm">Loading…</p>
      ) : items.length === 0 ? (
        <div className="text-center py-20 text-brand-muted">
          <p className="text-4xl mb-3">🛒</p>
          <p className="mb-3">Your shopping list is empty.</p>
          <p className="text-sm">
            Add items above, or connect{' '}
            <button onClick={() => navigate('/settings')} className="text-brand-blue hover:text-brand-blue-light underline transition-colors">
              Todoist
            </button>{' '}
            to auto-sync ingredients when you cook.
          </p>
        </div>
      ) : (
        <div className="forge-card divide-y divide-brand-border">
          {/* Unchecked items */}
          {unchecked.map((item) => (
            <ItemRow key={item.id} item={item} onToggle={handleToggle} onDelete={handleDelete} />
          ))}

          {/* Checked items */}
          {checked.length > 0 && (
            <>
              {unchecked.length > 0 && (
                <div className="px-4 py-2 bg-brand-bg">
                  <p className="text-xs font-bold text-brand-muted uppercase tracking-widest">
                    Checked
                  </p>
                </div>
              )}
              {checked.map((item) => (
                <ItemRow key={item.id} item={item} onToggle={handleToggle} onDelete={handleDelete} />
              ))}
            </>
          )}
        </div>
      )}
    </div>
  )
}

function ItemRow({ item, onToggle, onDelete }) {
  return (
    <div className="flex items-center gap-3 px-4 py-3 group">
      <button
        onClick={() => onToggle(item.id)}
        className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${
          item.is_checked
            ? 'bg-brand-fire border-brand-fire text-white'
            : 'border-brand-border hover:border-brand-fire'
        }`}
      >
        {item.is_checked && <span className="text-xs font-black">✓</span>}
      </button>

      <div className="flex-1 min-w-0">
        <p className={`text-sm transition-colors ${
          item.is_checked ? 'line-through text-brand-muted' : 'text-brand-text'
        }`}>
          {item.item_text}
        </p>
        {item.recipe_source && (
          <p className="text-xs text-brand-muted truncate">{item.recipe_source}</p>
        )}
      </div>

      <button
        onClick={() => onDelete(item.id)}
        className="opacity-0 group-hover:opacity-100 text-brand-muted hover:text-red-400 transition-all text-xs px-1"
      >
        ✕
      </button>
    </div>
  )
}
