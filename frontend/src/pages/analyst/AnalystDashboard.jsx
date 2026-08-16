// pages/analyst/AnalystDashboard.jsx — Main dashboard for analysts/government
import { useState, useEffect } from 'react'
import { nodesApi } from '../../api/client'
import { useOptimization } from '../../hooks/useOptimization'
import Header from '../../components/layout/Header'
import Sidebar from '../../components/layout/Sidebar'
import SupplyChainMap from '../../components/map/SupplyChainMap'
import CostBreakdown from '../../components/charts/CostBreakdown'
import KpiMetrics from '../../components/charts/KpiMetrics'
import toast from 'react-hot-toast'
import { Map, BarChart2, Activity, AlertTriangle } from 'lucide-react'

const DEFAULT_PARAMS = {
  carbon_tax_usd_per_kg: 0.03,
  biorefinery_capacity_ton_day: 500,
  emission_limit_ton_co2: null,
  max_budget_usd: null,
  solver_name: 'appsi_highs',
  time_limit_seconds: 300,
}

export default function AnalystDashboard() {
  const [activeTab, setActiveTab]   = useState('map')
  const [nodes, setNodes]           = useState(null)
  const [params, setParams]         = useState(DEFAULT_PARAMS)
  const [nodesError, setNodesError] = useState(null)

  const { status, result, error, progress, startOptimization, reset } = useOptimization()

  // Fetch spatial nodes on mount
  useEffect(() => {
    nodesApi.getAll()
      .then(res => setNodes(res.data))
      .catch(err => {
        const msg = err.response?.data?.detail || 'Gagal memuat data node spasial'
        setNodesError(msg)
        toast.error(msg)
      })
  }, [])

  const handleParamChange = (key, value) => {
    setParams(prev => ({ ...prev, [key]: value }))
  }

  const handleRunOptimization = async () => {
    if (status === 'running' || status === 'pending') return
    reset()
    toast('🔄 Optimasi dimulai...', { icon: '⚙️' })
    await startOptimization(params)
  }

  // Show toast on completion/error
  useEffect(() => {
    if (status === 'completed') toast.success('✅ Optimasi selesai! Solusi optimal ditemukan.')
    if (status === 'failed')    toast.error(`❌ Optimasi gagal: ${error}`)
    if (status === 'timeout')   toast('⏱️ Solver timeout — menampilkan solusi terbaik yang ada.', { icon: '⚠️' })
  }, [status])

  const isRunning   = status === 'running' || status === 'pending'
  const openHubs    = result?.open_hubs || []
  const routes      = result?.routes || []

  return (
    <div className="app-layout">
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onRunOptimization={handleRunOptimization}
        isRunning={isRunning}
        params={params}
        onParamsChange={handleParamChange}
      />

      <div className="main-content">
        <Header title="Dashboard Analis — BioChain-Opt" />

        {/* Main content area */}
        <div style={{ flex: 1, padding: 'var(--space-6)', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>

          {/* Nodes load error */}
          {nodesError && (
            <div style={{
              background: '#FFEBEE', border: '1px solid #FFCDD2',
              borderRadius: 'var(--radius-lg)', padding: 'var(--space-4)',
              display: 'flex', alignItems: 'center', gap: 12, color: '#C62828',
            }}>
              <AlertTriangle size={20} />
              <span>{nodesError} — Pastikan backend dan database berjalan.</span>
            </div>
          )}

          {/* Optimization Progress Bar */}
          {isRunning && (
            <div className="card" style={{ padding: 'var(--space-4) var(--space-6)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="status-dot running" />
                  <span style={{ fontWeight: 700, color: 'var(--color-gray-800)' }}>
                    Solver MILP sedang berjalan...
                  </span>
                </div>
                <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-500)' }}>
                  {Math.round(progress)}%
                </span>
              </div>
              <div className="gauge-bar">
                <div className="gauge-fill" style={{ width: `${progress}%`, background: 'linear-gradient(90deg, #4CAF50, #2E7D32)' }} />
              </div>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-400)', marginTop: 6 }}>
                CBC solver menghitung rute optimal Hub-and-Spoke untuk {nodes?.farms?.length || 0} farm,{' '}
                {nodes?.hubs?.length || 0} hub kandidat, {nodes?.biorefineries?.length || 0} biorefinery...
              </p>
            </div>
          )}

          {/* Tab Navigation */}
          <div className="tabs">
            {[
              { key: 'map',   label: '🗺️ Peta Spasial',     icon: Map },
              { key: 'costs', label: '📦 Rincian Biaya',    icon: BarChart2 },
              { key: 'kpi',   label: '📊 Metrik KPI',       icon: Activity },
            ].map(({ key, label }) => (
              <button
                key={key}
                className={`tab-btn ${activeTab === key ? 'active' : ''}`}
                onClick={() => setActiveTab(key)}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div style={{ flex: 1, minHeight: 0 }}>
            {activeTab === 'map' && (
              <div style={{ height: 'calc(100vh - 320px)', minHeight: 450 }}>
                {nodes ? (
                  <SupplyChainMap
                    nodes={nodes}
                    routes={routes}
                    openHubs={openHubs}
                  />
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                    <div className="spinner" />
                  </div>
                )}
              </div>
            )}

            {activeTab === 'costs' && (
              <CostBreakdown result={result} nodes={nodes} />
            )}

            {activeTab === 'kpi' && (
              <KpiMetrics result={result} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
