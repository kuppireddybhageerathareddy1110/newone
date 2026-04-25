import React from 'react'

export default function LoadingOverlay({ visible, message }) {
  return (
    <div className={`ov${visible ? ' on' : ''}`}>
      <div className="pulse">
        <div className="ring" />
        <i className="fas fa-heartbeat hbi" />
      </div>
      <p>{message || 'Analysing patient data...'}</p>
    </div>
  )
}
