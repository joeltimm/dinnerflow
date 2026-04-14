/** Shell layout: fixed sidebar + scrollable main content area. */
import Sidebar from './Sidebar'

export default function Layout({ children }) {
  return (
    <div className="flex min-h-screen bg-brand-bg">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8 min-w-0">
        {children}
      </main>
    </div>
  )
}
