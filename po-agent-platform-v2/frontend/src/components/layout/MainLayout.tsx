import { Outlet, Link, useLocation } from 'react-router-dom'
import { AppShell } from './AppShell'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { SidebarItem } from './SidebarItem'

export function MainLayout() {
  const location = useLocation()
  const activeTab = location.pathname.replace('/', '') || 'assistant'

  const navItems = [
    { id: 'assistant', label: 'Обзор', path: '/' },
    { id: 'tasks', label: 'Задачи', path: '/tasks' },
    { id: 'sprint', label: 'Спринты', path: '/sprint' },
    { id: 'releases', label: 'Релизы', path: '/releases' },
    { id: 'team', label: 'Команда', path: '/team' },
    { id: 'quality', label: 'Аналитика', path: '/quality' },
    { id: 'history', label: 'История', path: '/history' },
  ]

  return (
    <AppShell
      sidebar={
        <Sidebar>
          {navItems.map((item) => (
            <Link key={item.id} to={item.path} style={{ textDecoration: 'none' }}>
              <SidebarItem
                label={item.label}
                active={activeTab === item.id || (activeTab === '' && item.id === 'assistant')}
              />
            </Link>
          ))}
        </Sidebar>
      }
      content={
        <div style={{ flex: 1 }}>
          <TopBar
            title="PO Workspace"
            subtitle="Пространство владельца продукта"
            rightContent={null}
          />
          <main>
            <Outlet />
          </main>
        </div>
      }
    />
  )
}
