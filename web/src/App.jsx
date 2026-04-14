import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Tonight from './pages/Tonight'
import Recipes from './pages/Recipes'
import InstantChef from './pages/InstantChef'
import ShoppingList from './pages/ShoppingList'
import Dashboard from './pages/Dashboard'
import Settings from './pages/Settings'

function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<Login />} />

      {/* Protected — all wrapped in Layout (sidebar) */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/tonight" replace />} />
                <Route path="/tonight" element={<Tonight />} />
                <Route path="/recipes" element={<Recipes />} />
                <Route path="/instant" element={<InstantChef />} />
                <Route path="/shopping" element={<ShoppingList />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
