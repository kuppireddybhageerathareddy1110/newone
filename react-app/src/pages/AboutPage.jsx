import React from 'react'

function MetricRow({ label, value }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value ?? 'Unavailable'}</dd>
    </>
  )
}

const FEATURE_GLOSSARY = {
  age: {
    full: 'Age',
    meaning: 'Patient age in years.',
  },
  oldpeak: {
    full: 'ST Depression (Oldpeak)',
    meaning: 'Depression in the ST segment induced by exercise relative to rest.',
  },
  restingbp_final: {
    full: 'Resting Blood Pressure',
    meaning: 'Blood pressure measured at rest in mm Hg.',
  },
  chol_final: {
    full: 'Serum Cholesterol',
    meaning: 'Cholesterol level measured in mg/dl.',
  },
  maxhr_final: {
    full: 'Maximum Heart Rate',
    meaning: 'Highest heart rate achieved during testing or exercise.',
  },
  chol_age_ratio: {
    full: 'Cholesterol-to-Age Ratio',
    meaning: 'Engineered feature comparing cholesterol burden relative to age.',
  },
  bp_hr_ratio: {
    full: 'Blood Pressure-to-Heart Rate Ratio',
    meaning: 'Engineered feature comparing resting blood pressure with maximum heart rate.',
  },
  stress_index: {
    full: 'Stress Index',
    meaning: 'Engineered feature combining ST depression and heart rate.',
  },
  cardiac_load: {
    full: 'Cardiac Load',
    meaning: 'Engineered feature combining resting blood pressure and age.',
  },
  sex_Male: {
    full: 'Sex: Male',
    meaning: 'One-hot encoded flag indicating the patient is male.',
  },
  sex_M: {
    full: 'Sex: Male',
    meaning: 'Legacy one-hot encoded male indicator.',
  },
  fbs_final_Yes: {
    full: 'Fasting Blood Sugar > 120 mg/dl',
    meaning: 'One-hot encoded flag for elevated fasting blood sugar.',
  },
  exang_final_Yes: {
    full: 'Exercise-Induced Angina: Yes',
    meaning: 'One-hot encoded flag for chest pain induced by exercise.',
  },
  exang_final_Y: {
    full: 'Exercise-Induced Angina: Yes',
    meaning: 'Legacy one-hot encoded flag for exercise-induced angina.',
  },
  slope_final_Up: {
    full: 'ST Slope: Upsloping',
    meaning: 'One-hot encoded flag for an upsloping ST segment.',
  },
  slope_final_Flat: {
    full: 'ST Slope: Flat',
    meaning: 'One-hot encoded flag for a flat ST segment.',
  },
  slope_final_Down: {
    full: 'ST Slope: Downsloping',
    meaning: 'One-hot encoded flag for a downsloping ST segment.',
  },
}

function describeFeature(feature) {
  if (FEATURE_GLOSSARY[feature]) return FEATURE_GLOSSARY[feature]

  const chestPain = feature.match(/^cp_final_(.+)$/)
  if (chestPain) {
    return {
      full: `Chest Pain Type: ${chestPain[1]}`,
      meaning: 'One-hot encoded chest pain category used by the model.',
    }
  }

  const restingEcg = feature.match(/^restecg_final_(.+)$/)
  if (restingEcg) {
    return {
      full: `Resting ECG: ${restingEcg[1]}`,
      meaning: 'One-hot encoded resting electrocardiogram category.',
    }
  }

  if (/^cp_final_\d+$/.test(feature)) {
    return {
      full: `Chest Pain Encoded Flag (${feature})`,
      meaning: 'Legacy encoded chest pain indicator retained for model compatibility.',
    }
  }

  if (/^restecg_final_\d+$/.test(feature)) {
    return {
      full: `Resting ECG Encoded Flag (${feature})`,
      meaning: 'Legacy encoded resting ECG indicator retained for model compatibility.',
    }
  }

  if (/^slope_final_\d+$/.test(feature)) {
    return {
      full: `ST Slope Encoded Flag (${feature})`,
      meaning: 'Legacy encoded ST slope indicator retained for model compatibility.',
    }
  }

  return {
    full: feature,
    meaning: 'Model input feature exposed by the backend.',
  }
}

export default function AboutPage({ modelInfo }) {
  const metrics = modelInfo?.best_reported_metrics || {}
  const leaderboard = modelInfo?.leaderboard || []
  const artifacts = modelInfo?.artifacts || []
  const features = modelInfo?.feature_list || []

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

        <div className="card abc feature-card">
          <div className="ct"><i className="fas fa-book-medical" /> Feature Glossary</div>
          <div className="feature-list">
            {features.length ? features.map(feature => {
              const meta = describeFeature(feature)
              return (
                <div key={feature} className="feature-item">
                  <code>{feature}</code>
                  <strong>{meta.full}</strong>
                  <p>{meta.meaning}</p>
                </div>
              )
            }) : 'No feature list available.'}
          </div>
        </div>
      </div>
    </section>
  )
}
