import { useState } from 'react'

export default function StarRating({ value, onChange }) {
  const [hovered, setHovered] = useState(null)
  return (
    <div className="flex gap-1 star-rating">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => onChange(star)}
          onMouseEnter={() => setHovered(star)}
          onMouseLeave={() => setHovered(null)}
        >
          {star <= (hovered ?? Math.round(value ?? 0)) ? '★' : '☆'}
        </button>
      ))}
    </div>
  )
}
