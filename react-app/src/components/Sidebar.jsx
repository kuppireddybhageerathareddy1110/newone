import React from 'react'

const NAV_ITEMS = [
  { sec: 'predict', icon: 'fa-stethoscope', label: 'Assessment' },
  { sec: 'explain', icon: 'fa-microscope', label: 'XAI' },
  { sec: 'batch', icon: 'fa-table', label: 'Batch' },
  { sec: 'history', icon: 'fa-clock-rotate-left', label: 'History' },
  { sec: 'insights', icon: 'fa-notes-medical', label: 'Insights' },
  { sec: 'about', icon: 'fa-flask', label: 'Model Details' },
]

export default function Sidebar({ activeSection, onNavigate }) {
  return (
    <aside className="sb">
      <div className="brand">
        <span className="brand-icon">CardioAI</span>
        <span className="brand-name">
          Hybrid<span className="model-badge">v4.1</span>
        </span>
      </div>

      <nav className="sidenav">
        {NAV_ITEMS.map(({ sec, icon, label }) => (
          <button
            key={sec}
            className={`nav-item${activeSection === sec ? ' active' : ''}`}
            onClick={() => onNavigate(sec)}
          >
            <i className={`fas ${icon}`} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="sb-footer">
        <p>Stacked Hybrid · XGB + DL + Meta-LR</p>
        <p className="warn">Research use only</p>
      </div>
    </aside>
  )
}
