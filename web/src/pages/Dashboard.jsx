/**
 * Dashboard page — analytics charts.
 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { getDashboard } from '../api/client'

function StatCard({ label, value, icon }) {
  return (
    <div className="forge-card p-5">
      <p className="text-2xl mb-2">{icon}</p>
      <p className="text-3xl font-black text-brand-text">{value}</p>
      <p className="text-xs text-brand-muted mt-1 uppercase tracking-wide font-medium">{label}</p>
    </div>
  )
}

function Chart({ title, data, dataKey, color }) {
  if (!data.length) return null
  return (
    <div className="forge-card p-5">
      <h3 className="font-bold text-brand-text mb-4 text-sm uppercase tracking-wide">{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#1e2d40" />
          <XAxis
            type="number"
            tick={{ fontSize: 11, fill: '#4a5e72' }}
            axisLine={{ stroke: '#1e2d40' }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="title"
            width={140}
            tick={{ fontSize: 11, fill: '#7a90a8' }}
            tickFormatter={(v) => v.length > 20 ? v.slice(0, 20) + '…' : v}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              background: '#131920',
              border: '1px solid #1e2d40',
              color: '#c8d6e8',
            }}
            cursor={{ fill: '#1a2338' }}
          />
          <Bar dataKey={dataKey} fill={color} radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard().then((r) => {
      setData(r.data)
      setLoading(false)
    })
  }, [])

  if (loading) {
    return <p className="text-brand-muted animate-pulse text-sm">Loading dashboard…</p>
  }

  const isEmpty = data.total_recipes === 0 && data.total_cooked === 0

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-black text-brand-text tracking-wide mb-6">📊 Dashboard</h1>

      {isEmpty ? (
        <div className="forge-card p-8 text-center max-w-lg mx-auto">
          <p className="text-4xl mb-4">📊</p>
          <p className="text-brand-text font-bold mb-2">Your stats will show up here</p>
          <p className="text-sm text-brand-muted mb-6">
            Once you add recipes and start cooking, you'll see charts
            of your most-cooked meals, top-rated dishes, and cooking history.
          </p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => navigate('/recipes')} className="btn-fire px-5 py-2.5 text-sm">
              📚 Add recipes
            </button>
            <button onClick={() => navigate('/instant')} className="btn-steel px-5 py-2.5 text-sm">
              ⚡ Try Instant Chef
            </button>
          </div>
        </div>
      ) : (
        <>

      {/* ── Stats ───────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        <StatCard label="Recipes saved" value={data.total_recipes} icon="📚" />
        <StatCard label="Total cooks"   value={data.total_cooked}  icon="🍳" />
        <StatCard label="Favourites" value={data.total_favorites} icon="⭐" />
      </div>

      {/* ── Charts ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <Chart title="🔥 Most Cooked"   data={data.most_cooked}    dataKey="times_cooked" color="#d95f0e" />
        <Chart title="⭐ Highest Rated" data={data.highest_rated}  dataKey="rating"        color="#1d6fa4" />
      </div>

      {/* ── Recent log ──────────────────────────────────────────────────── */}
      {data.recent_log.length > 0 && (
        <div className="forge-card p-5">
          <h3 className="font-bold text-brand-text text-sm uppercase tracking-wide mb-4">
            Recent Cooks
          </h3>
          <div className="space-y-0">
            {data.recent_log.map((entry, i) => (
              <div
                key={i}
                className="flex items-center justify-between py-3 border-b border-brand-border last:border-0"
              >
                <div>
                  <p className="text-sm font-medium text-brand-text">{entry.title}</p>
                  <p className="text-xs text-brand-muted">
                    {new Date(entry.date_cooked).toLocaleDateString()}
                  </p>
                </div>
                {entry.rating && (
                  <span className="text-brand-gold text-sm">
                    {'★'.repeat(entry.rating)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

        </>
      )}
    </div>
  )
}
