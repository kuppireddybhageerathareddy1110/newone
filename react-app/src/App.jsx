import React, { useEffect, useState } from 'react'

import Sidebar from './components/Sidebar'
import LoadingOverlay from './components/LoadingOverlay'
import Toast from './components/Toast'

import AssessmentPage from './pages/AssessmentPage'
import ExplainPage from './pages/ExplainPage'
import InsightsPage from './pages/InsightsPage'
import AboutPage from './pages/AboutPage'
import HistoryPage from './pages/HistoryPage'
import BatchPage from './pages/BatchPage'

import { request } from './lib/api'

const HISTORY_KEY = 'cardioai-history-v1'

export default function App() {
  const [activeSection, setActiveSection] = useState('predict')
  const [loadingVisible, setLoadingVisible] = useState(false)
  const [loadingMsg, setLoadingMsg] = useState('Analysing patient data...')
  const [toasts, setToasts] = useState([])
  const [xaiData, setXaiData] = useState({})
  const [latestAssessment, setLatestAssessment] = useState(null)
  const [history, setHistory] = useState([])
  const [modelInfo, setModelInfo] = useState(null)

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
      if (Array.isArray(stored)) setHistory(stored)
    } catch {}
  }, [])

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 20)))
  }, [history])

  useEffect(() => {
    request('/model/info').then(setModelInfo).catch(() => {})
  }, [])

  const setLoading = (on, msg = 'Analysing patient data...') => {
    setLoadingMsg(msg)
    setLoadingVisible(on)
  }

  const showToast = html => {
    const id = Date.now()
    setToasts(ts => [...ts, { id, html, show: false }])
    requestAnimationFrame(() => {
      setToasts(ts => ts.map(t => (t.id === id ? { ...t, show: true } : t)))
    })
    setTimeout(() => {
      setToasts(ts => ts.map(t => (t.id === id ? { ...t, show: false } : t)))
      setTimeout(() => setToasts(ts => ts.filter(t => t.id !== id)), 400)
    }, 2400)
  }

  const loadGlobalPlot = async type => {
    const path = type === 'summary' ? '/explain/summary' : '/explain/importance'
    const message = type === 'summary' ? 'Computing global SHAP summary...' : 'Computing feature importance...'
    setLoading(true, message)
    try {
      const data = await request(path)
      setXaiData(prev => ({ ...prev, [type]: data.plot }))
    } finally {
      setLoading(false)
    }
  }

  const loadIndividualXai = async patient => {
    const opts = { method: 'POST', body: JSON.stringify(patient) }
    const [waterfall, force, lime] = await Promise.allSettled([
      request('/explain/waterfall', opts),
      request('/explain/force', opts),
      request('/explain/lime', opts),
    ])

    setXaiData(prev => ({
      ...prev,
      waterfall: waterfall.status === 'fulfilled' ? waterfall.value.plot : prev.waterfall,
      force: force.status === 'fulfilled' ? force.value.plot : prev.force,
      lime: lime.status === 'fulfilled' ? lime.value.plot : prev.lime,
      limeWeights: lime.status === 'fulfilled' ? lime.value.feature_weights || [] : prev.limeWeights || [],
    }))
  }

  const handleAssessmentComplete = async ({ patient, result }) => {
    const record = {
      id: Date.now(),
      patient,
      result,
    }

    setLatestAssessment(record)
    setHistory(prev => [record, ...prev].slice(0, 20))
    await loadIndividualXai(patient)
  }

  const restoreHistoryItem = item => {
    setLatestAssessment(item)
    setActiveSection('predict')
    showToast('<i class="fas fa-rotate-left"></i> Previous case restored')
  }

  return (
    <>
      <LoadingOverlay visible={loadingVisible} message={loadingMsg} />
      <Toast toasts={toasts} />

      <Sidebar activeSection={activeSection} onNavigate={setActiveSection} />

      <main className="main">
        {activeSection === 'predict' && (
          <AssessmentPage
            latestAssessment={latestAssessment}
            onLoading={setLoading}
            onToast={showToast}
            onNavigate={setActiveSection}
            onAssessmentComplete={handleAssessmentComplete}
          />
        )}

        {activeSection === 'explain' && (
          <ExplainPage xaiData={xaiData} onLoadGlobal={loadGlobalPlot} />
        )}

        {activeSection === 'batch' && (
          <BatchPage onLoading={setLoading} onToast={showToast} />
        )}

        {activeSection === 'history' && (
          <HistoryPage
            history={history}
            onRestore={restoreHistoryItem}
            onClear={() => setHistory([])}
          />
        )}

        {activeSection === 'insights' && (
          <InsightsPage latestAssessment={latestAssessment} />
        )}

        {activeSection === 'about' && (
          <AboutPage modelInfo={modelInfo} />
        )}
      </main>
    </>
  )
}
