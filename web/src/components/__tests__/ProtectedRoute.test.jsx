import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ProtectedRoute from '../ProtectedRoute'

// Stub Navigate so we can assert a redirect without a Router.
vi.mock('react-router-dom', () => ({
  Navigate: ({ to }) => <div>redirected to {to}</div>,
}))

let mockAuth
vi.mock('../../context/AuthContext', () => ({ useAuth: () => mockAuth }))

describe('ProtectedRoute', () => {
  it('shows a loading state while auth resolves', () => {
    mockAuth = { user: null, loading: true }
    render(<ProtectedRoute><div>secret</div></ProtectedRoute>)
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('redirects to /login when unauthenticated', () => {
    mockAuth = { user: null, loading: false }
    render(<ProtectedRoute><div>secret</div></ProtectedRoute>)
    expect(screen.getByText(/redirected to \/login/i)).toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    mockAuth = { user: { id: 1 }, loading: false }
    render(<ProtectedRoute><div>secret</div></ProtectedRoute>)
    expect(screen.getByText('secret')).toBeInTheDocument()
  })
})
