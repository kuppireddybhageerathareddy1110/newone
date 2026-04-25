import React, { useState } from 'react'

const TABS = [
  { id: 'waterfall', icon: 'fa-water', label: 'Waterfall' },
  { id: 'force', icon: 'fa-arrows-left-right', label: 'Force Plot' },
  { id: 'lime', icon: 'fa-lemon', label: 'LIME' },
  { id: 'summary', icon: 'fa-chart-bar', label: 'Global Summary' },
  { id: 'importance', icon: 'fa-list-ol', label: 'Importance' },
]

function PlotPlaceholder({ icon, message, onLoad }) {
  return (
    <div className="pph">
      <i className={`fas ${icon}`} />
      {onLoad
        ? <button className="load-btn" onClick={onLoad}><i className="fas fa-sync" /> Load Plot</button>
        : <p>{message || 'Run a prediction first'}</p>}
    </div>
  )
}

export default function ExplainPage({ xaiData, onLoadGlobal }) {
  const [activeTab, setActiveTab] = useState('waterfall')
  const { waterfall, force, lime, limeWeights, summary, importance } = xaiData || {}

  return (
    <section className="sec active">
      <div className="ph">
        <div>
          <h1>XAI Explanations</h1>
          <p>SHAP and LIME views for both patient-level and global interpretability.</p>
        </div>
      </div>

      <div className="tab-bar">
        {TABS.map(tab => (
          <button
            key={tab.id}
            className={`tab${activeTab === tab.id ? ' active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <i className={`fas ${tab.icon}`} /> {tab.label}
          </button>
        ))}
      </div>

      <div className={`tp${activeTab === 'waterfall' ? ' active' : ''}`}>
        <div className="card pc">
          <div className="ct">SHAP Waterfall</div>
          <p className="card-sub">Feature pushes that move this case above or below the baseline prediction.</p>
          <div className="pw">
            {waterfall
              ? <img className="plot-img loaded" src={`data:image/png;base64,${waterfall}`} alt="SHAP waterfall" />
              : <PlotPlaceholder icon="fa-image" message="Run a prediction first" />}
          </div>
        </div>
      </div>

      <div className={`tp${activeTab === 'force' ? ' active' : ''}`}>
        <div className="card pc">
          <div className="ct">SHAP Force Plot</div>
          <p className="card-sub">Red pushes toward disease risk; blue pushes away.</p>
          <div className="pw">
            {force
              ? <iframe className="force-frame" srcDoc={force} title="force-plot" />
              : <PlotPlaceholder icon="fa-image" message="Run a prediction first" />}
          </div>
        </div>
      </div>

      <div className={`tp${activeTab === 'lime' ? ' active' : ''}`}>
        <div className="card pc">
          <div className="ct">LIME Explanation</div>
          <p className="card-sub">Local surrogate explanation for the current prediction.</p>
          <div className="pw">
            {lime
              ? <img className="plot-img loaded" src={`data:image/png;base64,${lime}`} alt="LIME explanation" />
              : <PlotPlaceholder icon="fa-lemon" message="Run a prediction first" />}
          </div>
          {limeWeights?.length > 0 && (
            <div style={{ padding: '0 1.5rem 1.5rem' }}>
              <table className="lime-table">
                <thead>
                  <tr><th>Feature</th><th>Weight</th><th>Direction</th></tr>
                </thead>
                <tbody>
                  {limeWeights.map(({ feature, weight }) => {
                    const positive = weight > 0
                    return (
                      <tr key={feature}>
                        <td>{feature}</td>
                        <td style={{ color: positive ? '#be123c' : '#059669', fontWeight: 600 }}>
                          {positive ? '+' : ''}{weight.toFixed(4)}
                        </td>
                        <td style={{ color: positive ? '#be123c' : '#059669' }}>
                          {positive ? 'Increases Risk' : 'Decreases Risk'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className={`tp${activeTab === 'summary' ? ' active' : ''}`}>
        <div className="card pc">
          <div className="ct">Global SHAP Summary</div>
          <p className="card-sub">Representative global feature impact across the reference sample.</p>
          <div className="pw">
            {summary
              ? <img className="plot-img loaded" src={`data:image/png;base64,${summary}`} alt="Global SHAP summary" />
              : <PlotPlaceholder icon="fa-chart-bar" onLoad={() => onLoadGlobal('summary')} />}
          </div>
        </div>
      </div>

      <div className={`tp${activeTab === 'importance' ? ' active' : ''}`}>
        <div className="card pc">
          <div className="ct">Feature Importance</div>
          <p className="card-sub">Mean absolute SHAP value across the global reference sample.</p>
          <div className="pw">
            {importance
              ? <img className="plot-img loaded" src={`data:image/png;base64,${importance}`} alt="Feature importance" />
              : <PlotPlaceholder icon="fa-list-ol" onLoad={() => onLoadGlobal('importance')} />}
          </div>
        </div>
      </div>
    </section>
  )
}
