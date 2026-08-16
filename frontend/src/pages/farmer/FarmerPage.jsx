// pages/farmer/FarmerPage.jsx — Simple sell-my-harvest single-page for farmers
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { MapPin, Package, ChevronRight, ArrowLeft, Check, Phone } from 'lucide-react'
import toast from 'react-hot-toast'
import { transactionApi } from '../../api/client'

// Simulated nearest KUD data (in real app: computed from GPS + PostGIS)
const NEAREST_KUDS = [
  { id: 1, name: 'KUD Tuban Barat', distance: '3.2 km', eta: '12 menit', capacity: '80%', phone: '0356-321456' },
  { id: 2, name: 'KUD Pantura Hub', distance: '8.7 km', eta: '30 menit', capacity: '45%', phone: '0356-789012' },
]

const CORN_PRICE_TODAY = 850  // Rp/kg (simulated daily price)

export default function FarmerPage() {
  const { user, logout } = useAuth()
  const [step, setStep]       = useState('home')   // home | input | result
  const [weight, setWeight]   = useState('')
  const [gpsReq, setGpsReq]   = useState(false)
  const [loading, setLoading] = useState(false)
  const [pickup, setPickup]   = useState(false)

  const totalEarning = weight ? parseInt(weight) * CORN_PRICE_TODAY : 0

  const handleJual = () => {
    setLoading(true)
    setGpsReq(true)
    // Simulate GPS access + finding nearest KUD
    setTimeout(() => {
      setLoading(false)
      setStep('input')
    }, 1200)
  }

  const handleSubmit = async () => {
    if (!weight || parseInt(weight) <= 0) { toast.error('Masukkan jumlah yang valid'); return }
    setLoading(true)
    try {
      await transactionApi.createHarvest({
        farmer_id: user?.id || 1, // Fallback if no user id
        weight_kg: parseInt(weight),
        quality_grade: 'A',
        price_per_kg: CORN_PRICE_TODAY
      })
      setLoading(false)
      setStep('result')
      toast.success('Pesanan berhasil dikirim ke Pengepul!')
    } catch (err) {
      console.error(err)
      toast.error('Gagal mengirim pesanan')
      setLoading(false)
    }
  }

  return (
    <div className="farmer-page">
      {/* Header */}
      <header style={{
        background: 'linear-gradient(135deg, var(--color-primary-800), var(--color-primary-900))',
        padding: 'var(--space-4) var(--space-6)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 28 }}>🌿</span>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, color: 'white', fontSize: 'var(--text-xl)' }}>
              BioChain
            </div>
            <div style={{ color: 'rgba(255,255,255,0.7)', fontSize: 'var(--text-xs)' }}>
              Halo, {user?.full_name?.split(' ')[0] || 'Petani'}! 👋
            </div>
          </div>
        </div>
        <button onClick={logout} style={{ background: 'rgba(255,255,255,0.15)', border: 'none', color: 'white', padding: '8px 16px', borderRadius: 8, cursor: 'pointer', fontSize: 'var(--text-sm)' }}>
          Keluar
        </button>
      </header>

      {/* Price Banner */}
      <div className="price-banner">
        <p className="price-label">💰 Harga Tongkol Jagung Hari Ini</p>
        <div className="price-value">Rp {CORN_PRICE_TODAY.toLocaleString('id-ID')}</div>
        <p className="price-unit">per Kilogram</p>
        <div style={{ marginTop: 8, fontSize: 'var(--text-xs)', opacity: 0.7 }}>
          📍 {user?.kabupaten || 'Jawa Timur'} • Update: Hari ini 06:00 WIB
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, padding: 'var(--space-6)', maxWidth: 480, margin: '0 auto', width: '100%' }}>

        {/* ── STEP: Home ── */}
        {step === 'home' && (
          <div className="fade-in">
            {/* Info card */}
            <div className="card" style={{ marginBottom: 'var(--space-6)', background: 'linear-gradient(135deg, #E8F5E9, #F1F8E9)', border: '1px solid #C8E6C9' }}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <span style={{ fontSize: 32 }}>🌽</span>
                <div>
                  <p style={{ fontWeight: 700, color: 'var(--color-primary-800)', marginBottom: 4 }}>
                    Jual Tongkol Jagung Anda
                  </p>
                  <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-600)', lineHeight: 1.6 }}>
                    Tongkol jagung Anda akan diolah menjadi <b>Bioetanol Ramah Lingkungan</b>. 
                    Anda berkontribusi pada masa depan energi hijau Indonesia!
                  </p>
                </div>
              </div>
            </div>

            {/* BIG CTA Button */}
            <button className="btn-cta" onClick={handleJual} disabled={loading}>
              {loading ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                  <div className="spinner" style={{ borderColor: 'rgba(255,255,255,0.3)', borderTopColor: 'white' }} />
                  <span>Mencari lokasi Anda...</span>
                </div>
              ) : (
                <>
                  🛒<br />JUAL PANEN SAYA
                </>
              )}
            </button>

            {/* Pickup option */}
            <div style={{ marginTop: 'var(--space-5)' }}>
              <button
                className="btn btn-outline btn-full btn-lg"
                onClick={() => { setPickup(true); handleJual() }}
              >
                🚛 Minta Dijemput Pengepul
              </button>
            </div>

            {/* Quick stats */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
              {[
                { label: 'KUD Terdekat', value: '3.2 km', icon: '🏭' },
                { label: 'Harga Naik', value: '+5.2%', icon: '📈' },
              ].map((item, i) => (
                <div key={i} className="card" style={{ textAlign: 'center', padding: 'var(--space-4)' }}>
                  <div style={{ fontSize: 28 }}>{item.icon}</div>
                  <div style={{ fontWeight: 700, fontSize: 'var(--text-xl)', color: 'var(--color-primary-800)' }}>{item.value}</div>
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)' }}>{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── STEP: Input Weight ── */}
        {step === 'input' && (
          <div className="fade-in">
            <button className="btn btn-ghost" onClick={() => setStep('home')} style={{ marginBottom: 'var(--space-4)' }}>
              <ArrowLeft size={18} /> Kembali
            </button>

            <div className="card" style={{ marginBottom: 'var(--space-4)', background: 'linear-gradient(135deg, #E3F2FD, #BBDEFB)', border: '1px solid #90CAF9' }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', color: '#0277BD', fontWeight: 600 }}>
                <MapPin size={18} /> Lokasi GPS terdeteksi ✅
              </div>
              <p style={{ fontSize: 'var(--text-sm)', color: '#555', marginTop: 4 }}>
                {user?.kabupaten || 'Kabupaten Anda'} — KUD terdekat ditemukan
              </p>
            </div>

            <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'var(--text-2xl)', color: 'var(--color-gray-800)', marginBottom: 'var(--space-6)' }}>
                Berapa banyak yang ingin dijual?
              </h2>

              <div className="input-group" style={{ marginBottom: 'var(--space-6)' }}>
                <label className="input-label" style={{ fontSize: 'var(--text-base)' }}>
                  Jumlah Tongkol Jagung
                </label>
                <div style={{ position: 'relative' }}>
                  <input
                    type="number"
                    className="input"
                    placeholder="0"
                    value={weight}
                    onChange={e => setWeight(e.target.value)}
                    min={1}
                    style={{
                      fontSize: 'var(--text-4xl)',
                      fontWeight: 900,
                      textAlign: 'center',
                      padding: 'var(--space-4)',
                      borderRadius: 'var(--radius-xl)',
                      height: 100,
                      fontFamily: 'var(--font-display)',
                      color: 'var(--color-primary-800)',
                    }}
                  />
                </div>
                <p style={{ textAlign: 'center', color: 'var(--color-gray-500)', fontSize: 'var(--text-base)', marginTop: 4 }}>
                  Kilogram (kg)
                </p>
              </div>

              {weight > 0 && (
                <div style={{
                  background: 'linear-gradient(135deg, #E8F5E9, #C8E6C9)',
                  borderRadius: 'var(--radius-xl)', padding: 'var(--space-4)',
                  textAlign: 'center', marginBottom: 'var(--space-4)',
                  border: '1px solid #A5D6A7',
                }}>
                  <p style={{ color: 'var(--color-gray-600)', fontSize: 'var(--text-sm)' }}>Estimasi Pendapatan Anda</p>
                  <p style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: 'var(--text-4xl)',
                    fontWeight: 900,
                    color: 'var(--color-primary-800)',
                  }}>
                    Rp {totalEarning.toLocaleString('id-ID')}
                  </p>
                  <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)' }}>
                    {weight} kg × Rp {CORN_PRICE_TODAY.toLocaleString('id-ID')}/kg
                  </p>
                </div>
              )}

              <button
                className="btn btn-primary btn-full btn-xl"
                onClick={handleSubmit}
                disabled={loading || !weight}
              >
                {loading ? <><div className="spinner" style={{ width: 24, height: 24, borderWidth: 3 }} /> Memproses...</> : <>Cari KUD Terdekat <ChevronRight size={20} /></>}
              </button>
            </div>
          </div>
        )}

        {/* ── STEP: Result ── */}
        {step === 'result' && (
          <div className="fade-in">
            <div style={{
              background: 'linear-gradient(135deg, #E8F5E9, #C8E6C9)',
              borderRadius: 'var(--radius-2xl)', padding: 'var(--space-6)',
              textAlign: 'center', marginBottom: 'var(--space-5)',
              border: '1px solid #A5D6A7',
            }}>
              <div style={{ fontSize: 64, marginBottom: 8 }}>✅</div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: 'var(--text-3xl)', color: 'var(--color-primary-800)' }}>
                Pesanan Dikirim!
              </h2>
              <p style={{ color: 'var(--color-gray-600)', marginTop: 4 }}>
                KUD akan segera menghubungi Anda
              </p>
            </div>

            <p style={{ fontWeight: 700, color: 'var(--color-gray-700)', marginBottom: 'var(--space-3)' }}>
              {pickup ? '🚛 Pengepul akan menjemput di:' : '📍 Antar tongkol jagung ke:'}
            </p>

            {NEAREST_KUDS.map(kud => (
              <div key={kud.id} className="card" style={{ marginBottom: 'var(--space-3)', border: kud.id === 1 ? '2px solid var(--color-primary-500)' : '1px solid var(--color-gray-200)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <p style={{ fontWeight: 700, fontSize: 'var(--text-lg)', color: 'var(--color-gray-800)' }}>
                      🏭 {kud.name}
                    </p>
                    <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-500)', marginTop: 2 }}>
                      📍 {kud.distance} • ⏱ {kud.eta}
                    </p>
                    <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-gray-500)' }}>
                      📞 {kud.phone}
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span className={`badge ${parseInt(kud.capacity) > 70 ? 'badge-yellow' : 'badge-green'}`}>
                      Terisi {kud.capacity}
                    </span>
                    {kud.id === 1 && (
                      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-primary-700)', fontWeight: 700, marginTop: 4 }}>
                        ✨ Rekomendasi
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            <div className="card" style={{ background: '#FFF9C4', border: '1px solid #FFF176', textAlign: 'center' }}>
              <p style={{ fontWeight: 700, color: '#F57F17', fontSize: 'var(--text-base)' }}>
                💰 Total Pendapatan Anda
              </p>
              <p style={{ fontFamily: 'var(--font-display)', fontWeight: 900, fontSize: 'var(--text-4xl)', color: '#E65100' }}>
                Rp {totalEarning.toLocaleString('id-ID')}
              </p>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-gray-500)' }}>
                Dibayarkan saat penimbangan di KUD
              </p>
            </div>

            <button className="btn btn-outline btn-full btn-lg" style={{ marginTop: 'var(--space-4)' }} onClick={() => { setStep('home'); setWeight('') }}>
              Kembali ke Beranda
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
