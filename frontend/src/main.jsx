import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'

// Ensure compiled modules that reference `React` (without explicit import)
// have access to it on the global object. This helps avoid "React is not
// defined" errors from precompiled chunks during dev.
window.React = React

async function mount() {
  try {
    const { default: App } = await import('./App.jsx')
    ReactDOM.createRoot(document.getElementById('root')).render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    )
  } catch (err) {
    console.error('Failed to mount React app', err)
    const root = document.getElementById('root')
    if (root) {
      root.innerHTML = `<div style="font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial;padding:24px;color:#b91c1c"><h2>App failed to start</h2><pre style="white-space:pre-wrap;color:#111">${String(err)}</pre></div>`
    }
  }
}

mount()
