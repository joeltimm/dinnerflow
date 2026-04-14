/**
 * OnboardingContext — tracks first-run checklist state.
 *
 * Fetches GET /api/onboarding once on mount.
 * Provides: { hasRecipes, hasDietaryPrefs, hasCooked, recipeCount, loading, refresh, dismissed, dismiss }
 *
 * Components call refresh() after actions that change checklist state
 * (e.g. adding a recipe, saving prefs, logging a cook).
 */
import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { getOnboarding } from '../api/client'

const OnboardingContext = createContext(null)

const DISMISS_KEY = 'onboarding_dismissed'

export function OnboardingProvider({ children }) {
  const [state, setState] = useState({
    hasRecipes: false,
    hasDietaryPrefs: false,
    hasCooked: false,
    recipeCount: 0,
    loading: true,
  })
  const [dismissed, setDismissed] = useState(
    () => localStorage.getItem(DISMISS_KEY) === 'true'
  )

  const fetch_ = useCallback(async () => {
    try {
      const res = await getOnboarding()
      setState({
        hasRecipes: res.data.has_recipes,
        hasDietaryPrefs: res.data.has_dietary_prefs,
        hasCooked: res.data.has_cooked,
        recipeCount: res.data.recipe_count,
        loading: false,
      })
    } catch {
      setState((s) => ({ ...s, loading: false }))
    }
  }, [])

  useEffect(() => { fetch_() }, [fetch_])

  const refresh = useCallback(() => fetch_(), [fetch_])

  const dismiss = useCallback(() => {
    setDismissed(true)
    localStorage.setItem(DISMISS_KEY, 'true')
  }, [])

  const allDone = state.hasRecipes && state.hasDietaryPrefs && state.hasCooked

  return (
    <OnboardingContext.Provider value={{ ...state, allDone, dismissed, dismiss, refresh }}>
      {children}
    </OnboardingContext.Provider>
  )
}

export function useOnboarding() {
  return useContext(OnboardingContext)
}
