import React, { useState } from 'react'

import { request } from '../lib/api'

const TEMPLATE = `age,sex,oldpeak,chest_pain,restingbp_final,chol_final,maxhr_final,fasting_bs,resting_ecg,exercise_angina,st_slope
65,Male,2.5,Asymptomatic,160,300,130,Yes,ST-T Abnormality,Yes,Flat
54,Female,1.2,Non-anginal Pain,128,210,158,No,Normal,No,Upsloping`

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean)
  if (lines.length < 2) throw new Error('CSV needs a header row and at least one data row.')
  const headers = lines[0].split(',').map(h => h.trim())
  return lines.slice(1).map(line => {
    const cells = line.split(',').map(c => c.trim())
    const row = {}
    headers.forEach((header, index) => {
      row[header] = cells[index] ?? ''
    })
    ;['age', 'oldpeak', 'restingbp_final', 'chol_final', 'maxhr_final'].forEach(key => {
      row[key] = Number(row[key])
    })
    return row
  })
}

export default function BatchPage({ onLoading, onToast }) {
  const [csvText, setCsvText] = useState(TEMPLATE)
  const [batchResult, setBatchResult] = useState(null)

  const runBatch = async () => {
    onLoading(true, 'Running batch assessment...')
    try {
      const patients = parseCsv(csvText)
      const next = await request('/predict/batch', {
        method: 'POST',
        body: JSON.stringify({ patients }),
      })
      setBatchResult(next)
      onToast('<i class="fas fa-table"></i> Batch assessment completed')
    } catch (err) {
      alert(err.message)
    } finally {
      onLoading(false)
    }
  }

  const exportBatch = () => {
    if (!batchResult) return
    const header = ['prediction', 'probability', 'risk_level', 'xgb_probability', 'dl_probability']
    const rows = batchResult.results.map(item => header.map(key => item[key]).join(','))
    const blob = new Blob([[header.join(','), ...rows].join('\n')], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cardioai_batch_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="sec active">
      <div className="ph">
        <div>
          <h1>Batch Assessment</h1>
          <p>Paste CSV rows matching the model input schema to score multiple patients in one request.</p>
        </div>
      </div>

      <div className="batch-grid">
        <div className="card">
          <div className="ct"><i className="fas fa-file-csv" /> CSV Input</div>
          <div className="batch-body">
            <textarea className="batch-input" value={csvText} onChange={e => setCsvText(e.target.value)} />
            <div className="cta-row">
              <button className="cta primary" onClick={runBatch}>
                <i className="fas fa-play" /> Run Batch
              </button>
              <button className="cta ghost" onClick={() => setCsvText(TEMPLATE)}>
                <i className="fas fa-wand-magic-sparkles" /> Reset Template
              </button>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="ct"><i className="fas fa-list-check" /> Batch Results</div>
          {!batchResult ? (
            <div className="placeholder">
              <p>Run a batch assessment to view aggregate results.</p>
            </div>
          ) : (
            <div className="batch-body">
              <div className="batch-summary">
                <div><strong>{batchResult.count}</strong><span>Total cases</span></div>
                <div><strong>{batchResult.disease_count}</strong><span>Disease predictions</span></div>
                <div><strong>{(batchResult.average_probability * 100).toFixed(1)}%</strong><span>Average probability</span></div>
              </div>
              <div className="table-wrap">
                <table className="leaderboard">
                  <thead>
                    <tr><th>#</th><th>Prediction</th><th>Risk</th><th>Probability</th></tr>
                  </thead>
                  <tbody>
                    {batchResult.results.map((row, idx) => (
                      <tr key={`${row.timestamp}-${idx}`}>
                        <td>{idx + 1}</td>
                        <td>{row.prediction}</td>
                        <td>{row.risk_level}</td>
                        <td>{(row.probability * 100).toFixed(1)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <button className="cta ghost" onClick={exportBatch}>
                <i className="fas fa-download" /> Export Batch CSV
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
