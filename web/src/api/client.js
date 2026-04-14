/**
 * Axios API client.
 * - Base URL: /api (proxied to FastAPI backend via Vite in dev, nginx in prod)
 * - Credentials: 'include' so the session_token cookie is sent on every request
 * - 401 responses automatically redirect to /login
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,       // send/receive HTTP-only session cookie
  headers: { 'Content-Type': 'application/json' },
})

// Redirect to login on 401 (expired/missing session)
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (email, password) =>
  api.post('/auth/login', { email, password })

export const register = (email, password, full_name, email_consent = false) =>
  api.post('/auth/register', { email, password, full_name, email_consent })

export const logout = () => api.post('/auth/logout')

export const getMe = () => api.get('/auth/me')

// ── Recipes ───────────────────────────────────────────────────────────────────
export const listRecipes = () => api.get('/recipes')

export const getRecipe = (id) => api.get(`/recipes/${id}`)

export const createRecipe = (data) => api.post('/recipes', data)

export const updateRecipe = (id, data) => api.put(`/recipes/${id}`, data)

export const deleteRecipe = (id) => api.delete(`/recipes/${id}`)

export const logCook = (id, data) => api.post(`/recipes/${id}/cook`, data)

export const updateRating = (id, rating) =>
  api.put(`/recipes/${id}/rating`, { rating })

export const toggleFavorite = (id) => api.put(`/recipes/${id}/favorite`)

export const getRecipeHistory = (id) => api.get(`/recipes/${id}/history`)

export const uploadImage = (id, file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/recipes/${id}/image`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const importRecipeFromUrl = (url, title) =>
  api.post('/chef/cook', { url, title })

// ── Tonight ───────────────────────────────────────────────────────────────────
export const getTonightRecipes = () => api.get('/tonight')

// ── Chef ──────────────────────────────────────────────────────────────────────
export const getInstantIdeas = () => api.post('/chef/instant-ideas')

export const cookRecipe = (url, title) =>
  api.post('/chef/cook', { url, title })

export const triggerEmailPlan = () => api.post('/chef/email-plan')

// ── Settings ──────────────────────────────────────────────────────────────────
export const getPreferences = () => api.get('/settings/preferences')

export const updatePreferences = (dietary_preferences) =>
  api.put('/settings/preferences', { dietary_preferences })

export const getTodoist = () => api.get('/settings/todoist')

export const saveTodoistToken = (api_token) =>
  api.post('/settings/todoist', { api_token })

export const deleteTodoist = () => api.delete('/settings/todoist')

export const getTodoistProjects = () => api.get('/settings/todoist/projects')

export const selectTodoistProject = (project_id, project_name) =>
  api.put('/settings/todoist/project', { project_id, project_name })

export const createTodoistProject = (name) =>
  api.post('/settings/todoist/project', { name })

// ── Dashboard ─────────────────────────────────────────────────────────────────
export const getDashboard = () => api.get('/dashboard')

// ── Onboarding ────────────────────────────────────────────────────────────────
export const getOnboarding = () => api.get('/onboarding')

// ── Shopping list ─────────────────────────────────────────────────────────────
export const getShoppingList = () => api.get('/shopping')

export const addShoppingItem = (item_text, recipe_source = null) =>
  api.post('/shopping', { item_text, recipe_source })

export const toggleShoppingItem = (id) => api.put(`/shopping/${id}`)

export const deleteShoppingItem = (id) => api.delete(`/shopping/${id}`)

export const clearCheckedItems = () => api.delete('/shopping/checked')

// ── Account ───────────────────────────────────────────────────────────────────
export const getEmailPreferences = () => api.get('/account/email-preferences')

export const updateEmailPreferences = (email_consent) =>
  api.put('/account/email-preferences', { email_consent })

export const exportAccountData = () =>
  api.get('/account/export-data', { responseType: 'blob' })

export const deleteAccount = () =>
  api.delete('/account/delete', { data: { confirm: true } })

// ── Admin ─────────────────────────────────────────────────────────────────────
export const adminListUsers = () => api.get('/admin/users')

export const adminImpersonate = (user_id) =>
  api.post(`/admin/impersonate/${user_id}`)

export default api
