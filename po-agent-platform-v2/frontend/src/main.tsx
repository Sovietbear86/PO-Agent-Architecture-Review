import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { WorkspaceApp } from './recovery/WorkspaceApp'
import {
  ReleasesPage,
  SprintPage,
  TasksPage,
} from './recovery/Pages'
import { OverviewDashboard } from './recovery/OverviewDashboard'
import { QualityDashboard } from './recovery/QualityDashboard'
import { TeamDashboard } from './recovery/TeamDashboard'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WorkspaceApp />}>
          <Route index element={<OverviewDashboard />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="sprint" element={<SprintPage />} />
          <Route path="releases" element={<ReleasesPage />} />
          <Route path="team" element={<TeamDashboard />} />
          <Route path="quality" element={<QualityDashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

const root = document.getElementById('root')
if (root) createRoot(root).render(<App />)
