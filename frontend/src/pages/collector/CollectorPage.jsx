import { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { Package, Truck, PlusCircle, CheckCircle, Bell, LogOut, Users, Droplets } from 'lucide-react'
import toast from 'react-hot-toast'
import { transactionApi } from '../../api/client'

export default function CollectorPage() {
  const { user, logout } = useAuth()
  const [warehouse, setWarehouse]   = useState({
    capacity_ton: 120,
    current_ton: 0,
    dispatch_threshold_pct: 85,
  })
  const [records, setRecords]       = useState([])
  const [showModal, setShowModal]   = useState(false)
  const [truckDispatched, setTruckDispatched] = useState(false)
  const [truckEta, setTruckEta]     = useState(null)
  
  const [loading, setLoading]       = useState(true)
  const [dispatchLoading, setDispatchLoading] = useState(false)

  const fetchHarvests = async () => {
    try {
      const res = await transactionApi.getHarvests()
      setRecords(res.data)
      // Calculate current ton from pending harvests
      const totalKg = res.data.reduce((sum, r) => sum + r.weight_kg, 0)
      setWarehouse(prev => ({ ...prev, current_ton: totalKg / 1000 }))
      setLoading(false)
    } catch (err) {
      console.error(err)
      toast.error('Gagal memuat data penerimaan')
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHarvests()
  }, [])

  const fillPct      = (warehouse.current_ton / warehouse.capacity_ton) * 100
  const isNearFull   = fillPct >= warehouse.dispatch_threshold_pct
  const remaining    = warehouse.capacity_ton - warehouse.current_ton
  const pricePerKg   = 850

  const gaugeColor   = fillPct >= 90 ? 'danger' : fillPct >= 75 ? 'warning' : ''

  const handleCallTruck = async () => {
    setDispatchLoading(true)
    toast('🔄 Menghitung rute optimal & mengirim FTL...', { icon: '⚙️' })
    try {
      // Create a Hub Batch for all current ton
      const inputKg = warehouse.current_ton * 1000
      const batchRes = await transactionApi.createHubBatch({
        hub_id: user?.id || 1,
        input_kg: inputKg,
        shrinkage_pct: 0.18, // 18% shrinkage
      })

      // Create a Shipment
      await transactionApi.createShipment({
        hub_id: user?.id || 1,
        biorefinery_id: 1, // Sentral factory
        payload_ton: batchRes.data.output_kg / 1000,
        distance_km: 85, // Dummy distance
      })

      setDispatchLoading(false)
      setTruckDispatched(true)
      setTruckEta('2 Jam 15 Menit')
      setWarehouse(prev => ({ ...prev, current_ton: 0 }))
      toast.success('🚛 Truk berhasil dijadwalkan! Barang dikirim ke Pabrik.')
    } catch (err) {
      console.error(err)
      toast.error('Gagal mengirim truk')
      setDispatchLoading(false)
    }
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
              Gudang Konsolidasi (Cross-Docking)
            </div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: 'var(--text-xs)' }}>
              {user?.kabupaten || 'Bangkalan'} — {user?.full_name || 'Petugas Hub'}
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
                Batas pengiriman FTL: {warehouse.dispatch_threshold_pct}% kapasitas
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
            <div className={`gauge-fill ${gaugeColor}`} style={{ width: `${Math.min(fillPct, 100)}%`, borderRadius: 'var(--radius-lg)', position: 'relative' }}>
              {fillPct > 20 && (
                <span style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', color: 'white', fontWeight: 800, fontSize: 'var(--text-sm)' }}>
                  {warehouse.current_ton.toFixed(1)} ton
                </span>
              )}
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
                  Truk FTL Sedang Dalam Perjalanan!
                </h3>
                <p style={{ color: '#0277BD', fontSize: 'var(--text-base)', marginTop: 4 }}>
                  ⏱ Estimasi tiba di Biorefinery: <b style={{ fontSize: 'var(--text-xl)' }}>{truckEta}</b>
                </p>
                <p style={{ fontSize: 'var(--text-sm)', color: '#555', marginTop: 4 }}>
                  Kadar air telah disusutkan (Shrinkage applied). Rute optimal oleh BioChain-Opt.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 'var(--space-3)' }}>
          <button
            className="btn btn-lg"
            onClick={handleCallTruck}
            disabled={dispatchLoading || truckDispatched || warehouse.current_ton === 0}
            style={{
              borderRadius: 'var(--radius-xl)',
              background: truckDispatched
                ? 'var(--color-gray-300)'
                : warehouse.current_ton > 0
                  ? 'linear-gradient(135deg, #FF6F00, #E65100)'
                  : 'var(--color-gray-200)',
              color: (truckDispatched || warehouse.current_ton === 0) ? 'var(--color-gray-500)' : 'white',
              fontWeight: 800,
              fontSize: 'var(--text-base)',
              animation: isNearFull && !truckDispatched ? 'pulse-cta 2s infinite' : 'none',
            }}
          >
            {dispatchLoading ? (
              <><div className="spinner" style={{ width: 20, height: 20, borderWidth: 3, borderTopColor: 'white', borderColor: 'rgba(255,255,255,0.3)' }} /> Memproses Batch...</>
            ) : truckDispatched ? (
              <><CheckCircle size={22} /> Batch FTL Dikirim</>
            ) : (
              <><Truck size={22} /> KONSOLIDASI & KIRIM (FTL)</>
            )}
          </button>
        </div>

        {/* Incoming Records Table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: 'var(--space-4) var(--space-6)', background: 'var(--color-gray-50)', borderBottom: '1px solid var(--color-gray-200)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, color: 'var(--color-gray-800)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Users size={18} /> Panen Masuk (Dari Petani)
            </h3>
            <span className="badge badge-green">{records.length} transaksi</span>
          </div>
          
          {loading ? (
             <div style={{ textAlign: 'center', padding: 20 }}><div className="spinner"></div></div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Waktu</th>
                    <th>Petani (ID)</th>
                    <th style={{ textAlign: 'right' }}>Berat Masuk (kg)</th>
                    <th style={{ textAlign: 'right' }}>Grade</th>
                    <th style={{ textAlign: 'center' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map(rec => (
                    <tr key={rec.id}>
                      <td style={{ color: 'var(--color-gray-500)', fontSize: 'var(--text-sm)' }}>
                        {new Date(rec.created_at).toLocaleTimeString('id-ID', {hour: '2-digit', minute:'2-digit'})}
                      </td>
                      <td style={{ fontWeight: 600 }}>Petani #{rec.farmer_id}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--color-secondary-700)' }}>
                        {rec.weight_kg.toLocaleString('id-ID')}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--color-primary-800)' }}>
                        {rec.quality_grade}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <span className="badge badge-green">✅ Diterima</span>
                      </td>
                    </tr>
                  ))}
                  {records.length === 0 && (
                    <tr><td colSpan={5} style={{ textAlign: 'center', padding: 20 }}>Belum ada panen masuk hari ini.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
