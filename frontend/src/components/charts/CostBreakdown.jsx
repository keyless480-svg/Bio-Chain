// components/charts/CostBreakdown.jsx — Route cost table + bar chart
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LabelList,
} from 'recharts'
import { Truck, ArrowRight } from 'lucide-react'

const fmt = (n, dec = 2) => n != null ? Number(n).toLocaleString('id-ID', { maximumFractionDigits: dec }) : '—'

export default function CostBreakdown({ result, nodes }) {
  if (!result?.routes?.length) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--space-16)', color: 'var(--color-gray-400)' }}>
        <Truck size={48} style={{ margin: '0 auto 12px', display: 'block' }} />
        <p style={{ fontSize: 'var(--text-lg)', fontWeight: 600 }}>Belum ada data rute</p>
        <p style={{ fontSize: 'var(--text-sm)', marginTop: 8 }}>Jalankan optimasi terlebih dahulu</p>
      </div>
    )
  }

  // Build name lookup from nodes
  const names = {}
  nodes?.farms?.forEach(f => { names[`farm_${f.id}`] = f.name })
  nodes?.hubs?.forEach(h => { names[`hub_${h.id}`] = h.name })
  nodes?.biorefineries?.forEach(b => { names[`biorefinery_${b.id}`] = b.name })

  const routes = result.routes.sort((a, b) => b.flow_ton_day - a.flow_ton_day)

  // Group by hub for bar chart
  const hubFlows = {}
  routes.forEach(r => {
    if (r.from_type === 'farm') {
      const key = `hub_${r.to_id}`
      const name = (names[key] || `Hub ${r.to_id}`).replace('KUD ', '').replace(' Hub — ', '\n')
      hubFlows[key] = (hubFlows[key] || { name, flow: 0 })
      hubFlows[key].flow += r.flow_ton_day
    }
  })
  const chartData = Object.values(hubFlows)

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Bar chart: flow per hub */}
      <div className="card">
        <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: 'var(--space-4)', color: 'var(--color-gray-800)' }}>
          Aliran Tongkol per Hub (ton/hari)
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F0F0F0" />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 11, fontFamily: 'Inter' }}
              angle={-30} textAnchor="end" interval={0}
            />
            <YAxis tick={{ fontSize: 11, fontFamily: 'Inter' }} />
            <Tooltip
              formatter={(v) => [`${fmt(v, 1)} ton/hari`, 'Aliran']}
              contentStyle={{ fontFamily: 'Inter', fontSize: 13, borderRadius: 10 }}
            />
            <Bar dataKey="flow" fill="#4CAF50" radius={[6, 6, 0, 0]}>
              <LabelList dataKey="flow" position="top" style={{ fontSize: 11, fill: '#2E7D32', fontWeight: 600 }}
                formatter={v => `${v.toFixed(0)}t`} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Route Detail Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: 'var(--space-5) var(--space-6)', borderBottom: '1px solid var(--color-gray-100)' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: 'var(--color-gray-800)' }}>
            Rincian Rute Pengiriman ({routes.length} rute aktif)
          </h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Dari</th>
                <th>Tipe</th>
                <th>Ke</th>
                <th>Tipe</th>
                <th style={{ textAlign: 'right' }}>Aliran (ton/hari)</th>
                <th style={{ textAlign: 'right' }}>Jarak (km)</th>
                <th style={{ textAlign: 'right' }}>Biaya/hari (USD)</th>
                <th style={{ textAlign: 'right' }}>Emisi CO₂ (kg/hari)</th>
              </tr>
            </thead>
            <tbody>
              {routes.map((r, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500, maxWidth: 160 }}>
                    <span style={{ fontSize: 'var(--text-xs)', display: 'block' }}>
                      {(names[`${r.from_type}_${r.from_id}`] || `${r.from_type} #${r.from_id}`)
                        .replace('Lahan Jagung ', '').replace('KUD ', '')}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${r.from_type === 'farm' ? 'badge-green' : 'badge-yellow'}`}>
                      {r.from_type === 'farm' ? '🌽 Farm' : '🏭 Hub'}
                    </span>
                  </td>
                  <td style={{ fontWeight: 500, maxWidth: 160 }}>
                    <span style={{ fontSize: 'var(--text-xs)', display: 'block' }}>
                      {(names[`${r.to_type}_${r.to_id}`] || `${r.to_type} #${r.to_id}`)
                        .replace('KUD ', '').replace('Biorefinery ', '')}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${r.to_type === 'hub' ? 'badge-yellow' : 'badge-brown'}`}>
                      {r.to_type === 'hub' ? '🏭 Hub' : '⚗️ Pabrik'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--color-primary-800)' }}>
                    {fmt(r.flow_ton_day, 2)}
                  </td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.distance_km, 1)}</td>
                  <td style={{ textAlign: 'right', color: '#E65100' }}>${fmt(r.cost_usd_day, 4)}</td>
                  <td style={{ textAlign: 'right', color: '#1565C0' }}>{fmt(r.emission_kg_co2_day, 3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
