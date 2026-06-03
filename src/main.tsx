import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

const originalWarn = console.warn
const THREE_CLOCK_DEPRECATED_MSG = 'THREE.Clock: This module has been deprecated. Please use THREE.Timer instead.'
console.warn = (...args) => {
  const fullMsg = args.join(' ')
  if (fullMsg.includes(THREE_CLOCK_DEPRECATED_MSG)) {
    return
  }
  originalWarn.apply(console, args)
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
