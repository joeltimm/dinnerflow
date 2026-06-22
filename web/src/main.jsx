import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import { ChefProvider } from './context/ChefContext'
import { OnboardingProvider } from './context/OnboardingContext'
import ErrorBoundary from './components/ErrorBoundary'
import './index.css'

// Optional Sentry — only loaded when VITE_SENTRY_DSN is set at build time, so it
// adds nothing to the bundle's critical path otherwise.
if (import.meta.env.VITE_SENTRY_DSN) {
  import('@sentry/react').then((Sentry) => {
    Sentry.init({
      dsn: import.meta.env.VITE_SENTRY_DSN,
      environment: import.meta.env.MODE,
    })
  })
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ErrorBoundary>
        <AuthProvider>
          <OnboardingProvider>
            <ChefProvider>
              <App />
            </ChefProvider>
          </OnboardingProvider>
        </AuthProvider>
      </ErrorBoundary>
    </BrowserRouter>
  </React.StrictMode>
)
