import { createContext, useContext, useState, useEffect, useRef } from 'react'
import { getInstantIdeas } from '../api/client'

const ChefContext = createContext(null)

const IDEAS_KEY     = 'instantChef_ideas'
const GENERATING_KEY = 'instantChef_generating'

export function ChefProvider({ children }) {
  const [ideas, setIdeas]         = useState(() => {
    try { return JSON.parse(localStorage.getItem(IDEAS_KEY)) || [] } catch { return [] }
  })
  const [generating, setGenerating] = useState(
    () => localStorage.getItem(GENERATING_KEY) === 'true'
  )
  const [error, setError]         = useState('')
  const fetchedRef                = useRef(false)

  // Sync to localStorage whenever values change
  useEffect(() => {
    localStorage.setItem(IDEAS_KEY, JSON.stringify(ideas))
  }, [ideas])

  useEffect(() => {
    localStorage.setItem(GENERATING_KEY, String(generating))
  }, [generating])

  // If the page was refreshed mid-generation (generating=true but no active fetch),
  // reset to a clean state so the user can try again.
  useEffect(() => {
    if (generating && !fetchedRef.current) {
      setGenerating(false)
      localStorage.removeItem(GENERATING_KEY)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const generate = async () => {
    fetchedRef.current = true
    setGenerating(true)
    setIdeas([])
    setError('')
    try {
      const res = await getInstantIdeas()
      setIdeas(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate ideas. Check LLM/Tavily config.')
    } finally {
      setGenerating(false)
      fetchedRef.current = false
    }
  }

  const clearIdeas = () => {
    setIdeas([])
    localStorage.removeItem(IDEAS_KEY)
  }

  return (
    <ChefContext.Provider value={{ ideas, generating, error, generate, clearIdeas }}>
      {children}
    </ChefContext.Provider>
  )
}

export function useChef() {
  return useContext(ChefContext)
}
