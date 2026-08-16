// components/charts/KpiMetrics.jsx — KPI summary cards + emission donut
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts'
import { TrendingDown, Leaf, Package, DollarSign, Zap, Truck, ShieldAlert, CheckCircle, Droplets } from 'lucide-react'

const fmt = (n, dec = 2) => n != null ? Number(n).toLocaleString('id-ID', { maximumFractionDigits: dec }) : '—'
const fmtIDR = (n) => n != null ? `Rp ${fmt(n)}` : '—'

function KpiCard({ icon: Icon, label, value, unit, color = 'var(--color-primary-800)', accent }) {
  return (
    <div className="kpi-card" style={{ '--accent': accent || color }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span className="kpi-label">{label}</span>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={18} color={color} />
        </div>
      </div>
      <div className="kpi-value" style={{ color }}>{value}</div>
      <div className="kpi-unit">{unit}</div>
    </div>
  )
}

export default function KpiMetrics({ result }) {
  if (!result) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--space-16)', color: 'var(--color-gray-400)' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>📊</div>
        <p style={{ fontSize: 'var(--text-lg)', fontWeight: 600 }}>Jalankan optimasi untuk melihat KPI</p>
        <p style={{ fontSize: 'var(--text-sm)', marginTop: 8 }}>Atur parameter di sidebar lalu klik "Simulasikan"</p>
      </div>
    )
  }

  const costBreakdown = [
    { name: 'Hulu (Petani)', value: result.harvest_cost_year || 0, color: '#8D6E63' },
    { name: 'Transport Pengepul', value: result.transport_fh_cost_year || 0, color: '#FFB300' },
    { name: 'Pengepul (Handling)', value: result.hub_handling_cost_year || 0, color: '#FB8C00' },
    { name: 'Penyusutan (Shrinkage)', value: result.shrinkage_cost_year || 0, color: '#039BE5' },
    { name: 'Transport FTL', value: result.transport_hf_cost_year || 0, color: '#43A047' },
    { name: 'Pabrikasi', value: result.factory_cost_year || 0, color: '#1E88E5' },
    { name: 'Pajak Karbon', value: result.green_penalty_year || 0, color: '#E53935' },
    { name: 'Penalti Risiko', value: result.resilience_penalty_year || 0, color: '#8E24AA' },
  ]

  const statusColor = result.status === 'optimal' ? 'var(--color-success)' : 'var(--color-warning)'

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Status Banner */}
      <div style={{
        background: result.status === 'optimal'
          ? 'linear-gradient(135deg, #E8F5E9, #C8E6C9)'
          : 'linear-gradient(135deg, #FFF9C4, #FFF176)',
        borderRadius: 'var(--radius-xl)',
        padding: 'var(--space-4) var(--space-6)',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        border: `1px solid ${result.status === 'optimal' ? '#A5D6A7' : '#FFF176'}`,
      }}>
        <div>
          <p style={{ fontWeight: 700, fontSize: 'var(--text-base)', color: statusColor }}>
            {result.status === 'optimal' ? '✅ Solusi Optimal Ditemukan' : '⚡ Solusi Feasible (Batas Waktu)'}
          </p>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-600)', marginTop: 2 }}>
            Hub aktif: <b>{result.active_hubs?.length || 0}</b> dari total kandidat •
            Solver: {result.solver_status} •
            Waktu: {result.solve_time_seconds?.toFixed(1)}s
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)' }}>HPP (Cost of Goods)</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-2xl)', fontWeight: 900, color: 'var(--color-primary-800)' }}>
            Rp {fmt(result.hpp_per_kg, 0)}
          </div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)' }}>per kg tongkol</div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        <KpiCard
          icon={CheckCircle}
          label="Margin Fair Trade (Petani)"
          value={`${fmt(result.fair_trade_margin_pct, 1)}%`}
          unit="% dari total biaya"
          color="#388E3C"
        />
        <KpiCard
          icon={Droplets}
          label="Kehilangan Susut (Shrinkage)"
          value={fmt(result.total_shrinkage_ton_year, 1)}
          unit="ton air menguap / thn"
          color="#1976D2"
        />
        <KpiCard
          icon={ShieldAlert}
          label="Rata-rata Buffer Stock"
          value={`${fmt(result.buffer_stock_avg_pct, 1)}%`}
          unit="% dari kiriman harian"
          color="#FBC02D"
        />
        <KpiCard
          icon={Leaf}
          label="Total Emisi CO₂"
          value={fmt(result.total_emission_ton_co2_year, 1)}
          unit="ton CO₂ / tahun"
          color="#1565C0"
        />
        <KpiCard
          icon={Zap}
          label="Estimasi Etanol"
          value={fmt(result.total_ethanol_liter_year / 1000000, 2)}
          unit="juta liter / tahun"
          color="#7B1FA2"
        />
        <KpiCard
          icon={DollarSign}
          label="Total Biaya (TAC)"
          value={fmtIDR(result.total_annual_cost / 1000000)}
          unit="Juta Rupiah / tahun"
          color="var(--color-primary-800)"
        />
      </div>

      {/* Cost Breakdown Pie Chart */}
      <div className="card">
        <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: 'var(--space-4)', color: 'var(--color-gray-800)' }}>
          Komposisi Biaya ABC (Activity-Based Costing) Tahunan
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={costBreakdown.filter(d => d.value > 0)}
              cx="50%" cy="50%"
              outerRadius={100}
              innerRadius={55}
              paddingAngle={3}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
              labelLine={true}
            >
              {costBreakdown.filter(d => d.value > 0).map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(v) => [`Rp ${fmt(v / 1000000, 0)} Juta`, 'Biaya']}
              contentStyle={{ fontFamily: 'Inter', fontSize: 13, borderRadius: 10 }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
