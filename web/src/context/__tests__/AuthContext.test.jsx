import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { AuthProvider, useAuth } from '../AuthContext'

vi.mock('../../api/client', () => ({
  getMe: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
}))
import { getMe } from '../../api/client'

function Consumer() {
  const { user, loading } = useAuth()
  if (loading) return <div>loading</div>
  return <div>{user ? user.email : 'anon'}</div>
}

describe('AuthContext', () => {
  it('restores the session from getMe on mount', async () => {
    getMe.mockResolvedValue({ data: { id: 1, email: 'me@example.com' } })
    render(<AuthProvider><Consumer /></AuthProvider>)
    await waitFor(() => expect(screen.getByText('me@example.com')).toBeInTheDocument())
  })

  it('falls back to anonymous when there is no valid session', async () => {
    getMe.mockRejectedValue(new Error('401'))
    render(<AuthProvider><Consumer /></AuthProvider>)
    await waitFor(() => expect(screen.getByText('anon')).toBeInTheDocument())
  })
})
