// components/layout/Sidebar.jsx — Analyst sidebar with parameter controls
import { useState } from 'react'
import {
  Map, BarChart2, Activity, Settings, Leaf,
  DollarSign, Wind, Zap, Play, RotateCcw,
  ChevronRight, Recycle
} from 'lucide-react'

export default function Sidebar({ activeTab, onTabChange, onRunOptimization, isRunning, params, onParamsChange }) {
  const tabs = [
    { key: 'circular', label: 'Alur Sirkular', icon: Recycle },
    { key: 'map', label: 'Peta Spasial', icon: Map },
    { key: 'costs', label: 'Biaya ABC', icon: BarChart2 },
    { key: 'kpi', label: 'Metrik KPI', icon: Activity },
    { key: 'transactions', label: 'Transaksi', icon: Settings },
  ]

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div style={{
          width: 40, height: 40,
          background: 'linear-gradient(135deg, #66BB6A, #2E7D32)',
          borderRadius: 10,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 20,
        }}>🌿</div>
        <div>
          <div style={{ fontSize: 'var(--text-lg)', fontWeight: 800 }}>BioChain</div>
          <div style={{ fontSize: 'var(--text-xs)', opacity: 0.7, fontWeight: 400 }}>Opt v1.0</div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="sidebar-nav">
        <p style={{ fontSize: 'var(--text-xs)', opacity: 0.6, fontWeight: 700, letterSpacing: '0.08em', marginBottom: 8 }}>
          TAMPILAN
        </p>
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            className={`nav-item ${activeTab === key ? 'active' : ''}`}
            onClick={() => onTabChange(key)}
          >
            <Icon size={18} />
            {label}
          </button>
        ))}
      </nav>

      {/* Scenario Parameters */}
      <div style={{ marginTop: 'var(--space-8)', borderTop: '1px solid rgba(255,255,255,0.15)', paddingTop: 'var(--space-6)' }}>
        <p style={{ fontSize: 'var(--text-xs)', opacity: 0.6, fontWeight: 700, letterSpacing: '0.08em', marginBottom: 12 }}>
          PARAMETER SKENARIO
        </p>

        {/* Lambda Green */}
        <div className="input-group" style={{ marginBottom: 'var(--space-5)' }}>
          <label style={{ color: 'rgba(255,255,255,0.85)', fontSize: 'var(--text-sm)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Wind size={14} /> Pajak Karbon (Green Penalty)
          </label>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', opacity: 0.7, marginBottom: 4 }}>
            <span>Rp 0</span>
            <span style={{ fontWeight: 700, color: 'var(--color-accent-400)', fontSize: 'var(--text-sm)' }}>
              Rp {params.lambda_green || 465}/kg
            </span>
            <span>Rp 1.000</span>
          </div>
          <input
            type="range" className="slider"
            min={0} max={1000} step={10}
            value={params.lambda_green || 465}
            onChange={e => onParamsChange('lambda_green', parseFloat(e.target.value))}
          />
        </div>

        {/* Shrinkage */}
        <div className="input-group" style={{ marginBottom: 'var(--space-5)' }}>
          <label style={{ color: 'rgba(255,255,255,0.85)', fontSize: 'var(--text-sm)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Activity size={14} /> Asumsi Shrinkage (Air)
          </label>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', opacity: 0.7, marginBottom: 4 }}>
            <span>10%</span>
            <span style={{ fontWeight: 700, color: 'var(--color-accent-400)', fontSize: 'var(--text-sm)' }}>
              {((params.shrinkage_rate_override || 0.18) * 100).toFixed(0)}%
            </span>
            <span>30%</span>
          </div>
          <input
            type="range" className="slider"
            min={0.10} max={0.30} step={0.01}
            value={params.shrinkage_rate_override || 0.18}
            onChange={e => onParamsChange('shrinkage_rate_override', parseFloat(e.target.value))}
          />
        </div>

        {/* Biorefinery Capacity */}
        <div className="input-group" style={{ marginBottom: 'var(--space-5)' }}>
          <label style={{ color: 'rgba(255,255,255,0.85)', fontSize: 'var(--text-sm)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Zap size={14} /> Kapasitas Biorefinery
          </label>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', opacity: 0.7, marginBottom: 4 }}>
            <span>100t</span>
            <span style={{ fontWeight: 700, color: 'var(--color-accent-400)', fontSize: 'var(--text-sm)' }}>
              {params.biorefinery_capacity_ton_day} ton/hari
            </span>
            <span>1000t</span>
          </div>
          <input
            type="range" className="slider"
            min={100} max={1000} step={10}
            value={params.biorefinery_capacity_ton_day}
            onChange={e => onParamsChange('biorefinery_capacity_ton_day', parseInt(e.target.value))}
          />
        </div>

        {/* Emission Limit */}
        <div className="input-group" style={{ marginBottom: 'var(--space-5)' }}>
          <label style={{ color: 'rgba(255,255,255,0.85)', fontSize: 'var(--text-sm)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Wind size={14} /> Batas Emisi (ton/tahun)
          </label>
          <div style={{ position: 'relative' }}>
            <input
              type="number" className="input"
              min={0} placeholder="Tidak dibatasi"
              value={params.emission_limit_ton_co2 || ''}
              onChange={e => onParamsChange('emission_limit_ton_co2', e.target.value ? parseFloat(e.target.value) : null)}
              style={{ background: 'rgba(255,255,255,0.12)', color: 'white', borderColor: 'rgba(255,255,255,0.25)' }}
            />
          </div>
        </div>

        {/* Max Budget */}
        <div className="input-group" style={{ marginBottom: 'var(--space-6)' }}>
          <label style={{ color: 'rgba(255,255,255,0.85)', fontSize: 'var(--text-sm)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
            <DollarSign size={14} /> Batas Anggaran (USD/tahun)
          </label>
          <input
            type="number" className="input"
            min={0} placeholder="Tidak dibatasi"
            value={params.max_budget_usd || ''}
            onChange={e => onParamsChange('max_budget_usd', e.target.value ? parseFloat(e.target.value) : null)}
            style={{ background: 'rgba(255,255,255,0.12)', color: 'white', borderColor: 'rgba(255,255,255,0.25)' }}
          />
        </div>

        {/* Run Button */}
        <button
          className="btn btn-full"
          onClick={onRunOptimization}
          disabled={isRunning}
          style={{
            background: isRunning
              ? 'rgba(255,255,255,0.15)'
              : 'linear-gradient(135deg, var(--color-accent-500), var(--color-accent-600))',
            color: 'var(--color-gray-900)',
            fontWeight: 800,
            fontSize: 'var(--text-base)',
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-lg)',
            border: 'none',
          }}
        >
          {isRunning ? (
            <><div className="spinner" style={{ width: 20, height: 20, borderWidth: 3 }} /> Menghitung...</>
          ) : (
            <><Play size={18} fill="currentColor" /> Simulasikan</>
          )}
        </button>
      </div>

      {/* Footer */}
      <div style={{ marginTop: 'auto', paddingTop: 'var(--space-6)', fontSize: 'var(--text-xs)', opacity: 0.5, textAlign: 'center' }}>
        Greenovate Challenge 2026<br />
        Solver: CBC (MILP)
      </div>
    </aside>
  )
}
