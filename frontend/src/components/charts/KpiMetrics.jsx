// components/charts/KpiMetrics.jsx — KPI summary cards + emission donut
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend
} from 'recharts'
import { TrendingDown, Leaf, Package, DollarSign, Zap, Truck } from 'lucide-react'

const fmt = (n, dec = 2) => n != null ? Number(n).toLocaleString('id-ID', { maximumFractionDigits: dec }) : '—'
const fmtUSD = (n) => n != null ? `$${fmt(n)}` : '—'

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
    { name: 'Transportasi', value: result.transport_cost_usd_year || 0, color: '#4CAF50' },
    { name: 'Operasional Hub', value: result.hub_operating_cost_usd_year || 0, color: '#FFC107' },
    { name: 'Pajak Karbon', value: result.carbon_tax_cost_usd_year || 0, color: '#EF5350' },
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
            Hub aktif: <b>{result.open_hubs?.length || 0}</b> dari total kandidat •
            Solver: {result.solver_status} •
            Waktu: {result.solve_time_seconds?.toFixed(1)}s
          </p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)' }}>MESP</div>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 'var(--text-2xl)', fontWeight: 900, color: 'var(--color-primary-800)' }}>
            ${result.mesp_usd_per_liter?.toFixed(4)}
          </div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)' }}>per liter etanol</div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="kpi-grid">
        <KpiCard
          icon={DollarSign}
          label="Total Biaya Tahunan (TAC)"
          value={fmtUSD(result.total_annual_cost_usd)}
          unit="USD / tahun"
          color="var(--color-primary-800)"
        />
        <KpiCard
          icon={Leaf}
          label="Total Emisi CO₂"
          value={fmt(result.total_emission_ton_co2_year, 1)}
          unit="ton CO₂ / tahun"
          color="#1565C0"
        />
        <KpiCard
          icon={Package}
          label="Tongkol Jagung Terangkut"
          value={fmt(result.total_corncob_ton_day, 1)}
          unit="ton / hari"
          color="var(--color-secondary-700)"
        />
        <KpiCard
          icon={Zap}
          label="Produksi Bioetanol"
          value={fmt(result.total_ethanol_liter_year / 1000000, 2)}
          unit="juta liter / tahun"
          color="#7B1FA2"
        />
        <KpiCard
          icon={Truck}
          label="Biaya Transportasi"
          value={fmtUSD(result.transport_cost_usd_year)}
          unit="USD / tahun"
          color="#E65100"
        />
        <KpiCard
          icon={TrendingDown}
          label="Harga Jual Min. Etanol (MESP)"
          value={`$${result.mesp_usd_per_liter?.toFixed(4)}`}
          unit="USD / liter"
          color="#00695C"
        />
      </div>

      {/* Cost Breakdown Pie Chart */}
      <div className="card">
        <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: 'var(--space-4)', color: 'var(--color-gray-800)' }}>
          Komposisi Biaya Tahunan
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie
              data={costBreakdown}
              cx="50%" cy="50%"
              outerRadius={100}
              innerRadius={55}
              paddingAngle={3}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
              labelLine={true}
            >
              {costBreakdown.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(v) => [`$${fmt(v)}`, 'Biaya']}
              contentStyle={{ fontFamily: 'Inter', fontSize: 13, borderRadius: 10 }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
