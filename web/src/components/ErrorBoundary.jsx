import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="bg-white rounded-xl shadow p-10 max-w-md text-center">
            <p className="text-4xl mb-4">⚠️</p>
            <h2 className="text-xl font-bold text-gray-800 mb-2">Something went wrong</h2>
            <p className="text-gray-500 text-sm mb-6">{this.state.error.message}</p>
            <button
              onClick={() => this.setState({ error: null })}
              className="bg-amber-400 text-gray-900 px-6 py-2 rounded-lg font-semibold hover:bg-amber-300"
            >
              Try again
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
