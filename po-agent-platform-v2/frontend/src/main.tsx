import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout'
import { AssistantView } from './views/AssistantView'
import { TasksView } from './views/TasksView'
import { SprintView } from './views/SprintView'
import { TeamView } from './views/TeamView'
import { ReleasesView } from './views/ReleasesView'
import { QualityView } from './views/QualityView'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<AssistantView />} />
          <Route path="tasks" element={<TasksView />} />
          <Route path="sprint" element={<SprintView />} />
          <Route path="team" element={<TeamView />} />
          <Route path="releases" element={<ReleasesView />} />
          <Route path="quality" element={<QualityView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

const root = document.getElementById('root')
if (root) {
  createRoot(root).render(<App />)
}
