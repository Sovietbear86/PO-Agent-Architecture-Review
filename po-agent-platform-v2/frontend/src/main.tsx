import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { WorkspaceApp } from './recovery/WorkspaceApp'
import {
  OverviewPage,
  QualityPage,
  ReleasesPage,
  SprintPage,
  TasksPage,
  TeamPage,
} from './recovery/Pages'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WorkspaceApp />}>
          <Route index element={<OverviewPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="sprint" element={<SprintPage />} />
          <Route path="releases" element={<ReleasesPage />} />
          <Route path="team" element={<TeamPage />} />
          <Route path="quality" element={<QualityPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

const root = document.getElementById('root')
if (root) createRoot(root).render(<App />)
