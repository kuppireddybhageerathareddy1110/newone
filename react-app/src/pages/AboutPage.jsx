import React from 'react'

function MetricRow({ label, value }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value ?? 'Unavailable'}</dd>
    </>
  )
}

export default function AboutPage({ modelInfo }) {
  const metrics = modelInfo?.best_reported_metrics || {}
  const leaderboard = modelInfo?.leaderboard || []
  const artifacts = modelInfo?.artifacts || []

  return (
    <section className="sec active">
      <div className="ph">
        <div>
          <h1>Model Details</h1>
          <p>Live metadata from the backend rather than hardcoded project copy.</p>
        </div>
      </div>

      <div className="abg">
        <div className="card abc hybrid-card">
          <div className="ct"><i className="fas fa-layer-group" /> Architecture</div>
          <dl>
            <MetricRow label="Strategy" value={modelInfo?.architecture} />
            <MetricRow label="Base Models" value={modelInfo?.base_models?.join(' + ')} />
            <MetricRow label="Meta Learner" value={modelInfo?.meta_learner} />
            <MetricRow label="XAI Engine" value={modelInfo?.xai_engine} />
            <MetricRow label="Feature Count" value={modelInfo?.features} />
            <MetricRow label="API Version" value={modelInfo?.version} />
          </dl>
        </div>

        <div className="card abc">
          <div className="ct"><i className="fas fa-chart-line" /> Reported Metrics</div>
          <dl>
            <MetricRow label="Model" value={metrics.Model} />
            <MetricRow label="Accuracy" value={metrics['Accuracy']} />
            <MetricRow label="Precision" value={metrics['Precision']} />
            <MetricRow label="Recall" value={metrics['Recall']} />
            <MetricRow label="F1 Score" value={metrics['F1']} />
            <MetricRow label="ROC-AUC" value={metrics['ROC-AUC']} />
          </dl>
        </div>

        <div className="card abc">
          <div className="ct"><i className="fas fa-ranking-star" /> Top Models</div>
          <div className="table-wrap">
            <table className="leaderboard">
              <thead>
                <tr><th>Model</th><th>Category</th><th>Accuracy</th><th>ROC-AUC</th></tr>
              </thead>
              <tbody>
                {leaderboard.length ? leaderboard.slice(0, 6).map(row => (
                  <tr key={row.Model}>
                    <td>{row.Model}</td>
                    <td>{row.Category}</td>
                    <td>{row.Accuracy}</td>
                    <td>{row['ROC-AUC']}</td>
                  </tr>
                )) : (
                  <tr><td colSpan="4">No leaderboard data available.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card abc warn-card">
          <div className="ct"><i className="fas fa-box-archive" /> Artifacts</div>
          <div className="artifact-list">
            {artifacts.length ? artifacts.slice(0, 8).map(item => (
              <div key={item.name} className="artifact-item">
                <strong>{item.name}</strong>
                <span>{item.size_kb} KB</span>
              </div>
            )) : 'No artifacts discovered.'}
          </div>
        </div>
      </div>
    </section>
  )
}
