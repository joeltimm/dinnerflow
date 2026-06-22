import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import StarRating from '../StarRating'

describe('StarRating', () => {
  it('renders five stars and reports the clicked value', async () => {
    const onChange = vi.fn()
    render(<StarRating value={3} onChange={onChange} />)
    const stars = screen.getAllByRole('button')
    expect(stars).toHaveLength(5)
    await userEvent.click(stars[4])
    expect(onChange).toHaveBeenCalledWith(5)
  })
})
