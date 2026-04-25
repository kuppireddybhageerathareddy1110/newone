import React, { useEffect, useMemo, useState } from 'react'

import { request } from '../lib/api'

const DEFAULT_FORM = {
  age: 55,
  sex: 'Male',
  chest_pain: 'Atypical Angina',
  resting_ecg: 'Normal',
  exercise_angina: 'No',
  st_slope: 'Flat',
  restingbp_final: 140,
  chol_final: 250,
  maxhr_final: 150,
  oldpeak: 2.0,
  fasting_bs: 'No',
}

const SAMPLE = {
  age: 65,
  sex: 'Male',
  chest_pain: 'Asymptomatic',
  restingbp_final: 160,
  chol_final: 300,
  fasting_bs: 'Yes',
  resting_ecg: 'ST-T Abnormality',
  maxhr_final: 130,
  exercise_angina: 'Yes',
  oldpeak: 2.5,
  st_slope: 'Flat',
}

function ArcGauge({ pct }) {
  const off = 251.2 - (pct / 100) * 251.2
  const stroke = pct >= 70 ? '#ef4444' : pct >= 40 ? '#f59e0b' : '#10b981'
  return (
    <svg className="arc-svg" viewBox="0 0 200 120">
      <path d="M 20 100 A 80 80 0 0 1 180 100" stroke="#e2e8f0" strokeWidth="16" fill="none" strokeLinecap="round" />
      <path
        d="M 20 100 A 80 80 0 0 1 180 100"
        stroke={stroke}
        strokeWidth="16"
        fill="none"
        strokeLinecap="round"
        strokeDasharray="251.2"
        strokeDashoffset={off}
        style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1), stroke .8s' }}
      />
      <text x="100" y="92" textAnchor="middle" className="arc-pct">{pct.toFixed(1)}%</text>
      <text x="100" y="112" textAnchor="middle" className="arc-label">Hybrid Probability</text>
    </svg>
  )
}

function QuickAlerts({ form }) {
  const alerts = useMemo(() => {
    const next = []
    if (form.restingbp_final >= 140) next.push('Resting blood pressure is elevated.')
    if (form.chol_final >= 240) next.push('Cholesterol is in a high range.')
    if (form.oldpeak >= 2) next.push('Oldpeak suggests notable stress-induced ECG change.')
    if (form.exercise_angina === 'Yes') next.push('Exercise angina is present.')
    return next
  }, [form])

  if (!alerts.length) return null

  return (
    <div className="qa">
      <div className="qa-title">Input highlights</div>
      <ul>
        {alerts.map(alert => <li key={alert}>{alert}</li>)}
      </ul>
    </div>
  )
}

