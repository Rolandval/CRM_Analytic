import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'

export function AppLayout() {
  return (
    <div className="flex min-h-screen" style={{ backgroundColor: '#F1F3F8' }}>
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="max-w-[1440px] mx-auto px-7 py-7">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
