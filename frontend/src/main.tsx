import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// @ts-ignore: side-effect import of CSS module without type declarations
import './index.css'
import App from './App.js'

const element = document.getElementById('root')
if (!element) {
  throw new Error("Root element not found")
}

createRoot(element).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