export default function AssessmentPage({
  latestAssessment,
  onLoading,
  onToast,
  onNavigate,
  onAssessmentComplete,
}) {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [result, setResult] = useState(null)

  useEffect(() => {
    if (latestAssessment?.patient) {
      setForm(latestAssessment.patient)
      setResult(latestAssessment.result || null)
    }
  }, [latestAssessment])

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const numSet = (k, v) => setForm(f => ({ ...f, [k]: parseFloat(v) || 0 }))

  const loadSample = () => {
    setForm(SAMPLE)
    onToast('<i class="fas fa-check-circle"></i> High-risk sample patient loaded')
  }

  const handleSubmit = async e => {
    e.preventDefault()
    onLoading(true, 'Analysing patient data...')
    try {
      const next = await request('/predict', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setResult(next)
      await onAssessmentComplete({ patient: form, result: next })
      onToast('<i class="fas fa-heart-circle-check"></i> Assessment completed')
    } catch (err) {
      alert(`Cannot reach API.\n\nStart the backend:\n  uvicorn api_hybrid:app --port 8001\n\n${err.message}`)
    } finally {
      onLoading(false)
    }
  }

  const exportJSON = () => {
    if (!result) return
    const blob = new Blob([JSON.stringify({ patient: form, result }, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cardioai_case_${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
    onToast('<i class="fas fa-file-export"></i> Case exported')
  }

  const lvl = result ? (result.risk_level || 'low').toLowerCase() : null
  const em = { low: 'Low', medium: 'Medium', high: 'High' }
  const pct = result ? result.probability * 100 : 0
  const ci = result?.confidence_interval || {}

  return (
    <section className="sec active">
      <div className="ph">
        <div>
          <h1>Patient Risk Assessment</h1>
          <p>Hybrid model: XGBoost + Deep Learning stacked via Meta Logistic Regression.</p>
        </div>
        <button className="sample-btn" onClick={loadSample}>
          <i className="fas fa-user-injured" /> Load Sample
        </button>
      </div>

      <div className="hybrid-bar">
        <div className="hchip xgb"><i className="fas fa-tree" /> XGBoost (base)</div>
        <div className="hchip dl"><i className="fas fa-brain" /> Deep Learning (base)</div>
        <div className="hchip meta"><i className="fas fa-layer-group" /> Meta Logistic Regression (stacked)</div>
      </div>

      <div className="ag">
        <div className="card">
          <div className="ct"><i className="fas fa-clipboard-list" /> Patient Parameters</div>
          <form onSubmit={handleSubmit}>
            <div className="fgl">Demographics</div>
            <div className="fr">
              <div className="field">
                <label>Age <span className="unit">yrs</span></label>
                <input type="number" min="18" max="120" value={form.age} onChange={e => numSet('age', e.target.value)} required />
              </div>
              <div className="field">
                <label>Biological Sex</label>
                <select value={form.sex} onChange={e => set('sex', e.target.value)}>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
            </div>

            <div className="fgl">Cardiac Markers</div>
            <div className="fr">
              <div className="field">
                <label>Chest Pain Type</label>
                <select value={form.chest_pain} onChange={e => set('chest_pain', e.target.value)}>
                  <option value="Typical Angina">Typical Angina</option>
                  <option value="Atypical Angina">Atypical Angina</option>
                  <option value="Non-anginal Pain">Non-anginal Pain</option>
                  <option value="Asymptomatic">Asymptomatic</option>
                </select>
              </div>
              <div className="field">
                <label>Resting ECG</label>
                <select value={form.resting_ecg} onChange={e => set('resting_ecg', e.target.value)}>
                  <option value="Normal">Normal</option>
                  <option value="ST-T Abnormality">ST-T Abnormality</option>
                  <option value="LV Hypertrophy">LV Hypertrophy</option>
                </select>
              </div>
            </div>

            <div className="fr">
              <div className="field">
                <label>Exercise Angina</label>
                <select value={form.exercise_angina} onChange={e => set('exercise_angina', e.target.value)}>
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                </select>
              </div>
              <div className="field">
                <label>ST Slope</label>
                <select value={form.st_slope} onChange={e => set('st_slope', e.target.value)}>
                  <option value="Upsloping">Upsloping</option>
                  <option value="Flat">Flat</option>
                  <option value="Downsloping">Downsloping</option>
                </select>
              </div>
            </div>

            <div className="fgl">Vitals &amp; Labs</div>
            <div className="fr three">
              <div className="field">
                <label>Resting BP <span className="unit">mm Hg</span></label>
                <input type="number" min="80" max="200" value={form.restingbp_final} onChange={e => numSet('restingbp_final', e.target.value)} required />
              </div>
              <div className="field">
                <label>Cholesterol <span className="unit">mg/dl</span></label>
                <input type="number" min="100" max="600" value={form.chol_final} onChange={e => numSet('chol_final', e.target.value)} required />
              </div>
              <div className="field">
                <label>Max Heart Rate <span className="unit">bpm</span></label>
                <input type="number" min="60" max="220" value={form.maxhr_final} onChange={e => numSet('maxhr_final', e.target.value)} required />
              </div>
            </div>

            <div className="fr">
              <div className="field">
                <label>ST Depression <span className="unit">Oldpeak</span></label>
                <input type="number" min="0" max="10" step="0.1" value={form.oldpeak} onChange={e => numSet('oldpeak', e.target.value)} required />
              </div>
              <div className="field">
                <label>Fasting Blood Sugar <span className="unit">&gt;120 mg/dl</span></label>
                <select value={form.fasting_bs} onChange={e => set('fasting_bs', e.target.value)}>
                  <option value="No">No</option>
                  <option value="Yes">Yes</option>
                </select>
              </div>
            </div>

            <QuickAlerts form={form} />

            <button type="submit" className="pb">
              <i className="fas fa-brain" /> Run Hybrid Analysis
            </button>
          </form>
        </div>

        <div className="card rc">
          <div className="ct"><i className="fas fa-chart-pie" /> Hybrid Prediction Results</div>
          {!result ? (
            <div className="placeholder">
              <div className="placeholder-icon">CardioAI</div>
              <p>Complete the form and run the hybrid analysis to see the result.</p>
            </div>
          ) : (
            <div className="pred-results">
              <div className={`vb ${lvl}`}>
                <div className="ve">{em[lvl] || 'Unknown'} Risk</div>
                <div className="vl">{result.prediction}</div>
                <div className="vs">{result.model_used}</div>
              </div>

              <div className="contrib-row">
                <div className="contrib-chip xgb"><i className="fas fa-tree" /> XGB: <strong>{((result.xgb_probability || 0) * 100).toFixed(1)}%</strong></div>
                <div className="contrib-chip dl"><i className="fas fa-brain" /> DL: <strong>{((result.dl_probability || 0) * 100).toFixed(1)}%</strong></div>
                <div className="contrib-chip meta"><i className="fas fa-layer-group" /> Hybrid: <strong>{((result.probability || 0) * 100).toFixed(1)}%</strong></div>
              </div>

              <div className="prob-sec">
                <ArcGauge pct={pct} />
                <div className="ci-pill">
                  <i className="fas fa-bullseye" />
                  <span>95% range: <strong>{((ci.lower || 0) * 100).toFixed(1)}% - {((ci.upper || 0) * 100).toFixed(1)}%</strong></span>
                </div>
              </div>

              <div className="fcols">
                <div className="fcol risk-col">
                  <div className="fch"><i className="fas fa-triangle-exclamation" /> Risk Factors</div>
                  <ul>
                    {(result.risk_factors?.length ? result.risk_factors : ['No major risk features identified']).map(text => <li key={text}>{text}</li>)}
                  </ul>
                </div>
                <div className="fcol prot-col">
                  <div className="fch"><i className="fas fa-shield-heart" /> Protective Factors</div>
                  <ul>
                    {(result.protective_factors?.length ? result.protective_factors : ['No major protective features identified']).map(text => <li key={text}>{text}</li>)}
                  </ul>
                </div>
              </div>

              {!!result.recommendations?.length && (
                <div className="reco-card">
                  <div className="fch"><i className="fas fa-notes-medical" /> Suggested Follow-up</div>
                  <ul className="reco-list">
                    {result.recommendations.map(item => (
                      <li key={item.title}>
                        <strong>{item.title}</strong>
                        <span>{item.reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="cta-row">
                <button className="cta primary" onClick={() => onNavigate('explain')}>
                  <i className="fas fa-microscope" /> View XAI Explanations
                </button>
                <button className="cta ghost" onClick={() => onNavigate('insights')}>
                  <i className="fas fa-lightbulb" /> Personalized Insights
                </button>
                <button className="cta ghost" onClick={exportJSON}>
                  <i className="fas fa-file-arrow-down" /> Export JSON
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
