import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { DollarSign, ShieldAlert, Leaf } from 'lucide-react'

const fmt = (n) => n != null ? Number(n).toLocaleString('id-ID', { maximumFractionDigits: 0 }) : '—'
const fmtIDR = (n) => n != null ? `Rp ${fmt(n)}` : '—'

export default function CostBreakdown({ result, nodes }) {
  if (!result || !nodes) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--space-16)', color: 'var(--color-gray-400)' }}>
        <p style={{ fontSize: 'var(--text-lg)', fontWeight: 600 }}>Jalankan optimasi untuk melihat Rincian Biaya</p>
      </div>
    )
  }

  // Cost Data for Chart
  const costData = [
    {
      name: 'Biaya Dasar Operasional',
      'Hulu (Petani)': result.harvest_cost_year,
      'Transport F-H': result.transport_fh_cost_year,
      'Handling Hub': result.hub_handling_cost_year,
      'Biaya Susut': result.shrinkage_cost_year,
      'Transport H-F': result.transport_hf_cost_year,
      'Pabrikasi': result.factory_cost_year,
    },
    {
      name: 'Penalti Objektif',
      'Pajak Karbon': result.green_penalty_year,
      'Risiko Rantai': result.resilience_penalty_year,
      'Hulu (Petani)': 0,
      'Transport F-H': 0,
      'Handling Hub': 0,
      'Biaya Susut': 0,
      'Transport H-F': 0,
      'Pabrikasi': 0,
    }
  ]

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Objective Function Summary */}
      <div className="card">
        <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 700, marginBottom: 'var(--space-6)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <DollarSign size={20} color="var(--color-primary-600)" />
          Struktur Objektif Multi-Kriteria (MILP)
        </h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
          <div style={{ background: 'var(--color-gray-50)', padding: '16px', borderRadius: '8px' }}>
            <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-500)', marginBottom: '4px' }}>Total Biaya Logistik & Ops (Obj 1)</div>
            <div style={{ fontSize: 'var(--text-xl)', fontWeight: 800, color: 'var(--color-primary-800)' }}>
              Rp {fmt((result.harvest_cost_year + result.transport_fh_cost_year + result.hub_handling_cost_year + result.shrinkage_cost_year + result.transport_hf_cost_year + result.factory_cost_year) / 1000000)} Juta
            </div>
          </div>
          
          <div style={{ background: '#FFEBEE', padding: '16px', borderRadius: '8px' }}>
            <div style={{ fontSize: 'var(--text-sm)', color: '#C62828', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Leaf size={14} /> Total Pajak Karbon (Obj 2)
            </div>
            <div style={{ fontSize: 'var(--text-xl)', fontWeight: 800, color: '#B71C1C' }}>
              Rp {fmt(result.green_penalty_year / 1000000)} Juta
            </div>
          </div>

          <div style={{ background: '#FFF3E0', padding: '16px', borderRadius: '8px' }}>
            <div style={{ fontSize: 'var(--text-sm)', color: '#EF6C00', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ShieldAlert size={14} /> Penalti Risiko (Obj 3)
            </div>
            <div style={{ fontSize: 'var(--text-xl)', fontWeight: 800, color: '#E65100' }}>
              Rp {fmt(result.resilience_penalty_year / 1000000)} Juta
            </div>
          </div>
        </div>
        
        <div style={{ marginTop: '24px', padding: '16px', background: 'var(--color-primary-50)', borderRadius: '8px', border: '1px solid var(--color-primary-200)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-primary-700)', fontWeight: 600 }}>Total Fungsi Objektif Terminimumkan (Z)</div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)' }}>Termasuk seluruh biaya dan penalti artifisial</div>
          </div>
          <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 900, color: 'var(--color-primary-900)' }}>
            Rp {fmt(result.objective_value / 1000000)} Jt
          </div>
        </div>
      </div>

      <div className="card">
        <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 700, marginBottom: 'var(--space-6)' }}>
          Distribusi Biaya ABC per Kategori
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={costData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" />
            <YAxis tickFormatter={(val) => `Rp${fmt(val / 1000000)}Jt`} />
            <Tooltip
              formatter={(val) => `Rp ${fmt(val / 1000000)} Juta`}
              contentStyle={{ borderRadius: '8px', fontFamily: 'Inter' }}
            />
            <Legend />
            <Bar dataKey="Hulu (Petani)" stackId="a" fill="#8D6E63" />
            <Bar dataKey="Transport F-H" stackId="a" fill="#FFB300" />
            <Bar dataKey="Handling Hub" stackId="a" fill="#FB8C00" />
            <Bar dataKey="Biaya Susut" stackId="a" fill="#039BE5" />
            <Bar dataKey="Transport H-F" stackId="a" fill="#43A047" />
            <Bar dataKey="Pabrikasi" stackId="a" fill="#1E88E5" />
            <Bar dataKey="Pajak Karbon" stackId="a" fill="#E53935" />
            <Bar dataKey="Risiko Rantai" stackId="a" fill="#8E24AA" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
