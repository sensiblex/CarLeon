import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ApiKeyProvider } from './context/ApiKeyContext'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ApiKeyProvider>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ApiKeyProvider>
  </StrictMode>,
)
