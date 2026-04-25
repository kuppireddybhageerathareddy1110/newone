import React from 'react'

const BASE_INSIGHTS = [
  {
    title: 'Physical activity',
    body: 'Aim for regular aerobic activity and progression matched to clinical tolerance.',
  },
  {
    title: 'Diet quality',
    body: 'Prioritize a Mediterranean-style pattern with fiber, legumes, unsaturated fats, and lower processed food intake.',
  },
  {
    title: 'Blood pressure follow-up',
    body: 'Track blood pressure consistently and review sustained elevations with a clinician.',
  },
  {
    title: 'Medication adherence',
    body: 'If medication is prescribed, consistency matters more than occasional aggressive changes.',
  },
]

export default function InsightsPage({ latestAssessment }) {
  const recommendations = latestAssessment?.result?.recommendations || []

  return (
    <section className="sec active">
      <div className="ph">
        <div>
          <h1>Clinical Insights</h1>
          <p>Static prevention guidance plus patient-specific next steps from the latest assessment.</p>
        </div>
      </div>

      {recommendations.length > 0 && (
        <>
          <div className="section-note">Latest case guidance</div>
          <div className="ig">
            {recommendations.map(item => (
              <div className="ins personalized" key={item.title}>
                <span className={`priority-pill ${item.priority}`}>{item.priority}</span>
                <h3>{item.title}</h3>
                <p>{item.reason}</p>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="section-note">General prevention themes</div>
      <div className="ig">
        {BASE_INSIGHTS.map(item => (
          <div className="ins" key={item.title}>
            <h3>{item.title}</h3>
            <p>{item.body}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
