// main.jsx — React entry point + PWA service worker registration
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// Register service worker for PWA (vite-plugin-pwa handles generation)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    // vite-plugin-pwa auto-registers the SW; this is a fallback listener
    navigator.serviceWorker.ready.then(() => {
      console.log('BioChain-Opt PWA: Service Worker aktif ✅')
    })
  })
}
