import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/** Wraps a route so unauthenticated users are sent to /login. */
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-brand-bg">
        <span className="text-brand-silver text-xl animate-pulse">Loading…</span>
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />

  return children
}
