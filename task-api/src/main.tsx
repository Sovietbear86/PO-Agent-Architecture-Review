import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './components/App'
import './styles/global.css'

console.log('React rendering starting...')
try {
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  )
  console.log('React rendering complete')
} catch (error) {
  console.error('React rendering error:', error)
}
