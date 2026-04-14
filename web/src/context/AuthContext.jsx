/**
 * AuthContext — global user state.
 *
 * On mount, calls GET /api/auth/me to restore the session from the cookie.
 * Provides: user, loading, login(), register(), logout()
 */
import { createContext, useContext, useEffect, useState } from 'react'
import { getMe, login as apiLogin, logout as apiLogout, register as apiRegister } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Restore session on page load
  useEffect(() => {
    getMe()
      .then((res) => setUser(res.data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password) => {
    const res = await apiLogin(email, password)
    setUser(res.data)
    return res.data
  }

  const register = async (email, password, full_name) => {
    const res = await apiRegister(email, password, full_name)
    setUser(res.data)
    return res.data
  }

  const logout = async () => {
    await apiLogout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
