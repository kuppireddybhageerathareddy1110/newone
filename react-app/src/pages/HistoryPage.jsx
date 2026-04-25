import React from 'react'

export default function HistoryPage({ history, onRestore, onClear }) {
  return (
    <section className="sec active">
      <div className="ph">
        <div>
          <h1>Assessment History</h1>
          <p>Recent locally saved cases from this browser session.</p>
        </div>
        {!!history.length && (
          <button className="sample-btn" onClick={onClear}>
            <i className="fas fa-trash" /> Clear History
          </button>
        )}
      </div>

      {!history.length ? (
        <div className="card empty-state">
          <p>No saved cases yet. Run an assessment to create a history entry.</p>
        </div>
      ) : (
        <div className="history-grid">
          {history.map(item => (
            <div className="card history-card" key={item.id}>
              <div className="ct">
                <i className="fas fa-clock-rotate-left" />
                {new Date(item.result.timestamp).toLocaleString()}
              </div>
              <div className="history-body">
                <div className={`history-badge ${(item.result.risk_level || '').toLowerCase()}`}>
                  {item.result.risk_level} risk
                </div>
                <p><strong>{item.result.prediction}</strong> at {(item.result.probability * 100).toFixed(1)}%</p>
                <p>Age {item.patient.age}, {item.patient.sex}, BP {item.patient.restingbp_final}, Chol {item.patient.chol_final}</p>
                <button className="cta primary" onClick={() => onRestore(item)}>
                  <i className="fas fa-arrow-rotate-left" /> Restore Case
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
