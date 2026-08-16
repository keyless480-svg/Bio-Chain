// pages/collector/CollectorPage.jsx — KUD warehouse manager dashboard
import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { Package, Truck, PlusCircle, CheckCircle, Bell, LogOut, Users } from 'lucide-react'
import toast from 'react-hot-toast'

// Simulated warehouse data for KUD Bangkalan
const INITIAL_STATE = {
  capacity_ton: 120,
  current_ton: 96.8,
  dispatch_threshold_pct: 85,
}

const INITIAL_RECORDS = [
  { id: 1, farmer: 'Pak Sugeng', weight_kg: 850, time: '07:15', paid: 722500 },
  { id: 2, farmer: 'Bu Sari',    weight_kg: 620, time: '08:30', paid: 527000 },
  { id: 3, farmer: 'Pak Hadi',   weight_kg: 1200, time: '09:10', paid: 1020000 },
]

export default function CollectorPage() {
  const { user, logout } = useAuth()
  const [warehouse, setWarehouse]   = useState(INITIAL_STATE)
  const [records, setRecords]       = useState(INITIAL_RECORDS)
  const [showModal, setShowModal]   = useState(false)
  const [truckDispatched, setTruckDispatched] = useState(false)
  const [truckEta, setTruckEta]     = useState(null)
  const [newFarmer, setNewFarmer]   = useState('')
  const [newWeight, setNewWeight]   = useState('')
  const [dispatchLoading, setDispatchLoading] = useState(false)

  const fillPct      = (warehouse.current_ton / warehouse.capacity_ton) * 100
  const isNearFull   = fillPct >= warehouse.dispatch_threshold_pct
  const remaining    = warehouse.capacity_ton - warehouse.current_ton
  const pricePerKg   = 850

  const gaugeColor   = fillPct >= 90 ? 'danger' : fillPct >= 75 ? 'warning' : ''

  const handleReceive = () => {
    if (!newFarmer.trim() || !newWeight || parseInt(newWeight) <= 0) {
      toast.error('Isi nama petani dan berat dengan benar')
      return
    }
    const weightKg  = parseInt(newWeight)
    const weightTon = weightKg / 1000
    const paid      = weightKg * pricePerKg

    if (weightTon > remaining) {
      toast.error(`Kapasitas tersisa hanya ${remaining.toFixed(1)} ton!`)
      return
    }

    const rec = {
      id: records.length + 1,
      farmer: newFarmer,
      weight_kg: weightKg,
      time: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }),
      paid,
    }
    setRecords(prev => [rec, ...prev])
    setWarehouse(prev => ({ ...prev, current_ton: prev.current_ton + weightTon }))
    setNewFarmer('')
    setNewWeight('')
    setShowModal(false)
    toast.success(`✅ Diterima dari ${newFarmer}: ${weightKg} kg (Rp ${paid.toLocaleString('id-ID')})`)
  }

  const handleCallTruck = () => {
    setDispatchLoading(true)
    toast('🔄 Menghitung rute optimal...', { icon: '⚙️' })
    setTimeout(() => {
      setDispatchLoading(false)
      setTruckDispatched(true)
      setTruckEta('2 Jam 15 Menit')
      toast.success('🚛 Truk sedang dalam perjalanan!')
    }, 2500)
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-gray-50)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{
        background: 'linear-gradient(135deg, var(--color-secondary-700), var(--color-secondary-900))',
        padding: 'var(--space-4) var(--space-6)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        boxShadow: 'var(--shadow-lg)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 28 }}>🏭</span>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, color: 'white', fontSize: 'var(--text-xl)' }}>
              Gudang KUD
            </div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: 'var(--text-xs)' }}>
              {user?.kabupaten || 'Bangkalan'} — {user?.full_name || 'Petugas KUD'}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {isNearFull && !truckDispatched && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'rgba(255,193,7,0.2)', borderRadius: 8, padding: '6px 12px' }}>
              <Bell size={16} color="#FFC107" />
              <span style={{ color: '#FFC107', fontSize: 'var(--text-xs)', fontWeight: 700 }}>Gudang hampir penuh!</span>
            </div>
          )}
          <button onClick={logout} style={{ background: 'rgba(255,255,255,0.15)', border: 'none', color: 'white', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 'var(--text-sm)' }}>
            <LogOut size={14} style={{ display: 'inline', marginRight: 4 }} /> Keluar
          </button>
        </div>
      </header>

      <div style={{ padding: 'var(--space-5) var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', maxWidth: 800, margin: '0 auto', width: '100%' }}>

        {/* Warehouse Gauge Card */}
        <div className="card" style={{ border: isNearFull ? '2px solid var(--color-warning)' : '1px solid var(--color-gray-200)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
            <div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'var(--text-2xl)', color: 'var(--color-secondary-800)' }}>
                📦 Kapasitas Gudang
              </h2>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-500)', marginTop: 2 }}>
                Batas pengiriman: {warehouse.dispatch_threshold_pct}% kapasitas
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{
                fontFamily: 'var(--font-display)',
                fontSize: 'var(--text-4xl)',
                fontWeight: 900,
                color: fillPct >= 90 ? 'var(--color-error)' : fillPct >= 75 ? 'var(--color-warning)' : 'var(--color-primary-800)',
              }}>
                {fillPct.toFixed(0)}%
              </div>
              <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-500)' }}>
                {warehouse.current_ton.toFixed(1)} / {warehouse.capacity_ton} ton
              </div>
            </div>
          </div>

          {/* Big Gauge Bar */}
          <div className="gauge-label">
            <span>Kosong</span>
            <span style={{ color: isNearFull ? 'var(--color-warning)' : 'var(--color-primary-700)', fontWeight: 700 }}>
              Sisa: {remaining.toFixed(1)} ton
            </span>
            <span>Penuh</span>
          </div>
          <div className="gauge-bar" style={{ height: 36, borderRadius: 'var(--radius-lg)' }}>
            <div className={`gauge-fill ${gaugeColor}`} style={{ width: `${fillPct}%`, borderRadius: 'var(--radius-lg)', position: 'relative' }}>
              {fillPct > 20 && (
                <span style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', color: 'white', fontWeight: 800, fontSize: 'var(--text-sm)' }}>
                  {warehouse.current_ton.toFixed(0)} ton
                </span>
              )}
            </div>
          </div>

          {/* Dispatch markers */}
          <div style={{ position: 'relative', height: 20, marginTop: 4 }}>
            <div style={{
              position: 'absolute',
              left: `${warehouse.dispatch_threshold_pct}%`,
              top: 0,
              transform: 'translateX(-50%)',
              fontSize: 'var(--text-xs)',
              color: 'var(--color-warning)',
              fontWeight: 700,
              whiteSpace: 'nowrap',
            }}>
              ⚡ Batas Pengiriman ({warehouse.dispatch_threshold_pct}%)
            </div>
          </div>
        </div>

        {/* Truck dispatch notification */}
        {truckDispatched && (
          <div className="card fade-in" style={{ background: 'linear-gradient(135deg, #E3F2FD, #BBDEFB)', border: '2px solid #42A5F5' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <span style={{ fontSize: 48 }}>🚛</span>
              <div>
                <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, color: '#0277BD', fontSize: 'var(--text-xl)' }}>
                  Truk Sedang Dalam Perjalanan!
                </h3>
                <p style={{ color: '#0277BD', fontSize: 'var(--text-base)', marginTop: 4 }}>
                  ⏱ Estimasi tiba: <b style={{ fontSize: 'var(--text-xl)' }}>{truckEta}</b>
                </p>
                <p style={{ fontSize: 'var(--text-sm)', color: '#555', marginTop: 4 }}>
                  Rute optimal telah dihitung oleh sistem BioChain-Opt
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)' }}>
          <button
            className="btn btn-primary btn-lg"
            onClick={() => setShowModal(true)}
            style={{ borderRadius: 'var(--radius-xl)' }}
          >
            <PlusCircle size={22} />
            Terima Barang dari Petani
          </button>

          <button
            className="btn btn-lg"
            onClick={handleCallTruck}
            disabled={dispatchLoading || truckDispatched || !isNearFull}
            style={{
              borderRadius: 'var(--radius-xl)',
              background: truckDispatched
                ? 'var(--color-gray-300)'
                : isNearFull
                  ? 'linear-gradient(135deg, #FF6F00, #E65100)'
                  : 'var(--color-gray-200)',
              color: (truckDispatched || !isNearFull) ? 'var(--color-gray-500)' : 'white',
              fontWeight: 800,
              fontSize: 'var(--text-base)',
              animation: isNearFull && !truckDispatched ? 'pulse-cta 2s infinite' : 'none',
            }}
          >
            {dispatchLoading ? (
              <><div className="spinner" style={{ width: 20, height: 20, borderWidth: 3, borderTopColor: 'white', borderColor: 'rgba(255,255,255,0.3)' }} /> Menghitung...</>
            ) : truckDispatched ? (
              <><CheckCircle size={22} /> Truk Dipanggil</>
            ) : (
              <><Truck size={22} /> PANGGIL TRUK PABRIK</>
            )}
          </button>
        </div>

        {!isNearFull && (
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-400)', textAlign: 'center' }}>
            💡 Tombol panggil truk aktif saat gudang terisi ≥{warehouse.dispatch_threshold_pct}%
            ({(warehouse.capacity_ton * warehouse.dispatch_threshold_pct / 100).toFixed(0)} ton)
          </p>
        )}

        {/* Incoming Records Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: 'var(--space-4) var(--space-6)', background: 'var(--color-gray-50)', borderBottom: '1px solid var(--color-gray-200)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: 'var(--color-gray-800)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Users size={18} /> Catatan Penerimaan Hari Ini
            </h3>
            <span className="badge badge-green">{records.length} transaksi</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Waktu</th>
                  <th>Nama Petani</th>
                  <th style={{ textAlign: 'right' }}>Berat (kg)</th>
                  <th style={{ textAlign: 'right' }}>Dibayar (Rp)</th>
                  <th style={{ textAlign: 'center' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {records.map(rec => (
                  <tr key={rec.id}>
                    <td style={{ color: 'var(--color-gray-500)', fontSize: 'var(--text-sm)' }}>{rec.time}</td>
                    <td style={{ fontWeight: 600 }}>{rec.farmer}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--color-secondary-700)' }}>
                      {rec.weight_kg.toLocaleString('id-ID')}
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--color-primary-800)' }}>
                      Rp {rec.paid.toLocaleString('id-ID')}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <span className="badge badge-green">✅ Diterima</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ padding: 'var(--space-3) var(--space-6)', background: 'var(--color-gray-50)', borderTop: '1px solid var(--color-gray-200)', display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-600)', fontWeight: 600 }}>
              Total Hari Ini: {records.reduce((s, r) => s + r.weight_kg, 0).toLocaleString('id-ID')} kg
            </span>
            <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-primary-800)', fontWeight: 700 }}>
              Rp {records.reduce((s, r) => s + r.paid, 0).toLocaleString('id-ID')}
            </span>
          </div>
        </div>
      </div>

      {/* Modal: Receive Goods */}
      {showModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 'var(--z-modal)', padding: 'var(--space-6)',
          backdropFilter: 'blur(4px)',
        }}>
          <div className="card fade-in" style={{ maxWidth: 420, width: '100%' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'var(--text-2xl)', marginBottom: 'var(--space-5)', color: 'var(--color-secondary-800)' }}>
              🌽 Terima Barang Petani
            </h3>

            <div className="input-group" style={{ marginBottom: 'var(--space-4)' }}>
              <label className="input-label">Nama Petani</label>
              <input
                type="text" className="input"
                placeholder="Contoh: Pak Budi"
                value={newFarmer}
                onChange={e => setNewFarmer(e.target.value)}
              />
            </div>

            <div className="input-group" style={{ marginBottom: 'var(--space-4)' }}>
              <label className="input-label">Berat Tongkol Jagung (kg)</label>
              <input
                type="number" className="input"
                placeholder="0"
                value={newWeight}
                onChange={e => setNewWeight(e.target.value)}
                min={1}
                style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, textAlign: 'center' }}
              />
            </div>

            {newWeight > 0 && (
              <div style={{
                background: '#E8F5E9', borderRadius: 'var(--radius-lg)',
                padding: 'var(--space-3)', textAlign: 'center', marginBottom: 'var(--space-4)',
              }}>
                <span style={{ fontWeight: 600, color: 'var(--color-primary-800)' }}>
                  Bayar: Rp {(parseInt(newWeight) * pricePerKg).toLocaleString('id-ID')}
                </span>
              </div>
            )}

            <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
              <button className="btn btn-ghost btn-full" onClick={() => setShowModal(false)}>Batal</button>
              <button className="btn btn-primary btn-full" onClick={handleReceive}>
                <CheckCircle size={18} /> Konfirmasi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
